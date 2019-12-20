#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

include methods to load resources for hned nn filter

"""

from . import imfilter
import cv2

def register_dnn():
    
    protopath = 'edge_model/deploy.prototxt'
    modelpath = 'edge_model/hed_pretrained_bsds.caffemodel'

    net = cv2.dnn.readNetFromCaffe(protopath, modelpath)
    cv2.dnn_registerLayer("Crop", CropLayer)

    return ('net', net)
