# Use

### Processing a video
A description of the GUI components referred to here is given in the ''GUI description'' section.

Load the GUI from the command line with

``` shell
  $ conda activate safas_env
  (safas_env) $ safas
```
   or by double-clicking on the Safas shortcut, as described in the Installation section.

Steps:

2. Click ``input > file``, then select your video file. At this time, the .avi format has been tested.
3. In the video control box, click ``load`` -- to set the parameters and check inputs -- then ``view`` to load the video viewer.
4. The ``load`` button will change to ``release``, which can be pushed at any time to close the viewer and load a new video.  
5. The slider at the bottom of the video viewer may be used to scroll or scrub through the video.
6. Click ``Analyze`` to load the ``track panel`` GUI for access to image processing and object tracking tools.
7. Click ``Next frame >`` to process the first image. The objects detected will be listed in the track lists panel and will be outlined in green in the viewer.
8. If you decide to select a new region to analyze, press the ``pause`` button, then scrub to a new location in the video. Then, press ``start``, to re-start processing the images.
9. Carefully inspect the processed image. Are the flocs segmented properly? Zoom in and out with the magnifying glass or ctrl + mouse wheel. To improve the segmentation results, test different combinations of filters and parameters by loading the image filter parameters dialog.
10. Close the image filter parameters dialog (save the parameters if desired), then press ``next frame >`` to process the next image.
11. If there are any in focus objects, they will be outlined in green and the number corresponding to the object in the segmented image will be displayed in the ``New objects`` list.
12. Click on the ``New objects`` list panel. Press the up and down keys on the keyboard to highlight different objects. The current object will also be highlighted in the viewer. Note that smaller objects may be harder to see. To improve the visualization of small objects, you may open the image filter parameters dialog and increase the contour width.

13. With the ``New objects`` panel active, press the ``a`` key on the keyboard to add an object to the morphological properties and settling velocity analysis. Select as many objects in the frame as you would like.
14. Press the ``n`` key on the keyboard or press the ``next frame >`` button. This will process the next image and the program will attempt to match each object in the previous frame with one of the new objects detected in the new frame.
15. Press the ``n`` key several more times to get an adequate number of object displacements for calculation of velocity.
16. Click on the ``Track List`` panel to show the resulting object tracks.
17. Note that some objects may have been ``lost`` because they were not correlated in one of the frames. If this happens, the software will ``terminate`` the track of that object.
18. Click ``save`` to save the results as an .xlsx file. The morphological properties and velocity data of the objects will be saved.
19. When analyzing several sections of the same video, it is suggested to let the software automatically name the output as ''floc$\_$props$\_$frame$\_$NNNNN.xlsx'' where NNNNN is the number of the last frame analyzed.
20. Click ``plot`` and select variables to plot on the x- and y-axes. The plot window has several built in features for changing the axis appearance and scaling.
21. Note that the appearance of the figure may be changed by clicking on the icons at the top of the figure.
22. Click ``save`` to save the plot to the output folder.
23. Press ``clear lists`` to remove the current analysis. This is necessary before proceeding to analyze another section of video.
24. Analyze a different section of the video.
25. After analyzing several sections of video, press the ``merge`` button to compile the analyses into a single file.
26. Re-plot the results and ensure an adequate sampling of flocs has been achieved.
27. Press ``exit`` on the track panel or ``release`` in the main panel. Another video may now be loaded.
