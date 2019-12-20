#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

gui.py

* the safas GUI

* load data and trac particles

* a parameters dictionary ('params') is used to exchange information
    between the GUI and module. it may be constructed and passed manually,
    or a YAML file may be read

* note that few error checks or tests exist in the module at this time

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
from safas.stream import Stream
from safas.trackpanel import TrackPanel

class MainPanel(QMainWindow):
    def __init__(self, config_file=None, *args, **kwargs):
        super(MainPanel, self).__init__(*args, **kwargs)

        self.layout = QGridLayout()

        # Stream class is setup. GUI only accesses parameters through Stream
        self.stream = Stream(parent=self,
                             params=None,
                             params_file=config_file)

        self.file_status = {}
        self.buttons = {}

        self.setup_window()
        self.setup_io_panel()
        self.setup_control_panel()

        self.stream_status = self.panel(height=100, pos=2, title='status')
        self.params_status = self.panel(height=0, pos=3, title='params')

        self.update_params_status()
        self.update_io_status()
        self.show()

    def setup_window(self):
        self.setWindowTitle('safas 0.0')
        self.layout = QGridLayout()
        w = QWidget()
        w.setLayout(self.layout)
        self.setCentralWidget(w)
        self.setGeometry(100, 100, 500, 800)

    def setup_io_panel(self):
        """ display file input, output, params, and script"""
        top_layout_2 = QGridLayout()
        status_box = QGroupBox('i/o')

        # file input
        self.file_status['input'] = QLineEdit('')
        top_layout_2.addWidget(self.file_status['input'], 3, 1)
        self.buttons['input'] = QPushButton('input')
        user_menu = QMenu()
        user_menu.triggered.connect(self.file_select_clicked)
        #dir_setting = user_menu.addAction('directory')
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
        self.buttons['output'].setEnabled(False)

        # params input
        self.file_status['params'] = QLineEdit('')
        top_layout_2.addWidget(self.file_status['params'], 5, 1)
        self.buttons['params'] = QPushButton('params', clicked=self.click_params)
        top_layout_2.addWidget(self.buttons['params'], 5, 2)

        # set the params as a config file, allow user to mod some params
        self.buttons['params'].setEnabled(False)

        status_box.setLayout(top_layout_2)
        self.layout.addWidget(status_box, 0, 0)

    def setup_control_panel(self):
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

        self.buttons = {'setup': setup,
                        'view': view,
                        'track': track,}

        self.buttons['track'].setEnabled(False)
        self.buttons['view'].setEnabled(False)

    def panel(self, height, pos, title):
        """ params and status boxes """
        top_layout_2 = QGridLayout()
        status_box = QGroupBox(title)

        textbox = QLabel('...')
        top_layout_2.addWidget(textbox, 0, 0)
        textbox.setMinimumHeight(height)
        textbox.setMinimumWidth(300)
        textbox.setStyleSheet('background-color: white')
        status_box.setLayout(top_layout_2)
        self.layout.addWidget(status_box, pos, 0)

        return textbox

    def update_io_status(self):
        """ update input, output, params, script displays """
        params = self.stream.params

        if params['input'] == 0:
            self.file_status['input'].setText(params['basein'])
        else:
            self.file_status['input'].setText(params['input'])

        if params['output'] == 0:
            self.file_status['output'].setText(params['baseout'])
        else:
            self.file_status['output'].setText(params['output'])

        if params['params_file'] != None:
            self.file_status['params'].setText(params['params_file'])
        else:
            self.file_status['output'].setText('no parameters file loaded')

    def update_params(self):
        """ """
        self.stream.update_params()

    @pyqtSlot(QAction)
    def file_select_clicked(self, action):

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
            self.buttons['view'].setEnabled(True)
            self.update_params_status()

    @pyqtSlot(QAction)
    def setup_output(self, action):
        val = action.text()

        if val == 'time_stamp':
            self.config.set_output(dir_name=dir_name)

        if val == 'named':
            text, okPressed = QInputDialog.getText(self, "Enter directory name","Directory name:", QLineEdit.Normal, "")

            if okPressed and text != '':
                text = str(text)
                text = text.replace(' ', '_')
                self.config.set_output(dir_name=text)
                

    def update_status(self, line):
        self.stream_status.setText(line)

    def click_params(self):
        """ params required to load and process the stream"""
        file = QFileDialog.getOpenFileName(self,
                                           "open file",
                                           self.params_path,
                                           "image Files (*.yml *.yaml)")
        self.params_file = file[0]

        if params['params_file']:
            self.stream.config_params()

    def update_params_status(self):
        """ if config file available, that will be loaded
                otherwise self.params will be passed through config_params
        """
        params = self.stream.params

        if params is not None:
            # cannot serialize '_io.TextIOWrapper' object
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
                # close the windows ...

                self.stream.close_windows()
                self.buttons['setup'].setText('load')
                self.buttons['view'].setEnabled(False)
                self.buttons['track'].setEnabled(False)
                self.stream_status.setText('video released.')

    def click_view(self):
        # connect the raw and processed images
        tx = self.buttons['view'].text()
        if tx == 'view':
            self.buttons['track'].setEnabled(True)
            # only option is to release and reload
            self.buttons['view'].setEnabled(False)
            self.stream.view()
            # *** add lines above to gui
            self.update_status('viewer opened')

    def click_track(self):
        line = 'process the stream'
        self.update_status(line)
        # *** add lines below to gui
        self.stream.track()
        self.buttons['track'].setEnabled(False)
        # *** add lines above to gui

    def closeEvent(self, event=None):
        self.update_status('close button pressed')
        self.stream.stop()
        self.destroy()

        #if self.parent is None:
        sys.exit(0)

def main(params=None, params_file=None):
    global app
    app = QApplication([])
    window = MainPanel(params=params, params_file=params_file)
    app.exec_()

if __name__ == '__main__':
    params_file = 'params.yml'
    main(params_file=params_file, params=None)
