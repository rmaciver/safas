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
#   values are: [type, [MIN, MAX, DEFAULT]]
# define_args = {'img_thresh': [np.int, [0, 255, 120]],
#                'edge_thresh': [np.int, [0, 255, 120]],
#                'edge_distance': [np.int, [0,9, 1]],
#                'apply_focus_filter': [np.bool, [True, False, True]],
#                'apply_clearedge_filter': [np.bool, [True, False, True]],
#                'contour_thickness': [np.int, [1, 4, 1]]}

PARAMS = [
          {"name": "img_thresh",
                "type": "int", 
                "value": 120,
                "limits": (0, 255)
                },
                {'name': 'edge_thresh', 
                "type": "int",
                "value": 90,
                "limits": (0, 255)
                },
                {'name': 'apply_focus_filter', 
                "type": "bool",
                "value": True
                },
                {'name': 'apply_clear_edge_filter', 
                "type": "bool",
                "value": True
                },
                {'name': 'contour_thickness', 
                "type": "int",
                "value": 1,
                "limits": (1, 4)
                },
        ]

EDGE_THRESH = 60
TESTING = True
# 3 must have a setup function. keep pattern as some filters require setup.
def setup():
    return None

def imfilter(src,
            img_thresh=100,
            edge_thresh=40,
            apply_focus_filter=True,
            apply_clear_edge_filter=True,
            contour_thickness=1,
            contour_color=(0,255,0),
            **kwargs):

    thresh, gray = prethresh_filter(src.copy(), img_thresh)
    ret, labels = cv2.connectedComponents(thresh)
    
    if TESTING: edge_thresh = EDGE_THRESH
    if apply_focus_filter:
       labels = focus_filter(labels, gray, edge_thresh)

    if apply_clear_edge_filter:
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
               'edge_thresh': 140,
               'edge_distance': 1,
               'apply_focus_filter': True,
               'apply_clearedge_filter': True,
               }

    img = data.brightmudflocs()

    labels, contour_img = imfilter(img, **params)
    f, ax = plt.subplots(1,2, dpi=250)

    ax[0].imshow(labels)
    ax[1].imshow(contour_img)


