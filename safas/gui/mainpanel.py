#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mainpanel.py

* the main panel of the Safas GUI
* a parameters dictionary ('params') is used to exchange information
    between the GUI and the Stream, Handler, and Tracker modules.
"""
import os
import sys

import time
import cv2
import yaml

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import safas
from safas.comp.stream import Stream
from safas.gui.trackpanel import TrackPanel
from safas.comp.setconfig import set_dirout


class MainPanel(QMainWindow):
    def __init__(self, config_file=None, *args, **kwargs):
        super(MainPanel, self).__init__(*args, **kwargs)

        desktopsize = QDesktopWidget().screenGeometry()
        self.dt_height = desktopsize.height()
        self.dt_width = desktopsize.width()

        self.layout = QGridLayout()

        # Stream class is setup. GUI only accesses parameters through Stream
        self.stream = Stream(parent=self,
                             params=None,
                             params_file=config_file)
        self.file_status = {}
        self.buttons = {}
        # setup sections of the main panel
        self.setup_window()
        self.setup_io_panel()
        self.setup_control_panel()

        dims = [int(self.dt_height*0.04), int(self.dt_height*0.1)]
        widget = QLabel('...')
        self.stream_status = self.panel(dims,
                                        pos=2,
                                        title='status',
                                        widget=widget)

        dims = [int(self.dt_height*0.3), int(self.dt_height*0.5)]
        widget = QTextEdit()
        self.params_status = self.panel(dims,
                                        pos=3,
                                        title='params',
                                        widget=widget)

        self.update_params_status()
        self.update_io_status()
        self.setup_video_analysis_mode()
        self.show()

    def setup_window(self):
        """ setup the main window """
        self.setWindowTitle('safas 0.1.0')
        self.layout = QGridLayout()
        w = QWidget()
        w.setLayout(self.layout)
        self.setCentralWidget(w)
        x=int(self.dt_width*0.02)
        y=int(self.dt_height*0.05)

        w=int(self.dt_width*0.25)
        h=int(self.dt_height*0.75)

        self.setGeometry(x, y, w, h)

    def setup_io_panel(self):
        """ add panel to display file input, output, and params """
        top_layout_2 = QGridLayout()
        status_box = QGroupBox('i/o')

        # file input
        self.file_status['input'] = QLineEdit('')
        top_layout_2.addWidget(self.file_status['input'], 3, 1)
        self.buttons['input'] = QPushButton('input')
        user_menu = QMenu()
        user_menu.triggered.connect(self.file_select_clicked)
        file_setting = user_menu.addAction('file')

        self.buttons['input'].setMenu(user_menu)
        top_layout_2.addWidget(self.buttons['input'], 3, 2)

        # file output
        self.file_status['output'] = QLineEdit('')
        top_layout_2.addWidget(self.file_status['output'], 4, 1)
        self.buttons['output'] = QPushButton('output')
        user_menu = QMenu()
        user_menu.triggered.connect(self.setup_output)
        dir_setting = user_menu.addAction('time_stamp')
        file_setting = user_menu.addAction('named')
        self.buttons['output'].setMenu(user_menu)
        top_layout_2.addWidget(self.buttons['output'], 4, 2)

        # params input
        self.file_status['params'] = QLineEdit('')
        top_layout_2.addWidget(self.file_status['params'], 5, 1)
        self.buttons['params'] = QPushButton('params', clicked=self.click_params)
        top_layout_2.addWidget(self.buttons['params'], 5, 2)
        self.buttons['params'].setEnabled(True)

        status_box.setLayout(top_layout_2)
        self.layout.addWidget(status_box, 0, 0)

    def setup_video_analysis_mode(self): 
        """"""
        top_layout_2 = QHBoxLayout()

        ctrl_groupbox = QGroupBox('Analysis mode')  
        layout = QGridLayout()

        self.radio_analysis_mode = QRadioButton("Link-Manually")
        self.radio_analysis_mode.setChecked(False)
        top_layout_2.addWidget(self.radio_analysis_mode )
        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 7, 0)
        
    def setup_control_panel(self):
        """ buttons to load view analyze """
        top_layout_2 = QHBoxLayout()

        ctrl_groupbox = QGroupBox('video control')

        setup = QPushButton('load', clicked=self.click_setup)
        view = QPushButton('view', clicked=self.click_view)
        track = QPushButton('analyze', clicked=self.click_track)

        top_layout_2.addWidget(setup)
        top_layout_2.addWidget(view)
        top_layout_2.addWidget(track)

        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 1, 0)

        self.buttons['setup'] = setup
        self.buttons['view'] = view
        self.buttons['track'] = track

        self.buttons['track'].setEnabled(False)
        self.buttons['view'].setEnabled(False)

    def panel(self, dims, pos, title, widget):
        """ params and status boxes """
        top_layout_2 = QGridLayout()
        status_box = QGroupBox(title)
        textbox = widget
        top_layout_2.addWidget(textbox, 0, 0)

        textbox.setMaximumHeight(dims[1])
        textbox.setMinimumHeight(dims[0])

        textbox.setStyleSheet('background-color: white')
        status_box.setLayout(top_layout_2)
        self.layout.addWidget(status_box, pos, 0)
        return textbox

    def update_io_status(self):
        """ update input, output, params, script displays """
        params = self.stream.params
        if params['input'] ==0:
            self.file_status['input'].setText(str(params['basein']))
        else:
            self.file_status['input'].setText(str(params['input']))

        if params['output'] == 0:
            self.file_status['output'].setText(str(params['baseout']))
        else:
            self.file_status['output'].setText(str(params['output']))

        if params['params_file'] != 0:
            self.file_status['params'].setText(str(params['params_file']))
        else:
            self.file_status['output'].setText('no parameters file loaded')

    def update_params(self):
        self.stream.update_params()

    @pyqtSlot(QAction)
    def file_select_clicked(self, action):
        """ determine file type and open dialog for user to select a file """
        val = action.text()
        tx = self.file_status['input'].text()

        if val == 'directory':
            file = str(QFileDialog.getExistingDirectory(self, "select Directory", tx))
            self.stream.params['input'] = file

        if val == 'file':
            file = QFileDialog.getOpenFileName(self, "open file", tx, "image Files (*.avi *.mp4 *.png *.jpg *.tif *.bmp)")
            self.stream.params['input'] = file[0]

        if self.stream.params['input'] != 0:
            self.file_status['input'].setText(self.stream.params['input'])
            #self.buttons['view'].setEnabled(True)
            self.update_params_status()

    @pyqtSlot(QAction)
    def setup_output(self, action=None):
        """ A directory in the default/ base output path is created
            note: if not made explicitly by user, a time stamped folder
                is made when the data is saved
        """
        if self.stream.params['baseout'] == 0:
            msg = 'Base output directory not set. Please select a directory.'
            buttonReply = QMessageBox.question(self,
                                           'message',
                                           msg,
                                           QMessageBox.Ok | QMessageBox.Cancel,
                                           QMessageBox.Ok)
            
            if buttonReply == QMessageBox.Ok:
                # set a basein directory for saving files
                baseout = str(QFileDialog.getExistingDirectory(self, "select Directory",))
            
                print('directory selected:', baseout)
                
                self.stream.params['baseout'] = baseout
            
            msg = 'Consider setting baseout in safas/config.yaml'
            buttonReply = QMessageBox.question(self,
                                           'message',
                                           msg,
                                           QMessageBox.Ok,
                                           QMessageBox.Ok)
            
        if action is not None:
            val = action.text()
            dir_name = None
            
            if val == 'named':
                # get name extension for the output directory, otherwise a timestamp is used
                text, okPressed = QInputDialog.getText(self, "Enter directory name","Directory name:", QLineEdit.Normal, "")
    
                if okPressed and text != '':
                    text = str(text)
                    dir_name = text.replace(' ', '_')
        
            # create output directory if 'output' button was clicked
            self.stream.set_output(dir_name=dir_name)
            
        self.update_io_status()
        self.update_params_status()

    def update_status(self, line):
        self.stream_status.setText(line)

    def click_params(self):
        """ load a different params file """
        tx = None
        if self.stream.params['basein'] != 0:
            tx = self.stream.params['basein']
        file = QFileDialog.getOpenFileName(self,
                                           "Select config file",
                                           tx,
                                           "YAML files (*.yml *.yaml)")
        self.stream.config(params_file=file[0])
        self.update_io_status()
        self.update_params_status()

    def update_params_status(self):
        """ if config file available, that will be loaded
                otherwise self.params will be passed through config_params
        """
        params = self.stream.params

        if params is not None:
            # cremove bec. annot serialize '_io.TextIOWrapper' object
            if 'readme' in params:
                params.pop('readme')

            line = yaml.dump(params, default_flow_style=False)
            self.params_status.setText(line)

        if params is None:
            self.params_status.setText('no parameters loaded')

        if hasattr(self, 'params_file'):
            self.file_status['params'].setText(params['params_file'])

    def click_setup(self) :
        """ setup the stream and handler components """
        tx = self.buttons['setup'].text()

        if tx == 'load':
            ret = self.stream.setup()
            if ret:
                self.buttons['setup'].setText('release')
                self.buttons['view'].setEnabled(True)
                for str in ['input', 'params', 'output','track']:
                    self.buttons[str].setEnabled(False)

        if tx == 'release':
            # prompt to stop...
            msg = 'Stop analysis and close windows? Unsaved data will be lost'
            buttonReply = QMessageBox.question(self,
                                           'message',
                                           msg,
                                           QMessageBox.Yes | QMessageBox.No,
                                           QMessageBox.No)

            if buttonReply == QMessageBox.Yes:
                self.stream.stop()
                self.stream.close_windows()
                self.buttons['setup'].setText('load')
                self.buttons['view'].setEnabled(False)
                self.buttons['track'].setEnabled(False)
                self.stream_status.setText('video released.')

                for str in ['input','output','params']:
                    self.buttons[str].setEnabled(True)

    def click_view(self):
        """ open viewer for image stream """
        tx = self.buttons['view'].text()
        if tx == 'view':
            self.buttons['track'].setEnabled(True)
            self.buttons['view'].setEnabled(False)
            self.stream.view()
            self.update_status('viewer opened')

    def click_track(self):
        """ load the track panel GUI for user control """
        # check if baseout has been set
        if self.stream.params['baseout'] == 0: 
            self.setup_output()
        else: 
            self.update_status('Process the video')
           # if not self.radio_analysis_mode.isChecked(): 
            self.stream.track()
            #else: 
            #    print(f"Something completely different!!!")
            self.buttons['track'].setEnabled(False)

    def closeEvent(self, event=None):
        """ close window and exit the app context"""
        self.update_status('close button pressed')
        self.stream.stop()
        self.destroy()
        sys.exit(0)

def main(config_file):
    """ for testing run stand-alone"""
    global app
    app = QApplication([])
    window = MainPanel(config_file=config_file)
    app.exec_()

if __name__ == '__main__':
    file = os.path.dirname(safas.__file__)
    fname = os.path.join(file, 'config.yml')
    print(fname)
    main(config_file=fname)
