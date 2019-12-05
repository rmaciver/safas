# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 03:37:24 2019

@author: Ryan

refer to
https://github.com/s9xie/hed/tree/master/include/caffe
"""

# import the necessary packages
import argparse
import cv2
import os
 
# construct the argument parser and parse the arguments


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
    path = r'C:\Users\Ryan\Desktop\camera_setup\floctrac-master\floctrac\test\edge_model'
    frame = cv2.imread('49.png')
    (H, W) = frame.shape[:2]
    # load our serialized edge detector from disk
   
    protoPath = os.path.join(path, "deploy.prototxt")
    modelPath = os.path.join(path, "hed_pretrained_bsds.caffemodel")
    
    net = cv2.dnn.readNetFromCaffe(protoPath, modelPath)
     
    # register our new layer with the model
    cv2.dnn_registerLayer("Crop", CropLayer)
    
	# construct a blob out of the input frame for the Holistically-Nested
	# Edge Detector, set the blob, and perform a forward pass to
	# compute the edges
    mean=(50, 50, 50)
    blob = cv2.dnn.blobFromImage(frame, 
                                 scalefactor=1.0, 
                                 size=(W, H),
                                 mean=mean,
                                 swapRB=False, 
                                 crop=False)
    net.setInput(blob)
    hed = net.forward()
    hed = cv2.resize(hed[0, 0], (W, H))
    hed = (255 * hed).astype("uint8")
    
    import matplotlib.pyplot as plt
    
    f, ax = plt.subplots(1,2, dpi=200,)
    ax[0].imshow(hed)
    hed2 = hed > 30
    ax[1].imshow(hed2)
    
    contours, hierarchy = cv2.findContours(hed2, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    img2 = cv2.drawContours(frame, contours, -1, (0,255,0), 3)
    ax[1].imshow(img2) 