@echo off
echo ==================================================
echo GTM Voyager Platform - Authentication Setup
echo ==================================================

REM Check if we're in the right directory
if not exist "requirements.txt" (
    echo Error: Please run this script from the GTM Voyager Platform root directory
    pause
    exit /b 1
)

REM Try to find and activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo Virtual environment activated (venv)
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated (.venv)
) else if exist "env\Scripts\activate.bat" (
    call env\Scripts\activate.bat
    echo Virtual environment activated (env)
) else (
    echo Warning: Virtual environment not found, using system Python
    echo Make sure you have Python and pip installed
)

REM Install dependencies
echo.
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo Dependencies installed

REM Initialize database
echo.
echo Initializing database...
python src\gtm_voyager\database\init_db.py

echo.
echo Setup completed!
pause
