# -*- coding: utf-8 -*-
"""

"watershed" filter

The marker-based watershed algorithm is used

Refer: 
    https://docs.opencv.org/3.4/d3/db4/tutorial_py_watershed.html
    
Note:
* the focus and clear edge filters should be optimized.

"""
import os
import time
import numpy as np
import copy
import cv2

from safas.filters.imfilters_module import (marker_based_watershed,
                                           prethresh_filter,
                                           clearedge_filter,
                                           focus_filter,
                                           add_contours)

# 2 dict to setup the GUI control
#   values are: [type, [MIN, MAX, DEFAULT]]
define_args = {'img_thresh': [np.int, [0, 255, 120]],
               'edge_thresh': [np.int, [0, 255, 120]],
               'edge_distance': [np.int, [0, 9, 1]],
               'dist_factor': [np.int, [0, 100, 50]],
               'apply_focus_filter': [np.bool, [True, False, True]],
               'apply_clearedge_filter': [np.bool, [True, False, True]],
               'contour_thickness': [np.int, [1, 4, 1]]}

# 3 must have a setup function. keep pattern as some filters require setup.
def setup():
    return None

def imfilter(src,
            img_thresh=100,
            edge_thresh=40,
            edge_distance=2,
            dist_factor=50,
            apply_focus_filter=True,
            apply_clearedge_filter=True,
            contour_color=(0,255,0),
            contour_thickness=1,
            **kwargs):
    
    # apply a threshold value to convert grayscale image to binary image
    thresh, gray = prethresh_filter(src, img_thresh)     
    # watershed transform (on color or 3-channel gray)
    labels = marker_based_watershed(src.copy(), 
                                    thresh, 
                                    dist_factor=dist_factor)
    
    if apply_focus_filter:
       labels = focus_filter(labels, gray, edge_thresh)

    if apply_clearedge_filter:
        labels = clearedge_filter(labels)

    contour_img = add_contours(src.copy(), labels,
                              contour_color=contour_color,
                              contour_thickness=contour_thickness)
    
    return (labels, contour_img)

if __name__ == '__main__':
    import sys
    sys.path.append(r'C:\Users\Ryan\Desktop\camera_setup\safas-dev')
    import matplotlib.pyplot as plt
    from safas import data

    params = {'img_thresh': 150,
               'edge_thresh': 20,
               'edge_distance': 1,
               'apply_focus_filter': True,
               'apply_clearedge_filter': True,
               'dist_factor': 0.5,
               }

    img = data.brightmudflocs()

    labels, contour_img = imfilter(img, **params)
    f, ax = plt.subplots(1,2, dpi=250)

    ax[0].imshow(labels)
    ax[1].imshow(contour_img)