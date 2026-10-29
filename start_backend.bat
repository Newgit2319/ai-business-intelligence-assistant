@echo off
cd /d "%~dp0backend"
if not exist venv\Scripts\python.exe (
  echo Backend environment not found. Run setup_backend.bat first.
  pause
  exit /b 1
)
call venv\Scripts\activate.bat
uvicorn main:app --reload
