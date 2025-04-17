@echo off
:: Build script for Red Cloner
SETLOCAL

call venv\Scripts\activate

:: Create spec file if not exists
if not exist "cloner.spec" (
    echo Generating spec file...
    pyi-makespec --onefile --windowed --icon=cloner_icon.ico --name RedCloner gui.py
)

:: Build the executable
echo Building executable...
pyinstaller cloner.spec

if exist "dist\RedCloner.exe" (
    echo Build successful!
    echo Executable: %~dp0dist\RedCloner.exe
) else (
    echo Build failed!
)

pause