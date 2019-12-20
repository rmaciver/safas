# -*- coding: utf-8 -*-
"""

Matcher compares position and aera of tracked object to all other objects
    in the new frame

    Note: need to improve the comments/ documentation here.

"""
import numpy as np
from skimage.measure import regionprops
from scipy.spatial.distance import cdist

def matcher(A_props, A_ids, B_props, B_ids, criteria):
    """ find best match of tracked object in the new frame"""
    err = rank(A_props, B_props, criteria)
    B_matches = match(err, criteria['error_threshold'], A_ids, B_ids)
    return B_matches

def rank(A_props, B_props, criteria):
    """ calculate the error of each new object compared to most
            recent object added to the track """
    err = np.full((len(A_props), len(B_props)), 0, dtype=np.float64)

    if 'distance' in criteria:
        dist = cal_cdist(A_props, B_props)
        err += dist*criteria['distance']

    if 'area' in criteria:
        area = cal_carea(A_props, B_props)
        err += area*criteria['area']

    if 'squared' in criteria:
        if criteria['squared']:
            err = err**2
    return err

def match(err, error_threshold, A_ids, B_ids):
    errmin = np.argmin(err, axis=1)
    B_matches = B_ids[errmin]
    mask = errmin < error_threshold
    B_matches[np.where(~mask)] = -99999 # easier to deal with than nan or None
    return B_matches

def cal_cdist(A_props, B_props):
    A_cent =  np.array([prop.centroid for prop in A_props])
    B_cent =  np.array([prop.centroid for prop in B_props])
    return cdist(A_cent, B_cent)

def cal_carea(A_props, B_props):
    A_area = np.array([prop.area for prop in A_props])
    B_area =  np.array([prop.area for prop in B_props])
    return np.abs(B_area - A_area.reshape((A_area.shape[0], 1)))
