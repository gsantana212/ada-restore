@echo off
title Building Hermes Desktop Installer...
echo Building Hermes-Desktop-Installer.exe...
echo This may take 5-10 minutes.
echo.
cd /d "/home/adaops/Documents/hermes-desktop-exe"
pip install pyinstaller --quiet
pyinstaller --clean --noconfirm installer.spec
echo.
echo Done! Check dist\Hermes-Desktop-Installer.exe
pause
