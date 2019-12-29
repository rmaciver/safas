# -*- coding: utf-8 -*-
"""

ctrlparams.py

generate small gui for setting filter parameters

requires the file imfilter.py has a global 'define_args'

note:
    * the main gui will already have the script loaded
    * call the __globals__ on the
"""
import sys
import os
import numpy as np

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class ParamsDialog(QMainWindow):
    
    params_test_signal = pyqtSignal(object, name="params_test_signal")
    params_update_signal = pyqtSignal(object, name="params_update_signal")

    def __init__(self, parent=None, params=None, imfilter=None):

        super(ParamsDialog, self).__init__(parent)

        self.parent = parent
        self.imfilter = imfilter

        if parent != None:
            self.parent = parent
           # self.params = parent.params
        if params != None:
            self.params = params

        self.y = 0

    def setup(self):
        self.setup_window()
        self.pop_gui()
        self.control_buttons()
        self.show()

    def setup_window(self):
        self.setWindowTitle('filter parameters')
        self.layout = QGridLayout()

        # add the update and save buttons
        w = QWidget()
        w.setLayout(self.layout)
        self.setCentralWidget(w)

        self.height = 200
        self.width = 1000
        self.setGeometry(450, 100, self.width, self.height)

    def control_buttons(self):
        top_layout_2 = QHBoxLayout()
        ctrl_groupbox = QGroupBox('')
        ctrl_groupbox.setAlignment(Qt.AlignCenter)

        updateButton = QPushButton('Test', clicked=self.test_params)
        saveButton = QPushButton('Save', clicked=self.save_params)
        exitButton = QPushButton('Exit', clicked=self.exit_dialog)

        top_layout_2.addWidget(updateButton)
        top_layout_2.addWidget(saveButton)
        top_layout_2.addWidget(exitButton)
        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, self.y, 0)
        self.y += 1
        self.buttons = {}
        self.buttons['control'] = {'udpatetButton': updateButton,
                                   'saveButton': saveButton,
                                   'exitButton': exitButton,
                                   }

    def test_params(self, ):
        """ apply the params to the current image """
        self.params_test_signal.emit(self.params_temp)

    def save_params(self, ):
        """ pass the selected params back to the main configuration """
        self.params_update_signal.emit(self.params_temp)

    def pop_gui(self):
        """ add widgets for parameters in __globals__ of the filter script """
        # read the global variable define_args
        gvars = self.imfilter.__globals__['define_args']
        print('gvars:', gvars)
        self.params_temp = {}

        # only int and bool parameters are supported at this time
        for ky in gvars.keys():
            vtype = gvars[ky][0]

            if vtype == bool:
                defval = gvars[ky][1][2]
                groupbox = self.add_radio(name=ky, defval=defval)
                self.layout.addWidget(groupbox, self.y, 0)
                self.y += 1

                self.params_temp[ky] = defval

            if vtype == int:
                defval = gvars[ky][1][2]
                minval = gvars[ky][1][0]
                maxval = gvars[ky][1][1]

                groupbox = self.add_slider(name=ky, minval=minval, maxval=maxval, defval=defval)
                self.layout.addWidget(groupbox, self.y, 0)
                self.y += 1
                self.params_temp[ky] = defval
            
    def add_radio(self, name, defval):
        layout = QGridLayout()
        groupbox = QGroupBox('')
        groupbox.setAlignment(Qt.AlignCenter)

        label = QLabel(name)

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

    def radio_clicked(self):
        rb = self.sender()
        if rb.isChecked():
            self.params_temp[rb.name] = rb.value

    def add_slider(self, name, minval, maxval, defval):
        layout = QGridLayout()
        groupbox = QGroupBox('')
        groupbox.setAlignment(Qt.AlignCenter)

        label = QLabel(name)
        value = QLabel()
        slider = QSlider(Qt.Horizontal)
        slider.setFocusPolicy(Qt.StrongFocus)
        slider.setTickPosition(QSlider.TicksBothSides)
        slider.setTickInterval(10)
        slider.setSingleStep(1)
        slider.label = value
        slider.setMinimum(minval)
        slider.setMaximum(maxval)
        slider.setValue(defval)
        slider.name = name

        slider.valueChanged.connect(self.slider_update)
        layout.addWidget(label, 0,0)
        layout.addWidget(value, 0, 1)
        layout.addWidget(slider, 1, 0)
        groupbox.setLayout(layout)
        return groupbox

    def slider_update(self, val, **kwargs):
        """udpate gui and params from slider """
        self.params_temp[self.sender().name] = val
        self.sender().label.setText(str(val))

    def exit_dialog(self, event=None):
        buttonReply = QMessageBox.question(self, 'PyQt5 message', "Close filter parameters dialog?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            self.destroy()
            if self.parent == None:
                sys.exit(0)

def main(params=None, imfilter=None):
   """ run stand-alone for testing """
   app = QApplication([])
   w = CtrlParams(parent=None, params=params, imfilter=imfilter)
   w.show()
   sys.exit(app.exec_())


if __name__ == '__main__':
    print('setup a small gui for parameter control')

    from safas.filters.sobel_focus.imfilter import imfilter
    main(params=None, imfilter=imfilter)
