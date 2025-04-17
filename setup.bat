@echo off
:: Setup script for Red Cloner
SETLOCAL

:: Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Running as admin - good
) else (
    echo Please run this script as Administrator!
    pause
    exit /b 1
)

:: Create virtual environment
echo Creating virtual environment...
python -m venv venv
if not exist "venv\" (
    echo Failed to create virtual environment
    pause
    exit /b 1
)

:: Install dependencies
echo Installing dependencies...
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install pyinstaller PyQt5 tqdm

:: Create desktop shortcut
echo Creating desktop shortcut...
set SHORTCUT="%USERPROFILE%\Desktop\Red Cloner.lnk"
set TARGET="%~dp0venv\Scripts\pythonw.exe"
set ICON="%~dp0cloner_icon.ico"
set ARGS="%~dp0gui.py"

echo [InternetShortcut] > %SHORTCUT%
echo URL=%TARGET% %ARGS% >> %SHORTCUT%
echo IconFile=%ICON% >> %SHORTCUT%
echo IconIndex=0 >> %SHORTCUT%

echo Setup completed successfully!
pause