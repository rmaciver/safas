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

    params = {'img_thresh': 40,
               'edge_thresh': 70,
               'edge_distance': 1,
               'apply_focus_filter': True,
               'apply_clearedge_filter': True,
               }

    img = data.clayflocs()
    
    labels, contour_img = imfilter(img, **params)
    f, ax = plt.subplots(1,2, dpi=250)
    
    ax[0].imshow(labels)
    ax[1].imshow(contour_img)
    
    from skimage.measure import regionprops
    
    P = regionprops(labels)
    