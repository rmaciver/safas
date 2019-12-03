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

# define args used for init parameters and gui for user interaction
define_args = {'img_thresh': [np.int, [0, 255]],
               'edge_thresh': [np.int, [0, 255]],
               'apply_focus_filter': [np.bool, [True, False]],
               'apply_clearedge_filter': [np.bool, [True, False]],
               }

def imfilter(src,
            img_thresh=100,
            edge_thresh=40,
            apply_focus_filter=True,
            apply_clearedge_filter=True,
            contour_color=(0,255,0),
            **kwargs):
    
    # apply a threshold value to convert grayscale image to binary image
    thresh, gray = prethresh_filter(src, img_thresh)     
    # watershed transform (on color or 3-channel gray)
    labels = marker_based_watershed(src.copy(), thresh)
    
    if apply_focus_filter:
       labels = focus_filter(labels, img, edge_thresh)

    if apply_clearedge_filter:
        labels = clearedge_filter(labels)

    # add the contour image
    contour_img = add_contours(src.copy(), labels, contour_color=[255,0,0])
    
    return (img, contour_img)

if __name__ == '__main__':
    import sys
    sys.path.append(r'C:\Users\Ryan\Desktop\camera_setup\safas-dev')
    import matplotlib.pyplot as plt
    from safas import data

    params = {'img_thresh': 70,
               'edge_thresh': 90,
               'apply_focus_filter': True,
               'apply_clearborder_filter': True,
               }

    img = data.clayflocs()
    
    labels, contour_img = imfilter(img, **params)
    f, ax = plt.subplots(1,2, dpi=250)
    
    ax[0].imshow(labels)
    ax[1].imshow(contour_img)