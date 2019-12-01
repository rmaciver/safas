# Safas
**S**edimentation **a**nd **F**loc **A**nalysis **S**oftware

A Python module for processing and interpretation of images and videos of flocs, a.k.a. aggregates, a.k.a. cohesive sediments.

*Note*: This package under development.

## Overview
This package permits the direct analysis of images and videos of flocs. Size, morphology and settling rate information may be captured and saved in an easily accessible format. At this time, this package is documented with example uses of the image filters in the directory **notebooks**.

Several principles were kept in mind when organizing this software:
* A good analysis of floc sedimentation requires careful visual inspection.  
* New users should be able to appreciate how images are processed and analyzed.

## Development
This package is under development. The master branch contains one filter and a jupyter notebook that demonstrates segmentation and analysis of single images.

Current modifications and extensions in the **dev** branch of this repository package include:
* **gui** module for manual particle selection
* **tracker** module for labelling and tracking objects
* **installation** setup.py and Dockerfiles.
