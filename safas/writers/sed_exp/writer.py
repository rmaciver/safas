"""
safas/linkers/linear_flocs/linker

The linker matches objects in a series of images.
The track formed is a list of objects. 
The linker algorithm is separate from the track management.
Simple data structures (lists, dict) are preferred to classes. 
Functions that transform the data structures are preferred to class attributes.
Start with the simple case of matching by size and distance. 
Suitable for processing a recorded video, not a live video feed.

"""
from copy import deepcopy
import uuid
import json
from pathlib import Path
import sys
import os

import cv2
import numpy as np
from matplotlib import pyplot as plt
import pandas as pd

from rich import progress

# NOTE: path hack to get relative import above top of package. to fix on install. 
path = str(Path(__file__).absolute().parents[2])
sys.path.append(path) # Adds higher directory to python modules path.

from prints import print_writer as print

params = {
    "name": "kwargs", 
    "title": "Parameters",
    "type": "group", 
    "children": 
    [	
        {"name": "save_frames", "type": "bool", "value": True},
        {"name": "save_obj_image", "type": "bool", "value": True},
        {"name": "max_angle_dev", "type": "float", "value": 30, "limits": [0, 90]},
        {"name": "min_frames_per_track", "type": "int", "value": 5, "limits": [1, 50]},
        {"name": "clear_tracks_on_save", "type": "bool", "value": True,},
        {"name": "clear_objs_on_save", "type": "bool", "value": True,},
        {"name": "px_um_cal", "type": "float", "value": 8.6},
    ]
}

def setup(): return None

def writer(output_path, tracks, objs, cap, 
           px_um_cal=1, 
           save_frames=True, 
           save_obj_img=True, 
           max_angle_dev=30, 
           min_frames_per_track=5, 
           clear_on_save=True, 
           **kwargs): 
    """ 
    """
    if len(tracks) == 0: 
        print(f"No tracks to save")
        return tracks, objs
    
    if save_obj_img: 
        obj_img_path = str(Path(output_path).joinpath("objs"))
        os.makedirs(obj_img_path, exist_ok=True)

    fps = float(cap.get(cv2.CAP_PROP_FPS))
    dt = 1/fps
    
    print(f"Object properties caculated using {fps:0.2f} fps and metric pixel conversion of {px_um_cal:0.1f} um/px")
    
    track_idxs = list(set([key[0] for key in tracks])) # all tracks available
    dfx = [] #pd.DataFrame(columns=["track_idx", ])
    for track_idx in track_idxs: 
        keys = [key for key in tracks if key[0]==track_idx]
        items = []
        
        for key in keys: 
            track_idx = key[0]
            frame_idx = key[1]
            obj_idx = tracks[key]["obj_idx"]  
            cent = tracks[key]["obj_centroid"]
            area = tracks[key]["obj_area"]  
            contour = tracks[key]["obj_contour"]

            if len(contour) >= 5: 
                ellipse = cv2.fitEllipse(tracks[key]["obj_contour"])
                (xc,yc),(major_axis, minor_axis), angle = ellipse
            else: 
                # cannot calculate fitEllipse when contour is < 5
                major_axis = max(tracks[key]["obj_bbox"])
                minor_axis = min(tracks[key]["obj_bbox"] )

            match_error = tracks[key]["match_error"]
            
            # perimeter = cv2.arcLength(contours_i[0],True)
            # ellipse = cv2.fitEllipse(contours_i[0])
            # (xc,yc),(major_axis, minor_axis), angle = ellipse
            # ferret_x, ferret_y = np.where(mask>0)

            item = {
                "track_idx": track_idx,
                "frame_idx": frame_idx,
                "obj_idx": obj_idx,
                "x_pos": cent[0], 
                "y_pos": cent[1], 
                "area": area*px_um_cal**2, 
                "major_axis": major_axis*px_um_cal,
                "minor_axis": minor_axis*px_um_cal,
                "match_error": match_error
             }
            
            items.append(item)
            
            if save_obj_img: 
                try: 
                    for im_type in ["obj_img", "obj_img_mask"]: 
                        img = tracks[key][im_type]
                        if not (np.array(img.shape) ==0).any(): 
                            cv2.imwrite(str(Path(obj_img_path).joinpath(f"{track_idx}-{frame_idx}-{obj_idx}.png")), img)
                except KeyError as e: 
                    None # image is not present - maybe not saved upstream
                
        df = pd.DataFrame(items)
        # summary stats
        df["area_mean"] = df.area.mean()
        df["major_axis_mean"] = df.major_axis.mean()
        df["minor_axis_mean"] = df.major_axis.mean()
        df["vel_x_inst"] = (df.x_pos.diff()*px_um_cal)/dt/1e3 # convert um/s to mm/s
        df["vel_x_mean"] = df.vel_x_inst.mean()

        df["vel_y_inst"] = (df.y_pos.diff()*px_um_cal)/dt/1e3 # convert um/s to mm/s
        df["vel_y_mean"] = df.vel_y_inst.mean()
        df["N_frames"] = len(df)
        
        # TODO: (!) angle calculation is incorrect
        cents = np.array([(item["x_pos"], item["y_pos"]) for item in items])
        angles = [angle_between(np.array([1,0]), cent) for cent in cents]
        
        df["angle"] = angles
        angle_mean = np.abs(df.angle.mean())
        df["angle_mean"] = angle_mean
        df["match_error_mean"] = df["match_error"][1:].mean()

        # criteria to exclude from summary
        if angle_mean > max_angle_dev: 
            continue
        if len(df) < min_frames_per_track: 
            continue
        
        dfx.append(df) # full output
    
    if len(dfx) == 0: 
        print(f"No tracks saved: {len(track_idxs)} tracks tested, but 0 remain after filters")
        return tracks, objs
    
    dfx = pd.concat(dfx)
    dfx.to_csv(f"{output_path}/full_output.csv")
    
    # filter the summary
    dft = dfx.groupby("track_idx").last().reset_index(drop=False)
    cols = [
        "track_idx", 
        "vel_y_mean", "vel_x_mean", 
        "minor_axis_mean", "major_axis_mean", 
        "area_mean", "angle_mean", 
        "match_error_mean", "N_frames"
    ]
    dft = dft[cols] # only some columns make sense 
    dft.to_csv(f"{output_path}/summary_output.csv")
    
    # write all the frames
    save_frames = False
    if save_frames: 
        path = Path(output_path).joinpath("frames")
        os.makedirs(path, exist_ok=True)
        
        frame_idxs = list(set([key[1] for key in tracks]))
        for frame_idx in frame_idxs: 
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            cv2.imwrite(str(output_path.joinpath(f"{str(path)}/{frame_idx:05d}.png")), frame)
    print(f"Output written to: {output_path}")

    return tracks, objs

def angle_between(v1, v2):
    """ angle between vectors v1 and v2 """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.degrees(np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)))

def unit_vector(vector):
    """  unit vector of the vector """
    # true divide error not solved in some cases
    return vector / np.linalg.norm(vector)
