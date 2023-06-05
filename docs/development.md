# Development


# activate venv
venv\Scripts\activate

# build requirements.txt file
pip-compile --output-file=- > requirements.txt

# Compiling to exe on windows
https://www.pythonguis.com/tutorials/packaging-pyside2-applications-windows-pyinstaller/
pyinstaller --noconfirm --name "safas" app.py

then

pyinstaller safas.spec --noconfirm
