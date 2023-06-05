"""
safas/writers/

"""
import uuid
from pathlib import Path
import os
import logging
import multiprocessing

from copy import deepcopy
from threading import Thread
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

from rich.progress import Progress

import cv2
import numpy as np
import pandas as pd

params = {
    "name": "kwargs", 
    "title": "Parameters",
    "type": "group", 
    "children": 
    [	
        {"name": "save_frames", "type": "bool", "value": True},
        {"name": "save_obj_image", "type": "bool", "value": True},
        {"name": "max_track_angle", "type": "float", "value": 30, "limits": [0, 90]},
        {"name": "min_frames_per_track", "type": "int", "value": 5, "limits": [1, 50]},
        {"name": "join_discont_tracks", "type": "bool", "value": False,},
        {"name": "clear_tracks_on_save", "type": "bool", "value": True,},
        {"name": "clear_objs_on_save", "type": "bool", "value": True,},
        {"name": "px_um_cal", "type": "float", "value": 8.6},
    ]
}

log = logging.getLogger("rich")

def print_process(
    color, process_name, *args, error=False, warning=False, exception=False, **kwargs
    ):
    msg = " ".join([str(arg) for arg in args])  # Concatenate all incoming strings or objects
    rich_msg = f"[{color}]{process_name}[/{color}] | {msg}"
    
    if error:
        log.error(rich_msg)
    elif warning:
        log.warning(rich_msg)
    elif exception:
        log.exception(rich_msg)
    else:
        log.info(rich_msg)

def print(*args, **kwargs): print_process("cyan", "writer", *args, **kwargs)

def setup(): return None

def writer(output_path, tracks, objs, cap, 
           px_um_cal=1, 
           save_frames=True, 
           save_obj_img=True, 
           max_track_angle=None, 
           min_frames_per_track=None, 
           join_discont_tracks=False, 
           clear_on_save=True, 
           **kwargs): 
    """ 
    """
    if len(tracks) == 0: 
        print(f"No tracks to save.")
        return tracks, objs
    
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    dt = 1/fps
    print(f"Saving output to: {output_path}")
    print(f"Object properties caculated using {fps:0.2f} fps and metric pixel conversion of {px_um_cal:0.1f} um/px")
    
    track_idxs = list(set([key[0] for key in tracks])) # all tracks available
    dfx = [] 
    frame_items = dict()
    print(f"Analyzing {len(track_idxs)} tracks")
    for track_idx in track_idxs: 
        keys = [key for key in tracks if key[0]==track_idx]
        items = []
        track_uuid = str(uuid.uuid4())
  
        for key in keys: 
            track_idx = key[0]
            frame_idx = key[1]
            obj_idx = tracks[key]["obj_idx"]  
            cent = tracks[key]["obj_centroid"]
            area = tracks[key]["obj_area"]  
            contour = tracks[key]["obj_contour"]
            bbox = tracks[key]["obj_bbox"]
            
            if track_uuid not in frame_items: # keep first object for cropping later
                obj_item ={"track_idx": track_idx, "frame_idx": frame_idx, "obj_idx": obj_idx, "bbox": bbox}
                frame_items[track_uuid] = obj_item
            
            if len(contour) >= 5: 
                ellipse = cv2.fitEllipse(tracks[key]["obj_contour"])
                (xc,yc),(major_axis, minor_axis), angle = ellipse
            else: 
                # cannot calculate fitEllipse when contour is < 5
                major_axis = max(tracks[key]["obj_bbox"][2:])
                minor_axis = min(tracks[key]["obj_bbox"][2:])

            match_error = tracks[key]["match_error"]

            item = {
                "track_uuid": track_uuid,
                "frame_idx": frame_idx,
                "track_idx": track_idx,
                "obj_idx": obj_idx,
                "x_pos": cent[0], 
                "y_pos": cent[1], 
                "area": area*px_um_cal**2, 
                "major_axis": major_axis*px_um_cal,
                "minor_axis": minor_axis*px_um_cal,
                "match_error": match_error
             }
            
            items.append(item)

        df = pd.DataFrame(items)
  
        df["area_mean"] = df.area.mean()
        df["major_axis_mean"] = df.major_axis.mean()
        df["minor_axis_mean"] = df.major_axis.mean()
        df["vel_x_inst"] = (df.x_pos.diff()*px_um_cal)/dt/1e3 # convert um/s to mm/s
        df["vel_x_mean"] = df.vel_x_inst.mean()

        df["vel_y_inst"] = (df.y_pos.diff()*px_um_cal)/dt/1e3 # convert um/s to mm/s
        df["vel_y_mean"] = df.vel_y_inst.mean()
        df["N_frames"] = len(df)
        
        pts = np.array([(item["x_pos"], item["y_pos"]) for item in items])
        import pdb; pdb.set_trace()
        vect = [pts[1:]-pts[:-1]]
        angles = [angle_between(v, np.array([0, 1])) for v in vect]
        df.loc[1:, "angles"] = angles
        dfx.append(df) # full output
    
    if len(dfx) == 0: 
        print(f"No tracks saved: {len(track_idxs)} tracks tested, but 0 remain after filters")
        return tracks, objs
    
    dfx = pd.concat(dfx) # raw data
    
    if (min_frames_per_track is not None) & isinstance(min_frames_per_track, int): 
        track_uuid, ct = np.unique(df["track_uuid"], return_counts=True)
        track_uuid = track_uuid[ct>=min_frames_per_track]
        df = df.set_index("track_uuid").loc[track_uuid]

    if (max_track_angle is not None) & isinstance(max_track_angle, float): 
        if dfx.index.name != "track_uuid": dfx.set_index("track_uuid", inplace=True)
        print(f"Analyzing track angles")
        track_uuids = []
        for track_uuid in df.index.unique(): 
            if (df.loc[track_uuid, 'angles'].iloc[1:] < max_track_angle).all(): 
                track_uuids.append(track_uuid)
        print(f"Removing {len(dfx.index.unique()) - len(track_uuids)} tracks with angle > {max_track_angle} degrees")
        dfx = dfx.loc[track_uuids]
        dfx.reset_index(inplace=True, drop=False)

    dfx.to_csv(f"{output_path}/full_output.csv") # write full output

    dft = dfx.groupby("track_idx").last().reset_index(drop=False) # filter the summary

    cols = [
        "track_uuid", 
        "track_idx", 
        "vel_y_mean", "vel_x_mean", 
        "minor_axis_mean", "major_axis_mean", 
        "area_mean", 
        "N_frames"
    ]
    dft = dft[cols] # drop some columns in summary
    frame_idxs = dfx.groupby("track_idx").agg(['first', 'last'])["frame_idx"].values
    dft["frame_idx_start"] = frame_idxs[:,0]
    dft["frame_idx_end"] = frame_idxs[:,1]
    dft.to_csv(f"{output_path}/summary_output.csv")
    
    if save_obj_img: 
        print(f"Saving {len(frame_items)} object images")
        obj_path = str(Path(output_path).joinpath("objs"))
        os.makedirs(obj_path, exist_ok=True)

        vi = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, vi)
        ret, src = cap.read() 

        for frame_uuid in frame_items: 
            item = frame_items[frame_uuid]
            
            if item["frame_idx"] != vi: 
                cap.set(cv2.CAP_PROP_POS_FRAMES, item["frame_idx"])
                vi = item["frame_idx"]
                ret, src = cap.read() 
            
            x, y, dx, dy = item["bbox"] 
            pad = 5
                    
            ymin = np.clip(x-pad, a_min=0, a_max=src.shape[0]) 
            ymax = np.clip(x+dx+pad, a_min=0, a_max=src.shape[0])
            xmin = np.clip(y-pad, a_min=0, a_max=src.shape[1]) 
            xmax = np.clip(y+dy+pad, a_min=0, a_max=src.shape[1])

            obj_crop = src[xmin:xmax, ymin:ymax]
            if not (np.array(obj_crop.shape) ==0).any(): 
                fname = f"{item['track_idx']}-{item['frame_idx']}-{item['obj_idx']}-{frame_uuid}.png"
                cv2.imwrite(str(Path(obj_path).joinpath(fname)), obj_crop)

    if save_frames: 
        print(f"Saving {len(frame_idxs)} frames")
        path = Path(output_path).joinpath("frames")
        os.makedirs(path, exist_ok=True)
        frame_idxs = list(set([key[1] for key in tracks]))
        if len(frame_idxs) > 10: 
            n_threads = multiprocessing.cpu_count() - 1 
        else: 
            n_threads = 1
        run_frame_writer(cap, frame_idxs, n_threads, path)
  
    print(f"Output written to: {output_path}")
    return tracks, objs

def angle_between(v1, v2):
    """ angle between vectors v1 and v2 """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.degrees(np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)))

def unit_vector(vector):
    """  unit vector of the vector """
    # TODO: true divide error not solved in some cases
    return vector / np.linalg.norm(vector)

""" threaded frame writer to speed up"""
# NOTE: this gives good speedup but perhaps unecc. complex
def _producer(q_in, cap, frame_idxs, output_path):
    """ """
    for frame_idx in frame_idxs: 
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        fname = str(f"{output_path}/{frame_idx:05d}.png")
        q_in.put((frame, fname, frame_idx))
    q_in.put((None, None, None))
 
def _consumer(q_in, q_out):    
    """
    """
    while True:
        frame, fname, frame_idx = q_in.get() 
        if not frame_idx: 
            q_in.put((None, None, None)) 
            return   
        cv2.imwrite(fname, frame)
        q_out.put(frame_idx) 

def _monitor(q_out, n_frames): 
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Writing frames...", total=n_frames)
        
        while (not progress.finished) | (not q_out.empty()):            
            frame_idx = q_out.get()
            progress.update(task, advance=1)
    
def run_frame_writer(cap, frame_idxs, n_threads, output_path): 
    """ """   
    q_in = Queue(maxsize=100)
    q_out = Queue()

    for i in range(n_threads):
        worker = Thread(target=_consumer, args=(q_in, q_out))
        worker.setDaemon(True)
        worker.start()

    objs = dict()
    mon = Thread(target=_monitor, args=(q_out, len(frame_idxs)))
    mon.start()
   
    producer = Thread(target=_producer, args=(q_in, cap, frame_idxs, output_path))
    producer.start()
    
    producer.join()
    mon.join()

    print('Frame writer done')
