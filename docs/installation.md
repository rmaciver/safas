# Installation

The easiest way to use Safas is to download a pre-compiled binary (e.g. safas.exe for Windows). For tinkering and development, a few notes are made below for setting up Safas in a virtual environment. 

## Precompiled binary
For Windows 10 on x64-based PC, a package containing a pre-compiled binary can be downloaded from https://github.com/rmaciver/safas/releases. Note that the package is quite large (>200 MB) but contains all dependencies and files to run Safas without conducting any other installation steps. 

Download the package and extract the archive. Locate the file "safas.exe" in the extracted directory. Double-click to run and you are now using Safas.

## Virtualenv
The virtualenv package was used to make a virtual environment for Safas development with pip as the package manager. This was chosen due to the use of pyinstaller to generate the compiled version of the software.

Steps: 
* Install [virtualenv](https://virtualenv.pypa.io/en/latest/installation.html). Perhaps the easiest way is if you already have a Python interpreter installed is to use: 
```
python -m pip install --user virtualenv
```

* Open a console window inside the top-level project directory. Hint: In Windows you can type "cmd" in the address bar while in the project directory to open a console window there. 

* Create and activate the virtualenv. 
```
$ virtualenv venv
$ .\venv\Scripts\activate
(venv)$
```

* Install requirements.
```
(venv)$ pip install -r requirements.txt
```

* Run. 
```
(venv)$ python app.py
```

