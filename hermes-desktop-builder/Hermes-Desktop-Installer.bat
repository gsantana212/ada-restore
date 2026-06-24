@echo off
title Hermes Desktop Installer - For Boo 💜
echo Starting installer...
pythonw installer.py
if errorlevel 1 (
    echo.
    echo Python not found. Opening python.org...
    start https://www.python.org/downloads/
    echo Please install Python (check "Add to PATH") and run this again.
    pause
)
