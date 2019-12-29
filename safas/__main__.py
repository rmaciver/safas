"""
__main__.py

entry point to the safas gui

"""

import sys
import os
from PyQt5.QtWidgets import QApplication

import safas
from safas.gui.mainpanel import MainPanel

def main(args=None):
    """ parse args """
    # argument parsing with argparse here for access to functions later
    if args is None:
        args = sys.argv[1:]

    # do somehting to get a config file passed ...
    
    if len(args) == 0:
        # load the file from the safas module. this is weak but works for now
        print(safas.__path__)
        config_file = os.path.join(safas.__path__[0], 'config.yml')
        print(config_file)

    app = QApplication([])
    window = MainPanel(config_file)
    app.exec_()

if __name__ == "__main__":
    main()
