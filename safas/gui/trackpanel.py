# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 05:18:31 2019

@author: Ryan
"""
from copy import deepcopy
from shutil import copyfile
import os
from glob import glob

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import pandas as pd

from safas.gui.filterdialog_pg import FilterDialog
from safas.gui.matcherdialog_pg import MatcherDialog
from safas.gui.savedialog import SaveDialog
from safas.gui.makeplot import MakePlot
from safas.gui.mergepanel import MergePanel
Xp = 0.12

class TrackPanel(QMainWindow):

    status_update_signal = pyqtSignal(str, name="status_update_signal")

    def __init__(self, parent=None, params=None, params_file=None, *args, **kwargs):
        super(TrackPanel, self).__init__(*args, **kwargs)

        # parent is the Stream object
        self.parent = parent
        self.setWindowTitle('tracking')

        self.buttons = {}
        self.tracks = None
        self.matcherdialog = None
        self.paramsdialog = None

        self.layout = QGridLayout()
        self.setup_control_panel()
        self.setup_track_control()
        self.filter_control_panel()

        w = QWidget()
        w.setLayout(self.layout)
        self.setCentralWidget(w)

        x = int(self.parent.dt_width*Xp)
        y = int(self.parent.dt_height*0.8325)
        w = int(self.parent.dt_width*0.8)
        h = int(self.parent.dt_height*0.05)
        self.setGeometry(x, y, w, h)

        self.setMaximumWidth(self.parent.dt_width)
        self.show()
        self.pop_filt()

    def setup(self,):
        self.tracks = TrackLists(parent=self.parent)

    def setup_mode_panel(self):
        """ enable/disable NEW, OPEN,TRACKS"""
        top_layout_2 = QGridLayout()
        ctrl_groupbox = QGroupBox('modes')

        cb1 = QRadioButton()
        top_layout_2.addWidget(cb1, 0, 0)
        top_layout_2.addWidget(QLabel('find-all'), 0, 1)
        cb1.setChecked(True)
        cb1.mode = "find-all"
        cb1.toggled.connect(self.mode_radio_clicked)

        self.mode_boxes = {'manual': None,
                           'find-one': None,
                           'find-all': cb1,}

        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 0, 3)

    def mode_radio_clicked(self, event=None, **kwargs):
        radioButton = self.sender()
        if radioButton.isChecked():
            self.parent.params['tracker_control']['mode'] = radioButton.mode


    def pop_filt(self):
        """ """
        if 'filter' in self.parent.params['improcess']:
            filt = self.parent.params['improcess']['filter']
            index = self.filter_combo.findText(filt)
            self.filter_combo.setCurrentIndex(index)

    def filter_control_panel(self):
        top_layout_2 = QHBoxLayout()
        ctrl_groupbox = QGroupBox('image filter')

        self.filter_combo = QComboBox()
        self.list_filters()
        self.filter_combo.currentIndexChanged.connect(self.change_filter)
        top_layout_2.addWidget(self.filter_combo)

        params = QPushButton('filter params', clicked=self.click_params_dialog)
        top_layout_2.addWidget(params)

        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 0, 0)

    def list_filters(self):
        """ update the selected filter """
        self.filter_combo.addItems(self.parent.list_filters())

    def change_filter(self):
        """ select filter from list """
        print('updating filter to ', self.filter_combo.currentText())
        self.parent.params['improcess']['filter'] = self.filter_combo.currentText()
        # need to load the filter as well?
        self.parent.handler.get_filter(name=self.parent.params['improcess']['filter'])

    def setup_track_control(self):
        """ tracking related buttons"""
        top_layout_2 = QHBoxLayout()

        ctrl_groupbox = QGroupBox('track control')

        list_tracks = QPushButton('show lists', clicked=self.click_list_tracks)
        clear_tracks = QPushButton('clear lists', clicked=self.click_clear_tracks)
        match_dialog = QPushButton('match criteria', clicked=self.match_control_panel)

        save = QPushButton('save', clicked=self.click_save)
        merge = QPushButton('merge', clicked=self.click_merge)
        plot = QPushButton('plot', clicked=self.make_plot)
        plot.setEnabled(True)

        self.buttons['save'] = save
        self.buttons['merge'] = merge
        self.buttons['plot'] = plot

        top_layout_2.addWidget(match_dialog)
        top_layout_2.addWidget(list_tracks)
        top_layout_2.addWidget(clear_tracks)
        top_layout_2.addWidget(save)
        top_layout_2.addWidget(merge)
        top_layout_2.addWidget(plot)
        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 0, 1)

    def setup_control_panel(self):
        top_layout_2 = QHBoxLayout()

        ctrl_groupbox = QGroupBox('video control')
        if 'running' in self.parent.params['improcess']:
            defval = self.parent.params['improcess']['running']
        rb = self.add_radio(name='running', label='process img.', defval=defval)
        next_frame = QPushButton('next >', clicked=self.click_next)

        top_layout_2.addWidget(QLabel('step int.'))
        textedit = QLineEdit('')
        textedit.textChanged.connect(self.text_clicked)
        textedit.name = 'n_frames'

        if 'n_frames' in self.parent.params['improcess']:
            defval = self.parent.params['improcess']['n_frames']
            textedit.setText(str(defval))

        top_layout_2.addWidget(textedit)
        top_layout_2.addWidget(next_frame)
        top_layout_2.addWidget(rb)

        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 0, 2)

    def text_clicked(self, value, key='improcess'):
        rb = self.sender()
        if rb.name in ['n_frames']:
            if rb.text =='':
                rb = 2 # enforce min number of frames
            self.parent.params[key][rb.name] = int(rb.text())

    def radio_clicked(self, value, key='improcess', **kwargs):
        rb = self.sender()
        if rb.isChecked():
            self.parent.params[key][rb.name] = rb.value

    def match_control_panel(self):
        """ Create ui panel to set object match criteria
        """
        self.matcherdialog = MatcherDialog(parent=self, params=self.parent.params['matcher'])
        out = self.matcherdialog.exec_()
        self.parent.params["matcher"] = deepcopy(self.matcherdialog.params)

    def save_params_update(self, params):
        self.parent.params = params

    def click_save(self):
        """ """
        if self.parent.handler.tracker.frame_index != None:
            # filters if save pressed before analysis starts
            if self.parent.params['save']['confirm']:
                self.savedialog = SaveDialog(parent=self, params=self.parent.params)
                self.savedialog.params_update_signal.connect(self.save_params_update)
                self.savedialog.close_signal.connect(self.save_tracker)
                self.savedialog.setup()

            if not self.parent.params['save']['confirm']:
                self.save_tracker()

    def save_tracker(self,):
        self.parent.handler.tracker.save()

        if self.parent.params['save']['clear']:
            self.parent.restart_tracks()

    def click_merge(self):
        """ click files to merge """
        self.mergepanel = MergePanel(parent=self)
        print(self.mergepanel)
        self.mergepanel.show()

    def click_next(self):
        """ """
        self.parent.viewer.next_frame()

    def click_list_tracks(self):
        """ reopens the list if closed"""
        self.tracks.vis()

    def click_clear_tracks(self):
        msg = 'Clear the tracks? Consider to save the data before deleting.'
        buttonReply = QMessageBox.question(self, 'clear objects message', msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if buttonReply == QMessageBox.Yes:
            self.parent.restart_tracks()

    def make_plot(self):
        """ read the output and plot results in saved dataframe   """
        basedir=self.parent.params['output']
        self.plotwin = MakePlot(parent=self.parent, basedir=basedir)

    def click_params_dialog(self):
        """ """
        imfilter = self.parent.handler.imfilter
        imparams = deepcopy(self.parent.params["improcess"]["kwargs"])
        self.paramsdialog = FilterDialog(parent=self, imfilter=imfilter, params=imparams)
        self.paramsdialog.params_test_signal.connect(self.params_test)
        self.paramsdialog.exec_()
        self.parent.params["improcess"]["kwargs"] = deepcopy(self.paramsdialog.params)

    def params_test(self, params, **kwargs):
        H = self.parent.handler
        H.get_frame(H.frame_index, mode='test', params=params)

    def click_exit_track(self):
        """ """
        if self.paramsdialog:
            self.paramsdialog.destroy()
        if self.matcherdialog:
            self.matcherdialog.destroy()
        if self.tracks:
            self.tracks.destroy()

        self.destroy()

        if self.parent is None:
            sys.exit(0)

    def add_radio(self, name, label, defval):
        layout = QGridLayout()
        groupbox = QGroupBox('')
        groupbox.setAlignment(Qt.AlignCenter)

        label = QLabel(label)

        radiobutton = QRadioButton("On")

        if defval:
            radiobutton.setChecked(True)

        radiobutton.name = name
        radiobutton.value = True
        radiobutton.toggled.connect(self.radio_clicked)

        layout.addWidget(label, 0, 0)
        layout.addWidget(radiobutton, 0, 1)

        radiobutton = QRadioButton("Off")

        if not defval:
            radiobutton.setChecked(True)

        radiobutton.name = name
        radiobutton.value = False
        radiobutton.toggled.connect(self.radio_clicked)
        layout.addWidget(radiobutton, 0, 2)
        groupbox.setLayout(layout)

        return groupbox

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

        x = int(self.parent.dt_width*Xp)
        y = int(self.parent.dt_height*0.05)
        w = int(self.parent.dt_width*0.145)
        h = int(self.parent.dt_height*0.75)
        self.setGeometry(x, y, w, h)
        self.show()

        self.lists = ['new', 'tracks', 'open', ]
        self.set_shortcuts()
        self.current_track = None
        self.current_new = None
        self.current_open = None

    def vis(self):
        self.show()

    def set_shortcuts(self):
        link = QShortcut(QKeySequence("l"), self)
        link.activated.connect(self.link_pair)
        newtrack = QShortcut(QKeySequence("a"), self)
        newtrack.activated.connect(self.transfer_new)
        predictone = QShortcut(QKeySequence("n"), self)
        predictone.activated.connect(self.parent.track_panel.click_next)

        self.shortcuts = {'link': link,
                          'newtrack': newtrack,
                          'predictone': predictone}

    def setup_lists(self):
        """ """
        top_layout_2 = QGridLayout()

        ctrl_groupbox = QGroupBox()

        self.tracks = QListWidget()
        self.open_objs = QListWidget()
        self.new_objs = QListWidget()

        self.new_objs.itemDoubleClicked.connect(self.transfer_new)
        self.new_objs.currentItemChanged.connect(self.outline_pair)
        self.open_objs.currentItemChanged.connect(self.outline_pair)
        self.tracks.currentItemChanged.connect(self.outline_track)

        top_layout_2.addWidget(QLabel('Track List'), 0, 0)
        LF = QLabel('Last frame')
        top_layout_2.addWidget(LF, 0, 1)
        top_layout_2.addWidget(QLabel('New objects'), 0, 2)

        top_layout_2.addWidget(self.tracks, 1, 0)
        top_layout_2.addWidget(self.open_objs, 1, 1)
        top_layout_2.addWidget(self.new_objs, 1, 2)

        hide_open = True
        if hide_open:
            self.open_objs.hide()
            LF.hide()

        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 1, 1)

    def handle(self, **kwargs):
        """ step to take after image is filtered and labelled """
        self.list_new()
        self.list_open()

        index = self.parent.handler.frame_index
        tracker = self.parent.handler.tracker
        N = self.parent.params['improcess']['n_frames']

        if self.parent.params['improcess']['mode'] == 'find-all':
            """ find best match for each object added to track list """
            if len(tracker.tracks['id']) > 0:
                # check if n_frames method
                if N > 1:
                    # disable the GUI and keyboard shortcuts
                    self.parent.params['improcess']['running'] = False
                    self.parent.track_panel.setEnabled(False)
                    for key in self.shortcuts:
                        self.shortcuts[key].setEnabled(False)

                    # +1 to index to avoid adding same object twice
                    self.Ni = index + 1
                    self.Nf = N + index

                    # list is watched in wait_queue_finished
                    self.all_inds = list(range(self.Ni, self.Nf))

                    self.parent.handler.get_n_frames(indexi=self.Ni, indexf=self.Nf)

                if self.parent.params['improcess']['n_frames'] > 1:
                    tracker.predict_next_all(index=index)
                    self.status_update_signal.emit('finished matching')
            else:
                self.status_update_signal.emit('no objects to track')

    def wait_queue_finished(self, frame, index, **kwargs):
        """ process queue and wait for index of last frame to arrive
                before updating viewer and releasing GUI """
        if index == (self.Nf-1):
            self.last_frame = frame
            self.last_index = index

        self.all_inds.remove(index)

        if len(self.all_inds) == 0:
            for i in range(self.Ni, self.Nf):
                self.parent.handler.tracker.predict_next_all(i)

            self.parent.handler.frame_index = self.Nf-1
            self.parent.handler.contour_img = self.last_frame

            for key in self.shortcuts:
                self.shortcuts[key].setEnabled(True)
            self.parent.track_panel.setEnabled(True)

            self.parent.viewer.update_frame(self.last_frame, self.last_index)
            tracker = self.parent.handler.tracker
            tracks = list(tracker.tracks['id'])

            tracker.outline_track(self.last_frame.copy(),
                                  self.last_index,
                                  id_obj=tracks)

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
        val_track, val_open, val_new = self.get_obj_pair(src='open')

        if val_new is not None:
             self.tracks.clear()
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

    def outline_pair(self, val, update_vals=True, val_new=None, val_open=None, **kwargs):
        """ outline a single new and open object highlight to user for linking """
        if update_vals:
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
        """ highlight a single track when selected in tracks list box """
        frame = self.parent.handler.contour_img
        index = self.parent.handler.frame_index
        tracker = self.parent.handler.tracker
        val_track_out = list(tracker.tracks['id'])
        tracker.outline_track(frame.copy(), index, id_obj=val_track_out)

def main(params=None, params_file=None):
    global app
    app = QApplication([])
    window = TrackPanel(params=params, params_file=params_file)
    app.exec_()

if __name__ == '__main__':
    main()
