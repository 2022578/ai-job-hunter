@echo off
echo Stopping any running Streamlit processes...
taskkill /F /IM streamlit.exe 2>nul
timeout /t 2 /nobreak >nul

echo Starting Streamlit...
call venv\Scripts\activate
streamlit run app.py
