# -*- coding: utf-8 -*-
"""

try to calculate approximate weighting of matching criteria

"""

import numpy as np



dists = np.array([20, 50, 200, 1000, 500, 1250])

dist_err = dists**2

print('dist_err:', dist_err)

area_err = np.array([10, 200, 500, 1000, 20000, 15])

print('abs_area_err:', area_err)

wts = np.array([1, 1])




