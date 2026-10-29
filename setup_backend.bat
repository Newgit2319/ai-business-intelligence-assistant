@echo off
cd /d "%~dp0backend"
python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python import_data.py
pause
