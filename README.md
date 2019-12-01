# safas
**s**edimentation **a**nd **f**loc **a**nalysis **s**oftware

A Python module for processing and interpretation of images and videos of flocs, a.k.a. aggregates, a.k.a. cohesive sediments.

## Overview
This package permits the direct analysis of images and videos of flocs. Size, morphology and settling rate information may be captured and saved in an easily accessible format. This package is documented in the **notebooks\examples** directory and a more detailed guide is in **docs\README.md**

The main modules are:

* **gui** contains components that take care of reading, writing, and displaying images.

* **track** contains classes and scripts that permit manual or semi-automated labelling of flocs in a time series of images.

* **filter** contains a set of scripts that were developed for the special case of segmenting and extracting flocs from images and video.

Several principles were kept in mind when organizing this software:
* A good analysis of floc sedimentation requires careful visual inspection.  
* New users should be able to appreciate how images are processed and analyzed.

There are step-by-step guides to using the filters on individual images and tutorials on preparing new image filters in the **notebooks\examples** directory.

## To do in dev branch

### Installation
There are two suggested methods to install this software:

* Docker image. This is the suggested method. A Dockerfile has been prepared for Windows users to make installation and use of this software more reliable.  

* Users familiar with installing packages in a virtual environment may download and install it directly using the environment.yml and setup.py files.


#### Docker setup



#### Virtual environment setup

**GPU-enabled OpenCV in Windows**

Here is a quick way to get OpenCL-enabled OpenCV working in a virtual environment in Windows.
1. download the prebuilt OpenCV binary for windows
2. activate the conda environment
3. in cmd run setup_vars_opencv4 in opencv\build
4. copy .pyd file from opencv\build\python\cv2\python-3.6 to the cond env Lib\site_packages

### command line access
refer to tofu style bin directory and gui model
