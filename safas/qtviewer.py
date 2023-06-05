from pathlib import Path
from copy import deepcopy
import itertools
import time
from PySide2 import QtWidgets, QtCore, QtGui 
from PySide2.QtCore import Qt, QTimer

import cv2
import numpy as np

from .app import RESOURCE_PATH
from .prints import print_viewer as print

class PhotoViewer(QtWidgets.QGraphicsView):
    photoClicked = QtCore.Signal(QtCore.QPoint)
    
    def __init__(self, parent=None, layout=None):
        super(PhotoViewer, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QtWidgets.QGraphicsScene(self)
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        
        if layout is not None: layout.addWidget(self)

    def hasPhoto(self): return not self._empty

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0

    def setPhoto(self, pixmap=None):
        if pixmap is None: 
            return None
        if not isinstance(pixmap, QtGui.QPixmap): 
            qimg = QtGui.QImage(pixmap, pixmap.shape[1], pixmap.shape[0], QtGui.QImage.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(qimg)

        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())
        self.fitInView()

    def wheelEvent(self, event):
        if self.hasPhoto():
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            else:
                self._zoom = 0

    def set_zoom(self, zoom=1): 
        """Manually set zoom on image """
        factor = 1.25*zoom
        self._zoom += zoom
        if self._zoom > 0:
            self.scale(factor, factor)

    def toggleDragMode(self):
        if self.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def mousePressEvent(self, event):
        if self._photo.isUnderMouse():
            self.photoClicked.emit(self.mapToScene(event.pos()).toPoint())
        super(PhotoViewer, self).mousePressEvent(event)

class Viewer(PhotoViewer): 
    status_update_signal = QtCore.Signal(str)
    frame_idx_change = QtCore.Signal(int)
    remove_track_signal = QtCore.Signal(int)
    add_object_signal = QtCore.Signal(object, int)
    track_objects_signal = QtCore.Signal(bool)

    def __init__(self, parent=None, layout=None, *args, **kwargs):
        super(Viewer, self).__init__(parent=parent, layout=layout, *args, **kwargs)
 
        if parent is not None: self.parent = parent # access to safas.handler.Handler
        self.fr = QtWidgets.QFrame()
        if layout is not None: layout.addWidget(self.fr)

        qh = QtWidgets.QHBoxLayout()
        if layout is not None: 
            self.fr.setLayout(qh)
        else: 
            self.addLayout(1,2)
        
        self.label = QtWidgets.QLabel()
        self.label.setText(str(0))
        self.label.setFont(QtGui.QFont("Times", 10, QtGui.QFont.Bold))
        qh.addWidget(self.label)
        
        self.slider = QtWidgets.QSlider(orientation=Qt.Horizontal)
        self.slider.setTracking(True)
        self.slider.valueChanged.connect(self.update_video_index)

        qh.addWidget(self.slider)
        
        if layout is None: self.show()
        try: 
            fname = Path(RESOURCE_PATH).joinpath("ui/tracking_plus_words.png")
            image = cv2.imread(str(fname))
            self.update_frame({"raw_image": image, "frame_idx": 0, "objs_an": None, "tracks_an": None}) 
            time.sleep(0.1)
            self.set_zoom(15)   
   
        except Exception as e: 
            print(f"Splash image: {e}", error=True)
        
    @QtCore.Slot(int)
    def update_video_index(self, frame_idx): 
        """ """
        self.frame_idx = frame_idx
        self.label.setText(str(self.frame_idx))
        self.frame_idx_change.emit(self.frame_idx)
    
    @QtCore.Slot(int)
    def inc_video_index(self, frame_idx_inc): 
        """ frame_idx_inc: +/- 1         """
        self.frame_idx += frame_idx_inc
        self.label.setText(str(self.frame_idx))
        self.frame_idx_change.emit(self.frame_idx)

    @QtCore.Slot(int, int)
    def set_slider_range(self, vmin, vmax):
        """ """
        self.slider.setMinimum(vmin)
        self.slider.setMaximum(vmax)
        self.slider.setValue(vmin)
        self.label.setText(str(vmin))

    @QtCore.Slot(object)
    def update_frame(self, fr): 
        """         
        """
        self.frame_idx = fr["frame_idx"]
        self.setPhoto(fr["raw_image"])

        track_idxs, obj_idxs = self.parent.handler.get_items_in_frame(self.frame_idx)
        self.init_annotations() # always clear on new frame
        
        if len(track_idxs) > 0: self.add_tracks(self.frame_idx, track_idxs) 
        if len(obj_idxs) > 0: self.add_objs(self.frame_idx, obj_idxs)

        try: # NOTE frame and index change may come from backend not UI
            self.label.setText(str(self.frame_idx)) 
            self.slider.blockSignals(True)
            self.slider.setValue(self.frame_idx)
            self.slider.blockSignals(False)
        except Exception as e: 
            print(f"Error: did not update label: {e}", error=True)

    def init_annotations(self, disp=True): 
        """ 
            annotations are cleared on new build_frame call
        """
        try: 
            self.annotations
        except AttributeError as e: 
            self.annotations = {"objs": dict(), "tracks": dict()}
            return None
        
        for key, item_type in itertools.product(["objs", "tracks"],["line_item", "contour_item"]):
            
            for idx in self.annotations[key]: 
                try: 
                    item = self.annotations[key][idx][item_type]
                except KeyError:
                    continue  
                
                if not isinstance(item, list): item = [item]
                
                for i in item: 
                    try: 
                        self._scene.removeItem(i)
                    except Exception as e: 
                        if disp: print(f"An. idx {idx} type {key} item {i}: {e}", debug=True)
        
        self.annotations = {"objs": dict(), "tracks": dict()}

    @QtCore.Slot(int, int, bool)
    def add_objs(self, frame_idx, obj_idxs, setHighlight=False): 
        """ """
        if isinstance(obj_idxs, int): obj_idxs = [obj_idxs]
        self.del_objs(frame_idx, obj_idxs) # remove prev. annotations at this obj_idx
        objs_an = self.parent.handler.build_obj_an(frame_idx, obj_idxs)

        for obj_idx in obj_idxs: 
            contour = objs_an["objs"][obj_idx]["obj_contour"]
            c_kwargs = objs_an["kwargs"]
            
            if setHighlight: 
                an = self.annotations["objs"] # remove and replace prev highlight
                obj_idxs_t = [i for i in an if an[i]["highlighted"]]
                if len(obj_idxs_t) > 0:  
                    self.add_objs(frame_idx, [obj_idxs_t[0]], setHighlight=False)
                
                hl_c_kwargs = deepcopy(c_kwargs) # now add current with color modified
                hl_c_kwargs["contour_color"] = hl_c_kwargs["contour_color_active"]
                contour_item = self.add_contour(contour, **hl_c_kwargs)
            else: 
                contour_item = self.add_contour(contour, **c_kwargs) # add current with standard color

            self.annotations["objs"][obj_idx] = {"contour_item": contour_item, 
                                                 "frame_idx": frame_idx,
                                                 "obj_contour": contour,
                                                 "kwargs": c_kwargs,
                                                 "highlighted": setHighlight
                                                 }

    @QtCore.Slot(int, int, bool)
    def del_objs(self, frame_idx, obj_idxs): 
        """ """
        if isinstance(obj_idxs, int): obj_idxs=[obj_idxs]
        for obj_idx in obj_idxs:  
            if obj_idx in self.annotations["objs"]: 
                item = self.annotations["objs"][obj_idx]
                self._scene.removeItem(item["contour_item"])
                self.annotations["objs"].pop(obj_idx)

    # NOTE: add_contour is common to add_objs and add_tracks - ie patches and tracks are just contours   
    def add_contour(self, contour, contour_color=(0,255,0, 125), contour_linewidth=2, 
                    filled=True, closed=True, **kwargs): 
        """ """       
        path = QtGui.QPainterPath()
        pts = [QtCore.QPointF(p[0], p[1]) for p in contour]
        path.addPolygon(QtGui.QPolygonF(pts))
        
        if closed: path.closeSubpath()
        
        myPen = QtGui.QPen(
            QtGui.QColor.fromRgb(*contour_color), 
            contour_linewidth, 
            Qt.SolidLine, 
            Qt.RoundCap, 
            Qt.RoundJoin)
            
        if filled: 
            myBrush = QtGui.QBrush(QtGui.QColor.fromRgb(*contour_color), Qt.SolidPattern)
            return self._scene.addPath(path, pen=myPen, brush=myBrush)
        else: 
            return self._scene.addPath(path, pen=myPen)

    @QtCore.Slot(int, int, bool)
    def add_tracks(self, frame_idx, track_idxs, setHighlight=False, **kwargs): 
        """ """
        if isinstance(track_idxs, int): track_idxs = [track_idxs]
        self.del_tracks(frame_idx, track_idxs)
        tracks_an = self.parent.handler.build_tracks_an(frame_idx, track_idxs)
       
        for track_idx in track_idxs:  
          
            cents = tracks_an["tracks"][track_idx]["obj_centroid"] 
            contour = tracks_an["tracks"][track_idx]["obj_contour"]
            t_kwargs = tracks_an["kwargs"]
            
            if setHighlight: 
                an = self.annotations["tracks"]
                track_idxs_t = [i for i in an if an[i]["highlighted"]]
                if len(track_idxs_t) > 0: 
                    self.add_tracks(frame_idx, [track_idxs_t[0]], setHighlight=False)
                # hl with modified color
                hl_t_kwargs = deepcopy(t_kwargs)
                hl_t_kwargs["contour_color"] = hl_t_kwargs["contour_color_active"]
                hl_t_kwargs["line_color"] = hl_t_kwargs["line_color_active"]
                line_item, contour_item  = self.add_track(cents, contour, track_kwargs=hl_t_kwargs)
            else: 
                # add current with standard color
                line_item, contour_item  = self.add_track(cents, contour, track_kwargs=t_kwargs)

            item = {"line_item": line_item, 
                    "contour_item": contour_item, 
                    "obj_centroid": cents,
                    "obj_contour": contour, 
                    "highlighted": setHighlight, 
                    "kwargs": t_kwargs}

            self.annotations["tracks"][track_idx] = item

    @QtCore.Slot(int, int, bool)
    def del_tracks(self, frame_idx, track_idxs): 
        """ """
        if isinstance(track_idxs, int): track_idxs = [track_idxs]
        for track_idx in track_idxs:  
            if track_idx in self.annotations["tracks"]: # remove prev. QT item
                item = self.annotations["tracks"][track_idx]
                try: 
                   self._scene.removeItem(item["line_item"])
                except Exception as e: 
                    print(f"{item['line_item']} not removed: {e}")
                
                for gpi in item['contour_item']: 
                    try: 
                        self._scene.removeItem(gpi)
                    except Exception as e: 
                        print(f"gpi not removed: {e}")
                
                self.annotations["tracks"].pop(track_idx)

    def add_track(self, cents, contour, track_kwargs, **kwargs): 
        """ """
        contour_keys = ["contour_color","contour_linewidth"]
        line_keys = ["line_color", "line_linewidth"]
        # ---- link centroids in track with a contour
        line_kwargs = dict((ck, track_kwargs[lk]) for ck, lk in zip(contour_keys,line_keys) )
        line_item = self.add_contour(cents, closed=False, filled=False, **line_kwargs)
        # ---- outline contours for all objects in track
        contour_kwargs = dict((k, track_kwargs[k]) for k in contour_keys)
        contour_item = []
        for ctr in contour: 
            ci = self.add_contour(ctr, **contour_kwargs)
            contour_item.append(ci)
        
        return line_item, contour_item
