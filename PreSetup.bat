@echo off
title Controller Mapper Setup

echo ========================================
echo  Controller Mapper Dependency Installer
echo ========================================
echo.
echo This script will check for Python and install the required libraries.
echo.

REM --- Check for Python ---
echo [+] Checking for Python 3...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [!] ERROR: Python is not installed or not added to your system's PATH.
        echo Please install Python 3 from python.org and make sure to check the
        echo "Add Python to PATH" option during installation.
        echo.
        pause
        exit /b
    )
)

echo [+] Python found. Checking for pip...

REM --- Ensure Pip is available ---
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Pip not found. Attempting to install it...
    python -m ensurepip --upgrade
    if %errorlevel% neq 0 (
        echo [!] ERROR: Failed to install pip. Your Python installation might be corrupted.
        echo Please try reinstalling Python.
        echo.
        pause
        exit /b
    )
)
echo [+] Pip is available.

REM --- Install required packages ---
echo.
echo [+] Installing required packages (pygame, pynput)...
python -m pip install pygame pynput
echo.

echo ========================================
echo  Setup Complete!
echo ========================================
echo All necessary libraries have been installed.
echo You can now run the 'Uni_Mapper.py' script.
echo.
pause