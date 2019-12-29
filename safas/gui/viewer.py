# -*- coding: utf-8 -*-
"""

viewer.py

opencv window with scollbar to view images

"""
import numpy as np
import cv2

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class TrackbarViewer(QObject):

    frame_index_signal = pyqtSignal(int, name="frame_index_signal")

    def __init__(self,
                 parent=None,
                 size=None,
                 pos=(750,50),
                 scale=0.5,
                 params=None,
                 index=None,
                 **kwargs):

        super(TrackbarViewer, self).__init__(**kwargs)

        self.parent = parent
        self.size = size
        self.name = 'trackbar'
        self.pos = pos
        self.scale = scale
        if index is None:
            self.frame_index = 0
        else:
            self.frame_index = index
        self.setup_window()

    def setup_window(self):
        """ set postion and scaling of trackbar window"""
        cv2.namedWindow(self.name, cv2.WINDOW_NORMAL)
        cv2.startWindowThread()
        cv2.moveWindow(self.name, self.pos[0], self.pos[1])
        cv2.resizeWindow(self.name,
                         int(self.size[1]*self.scale),
                         int(self.size[0]*self.scale))

        cv2.createTrackbar('start', 
                           self.name, 
                           0, 
                           self.size[2], 
                           self.on_change)
        cv2.createTrackbar('end', 
                           self.name, 
                           self.size[2], 
                           self.size[2], 
                           self.on_change)
        self.on_change(1)

        self.start = cv2.getTrackbarPos('start', self.name)
        self.end   = cv2.getTrackbarPos('end', self.name)

        if self.start >= self.end:
            raise Exception("start must be less than end")

    def update_frame(self, frame, index, **kwargs):
        cv2.setTrackbarPos('start', self.name, int(index))
        self.frame_index = index
        
        frame = frame.astype(np.uint8) # force to uint8. 
        cv2.imshow(self.name, frame)
     
    def next_frame(self, **kwargs):
        """ """
        frame_num = self.frame_index
        frame_num += 1

        cv2.setTrackbarPos('start', self.name, int(frame_num))

    def on_change(self, trackbarValue):
        """ emit the frame index to the handler """
        self.frame_index_signal.emit(trackbarValue)

    def update(self, frame, index, **kwargs):
        """ update the current image, external source connects here """
        if frame is not None:
            frame = frame.astype(np.uint8) # force to uint8. 
            cv2.imshow(self.name, frame)
            self.frame_index = index
            
    def stop(self, **kwargs):
        cv2.waitKey(1)
        cv2.destroyAllWindows()
        cv2.waitKey(1)