"""
safas/handler.py

Prepare an image analysis pipline to label and 
    link objects in a series of images
"""
import json
from pathlib import Path
import shutil
import time
from copy import deepcopy
import multiprocessing
import os
from datetime import datetime
import pickle
import numpy as np

import cv2
import pandas as pd

import filetype
import flatten_dict
import rich
from rich import progress

from .prints import print_handler as print
from . import labeler_worker

from .labelers.edge_gradient import labeler as edge_gradient
from .linkers.linear_flocs import linker as linear_flocs
from .writers.sed_exp import writer as sed_exp

labeler_modules = {"edge_gradient": edge_gradient,}
linker_modules = {"linear_flocs": linear_flocs}
writer_modules = {"sed_exp": sed_exp}

DEFAULT_CONFIG = {"output_path": None, "auto_reload": True}
USE_QT = True

from PySide2 import QtCore

class QtInteractor(QtCore.QObject): 
    """ Permit minimal connection with QT ui from the handler"""
    frame_ready_signal = QtCore.Signal(dict)
    frame_count_signal = QtCore.Signal(int, int)
    frame_idx_signal = QtCore.Signal(int)
    update_lists_signal = QtCore.Signal(int) # signal is frame_idx
    ui_params_update_signal = QtCore.Signal(dict)
    ui_params_child_signal = QtCore.Signal(str, dict)
    ui_video_loaded_signal = QtCore.Signal(bool)
    toggle_process_signal = QtCore.Signal(bool)

    def update_qt_node_params(self, node_name, key, params_list): 
        try: 
            if USE_QT: 
                self.ui_params_child_signal.emit(node_name, {key: params_list})
        except KeyError as e:
            print(f"key {node_name} not in user_params")
        except Exception as e: 
            print(f"child parameter group {node_name} not emitted from qt_interactor: {e}", error=True)
  
class Node(): 
    pass

class SyncedDict(dict):
    """ Dict that emits a callback when updated"""
    def __init__(self, parent): 
        self.parent = parent
    def __setitem__(self, item, value):
        super(SyncedDict, self).__setitem__(item, value)        
        try: 
            out = {item:value}
            self.parent.qt_interactor.ui_params_update_signal.emit(out)
        except Exception as e: 
            print(f"qt_interactor.ui_params_signal not emitted: {e}")

class Handler(QtCore.QObject): 
    
    def __init__(self, parent=None, layout=None):
        super(Handler, self).__init__(parent)

        if USE_QT: 
            self.params = SyncedDict(parent=self) # auto-update external dict on UI
            self.qt_interactor = QtInteractor()
        else: 
            self.params = dict()
            self.qt_interactor = None

        self.objs = dict()
        self.tracks = dict() 
        self.annotations = dict()
        self.next_track_idx = 1
        self.config = None
        self.cap = None
        self.linker = None
        self.labeler = None

        try: 
            config_file = "config/config.json"
            self.config = load_json(config_file) # config always stored here...
            print(f"Config loaded from {config_file}")
        except Exception as e: 
            print(f"Config not loaded from file {e}", warn=True)
            
        if self.config is None: 
            with open(config_file, "w") as f: json.dump(DEFAULT_CONFIG, f)
            self.config = DEFAULT_CONFIG
            print(f"Default config loaded")

    def load_params(self, filename=None, display_params=False): 
        """ """
        user_params = None # try loading params from various locations
        loc = None
        
        if (filename is not None) & (filename != ""): 
            user_params = self._load_p(filename)
            loc = "user"
   
        if (user_params is None) & (self.config["output_path"] is not None):
            filename = str(Path(self.config["output_path"]).joinpath("_last_params.json"))
            user_params = self._load_p(filename)
            loc = self.config["output_path"]
       
        if user_params is None: 
            user_params = self._load_p("config/_last_params.json")
            loc = "config/_last_params.json"

        if user_params is None: 
            user_params = self._load_p("config/params.json")
            loc = "config/params.json"
        
        if user_params is None: 
            print(f"Params not loaded from locations available. Please select another params.json file", warning=True)
            return None

        print(f"Loaded params from {loc}")
        # NOTE: store labeler, linker, writer kwargs as class attribute until UI setup
        for node_name in ["labeler", "linker", "writer"]: 
            try: 
                setattr(self, f"{node_name}_kwargs", user_params[node_name]["kwargs"])
                user_params[node_name].pop("kwargs")
            except Exception as e: 
                print(f"{node_name} had no kwargs {e}")

        # NOTE: params as flattened dictionary with tuple keys in most places 
        try: 
            user_params = flatten_dict.flatten(user_params)
        except Exception as e: 
            print(f"Could not flatten params dict: {e}")
            return None
        
        # NOTE: avoid changing SyncedDict type this way
        for key in user_params: self.params[key] = user_params[key] 

        self.clear_all_tracks() 
        self.clear_all_objs()
        
    def _load_p(self, filename): 
        try: 
            user_params = load_json(filename)
            if len(user_params) == 0: user_params = None    
        except Exception as e: 
            print(f"Params not loaded from {filename}, {e}")
            user_params = None
        finally: 
            return user_params
        
    def load_source(self, data_file=None, display=False, **kwargs): 
        """ load data source"""
        
        if data_file is None:
            try:  
                data_file = self.params[("io","data_file")]
            except KeyError as e: 
                if len(self.params) == 0: 
                    print(f"Params not loaded")
                    self.qt_interactor.ui_video_loaded_signal.emit(False)
                    return None
                else: 
                    print(f"Verify key data_file is in params")
                    self.params[("io", "data_file",)] = "<source filename>"
                    self.qt_interactor.ui_video_loaded_signal.emit(False)
                    return None
            except Exception as e: 
                self.qt_interactor.ui_video_loaded_signal.emit(False)
                print(f"Error: {e}")

        if (data_file is None) | (data_file == "") | (data_file == 0): 
            self.qt_interactor.ui_video_loaded_signal.emit(False)
            print(f"[cyan]Source[/cyan] No data file selected")
            return None
        
        supported = ['video/x-msvideo']  #TODO: decide which loader to used based on file content
        kind = filetype.guess(data_file)

        if kind is None:
            print(f'[cyan]Source[/cyan] cannot determine file type of {data_file}')
            self.qt_interactor.ui_video_loaded_signal.emit(False)
            return None
        else: 
            print(f'[cyan]Source[/cyan] file extension: {kind.extension}, MIME type: {kind.mime}')
            if kind.mime == "video/x-msvideo": 
                self.cap = load_video(data_file)
                width, height, fps, frame_count = get_video_frame_details(self.cap) 
                if USE_QT: 
                    try: 
                        self.qt_interactor.frame_count_signal.emit(0, frame_count)
                        self.qt_interactor.ui_video_loaded_signal.emit(True)
                    except Exception as e: 
                        print(f"Frame count not emitted by qt_interactor: {e}")
                self.build_frame(0) # default beginning of file
            else: 
                print(f"Supported MIME types: {supported} ")
                self.qt_interactor.ui_video_loaded_signal.emit(False)

    def load_node(self, node_name, *args, **kwargs): 
        """ Load function and parameters for LABELER or LINKER"""
        available = ["labeler", "linker", "writer"]
        
        if node_name not in available: 
            print(f"node_type {node_name} not in {available}", error=True)
            return None
        
        try: 
            func_name = self.params[(node_name, "common", "name")]
            params_file = self.params[(node_name, "common", "params_file")]
        except Exception as e: 
            print(f"{node_name} func_name and file_name not loaded: {e}")
        
        try: 
            setup, func, params_list, errors = self.load_node_module(func_name, node_name)

            if len(errors) > 0: 
                print(f"One or more {node_name} attributes not loaded:", warning=True)
                [print(f"{ky}: {errors[ky]}",error=True) for ky in errors]
                return None
        except Exception as e: 
            print(f"{node_name} node not loaded: {e}")
            return None
        
        setattr(self, node_name, Node()) # NOTE: option for custom Node setup

        try: 
            setattr(getattr(self, node_name), "setup", setup)
            setattr(getattr(self, node_name), "func", func)
            setattr(getattr(self, node_name), "name", func_name)
            print(f"[cyan]{node_name.title()}[/cyan] [dark_green]{func_name}[/dark_green] registered")
        except Exception as e: 
            print(f"Labeler {func_name} not registered: {e}", error=True)

        # automatically updates shared params
        if USE_QT: self.qt_interactor.update_qt_node_params(node_name, "kwargs", params_list) 
        
        try: # reload node kwargs from state if available
            node_kwargs = getattr(self, f"{node_name}_kwargs") # these are in dict format
        except Exception as e: 
            print(f"{node_name} kwargs not recovered from state, module defaults will be used")
            node_kwargs = dict()
            for item in params_list["children"]: 
                node_kwargs[item["name"]] = item["value"] 
        
        to_remove = [] # remove the existing node_kwargs
        for key in self.params: 
            if len(set((node_name, "kwargs")).difference(set(key))) == 0: 
                to_remove.append(key)
        [self.params.pop(key) for key in to_remove]
       
        for key in node_kwargs:  # update node_kwargs on shared params now
            self.params[(node_name, "kwargs", key)] = node_kwargs[key]

    def load_node_module(self, func_name, node_type): 
        """ Load function by name from safas.labelers or safas.linkers
        
        Parameters: 
        ----------
            filter_name, str: name of filter to retreive
        
        Returns: 
        ----------
            setup, function: called on filter setup (eg load required model)
            filter, function: called during image processing
            params_list, list: parameters for pg.ParameterTree and pg.Parameter    

        Note:
        ----------
            filter_name must have been loaded to filters globals during __init__ 
        """
        errors = dict()
        
        try: 
            mod = globals()[f"{node_type}_modules"][func_name] 
        except Exception as e: 
            mod = None
            errors["module"] = e
        
        try: 
            func = getattr(mod, node_type)
        except Exception as e: 
            func = None
            errors[f"{node_type}.{node_type}"] = e

        try: 
            setup = mod.setup
        except Exception as e: 
            setup = None
            errors[f"{node_type}.setup"] = e
        
        try: 
            params_list = mod.params
        except Exception as e: 
            params_list = None
            errors[f"{node_type}.params"] = e
        
        return (setup, func, params_list, errors)

    def build_frame(self, frame_idx):  
        """Assemble frame at given index for front-end"""
        if self.cap is None: 
            print(f"[cyan]Source[/cyan] not loaded", warning=True)   
            return None

        process_on_new_frame = self.params[("io","process_on_new_frame")]
        process_n_frames = self.params[("io", "process_n_frames")]

        if process_on_new_frame & process_n_frames: 
            raise ValueError("Only one of process_on_new_frame or process_n_frames can be true")    

        if self.params[('labeler','common','process')] & (self.labeler is not None): 
            try: 
                if self.params[("labeler", "common","process")]: 
                    vi = self.run_labeler(image_index=frame_idx, 
                                    process_on_new_frame=process_on_new_frame, 
                                    process_n_frames=process_n_frames, 
                                    display_table=True)
                else: 
                    vi = frame_idx
            except AttributeError as e: 
                print(f"[cyan]Labeler[/cyan] error: {e}", errror=True)
                vi = frame_idx
        else: 
            vi = frame_idx

        if self.params[('linker','common','process')] & (self.linker is not None): # Linker
            try: 
                obj_selection = self.params[("linker","common", "obj-select-mode")]
                if self.params[("linker", "common", "process")]: 
                    self.run_linker(frame_idx=frame_idx, 
                                process_on_new_frame=process_on_new_frame, 
                                process_n_frames=process_n_frames, 
                                obj_selection=obj_selection
                    )
            except AttributeError as e: 
                print(f"[cyan]Linker[/cyan] error: {e}", errror=True)
        
        try:  # Update to latest frame
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, vi)
            result, image = self.cap.read()
        except Exception as e: 
            print(f"Could not get image from cap: {e}")

        tracks_an = self.build_tracks_an(vi)     
        objs_an = self.build_obj_an(vi)
     
        self.latest_frame = {"raw_image": image, "objs_an": objs_an, "tracks_an": tracks_an, "frame_idx": vi}
        
        if USE_QT: 
            try: 
                self.qt_interactor.frame_ready_signal.emit(self.latest_frame) # TODO: may optimize with a queue
            except Exception as e:  
                print(f"Did not emit frame via frame_read_signal: {e}")
            self.qt_interactor.update_lists_signal.emit(vi)
            if process_n_frames: 
                self.qt_interactor.toggle_process_signal.emit(False)
        else: 
            return self.latest_frame
        
    def run_labeler(self, 
                    image_index=None, 
                    process_on_new_frame=True, 
                    process_n_frames=False, 
                    display_table=True): 
        """
        Parameters:
        --------
            image_index (int): index of the image in video cap to analyze
            display_table (bol): show table of N objects detected per frame
        """
        try: 
            cap = self.cap
        except Exception as e: 
            print(f"Could not get video cap from state: {e}.", error=True)
            return None
        
        if process_n_frames:  
            n_frames = self.params[("io", "n_frames")] 
            x1, x2 = image_index, image_index + n_frames -1 
            x2 = min(x2, int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            n_threads = multiprocessing.cpu_count() - 1 
        elif process_on_new_frame: 
            n_frames = 1
            x1, x2 = image_index, image_index
            n_threads = 1
        
        print(f"[cyan]Labeler[/cyan] [dark_green]{self.labeler.name}[/dark_green] on {n_frames} images from {x1} to {x2} with {n_threads} threads")
        start = time.perf_counter()

        try:  
            labeler_kwargs = flatten_dict.unflatten(self.params)["labeler"]["kwargs"]
        except Exception as e: 
            print(f"labeler kwargs not loaded from params: {e}")
        
        # TODO: run in thread and release UI
        objs = labeler_worker.run_labeler(self.cap, x1, x2, n_threads, self.labeler.func, labeler_kwargs)
        self.objs.update(objs)
        finish = time.perf_counter()
      
        if display_table:  
            table = rich.table.Table(title="Objects labeled per image")
            table.add_column("Image index", justify="right", style="cyan", no_wrap=True)
            table.add_column("N Objects", style="magenta")
            
            disp_results = [] 
            [disp_results.append((str(frame_idx), str(len(self.objs[frame_idx])))) for frame_idx in range(x1, x2+1)]
            
            max_results = 10
            if len(disp_results) > max_results*2: 
                disp_results = disp_results[:max_results] + [("...", "...")] + disp_results[-max_results:]
    
            [table.add_row(item[0], item[1]) for item in disp_results]
            console = rich.console.Console()
            console.print(table)

        print(f"Processed {n_frames} images in {finish-start:0.1f} second(s)") 
        return x2

    def run_linker(self,
            frame_idx=None, 
            process_on_new_frame=True, 
            process_n_frames=False, 
            obj_selection="none",
            display_table=True): 
        """ """
        if process_n_frames:  
            x1, x2 = frame_idx, frame_idx + self.params[("io", "n_frames")] 
            x2 = min(x2, int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            n_threads = self.params[("io","n_threads")]    
        elif process_on_new_frame: 
            x1, x2 = frame_idx, frame_idx + 1
            n_threads = 1
        
        print(f"[cyan]Linker[/cyan] [dark_green]{self.linker.name}[/dark_green] on {x2-x1} images from {x1} to {x2-1} with {n_threads} threads")
        start = time.perf_counter()
        
        try:  
            linker_kwargs = flatten_dict.unflatten(self.params)["linker"]["kwargs"]
        except Exception as e: 
            print(f"linker kwargs not loaded from params: {e}")

        self.tracks, self.objs = self.linker.func(tracks=self.tracks, 
                                                    objs=self.objs, 
                                                    frame_idx=frame_idx, 
                                                    n_frames=x2-x1, 
                                                    obj_selection=obj_selection,
                                                    **linker_kwargs) 
        
        if display_table:  
            table = rich.table.Table(title="Active tracks per image")
            table.add_column("Image index", justify="right", style="cyan", no_wrap=True)
            table.add_column("N tracks", style="magenta")
            
            disp_results = [] 
            for frame_idx in range(x1, x2): 
                track_idxs, obj_idxs = self.get_items_in_frame(frame_idx)
                disp_results.append((str(frame_idx), str(len(track_idxs))))
      
            max_results = 10
            if len(disp_results) > max_results*2: 
                disp_results = disp_results[:max_results] + [("...", "...")] + disp_results[-max_results:]
    
            [table.add_row(item[0], item[1]) for item in disp_results]
            
            console = rich.console.Console()
            console.print(table)
        
        print(f"Object linking complete")

    def add_obj_to_track(self, frame_idx, obj_idx): 
        """ """
        track_idx = self.next_track_idx
        obj = self.objs[frame_idx][obj_idx] # removed from open objs
        obj["track_idx"] = track_idx
        obj["match_error"] = 0
        self.tracks[(track_idx, frame_idx)] = obj
        self.next_track_idx += 1
        self.objs[frame_idx].pop(obj_idx)
        return track_idx

    def clear_all_objs(self): 
        self.objs = dict()

    def clear_all_tracks(self, ): 
        track_idxs = list(set([k[0] for k in self.tracks]))
        for track_idx in track_idxs: 
            self.remove_track(track_idx)  # dict() # TODO: add confirm before doing this

    def remove_track(self, track_idx): 
        """ """
        keys = [key for key in self.tracks if (key[0]==(track_idx))]
        
        for track_idx, frame_idx in keys: # put objs back into data structure
            obj = self.tracks[(track_idx, frame_idx)]
            obj_idx = obj["obj_idx"]
            self.objs[frame_idx][obj_idx] = obj
            self.tracks.pop((track_idx, frame_idx)) 

    def update_params(self, new_params): 
        """ """
        if USE_QT: self.qt_interactor.blockSignals(True) 
        self.params.update(flatten_dict.flatten(new_params))
        self.config["output_path"] = self.params[("io", "output_path")]
        if USE_QT: self.qt_interactor.blockSignals(False) 
        
    def set_frame_idx(self, v): 
        """ """
        if USE_QT: 
            try: 
                self.qt_interactor.frame_idx_signal.emit(v)
            except Exception as e: 
                print(f"Frame index not emitted by qt_interactor: {e}")
        
    def relabel_frame(self): self.rebuild_frame(setLabelerOn=True) 

    def get_items_in_frame(self, frame_idx): 

        track_idxs = list(set([l[0] for l in list(self.tracks.keys()) if l[1]==frame_idx]))

        try: 
            obj_idxs = list(self.objs[frame_idx])
        except KeyError as e: 
            obj_idxs = list()

        return track_idxs, obj_idxs

    def build_tracks_an(self, frame_idx, track_idxs=None):
        """ """ 
        # NOTE: want tracks upt to previous frame
        params_t = deepcopy(flatten_dict.unflatten(self.params)["display"])
        tracks_an = {"tracks": dict(), "kwargs": params_t["tracks"]} 
        
        if (not params_t["tracks"]["show_lines"]) & (not params_t["tracks"]["show_objs"]):  
            tracks_an = None
        else: 
            if track_idxs is None: 
                track_idxs = list(set([l[0] for l in self.tracks if l[1] <=(frame_idx)]))

            if isinstance(track_idxs, int): 
                track_idxs = [track_idxs]

            if len(track_idxs) == 0: 
                return None
            
            for track_idx in track_idxs:   
                keys = [key for key in self.tracks if ((key[0]==track_idx) & (key[1]<=(frame_idx)))]
       
                if params_t["tracks"]["show_lines"]: 
                    centroids = np.array([self.tracks[key]["obj_centroid"] for key in keys])
                else: 
                    centroids = None
                
                if params_t["tracks"]["show_objs"]: 
                    contour = [self.tracks[key]["obj_contour"] for key in keys]
                else: 
                    contour = None

                item ={"obj_contour": contour,"obj_centroid": centroids}
                tracks_an["tracks"][track_idx] = item

        return tracks_an
    
    def build_obj_an(self, frame_idx, obj_idxs=None): 
        """ """
        params_t = deepcopy(flatten_dict.unflatten(self.params)["display"])
        objs_an = {"objs": dict(), "kwargs": params_t["objects"]}
        
        if frame_idx not in self.objs: return None
        
        if params_t["objects"]["show"]:
            if obj_idxs is None: obj_idxs = list(self.objs[frame_idx])
            if isinstance(obj_idxs, int): obj_idxs = [obj_idxs]

            for obj_idx in obj_idxs: 
                item = {"obj_contour": self.objs[frame_idx][obj_idx]["obj_contour"]}
                objs_an["objs"][obj_idx] = item
        return objs_an
  
    def save_tracks(self): 
        if self.cap is None: 
            print(f"[cyan]Source[/cyan] not loaded", warning=True)   
            return None
        
        try:  
            writer_kwargs = flatten_dict.unflatten(self.params)["writer"]["kwargs"]
        except Exception as e: 
            print(f"writer kwargs not loaded from params: {e}")
        
        output_path = self.params[("io", "output_path")]
        if (output_path is None) | (output_path == ""): 
            print(f"Please set the output_path before saving")
            return False
       
        os.makedirs(output_path, exist_ok=True)
        output_path = Path(output_path).joinpath(microtime())
        os.makedirs(output_path, exist_ok=True)

        self.tracks, self.objs, dft, dfx = self.writer.func(output_path, tracks=self.tracks, objs=self.objs, cap=self.cap, **writer_kwargs)
        
        clear_objs = writer_kwargs["clear_objs_on_save"]
        clear_tracks = writer_kwargs["clear_tracks_on_save"]
        
        if writer_kwargs["clear_tracks_on_save"]: 
            self.rebuild_frame(frame_idx=None, func=self.clear_all_tracks)

        if writer_kwargs["clear_objs_on_save"]:
            self.rebuild_frame(frame_idx=None, func=self.clear_all_objs) 

    def rebuild_frame(self, frame_idx=None, func=None, setLabelerOn=False, setLinkerOn=False): 
        if self.cap is None: 
            print(f"[cyan]Source[/cyan] not loaded", warning=True)   
            return None

        # basically allows annotations to be recreated without reprocessing
        la_rev = deepcopy(self.params[('labeler','common','process')]) 
        self.params[('labeler','common','process')] = setLabelerOn
        li_rev = deepcopy(self.params[('linker','common','process')])
        self.params[('linker','common','process')] = setLinkerOn
        
        nf_rev = deepcopy(self.params[("io","n_frames")])
        pf_rev = deepcopy(self.params[("io","process_on_new_frame")])

        self.params[("io","process_on_new_frame")] = True # should toggle the other to False
        self.params[("io","process_n_frames")] = False # should toggle the other to False
        self.params[("io","n_frames")] = 1 # if set to 1 + only rebuild one frame
        
        # run a function while processing is paused
        if func is not None: func() # TODO: permit passing args and kwargs
   
        if frame_idx is None: frame_idx = self.latest_frame["frame_idx"]
        self.build_frame(frame_idx)
        
        self.params[('labeler','common','process')] = la_rev # revert processing values
        self.params[('linker','common','process')] = li_rev
        self.params[("io","n_frames")] = nf_rev
        self.params[("io","process_on_new_frame")] = pf_rev
        self.params[("io","process_n_frames")] = not pf_rev

    def dump_labeled_frames(self, write_frames=True, **kwargs): 
        """ write all data to file"""
        # NOTE: was helpful during development
        write_frames = True # NOTE: (!) not working as a kwarg for some reason 
        if len(self.objs) == 0: 
            print(f"No data to write")
            return None
        
        output_path = self.params[("io", "output_path")]
        if (output_path is None) | (output_path == ""): 
            print(f"Please set the output_path before saving")
            return False

        os.makedirs(output_path, exist_ok=True)
        output_path = Path(output_path).joinpath(microtime())
        os.makedirs(output_path, exist_ok=True)

        monitor = progress.track(self.objs, description='[green] Saving objects & frames', total=len(self.objs))

        for frame_idx in monitor: 
            with open(str(output_path.joinpath(f"objs_in_frame_{frame_idx:05d}.obj")), "wb") as f: 
                pickle.dump(self.objs[frame_idx], f)
     
            if write_frames: 
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = self.cap.read()
                filename = str(output_path.joinpath(f"{frame_idx:05d}.png"))
                if frame is not None: 
                    cv2.imwrite(str(output_path.joinpath(f"{frame_idx:05d}.png")), frame)
        print(f"Objects and frames saved to: {output_path}")

    def compile_outputs(self, paths=None): 
        """ write all data to file"""
        lines = []
        # TODO: Move to writer module. merge is dependent on writer-specific formatting 
        output_path = self.params[("io", "output_path")]

        if (output_path is None) | (output_path == ""): 
            print(f"Please set the output_path before saving")
            return False

        os.makedirs(output_path, exist_ok=True)
        output_path = Path(output_path).joinpath(f"{microtime()}-merged")
        os.makedirs(output_path, exist_ok=True)
        print(f"Compiling outputs")

        if self.params[("writer","merge","merge_summary_files")]: 
            files = []
            for path in paths: 
                try: 
                    files.append(str(Path(path).joinpath("summary_output.csv")))
                except Exception as e: 
                    print(f"Summary file not located in {path}: {e}")
    
            if len(files) > 1: 
                df = pd.concat(pd.read_csv(file) for file in files)
            elif len(files) == 1: 
                df = pd.read_csv(files[0])
            elif len(files) == 0:     
                return None
            
            filename = f"{output_path}/summary_output_merged.csv"
            df.to_csv(filename)

            print(f"summary output: {len(df)} rows from {len(files)} files saved to {Path(filename).name}")

        if self.params[("writer","merge","merge_full_output_files")]: 
            files = []
            for path in paths: 
                try: 
                    files.append(list(Path(path).glob("*full_output.csv"))[0])
                except Exception as e: 
                    print(f"full output not located in {path}: {e}")
           
            if len(files) > 1: 
                df = pd.concat(pd.read_csv(file) for file in files)
            elif len(files) == 1: 
                df = pd.read_csv(files[0])
            elif len(files) == 0:     
                return None
            
            filename = f"{output_path}/full_output_merged.csv"
            df.to_csv(filename)
            print(f"full output: {len(df)} lines from {len(files)} files saved to {Path(filename).name}")

        if self.params[("writer","merge","merge_obj_images")]: 
            path = Path(output_path).joinpath("objs")
            os.makedirs(path, exist_ok=True)
            files = []
            for path in paths: 
                files.extend(list(Path(path).joinpath("objs").glob("*.png")))
            print(f"object images: found {len(files)} images")
            [shutil.copy(file, str(Path(output_path).joinpath("objs").joinpath(str(Path(file).name)))) for file in files]      
            print(f"object images: copied {len(files)} images")
            
        if self.params[("writer","merge","merge_frames")]:
            path = Path(output_path).joinpath("frames")
            os.makedirs(path, exist_ok=True)
            files = dict()
            for path in paths: 
                for name in Path(path).joinpath("frames").glob("*.png"): 
                    if name.name not in files: files[name.name] = str(name)
            
            print(f"frames: found {len(files)} images")
            [shutil.copy(files[name], str(Path(output_path).joinpath("frames").joinpath(name))) for name in files]
            print(f"frames: copied {len(files)} images")

        print(f"Data merge complete")

    def write_params(self, filename=None): 
        if filename is None: 
            output_path = self.params[("io","output_path")]
            if (output_path is not None) & (output_path != "") & (output_path!=0):
                filename = str(Path(self.params[("io","output_path")]).joinpath("_last_params.json"))
            else: 
                filename = "config/_last_params.json"

        try: 
            params_t = flatten_dict.unflatten(self.params)
            with open(filename, "w") as f: json.dump(params_t, f, indent=2)
            print(f"[cyan]Params[/cyan] written to {filename}")
            return True
        except Exception as e: 
            print(f"Parameters not written {Path(filename).name}: {e}", error=True)
            return False
        
    def write_config(self): 
        try: 
            filename = "config/config.json"
            with open(filename, "w") as f: json.dump(self.config, f)
            print(f"[cyan]Config[/cyan] written to {filename}")
        except Exception as e: 
            print(f"Config not written {Path(filename).name}: {e}", error=True)
    
def microtime()->str: return datetime.now().strftime("%Y-%m-%d-%H-%M-%SS.%f")

def load_json(filename, display_params=False): 
    try: 
        with open(filename, "r") as f:
            user_params = json.load(f)
        return user_params
    except Exception as e: 
        print(f"Params not loaded from {filename}: {e}")
        return None

def get_video_frame_details(cap): 

    try: 
        width, height, fps, frame_count = (
                int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                float(cap.get(cv2.CAP_PROP_FPS)),
                int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        )
    except Exception as e: 
        print(f"Could not get video cap properties", error=True)   
    
    return (width, height, fps, frame_count)

def load_video(data_file): 
    """ """
    try: 
        cap = cv2.VideoCapture(data_file)
        try: 
            ret, out = cap.read() 
            print(f"[cyan]Video[/cyan] loaded: {data_file}")
            return cap
        except Exception as e: 
            print(f"[cyan]Video[/cyan] not loaded: {data_file}: {e}")
            return None      
    except Exception as e: 
        print(f"[cyan]Video[/cyan] not loaded: {data_file}: {e}")
        return None