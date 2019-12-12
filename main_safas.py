
"""

main_safas.py

entry point to the safas gui

"""
from safas.mainpanel import MainPanel

if __name__ == '__main__':
    config_file = 'config_file.yml'
    MainPanel(config_file)
