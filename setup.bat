@echo off
setlocal

REM Define virtual environment directory name
set VENV_DIR=venv
set PYTHON_VERSION=3.11

REM Check if virtual environment already exists
if exist %VENV_DIR%\ (
    echo Virtual environment "%VENV_DIR%" already exists. Skipping creation.
) else (
    echo Creating virtual environment in "%VENV_DIR%"...
    python%PYTHON_VERSION% -m venv %VENV_DIR%
    echo Virtual environment created.
)

REM Activate the virtual environment
echo Activating virtual environment...
call %VENV_DIR%\Scripts\activate.bat

REM Check for requirements.txt and install if present
if exist requirements.txt (
    echo Installing dependencies from requirements.txt...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo Dependencies installed.
) else (
    echo requirements.txt not found. Skipping dependency installation.
)

echo Setup complete.
endlocal
pause
