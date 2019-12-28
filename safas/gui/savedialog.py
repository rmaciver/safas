# -*- coding: utf-8 -*-
"""

savedialog.py

some options are presented to the user when the tracklist is saved

"""
import sys
import os
import numpy as np

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class SaveDialog(QMainWindow):

    params_update_signal = pyqtSignal(object, name="params_update_signal")
    close_signal = pyqtSignal(object, name="close_signal")
    
    def __init__(self, parent=None, params=None, imfilter=None):

        super(SaveDialog, self).__init__(parent)
        self.parent = parent
        if parent != None:
            self.parent = parent
            self.params = parent.parent.params
        if params != None:
            self.params = params
        self.y = 0
        if parent == None: 
            self.setup()
        
    def setup(self):
        self.setup_window()
        self.pop_gui()
        self.control_buttons()
        self.show()

    def setup_window(self):
        self.setWindowTitle('save dialog')
        self.layout = QGridLayout()
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

        saveButton = QPushButton('Ok', clicked=self.return_params)
        cancelButton = QPushButton('Cancel', clicked=self.exit_dialog)

        top_layout_2.addWidget(saveButton)
        top_layout_2.addWidget(cancelButton)
        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, self.y, 0)

    def pop_gui(self):
        """ add widgets for parameters in __globals__ of the filter script """
        self.layout.addWidget(QLabel('Confirm properties each save?'), self.y, 0)
        groupbox = self.add_radio(name='confirm', defval=True)        
        self.layout.addWidget(groupbox, self.y, 1)
        self.y += 1
        
        self.layout.addWidget(QLabel('Save frames?'), self.y, 0)
        groupbox = self.add_radio(name='save_frames', defval=self.params['save']['save_frames'])        
        self.layout.addWidget(groupbox, self.y, 1)
        self.y += 1
        
        self.layout.addWidget(QLabel('Clear data after save?'), self.y, 0)
        groupbox = self.add_radio(name='clear', defval=self.params['save']['clear'])        
        self.layout.addWidget(groupbox, self.y, 1)
        self.y += 1
        
        self.layout.addWidget(QLabel('filename?'), self.y, 0)
        textedit = QLineEdit('')
        if 'filename' in self.params['save']: 
            defval = self.params['save']['filename']
            textedit.setText(str(defval))
        textedit.name = 'filename'
        textedit.textChanged.connect(self.text_clicked)
        self.layout.addWidget(textedit, self.y, 1)
        self.y += 1
        
        self.layout.addWidget(QLabel('Confirm frames rate [fps]?'), self.y, 0)
        textedit = QLineEdit('')
        if 'fps' in self.params['improcess']: 
            defval = self.params['improcess']['fps']
            textedit.setText(str(defval))
        textedit.name = 'fps'
        textedit.textChanged.connect(self.text_clicked)
        self.layout.addWidget(textedit, self.y, 1)
        self.y += 1
        
        self.layout.addWidget(QLabel('Confirm pixel size [microns]?'), self.y, 0)
        textedit = QLineEdit('')
        if 'pixel_size' in self.params['improcess']: 
            defval = self.params['improcess']['pixel_size']
        if defval is not None: 
            textedit.setText(str(defval))
        textedit.name = 'pixel_size'
        textedit.textChanged.connect(self.text_clicked)
        self.layout.addWidget(textedit, self.y, 1)
        self.y += 1
        
    def add_radio(self, name, defval):
        layout = QGridLayout()
        groupbox = QGroupBox('')
        groupbox.setAlignment(Qt.AlignCenter)
        radiobutton = QRadioButton("On")

        if defval:
            radiobutton.setChecked(True)

        radiobutton.name = name
        radiobutton.value = True
        radiobutton.toggled.connect(self.radio_clicked)
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
        
    def text_clicked(self, value, key='improcess'):
         rb = self.sender()
         if rb.name in ['fps', 'pixel_size']:
             key='improcess'
             self.params[key][rb.name] = float(rb.text())
         if rb.name in ['filename']:
             key = 'save'
             self.params[key][rb.name] = rb.text()
         
            
    def radio_clicked(self, value, key='save', **kwargs):
        rb = self.sender()
        if rb.isChecked():
            self.params[key][rb.name] = rb.value

    def return_params(self,):
        self.params_update_signal.emit(self.params)
        self.close_signal.emit(self.params)
        self.destroy()
        if self.parent == None:
            sys.exit(0)
                
    def exit_dialog(self, event=None):
        buttonReply = QMessageBox.question(self, 'PyQt5 message', "Close filter parameters dialog?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if buttonReply == QMessageBox.Yes:
            self.destroy()
            if self.parent == None:
                sys.exit(0)

def main(params=None, imfilter=None):
   """ run stand-alone for testing """
   app = QApplication([])
   w = SaveDialog(parent=None, params=params, imfilter=imfilter)
   w.show()
   sys.exit(app.exec_())


if __name__ == '__main__':
    print('setup a small gui for user')
  
  
    params = {'save': {'confirm': True,
                       'filename': 'props_frame_%05d.xlsx',
                       'pixel_size': True,
                       'save_frames': False,
                       'fps': True,
                       'clear': True,
                       },

               'improcess': {'pixel_size': 8.6,
                             'fps': 23.2,
                             },
              }
    
    main(params=params)
