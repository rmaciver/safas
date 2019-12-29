# Overview

# safas
**s**edimentation **a**nd **f**loc **a**nalysis **s**oftware

A Python module for processing and interpretation of images and videos of flocs, a.k.a. aggregates, a.k.a. cohesive sediments.

This package permits the direct analysis of images and videos of flocs. Size, morphology and settling rate information may be captured and saved in an easily accessible format. Several features of this package are documented in Jupyter notebooks in the notebooks directory, including how to use the filters and visualizing the results.

The main modules are:

* **gui** and **trackpanel** contain components for visualization, image processing control, and object selection.

* **track** contains classes and scripts that permit manual or semi-automated labelling of flocs in a time series of images.

* **filter** contains a set of scripts that were developed for the special case of segmenting and extracting flocs from images and video.

## Why Safas?
**Safas** is written in Python. It is open-source and the image filters are acessible and extensible. The image filters use functions from  and were designed and tested for segmenting and quantifying images of flocs.

**Safas** has several features that make if useful for the analysis of floc images and video:
* **"One-step" analysis.** The user can open a video file and directly process the frames. The results may exported to an .xlsx file in tabular format for analysis or reporting.

* **Optimized floc filters.** Image analysis can be challenging and each image class often requires a different treatment. The pre-defined filters are built on OpenCV and Scikit-Image and have been designed to work well with images of flocs.

* **GPU-enabled.** Several filters in safas are GPU-enabled, through OpenCV with OpenCL, if the software environment is configured correctly during installation.
