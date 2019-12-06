# -*- coding: utf-8 -*-
"""
test getting and setting list items
"""
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np

class TrackLists(QMainWindow):
  

    def __init__(self, v1, v2, *args, **kwargs):
        super(TrackLists, self).__init__(*args, **kwargs)
       
        self.v1 = v1
        self.v2 = v2
        
        self.setWindowTitle('tracklists')

        self.layout = QGridLayout()
        self.setup_lists()
        
        w = QWidget()
        w.setLayout(self.layout)
        self.setCentralWidget(w)

        self.setGeometry(50, 50, 600, 1000)
        self.show()
        
        self.set_values()
        
    def setup_lists(self):
        """ """
        top_layout_2 = QGridLayout()

        ctrl_groupbox = QGroupBox('control')


        self.open_objs = QListWidget()
        self.new_objs = QListWidget()


        top_layout_2.addWidget(QLabel('open'), 0, 1)
        top_layout_2.addWidget(QLabel('new'), 0, 2)


        top_layout_2.addWidget(self.open_objs, 1, 1)
        top_layout_2.addWidget(self.new_objs, 1, 2)
        
        vals = np.arange(20,30,1)
        self.new_objs.addItems([str(v) for v in vals])
        vals = np.arange(0,10,1)
        self.open_objs.addItems([str(v) for v in vals])
        
        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 1, 1)
    
    def set_values(self):
        print('values v1, v2:', self.v1, self.v2)
        a = self.open_objs.findItems(str(self.v1), Qt.MatchExactly)
        b = self.new_objs.findItems(str(self.v2), Qt.MatchExactly)
        print('items are:', a, b)
        print(dir(a))
        self.open_objs.setCurrentItem(a[0])
        self.new_objs.setCurrentItem(b[0])
        
        print('found:', a, b)
def main(v1, v2):
    global app
    app = QApplication([])
    T = TrackLists(v1,v2)
    app.exec_()
    
if __name__ == '__main__': 
    main(v1=5, v2=25)
    