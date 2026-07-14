@echo off
cd /d "%~dp0"
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
)
streamlit run teacher_app.py --server.port 8501
pause
