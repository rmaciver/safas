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

"""

"""

keys = ['area', 
        'equivalent_diameter', 
        'perimeter', 
        'euler_number',  
        'minor_axis_length', 
        'major_axis_length',
        'extent',]

class Tracker(QObject):
    display_frame_signal = pyqtSignal(object, int, name="display_frame_signal")

    def __init__(self, parent=None, params=None, *args, **kwargs):
        super(Tracker, self).__init__(*args, **kwargs)

        if parent is None:
            self.params = params

        if parent is not None:
            self.parent = parent
            self.params = parent.params

        self.frames = collections.OrderedDict()
        self.tracks = {'id': collections.OrderedDict(),
                       'frame': collections.OrderedDict()}
        self.object_counter = 0
        self.frame_index = None
        self.frame_count = 0
        self.overlay = None

    def add_frame(self, frame, frame_index, add_all_objects=False, **kwargs):
        """ filtered binary frames are labelled then added
            frame: <uint8 array>
            frame_index: <int32>
        """
        # simple check in case viewer was scrolled back
        if frame_index not in self.frames:
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

            self.frames[frame_index] = {'frame': frame,
                                      'labels': L,
                                      'props': P,
                                      'contour': C,
                                      'total': T}
            self.frame_index = frame_index
            self.frame_count += 1

    def list_new(self):
        # for external connections.
        if self.frame_index is not None:
            return self.frames[self.frame_index]['total']

        if self.frame_index is None:
            return None

    def list_open(self, **kwargs):
        """ return a list of object numbers in previous frame i.e. open
            to be connected in the current frame
        """
        index = self.frame_index - 1

        if len(self.tracks['id']) > 0:
            vals = []

            for id_obj in self.tracks['id']:
                v = self.tracks['id'][id_obj][-1]['id_curr']
                vals.append(v)

            return vals
        else:
            return None

    def add_object(self, frame_index, id_curr, **kwargs):
        """ add a new object to track """
        prop = self.frames[self.frame_index]['props'][id_curr]
        id_obj = self.object_counter

        # convert to dictionary format
        vals = {'frame_index': frame_index,
                'id_curr': id_curr,
                'centroid': prop.centroid,
                'prop': prop}

        self.tracks['id'][id_obj] = [vals]

        if frame_index not in self.tracks['frame']:
            self.tracks['frame'][frame_index] = []

        self.tracks['frame'][frame_index].append(id_curr)
        self.object_counter += 1

    def remove_object(self, id_obj, **kwargs):
        """ remove the track from the list """
        self.tracks['id'].pop(id_obj)

    def n_tracks(self):
        val = len(list(self.tracks['id'].keys()))
        return val

    def update_object_track(self, frame_index, id_obj, id_curr, **kwargs):
        """ add a new object to an existing track """
        prop = self.frames[frame_index]['props'][id_curr]
        vals = {'frame_index': frame_index,
                'id_curr': id_curr,
                'centroid': prop.centroid,
                'prop': prop,
                'velocity': None}
        self.tracks['id'][id_obj].append(vals)

    def predict_next(self, frame, index, id_obj, **kwargs):
        """ """

        p0 = self.tracks['id'][id_obj][-1]['prop'] # most recent one added
        props = self.frames[index]['props']
        M = Matcher(self.tracks['id'])
        p1 = M.rank_and_match()

    def outline_pair(self, frame, index, val_open=None, val_new=None, **kwargs):
        """ outline the selected new and open objects """
        if val_new is not None:
            frame, index = self.outline_single_new(frame, index, val_new)
        if val_open is not None:
            frame, index = self.outline_single_open(frame, index, val_open)

        self.display_frame_signal.emit(frame, index)
  
    def outline_single_new(self, frame, index, val, **kwargs):
        """ make image to be displayed in window for user interaction"""
        #contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        coords = self.frames[index]['props'][val].coords
        frame[coords[:,0], coords[:,1]] = [0, 0, 255] # red
        return (frame, index)

    def outline_single_open(self, frame, index, val, **kwargs):
        """ make image to be displayed in window for user interaction"""
        index -= 1

        if index in self.frames:
            coords = self.frames[index]['props'][val].coords
            frame[coords[:,0], coords[:,1]] = [255, 0, 0] # blue
            return (frame, index)
        else:
            return None

    def outline_track(self, frame, index, id_obj, **kwargs):
        """ overlay a single track when selected """
#        print('outline in the tracker')
        overlay_t = np.zeros_like(frame, dtype=np.uint8)
        alpha = 0.9
        
        for track in self.tracks['id'][id_obj]:
#            print('track is:', track, track['prop'])
            xy = track['prop'].coords
            alpha = alpha*0.9
            overlay_t[xy[:,0], xy[:,1]] = [70, 255, 50]

        frame = cv2.addWeighted(frame, 1, overlay_t, alpha, 0)
        self.display_frame_signal.emit(frame, index)

    def plot_prop(self, prop, **kwargs):
        # dump the tracks into pandas file
        plot_props(self.tracks, prop=prop)
        
    def plot_prop(self, tracks, prop, ax=None):
        # plot histogram of a property
        if ax is None: 
            f, ax = plt.subplots(1,1, dpi=250, figsize=(3.5, 2.2))
        
        vals = [track[prop] for track in tracks['id']]
        ax.hist(vals)
        
        ax.set_xlabel(prop)
        ax.set_ylabel('counts')
        plt.tight_layout()
        
    def save(self):

        # dump the tracks into pandas file
        tracks = self.tracks['id']
    
        # take the first instance in each track list
        if self.params['output'] == 0:
            self.parent.parent.set_output()
        
        dirout = self.params['dirout']
        print(tracks)
        # use 0 index to get first on list
        P = [tracks[t][0]['prop'] for t in tracks]    
        T = [ {ky: prop[ky] for ky in keys} for prop in P]
        df = pd.DataFrame(T)
        
        # check existing files in dir_out/data
        val =  len(glob(os.path.join(dirout,'data', '*.xlsx')))
        name = 'floc_props_%d.xlsx' % (val + 1)
        fname = os.path.join(dirout,'data', name)
        # write to excel file
        df.to_excel(fname)
    
    def cal_vel(self,):
        """ cal velocity from a series of centroids """
        print('frame rate:', self.parent.fps)
        
        dt = 1/self.parent.fps
        
        for i in self.tracks['id']:
            track = self.tracks['id'][i]
            if len(track) > 1:
                print('try to cal displacement')
                cents = [t['centroid'] for t in track]
                print('total cents:', len(cents))
                disp = np.diff(cents, axis=0)
                print('displacement:', disp)
                 
                vals = []
                for i in range(len(disp)-1):        
                    dist = np.linalg.norm(disp[(i+1),:]-disp[i,:])
                    vals.append(dist)
                    
            # where to put these values then....back into the dict
            
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

    T.add_frame(frame=t, frame_index=200)
    T.add_all_objects()

    frame = np.zeros((1000,1000,3))
    contourimg = cv2.drawContours(frame, contours, -1, (255, 0, 0), 3)

    T.display_frame_signal.connect(T.display_test)
    T.overlay_single(frame=frame, index=200, val=1)
