# -*- coding: utf-8 -*-
"""

Matcher compares position and aera of tracked object to all other objects
    in the new frame

"""
import numpy as np
from skimage.measure import regionprops
from scipy.spatial.distance import cdist

def matcher(A_props, A_ids, B_props, B_ids, criteria):
    """ find best match of tracked object in the new frame

    A_props: a skimage.measure.regionprops object in frame n-1
    A_ids: integer id of the A_props object in frame n-1
    B_props: list of skimage.measure.regionprops objects in frame n
    A_ids: integer ids of the B_props objects in frame n-1
    criteria: type dict. must contain 'error_threshold' key and may contain
                'distance', 'area', 'squared' keys

    ex. criteria dictionary:
        criteria = {'error_threshold': 2500,
                    'distance': 1,
                    'area': 1,
                    'squared': False,
                    }

        'error_treshold': float, an object that is otherwise the "best" match
                                will be excluded if the match error is above
                                the error threshold

        'distance': float, this is the weighting given in the matching function
                    to the pixel-wise distance between the centroids of the
                    two objects

        'area': float, this is the weighting given in the matching function
                    to the pixel-wise area difference of the two objects
        'squared': bool, whether to square the error, the user must adjust
                    the error_threshold accordingly. in some cases squared
                    error may desirable.

    notes: 
        objects type may be other than skimage.measure.regionprops, but must
            have 'centroid' and 'area' attributes, such as a class or named
            tuple. however, that may (would) break safas in other places
            at this time
    """
    err = rank(A_props, B_props, criteria)
    B_matches = match(err, criteria['error_threshold'], A_ids, B_ids)
    return B_matches

def rank(A_props, B_props, criteria):
    """ calculate the error of each new object compared to most
            recent object added to the track
            """
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
    """ find the value and index of the objects with lowest error """
    # index of min value
    erridx = np.argmin(err, axis=1)
    errmin = np.min(err, axis=1)
    #print(erridx, errmin, B_ids)
    B_matches = B_ids[erridx]
    mask = errmin < error_threshold
    B_matches[np.where(~mask)] = -99999 # easier to deal with than nan or None

    return (B_matches, errmin)

def cal_cdist(A_props, B_props):

    A_cent =  np.array([prop.centroid for prop in A_props])
    B_cent =  np.array([prop.centroid for prop in B_props])
    return cdist(A_cent, B_cent)

def cal_carea(A_props, B_props):
    A_area = np.array([prop.area for prop in A_props])
    B_area =  np.array([prop.area for prop in B_props])
    return np.abs(B_area - A_area.reshape((A_area.shape[0], 1)))


if __name__=='__main__':
    P = FakeProp()
