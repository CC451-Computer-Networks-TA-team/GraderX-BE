GraderX-BE
=================


Getting Started
-----------

### Install requirements
In a virtual environment with python 3.8
```bash
pip install -r requirements.txt
```
### Pull submodules
Make sure you have access to the submodule repo
```bash
git submodule update --init --recursive
```
### Run
```bash
python run.py
```

Notes
-----------
- When you try to upload a submissions file to the api, you'll be prompted to enter your password because the grader requires sudo access

