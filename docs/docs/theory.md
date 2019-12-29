# Object morphology



The object properties are calculated with the Scikit-Image function \href{https://scikit-image.org/docs/dev/api/skimage.measure.html#skimage.measure.regionprops}{regionprops}. A complete description of these properties may be found in the in the Scikit-Image documentation. At this time, the properties in Table \ref{tab:props} are stored in the output .xlsx file.

\begin{table}[]
	\centering
	\caption{Morphological object properties}
	\label{tab:props}
	\begin{tabular}{ll} \toprule
		Property             & Unit       \\  \midrule
		area                 & [$\mu$m$^2$] \\
		equivalent\_diameter & [$\mu m$]    \\
		perimeter            & [$\mu m$]    \\
		euler\_number        & [--]         \\
		minor\_axis\_length & [$\mu m$]    \\
		major\_axis\_length  & [$\mu m$]    \\
		extent               & [--]      \\ \bottomrule  
	\end{tabular}
\end{table}

# Velocity and object tracking
If a selected object is linked to an object in the next frame, the instantaneous velocity will be calculated based on the displacement of the object centroid, area, and the frame rate of the video. In brief: the best match of an object in the previous frame and an object in the current frame will be assigned to the nearest object with the most similar area. In the default mode, a simple sum of distance and area is made to determine the best match. The velocity will be calculated for each object displacement, and reported with a standard deviation as summarized in Table \ref{tab:evl}

# Object tracking

# Trajectory
A trajectory filter has been added to avoid tracking objects with the incorrect trajectory -- i.e. objects that are not moving ``downward'' in the image. The filter calculates the absolute value of the angle between the object direction and [1,0] -- i.e. ``down'' in the image; then removes objects with an average trajectory that exceeds the maximum angle defined in the parameters. Refer to the Safas module tracker.py for more details of the implementation. At this time, the user must set the maximum angle manually in the configuration file, by changing the value of the parameter ``max$\_$object$\_$angle.''

\begin{table}[]
	\centering
	\caption{Object velocity calculation}
	\label{tab:evl}
	\begin{tabular}{lll}

		property & unit & description \\ \midrule

		vel\_mean & [mm/s]	& velocity \\
		vel\_N	& [--]  & number of objects linked \\
		vel\_std & [mm/s] & standard deviation of velocity \\ \bottomrule
	\end{tabular}
\end{table}

# Effective mass density
