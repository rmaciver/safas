"""
__main__.py

entry point to the safas gui

"""

import sys
import os
from glob import glob
from PyQt5.QtWidgets import QApplication

import safas
from safas.gui.mainpanel import MainPanel

def main(config_file=None):
    """ parse args """
    # argument parsing with argparse here for access to functions later
    # update to more formal implementation
    if config_file is None:
        file = sys.argv[1:][0]
        if len(file) > 0:
            print('file passed to cmd line')
            if os.path.isfile(file):
                config_file = file

    if config_file is None:
        print('local file from launch directory')
        file = os.path.join(os.getcwd(), glob('*.yml')[0])
        print(file)
        if os.path.isfile(file):
            config_file = file

    if config_file is None:
        print('default from module')
        print(safas.__path__)
        config_file = os.path.join(safas.__path__[0], 'config.yml')
        print(config_file)

    app = QApplication([])
    window = MainPanel(config_file)
    app.exec_()

if __name__ == "__main__":
    main()
