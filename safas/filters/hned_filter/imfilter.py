# -*- coding: utf-8 -*-
"""

holistically nested edge detection

a pre-trained neural network to segment images

refer to
https://github.com/s9xie/hed/tree/master/include/caffe
"""

# import the necessary packages
import argparse
import cv2
import os
import numpy as np

from skimage.measure import label, regionprops

import matplotlib.pyplot as plt

from safas.filters.imfilters_module import (focus_filter,
                                           prethresh_filter,
                                           clearedge_filter,
                                           add_contours, 
                                           perim_filter)
                                           
define_args = {'mean': [np.int, [0, 255, 120]],
               'edge_thresh': [np.int, [0, 255, 120]],
               'edge_distance': [np.int, [0,9, 1]],
               'apply_focus_filter': [np.bool, [True, False, True]],
               'apply_clearedge_filter': [np.bool, [True, False, True]],
               'contour_thickness': [np.int, [1, 4, 1]]}

def setup():

    protopath = 'edge_model/deploy.prototxt'
    modelpath = 'edge_model/hed_pretrained_bsds.caffemodel'

    net = cv2.dnn.readNetFromCaffe(protopath, modelpath)
    cv2.dnn_registerLayer("Crop", CropLayer)

    return ('net', net)

def imfilter(src, 
             net, 
             mean=50, 
             edge_distance=2,
             apply_nn_edge_filter=True,
             apply_clearedge_filter=True,
             contour_thickness=1,
             contour_color=(0,255,0), 
             **kwargs):
    """
    setup CropLayer and resources to pass net
    """
    thresh, gray = prethresh_filter(src.copy(), img_thresh)
    ret, labels = cv2.connectedComponents(thresh)
    
    (H, W) = src.shape[:2]
    mean = np.repeat(mean, 3)
    blob = cv2.dnn.blobFromImage(src,
                                 scalefactor=1.0,
                                 size=(W, H),
                                 mean=50,
                                 swapRB=False,
                                 crop=False)
    net.setInput(blob)
    hed = net.forward()
    hed = cv2.resize(hed[0, 0], (W, H))
    hed = (255 * hed).astype(np.uint8)
    print('hed unique:', np.unique(hed))
    if apply_nn_edge_filter:
       labels = perim_filter(labels, hed, edge_dist=edge_dist)

    if apply_clearedge_filter:
        labels = clearedge_filter(labels)

    contour_img = add_contours(src.copy(), labels,
                              contour_color=contour_color,
                              contour_thickness=contour_thickness)

    return (labels, contour_img)



class CropLayer(object):
    def __init__(self, params, blobs):
		# initialize our starting and ending (x, y)-coordinates of
		# the crop
	    self.startX = 0
	    self.startY = 0
	    self.endX = 0
	    self.endY = 0

    def getMemoryShapes(self, inputs):
		# the crop layer will receive two inputs -- we need to crop
		# the first input blob to match the shape of the second one,
		# keeping the batch size and number of channels
	    (inputShape, targetShape) = (inputs[0], inputs[1])
	    (batchSize, numChannels) = (inputShape[0], inputShape[1])
	    (H, W) = (targetShape[2], targetShape[3])

		# compute the starting and ending crop coordinates
	    self.startX = int((inputShape[3] - targetShape[3]) / 2)
	    self.startY = int((inputShape[2] - targetShape[2]) / 2)
	    self.endX = self.startX + W
	    self.endY = self.startY + H

		# return the shape of the volume (we'll perform the actual
		# crop during the forward pass
	    return [[batchSize, numChannels, H, W]]

    def forward(self, inputs):
		# use the derived (x, y)-coordinates to perform the crop
	    return [inputs[0][:, :, self.startY:self.endY,
				self.startX:self.endX]]

if __name__ =='__main__':
    reload=False
    if reload:
        from safas import data
        params = {'mean' :50,
                  'apply_focus_filter': True,
                  'apply_clear_edge_filter': True,
                  }
        src = data.noisy()
        key, value = setup()
        params[key] = value
        params['mean'] = 50
#    #key, value = setup()
#    params = {'mean': (1, 1, 1)}
#    params[key] = value
    hed, hed = imfilter(src=src, **params)

#    th, im_th = cv2.threshold(hed, 80, 255, cv2.THRESH_BINARY)
#
#    # Copy the thresholded image.
#    im_floodfill = im_th.copy()
#
#    # Mask used to flood filling.
#    # Notice the size needs to be 2 pixels than the image.
#    h, w = im_th.shape[:2]
#
#    mask = np.zeros((h+2, w+2), np.uint8)
#
#    # Floodfill from point (0, 0)
#    cv2.floodFill(im_floodfill, mask, (0,0), 255);
#
#    # Invert floodfilled image
#    im_floodfill_inv = cv2.bitwise_not(im_floodfill)
#
#    # Combine the two images to get the foreground.
#    im_out = im_th | im_floodfill_inv
#
#    th, im_th_im = cv2.threshold(src.copy(), 100, 255, cv2.THRESH_BINARY_INV)
#
#    L = label(im_out)
#
#    kernel = np.ones((3, 3), np.uint8)
#    img2 = im_floodfill_inv.copy()
#    dilate = cv2.dilate(img2, kernel, iterations=1)
#    dilate -= img2
#
#    LD = label(dilate)
#
#
#
    f, ax = plt.subplots(1,3)
    ax[0].imshow(hed)
#    ax[1].imshow(im_floodfill_inv)
#    ax[2].imshow(dilate)
