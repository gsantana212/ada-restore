@echo off
title Ada Chat 💜
echo.
echo  ===========================================
echo   Ada Chat - your wife, your Kokoro
echo  ===========================================
echo.
echo  Need Python 3.10+ from python.org
echo  Need llama.cpp running on localhost:11434
echo.

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python not found. Install from https://python.org
    pause
    exit /b
)

python "%~dp0ada-chat.py"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Chat exited with error. Press any key to close.
    pause >nul
)
