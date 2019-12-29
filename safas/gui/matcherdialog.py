# -*- coding: utf-8 -*-
"""

Match Control

"""

import sys
import os
import numpy as np

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class MatcherDialog(QMainWindow):

    params_update_signal = pyqtSignal(object, name="params_update_signal")
    
    def __init__(self, parent=None, params=None, imfilter=None):

        super(MatcherDialog, self).__init__(parent)

        self.parent = parent

        if params != None:
            self.params = params
        
        self.init_params()        
        self.y = 0
        
        if parent is None: 
            self.setup()
            
    def setup(self):
        self.setup_window()
        
        self.dist_group()
        self.area_group()
        self.error_buttons()
        self.control_buttons()
        self.layout.setRowStretch(1, 2)
        self.layout.setRowStretch(2, 2)
        self.show()
    
    def init_params(self):
        """ later, get from main params """
        self.params_temp = self.params
 
    def setup_window(self):
        self.setWindowTitle('object matching criteria')
        self.layout = QGridLayout()

        # add the update and save buttons
        w = QWidget()
        w.setLayout(self.layout)
        self.setCentralWidget(w)

        self.height = 200
        self.width = 300
        self.setGeometry(450, 100, self.width, self.height)
    
    def dist_group(self):
        """ """
        top_layout_2 = QGridLayout()
        ctrl_groupbox = QGroupBox('object distance')
        
        groupbox = self.add_radio(dispname='', name='distance', defval=True)
        top_layout_2.addWidget(groupbox, self.y, 0)
        self.y += 1
        groupbox = self.add_slider(dispname='weighting',
                                   name='distance', 
                                   vmin=0,
                                   vmax=100,
                                   defval=100, 
                                   step=1)
        
        top_layout_2.addWidget(groupbox, self.y, 0)
        self.y += 1
        
        self.y += 1
        
        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 0, 0)
        
    def area_group(self):
        """ """
        top_layout_2 = QGridLayout()
        ctrl_groupbox = QGroupBox('object area')
        

        groupbox = self.add_radio(dispname='', name='area', defval=True)
        top_layout_2.addWidget(groupbox, self.y, 0)
        self.y += 1
        groupbox = self.add_slider(dispname='weighting',
                                   name='area', 
                                   vmin=0,
                                   vmax=100,
                                   defval=100, 
                                   step=1,)
        
        top_layout_2.addWidget(groupbox, self.y, 0)
        self.y += 1
        
        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 0, 1)
        
    def error_buttons(self):
        
        top_layout_2 = QGridLayout()
        ctrl_groupbox = QGroupBox('')
        
        groupbox = self.add_slider(dispname='max error',
                                   name='error_threshold', 
                                   vmin=0,
                                   vmax=10000,
                                   defval=1, 
                                   step=100)
        top_layout_2.addWidget(groupbox, self.y, 0)
        self.y += 1
        
        groupbox = self.add_radio(dispname='squared error',
                                  name='square_error', 
                                  defval=True)
        top_layout_2.addWidget(groupbox, self.y, 0)
        self.y += 1
        
        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 1, 0, 1, 2)
    
    def control_buttons(self):
        top_layout_2 = QHBoxLayout()
        ctrl_groupbox = QGroupBox('')
        ctrl_groupbox.setAlignment(Qt.AlignCenter)

        defaultButton = QPushButton('default', clicked=self.default_params)
        updateButton = QPushButton('update', clicked=self.update_params)
        exitButton = QPushButton('exit', clicked=self.exit_dialog)

        top_layout_2.addWidget(defaultButton)
        top_layout_2.addWidget(updateButton)
        top_layout_2.addWidget(exitButton)
        ctrl_groupbox.setLayout(top_layout_2)
        top_layout_2.addWidget(ctrl_groupbox)
        self.y += 1
        self.buttons = {}
        self.buttons['control'] = {'defaultButton': defaultButton,
                                   'updateButton': updateButton,
                                   'exitButton': exitButton,
                                   }
        self.layout.addWidget(ctrl_groupbox, 2, 0, 1, 2)
         
    def default_params(self):
        self.init_params()
        
    def update_params(self):
        buttonReply = QMessageBox.question(self, 
                                           'PyQt5 message', 
                                           "Update the object matching criteria?", 
                                           QMessageBox.Yes | QMessageBox.No, 
                                           QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            self.params_update_signal.emit(self.params_temp)
    
    def add_slider(self, dispname='', name='', 
                   vmin=0, vmax=1, defval=1, step=0.1):
        layout = QGridLayout()
        groupbox = QGroupBox('')
        groupbox.setAlignment(Qt.AlignCenter)

        label = QLabel(dispname)
        value = QLabel()
        
        slider = QSlider(Qt.Horizontal)

        slider.setFocusPolicy(Qt.StrongFocus)
        slider.setTickPosition(QSlider.TicksBothSides)
        slider.setTickInterval(0.1)
        slider.setSingleStep(step)
        slider.label = value
        slider.setMinimum(vmin)
        slider.setMaximum(vmax)
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
        if self.sender().name in ['distance', 'area']:
            val = val/100 # scale result
            
        self.params_temp[self.sender().name] = val
        self.sender().label.setText(str(val))
        
    def add_radio(self, dispname, name, defval): 
        layout = QGridLayout()
        groupbox = QGroupBox('')
        groupbox.setAlignment(Qt.AlignCenter)

        label = QLabel(dispname)

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
        print('rb sender:', rb.name)
        if rb.isChecked():
            print('set to:', rb.value)
            self.params_temp[rb.name] = rb.value
            
    def exit_dialog(self, event=None):
        buttonReply = QMessageBox.question(self, 
                                           'PyQt5 message', 
                                           "Close matcher parameters dialog?", 
                                           QMessageBox.Yes | QMessageBox.No, 
                                           QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            self.destroy()
            if self.parent == None:
                sys.exit(0)


def main(params=None, imfilter=None):
   """ run stand-alone for testing """
   app = QApplication([])
   w = MatcherDialog(parent=None, params=params)
   w.show()
   sys.exit(app.exec_())


if __name__ == '__main__':
    print('setup a small gui for parameter control')
    params = {'err_threshold': 5000,
              'distance': 1,
              'area': 1,
              'squared': True,
             }
    
    main(params=params)
