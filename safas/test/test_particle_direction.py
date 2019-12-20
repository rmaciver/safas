# -*- coding: utf-8 -*-
"""
Created on Wed Dec 18 13:23:32 2019

@author: Ryan
"""

# test a direction filter

import numpy as np
from scipy.spatial import distance

import numpy as np

def unit_vector(vector):
    # David Wolever https://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python/13849249#13849249
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)

def angle_between(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'::
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.degrees(np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)))

theta_max = 45

p0 = np.array([[1,1],[1,1],[1,1],[1,1], [1,1],[1,1],[10,10]])
p1 = np.array([[0,1],[2,1],[1,0],[1,2], [1.5,1.5],[1.75,1.75],[0,0]])

for i in range(len(p0)):
    dist =  distance.pdist((p0[i], p1[i]), 'euclidean')
    vect = p1[i] - p0[i]
    # the vector [1,0] is "downward" in the image
    angle = angle_between(np.array([1,0]), vect)
#    print('distances:', dist)
#    print('y-direction:', vect)
#    print('angle:', angle)
#    print('accept particle?', (angle < theta_max))

# filter particles not moving with theta of the downward vector

cents = np.array([[5,5], [6,5], [8,5], [11,5], [12,6], [14,7], [15,8]])


dist = np.linalg.norm((cents[1:]-cents[:-1]), axis=1)
vect = cents[1:] - cents[:-1]
mean_angle = np.mean([angle_between(np.array([1,0]), vt) for vt in vect])

if mean_angle < theta_max: 
    print('yes!')
