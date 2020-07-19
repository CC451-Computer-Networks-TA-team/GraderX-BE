GraderX-BE
=================


Getting Started
-----------

### Install requirements
> #### Virtual environment setup

1. [__optional__] install Virtual Python Environment builder
    ```bash
    pip install virtualenv 
    ```
1. Create your virtual environment
    ```bash
    virtualenv -p python3 <environment_name>
    virtualenv -p python3 venv
    ```
1. Finally, activate it
    ```bash
    source ./venv/bin/activate
    ```

    > On activation, your terminal should now start with _(venv)_

1. Make sure lists are installed, python version is 3.8
    ```bash
    pip list
    python -V
    ```
> In a __virtual environment__ with _python 3.8_
    
```bash
    pip install -r requirements.txt
```

---

### Pull submodules
> Make sure you have __access__ to the submodule repo
```bash
git submodule update --init --recursive
```
---

### Run
> Make sure the virtual environment is __activated__
```bash
python run.py
```

---
Notes
-----------
- When you try to upload a submissions file to the api, you'll be prompted to enter your password because the grader requires __sudo__ access

- If you got :
    > SyntaxError: Non-ASCII character '\xe2' in file

    just add `# -*- coding: utf-8 -*-` to the top of `console_log_parser.py` file