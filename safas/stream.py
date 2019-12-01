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

import importlib
import time

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from pathlib import Path

import safas
from safas.viewer import TrackbarViewer
from safas.trackpanel import TrackPanel
from safas.handler import Handler
from safas.qt_threads import QueueThreads
from safas.config import config_params, read_params, set_dirout


__author__ = 'Ryan MacIver'
__copyright__ = 'Copyright 2019'
__credits__ = ['Ryan MacIver']
__license__ = 'MIT'
__version__ = '0.0.1'
__maintainer__ = 'Ryan MacIver'
__email__ = 'rmcmaciver@hotmail.com'
__status__ = 'Dev'

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

        self.update_resource_path()
        self.config()
        self.threadpool = QueueThreads()

        self.source = None
        self.running = False
        self.track_init = False

    def update_resource_path(self, **kwargs):
        self.res_path = Path(os.path.realpath(__file__)).parents[0]
        self.params_path = os.path.join(self.res_path, 'params')

    def config(self):
        """ update params from config file if necessary"""
        # params path should be relative to the main package in params directory
        self.params_file = os.path.join(self.params_path, self.params_file)
        self.params = config_params(params=self.params, params_file=self.params_file)

    def set_output(self):
        self.params['dirout'] = set_dirout(self.params)

    def setup(self):
        """
        take params from file or from gui, setup the data source based on
            the device macro
        """
        # setup the handler to read files
        self.handler = Handler(parent=self)
        self.handler.setup()

    def view(self):
        """ setup the trackbar viewer """
        self.viewer = TrackbarViewer(parent=self, size=self.handler.size)
        # outgoing signal from viewer
        self.viewer.frame_index_signal.connect(self.handler.get_frame)
        # incoming signal from handler
        self.handler.frame_signal.connect(self.viewer.update)

    def update_params(self, **kwargs):
        """ """

    def track(self):
        """ track in GUI or headless mode """
        self.track_panel = TrackPanel(parent=self)
        self.track_panel.status_update_signal.connect(self.parent.update_status)

        # self.viewer_trackbar.raw_frame_signal.connect(self.handler.handle)
        # self.viewer_trackbar.mouse_event_signal.connect(self.track_panel.mouse_event)
        # self.handler.contour_frame_signal.connect(self.viewer_trackbar.update)
        # self.handler.tracker.done_process_signal.connect(self.track_panel.update_list_new)
        # self.handler.tracker.open_overlay_signal.connect(self.viewer_trackbar.update)
        # self.track_panel.tracks.status_update_signal.connect(self.parent.update_status)
        # # modify with outline of a single image
        # self.handler.tracker.display_frame_signal.connect(self.viewer_trackbar.update)
        # self.handler.tracker.display_frame_signal.connect(self.viewer_trackbar.update)
        #
        # self.handler.tracker.display_frame_signal.connect(self.viewer_trackbar.update)

    def stop(self):
       """
       stop the data source
       """

       # stop the handler
       print('stop the handler')
       self.handler.stop()
       self.viewer_trackbar.stop()
       # clear threadpool
       print('clear the threadpool')
       self.threadpool.clear()
