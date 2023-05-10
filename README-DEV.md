# activate venv
venv\Scripts\activate

# build requirements.txt file
pip-compile --output-file=- > requirements.txt