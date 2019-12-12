# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 05:18:31 2019

@author: Ryan
"""

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from safas.paramsdialog import ParamsDialog
from safas.matcherdialog import MatcherDialog
from safas.makeplot import MakePlot

class TrackPanel(QMainWindow):

    status_update_signal = pyqtSignal(str, name="status_update_signal")

    def __init__(self, parent=None, params=None, params_file=None, *args, **kwargs):
        super(TrackPanel, self).__init__(*args, **kwargs)
        # parent is the Stream object
        self.parent = parent
        self.setWindowTitle('tracking')
        self.buttons = {}
        
        self.layout = QGridLayout()
        self.setup_control_panel()
        self.setup_track_control()
        self.setup_mode_panel()
        self.filter_control_panel()
        
        w = QWidget()
        w.setLayout(self.layout)
        self.setCentralWidget(w)

        self.setGeometry(100, 1500, 50, 10)
        self.show()

        self.action = 'pause'
        self.params_to_gui()
        self.saved_data = False
        
    def setup(self,):
        self.tracks = TrackLists(parent=self.parent)
        self.click_start()

    def setup_mode_panel(self):
        """ enable/disable NEW, OPEN,TRACKS"""
        top_layout_2 = QGridLayout()
        ctrl_groupbox = QGroupBox('modes')

        cb1 = QRadioButton()  # new
        cb2 = QRadioButton()  # open
        cb3 = QRadioButton() # tracks

        top_layout_2.addWidget(cb3, 0, 0)
        top_layout_2.addWidget(QLabel('manual'), 0, 1)
        cb3.setChecked(False)
        cb3.mode = "manual"
        cb3.toggled.connect(self.mode_radio_clicked)
        
        top_layout_2.addWidget(cb2, 0, 4)
        top_layout_2.addWidget(QLabel('find-one'), 0, 5)
        cb2.setChecked(True)
        cb2.mode = "find-one"
        cb2.toggled.connect(self.mode_radio_clicked)

        top_layout_2.addWidget(cb1, 0, 2)
        top_layout_2.addWidget(QLabel('find-all'), 0, 3)
        cb1.setChecked(False)
        cb1.mode = "find-all"
        cb1.toggled.connect(self.mode_radio_clicked)
        
        self.mode_boxes = {'manual': cb3, 
                           'find-one': cb2,
                           'find-all': cb1,
                           }
        
        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 0, 3)

    def mode_radio_clicked(self, event=None, **kwargs):
        radioButton = self.sender()
        if radioButton.isChecked():
            self.parent.params['tracker_control']['mode'] = radioButton.mode

    def view_box_clicked(self, event):
         """ update params from box values """
         cbox= self.sender()
         views_hand = self.parent.params['tracker_control']['views']
         views_hand[cbox.view] = event
    
    def params_to_gui(self):
        """ """
        if 'mode' in self.parent.params['improcess']:
            mode = self.parent.params['improcess']['mode']
            if mode in self.mode_boxes: 
                for md in self.mode_boxes:
                    self.mode_boxes[md].setChecked(False)
                self.mode_boxes[mode].setChecked(True)
            
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
        self.parent.params['improcess']['filter'] = self.filter_combo.currentText()
    
    def setup_track_control(self):
        """ tracking related buttons"""
        top_layout_2 = QHBoxLayout()

        ctrl_groupbox = QGroupBox('track control')
        
        list_tracks = QPushButton('show lists', clicked=self.click_list_tracks)
        clear_tracks = QPushButton('clear lists', clicked=self.click_clear_tracks)
        match_dialog = QPushButton('match criteria', clicked=self.match_control_panel)
        
        save = QPushButton('save', clicked=self.click_save)
        plot = QPushButton('plot', clicked=self.make_plot)
        plot.setEnabled(False)
        
        self.buttons['save'] = save
        self.buttons['plot'] = plot
        
        top_layout_2.addWidget(match_dialog)
        top_layout_2.addWidget(list_tracks)
        top_layout_2.addWidget(clear_tracks)
        top_layout_2.addWidget(save)
        top_layout_2.addWidget(plot)
        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 0, 1)
        
    def setup_control_panel(self):
        top_layout_2 = QHBoxLayout()

        ctrl_groupbox = QGroupBox('video control')
        start = QPushButton('start', clicked=self.click_start)
        pause = QPushButton('pause', clicked=self.click_pause)
        next_frame = QPushButton('next frame >', clicked=self.click_next)
        exit_track = QPushButton('exit', clicked=self.click_exit_track)
      
        top_layout_2.addWidget(next_frame)
        top_layout_2.addWidget(start)
        top_layout_2.addWidget(pause)
       
        top_layout_2.addWidget(exit_track)
        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 0, 2)

        self.buttons['pause'] = pause
        self.buttons['start'] = start

    def match_control_panel(self):
        self.matcherdialog = MatcherDialog(parent=self, params=self.parent.params['matcher'])
        self.matcherdialog.params_update_signal.connect(self.matcher_params_update)
        self.matcherdialog.setup()
        
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
        self.buttons['plot'].setEnabled(True)
        
    def click_next(self):
        """ """
        self.parent.viewer.next_frame()

    def click_prev(self):
        """ """

    def click_list_tracks(self):
        """ reopens the list if closed"""
        self.tracks.vis()
    
    def click_clear_tracks(self):
        msg = 'Clear the tracks? Consider to save the data before deleting.'
        buttonReply = QMessageBox.question(self, 'clear objects message', msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            self.parent.handler.reset_tracker()
            
    def make_plot(self):
        """ read the output and plot results in saved dataframe
        * must be at least one dataframe saved
        """
        self.plotwin = MakePlot(parent=self, dirout=self.parent.params['dirout'])

    def click_params_dialog(self):
        """ """
        imfilter = self.parent.handler.imfilter
        self.paramsdialog = ParamsDialog(parent=self, imfilter=imfilter)
        self.paramsdialog.params_test_signal.connect(self.params_test)
        self.paramsdialog.params_update_signal.connect(self.filter_params_update)
        self.paramsdialog.setup()

    def params_test(self, params, **kwargs):
        H = self.parent.handler
        H.get_frame(H.frame_index, mode='test', params=params)

    def filter_params_update(self, params, **kwargs):
        """ update params from user input """
        self.parent.params['improcess']['kwargs'] = params
    
    def matcher_params_update(self, params, **kwargs):
        """ update params from user input """
        self.parent.params['matcher'] = params
        
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
        self.current_track = None
        self.current_new = None
        self.current_open = None

    def vis(self):
        self.show()

    def set_shortcuts(self):
        # link open end of track to the new object
        self.link_shortcut = QShortcut(QKeySequence("l"), self)
        self.link_shortcut.activated.connect(self.link_pair)
        # add the new object as a new track
        self.newtrack_shortcut = QShortcut(QKeySequence("a"), self)
        self.newtrack_shortcut.activated.connect(self.transfer_new)

        # add then predict next for selected track
        self.predictone_shortcut = QShortcut(QKeySequence("n"), self)
        self.predictone_shortcut.activated.connect(self.parent.track_panel.click_next)
#
#        lines = 'keyboard shortcuts:'
#        lines += '\n"a" to add object from "new" list'
#        lines += '\n"l" to link selected new and open objects'
#        lines += '\n"n" next frame'
#
#        self.control_message = lines
#        self.status_update_signal.emit(self.control_message)

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
        self.list_new()
        self.list_open()

        frame = self.parent.handler.contour_img
        index = self.parent.handler.frame_index
        tracker = self.parent.handler.tracker

        if self.parent.params['tracker_control']['mode'] == 'manual':
            self.status_update_signal.emit(self.control_message)

        if self.parent.params['tracker_control']['mode'] == 'find-one':

            if self.current_track is not None:
                val_new, val_open = self.parent.handler.tracker.predict_next(frame=frame,
                                                                   index=index,
                                                                   id_obj=self.current_track)

                if val_new is not None:
                    a = self.open_objs.findItems(str(val_open), Qt.MatchExactly)
                    b = self.new_objs.findItems(str(val_new), Qt.MatchExactly)
                    c = self.tracks.findItems(str(self.current_track), Qt.MatchExactly)

                    if len(a) > 0:
                        self.open_objs.setCurrentItem(a[0])
                    if len(b) > 0:
                        self.new_objs.setCurrentItem(b[0])

                    self.tracks.setCurrentItem(c[0])
                    self.outline_pair(val=None,
                                      update_vals=False,
                                      val_new=val_new,
                                      val_open=val_open)
                    self.new_objs.setFocus()
                    self.status_update_signal.emit('finished matching')

        if self.parent.params['tracker_control']['mode'] == 'find-all':
            """ find best match for each object added to track list """
            # try to match open with new, link automatically
            if len(tracker.tracks['id']) > 0:
                for val_track in tracker.tracks['id']:
                    val_new, val_open = self.parent.handler.tracker.predict_next(frame=frame,
                                                                           index=index,
                                                                           id_obj=val_track)
                    #if val_new is not None:
                    # will skip the obj if not found or beyond max length
                    # adding val_new as None will effectively terminate the track
                    print('new obj is:', val_new)
                    tracker.update_object_track(index, id_obj=val_track, id_curr=val_new)
                    print('updated:', val_track)

                self.status_update_signal.emit('finished matching')
            else:
                self.status_update_signal.emit('no objects to track')

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

        if self.parent.params['tracker_control']['mode'] == 'find-one':
            val_track, val_open, val_new = self.get_obj_pair(src='open')
            self.current_track = val_track
            self.current_open = val_open
            self.current_new = val_new
            self.parent.track_panel.click_next()

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
        val_track, val_open, val_new = self.get_obj_pair(src='tracks')

        frame = self.parent.handler.contour_img
        index = self.parent.handler.frame_index
        tracker = self.parent.handler.tracker

        if self.parent.params['tracker_control']['views']:
            val_track_out = list(tracker.tracks['id'])
        else:
            val_track_out = val_track

        tracker.outline_track(frame.copy(), index, id_obj=val_track_out)

        self.current_track = val_track
        self.current_open = val_open
        self.current_new = val_new
        print('in outline track:', self.current_track, 'open:', self.current_open, 'new:', self.current_new)


def main(params=None, params_file=None):
    global app
    app = QApplication([])
    window = TrackPanel(params=params, params_file=params_file)
    app.exec_()

if __name__ == '__main__':
    main()
