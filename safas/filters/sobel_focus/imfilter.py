# -*- coding: utf-8 -*-
"""

"sobel_focus" filter

The sobel operator is used to produce a gradient image that may be used to
filter out-of focus flocs.

Notes:
* the focus and clear edge filters should be optimized.

"""
import os
import time
import numpy as np
import copy
import cv2

from safas.filters.imfilters_module import (focus_filter,
                                           prethresh_filter,
                                           clearedge_filter,
                                           add_contours)

# 2 dict to setup the GUI control
define_args = {'img_thresh': [np.int, [0, 255]],
               'edge_thresh': [np.int, [0, 255]],
               'apply_focus_filter': [np.bool, [True, False]],
               'apply_clearedge_filter': [np.bool, [True, False]],}

# 3 must have a setup function. keep pattern as some filters require setup.
def setup():
    return None


def imfilter(src,
            img_thresh=100,
            edge_thresh=40,
            edge_distance=2,
            apply_focus_filter=True,
            apply_clearedge_filter=True,
            contour_color=(0,255,0),
            **kwargs):

    thresh, gray = prethresh_filter(src.copy(), img_thresh)
    ret, labels = cv2.connectedComponents(thresh)

    if apply_focus_filter:
       labels = focus_filter(labels, gray, edge_thresh)

    if apply_clearedge_filter:
        labels = clearedge_filter(labels)

    contour_img = add_contours(src.copy(), labels, contour_color=contour_color)

    return (labels, contour_img)


if __name__ == '__main__':
    import sys
    sys.path.append(r'C:\Users\Ryan\Desktop\camera_setup\safas-dev')
    import matplotlib.pyplot as plt
    from safas import data

    params = {'img_thresh': 150,
               'edge_thresh': 30,
               'edge_distance': 1,
               'apply_focus_filter': True,
               'apply_clearedge_filter': True,
               }

    img = data.brightmudflocs()

    labels, contour_img = imfilter(img, **params)
    f, ax = plt.subplots(1,2, dpi=250)

    ax[0].imshow(labels)
    ax[1].imshow(contour_img)

    from skimage.measure import regionprops

    P = regionprops(labels)
