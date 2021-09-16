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
from skimage.color import rgb2gray
from skimage.util import pad

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
    status_update_signal = pyqtSignal(str, name="status_update_signal")
    restart_tracks_signal = pyqtSignal(str, name="restart_tracks_signal")

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
        self.tracks_terminated = {}

        self.track_stats = {}
        self.props_frame = None

        self.object_counter = 0
        self.frame_index = None
        self.frame_count = 0
        self.overlay = None

    def add_frame(self, label_frame, contour_frame, raw_frame, frame_index, **kwargs):
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

            if L is not None:
                P = regionprops(label_image=L)
                T= len(P) # do not include the background
                C = find_contours(label_frame, 100)

                self.frames[frame_index] = {'frame': label_frame,
                                            'cframe': contour_frame,
                                            'rframe': raw_frame,
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

    def add_object(self, frame_index, id_curr, add_image=True, **kwargs):
        """ add a new object to track """
        prop = self.frames[self.frame_index]['props'][id_curr]
        raw_frame = self.frames[self.frame_index]['rframe']

        binary_pad, gs_pad = pad_images(prop, raw_frame)

        vals = {}
        if add_image:
            # save floc image for recal or reseg
            vals['image'] = {'intensity': gs_pad, 'binary': binary_pad}

        id_obj = self.object_counter

        vals_tem = {'frame_index': frame_index,
                    'id_curr': id_curr,
                    'centroid': prop.centroid,
                    'prop': prop,
                    'velocity': None,
                    'match_error': 0,
                    }

        vals.update(vals_tem)

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

    def update_object_track(self,
                            frame_index,
                            id_obj,
                            id_curr,
                            match_error=None,
                            **kwargs
                            ):
        """ Add a new object to an existing track"""
        print('data:', frame_index, id_obj, id_curr, match_error)

        # test if not the first object and if last obj added was -99999
        # a method to overwrite 'lost' tracks with -99999
        track = self.tracks['id'][id_obj]
        if (len(track) > 1) & (track[-1]['id_curr'] == -99999):
            id_curr == -99999

        if id_curr == -99999:
            # match_error > threshold, invalid match, filled with -99999

            # need a fake prop to ....

            vals = {'frame_index': frame_index,
                    'id_curr': id_curr,
                    'centroid': None,
                    'prop': FakeProp(),
                    'velocity': None,
                    'match_error': match_error}

        else:
            prop = self.frames[frame_index]['props'][id_curr]
            vals = {'frame_index': frame_index,
                    'id_curr': id_curr,
                    'centroid': prop.centroid,
                    'prop': prop,
                    'velocity': None,
                    'match_error': 0}

            if match_error is not None:
                vals['match_error'] = match_error

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

        # objects in most recent frame
        if index in self.frames:
            B_props = self.frames[index]['props']
        else:
            line = 'All tracks lost in at least one frame.'
            self.status_update_signal.emit(line)
            return None

        B_ids = np.arange(len(B_props))
        B_matches, error_min = matcher(A_props=A_props,
                                       A_ids=A_ids,
                                       B_props=B_props,
                                       B_ids=B_ids,
                                       criteria=criteria)

        for id_obj, val_new, match_error in zip(self.tracks['id'],
                                                B_matches,
                                                error_min):
            self.update_object_track(index,
                                     id_obj=id_obj,
                                     id_curr=val_new,
                                     match_error=match_error)

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
                if xy[0][0] == -99999:
                    # this is a FakeProp i.e. a terminated object track
                    continue
                overlay_t[xy[:,0], xy[:,1]] = [225, 255, 50]

        frame = cv2.addWeighted(frame, 1, overlay_t, alpha, 0)
        self.display_frame_signal.emit(frame, index)

    def save(self, filename=None):
        """ calculate velocity and convert tracks to dataframe format"""

        # make an output
        if self.params['output'] == 0:
            if self.parent is None:
                self.params = set_dirout(params=self.params)
            else:
                self.parent.parent.set_output(folders=['imgs','params','data'])

        dirout = self.params['output']
        N = len(os.listdir(os.path.join(dirout,'data')))

        name = '%02d_' % (N + 1) + 'frame_index_%d' % self.frame_index
        dirout_data = os.path.join(dirout, 'data', name)

        if not os.path.isdir(dirout_data):
            os.mkdir(dirout_data)
            os.mkdir(os.path.join(dirout_data, 'track_stats'))

        # calculate velocity, metric props
        self.cal_vel()
        self.cal_props()

        # write frames if available
        if self.props_frame is not None:
            name = 'props_frame_%d.xlsx' % self.frame_index
            fname = os.path.join(dirout_data, name)
            self.props_frame.to_excel(fname)

        if len(self.track_stats) > 0:
            for i in self.track_stats:
                name = '%02d_track_stats_%d.xlsx' % (i, self.frame_index)
                fname = os.path.join(dirout_data, 'track_stats', name)
                self.track_stats[i].to_excel(fname)

        # write parameters for track
        name = 'params_%d.yml' % (N + 1)
        yname = os.path.join(dirout, 'params', name)
        params = self.params
        write_params(file=yname, params=params)

        if self.params['save']['save_object_images']:
            # save individual floc images
            dirout = os.path.join(self.params['output'], 'imgs')

            if not os.path.isdir(dirout):
                os.mkdir(dirout)

            N = len(os.listdir(dirout))
            name = '%02d_' % (N + 1) + 'objects_%d' % self.frame_index
            dirout = os.path.join(dirout, name)

            if not os.path.isdir(dirout):
                os.mkdir(dirout)

            self.save_obj_images(dirout=dirout)

    def cal_props(self):
        """ convert props from tracks to metric"""
        tracks = self.tracks['id']
        pxcal = self.params['improcess']['pixel_size']
        # list of processed tracks
        T = []
        for t in tracks:
            # the first item
            tk = tracks[t][0]

            #if tracks[t][-1] is not None:
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
                for key in ['vel_N',
                            'vel_mean', 'vel_std',
                            'vel_x_mean', 'vel_x_std',
                            'vel_y_mean','vel_y_std']:
                    pk[key] = tk[key]

            T.append(pk)
    
        self.props_frame = pd.DataFrame(T)

    def save_obj_images(self, dirout=None):
        """ save the images """
        for i in self.tracks['id']:
            track = self.tracks['id'][i][0]
            binary = track['image']['binary']
            gs = track['image']['intensity']
            for img, name in zip([binary, gs], ['binary','intensity']):
                fname = '%04d_' % i + '%s.png' % name
                fname = os.path.join(dirout, fname)
                if name == 'binary':
                    img = (img*255).astype(np.uint8)
                print('image save:', img.shape, 'object:', i)
                sio.imsave(arr=img, fname=fname)

    def cal_fractal_dimension(self,):
        """ calculate box counting fractal dimension of the flocs"""
        T = {}
        #next:  parallelize to speed up
        for i in self.tracks['id']:
            track = self.tracks['id'][i][0]
            img = track['image']['binary']
            fd = fractal_dimension(img, pads=3)
            track[0]['fract_dim'] = fd
            T[i] = track

        # add tracks with fd back in dict
        self.tracks['id'] = T

    def cal_vel(self, theta_max=45, N=2):
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
            cents = np.array([t['prop'].centroid for t in track])
            # mask cents on -99999
            mask = cents[:,0] != -99999
            cents = cents[mask]

            if len(cents) >= N:
                dist = np.linalg.norm((cents[1:]-cents[:-1]), axis=1)
                # calculate angle of each track wrt [1,0]
                vect = cents[1:] - cents[:-1]
                angles = [angle_between(np.array([1,0]), vt) for vt in vect]
                disp_metric = np.array(dist)*self.params['improcess']['pixel_size']/10**3 # in mm
                v = disp_metric/dt
                match_errors = np.array([t['match_error'] for t in track])
                match_errors = match_errors[mask]

                # calculate x, y displacement & velocity components
                disp_xy = np.diff(cents, axis=0)
                vel_xy = disp_xy/dt[1:]
                vel_y = vel_xy[:,0]
                vel_x = vel_xy[:,1]

                # dataframe for track stats
                track_stats = {'cents_x': cents[:,1],
                               'cents_y': cents[:,0],
                               'dist': np.append(0, dist),
                               'angles': np.append(0, angles),
                               'velocity': np.append(0, v),
                               'velocity_x': np.append(0, vel_x),
                               'velocity_y': np.append(0, vel_y),
                               'match_error': match_errors,
                               }
                self.track_stats[i] = pd.DataFrame(track_stats)

                # track excluded if angle is too large
                if np.abs(np.nanmean(angles))< theta_max:

                    track[0]['vel_N'] = len(v)
                    track[0]['vel_mean'] = np.mean(v)
                    track[0]['vel_std'] = np.std(v)

                    track[0]['vel_x_mean'] = np.mean(vel_x)
                    track[0]['vel_x_std'] = np.std(vel_x)

                    track[0]['vel_y_mean'] = np.mean(vel_y)
                    track[0]['vel_y_std'] = np.std(vel_y)

                    T[i] = track

        # filtered tracks with velocity added are put back in the tracks dict
        self.tracks['id'] = T

def pad_images(prop, raw_frame, pad_val=10):
    """ pad the binary image and extract the intensity image"""
    # crop out the raw intensity image area
    pb = prop.bbox
    ps = np.array([(pb[0]-pad_val),(pb[1]-pad_val),
                   (pb[2]+pad_val),(pb[3]+pad_val)])
    print('prop box:', pb, 'gs box:', ps)
    gs_pad = raw_frame[ps[0]:ps[2], ps[1]:ps[3]]

    # pad the binary image
    binary_pad = pad(prop.image, pad_width=((pad_val,pad_val),
                                            (pad_val,pad_val)))

    return (binary_pad, gs_pad)

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


class FakeProp():
    # replace None with a FakeProp filled with -99999
    centroid = (-99999,-99999)
    area = -99999
    coords = [(-99999, -99999)]

if __name__ == '__main__':

    F = FakeProp()
    # t = test_img()

    # params = {'improcess': {'fps': 25},
    #           'baseout': 'C:/',
    #           'output': 0,
    #           }

    # # test calc vel and writing
    # T = Tracker(parent=None, params=params)
    # T.add_frame(frame=t, frame_index=1)
    # T.add_object(frame_index=1, id_curr=1)
    # T.add_frame(frame=t, frame_index=2)
    # T.update_object_track(frame_index=2, id_obj=0, id_curr=2)
    # T.save()

    P = FakeProp()
