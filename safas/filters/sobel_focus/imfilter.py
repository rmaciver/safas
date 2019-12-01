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

def imfilter(src,
            img_thresh=100,
            edge_thresh=40,
            focus_filter=True,
            clearedge_filter=True,
            contour_color=(0,255,0),
            **kwargs):

    # convert to grayscale and de-noise with gaussian blur
    gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    img = cv2.GaussianBlur(gray, (3, 3), 0)

    # apply a threshold value to convert grayscale image to binary image
    ret, thresh = cv2.threshold(img, img_thresh, 255, cv2.THRESH_BINARY_INV)
    # label individual objects in the binary image
    ret, labels = cv2.connectedComponents(thresh)

    # calculate the gradient image
    if focus_filter:
        scale = 1
        delta = 0
        ddepth = cv2.CV_16S

        grad_x = cv2.Sobel(gray, ddepth, 1, 0, ksize=3, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        grad_y = cv2.Sobel(gray, ddepth, 0, 1, ksize=3, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        abs_grad_x = cv2.convertScaleAbs(grad_x)
        abs_grad_y = cv2.convertScaleAbs(grad_y)

        grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)
        N, filt = cv2.threshold(grad, edge_thresh, 255, cv2.THRESH_BINARY)

        # filter the objects in 'labels' image with the gradient image 'filt'
        labels = apply_focus_filter(labels, filt)

    if clearedge_filter:
        labels = apply_clearedge_filter(labels)

    # overlay contours
    ret, thresh = cv2.threshold(labels.astype(np.uint8), 1, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contourimg = cv2.drawContours(src, contours, -1, contour_color, 3)

    return (labels, contourimg)

def apply_clearedge_filter(labels):
    """ clear objects touching edge """

    x = np.arange(0, labels.shape[1])
    y = np.arange(0, labels.shape[0])

    vals = np.array(labels[y[0], x])
    vals = np.append(vals, labels[y, x[0]])
    vals = np.append(vals, labels[y, x[-1]])
    vals = np.append(vals, labels[y[-1], x])

    for v in np.unique(vals):
        labels[np.where(labels==v)] = 0

    return labels

def apply_focus_filter(labels, grad):
    """ remove out of focus flocs by combining labels and gradient images """
    for lab in np.unique(labels):
        xy = np.where(labels==lab)
        vals = grad[xy[0], xy[1]]

        if not vals.any():
            labels[xy[0], xy[1]] = 0

    return labels

if __name__ == '__main__':

    params = {'img_thresh': 90,
               'edge_thresh': 30,
               'focus_filter': True,
               'clearborder_filter': True,
               }
