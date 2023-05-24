# TODO

* clear tracks issue in exe: deleting manually does not remove, new flocs added manually added to "non-existent" tracks
* fix process toggle on control panel - link to params correctly 
* save cropped ROI's in writer: need to reload image each time, so do this out of the track analysis loop
* labeler error when gradient filter turned off - queue never ends
* writer angle calculation is incorrect - test in Jupyter
* optional direction arrow to indicate bad settling
* complete packaging as exe
* make params button clear in paramtree: save? load? 
* make compile function clearer
* update docs
* add link to docs somewhere in safas: help icon

# activate venv
venv\Scripts\activate

# build requirements.txt file
pip-compile --output-file=- > requirements.txt

# Compiling to exe on windows
https://www.pythonguis.com/tutorials/packaging-pyside2-applications-windows-pyinstaller/
pyinstaller --noconfirm --name "safas" app.py

then

pyinstaller safas.spec --noconfirm