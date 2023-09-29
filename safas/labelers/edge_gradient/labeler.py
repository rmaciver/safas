"""
safas/labelers/edge_gradient/labeler.py

Identify objects that have a "crisp" outline (i.e. above a threshold in the gradient image). Inspired by Keyvani and Strom (2013) paper for
    an automated floc identification method. 

@article{keyvani2013fully,
  title={A fully-automated image processing technique to improve measurement of suspended particles and flocs by removing out-of-focus objects},
  author={Keyvani, Ali and Strom, Kyle},
  journal={Computers \& Geosciences},
  volume={52},
  pages={189--198},
  year={2013},
  publisher={Elsevier}
}

"""

import numpy as np
import cv2

params = {
    "name": "kwargs", 
    "title": "Parameters",
    "type": "group", 
    "children": 
    [	
        {"name": "brightfield", "title": "Brightfield", "type":  "bool", "value": True, "readOnly": True},
        {"name": "thresh_val", "title": "Threshold talue", "type":  "float", "limits": [0, 255], "value": 120},
        {"name": "apply_grad_filter", "title": "Edge grad. filter", "type":  "bool", "value": True},
        {"name": "grad_thresh_val", "title": "Edge grad. val.", "type":  "int", "limits": [0, 255], "value": 30},
        {"name": "apply_min_px_filter", "title": "Min. size filter", "type":  "bool", "value": True},
        {"name": "area_min_px", "title": "Min. size (px)", "type":  "int", "value": 5},
        {"name": "cal_axis_length", "title": "Cal. axis length", "type":  "bool", "value": False, "visible": False},
        {"name": "add_images", "title": "Add obj. images", "type":  "bool", "value": False, "visible": False},
    ]
}

def setup(): return None

def labeler(src, 
    brightfield:bool=True,
    thresh_val:int=120,
    apply_grad_filter:bool=True,
    apply_blur:bool=True,
    blur_kernel_size:int=3,
    grad_thresh_val:int=80,
    apply_min_px_filter:bool=True,
    area_min_px:int=5,
    cal_axis_length:bool=False,
    clear_edge_filter:bool=True,
    frame_idx:int=None,
    add_obj_images:bool=False, 
    return_objects:bool=True,
    **kwargs
    ) -> dict:
    """ Identify objects that have a "crisp" outline (i.e. above a threshold in the gradient image). Inspired by Keyvani and Strom (2013) paper for an automated floc identification method. 
        
    Parameters: 
    ----------
        src, 
        brightfield:bool=True,
        thresh_val:int=120,
        apply_grad_filter:bool=True,
        grad_thresh_val:int=80,
        apply_min_px_filter:bool=True,
        area_min_px:int=5,
        cal_axis_length:bool=False,
        clear_edge_filter:bool=True,
        frame_idx:int=None
        return_objects:bool=True
    Returns: 
    ----------
        objs (dict) 
    """
    if src.ndim == 3: 
        src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)

    if apply_blur: 
        src = cv2.GaussianBlur(
            src, 
            (blur_kernel_size, blur_kernel_size), 
            0
        )
    
    if brightfield: # thresh_inv = True is brightfield, ie the objects are darker than the field
        ret, thresh = cv2.threshold(src, thresh_val, 255, cv2.THRESH_BINARY_INV)
    else: 
        ret, thresh = cv2.threshold(src, thresh_val, 255, cv2.THRESH_BINARY)

    _, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh, 4, cv2.CV_32S)
    del thresh
    obj_idxs, coords = labels_to_coords(labels) # get coords of each label in the image
    
    area = stats[:, 4]
    bbox = stats[:,:4]

    if clear_edge_filter: 
        obj_idxs_fill = objs_on_edge(labels)
        labels = fill_coords(labels, coords, obj_idxs_fill)
        obj_idxs = np.setdiff1d(obj_idxs, obj_idxs_fill)

    if apply_grad_filter: 
        grad = cal_grad_img(src, grad_thresh_val=grad_thresh_val)
        obj_idxs, grad_counts = np.unique(labels[grad>0], return_counts=True)
        del grad
        obj_idxs_fill = np.setdiff1d(np.unique(labels), obj_idxs)
        labels = fill_coords(labels, coords, obj_idxs_fill)

    if apply_min_px_filter: 
        obj_idxs_fill = np.intersect1d(np.argwhere(area < area_min_px).ravel(), obj_idxs)
        labels = fill_coords(labels, coords, obj_idxs_fill)
        obj_idxs = np.setdiff1d(obj_idxs, obj_idxs_fill)

    if return_objects: 
        objs = format_output_objects(obj_idxs=obj_idxs, 
                                    bbox=bbox, 
                                    area=area, 
                                    centroids=centroids, 
                                    coords=coords,
                                    labels=labels, 
                                    src=src, 
                                    cal_axis_length=cal_axis_length,
                                    add_obj_images=add_obj_images,
                                    frame_idx=frame_idx
                                    )
        return objs
    else: 
        return None
    
def cal_grad_img(img, grad_thresh_val=30):
    """ calculate the gradient image in two directions """
    scale = 1
    delta = 0
    ddepth = cv2.CV_16S

    grad_x = cv2.Sobel(img, ddepth, 1, 0, ksize=3, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
    grad_y = cv2.Sobel(img, ddepth, 0, 1, ksize=3, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
    abs_grad_x = cv2.convertScaleAbs(grad_x)
    abs_grad_y = cv2.convertScaleAbs(grad_y)

    grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)
    N, filt = cv2.threshold(grad, grad_thresh_val, 255, cv2.THRESH_BINARY)
    return filt

def objs_on_edge(labels):
    """ clear objects touching edge """
    x  = labels[[0, labels.shape[0]-1], :] # NOTE: no -1 index in cython
    y = labels[:, [0, labels.shape[1]-1]]
    return np.unique(np.hstack([x.ravel(),y.ravel()]))

def fill_coords(labels, coords, obj_idxs): 
    pts = np.vstack([coords[obj_idx] for obj_idx in obj_idxs])
    labels[pts[:,0], [pts[:,1]]] = 0
    return labels

def compare_idxs_lbls(labels, obj_idxs, disp=False): 
    # compare obj_idxs and labels
    idxs_labels = np.unique(labels)
    diffs = np.setdiff1d(obj_idxs, idxs_labels)
    if disp: 
        print(f"labels contains: {idxs_labels}")
        print(f"bj_idxs contains: {obj_idxs}")
        print(f"diffs are: {diffs}")
    return diffs

def labels_to_coords(x): 
    """  
    Return list that contains indices of each  unique values in x
    ----------
        x (np.array): Array with arbitrary dimensions
    Returns
    -------
        - nique values in x
        - List of assays with indices where a given value in x is found
    """
    x_flat = x.ravel()
    ix_flat = np.argsort(x_flat)
    u, ix_u = np.unique(x_flat[ix_flat], return_index=True)
    ix_ndim = np.unravel_index(ix_flat, x.shape)
    ix_ndim = np.c_[ix_ndim] if x.ndim > 1 else ix_flat
    return u, np.split(ix_ndim, ix_u[1:])

def format_output_objects(obj_idxs, 
                          bbox, 
                          area, 
                          centroids, 
                          coords, 
                          labels=None, 
                          src=None, 
                          cal_axis_length=False,
                          add_obj_images=False,
                          frame_idx=None): 
    """ Format object output for handling in Tracker and ViewerWindow
    """
    objs = dict()
    
    obj_idx_l = 1

    diffs = compare_idxs_lbls(labels, obj_idxs, disp=False)
    
    if len(diffs) > 0: 
        print(f"FORMAT OBJS obj_idxs diffs: {obj_idxs}", warning=True)
 
    for ix, obj_idx in enumerate(obj_idxs): 
        if obj_idx == 0: continue # exclude 0 object (background)
        if area[obj_idx] == 0: continue
        x,y,w,h = bbox[obj_idx]
        mask = labels[y:(y+h), x:(x+w)] # ,w,h,a
        contours_i, hierarchy = cv2.findContours((mask*255).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours_coor = contours_i[0].reshape(-1, 2)

        if cal_axis_length: # much faster to only calculate these for objects in tracks
            try: 
                (xm,ym),(ma,mi),angle = cv2.fitEllipse(contours_coor)
                major_axis = max(ma,mi)
                minor_axis = min(ma,mi)
            except: 
                major_axis = max(w,h)
                minor_axis = min(w,h)
            
            if not np.isfinite(major_axis): major_axis = max(w,h)
            if not np.isfinite(minor_axis): minor_axis = min(w,h)
        else: 
            minor_axis, major_axis = None, None

        if add_obj_images: 
            pad = 5
            xmin = np.clip(x-pad, a_min=0, a_max=src.shape[0]) 
            xmax = np.clip(x+w+pad, a_min=0, a_max=src.shape[0])
            ymin = np.clip(y-pad, a_min=0, a_max=src.shape[1]) 
            ymax = np.clip(y+h+pad, a_min=0, a_max=src.shape[1])

            obj_img = src[xmin:xmax, ymin:ymax]
            obj_mask = mask[xmin:xmax, ymin:ymax]
        else: 
            obj_img, obj_mask = None, None

        contours_coor[:,0] += x
        contours_coor[:,1] += y

        objs[obj_idx_l] = {"obj_idx": obj_idx, 
                        "track_idx": None, 
                        "frame_idx": frame_idx,
                        "obj_area": area[obj_idx], 
                        "obj_centroid": centroids[obj_idx], 
                        "obj_contour": contours_coor,
                        "obj_contour_cv": contours_i,
                        "obj_bbox": bbox[obj_idx],
                        "obj_major_axis": major_axis,
                        "obj_minor_axis": minor_axis,
                        "obj_img": obj_img,
                        "obj_img_mask": obj_mask,
                        "image_size": src.shape
                        }
        
        obj_idx_l += 1 # increment now
    
    return objs

# def format_output_objects(obj_idxs, 
#                           bbox, 
#                           area, 
#                           centroids, 
#                           coords, 
#                           labels=None, 
#                           src=None, 
#                           cal_axis_length=False,
#                           add_obj_images=False,
#                           frame_idx=None): 
#     """ Format object output for handling in Tracker and ViewerWindow
#     """
#     objs = dict()
    
#     obj_idx_l = 1

#     diffs = compare_idxs_lbls(labels, obj_idxs, disp=False)
    
#     if len(diffs) > 0: 
#         print(f"FORMAT OBJS obj_idxs diffs: {obj_idxs}", warning=True)
 
#     for ix, obj_idx in enumerate(obj_idxs): 
#         if obj_idx == 0: continue # exclude 0 object (background)
        
#         mask = (labels == obj_idx).astype("uint8")*255
#         if mask.sum() == 0: continue
#         contours_i, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#         contours_coor = contours_i[0].reshape(-1, 2)

#         minor_axis, major_axis = None, None
        
#         if cal_axis_length: # much faster to only calculate these for objects in tracks
#             if len(contours_coor) >= 5: 
#                 ellipse = cv2.fitEllipse(contours_coor)
#                 (xc,yc), (major_axis, minor_axis), angle = ellipse
#             else: 
#                 # fitEllipse function requires >= 5 points
#                 major_axis = max(bbox[obj_idx])
#                 minor_axis = min(bbox[obj_idx])
         
#         if add_obj_images: 
#             pad = 5
#             x, y, dx, dy = bbox[ix]
#             xmin = np.clip(x-pad, a_min=0, a_max=src.shape[0]) 
#             xmax = np.clip(x+dx+pad, a_min=0, a_max=src.shape[0])
#             ymin = np.clip(y-pad, a_min=0, a_max=src.shape[1]) 
#             ymax = np.clip(y+dy+pad, a_min=0, a_max=src.shape[1])

#             obj_img = src[xmin:xmax, ymin:ymax]
#             obj_mask = mask[xmin:xmax, ymin:ymax]
#         else: 
#             obj_img, obj_mask = None, None

#         objs[obj_idx_l] = {"obj_idx": obj_idx, 
#                         "track_idx": None, 
#                         "frame_idx": frame_idx,
#                         "obj_area": area[obj_idx], 
#                         "obj_centroid": centroids[obj_idx], 
#                         "obj_contour": contours_coor,
#                         "obj_contour_cv": contours_i,
#                         "obj_bbox": bbox[obj_idx],
#                         "obj_major_axis": major_axis,
#                         "obj_minor_axis": minor_axis,
#                         "obj_img": obj_img,
#                         "obj_img_mask": obj_mask,
#                         "image_size": src.shape
#                         }
        
#         obj_idx_l += 1 # increment now
    
#     return objs
