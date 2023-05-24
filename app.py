"""

"""

import sys
import threading
from time import sleep
from pathlib import Path
from datetime import datetime
import queue
import functools

from PySide2 import QtWidgets, QtCore, QtGui

import flatten_dict

import safas
from safas.prints import print_app as print

DATETIME_FORMAT = "%Y-%m-%d-%H-%M-%S"

def timestamp(time_format=DATETIME_FORMAT): 
    return datetime.now().strftime(time_format)

def format_status_update(label, time_format=DATETIME_FORMAT):
    """ Textbox status for ui """
    return f"{timestamp(time_format=time_format)}:{label}"

class MainWindow(QtWidgets.QMainWindow):
    """ """
    toggle_controls_signal = QtCore.Signal(bool)

    def __init__(self):
        super().__init__()
        try: 
            self.resource_path = str(Path(__file__).absolute().parents[0])
            ui_file = str(Path(self.resource_path).joinpath("ui/main.ui")) # load ui
            safas.loader_util.loadUi(ui_file, self)
        except Exception as e: 
            print(f"ui not loaded: {e}", error=True)
            return None
        self.installEventFilter(self) # custom close event

        self.handler = safas.handler.Handler() 

        self.viewer = safas.qtviewer.Viewer(parent=self, layout=self.layout_video)
        self.viewer.frame_idx_change.connect(self.build_frame) 

        self.params = safas.qtparams.ParamsView(parent=self, layout=self.layout_params)
        
        # image interaction
        self.handler.qt_interactor.frame_ready_signal.connect(self.viewer.update_frame)
        self.handler.qt_interactor.frame_count_signal.connect(self.viewer.set_slider_range)
        self.handler.qt_interactor.frame_idx_signal.connect(self.viewer.update_frame)

        # parameters syncing
        self.handler.qt_interactor.ui_params_update_signal.connect(self.params.sync_from_ext)
        self.handler.qt_interactor.ui_params_child_signal.connect(self.params.insert_child_group)
        
        self.params.params_update_signal.connect(self.handler.update_params) 
        self.params.data_file_signal.connect(self.handler.load_source) 
        
        self.params.p.param("labeler","common","name").sigValueChanged.connect(functools.partial(self.handler.load_node, "labeler"))
        self.params.p.param("linker","common","name").sigValueChanged.connect(functools.partial(self.handler.load_node, "linker"))
        self.params.p.param("writer","common","name").sigValueChanged.connect(functools.partial(self.handler.load_node, node_name="linker"))

        # self.params.p.param("screencap","common","get_cap").sigActivated.connect(self.get_screencap)
        # avoid passing all ui params to TrackTab - connect out here
        self.tracktab = TrackTab(parent=self, 
                                 button_remove_track=self.button_remove_track,
                                 button_remove_all_tracks=self.button_remove_all_tracks,
                                 button_add_object=self.button_add_object,
                                 button_add_all_objects=self.button_add_all_objects,
                                 list_tracks=self.list_tracks,
                                 list_objects=self.list_objects
                                )
        self.tracktab.ui_add_objs_signal.connect(self.viewer.add_objs)
        self.tracktab.ui_add_tracks_signal.connect(self.viewer.add_tracks)
        self.tracktab.ui_del_objs_signal.connect(self.viewer.del_objs)
        self.tracktab.ui_del_tracks_signal.connect(self.viewer.del_tracks)
        self.handler.qt_interactor.update_lists_signal.connect(self.tracktab.update_lists)
        
        self.control_buttons = ["button_step_forward", "button_reprocess", 
                                "button_step_back", "button_reprocess",
                                "button_save","button_compile", 
                                "radio_linking", "radio_labeling"]
        
        self.setup_control_buttons()
        self.button_compile.clicked.connect(self.handler.compile_outputs)
        self.radio_process.clicked.connect(self.activate_radio)
        # startup macro
        self.handler.load_params()
        self.handler.load_node("labeler")
        self.handler.load_node("linker")
        self.handler.load_node("writer")

    def eventFilter(self, obj, event):
        if obj is self and event.type() == QtCore.QEvent.Close:
            self.handler.write_config()
            self.handler.write_params()
            return True
        return super(MainWindow, self).eventFilter(obj, event)

    def activate_radio(self, v): 
        [self.params.p.param(key,"common","process").setValue(v) for key in ["labeler","linker"]]
  
    @QtCore.Slot(int)
    def build_frame(self, frame_idx):
        self.toggle_controls_signal.emit(False)
        self.handler.build_frame(frame_idx) 
        self.toggle_controls_signal.emit(True)

    # ---- behaviour of buttons below image viewer
    def setup_control_buttons(self): 
        """ """
        buttons = ["button_step_back", 
                "button_step_forward",
                "button_reprocess",
                "button_save"]
        
        icons = ["ui/control-stop-180.png",
                "ui/control-stop.png",
                "ui/arrow-circle-225.png",
                "ui/disk--arrow.png",
                ]
        
        for b, ic in zip(buttons, icons): 
            icon = QtGui.QIcon(str(Path(self.resource_path).joinpath(ic)))
            button = getattr(self, b)
            button.setIcon(icon)
            button.clicked.connect(getattr(self, b.split("button_")[-1]))

    def step_back(self):
        """ """ 
        self.params.p.param("labeler","common","process").setValue(False)
        self.params.p.param("linker","common","process").setValue(False)
        self.viewer.inc_video_index(-1)
    
    def step_forward(self): self.viewer.inc_video_index(1)
    def reprocess(self): self.handler.relabel_frame()
    def save(self): self.handler.save_tracks()

class TrackTab(QtCore.QObject): 
    """ """
    ui_add_tracks_signal = QtCore.Signal(int, int, bool)
    ui_add_objs_signal = QtCore.Signal(int, int, bool)
    ui_del_tracks_signal = QtCore.Signal(int, int)
    ui_del_objs_signal = QtCore.Signal(int, int)

    def __init__(self,
                parent,
                button_remove_track,
                button_remove_all_tracks,
                button_add_object,
                button_add_all_objects,
                list_tracks,
                list_objects,
                **kwargs): 
        super(TrackTab, self).__init__(parent) # is this necessary? 
        self.parent = parent # allow access to handler
        self.button_remove_track = button_remove_track
        self.button_remove_all_tracks = button_remove_all_tracks
        self.button_add_object = button_add_object
        self.button_add_all_objects = button_add_all_objects

        self.list_tracks = list_tracks
        self.list_objs = list_objects

        self.button_add_object.clicked.connect(self.add_obj_to_track)
        self.button_add_all_objects.clicked.connect(self.add_all_objs)

        # NOTE: (!) using functools to ensure kwarg is being passed, resetting to False always for some reason
        self.button_remove_track.clicked.connect(functools.partial(self.remove_track, rebuild_frame=True))
        self.button_remove_all_tracks.clicked.connect(self.remove_all_tracks)
        self.list_objs.itemDoubleClicked.connect(self.add_obj_to_track)

        
        ic_kwargs = dict(setHighlight=True, setVisible=True, addNew=False)
        self.list_objs.currentItemChanged.connect(self.highlight_obj)
        self.list_tracks.currentItemChanged.connect(self.highlight_track)

        self.hl_obj_blocker = QtCore.QSignalBlocker(self.list_objs)
        self.hl_obj_blocker.unblock()
        self.hl_track_blocker = QtCore.QSignalBlocker(self.list_tracks)
        self.hl_track_blocker.unblock()

    @QtCore.Slot(int)
    def update_lists(self, frame_idx, **kwargs): 
        
        self.hl_obj_blocker.reblock()
        self.hl_track_blocker.reblock()

        self.frame_idx = frame_idx
        [self.list_objs.takeItem(0) for i in range(self.list_objs.count())]
        [self.list_tracks.takeItem(0) for i in range(self.list_tracks.count())]
            
        track_idxs, obj_idxs = self.parent.handler.get_items_in_frame(frame_idx)
        obj_idxs = sorted(obj_idxs)
        track_idxs = sorted(track_idxs)

        if len(obj_idxs) > 0: 
            self.list_objs.addItems([str(idx) for idx in obj_idxs])

        if len(track_idxs) > 0: 
            self.list_tracks.addItems([str(idx) for idx in track_idxs])

        self.hl_obj_blocker.unblock()
        self.hl_track_blocker.unblock()

    def remove_track(self, rebuild_frame=True, **kwargs): 
        track_idx = self.list_tracks.currentItem()
        
        if track_idx is None: return None 
        
        row = self.list_tracks.currentRow()

        track_idx = int(track_idx.text())
        self.parent.handler.remove_track(track_idx)
        item = self.list_tracks.takeItem(self.list_tracks.currentRow()) 
        self.ui_del_tracks_signal.emit(self.frame_idx, track_idx)

        if rebuild_frame: self.parent.handler.rebuild_frame()

        self.list_tracks.setCurrentRow(max(0, row-1))

    def remove_all_tracks(self, **kwargs): 
        total = self.list_tracks.count()
        for i in range(total): 
            self.list_tracks.setCurrentRow(0)
            self.remove_track(rebuild_frame=False)
        
        self.parent.handler.rebuild_frame()

    def add_all_objs(self): 
        total = self.list_objs.count()
        for i in range(total): 
            self.list_tracks.setCurrentRow(0)
            self.add_obj_to_track()

    def add_obj_to_track(self): 
        """ """
        self.hl_obj_blocker.reblock()
        self.hl_track_blocker.reblock()
  
        obj_idx = self.list_objs.currentItem()
        if obj_idx is None: return None
        
        row = self.list_objs.currentRow()
        obj_idx = int(obj_idx.text())
 
        # remove object
        self.ui_del_objs_signal.emit(self.frame_idx, obj_idx)
        track_idx = self.parent.handler.add_obj_to_track(frame_idx=self.frame_idx, obj_idx=obj_idx)
        self.list_objs.takeItem(self.list_objs.currentRow()) # removed from the UI

        # update qtviewer
        setHighlight = False
        self.ui_add_tracks_signal.emit(self.frame_idx, track_idx, setHighlight) 
        self.list_tracks.addItems([str(track_idx)]) # update lists

        self.hl_obj_blocker.unblock()
        self.hl_track_blocker.unblock()
        self.list_objs.setCurrentRow(max(0, row-1))

    def highlight_obj(self): 
        """ """
        obj_idx = self.list_objs.currentItem()
        if obj_idx is None: return None
        obj_idx = int(obj_idx.text())
        self.ui_add_objs_signal.emit(self.frame_idx, obj_idx, True) 

    def highlight_track(self): 
        """ """
        track_idx = self.list_tracks.currentItem()
        if track_idx is None: return None
        track_idx = int(track_idx.text())
        self.ui_add_tracks_signal.emit(self.frame_idx, track_idx, True)

if __name__ == "__main__": 
    # entry point
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow() 
    window.show()
    app.exec_()