# -*- coding: utf-8 -*-
"""

filter components that can be used in signal chain

"""

import cv2
from skimage.measure import regionprops

import numpy as np
from safas import data
import matplotlib.pyplot as plt

def focus_filter(labels, img, edge_thresh=30, edge_dist=2, **kwargs):
    """ remove out of focus flocs by combining labels and gradient images """
    grad = cal_grad_img(img, edge_thresh=edge_thresh)
    labels = perim_filter(labels, grad, edge_dist=edge_dist)
    
    return labels

def perim_filter(labels, grad, edge_dist=5, show=False, **kwargs):
    """ remove out of focus flocs by combining labels and gradient images
    """
    perim = np.zeros_like(labels, dtype=np.uint8)
    perim[labels > 0] = 255
    kernel = np.ones((edge_dist, edge_dist), np.uint8)
    erosion = perim.copy()
    erosion = cv2.erode(erosion, kernel, iterations=1)
    perim -= erosion

    # convet to bool for & operation
    perimb = perim > 0
    gradb = grad > 0

    fmask = perimb & gradb

    # erode flood mask to remove marginally focused
    kernel = np.ones((1, 1), np.uint8)
    fmask_er = fmask.astype(np.uint8).copy()*255
    fmask_er = cv2.morphologyEx(fmask_er, cv2.MORPH_OPEN, kernel)

    P = regionprops(labels)
    out = np.zeros_like(labels, np.uint8)

    for p in P:
        xy = p.coords
        if fmask_er[xy[:,0], xy[:,1]].any(): 
            out[xy[:,0], xy[:,1]] = p.label
        
    if show:
         f, ax = plt.subplots(1,3)
         ax[0].imshow(perimb)
         ax[1].imshow(fmask)
         ax[2].imshow(out)
    
    return out
   
def cal_grad_img(img, edge_thresh=30):
    # calculate the gradient image
    scale = 1
    delta = 0
    ddepth = cv2.CV_16S

    grad_x = cv2.Sobel(img, ddepth, 1, 0, ksize=3, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
    grad_y = cv2.Sobel(img, ddepth, 0, 1, ksize=3, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
    abs_grad_x = cv2.convertScaleAbs(grad_x)
    abs_grad_y = cv2.convertScaleAbs(grad_y)

    grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)
    N, filt = cv2.threshold(grad, edge_thresh, 255, cv2.THRESH_BINARY)
    return filt

def clearedge_filter(labels):
    """ clear objects touching edge """
    x = np.arange(0, labels.shape[1])
    y = np.arange(0, labels.shape[0])

    # values on the edges, these objects will be filled
    vals = np.array(labels[y[0], x])
    vals = np.append(vals, labels[y, x[0]])
    vals = np.append(vals, labels[y, x[-1]])
    vals = np.append(vals, labels[y[-1], x])

    for v in np.unique(vals):
        labels[np.where(labels==v)] = 0
    return labels

def prethresh_filter(img, img_thresh=90, **kwargs):
    """ convert to grayscale, gaussian blur, apply threshold, label
    note: THRESH_BINARY_INV for dark objects in bright field """
    if img.ndim == 3:
        img2 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if img.ndim == 2:
        img2 = img.copy()

    img2 = cv2.GaussianBlur(img2, (3, 3), 0)
    ret, thresh = cv2.threshold(img2, img_thresh, 255, cv2.THRESH_BINARY_INV)

    return (thresh, img2)

def marker_based_watershed(img, thresh, dist_factor=0, **kwargs):
    """ Apply marker based watershed transform the pre-thresholded image
    Refer to: https://docs.opencv.org/3.4/d3/db4/tutorial_py_watershed.html
    dist_factor may be increased from 0 to 1.
    """
    # noise removal
    kernel = np.ones((3,3),np.uint8)
    opening = cv2.morphologyEx(thresh,cv2.MORPH_OPEN,kernel, iterations = 2)
    # sure background area
    sure_bg = cv2.dilate(opening,kernel,iterations=3)
    # Finding sure foreground area
    dist_transform = cv2.distanceTransform(opening,cv2.DIST_L2, 5)
    dist_factor = dist_factor/100 # note: input as integer, but float used
    ret, sure_fg = cv2.threshold(dist_transform, dist_factor*dist_transform.max(), 255, 0)
    # Finding unknown region
    sure_fg = np.uint8(sure_fg)
    unknown = cv2.subtract(sure_bg,sure_fg)
    # Marker labelling
    ret, labels = cv2.connectedComponents(sure_fg)
    # Add one to all labels so that sure background is not 0, but 1
    labels = labels + 1
    # Now, mark the region of unknown with zero
    labels[unknown==255] = 0

    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    labels = cv2.watershed(img, labels)

    # put background to 0 and -1 edges to 0, for compatibility with other segs
    labels -= 1
    labels[labels== -2] = 0

    return labels

def add_contours(img, labels, contour_color, contour_thickness=1, **kwargs):
    ret, thresh = cv2.threshold(labels.astype(np.uint8), 1, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contourimg = cv2.drawContours(img, contours, -1, contour_color, contour_thickness)

    return contourimg

if __name__ =='__main__':
    print('test the focus_filter')

    img = data.mudflocs()
    thresh, img = prethresh_filter(img, img_thresh=80)
    labels = marker_based_watershed(img, thresh)
    grad = cal_grad_img(img, edge_thresh=100)
    out = nn_perim_filter(labels, grad, edge_dist=2)
    out2 = focus_filter(labels=labels, img=img, edge_thresh=100, edge_dist=2)
    f, ax = plt.subplots(1,3, dpi=250)
    ax[0].imshow(img)
    ax[1].imshow(out)
    ax[2].imshow(out2)
