# -*- coding: utf-8 -*-
"""

"grad_seg" filter

Uses the gradient images to make the outline.


"""
import os
import time
import numpy as np
import copy
import cv2

# 1 import filter building blocks
from safas.filters.imfilters_module import (marker_based_watershed,
                                           prethresh_filter,
                                           cal_grad_img,
                                           clearedge_filter,
                                           focus_filter,
                                           add_contours)

# 2 dict to setup the GUI control
define_args = {'img_thresh': [np.int, [0, 255]],
               'edge_thresh': [np.int, [0, 255]],
               'apply_focus_filter': [np.bool, [True, False]],
               'apply_clearedge_filter': [np.bool, [True, False]],}

# 3 must have a setup function. keep pattern as some filters require setup.
def setup():
    return None

# 4 function must have imfilter.
def imfilter(src,
            edge_thresh=40,
            block_size=50,
            apply_focus_filter=True,
            apply_clearedge_filter=True,
            contour_color=(0,255,0),
            **kwargs):

    # apply a threshold value to convert grayscale image to binary image
    thresh, gray = prethresh_filter(src.copy(), block_size=block_size)
    labels = cal_grad_img(src.copy(), edge_thresh=30)
    
    return (labels, thresh)

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

    img = data.brightmudflocs()

    labels, contour_img = imfilter(img, **params)
    f, ax = plt.subplots(1,2, dpi=250)

    ax[0].imshow(labels)
    ax[1].imshow(contour_img)
