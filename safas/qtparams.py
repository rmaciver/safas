"""
safas/qtparams.py

parameter tree UI element with pyqtgraph
"""
from copy import deepcopy
import sys
from pathlib import Path
import json

import logging
logger = logging.getLogger(__name__)

from PySide2.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from PySide2 import QtCore

import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree
import pyqtgraph as pg

import flatten_dict

from .prints import print_params as print

# NOTE: int values PARAMS cannot be None
PARAMS = [
{'name': 'io', "title": "I/O", 'type': 'group', 
'children': [
    {"name": "params_file", "type": "str", "value": "params.json"},
    {'name': 'input_path', "title": "Input path", "type": "file", "fileMode": "Directory","value": None, "directory": None},
    {'name': 'output_path', "title": "Output path", "type": "file", "fileMode": "Directory","value": None},
    {"name": "data_file", "title": "Input file", "type": "file", "fileMode": "ExistingFile", "directory": None,"psync": False,"value": None},
    {"name": "process_on_new_frame", "type": "bool", "value": True},
    {"name": "process_n_frames", "type": "bool", "value": False},
    {"name": "n_frames", "type": "int", "value": 50},
    {"name": "n_threads", "type": "int", "value": 6},
]
},
{"name": "labeler", "title": "Labeler", "type": "group",
 "children": [
    {"name": "common", "title": "Common", "type": "group", "children": 
        [{"name": "params_file", "type": "file", "fileMode": "ExistingFile", "psync": False,"value": None, "visible": False},
        {"name": "name", "type": "list", "value": "sobel_focus_v2", "values": ["edge_gradient"]},
        {"name": "process", "type": "bool", "value": True}
        ]
    },
]
},
{"name": "linker", "title": "Linker", "type": "group",
 "children": [
    {"name": "common", "title": "Common", "type": "group", "children": 
        [{"name": "params_file", "type": "file", "fileMode": "ExistingFile", "psync": False,"value": None, "visible": False},
        {"name": "name", "type": "list", "value": "linear", "values": ["linear_flocs"]},
        {"name": "process", "type": "bool", "value": True},
        {"name": "obj-select-mode", "type": "list", "value": "auto", "values": ["auto", "none"]}
        ]
    },
]
},
{"name": "writer", "title": "Writer", "type": "group",
 "children": [
    {"name": "common", "title": "Common", "type": "group", "children": 
        [{"name": "params_file", "type": "file", "fileMode": "ExistingFile", "psync": False,"value": None},
          
            {"name": "name", "type": "list", "value": "linear", "values": ["sed_exp"]},

        ]
    },
]
},
{'name': 'display', "title": "Display", 'type': 'group', 
'children': [
    {'name': 'objects', "title": "Objects", 'type': 'group', 'children': 
     [{'name': 'show', 'type': 'bool', 'value': True},
      {'name': 'contour_color', 'type': 'color', 'value': (0, 255, 0, 125)},
      {'name': 'contour_color_active', 'type': 'color', 'value': (255, 0, 255, 125)},
      {'name': 'contour_linewidth', 'type': 'float', 'value': 0.25, "limits": [0.1, 10]}
    ]},
    {'name': 'tracks', "title": "Tracks", 'type': 'group', 'children': 
      [{'name': 'show_objs', 'type':'bool','value': True},
      {'name': 'contour_color', 'type': 'color', 'value': (0, 0, 255, 125)},
      {'name': 'contour_linewidth', 'type': 'float', 'value': 0.25, "limits": [0.1, 10]},
      {'name': 'contour_color_active', 'type': 'color', 'value': (255, 0, 0, 125)},      
      {'name': 'show_lines', 'type':'bool','value': True},
      {'name': 'line_color', 'type': 'color', 'value': (100, 50, 255, 125)},
      {'name': 'line_color_active', 'type': 'color', 'value': (0, 50, 255, 125)},
      {'name': 'line_linewidth', 'type': 'float', 'value': 0.25, "limits": [0.1, 10]}
    ]}
]
},
# {"name": "screencap", "title": "ScreenCap", "type": "group",
#  "children": [
#     {"name": "common", "title": "Common", "type": "group", "children": 
#         [{"name": "x1", "type": "int", "value": None},
#          {"name": "x2", "type": "int", "value": None},
#          {"name": "get_cap", "title": "Record", "type": "action"},
#          {"name": "filename", "type": "file", "fileMode": "ExistingFile", "psync": False,"value": None},

#         ]
#     },
# ]
# },
]     

# TODO: populate linker and labler drop-down options with plugins available
class ParamsView(QWidget): 
    """Load ui file and connect application logic"""
    params_update_signal = QtCore.Signal(dict, name="params_update_signal")
    data_file_signal = QtCore.Signal(dict, name="data_file_signal")

    def __init__(self, 
                 parent=None, 
                 layout=None, 
                 params=None, 
                 ui=True, *args, **kwargs):
        super(ParamsView, self).__init__(*args, **kwargs)
        self.parent = parent
        self.params_setup(layout=layout, params=params, ui=ui)
     
    def params_setup(self, layout=None, params=None, ui=True): 
        """ populate the ui from parameters file """
        if params is None: params = deepcopy(PARAMS) # use default if None passed 
        self.p = Parameter.create(name='params', type='group', children=params)
        self.p.sigTreeStateChanged.connect(self.sync_to_ext) # sync external copies
        self.p.param("io","data_file").sigValueChanged.connect(self.data_file_changed)
        
        if ui: 
            # link pair of params
            self.pro_n = self.p.param('io','process_n_frames')
            self.pro_n.sigValueChanged.connect(self.pro_n_Changed)

            self.pro_new = self.p.param('io','process_on_new_frame')
            self.pro_new.sigValueChanged.connect(self.pro_new_Changed)

            # link processing on/off
            self.pro_label = self.p.param('labeler','common', 'process')
            self.pro_link = self.p.param('linker','common', 'process')
            
            self.pro_label.sigValueChanged.connect(self.pro_label_Changed)
            self.pro_link.sigValueChanged.connect(self.pro_link_Changed)

            self.t = ParameterTree(parent=self)
            self.t.setParameters(self.p, showTop=False)
        
            if layout is None: # make layout if not embedded in parent
                layout = QVBoxLayout()
                self.setLayout(layout)
            layout.addWidget(self.t)
    
    # next two are linked
    def pro_label_Changed(self):
        v = self.pro_label.value()
        self.pro_link.setValue(v, blockSignal=self.pro_link_Changed)
        self.parent.radio_process.setChecked(v)

    def pro_link_Changed(self):
        v = self.pro_link.value()
        self.pro_label.setValue(v, blockSignal=self.pro_label_Changed)
        self.parent.radio_process.setChecked(v)

    # next two are linked
    def pro_n_Changed(self):
        self.pro_new.setValue(not self.pro_n.value(), blockSignal=self.pro_new_Changed)

    def pro_new_Changed(self):
        self.pro_n.setValue(not self.pro_new.value(), blockSignal=self.pro_n_Changed)

    def data_file_changed(self): 
        self.data_file_signal.emit(self.p.param("io","data_file").value())

    def params_from_file(self, from_config=False, **kwargs): 
        """ """   
        pth = self.p.param('io', 'base_input').value
        out = QFileDialog().getOpenFileName(parent=None, 
                                            directory=pth, 
                                            caption="Select parameters file",
                                            filter="JSON (*.json)")
        if len(out) == 0: return False
        filename = Path(out[0])
   
        try: 
            with open(filename, "r") as f: params = json.load(f)
            self.p.restoreState(params)
            self.p.param("io", "params_file").setValue(str(filename))
        except (json.JSONDecodeError, FileNotFoundError) as error:  
            txt = f"Error in params file: {error}"
        except Exception as error: 
            txt = f"Error in params file: {error}"

    def params_to_file(self, filename=None): 
        """
        """
        if filename is None: 
            pth = self.p.param('io', 'output_path').value
            out = QFileDialog.getSaveFileName(parent=None, 
                                            directory=pth, 
                                            caption="Select parameters file",
                                            filter="JSON (*.json)")
            if len(out) == 0: return None
            filename = Path(out[0])
              
        state = dict(self.p.saveState(filter="user")) # remove module/ UI element-instances
        state = ungroup_params(state)  # remove unnecessary value/ children keys
        
        try: 
            with open(str(filename), "w") as f: json.dump(state, f, indent=1)
        except Exception as e: 
            print(f"Params not written: {e}")

    def sync_to_ext(self): 
        """ update to external"""
        path = self.p.param("io","input_path").value() 
        if (path != "") & (path is not None) & (path !=0): 
            self.p.param("io","data_file").setOpts(directory=path) # sync external copies
        # NOTE: sync with flat dict
        state = dict(self.p.saveState(filter="user")) # remove module/ UI element-instances
        state = ungroup_params(state)  # remove unnecessary value/ children keys
        self.params_update_signal.emit(state)

    @QtCore.Slot(str, dict)
    def insert_child_group(self, node_name, group_params): 
        """ update to external"""
        # TODO: handle remove/ replace kwargs when new plugin is added
        key = list(group_params)
        try: 
            self.p.param(node_name).addChildren(group_params)
        except Exception as e: 
            key = list(group_params.keys())[0]
            print(f"{key} parameters not restored: {e}")

    @QtCore.Slot(dict)
    def sync_from_ext(self, param): 
        """ update single value from external flat dict"""
        try: 
            key, value = list(param.items())[0]
        except Exception as e: 
            print(f"key-value pair not parsed from param {param}: {e}")
            return None

        try:               
           self.p.param(*key).setValue(value)
        except Exception as e: 
            print(f"qtparams tree not updated with {key}:{value}: {e}")

def ungroup_params(params): 
    """ remove value, children headings introduced by pyqtgraph on export"""
    # TODO: deuglify this code to cleanup headings for user readable config files
    params_f = flatten_dict.flatten(params)
    params_m = {}
    for key in params_f: 
        key_t = list(key)
        key_t = [i for i in key_t if i != "children"]
        key_t = [i for i in key_t if i != "value"]
        if len(key_t) <= 1: 
            continue
        params_m[tuple(key_t)] = params_f[key]

    params_x = {}

    for key in params_m: 
        out = [len(list(set(key).difference(set(v)))) for v in params_m]
        out = [a for a in out if a == 0]
        if len(out) == 1: 
            params_x[key] = params_m[key]
    params_x = flatten_dict.unflatten(params_x)
    return params_x