# -*- coding: utf-8 -*-
"""

Matcher compares position and aera of tracked object to all other objects 
    in the new frame

Notes: 
    * consider other morphological properties or velocity 
    * consider other weighting strategies
    
"""
from skimage.measure import regionprops, label

import numpy as np

KEYS = ['area', 
        'centroid', 
        'major_axis_length', 
        'minor_axis_length', 
        'orientation', 
        'perimeter']

class Matcher():

    def __init__(self, p0=None, props=None, criteria=None, **kwargs): 
        """
        track_data: identified (+) instances of the object
        props: regionprops info for current image
        """
        self.p0 = p0
        self.obj0 = None
        self.props = props
        
        if criteria is not None:
            self.criteria = criteria
        else:
            self.criteria = {'area': 1,
                             'distance': 1,
                             'squared': True,
                             'error_threshold': 5000,
                             }

    def rank_and_match(self):
        self.rank()
        self.match()
        
        if self.obj0 is not None: 
            return self.obj0
            
        if self.obj0 is None: 
            return None
        
    def rank(self):
        """ compared p0 size and distance to objects in the new frame """
        p0 = self.p0
        props = self.props            

        err = np.full(len(props), 0, dtype=np.float64)
        
        if 'distance' in self.criteria:
            print('calculate distances')
            dist = cal_dist(p0, props)
            err += dist*self.criteria['distance']
        
        if 'area' in self.criteria: 
            print('calculate distances')
            area = cal_area(p0, props)
            err += area*self.criteria['area']
        
        if 'squared' in self.criteria: 
            err = err**2
            
        print('err is:', err)
        self.err = err
    
    def match(self):
        """ return best match if below error threshold """
        index = np.argmin(self.err)
        
        if self.err[index] < self.criteria['error_threshold']: 
            self.obj0 = index
        else:
            self.obj0 = None

def cal_dist(p0, props):
    dist = np.array([p.centroid for p in props]) - p0.centroid
    dist = np.linalg.norm(dist, axis=1)
    dist = dist.astype(np.float64)
    return dist

def cal_area(p0, props):
    area = np.array([p.area for p in props]) - p0.area
    area = np.abs(area)
    return err
         
if __name__ == '__main__':
    print('Test matching')
    
    
    
    T = test_img()
    L = label(T)
    P = regionprops(L)
   
    
    p0 = P[2]
    
    M = Matcher()
#    err, vals = M.rank_props()
    err = cal_dist(p0, P)
    
   