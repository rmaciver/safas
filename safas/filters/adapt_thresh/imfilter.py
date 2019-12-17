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
                                           adapt_prethresh_filter,
                                           clearedge_filter,
                                           focus_filter,
                                           add_contours)

# 2 dict to setup the GUI control
#   values are: [type, [MIN, MAX, DEFAULT]]
# define_args = {'img_thresh': [np.int, [0, 255, 120]],
#                'edge_thresh': [np.int, [0, 255, 120]],
#                'edge_distance': [np.int, [0,9, 1]],
#                'apply_focus_filter': [np.bool, [True, False, True]],
#                'apply_clearedge_filter': [np.bool, [True, False, True]],
#                'contour_thickness': [np.int, [1, 4, 1]]}

# 3 must have a setup function. keep pattern as some filters require setup.
def setup():
    return None

def imfilter(src,
            img_thresh=100,
            edge_thresh=40,
            block_size=50,
            apply_focus_filter=True,
            apply_clearedge_filter=True,
            contour_color=(0,255,0),
            **kwargs):

    # apply a threshold value to convert grayscale image to binary image
    thresh, gray = adapt_prethresh_filter(src.copy(), block_size=block_size)
    ret, labels = cv2.connectedComponents(img_thresh)

    if apply_focus_filter:
       labels = focus_filter(labels, gray, edge_thresh)

    if apply_clearedge_filter:
        labels = clearedge_filter(labels)

    # add the contour image
    contour_img = add_contours(src.copy(), labels, contour_color=[255,0,0])

    return (labels, contour_img)

if __name__ == '__main__':
    import sys
    sys.path.append(r'C:\Users\Ryan\Desktop\camera_setup\safas-dev')
    import matplotlib.pyplot as plt
    from safas import data

    params = {'img_thresh': 70,
               'edge_thresh': 90,
               'edge_distance': 1,
               'apply_focus_filter': True,
               'apply_clearborder_filter': True,
               }

    img = data.clayflocs()

    labels, contour_img = imfilter(img, **params)
    f, ax = plt.subplots(1,2, dpi=250)

    ax[0].imshow(labels)
    ax[1].imshow(contour_img)
