#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

    automatically retrieve TIS camera properties with python

    this is a GUI wrapper for the camprops.py module

    m.r. maciver, rmaciver@chemetc.com

    with reference to:
    https://github.com/TheImagingSource/tiscamera.git/examples/python/01-list-properties.py

    refer to: DFK 33GX264 Technical Reference Manual, trmdfk33gx264.en_US.pdf
        chapter 5, pg 13


"""
import sys
import os

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import fragmon
from fragmon.comp.cam_props import CamProps
from fragmon.comp.parse_props import *
from fragmon.comp.parse_config import Config

class DialogProps(QMainWindow):

    def __init__(self,
                 parent=None,
                 camera=None,
                 params=None,
                 config_file=None,
                 cprops=None,
                 ):

        super(DialogProps, self).__init__(parent)

        # check if config is a file or a dict ... then read it in if nec.
        if config_file is not None:
            # read in the file
            cfig = Config(config_file)
            self.params = cfig.config
        elif params != None:
            self.params = params
        else:
            self.params = {}

        self.parent = parent
        self.camera = camera

        # workaround for the testsrc
        if not hasattr(self.parent.cprops):
            self.cprops = CamProps(camera=self.camera, params=self.params)

        self.setup_window()

    def setup_window(self):
        self.setWindowTitle('camera properties')
        self.layout = QGridLayout()

        # fill tabs with cam props
        T = PropsTabs(params=self.params, parent=self)
        self.layout.addWidget(T, 0, 0)
        self.widgs = T.tabs_list

        # add the update and save buttons
        self.control_buttons()

        w = QWidget()
        w.setLayout(self.layout)
        self.setCentralWidget(w)

        self.height = 1000
        self.width = 1000
        # resize and show the display window
        self.setGeometry(450, 100, self.width, self.height)
        self.show()

    def control_buttons(self):
        top_layout_2 = QHBoxLayout()
        ctrl_groupbox = QGroupBox('')
        ctrl_groupbox.setAlignment(Qt.AlignCenter)

        updateButton = QPushButton('Update', clicked=self.set_cam_props)
        saveButton = QPushButton('Save', clicked=self.save_cam_props)
        exitButton = QPushButton('Exit', clicked=self.exit_dialog)

        top_layout_2.addWidget(updateButton)
        top_layout_2.addWidget(saveButton)
        top_layout_2.addWidget(exitButton)
        ctrl_groupbox.setLayout(top_layout_2)
        self.layout.addWidget(ctrl_groupbox, 1, 0)

        self.buttons = {}
        self.buttons['control'] = {'udpatetButton': updateButton,
                                   'saveButton': saveButton,
                                   'exitButton': exitButton,
                                   }

    def get_cam_props(self):
        self.cprops = CamProps(camera=self.camera)

    def set_cam_props(self):
        print('Update camera from GUI settings')
        props = self.get_gui_props()
        self.cprops.props = props
        for name in props.keys():
            self.set_prop(name, props[name])

    def set_prop(self, name, value):
        self.cprops.set_props(name, value)

    def get_gui_props(self):
       # a bit awkward here ...
        propsout = {}

        for tab in self.widgs:
            for grp in self.widgs[tab]['group'].keys():
                T = self.widgs[tab]['group'][grp]

                for name in T.keys():
                    # quick fix: no apparent need to write the button values
                    if type(T[name]['widget']) == QPushButton:
                        continue

                    propsout[name] = {'value_type': T[name]['value_type'] }

                    if type(T[name]['widget']) == QLabel:
                        propsout[name]['value'] =  T[name]['widget'].text(),

                    if type(T[name]['widget']) == QSlider:
                        propsout[name]['value'] =  T[name]['widget'].value()

                    if type(T[name]['widget']) == QWidget:
                        for wg in T[name]['widget'].children():
                            if type(wg) == QRadioButton:
                                if wg.text() == 'True':
                                    if wg.isChecked:
                                        propsout[name]['value'] = True
                                    else:
                                         propsout[name]['value'] = False
        return propsout            

    def save_cam_props(self):
        print('save the props to a config file or device mem for reloading')
        print('Enter file name.')
        path = os.path.dirname(fragmon.__file__)
        path = os.path.join(path, 'params/device')

        dialog = QFileDialog()
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(['*.yml'])
        dialog.setDirectory(path)

        if dialog.exec_() == QDialog.Accepted:
            self.params['device_settings'] = dialog.selectedFiles()[0]
        else:
            print('Cancelled')

        self.cprops.props = self.get_gui_props()
        self.cprops.save_props(params=self.params)

    def exit_dialog(self, event=None):
        print('close the dialog')

        buttonReply = QMessageBox.question(self, 'PyQt5 message', "Close camera properties dialog?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if buttonReply == QMessageBox.Yes:
            print('Yes clicked.')
            self.destroy()

            if self.parent == None:
                sys.exit(0)
        if buttonReply == QMessageBox.No:
            print('No clicked.')

class PropsTabs(QTabWidget):
    """
    categories of properties for the camera
    """
    def __init__(self, parent=None, params=None):
        super(PropsTabs, self).__init__(parent)

        # only get/ set properties in this dictionary, for tcam
        self.prop_filt = {'tcam-gige': ['Color','Exposure'],
                          'nocam-test': ['Color', 'Exposure'],
                          }

        self.params = params
        top_layout = QHBoxLayout()
        ctrl_groupbox = QGroupBox('tabs')

        self.parent = parent

        if parent != None:
            self.props = parent.cprops.props

        self.org_names()
        self.names_to_tabs()

    def org_names(self):
        props = self.props
        # organize properties by Category > Group > Name to pop. the tabs
        cats = set()
        tabs = {}

        for name in props:
            cat = props[name]['category']
            grp = props[name]['group']

            if not cat in cats:
                cats.add(cat)
                tabs[cat] = {}
            if not grp in tabs[cat]:
                tabs[cat][grp] = set()

            tabs[cat][grp].add(name)

        self.tabs = tabs

    def names_to_tabs(self):

        tabs = self.tabs
        self.tabs_list = {}

        src = self.params['srcname']
        # then add Category > Group > Name
        for tab in tabs:
            if tab not in self.prop_filt[src]:
                continue

            print('Tab is:', tab)
            # make and add the tab
            self.tabs_list[tab] = {}
            self.tabs_list[tab]['group'] = {}
            self.tabs_list[tab]['category'] = tab

            self.tabs_list[tab]['tabWidget'] = QWidget()
            self.addTab(self.tabs_list[tab]['tabWidget'], tab)

            toplayout = QGridLayout()
            i=0

            for grp in tabs[tab]:
                #sublayout = QVBoxLayout()

                self.tabs_list[tab]['group'][grp] = {}

                # add a group box to the tab
                labelA = QLabel()
                labelA.setText(grp)
                labelA.setFont(QFont("Times", 11, QFont.Bold))
                labelA.setAlignment(Qt.AlignCenter)
                toplayout.addWidget(labelA, i, 0, 1, 2)
                i+=1

                # refer to trmdfk33gx264.en_US.pdf camera manual for
                # settings to turn off auto exposure and auto gain, if necessary

                for name in tabs[tab][grp]:
                    if (name == 'DeviceTemperature') or (name == 'DeviceTemperatureSelector'):
                        continue

                    labelA = QLabel()
                    labelA.setText(name)
                    labelA.setFont(QFont("Times", 10))

                    toplayout.addWidget(labelA, i, 0)

                    widg = get_widget(self.props[name])
                    value_type = self.props[name]['value_type']
                    self.tabs_list[tab]['group'][grp][name] = {'widget': widg,
                                                               'value_type': value_type}
                    toplayout.addWidget(widg, i, 1)
                    i+=1

                #toplayout.addLayout(sublayout, i, 0)
                toplayout.setContentsMargins(10,10,0,0)
                self.tabs_list[tab]['tabWidget'].setLayout(toplayout)

def main(params=None, config_file=None):

   app = QApplication([sys.argv])
   w = DialogProps(parent=None, params=params, config_file=config_file)
   w.show()
   sys.exit(app.exec_())

if __name__ == '__main__':
    print('Test camera properties dialog')


    params = {'serial': '06910224',
              'test': True,
              'srcname': 'nocam-test'}

    path = os.path.dirname(fragmon.__file__)

    config_file = os.path.join(path, 'params/stream/INS_videotestsrc.yml')

    main(config_file=config_file)
