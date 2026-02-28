@echo off
REM Full build script for Preservation Universe App
REM This script builds the app, generates hash, and copies all necessary files

echo ========================================
echo Building Preservation Universe App
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed!
    echo Please install it with: pip install pyinstaller
    pause
    exit /b 1
)

echo Step 1: Building application with PyInstaller...
echo.
python -m PyInstaller main.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo Step 2: Copying version.txt to dist folder...
if exist version.txt (
    copy /Y version.txt dist\version.txt >nul
    echo   - version.txt copied
) else (
    echo   - WARNING: version.txt not found
)

echo.
echo Step 3: Generating SHA256 hash file...
cd dist
if exist "Preservation Universe.exe" (
    powershell -Command "Get-FileHash -Path 'Preservation Universe.exe' -Algorithm SHA256 | Select-Object -ExpandProperty Hash | Out-File -Encoding ASCII 'Preservation Universe.exe.sha256'"
    echo   - SHA256 hash generated: Preservation Universe.exe.sha256
) else (
    echo   - ERROR: Preservation Universe.exe not found!
    cd ..
    pause
    exit /b 1
)

cd ..

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Files created in dist folder:
echo   - Preservation Universe.exe
echo   - Preservation Universe.exe.sha256
echo   - version.txt
echo.
echo Ready for distribution!
echo.
pause
