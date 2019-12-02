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

    def __init__(self, parent=None, size=None, params=None,**kwargs):
        super(TrackbarViewer, self).__init__(**kwargs)

        # parameterize this later
        self.parent = parent
        self.size = size
        self.name = 'trackbar'
        self.pos = (750, 50)
        self.scale = 0.5
        self.frame_index = 0

        self.setup_window()

    def setup_window(self):
        """ set postion and scaling of trackbar window"""
        cv2.namedWindow(self.name, cv2.WINDOW_NORMAL)
        cv2.moveWindow(self.name, self.pos[0], self.pos[1])

        print('\ncv2 window props:',
              '\n\tname:', self.name,
              '\n\tsize', self.size,
              '\n\tscale', self.scale)

        cv2.resizeWindow(self.name,
                         int(self.size[1]*self.scale),
                         int(self.size[0]*self.scale))

        cv2.createTrackbar( 'start', self.name, 0, self.size[2], self.on_change)
        cv2.createTrackbar( 'end'  , self.name, self.size[2], self.size[2], self.on_change)
        self.on_change(1)

        self.start = cv2.getTrackbarPos('start', self.name)
        self.end   = cv2.getTrackbarPos('end', self.name)

        if self.start >= self.end:
            raise Exception("start must be less than end")

    def next_frame(self, **kwargs):
        """ """
        frame_num = self.frame_index
        frame_num += 1
        self.on_change(frame_num)
        cv2.setTrackbarPos('start', self.name, int(frame_num))

    def on_change(self, trackbarValue):
        """ emit the frame index to the handler """
        self.frame_index_signal.emit(trackbarValue)

    def update(self, frame, index, **kwargs):
        """ update the current image
            frames from external source are connected here
        """
        frame = frame.astype(np.uint8) # force to uint8. one function sends int32
        cv2.imshow(self.name, frame)
        self.frame_index = index

    def stop(self, **kwargs):
        cv2.destroyAllWindows()
