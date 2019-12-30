# Development


## Creating a new image filter
Users interested in developing their own image filters -- Python scripts that follow a template in Safas -- should follow the considerations below. It is suggested to examine the source code while reading these instructions to understand the format of the image filters.

Four main steps to making a new image filter:

* **Input.** To be compatible with the analysis and visualization tools in Safas, the input of the filter must be a 3-channel UINT8 image, and any number of key-word arguments (kwargs in Python.)

* **Output.** Must be two images. One 3-channel UINT8 grayscale image with the outline of the detected objects overlaid -- using OpenCV contours function -- and one single channel UINT32 label map image.

* **GUI parameter control.** Safas will automatically generate a user interface for your filter if you include a global dictionary at the top of the script called ''define_vars''. The user may set the type of variable to ''int'' or ''bool'', set the default and min and max values -- where applicable -- and the GUI user control will be automatically generated.

* **Filter import.** Add the name of your filter to the list of modules imported in ''safas/filters/__init__.py'', so it will be available when the GUI is loaded. For example, the init file should look something like this:

``` Python
from . import sobel_focus, adapt_thresh, my_new_filter
```
