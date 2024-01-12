"""
safas/linkers/linear_flocs/linker

The linker matches objects in a series of images.
The track formed is a list of objects. 
The linker algorithm is separate from track management.
Simple data structures (lists, dict) are preferred to classes. 
Functions that transform the data structures are preferred to class attributes.
Start with the simple case of matching by size and distance. 
Suitable for processing a recorded video, not a live video feed.

"""
from copy import deepcopy
#import uuid
#import json
#from pathlib import Path
#import sys
from dataclasses import dataclass

#import cv2
import numpy as np
from matplotlib import pyplot as plt
from rich import progress

PRINT_OBJ_INFO_FLAG = True

params = {
    "name": "kwargs", 
    "title": "Parameters",
    "type": "group", 
    "children": 
    [	
        {"name": "dist_max_filt", "title": "Filter close objects", "type":  "bool", "value": True},
        {"name": "dist_max_filt_m", "title": "Filter dist m", "type":  "float", "limits": [0, 3000], "value": 200},
        {"name": "dist_max_filt_k", "title": "FIlter dist k", "type":  "float", "limits": [0, 5], "value": 1.25},
        {"name": "dist_wt", "title": "Distance error weight", "type":  "float", "value": 1, "limits": [0, 100]},
        {"name": "dist_square", "title": "Dist error square", "type":  "bool", "value": True},
        {"name": "area_wt", "title": "Area error weight", "type":  "float", "value": 1, "limits": [0, 100]},
        {"name": "area_square", "title": "Area error square", "type":  "bool", "value": True,},
        {"name": "error_threshold", "title": "Error threshold", "type":  "float", "limits": [1, 1e6], "value": 1e3},

    ]
}

def setup(): 
    return None

@dataclass
class LinkerParams(): 
    dist_max_filt:bool=True
    dist_max_filt_m:int=200
    dist_max_filt_k:float=1.25
    dist_wt:float=1
    dist_square:bool=True
    area_wt:float=1
    area_square:bool=True
    error_threshold:float=1e3

def linker(tracks, objs, frame_idx, n_frames, obj_selection="none", linker_kwargs=None, **kwargs): 
    """ 
    custom linker algorithm.

    Parameters: 
        tracks (dict): tracks in dict with keys (track_idx, frame_idx) 
        objs (dict): objs in dict with keys frame_idx 
        frame_idx (int): index of image in video 
        n_frames (int): number of frames to track objects through

    Returns: 
        tracks, objs (perhaps modified in this function)
    """
    if linker_kwargs is None: 
        linker_params = LinkerParams() # apply the defaults
    else: 
        linker_params = LinkerParams(**linker_kwargs)

    if len(tracks) == 0: 
        next_track_idx = 1
    else:     
        next_track_idx = max(list(set([key[0] for key in list(tracks)]))) + 1

    for f_idx in progress.track(range(frame_idx, frame_idx+n_frames), description="[green] Linking objects", total=n_frames): 
        # tracks existing in prev. frame
        track_idxs = [key[0] for key in tracks if (key[1]==(f_idx-1))] 
        # match to objs in current frame: 
        if PRINT_OBJ_INFO_FLAG: 
            print(f"Tracks in current frame: {track_idxs}")
        for track_idx in track_idxs: 
            obj = tracks[(track_idx, f_idx-1)] # get last obj added to the track
            keys = ['track_idx','frame_idx', 'obj_area', 'obj_centroid']

            objs_current = objs[f_idx]
           
            if PRINT_OBJ_INFO_FLAG: 
                print(f"Last object added to track {track_idx} in previous frame:")
                print(f"\tObject with obj_idx: {obj['obj_idx']}:")
                for key in keys: 
                    print(f"\t{key}: {obj[key]}")
                print(f"{len(objs_current)} objects in current frame:")          
            for idx in objs_current: 
                print(f"\tObject with obj_idx: {objs[f_idx][idx]['obj_idx']}:")
                for key in keys: 
                    print(f"\t{key}: {objs[f_idx][idx][key]}")
            obj_idx, match_error = _match_obj_in_frame(obj, deepcopy(objs[f_idx]), linker_params=linker_params) # match obj this frame
            
            if PRINT_OBJ_INFO_FLAG: 
                if obj_idx is not None: 
                    print(f"Matched obj_idx: {obj_idx} with match_error: {match_error}")
                else: 
                    print(f"No object matched with obj_idx: {obj['obj_idx']}")
                    
            if obj_idx is not None:  
                obj_n = objs[f_idx][obj_idx]
                obj_n["track_idx"] = track_idx
                obj_n["match_error"] = match_error
                tracks[(track_idx, f_idx)] = obj_n # add matched object to the track
                objs[f_idx].pop(obj_idx) # remove this obj from objs  
            # else: no match, track is terminate
            
        # NOTE: integrate new object selection with linker so objects from f_idx may be linked in f_idx + 1
        if obj_selection == "auto": 
            obj_idxs = obj_selection_auto(objs[f_idx]) # see if any remaining objects match selection criteria
            for obj_idx in obj_idxs: 
                obj_n = objs[f_idx][obj_idx]
                obj_n["match_error"] = 0
                tracks[(next_track_idx, f_idx)] = obj_n # add selected object to new track
                objs[f_idx].pop(obj_idx)
                next_track_idx += 1

    return tracks, objs

def obj_selection_auto(objs):
    """ """ 
    # TODO set some critiera for tracking objects. for now, simply re-add all if in auto
    return list(objs)

def _match_obj_in_frame(obj, objs, linker_params): 
                # dist_max_filt=True, dist_max_filt_m=200, dist_max_filt_k=1.25,
                # dist_wt=1, dist_square=True, 
                # area_wt=1, area_square=True,
                # error_threshold=1e3):
    """ """  
    if linker_params is None: linker_params = LinkerParams() # apply the defaults
    
    if linker_params.dist_max_filt: 
        dist_max = linker_params.dist_max_filt_m*obj["obj_area"]**linker_params.dist_max_filt_k
        to_remove = []
        for obj_idx in objs: 
            obj_a = obj["obj_centroid"]
            obj_b = objs[obj_idx]["obj_centroid"]
            if np.linalg.norm(obj_a-obj_b) > dist_max: 
                to_remove.append(obj_idx)
        for obj_idx in to_remove: 
            objs.pop(obj_idx)
        if len(objs) == 0: 
            return None, None
    
    dists = np.array([np.linalg.norm(objs[obj_idx]["obj_centroid"] - obj["obj_centroid"]) for obj_idx in objs])
    areas = np.array([objs[obj_idx]["obj_area"] - obj["obj_area"] for obj_idx in objs])
    obj_idxs = np.array(list(objs))
    if PRINT_OBJ_INFO_FLAG: print(f"Dists: {dists}, Areas: {areas}")
    dists = dists*linker_params.dist_wt
    areas = areas*linker_params.area_wt
    
    if linker_params.dist_square: dists = dists**2
    if linker_params.area_square: areas = areas**2
    
    error = dists + areas
    if PRINT_OBJ_INFO_FLAG: print(f"Error: {error} (threshold={linker_params.error_threshold})")
    idx_min = np.argmin(error)
    if error[idx_min] < linker_params.error_threshold: 
        return obj_idxs[idx_min], error[idx_min]
    else: 
        return None, None
