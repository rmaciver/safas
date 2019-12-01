# -*- coding: utf-8 -*-
"""

Tracker

"""
import os
from glob import glob
from itertools import cycle
import collections
import importlib

import numpy as np
import skimage
import skimage.io as sio
from skimage.filters import sobel, gaussian
from skimage.segmentation import clear_border, random_walker
from skimage.color import rgb2grey, grey2rgb
from skimage.measure import label, regionprops, find_contours
from skimage.exposure import rescale_intensity

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import pandas as pd

import cv2

from safas.matcher import Matcher

class Tracker(QObject):
    display_frame_signal = pyqtSignal(object, int, name="display_frame_signal")
    done_process_signal = pyqtSignal(int, name="done_process_signal")
    open_overlay_signal = pyqtSignal(object, int, name="open_overlay_signal")

    def __init__(self, parent=None, params=None, *args, **kwargs):
        super(Tracker, self).__init__(*args, **kwargs)

        if parent is None:
            self.params = params

        if parent is not None:
            self.params = parent.params

        self.frames = collections.OrderedDict()
        self.tracks = {'id': collections.OrderedDict(),
                       'frame': collections.OrderedDict()}
        self.object_counter = 0
        self.frame_num = None
        self.frame_count = 0
        self.overlay = None

    def add_frame(self, frame, frame_num, add_all_objects=False, **kwargs):
        """ filtered binary frames are labelled then added
            frame: <uint8 array>
            frame_num: <int32>
        """
        # simple check in case viewer was scrolled back
        if frame_num not in self.frames:
            if self.frame_count == 0:
                self.overlay_img = np.zeros_like(frame)

            if len(np.unique(frame)) == 2:
                # frame is not labelled
                L = label(frame)
            if len(np.unique(frame)) > 2:
                L = frame

            P = regionprops(L)
            T= len(P) # do not include the background

            # assume frame is uint8
            C = find_contours(frame, 100)

            self.frames[frame_num] = {'frame': frame,
                                      'labels': L,
                                      'props': P,
                                      'contour': C,
                                      'total': T}
            self.frame_num = frame_num
            self.frame_count += 1
            self.done_process_signal.emit(frame_num)

    def list_new(self):
        # for external connections.
        if self.frame_num is not None:
            return self.frames[self.frame_num]['total']

        if self.frame_num is None:
            return None

    def list_open(self, index, **kwargs):
        """ return a list of object numbers in previous frame i.e. open
            to be connected in the current frame
        """
        index = index - 1 # check previous frame
        # test if any open chains
        if len(self.tracks['id']) > 0:
            vals = []

            for id_obj in self.tracks['id']:
                v = self.tracks['id'][id_obj][-1]['id_curr']
                vals.append(v)

            return vals
        else:
            return None

    def n_tracks(self):
        val = len(list(self.tracks['id'].keys()))
        return val

    def add_all_objects(self):
        # used for the first frame to instantiate new tracks
        for i in range(self.frames[self.frame_num]['total']):
            prop = self.frames[self.frame_num]['props'][i]

            self.add_object(self.frame_num, i)

    def add_object(self, frame_num, id_curr, **kwargs):
        """ add a new object to track """
        prop = self.frames[self.frame_num]['props'][id_curr]
        id_obj = self.object_counter

        # convert to dictionary format
        vals = {'frame_num': frame_num,
                'id_curr': id_curr,
                'centroid': prop.centroid,
                'prop': prop}

        self.tracks['id'][id_obj] = [vals]

        if frame_num not in self.tracks['frame']:
            self.tracks['frame'][frame_num] = []

        self.tracks['frame'][frame_num].append(id_curr)
        self.object_counter += 1

    def remove_object(self, id_obj, **kwargs):
        """ remove the track from the list """
        self.tracks['id'].pop(id_obj)

    def update_object_track(self, frame_num, id_obj, id_curr, **kwargs):
        """ add a new object to an existing track """
        prop = self.frames[frame_num]['props'][id_curr]
        vals = {'frame_num': frame_num,
                'id_curr': id_curr,
                'centroid': prop.centroid,
                'prop': prop}
        self.tracks['id'][id_obj].append(vals)


    def save(self, **kwargs):
        # dump the tracks into pandas file
        df = pd.DataFrame()

    def predict_next(self, frame, index, id_obj, **kwargs):
        """ """

        p0 = self.tracks['id'][id_obj][-1]['prop'] # most recent one added
        props = self.frames[index]['props']
        M = Matcher(self.tracks['id'])
        p1 = M.rank_and_match()


    def overlay_single_new(self, frame, index, val, **kwargs):
        """ make image to be displayed in window for user interaction"""
        #contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        coords = self.frames[index]['props'][val].coords
        frame[coords[:,0], coords[:,1]] = [0, 0, 255] # red
        return (frame, index)

    def overlay_single_open(self, frame, index, val, **kwargs):
        """ make image to be displayed in window for user interaction"""
        #contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        index -= 1

        if index in self.frames:
            coords = self.frames[index]['props'][val].coords
            frame[coords[:,0], coords[:,1]] = [255, 0, 0] # red
            return (frame, index)
        else:
            return None

    def outline_pair(self, frame, index, val_open=None, val_new=None, **kwargs):
        """ outline the selected new and open objects """
        if val_new is not None:
            frame, index = self.overlay_single_new(frame, index, val_new)
        if val_open is not None:
            frame, index = self.overlay_single_open(frame, index, val_open)

        self.display_frame_signal.emit(frame, index)

    def overlay_open(self, frame, index, vals, **kwargs):
        """ make image to be displayed in window for user interaction"""
        # make image with open objects overlay
        index -= 1
        vals = self.tracks['frame'][index]
        emt = np.zeros_like(frame)

        # will be slower for multiple tracks, use gpu method later
        for val in vals:
            coords = self.frames[index]['props'][val].coords
            frame[coords[:,0], coords[:,1]] = [255, 0, 0] # red

        self.open_overlay_signal.emit(frame, index)

    def outline_track(self, frame, index, id_obj, **kwargs):
        """ overlay a single track when selected """
#        print('outline in the tracker')
        overlay_t = np.zeros_like(frame, dtype=np.uint8)
        alpha = 0.9
        for track in self.tracks['id'][id_obj]:
#            print('track is:', track, track['prop'])
            xy = track['prop'].coords
            alpha = alpha*0.9
            overlay_t[xy[:,0], xy[:,1]] = [100, 175, 255]

#        print('added coords in tracker')
        frame = cv2.addWeighted(frame, 1, overlay_t, alpha, 0)
#        print('image overlay in tracker')
        self.display_frame_signal.emit(frame, index)
#        print('emitted image from outline track')

    def overlay_tracks(self, frame, index, **kwargs):

        for track in self.tracks['id']:
            vals = self.tracks['id'][track]

            frame_num = [item[0] for item in vals]
            id_curr = [item[1] for item in vals]
            centroid = [item[2] for item in vals]
            prop = [item[3] for item in vals]

            overlay = np.zeros_like(frame, dtype=np.uint8)

            for i in range(len(frame_num)):
                fn = self.frame_num - frame_num[i]
                alpha = np.exp(-fn/4)

                # list of items in this image
                vals = self.tracks['frame'][i]

                props = self.frames[frame_num]['props'][vals]
                overlay_t = np.zeros_like(frame, dtype=np.uint8)

                for prop in props:
                    coords = prop[i].coords
                    overlay_t[coords[:,0], coords[:,1]] = [0.7, 1, 1]

                overlay = cv2.addWeighted(overlay, 1, overlay_t, alpha, 0)

        # blend withthe final image
        frame = cv2.addWeighted(frame, 1, overlay, 1, 0)
        self.display_frame_signal.emit(frame, index)





def test_img():
    img = np.zeros((1000,1000))
    img[100:200, 100:200] = 255
    img[300:400,300:400] = 255
    img[500:600,500:600] = 255
    return img


if __name__ == '__main__':
    print('test the tracker')
    contours = [np.array([[1,1],[10,50],[50,50]], dtype=np.int32) , np.array([[99,99],[99,60],[60,99]], dtype=np.int32)]

    t = test_img()
    T = Tracker()

    T.add_frame(frame=t, frame_num=200)
    T.add_all_objects()

    frame = np.zeros((1000,1000,3))
    contourimg = cv2.drawContours(frame, contours, -1, (255, 0, 0), 3)

    T.display_frame_signal.connect(T.display_test)
    T.overlay_single(frame=frame, index=200, val=1)
