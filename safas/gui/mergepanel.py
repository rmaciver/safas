#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
move and combine files

- functions (150 lines in trackpanel)
"""
import sys
import os
import datetime
from glob import glob 
from shutil import copyfile

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import pandas as pd

class MergePanel(QMainWindow):

    #status_update_signal = pyqtSignal(str, name="status_update_signal")

    def __init__(self, parent=None, *args, **kwargs):
        super(MergePanel, self).__init__(*args, **kwargs)
        # parent is the Stream object
        self.parent = parent
        self.setWindowTitle('merge data')        
        self.layout = QGridLayout()
        # main params to setup the merge function
        self.mode = {'dataframes': {'setting': True, 'filespec': '*.xlsx', 'subdir': 'data'},
                     'images': {'setting': True, 'filespec': '*intensity.png', 'subdir': 'imgs'},
                     }
        self.output = None        
        self.control_panel()
        w = QWidget()
        w.setLayout(self.layout)
        self.setCentralWidget(w)
    
        self.show()
    
    def put_radio(self, pos, name): 
         # add as group box to make independent
        groupbox = QGroupBox()
        layout = QGridLayout()
        cb1 = QRadioButton()
        cb1.name = name
        cb1.toggled.connect(self.radio_clicked)
        # set default to initial value in self.mode 
        cb1.setChecked(self.mode[name]['setting'])
        layout.addWidget(cb1, 0,0)
        layout.addWidget(QLabel(name), 0,1)
        groupbox.setLayout(layout)
        self.layout.addWidget(groupbox, 0, pos)
                            
    def control_panel(self):
        """ setup radio and push buttons"""
        # radio buttons are linked to the self.mode dictionary"
        pos = 0
        for name in self.mode:
            self.put_radio(pos=pos, name=name)
            pos +=1
        
        # add merge and exit buttons
        ctrl_groupbox = QGroupBox()
        layout = QGridLayout()
        layout.addWidget(QPushButton('merge', clicked=self.click_merge), 0,0)
        layout.addWidget(QPushButton('exit', clicked=self.click_cancel), 0,1)
        ctrl_groupbox.setLayout(layout)
        
        self.layout.addWidget(ctrl_groupbox, 0, pos)
    
    def radio_clicked(self, value, **kwargs):
        rb = self.sender()
        if rb.isChecked():
            self.mode[rb.name]['setting'] = True
        else: 
            self.mode[rb.name]['setting'] = False
            
    def click_merge(self): 
        """ output written to baseout """
        
        # select the directories to merge
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.DirectoryOnly)
        tree_view = file_dialog.findChild(QTreeView)
        tree_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        list_view = file_dialog.findChild(QListView, "listView")
        list_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        if file_dialog.exec_() == QDialog.Accepted:
            directories =  file_dialog.selectedFiles()
        else:
            directories = file_dialog.getOpenFileNames(self, "", "/")
        
        # compare length of dataframe and images in each subdir
        LDFS = []
        LIMS = []
        
        # set the output:         
        if len(directories) > 0: 
            for mode in self.mode: 
                if self.mode[mode]['setting']: 
                    filespec = self.mode[mode]['filespec']
                    filelist = []
                    
                    for directory in directories: 
                        subdirs = sorted(os.listdir(os.path.join(directory, self.mode[mode]['subdir'])))
                        if len(subdirs) > 0: 
                            for subdir in subdirs: 
                                files = sorted(glob(os.path.join(directory,self.mode[mode]['subdir'], subdir,filespec)))
                                [filelist.append(file) for file in files]
                                if mode=='images': 
                                    LIMS.append(len(files))
                                if mode=='dataframes': 
                                    di = pd.read_excel(files[0])
                                    LDFS.append(len(di))
                    if len(filelist) > 0: 
                        print('found files to merge')
                        
                        if self.output is None: 
                            self.output = gen_dirout(directory, subdirs=['data','imgs'])
                            
                        if mode == 'dataframes': 
                            print('merge dataframes')
                            dfs = [pd.read_excel(file) for file in filelist]
                            for i, df in enumerate(dfs): 
                                df['set'] = i
                            result = pd.concat(dfs)
                            result.to_excel(os.path.join(self.output, 'data', 'merge.xlsx'))
                            print('total frames:', len(result))
                        if mode == 'images': 
                            print('copy images')
                            for i, file in enumerate(filelist):     
                                 pth, fname = os.path.split(file)
                                 pth_base = os.path.basename(pth)
                                 fname = '%03d_frame_' % i + pth_base + '_' + fname 
                                 newname = os.path.join(self.output, 'imgs', fname)
                                 copyfile(file, newname)
                            print('total images:', len(filelist))
        print('images in each subdir:', LIMS)
        print('objects in each frame:', LDFS)
    def click_cancel(self): 
        print('exit the panel')
        self.destroy()
        
        if self.parent is None:
            print('exit the program')
            sys.exit(0)

def gen_dirout(directory, subdirs=None): 
    """ """
    fname = 'merge_%s' % datetime.datetime.now().strftime('%Y-%m-%d_%H.%M.%S')
    outdir = os.path.join(os.path.dirname(directory),fname)
    [os.makedirs(os.path.join(outdir, pth)) for pth in subdirs] 
    return outdir
         
if __name__ == '__main__': 
    
    app = QApplication([])
    window = MergePanel()
    app.exec_()
    