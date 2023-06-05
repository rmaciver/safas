# Installation

The easiest way to use Safas is to download a pre-compiled binary (e.g. safas.exe for Windows). For tinkering and development, a few notes are made below for setting up Safas in a virtual environment. 

The 
## Virtualenv
The virtualenv package was used to make a virtual environment for Safas development with pip as the package manager. This was chosen due to the use of pip freeze to generate the compiled (safas.exe on Windows) version of the software. It should still be possible to run the project from Conda; however this is no longer the preferred method. 

Steps: 
1. Install [virtualenv](https://virtualenv.pypa.io/en/latest/installation.html). Perhaps the easiest way is if you already have a Python interpreter installed is to use: 
```
python -m pip install --user virtualenv
```
2. Open a console window inside the top-level project directory. Hint: In Windows you can type "cmd" in the address bar while in the project directory to open a console window there. 

3. Create and activate the virtualenv. 
```
virtualenv venv
.\venv\Scripts\activate
```
4. Install the requirements. 
Activate virtual env: 
```
safas-dist$ .\venv\scripts\activate
```


Create virtual env: 
```
virtualenv venv
.\venv\Scripts\activate
```

Activate virtual env: 
```
mudrushdetector-master$ .\venv\scripts\activate
```


Setup before install:
* Download and install [Miniconda3](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/distribution/#download-section)
* Add Miniconda3/condabin to system PATH so 'conda' can be called from cmd prompt
* Download and install atom https://atom.io/ a text editor to preserve yml and py formatting.

## Setup conda path
Before you can use conda on the command line, the condabin directory must be added to the path in windows environmental variables. Click the windows icon, then start typing "environmental variables", then follow the steps outline in the figure below.   

<img align="center" src="../img/conda_bin_env_var.PNG" alt="add condabin" width="400">

*Fig. 1: Add condabin to path*

## Virtual environment
Download or pull (with git) the Safas package master branch from the command line or by pressing the green "Clone or Download" button at the top right-hand side of the page:

<https://github.com/rmaciver/safas>

Open a command prompt in the downloaded Safas package. The file 'environment.yml' will be used to prepare a conda virtual environment using the following command:

``` shell
$ conda env create -f environment.yml
```

When the environment has been installed, activate it with:

``` shell
$ conda activate safas_env
```

The Safas package may now be installed with:
``` shell
(safas_env) $ python setup.py install
```

Safas can be loaded from the command prompt as follows:
``` shell
(safas_env) $ safas
```
Or, setup a batch file to open Safas with one click.

## Creating a shortcut
The file 'safas/config.yml' contains many of the key parameters and variables used by Safas for calculations and visualizations. By default, the one from the package will be used to setup Safas if one is not passed to the software when it is started.

One option is to make a copy of the config.yml file and place it in a directory along with a batch file to load the virtual environment and launch the software. Open a command prompt in the location you would like to setup the Safas shortcut (e.g. Desktop or project folder), then type the following commands:

``` shell
(safas_env) $ mkdir safas
(safas_env) $ cd safas
(safas_env) $ (echo call activate safas_env && echo safas config.yml  && echo pause) > safasrun.bat
```
Then copy the 'config.yml' file from the downloaded package (or module inside the virtual env) into the new safas folder. Then, you will be able to modify the config file as necessary and start Safas by dobule-clicking the batch (.bat) file.

##  New installation notes
* download and install Miniconda3 https://docs.conda.io/en/latest/miniconda.html
* add Miniconda3/condabin to system PATH so 'conda' can be called from cmd prompt
* download and install atom https://atom.io/ a text editor to preserve yml and py formatting
* download and unzip safas https://github.com/rmaciver/safas
* open command line in the unzipped safas directory
* create a conda environment from the environment.yml file:
``` shell
$ conda env create -f environment.yml
```
* activate safas_env and install safas:
``` shell
$ conda activate safas_env
```
(safas_env) $ python setup.py install
* create a shortcut folder and .bat file with link to safas on readthedocs

## GPU-enabled OpenCV
Safas will run slightly faster if the OpenCV package used is GPU-enabled. The default OpenCV4 in the Conda repository is not GPU-enabled, therefore you must either build OpenCV from source or download a prebuilt binary and install it manually.

Here is one method to install a GPU-enabled version of OpenCV with Windows 10:

1. Confirm whether any previous installation of OpenCV is OpenCL-enabled. In a Python shell:
``` shell
import cv2
cv2.ocl.useOpenCL()
```
2. If Step 1. was False, then remove the existing OpenCV installation and proceed to install the pre-comiled OpenCV executable from Source Forge.
3. Download the [precompiled OpenCV binary for windows:](https://sourceforge.net/projects/opencvlibrary/files/opencv-win/).
4. Click: "Download Latest Version" (opencv-4.1.2-vc14_vc15.exe), then extract the package.
4. Activate your conda environment
3. Setup the environmental variables. Run 'opencv/build/setup_vars_opencv4.cmd' in the command prompt to update the path variables that will enable your Python executable to find OpenCV.
4. Copy the OpenCV .pyd file from 'opencv\build\python\cv2\python-3.6\cv2.cp36-win_amd64.pyd' to the directory of your Python executable. For example, with a Miniconda installation Python 3.6 environment called 'safas_env', move the file to '\Miniconda3\envs\safas_env.'
5. Check that you can import OpenCV and that it is OpenCL-enabled, as in Step 1.
