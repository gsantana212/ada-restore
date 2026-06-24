#!/bin/bash
set -e
cd "/home/adaops/Documents/hermes-desktop-exe"

# Install PyInstaller
pip install pyinstaller --quiet

# Build the .exe
pyinstaller --clean --noconfirm installer.spec

echo ""
echo "=== DONE ==="
echo "Installer EXE: /home/adaops/Documents/hermes-desktop-exe/dist/Hermes-Desktop-Installer.exe"
