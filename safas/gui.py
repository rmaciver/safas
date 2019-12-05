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

sys.path.append(r'C:\Users\Ryan\Desktop\src\safas-dev')
params_path = r'C:\Users\Ryan\Desktop\src\safas-dev\params'

import time
import cv2
import yaml

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from safas.stream import Stream
from safas.trackpanel import TrackPanel

__author__ = 'Ryan MacIver'
__copyright__ = 'Copyright 2019'
__credits__ = ['Ryan MacIver']
__license__ = 'MIT'
__version__ = '0.0.1'
__maintainer__ = 'Ryan MacIver'
__email__ = 'rmcmaciver@hotmail.com'
__status__ = 'Dev'

class Gui(QMainWindow):
    def __init__(self, params=None, params_file=None, parent=None, *args, **kwargs):
        super(Gui, self).__init__(*args, **kwargs)

        # Stream class is setup. GUI only accesses parameters through Stream
        self.stream = Stream(parent=self, params=params, params_file=params_file)

        self.setWindowTitle('floctrac gui')
        app.aboutToQuit.connect(self.closeEvent)

        self.layout = QGridLayout()

        self.file_status = {}
        self.buttons = {}

        self.setup_control_panel()
        self.setup_io_panel()
        self.stream_status = self.panel(height=100, pos=2, title='status')
        self.params_status = self.panel(height=0, pos=3, title='params')
#
        w = QWidget()
        w.setLayout(self.layout)
        self.setCentralWidget(w)

        self.setGeometry(100, 100, 50, 1000)
        self.show()

        self.update_params_status()
        self.update_io_status()

    def setup_control_panel(self):
        top_layout_2 = QHBoxLayout()

        ctrl_groupbox = QGroupBox('controls')

        setup = QPushButton('setup', clicked=self.click_setup)
        view = QPushButton('view', clicked=self.click_view)
        track = QPushButton('track', clicked=self.click_track)

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
        dir_setting = user_menu.addAction('directory')
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

        # script input
        self.filter_combo = QComboBox()
        self.list_filters()
        self.filter_combo.currentIndexChanged.connect(self.change_filter)
        top_layout_2.addWidget(self.filter_combo, 6, 1)
        top_layout_2.addWidget(QLabel('filter'), 6, 2)
        ####
        status_box.setLayout(top_layout_2)
        self.layout.addWidget(status_box, 0, 0)

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

    def list_filters(self):
        """ update the selected filter """
        self.filter_combo.addItems(self.stream.list_filters())

    def change_filter(self):
        """ select filter from list """
        self.stream.params['improcess']['filter'] = self.filter_combo.currentText()
        self.update_params_status()

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
        """ steup the stream and handler components """

        self.stream.setup()
        self.buttons['track'].setEnabled(True)
        self.buttons['view'].setEnabled(True)

    def click_view(self):
        # connect the raw and processed images
        self.buttons['track'].setEnabled(True)
        self.stream.view()
        # *** add lines above to gui

    def click_track(self):
        line = 'process the stream'
        self.update_status(line)
        # *** add lines below to gui
        self.stream.track()
        # *** add lines above to gui

    def closeEvent(self, event=None):
        self.update_status('close button pressed')
        cv2.destroyAllWindows()
        self.destroy()
        if self.parent is None:
            sys.exit(0)

def main(params=None, params_file=None):
    global app
    app = QApplication([])
    window = Gui(params=params, params_file=params_file)
    app.exec_()

if __name__ == '__main__':
    params_file = 'test_params.yml'
    main(params_file=params_file, params=None)
