@echo off
REM Create venv and install requirements (Windows CMD)
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
echo Virtualenv created. Activate with: .\.venv\Scripts\activate.bat
