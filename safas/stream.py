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

from safas.viewer import TrackbarViewer
from safas.trackpanel import TrackPanel
from safas.handler import Handler
from safas.qt_threads import QueueThreads
from safas.config import config_params, read_params, set_dirout
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
        self.params = params
        self.params_file = params_file

        self.config()
        self.threadpool = QueueThreads()

        self.source = None
        self.running = False
        self.track_init = False

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

    def config(self):
        """ update params from config file if necessary"""
        # params path should be relative to the main package in params directory
        self.params = config_params(params=self.params, params_file=self.params_file)

    def set_output(self):
        self.params['output'] = set_dirout(self.params)

    def setup(self):
        """
        take params from file or from gui, setup the data source
        """
        self.handler = Handler(parent=self)
        self.handler.setup()

    def view(self):
        """ setup the trackbar viewer """
        # assumes this has already been set in the Handler
        size = self.params['improcess']['img_dim']
        self.viewer = TrackbarViewer(parent=self, size=size)
        # outgoing signal from viewer
        self.viewer.frame_index_signal.connect(self.handler.get_frame)
        # incoming signal from handler
        self.handler.frame_signal.connect(self.viewer.update)

    def update_params(self, **kwargs):
        """ """

    def track(self):
        """ track in GUI or headless mode """
        self.track_panel = TrackPanel(parent=self)
        self.track_panel.setup() # add the TrackLists in this step to access Stream

        # connect TrackPanel and Tracks objects to status box in main gui
        self.track_panel.status_update_signal.connect(self.parent.update_status)
        self.track_panel.tracks.status_update_signal.connect(self.parent.update_status)
        self.handler.status_update_signal.connect(self.parent.update_status)
        
        # this is the main control point in the tracking display and user input
        self.handler.process_finished_signal.connect(self.track_panel.tracks.handle)
        self.handler.tracker.display_frame_signal.connect(self.viewer.update)

    def stop(self):
       self.handler.stop()
       self.viewer.stop()
       self.threadpool.clear()
