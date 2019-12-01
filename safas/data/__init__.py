"""
Load test images.

Note: this is the same loader mechanism used by scikit-image

"""

import os as _os
import skimage
import numpy as _np
from warnings import warn

import os.path as osp
data_dir = osp.abspath(osp.dirname(__file__))

__all__ = ['mudflocs']

def load(f, as_gray=False):
    """Load an image file located in the data directory.
    Parameters
    ----------
    f : string
        File name.
    as_gray : bool, optional
        Whether to convert the image to grayscale.
    Returns
    -------
    img : ndarray
        Image loaded from ``skimage.data_dir``.
    Notes
    -----
    This functions is deprecated and will be removed in 0.18.
    """
    warn('This function is deprecated and will be removed in 0.18. '
         'Use `skimage.io.load` or `imageio.imread` directly.',
         stacklevel=2)
    return _load(f, as_gray=as_gray)


def _load(f, as_gray=False):
    """Load an image file located in the data directory.
    Parameters
    ----------
    f : string
        File name.
    as_gray : bool, optional
        Whether to convert the image to grayscale.
    Returns
    -------
    img : ndarray
        Image loaded from ``skimage.data_dir``.
    """
    # importing io is quite slow since it scans all the backends
    # we lazy import it here
    from skimage.io import imread
    return imread(_os.path.join(data_dir, f), plugin='pil', as_gray=as_gray)


def mudflocs():
    """Gray-level "mudflocs" image.
    Example image of mud flocs in settling colum.
    Higher number density
    Returns
    -------
    camera : (512, 512, 3) uint8 ndarray
        Mudflocs image.
    """
    return _load("mudflocs.png")

def clayflocs():
    """Gray-level "clayflocs" image.
    Example image of clay flocs in settling colum.
    Lower number density
    Returns
    -------
    camera : (512, 512, 3) uint8 ndarray
        clayflocs image.
    """
    return _load("clayflocs.png")
