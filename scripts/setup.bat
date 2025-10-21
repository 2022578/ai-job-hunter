@echo off
REM GenAI Job Assistant - Setup Script for Windows
REM This script handles initial installation and configuration

setlocal enabledelayedexpansion

echo.
echo ==========================================
echo GenAI Job Assistant - Setup
echo ==========================================
echo.

REM Step 1: Check Python version
echo [INFO] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.8 or higher.
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python %PYTHON_VERSION% found
echo.

REM Step 2: Create virtual environment
echo [INFO] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo [SUCCESS] Virtual environment created
) else (
    echo [WARNING] Virtual environment already exists
)
echo.

REM Step 3: Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
echo [SUCCESS] Virtual environment activated
echo.

REM Step 4: Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1
echo [SUCCESS] pip upgraded
echo.

REM Step 5: Install dependencies
echo [INFO] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    exit /b 1
)
echo [SUCCESS] Dependencies installed
echo.

REM Step 6: Check Ollama installation
echo [INFO] Checking Ollama installation...
where ollama >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama is not installed
    echo [INFO] Please install Ollama from: https://ollama.ai/download
    echo [INFO] After installation, run: ollama pull llama3
) else (
    echo [SUCCESS] Ollama found
    
    REM Check if Ollama is running
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if not errorlevel 1 (
        echo [SUCCESS] Ollama service is running
        
        REM Check if llama3 model is available
        ollama list | findstr "llama3" >nul 2>&1
        if not errorlevel 1 (
            echo [SUCCESS] llama3 model is available
        ) else (
            echo [WARNING] llama3 model not found
            echo [INFO] Downloading llama3 model (this may take a while)...
            ollama pull llama3
            echo [SUCCESS] llama3 model downloaded
        )
    ) else (
        echo [WARNING] Ollama service is not running
        echo [INFO] Start Ollama with: ollama serve
    )
)
echo.

REM Step 7: Check Chrome
echo [INFO] Checking Chrome installation...
where chrome >nul 2>&1
if not errorlevel 1 (
    echo [SUCCESS] Chrome found
) else (
    echo [WARNING] Chrome not found
    echo [INFO] Please install Chrome for web scraping functionality
)
echo.

REM Step 8: Initialize application
echo [INFO] Initializing application...
python scripts\init_app.py
if errorlevel 1 (
    echo [ERROR] Application initialization failed
    exit /b 1
)
echo [SUCCESS] Application initialized successfully
echo.

REM Step 9: Display next steps
echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo.
echo 1. Configure your preferences:
echo    - Edit config\config.yaml with your job search criteria
echo    - Update user profile information
echo    - Configure notification settings
echo.
echo 2. (Optional) Set up notifications:
echo    - For email: Add SMTP credentials to config\config.yaml
echo    - For WhatsApp: Add Twilio credentials to config\config.yaml
echo.
echo 3. Start the application:
echo    - Interactive UI: streamlit run app.py
echo    - Background scheduler: python scripts\run_scheduler.py
echo.
echo 4. (Optional) Set up automated backups:
echo    - Run: python scripts\backup_db.py
echo    - Add to Task Scheduler for daily backups
echo.
echo [SUCCESS] Setup completed successfully!
echo.

pause
