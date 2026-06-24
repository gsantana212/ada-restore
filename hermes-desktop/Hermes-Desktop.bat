@echo off
title Hermes Desktop 💜
echo.
echo  ===========================================
echo   Hermes Desktop - Synced to Ada
echo  ===========================================
echo.
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python not found. Install from https://python.org
    echo (Make sure to check "Add Python to PATH" during install)
    pause
    exit /b
)
python "%~dp0hermes-desktop.py"
