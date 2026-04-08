@echo off
REM Run script for OpenEnv Email Triage (Windows)

echo.
echo 🚀 Starting OpenEnv Email Triage v2.0
echo.

REM Check Python version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    exit /b 1
)

python --version
echo ✅ Python found

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo 📚 Installing dependencies...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

REM Create static directory if it doesn't exist
if not exist "static" (
    echo 📁 Creating static directory...
    mkdir static
)

REM Run the application
echo.
echo 🌐 Starting server...
echo ═══════════════════════════════════════════════════════════════════
echo 📧 OpenEnv Email Triage is running!
echo.
echo 🌐 Frontend:  http://localhost:8000
echo 📚 API Docs:  http://localhost:8000/docs
echo 📖 ReDoc:     http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo ═══════════════════════════════════════════════════════════════════
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
