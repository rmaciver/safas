"""
handler.py

classes to control movement of images in the module

* stream is always the parent
* at this time only videos are supported
* emit frames to Viewer
* emit frames to Tracker
"""
import os
import importlib

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import cv2

from safas.qt_threads import QueueThreads
from safas.tracker import Tracker
from safas import filters

__author__ = 'Ryan MacIver'
__copyright__ = 'Copyright 2019'
__credits__ = ['Ryan MacIver']
__license__ = 'MIT'
__version__ = '0.0.1'
__maintainer__ = 'Ryan MacIver'
__email__ = 'rmcmaciver@hotmail.com'
__status__ = 'Dev'

class Handler(QObject):

    frame_signal = pyqtSignal(object, int, name="frame_signal")
    process_finished_signal = pyqtSignal(int, name='process_finished_signal')

    def __init__(self, parent=None, params=None):
        super(self.__class__, self).__init__(parent)

        # params must be in one or the others
        if parent is not None:
            self.parent = parent
            self.params = parent.params
            self.threadpool = parent.threadpool
        
        if parent is None:
            self.params = params

        self.frame_index = 0
        self.frame_count = 0
        self.process_frames = False

    def setup(self):
        """ take params and setup the file source and connections """
        self.open_vidreader()
        self.threadpool.add_to_queue(self.start_video)
        self.get_filter(name=self.params['improcess']['filter'])
        self.tracker = Tracker(parent=self)

        if self.params['improcess']['mode']  == 'trigger':
            self.params['improcess']['running'] = False

        if self.params['improcess']['mode'] == 'auto':
            self.params['improcess']['running'] = True

    def open_vidreader(self):
        file = self.params['input']

        if not os.path.isfile(file):
            self.status_update_signal.emit('input file does not exist')

        self.cap = cv2.VideoCapture(file)

        if not self.cap.isOpened():
            print('video is not open')

        width  = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # float
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) # float
        length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # may want to allow user to override fps if not correct in video header
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        # update params 
        self.params['improcess']['fps'] = fps
        self.params['improcess']['img_dim'] = [height, width, length]
        
        self.fps = fps
        self.size = (width, height, length)

    def start_video(self, **kwargs):
        print('video starting...', self.cap.isOpened())

        while self.cap.isOpened():
            if self.cap.get(cv2.CAP_PROP_POS_FRAMES) >= self.size[2]:
                break

    def get_frame(self, index, mode=None, params=None, **kwargs):
        """ viewer callback, manual mode """
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        err, frame = self.cap.read()
        self.frame_index = index
        
        if mode == 'test':
            # do not add to the analysis
            print('get_frame in params test mode')
            print('params:', params)
            label_frame, frame = self.imfilter(src=frame, **params)
        else: 
            if self.params['improcess']['running']:
                label_frame, frame = self.imfilter(src=frame,
                                                 **self.params['improcess']['kwargs'])
                self.frame_count += 1
                self.label_img = label_frame
                self.contour_img = frame
                self.tracker.add_frame(label_frame, index)
                self.process_finished_signal.emit(1)
    
        # emit either the raw or overlay image
        print('emit the processed image')
        self.frame_signal.emit(frame, index)

    def set_process(self, **kwargs):
        self.process_frames = True

    def get_filter(self, name):
        """
        device name and script must match
        """
        script = 'filters.' + name + '.imfilter'
        imfilter = importlib.import_module(script)
        self.imfilter = imfilter.imfilter
        print('%s filter was loaded' % name)