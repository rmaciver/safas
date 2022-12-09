"""

pyqtgraph version of matcherdialog

"""

import sys
import os
from copy import deepcopy

import numpy as np

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree
import pyqtgraph as pg

PARAMS = [{'name': 'matcher', 'type': 'group', 
                'children': [
                        {"name": "error_threshold",
                        "type": "int", 
                        "value": 500
                        },
                        {'name': 'distance', 
                        "type": "int",
                        "value": 1
                        },
                        {'name': 'area', 
                        "type": "int",
                        "value": 1
                        },
                        {'name': 'squared', 
                        "type": "bool",
                        "value": False
                        },
                        ]
          }
        ]

class MatcherDialog(QDialog): 
    """Load ui file and connect application logic"""
    params_update_signal = pyqtSignal(object, name="params_update_signal")
    
    def __init__(self, 
                 parent=None, 
                 params=None, 
                 **kwargs):
        super(MatcherDialog, self).__init__() # must init otherwise bare class Signal's do not work
        self.parent = parent
        self.p = Parameter.create(name='params', type='group', children=PARAMS) ## Create tree of Parameter objects
        self.p.sigTreeStateChanged.connect(self.sync_params) # sync external copies on UI update
        
        self.params = params
        for key in ["error_threshold", "distance", "area", "squared"]:   # update from params input
            self.p.param('matcher', key).setValue(params[key])
        
        self.state = self.p.saveState() # save the input parameters

        self.tree = ParameterTree(parent=self, showHeader=False)
        self.tree.setParameters(self.p, showTop=False)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.tree)
            
        self.setWindowTitle("Object Matching Criteria")
        self.setGeometry(450, 100, 300, 300)

        self.okButton = QPushButton("Ok")
        self.cancelButton = QPushButton("Cancel")
        layout.addWidget(self.okButton) 
        layout.addWidget(self.cancelButton) 
        self.okButton.clicked.connect(self.click_close)
        self.cancelButton.clicked.connect(self.click_close)

    def sync_params(self): 
        """  """
        for key in ["error_threshold", "distance", "area", "squared"]:   # update from params input
            self.params[key] = self.p.param('matcher', key).value()
        
    def click_close(self, **kwargs): 
        """ """
        if self.sender().text() == "Cancel": # only emit if changes accepted
            self.p.restoreState(self.state)
            self.done(0)
        else: 
            self.done(1)