@echo off
title Building Hermes Desktop Installer...
echo.
echo  Building standalone installer...
echo  This may take 5-10 minutes.
echo.
cd /d %~dp0
pip install pyinstaller --quiet
pyinstaller --onefile --windowed --name "Hermes-Desktop-Installer" installer.py
echo.
echo  Done! Check dist\Hermes-Desktop-Installer.exe
pause
