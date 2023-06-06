# Development

Additional dependencies:
```
pyinstaller
```

Activate venv: 
```
venv\Scripts\activate
```
Build requirements.txt file: 
```
(venv)$ pip-compile --output-file=- > requirements.txt
```
# Compiling to exe on windows
https://www.pythonguis.com/tutorials/packaging-pyside2-applications-windows-pyinstaller/

To run first build and generate spec file: 
```
pyinstaller --noconfirm --name "safas" safas/app.py
```
then run with that spec file (need to add ui and config files): 
```
pyinstaller safas.spec --noconfirm
```