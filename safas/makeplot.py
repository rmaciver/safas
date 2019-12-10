# -*- coding: utf-8 -*-
"""
makeplot.py

make a figure from the data selected
"""

class MakePlot(QMainWindow):
    def __init__(self, dirout=None, *args, **kwargs):
        super(MakePlot, self).__init__(*args, **kwargs)
        
        self.dirout = dirout
