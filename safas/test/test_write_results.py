# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 09:23:03 2019

@author: Ryan
"""
import os
import sys
from glob import glob
import pandas as pd
import matplotlib.pyplot as plt

keys = ['area', 
        'equivalent_diameter', 
        'perimeter', 
        'euler_number',  
        'minor_axis_length', 
        'major_axis_length',
        'extent',]
        
def plot_prop(tracks, prop, ax=None):
    """ plot histogram of object property """
    if ax is None: 
        f, ax = plt.subplots(1,1, dpi=250, figsize=(3.5, 2.2))
    
    vals = [track[prop] for track in tracks['id']]
    ax.hist(vals)
    
    ax.set_xlabel(prop)
    ax.set_ylabel('counts')
    plt.tight_layout()
    
def save_props(tracks, dir_out=None):
    """ write track objects to pandas frame 
        vals = {'frame_index': frame_index,
                'id_curr':     id_curr,
                'centroid':    prop.centroid,
                'prop':        prop,
                'v':           v,}

        tracks['id'][id_obj] = [vals]
    """
    # take the first instance in each track list
    P = [t['prop'] for t in tracks]    
    T = [ {ky: prop[ky] for ky in keys} for prop in P]
    df = pd.DataFrame(T)
    
    # check existing files in dir_out/data
    val =  len(glob(os.path.join(dir_out,'data', '*.xlsx')))
    name = 'floc_props_%d.xlsx' % (val + 1)
    fname = os.path.join(dir_out,'data', name)
    # write to excel file
    df.to_excel(fname)


if __name__ == '__main__':

    reload=False
    if reload:
        import sys
        sys.path.append(r'C:\Users\Ryan\Desktop\camera_setup\safas-dev')
        import matplotlib.pyplot as plt
        from safas import data
        from safas.filters.sobel_focus.imfilter import imfilter
        params = {'img_thresh': 40,
                   'edge_thresh': 70,
                   'apply_focus_filter': True,
                   'apply_clearedge_filter': True,
                   }
    
        img = data.clayflocs()
        
        labels, contour_img = imfilter(img, **params)
        f, ax = plt.subplots(1,2, dpi=250)
        
        ax[0].imshow(labels)
        ax[1].imshow(contour_img)
        
        from skimage.measure import regionprops
        
        P = regionprops(labels)
    df = save_props(P, dir_out='C:/Users/Ryan/Desktop/test')
    
    ps = [p.area for p in P]
    
    #plot_prop(ps, 'area')
    