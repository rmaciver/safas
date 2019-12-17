
"""

main_safas.py

entry point to the safas gui

"""
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from safas.mainpanel import MainPanel

if __name__ == '__main__':
    config_file = 'config_file.yml'
    app = QApplication([])
    window = MainPanel(config_file)
    app.exec_()
