# -*- coding: utf-8 -*-
"""
makeplot.py

make a figure from the data selected
"""
import sys
import os
from glob import glob

from matplotlib import pyplot as plt
import pandas as pd
import numpy as np

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class MakePlot(QMainWindow):
    def __init__(self, parent=None, dirout=None, *args, **kwargs):
        super(MakePlot, self).__init__(*args, **kwargs)

        print('dirout is:', dirout)
        self.parent = parent
        self.dirout = dirout
        self.read_file()
        print('read the files')
        self.setWindowTitle('plot gui')
        #app.aboutToQuit.connect(self.exit_dialog)
        self.layout = QGridLayout()
        w = QWidget()
        w.setLayout(self.layout)
        self.setCentralWidget(w)
        self.setup_window()
        print('window was setup')
        self.setGeometry(100, 100, 50, 100)
        self.show()

    def setup_window(self):
        top_layout_2 = QGridLayout()
        status_box = QGroupBox('')

        combox = QComboBox()
        self.list_variables(combox)
        combox.currentIndexChanged.connect(self.change_variable)
        combox.name = 'xvar'
        top_layout_2.addWidget(combox, 0, 1)
        top_layout_2.addWidget(QLabel('x variable'), 0, 2)

        comboy = QComboBox()
        self.list_variables(comboy)
        comboy.currentIndexChanged.connect(self.change_variable)
        comboy.name = 'yvar'
        top_layout_2.addWidget(comboy, 0, 3)
        top_layout_2.addWidget(QLabel('y variable'), 0, 4)

        # plot button
        self.buttons = {}
        self.buttons['plot'] = QPushButton('plot', clicked=self.make_plot)
        top_layout_2.addWidget(self.buttons['plot'], 0, 5)

        self.buttons['save'] = QPushButton('save', clicked=self.save_plot)
        top_layout_2.addWidget(self.buttons['save'], 0, 6)

        self.buttons['exit'] = QPushButton('exit', clicked=self.exit_dialog)
        top_layout_2.addWidget(self.buttons['exit'], 0, 7)
        # save button
        status_box.setLayout(top_layout_2)
        self.layout.addWidget(status_box, 0, 0)

    def list_variables(self, combo):
        combo.addItems(self.dataframe.keys())

    def change_variable(self):
        s = self.sender()
        if s.name == 'xvar':
            self.xvar = s.currentText()
        if s.name == 'yvar':
            self.yvar = s.currentText()

    def read_file(self):
        # default is to load last saved file
        files = glob(os.path.join(self.dirout, 'data','*.xlsx'))
        self.dataframe = pd.read_excel(files[-1])

    def make_plot(self):
        f, ax = plt.subplots(1,1, figsize=(3.5, 2.2), dpi=250)

        xdata = self.dataframe[self.xvar]
        ydata = self.dataframe[self.yvar]

        ax.plot(xdata, ydata, marker='o', linestyle='None')
        ax.set_xlabel(self.xvar)
        ax.set_ylabel(self.yvar)
        plt.tight_layout()
        self.f = f
        self.ax = ax
        plt.show()

    def save_plot(self):
        """ write to the output"""
        dirout = os.path.join(self.dirout, 'data', 'plots')

        if not os.path.isdir(dirout):
            os.mkdir(dirout)

        files = glob(os.path.join(dirout, '*.png'))
        N = len(files) + 1
        sname = 'plot_%d.png' % N
        fname = os.path.join(dirout, sname)
        self.f.savefig(fname, dpi=900)

    def exit_dialog(self, event=None):
        buttonReply = QMessageBox.question(self, 'PyQt5 message', "Close parameters control dialog?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if buttonReply == QMessageBox.Yes:
            self.destroy()
            if self.parent == None:
                sys.exit(0)


def main(dirout=None):
   """ run stand-alone for testing """
   global app
   app = QApplication([])
   w = MakePlot(dirout=dirout)
   w.show()
   sys.exit(app.exec_())

if __name__ == '__main__':
    print('setup a small gui for plot control')
    dirout='C:/Users/Ryan/Desktop/Data/pro/2019-12-06_00.53.51'
    main(dirout=dirout)
