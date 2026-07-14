@echo off
cd /d "%~dp0"
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
)
streamlit run student_app.py --server.port 8502
pause
