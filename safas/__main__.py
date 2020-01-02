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
        # check for config file from command line
        args = sys.argv[1:]
        if len(args) > 0:
            file = args[0]
            if os.path.isfile(file):
                config_file = file

    if config_file is None:
        # load the default config file from safas module
        config_file = os.path.join(safas.__path__[0], 'config.yml')

    app = QApplication([])
    f = app.font();
    f.setFamily("Monaco");
    f.setPointSize(9);
    app.setFont(f)

    window = MainPanel(config_file)
    app.exec_()

if __name__ == "__main__":
    main()
