#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

setconfig.py

1 import YAML configuration file
2 setup output

* functionality would be easier to access from GUI and contol.py if this were
    a class

"""
import os
import datetime
import shutil
import yaml

def config_params(params=None, params_file=None, **kwargs):
    """
    take parameters from YAML configuration file or from dictionary passed
    """
    if params_file:
        params = read_params(params_file)
        params['params_file'] = params_file

    elif params:
        params = params
    else:
        print('params file or dictionary not passed')

    return params

def set_dirout(params=None, dir_name=None, folders=None, **kwargs):
    # check the inputs: min headings need to be included
    dir_out = params['baseout']

    if not os.path.exists(dir_out):
        os.makedirs(dir_out)

    time_stamp = datetime.datetime.now().strftime('%Y-%m-%d_%H.%M.%S')
    dir_stamp = time_stamp

    if dir_name:
        dir_stamp += '_'
        dir_stamp += str(dir_name)

    dir_out = os.path.join(dir_out, dir_stamp)
    os.makedirs(dir_out)

    if folders is None:
        folders = ['params', 'imgs', 'data']

    [os.makedirs(os.path.join(dir_out,pth)) for pth in folders]

    params['output'] = dir_out

    if 'params_file' in params:
        copy_params(params['params_file'], params['output'])

    params['readme'] = readme(params['output'])
    values = [('Image trial info'),('File timestamp: ' + time_stamp)]
    updatereadme(params['readme'].name, values)

    return params

def read_params(file):
    """ get parameters from config file """
    with open(file) as f:
        params = yaml.safe_load(f)
    return params

def write_params(file, params):
    """ write params to yaml file"""
     # cannot serialize '_io.TextIOWrapper' object
    if 'readme' in params:
        params.pop('readme')

    with open(file, 'w') as file:
        docs = yaml.dump(params, file)

def updatereadme(readme, lines):
    """
    add new lines to the readme file
    """
    lines2 = []
    for st in lines:
        lines2.append((st + '\n'))

    with open(readme, "a") as myfile:
        myfile.write('\n')
        myfile.writelines(lines2)

def readme(new_dir):
    """
    make a readme in the output folder
    """
    nm = os.path.join(new_dir, 'params','readme.txt')
    f = open(nm,'w')
    f.close()

    return f

def copy_params(config_file, new_dir):
    """
    copy config_file to new location
    """
    name = os.path.basename(config_file)
    new_dir = os.path.join(new_dir, 'params', name)
    shutil.copyfile(config_file, new_dir)
