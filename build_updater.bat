@echo off
REM Build script for updater.exe
REM This script builds the updater executable using PyInstaller

echo Building updater.exe...
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed!
    echo Please install it with: pip install pyinstaller
    pause
    exit /b 1
)

REM Build updater.exe
python -m PyInstaller updater.spec

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo Build successful!
echo updater.exe is located in: dist\updater.exe
echo.
echo Copy updater.exe to your app directory alongside PreservationApp.exe
echo.
pause

