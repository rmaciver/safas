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



def setup(res_path=None):
    """
    run before filter is applied. in this case, the net will be added to 
    kwargs passed to the filter at runtime
    """
    if res_path == None:
        res_path = r'C:\Users\Ryan\Desktop\src\safas-dev\safas'

    basepath = os.path.join(res_path, 'filters/hned_filter/edge_model')
    protopath = os.path.join(basepath, 'deploy.prototxt')       
    modelpath = os.path.join(basepath, 'hed_pretrained_bsds.caffemodel')
    
    net = cv2.dnn.readNetFromCaffe(protopath, modelpath)
    cv2.dnn_registerLayer("Crop", CropLayer)
    
    # if something is returned, it should be added to params as a kwarg 
    # i.e. the tuple returned should be the key and value
    return ('net', net)

def imfilter(src, net, mean=(50,50,50),**kwargs):
    """  
    setup CropLayer and resources to pass net
    """  
    (H, W) = src.shape[:2]

    blob = cv2.dnn.blobFromImage(src,
                                 scalefactor=1.0,
                                 size=(W, H),
                                 mean=mean,
                                 swapRB=False,
                                 crop=False)
    net.setInput(blob)
    hed = net.forward()
    hed = cv2.resize(hed[0, 0], (W, H))
    hed = (255 * hed).astype(np.uint8)
    return hed


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
    from safas import data
    src = data.brightmudflocs()
    #key, value = setup() 
    params = {'mean': (1, 1, 1)}
    params[key] = value
    hed = imfilter(src=src, net=params['net'])
    
    th, im_th = cv2.threshold(hed, 80, 255, cv2.THRESH_BINARY)
 
    # Copy the thresholded image.
    im_floodfill = im_th.copy()
     
    # Mask used to flood filling.
    # Notice the size needs to be 2 pixels than the image.
    h, w = im_th.shape[:2]
    
    mask = np.zeros((h+2, w+2), np.uint8)
     
    # Floodfill from point (0, 0)
    cv2.floodFill(im_floodfill, mask, (0,0), 255);
     
    # Invert floodfilled image
    im_floodfill_inv = cv2.bitwise_not(im_floodfill)
     
    # Combine the two images to get the foreground.
    im_out = im_th | im_floodfill_inv
    
    th, im_th_im = cv2.threshold(src.copy(), 100, 255, cv2.THRESH_BINARY_INV)
    
    L = label(im_out)
    
    kernel = np.ones((3, 3), np.uint8)
    img2 = im_floodfill_inv.copy()
    dilate = cv2.dilate(img2, kernel, iterations=1)
    dilate -= img2
    
    LD = label(dilate)
    
    
    
    f, ax = plt.subplots(3,1)
    ax[0].imshow(im_th)
    ax[1].imshow(im_floodfill_inv)
    ax[2].imshow(dilate)

    
    
    