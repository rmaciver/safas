# -*- coding: utf-8 -*-
"""

-prediction for second frame includes only size, shape
-prediction for 3rd frame includes velocity 
        
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

    def __init__(self, p0=None, props=None, params=None, **kwargs): 
        """
        track_data: identified (+) instances of the object
        props: regionprops info for current image
        """
        self.params = params
        self.track_data = track_data
        
        self.err_max = 10e7
        self.dist_thresh = 500
        self.criteria = {'props': 1, 'disp': 1, 'vel': 1}
        self.obj0 = None
    
    def rank_and_match(self):
        self.rank()
        self.match()
        if self.obj0 is not None: 
            return self.obj0
            print('found a match')
        if self.obj0 is None: 
            print('no match found')
            return None
        
    def rank(self):
        """ N most recent objects is compared to current objects id'd in image
                determine most likely object in forward direction """
        # most recent value
        p0 = self.p0
        props = self.props            
        
        err = np.arange(len(props))
        
        if 'props' in self.criteria:
            props_err = props_err(p0, props)
            err += props_err*self.criteria['props']
            
        if 'dist' in self.criteria:
            dist = cal_dist(p0, props)
            err += props_err*self.criteria['props']
        
        if 'vel' in self.criteria:
            print('compare velocity and direction')
        
        self.err = err
    
    def best_match(self):
        """ one match is returned now. later, return a ranking and allow
            corretion by user.
            match only returned if below a max value
        """
        index = np.argmin(self.err)
        if self.err[index] < self.err_thresh: 
            self.obj0 = index
        else:
            self.obj0 = None

def cal_dist(p0, props):
    dist = np.array([p.centroid for p in props]) - p0.centroid
    dist = np.linalg.norm(dist, axis=1)
    return dist

def dist_err(dist):
    """ a simple metric, assumes slow moving so closer is better"""
    return dist**2
    
def props_err(p0, props):
    """ """
    # can adjust weightings (w) and error function (err_func) 
    area = np.array([p.area for p in props]) - p0.area
    major_axis_length = np.array([p.major_axis_length for p in props]) - p0.major_axis_length
    minor_axis_length = np.array([p.minor_axis_length for p in props]) - p0.minor_axis_length
    orientation = np.array([p.orientation for p in props]) - p0.orientation
    perimeter = np.array([p.perimeter for p in props]) - p0.perimeter
    
    vals = np.array((area, 
                    perimeter, 
                    minor_axis_length, 
                    major_axis_length,
                    orientation, 
                    perimeter,
                    ))
    
    w = np.array([1,1,1,1,1,1]) 
    err = np.apply_along_axis(err_func, 0, vals, w)
    err = err.sum(axis=0)
    return err
    
def err_func(a, w=None):
    """Average first and last element of a 1-D array"""    
    return np.array((w[0]*a[0]**2, 
                     w[1]*a[1]**2, 
                     w[2]*a[2]**2, 
                     w[3]*a[3]**2, 
                     w[4]*a[4]**2, 
                     w[5]*a[5]**2))





def test_img():
    img = np.zeros((1000,1000))
    img[100:200, 120:200] = 255
    img[300:400,350:400] = 255
    img[500:600,50:600] = 255
    return img           


        
#    def cal_disp(self, p1, p2):
#        dist = np.linalg.norm(p2-p1)
#        
#        print('distance:', dist)
#        
if __name__ == '__main__':
    print('Test matching')
    
    
    
    T = test_img()
    L = label(T)
    P = regionprops(L)
   
    
    p0 = P[2]
    
    M = Matcher()
#    err, vals = M.rank_props()
    err = cal_dist(p0, P)
    
   