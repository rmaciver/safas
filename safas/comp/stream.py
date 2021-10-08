#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

stream_control.py

control and acquisition of data streams
make connections to the GUI

M. R. MacIver, 16 Nov. 2019

notes:

1 **kwargs is oftened passed to catch signals passed when the QueueThreads
    module is used with an explicit slot or additional keyword arguments

"""
import os
import sys
from glob import glob
import importlib
import time

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from pathlib import Path

from safas.gui.viewer import TrackbarViewer
from safas.gui.trackpanel import TrackPanel
from safas.comp.handler import Handler
from safas.comp.qt_threads import QueueThreads
from safas.comp.setconfig import config_params, read_params, set_dirout
from safas import filters

class Stream(QObject):
    """
    these functions are controlled directly by the GUI or parameters file
    """
    stream_running_signal = pyqtSignal(bool, name="stream_running_signal")

    def __init__(self, parent=None, params=None, params_file=None, *args, **kwargs):
        super(Stream, self).__init__(*args, **kwargs)
        # setup params
        self.parent = parent

        # transfer to make reference consistent
        self.dt_height = parent.dt_height
        self.dt_width = parent.dt_width

        self.params = params
        self.params_file = params_file

        self.config()
        self.threadpool = QueueThreads()

        self.source = None
        self.running = False
        self.track_init = False
        self.viewer = None
        self.track_panel = None

    def list_filters(self):
        """ get short names of folders for import """
        filts = []

        for filt in dir(filters):
            # do not add dunder methods or filter functions module
            if '__' in filt:
                continue
            if filt == 'imfilters_module':
                continue
            filts.append(filt)

        return filts

    def config(self, params_file=None):
        """ update params from config file if necessary"""
        if params_file is not None:
            self.params_file = params_file

        self.params = config_params(params=self.params, params_file=self.params_file)

    def set_output(self, dir_name=None, folders=None):
        self.params = set_dirout(self.params, dir_name=dir_name, folders=folders)

    def setup(self):
        """
        take params from file or from gui, setup the data source
        """
        self.handler = Handler(parent=self)
        self.handler.status_update_signal.connect(self.parent.update_status)
        ret = self.handler.setup()

        return ret

    def view(self, index=None):
        """ setup the trackbar viewer """
        # assumes this has already been set in the Handler
        size = self.params['improcess']['img_dim']
        self.viewer = TrackbarViewer(parent=self, size=size, index=index)
        # outgoing signal from viewer
        self.viewer.frame_index_signal.connect(self.handler.get_frame)
        # incoming signal from handler
        self.handler.frame_signal.connect(self.viewer.update)
        self.viewer.next_frame()

    def track(self):
        """ track in GUI or headless mode """

        self.track_panel = TrackPanel(parent=self)

        self.track_panel.setup() # add the TrackLists in this step to access Stream

        # connect TrackPanel and Tracks objects to status box in main gui
        self.track_panel.status_update_signal.connect(self.parent.update_status)
        self.track_panel.tracks.status_update_signal.connect(self.parent.update_status)
        self.handler.status_update_signal.connect(self.parent.update_status)

        # allows a series of images to be processed through config.yml or
        self.handler.frame_finished_signal.connect(self.track_panel.tracks.wait_queue_finished)

        # this is the main control point in the tracking display and user input
        self.handler.process_finished_signal.connect(self.track_panel.tracks.handle)
        self.handler.tracker.display_frame_signal.connect(self.viewer.update)

    def restart_tracks(self):
        """ a more thorough restart of the objects """
        self.params['improcess']['running'] = False
        cf = self.handler.frame_index
        self.stop()
        self.track_panel.click_exit_track()
        self.setup()
        self.view(index=cf)
        self.track()
        self.viewer.next_frame()

    def close_viewer(self):
        """ close viewer """
        self.viewer.stop()

    def close_windows(self):
        if getattr(self, 'track_panel'):
            self.track_panel.click_exit_track()

    def stop(self):
        """ on exit and stop """
        self.params['improcess']['running'] = False

        if getattr(self, 'handler'):
            self.handler.stop()

        if getattr(self, 'viewer'):
            self.viewer.stop()
