# -*- coding: utf-8 -*-
"""

Tracker

"""
import os
from glob import glob
from itertools import cycle
import collections
import importlib
import yaml

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
from safas.config import write_params, set_dirout
"""

"""
KEYS = ['area',
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
            self.parent = parent

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
                'prop': prop,
                'velocity': None}

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

    def predict_next_all(self, frame, index, **kwargs):
        """ threaded or array func based predictions, rather than
                loop based in the track_panel gui object"""
        print('predict all next inside tracker')

    def predict_next(self, frame, index, id_obj, **kwargs):
        """ """
        # an easy way to terminate need to terminate after certain length.... 5?
        print('id_obj:', id_obj)

        maxobjs = self.params['improcess']['max_track_len']
        val_open = self.tracks['id'][id_obj][-1]['id_curr']
        print('max track len:', maxobjs)

        if len(self.tracks['id'][id_obj]) < maxobjs:
            p0 = self.tracks['id'][id_obj][-1]['prop'] # most recent one added
            props = self.frames[index]['props']
            criteria = self.params['matcher']
            M = Matcher(p0=p0, props=props, criteria=criteria)
            p1 = M.rank_and_match()
            return (p1, val_open)
        else:
            return (None, val_open)

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

        if type(id_obj) == int:
            id_obj = [id_obj]

        for id_o in id_obj:
            alpha = 0.9
            for track in self.tracks['id'][id_o]:
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

        # update the velocity if more than one object in track
        self.cal_vel()
        # save tracks to pandas file
        tracks = self.tracks['id']

        # take the first object in each track list
        if self.params['output'] == 0:
            if self.parent is None:
                self.params = set_dirout(params=self.params)
            else:
                self.parent.parent.set_output()

        dirout = self.params['dirout']

        T = []
        pxcal = self.params['improcess']['pixel_size']

        for t in tracks:
            tk = tracks[t][0]

            if tracks[t][-1] is not None:
                # do not calculate for 'lost' objects
                pk = {}
                for ky in KEYS:
                    # calculate metric vals with pxcal
                    if ky == 'area':
                        pk[ky] = tk['prop'][ky]*pxcal**2

                    elif ky in ['equivalent_diameter',
                              'perimeter',
                              'minor_axis_length',
                              'major_axis_length']:

                        pk[ky] = tk['prop'][ky]*pxcal
                    else:
                        pk[ky] = tk['prop'][ky]

                if 'vel_mean' in tk:
                    pk['vel_mean'] = tk['vel_mean']
                    pk['vel_N'] = tk['vel_N']
                    pk['vel_std'] = tk['vel_std']
                T.append(pk)

        df = pd.DataFrame(T)

        # check existing files in dir_out/data
        val =  len(glob(os.path.join(dirout,'data', '*.xlsx')))
        name = 'floc_props_%d.xlsx' % (val + 1)
        fname = os.path.join(dirout,'data', name)
        # write to excel file
        df.to_excel(fname)

        # also save the params as a yaml
        name = name = 'exp_params_%d.yml' % (val + 1)
        yname = os.path.join(dirout,'params', name)
        params = self.params
        write_params(file=yname, params=params)

    def cal_vel(self,):
        """ cal velocity from a series of centroids

        note: assumption is that centroids occur in sequential frames

        """
        # calculated before saving for now. may move to "live" location.
        # note: mechanism to detected when the frames are not sequential
        #       i.e. if object is detected in frame 1 and 3, then velocity
        #            will appear to be double the actual value
        dt = 1/self.params['improcess']['fps']

        T = {}
        for i in self.tracks['id']:
            track = self.tracks['id'][i]

            if len(track) > 1:
                cents = np.array([t['centroid'] for t in track])
                disp = []
                for k in range(len(cents)-1):
                    dist = np.linalg.norm(cents[(k+1)]-cents[k])
                    disp.append(dist)

                disp_metric = np.array(disp)*self.params['improcess']['pixel_size']/10**3 # in CM
                v = disp_metric/dt
                N = len(v)
                v_mean = np.mean(v)
                v_std = np.std(v)

                # convert to metric
                track[0]['vel_mean'] = v_mean
                track[0]['vel_std'] = v_std
                track[0]['vel_N'] = N
                T[i] = track

        self.tracks['id'] = T


def test_img():
    img = np.zeros((1000,1000))
    img[100:200, 100:200] = 255
    img[300:400,300:400] = 255
    img[500:600,500:600] = 255
    return img


if __name__ == '__main__':
    print('test the tracker')

    t = test_img()

    params = {'improcess': {'fps': 25},
              'baseout': 'C:/Users/Ryan/Desktop/Data/pro',
              'output': 0,
              }

    # test calc vel and writing
    T = Tracker(parent=None, params=params)
    T.add_frame(frame=t, frame_index=1)
    T.add_object(frame_index=1, id_curr=1)
    T.add_frame(frame=t, frame_index=2)
    T.update_object_track(frame_index=2, id_obj=0, id_curr=2)
    T.save()




#    frame = np.zeros((1000,1000,3))
#    contours = [np.array([[1,1],[10,50],[50,50]], dtype=np.int32) , np.array([[99,99],[99,60],[60,99]], dtype=np.int32)]
#    contourimg = cv2.drawContours(frame, contours, -1, (255, 0, 0), 3)
