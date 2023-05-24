"""
Load test images.

Note: this is the same loader mechanism used by scikit-image

"""

import os
import numpy as _np
from warnings import warn
import pandas as pd
import cv2

from pathlib import Path
import os.path as osp
data_dir = str(Path(__file__).absolute().parents[0])

__all__ = ['mudflocs']

def _load(f): 
    filename = Path(data_dir).joinpath(f)
    return cv2.imread(str(filename))

def noisy(): return _load("noisy.png")

def mudflocs():
    """Gray-level "mudflocs" image.
    Example image of mud flocs in settling colum.
    Higher number density
    Returns
    -------
    camera : (1000, 1000, 3) uint8 ndarray
        Mudflocs image.
    """
    return _load("mudflocs.png")

def clayflocs():
    """Gray-level "clayflocs" image.
    Example image of clay flocs in settling colum.
    Lower number density
    Returns
    -------
    camera : (1000, 1000) uint8 ndarray
        clayflocs image.
    """
    return _load("clayflocs.png")

def brightmudflocs():
    """Gray-level "clayflocs" image.
    Example image of clay flocs in settling colum.
    Brighter light source w. mean approx. 225 on uint8 scale

    Returns
    -------
    camera : (1000, 1000, 3) uint8 ndarray
        brightmudflocs image.
    """
    return _load("brightmudflocs.png")

def clearfloc():
    """Gray-level "clearfloc" image.
    Example image of a single mud floc with a clear background.

    Returns
    -------
    camera : (512, 512, 3) uint8 ndarray
        clearfloc image.
    """
    return _load("clearfloc.png")

def noisyfloc():
    """Gray-level "noisyfloc" image.
    Example image of a single mud floc with a noisy background.

    Returns
    -------
    camera : (512, 512, 3) uint8 ndarray
        noisyfloc image.
    """
    return _load("noisyfloc.png")

def por_flocs():
    """ results from video measurement of the POR sample


    Returns
    -------
    pandas data frame
    """
    return pd.excel_read('por_flocs.xlsx')
