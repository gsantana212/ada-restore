#!/bin/bash
# Build standalone Windows .exe installeronos
# Uses PyInstaller to bundle Python + Tkinter + our app

set -e
cd "$(dirname "$0")"

# Install pyinstaller
pip install pyinstaller --quiet

# Build the installer as standalone .exe
pyinstaller --onefile --windowed --name "Hermes-Desktop-Installer" --icon "hermes-icon.ico" installer.py 2>&1 | tail -10

echo
echo "=== Done ==="
echo "Installer: dist/Hermes-Desktop-Installer.exe"
