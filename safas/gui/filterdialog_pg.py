"""
paramsdialog_pg.py

pyqtgraph version of image filter parameters dialog to  generate small
    gui for setting filter parameters

* requires global PARAMS in imfilter.py 

"""
import sys
import os
from copy import deepcopy
import json

import numpy as np

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree
import pyqtgraph as pg

class FilterDialog(QDialog): 
    """Load ui file and connect application logic"""
    params_test_signal = pyqtSignal(object, name="params_test_signal")

    def __init__(self, 
                 parent=None, 
                 imfilter=None, 
                 params=None,
                 **kwargs):
        super(FilterDialog, self).__init__() # must init otherwise bare class Signal's do not work
        self.parent = parent
        self.params = params

        PARAMS = imfilter.__globals__['PARAMS']
        self.p = Parameter.create(name='params', type='group', children=PARAMS) ## Create tree of Parameter objects
        
        if self.params is not None: 
            for key in self.params: 
                try: 
                    self.p.param(key).setValue(self.params[key])
                except Exception as e: 
                    print(f"Error: {e}")
        
        self.state = self.p.saveState() # save the default state

        self.tree = ParameterTree(parent=self, showHeader=False)
        self.tree.setParameters(self.p, showTop=False)
        self.p.sigTreeStateChanged.connect(self.sync_params) # start syncing after the manual changes

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.tree)
            
        self.setWindowTitle("Image Filter Parameters")
        self.setGeometry(450, 100, 300, 300)

        self.okButton = QPushButton("Ok")
        self.cancelButton = QPushButton("Cancel")
        self.testButton = QPushButton("Test")

        layout.addWidget(self.okButton) 
        layout.addWidget(self.cancelButton) 
        layout.addWidget(self.testButton) 
        
        self.okButton.clicked.connect(self.click_close)
        self.cancelButton.clicked.connect(self.click_close)
        self.testButton.clicked.connect(self.click_test)

    def click_test(self):
        self.params_test_signal.emit(self.params)

    def sync_params(self): 
        for child in self.p.children(): 
            self.params[child.name()] = child.value()
       
    def default_params(self): 
        self.p.restoreState(self.state)

    def click_close(self, **kwargs): 
        """ """
        if self.sender().text() == "Cancel": # only emit if changes accepted
            self.p.restoreState(self.state)
            self.done(0)
        else: 
            self.done(1)