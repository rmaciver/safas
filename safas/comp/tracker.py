# -*- coding: utf-8 -*-
"""

tracker.py

Tracker class for correlating objects in time series of frames

-functions to:
    * add frames,
    * add objects to track,
    * correlate objects between frames,
    * visualize objects and tracks,
    * calculate object velocity
    * save output,

- Tracker emits signals that are connected to the Viewer in the Stream class

- Tracker is connected to signals emitted from the TrackPanel and TrackLists
    objects to select objects to highlight and track

-todo:
    1 separate functionality of this class for easier access in 'headless'
    mode.
    2 true divide error observed a couple of times in 'angle_between'
"""
import os
from glob import glob
from itertools import cycle
import collections
import importlib
import yaml

import numpy as np
from scipy.spatial import distance
import pandas as pd

import skimage
import skimage.io as sio
from skimage.measure import label, regionprops, find_contours

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import cv2

from safas.comp.matcher import matcher
from safas.comp.setconfig import write_params, set_dirout

# these properties from skimage.measure.regioprops are added to the object
#   analysis. other keys may be added.
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

    def add_frame(self, label_frame, frame, frame_index, **kwargs):
        """ filtered binary frames are labelled then added
            frame: <uint8 array>
            frame_index: <int32>
        """
        # simple check in case viewer was scrolled back
        if frame_index not in self.frames:
            L = None
            if self.frame_count == 0:
                self.overlay_img = np.zeros_like(label_frame)
            if len(np.unique(label_frame)) == 2:
                # frame is not labelled
                L = label(label_frame)
            if len(np.unique(label_frame)) > 2:
                L = label_frame

            if L is not None :
                P = regionprops(L)
                T= len(P) # do not include the background
                C = find_contours(label_frame, 100)

                self.frames[frame_index] = {'frame': label_frame,
                                            'cframe': frame,
                                          'labels': L,
                                          'props': P,
                                          'contour': C,
                                          'total': T}
                self.frame_index = frame_index
                self.frame_count += 1

    def list_new(self):
        """ for external connections."""
        if self.frame_index is not None:
            return self.frames[self.frame_index]['total']

        if self.frame_index is None:
            return None

    def list_open(self, **kwargs):
        """ return a list of object numbers in previous frame on the track """
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
        """ calculate number of objects being tracked """
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

    def predict_next_all(self, index, **kwargs):
        """ correlate each selected object in frame N-1 with an object in the
                current frame """
        criteria = self.params['matcher']
        A_props = []
        A_ids = []

        for id_obj in self.tracks['id']:
            A_props.append(self.tracks['id'][id_obj][-1]['prop'])
            A_ids.append(id_obj)

        B_props = self.frames[index]['props']
        B_ids = np.arange(len(B_props))
        B_matches = matcher(A_props=A_props,
                            A_ids=A_ids,
                            B_props=B_props,
                            B_ids=B_ids,
                            criteria=criteria)

        for id_obj, val_new in zip(self.tracks['id'], B_matches):
            self.update_object_track(index, id_obj=id_obj, id_curr=val_new)

    def outline_pair(self, frame, index, val_open=None, val_new=None, **kwargs):
        """ outline the selected new and open objects """
        if val_new is not None:
            frame, index = self.outline_single_new(frame, index, val_new)
        if val_open is not None:
            frame, index = self.outline_single_open(frame, index, val_open)

        self.display_frame_signal.emit(frame, index)

    def outline_single_new(self, frame, index, val, **kwargs):
        """ make image to be displayed in window for user interaction"""
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
        overlay_t = np.zeros_like(frame, dtype=np.uint8)
        alpha = 0.9
        if type(id_obj) == int:
            id_obj = [id_obj]

        for id_o in id_obj:
            for track in self.tracks['id'][id_o]:
                xy = track['prop'].coords
                overlay_t[xy[:,0], xy[:,1]] = [225, 255, 50]

        frame = cv2.addWeighted(frame, 1, overlay_t, alpha, 0)
        self.display_frame_signal.emit(frame, index)

    def save(self, filename=None):
        """ calculate velocity and convert tracks to dataframe format"""
        self.cal_vel()

        tracks = self.tracks['id']

        if self.params['output'] == 0:
            # set the output if not already set
            # bec. it may have been set by user in the main panel
            if self.parent is None:
                self.params = set_dirout(params=self.params)
            else:
                self.parent.parent.set_output()

        dirout = self.params['output']

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

        val =  len(glob(os.path.join(dirout,'data', '*.xlsx')))

        if 'filename' in self.params['save']:
            name = '%02d_' % (val + 1) + self.params['save']['filename'] % self.frame_index

        fname = os.path.join(dirout,'data', name)
        df.to_excel(fname)

        name = 'params_%d.yml' % (val + 1)
        yname = os.path.join(dirout, 'params', name)
        params = self.params
        write_params(file=yname, params=params)

        if self.params['save']['save_frames']:
            path = 'imgs_frame_%05d' % self.frame_index
            imdirout = os.path.join(dirout, 'imgs', path)

            for frame in self.frames:
                img = self.frames[frame]['frame']
                name = 'img_%d.png' % frame
                fname = os.path.join(imdirout, name)
                cv2.imwrite(filename=fname, img=img)

                img = self.frames[frame]['cframe']
                name = 'contour_img_%d.png' % frame
                fname = os.path.join(imdirout, name)
                cv2.imwrite(filename=fname,  img=img)

    def cal_vel(self, theta_max=45, N=2 ):
        """ cal velocity from a series of centroids
            * filter flocs not moving generally downward
            * pixel size calibration in um.
            * dt is time in seconds
            * velocity in mm/s
            * assumption is that centroids occur in sequential frame; forced
                because when no match is found and -99999 is added
        """
        if 'max_object_angle' in self.params['improcess']:
            theta_max = self.params['improcess']['max_object_angle']

        if 'min_track_len' in self.params['improcess']:
            N = self.params['improcess']['min_track_len']

        dt = 1/self.params['improcess']['fps']
        # dictionary to hold the
        T = {}

        for i in self.tracks['id']:
            track = self.tracks['id'][i]
            if len(track) >= N:
                cents = np.array([t['centroid'] for t in track])
                dist = np.linalg.norm((cents[1:]-cents[:-1]), axis=1)

                # calculate angle of each track wrt [1,0]
                vect = cents[1:] - cents[:-1]
                angles = [angle_between(np.array([1,0]), vt) for vt in vect]
                mean_angle = np.abs(np.nanmean(angles))

                # track excluded if angle is too large
                if mean_angle < theta_max:
                    disp_metric = np.array(dist)*self.params['improcess']['pixel_size']/10**3 # in MM
                    v = disp_metric/dt
                    track[0]['vel_mean'] = np.mean(v)
                    track[0]['vel_std'] = np.std(v)
                    track[0]['vel_N'] = len(v)
                    T[i] = track

        # filtered tracks with velocity added are put back in the tracks dict
        self.tracks['id'] = T

def angle_between(v1, v2):
    """ angle between vectors v1 and v2 """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.degrees(np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)))

def unit_vector(vector):
    """  unit vector of the vector """
    # true divide error not solved in some cases
    return vector / np.linalg.norm(vector)

def test_img():
    img = np.zeros((1000,1000))
    img[100:200, 100:200] = 255
    img[300:400,300:400] = 255
    img[500:600,500:600] = 255
    return img

if __name__ == '__main__':
    t = test_img()

    params = {'improcess': {'fps': 25},
              'baseout': 'C:/',
              'output': 0,
              }

    # test calc vel and writing
    T = Tracker(parent=None, params=params)
    T.add_frame(frame=t, frame_index=1)
    T.add_object(frame_index=1, id_curr=1)
    T.add_frame(frame=t, frame_index=2)
    T.update_object_track(frame_index=2, id_obj=0, id_curr=2)
    T.save()
