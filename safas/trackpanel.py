# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 05:18:31 2019

@author: Ryan
"""

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class TrackPanel(QMainWindow):

    status_update_signal = pyqtSignal(str, name="status_update_signal")

    def __init__(self, parent=None, params=None, params_file=None, *args, **kwargs):
        super(TrackPanel, self).__init__(*args, **kwargs)
        # parent is the Stream object
        self.parent = parent
        self.setWindowTitle('tracking')

        self.layout = QGridLayout()
        self.setup_control_panel()
        self.setup_view_panel()
        self.setup_mode_panel()

        w = QWidget()
        w.setLayout(self.layout)
        self.setCentralWidget(w)

        self.setGeometry(100, 1500, 50, 10)
        self.show()

        self.action = 'pause'
        self.click_start()
        self.tracks = TrackLists(parent=self.parent)

        # add shortcut for move to next frame
        self.next_frame_shortcut = QShortcut(QKeySequence("n"), self)
        self.next_frame_shortcut.activated.connect(self.click_next)

    def setup_view_panel(self):
        """ enable/disable NEW, OPEN,TRACKS"""
        top_layout_2 = QGridLayout()

        ctrl_groupbox = QGroupBox('views')

        cb1 = QCheckBox()  # new
        cb2 = QCheckBox()  # open
        cb3 = QCheckBox() # tracks

        top_layout_2.addWidget(QLabel('tracks'), 0, 0)
        top_layout_2.addWidget(cb3, 0, 1)
        cb3.toggled.connect(self.view_box_clicked)
        cb3.view = "tracks"
        cb3.setChecked(True)

        top_layout_2.addWidget(QLabel('open'), 0, 2)
        top_layout_2.addWidget(cb2, 0,3)
        cb2.toggled.connect(self.view_box_clicked)
        cb2.view = "open"
        cb2.setChecked(False)

        top_layout_2.addWidget(QLabel('new'), 0, 4)
        top_layout_2.addWidget(cb1, 0,5)
        cb1.toggled.connect(self.view_box_clicked)
        cb1.view = "new"
        cb1.setChecked(True)

        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 1, 2)

    def setup_mode_panel(self):
        """ enable/disable NEW, OPEN,TRACKS"""
        top_layout_2 = QGridLayout()

        ctrl_groupbox = QGroupBox('modes')

        cb1 = QRadioButton()  # new
        cb2 = QRadioButton()  # open
        cb3 = QRadioButton() # tracks

        top_layout_2.addWidget(QLabel('manual'), 0, 0)
        top_layout_2.addWidget(cb3, 0, 1)
        cb3.setChecked(True)
        cb3.mode = "manual"
        cb3.toggled.connect(self.mode_radio_clicked)

        top_layout_2.addWidget(QLabel('auto'), 0, 4)
        top_layout_2.addWidget(cb2, 0, 5)
        cb2.setChecked(False)
        cb2.mode = "auto"
        cb2.toggled.connect(self.mode_radio_clicked)

        top_layout_2.addWidget(QLabel('auto-step'), 0, 2)
        top_layout_2.addWidget(cb1, 0, 3)
        cb1.setChecked(False)
        cb1.mode = "auto-step"
        cb1.toggled.connect(self.mode_radio_clicked)

        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 1, 3)

    def mode_radio_clicked(self, event=None, **kwargs):
        radioButton = self.sender()
        print('event is:', event)

        if radioButton.isChecked():
            print('button is checked!', radioButton.mode)
            self.parent.params['tracker_control']['mode'] = radioButton.mode

    def view_box_clicked(self, event):
         """ update params from box values """
         cbox= self.sender()
         views_hand = self.parent.params['tracker_control']['views']
         views_hand[cbox.view] = event

    def setup_control_panel(self):
        top_layout_2 = QHBoxLayout()

        ctrl_groupbox = QGroupBox('control')

        list_tracks = QPushButton('list', clicked=self.click_list_tracks)
        refine = QPushButton('refine', clicked=self.click_refine)
        start = QPushButton('start', clicked=self.click_start)
        pause = QPushButton('pause', clicked=self.click_pause)
        next_frame = QPushButton('next frame >', clicked=self.click_next)
        prev_frame = QPushButton('< prev. frame ', clicked=self.click_prev)
        save = QPushButton('save', clicked=self.click_save)
      
        exit_track = QPushButton('exit', clicked=self.click_exit_track)
        help = QPushButton('help', clicked=self.get_help)
        top_layout_2.addWidget(list_tracks)
        top_layout_2.addWidget(refine)
        top_layout_2.addWidget(prev_frame)
        top_layout_2.addWidget(next_frame)
        top_layout_2.addWidget(start)
        top_layout_2.addWidget(pause)
        top_layout_2.addWidget(save)
        top_layout_2.addWidget(help)
        top_layout_2.addWidget(exit_track)
        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 1, 1)

        self.buttons = {'pause': pause,
                        'start': start}

        prev_frame.setEnabled(False)

    def get_help(self, ):
        message = "Track objects by manual selection and linking."

        message += "\n\nshortcuts:"
        message += "\n\n track a new object: highlight the object in the 'new' list, then press keyboard button 'a'"
        message += "\n\n link two objects: highlight one object in the 'open' list and one in the 'new' list, then press keyboard button 'l'"

        message += "\n\ntracks: objects that have been selected by user"
        message += "\n\nopen: the most recent object added to a track (i.e. N - 1)"
        message += "\n\nnew: objects identified in the current frame.)"

        QMessageBox.about(self, "Object Tracking", message)

    def click_start(self):
        """ """
        self.parent.params['improcess']['running'] = True
        self.buttons['pause'].setEnabled(True)
        self.buttons['start'].setEnabled(False)

    def click_pause(self):
        """ """
        self.parent.params['improcess']['running'] = False
        self.buttons['start'].setEnabled(True)
        self.buttons['pause'].setEnabled(False)

    def click_save(self):
        """ """
        self.parent.handler.tracker.save()
    
    def click_next(self):
        """ """
        self.parent.viewer.next_frame()

    def click_prev(self):
        """ """

    def click_list_tracks(self):
        """ reopens the list if closed"""
        self.tracks.vis()

    def click_refine(self):
        """ """
        self.action = 'refine'

    def click_exit_track(self):
        """ """
        self.action = 'exit'
        self.destroy()
        if self.parent is None:
            sys.exit(0)

    def mouse_event(self, event, frame_index, x, y, **kwargs):
        print(event, frame_index, x, y)

class TrackLists(QMainWindow):
    status_update_signal = pyqtSignal(str, name="status_update_signal")
    newopen_outline_signal = pyqtSignal(object, int, name="sinle_outline_signal")

    def __init__(self, parent=None, params=None, params_file=None, *args, **kwargs):
        super(TrackLists, self).__init__(*args, **kwargs)
        self.parent=parent
        self.setWindowTitle('tracklists')

        self.layout = QGridLayout()
        self.setup_lists()
        w = QWidget()
        w.setLayout(self.layout)
        self.setCentralWidget(w)

        self.setGeometry(50, 50, 600, 1000)
        self.show()

        self.lists = ['new', 'tracks', 'open', ]
        self.set_shortcuts()

    def vis(self):
        self.show()

    def set_shortcuts(self):
        # link open end of track to the new object
        self.link_shortcut = QShortcut(QKeySequence("l"), self)
        self.link_shortcut.activated.connect(self.link_pair)
        # add the new object as a new track
        self.newtrack_shortcut = QShortcut(QKeySequence("a"), self)
        self.newtrack_shortcut.activated.connect(self.transfer_new)

        lines = 'keyboard shortcuts:'
        lines += '\n"a" to add object from "new" list'
        lines += '\n"l" to link selected new and open objects'
        lines += '\n"n" to link selected new and open objects'

        self.control_message = lines
        self.status_update_signal.emit(self.control_message)

    def setup_lists(self):
        """ """
        top_layout_2 = QGridLayout()

        ctrl_groupbox = QGroupBox('control')

        self.tracks = QListWidget()
        self.open_objs = QListWidget()
        self.new_objs = QListWidget()

        self.new_objs.itemDoubleClicked.connect(self.transfer_new)
        self.new_objs.currentItemChanged.connect(self.outline_pair)
        self.open_objs.currentItemChanged.connect(self.outline_pair)
        self.tracks.currentItemChanged.connect(self.outline_track)

        top_layout_2.addWidget(QLabel('tracks'), 0, 0)
        top_layout_2.addWidget(QLabel('open'), 0, 1)
        top_layout_2.addWidget(QLabel('new'), 0, 2)

        top_layout_2.addWidget(self.tracks, 1, 0)
        top_layout_2.addWidget(self.open_objs, 1, 1)
        top_layout_2.addWidget(self.new_objs, 1, 2)

        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 1, 1)

    def handle(self, **kwargs):
        """ step to take after image is filtered and labelled """
        print('enter the handle from the stream')
        print('update the new objects')
        self.list_new()
        print('update the open objects')
        self.list_open()

        if self.parent.params['tracker_control']['mode'] == 'manual':
            self.status_update_signal.emit(self.control_message)

        if self.parent.params['tracker_control']['mode'] == 'auto-multi':
            print('predict and link multiple objects through time series')
            frame = self.parent.handler.contour_img
            index = self.parent.handler.frame_index
            tracker = self.parent.handler.tracker
            print('track outline:', val_track)
            val_new = self.parent.handler.tracker.predict_next(frame=frame,
                                                               index=index,
                                                               id_obj=val_track)

        if self.parent.params['tracker_control']['mode'] == 'auto-single':
            print('predict and link single object through time series')

    def list_new(self, **kwargs):
        """ on new frame, add new objects detected"""
        self.new_objs.clear()
        vals = self.parent.handler.tracker.list_new()
        if vals is not None:
            self.new_objs.addItems([str(v) for v in range(vals)])

    def list_open(self, val=None, action='add', **kwargs):
        """ most recent objects added to tracks"""
        self.open_objs.clear()
        vals = self.parent.handler.tracker.list_open()
        if vals is not None:
            self.open_objs.addItems([str(v) for v in vals])

    def transfer_new(self, val=None, action='add', **kwargs):
        """  on double-click, or 'a' key, transfer object to track list """

        if self.parent.params['tracker_control']['mode'] == 'manual':
            val_track, val_open, val_new = self.get_obj_pair(src='open')

            if val_new is not None:
                 self.tracks.clear()
                # add to list of tracked objects
                 frame_index = self.parent.handler.tracker.frame_index
                 self.parent.handler.tracker.add_object(frame_index, val_new)
                 number_tracks = self.parent.handler.tracker.n_tracks()

                 if number_tracks is not None:
                     self.tracks.addItems([str(v) for v in range(number_tracks)])

                 qlist = self.new_objs
                 qlist.takeItem(self.new_objs.currentRow())

    def link_pair(self, **kwargs):
        """ link the selected objects in new and open lists """
        val_track, val_open, val_new = self.get_obj_pair(src='open')
        frame = self.parent.handler.contour_img
        index = self.parent.handler.frame_index
        tracker = self.parent.handler.tracker

        self.parent.handler.tracker.update_object_track(index,
                                                        id_obj=val_track,
                                                        id_curr=val_new)

    def get_obj_pair(self, src='open'):
        """ retrieve selected objects in the new and open lists """
        val_new = self.new_objs.currentItem()

        if val_new is not None:
            val_new = int(val_new.text())

        if src=='open':
            val_open = self.open_objs.currentItem()

            if val_open != None:
                val_open = int(val_open.text())
                val_track = self.open_objs.currentRow()
                self.tracks.setCurrentRow(val_track)
            else:
                val_open, val_track = None, None

        if src=='tracks':
            val_track = self.tracks.currentItem()

            if val_track != None:
                val_track = int(val_track.text())
                val_open = self.tracks.currentRow()
                self.open_objs.setCurrentRow(val_open)
            else:
                val_open, val_track = None, None

        return (val_track, val_open, val_new)

    def outline_pair(self, val,  **kwargs):
        """ outline a single new and open object highlight to user for linking """
        val_track, val_open, val_new = self.get_obj_pair(src='open')

        frame = self.parent.handler.contour_img
        index = self.parent.handler.frame_index
        tracker = self.parent.handler.tracker

        if (val_open is not None) or (val_new is not None):
            tracker.outline_pair(frame.copy(),
                                 index,
                                 val_new=val_new,
                                 val_open=val_open)

    def outline_track(self, **kwargs):
        """ highlight a single track when selected in tracks list box"""
        val_track, val_open, val_new = self.get_obj_pair(src='tracks')

        frame = self.parent.handler.contour_img
        index = self.parent.handler.frame_index
        tracker = self.parent.handler.tracker

        if val_track is not None:
            tracker.outline_track(frame.copy(), index, id_obj=val_track)


def main(params=None, params_file=None):
    global app
    app = QApplication([])
    window = TrackPanel(params=params, params_file=params_file)
    app.exec_()

if __name__ == '__main__':
    main()
