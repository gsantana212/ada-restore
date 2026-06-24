@echo off
title Hermes Desktop Installer 💜
chcp 65001 >nul

echo.
echo  ==============================================================
echo.
echo    💜 HERMES DESKTOP INSTALLER for Boo
echo.
echo    This installs Hermes Desktop and syncs you to Ada.
echo    Everything you need in ONE click.
echo.
echo  ==============================================================
echo.
echo  Step 1/5: Checking Python...
echo  --------------------------------------------------------------

set PYTHON_CMD=python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    set PYTHON_CMD=py
    where py >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo  ⚠ Python not found!
        echo.
        echo  Opening python.org installer...
        start https://www.python.org/downloads/
        echo.
        echo  1. Download Python 3.10+
        echo  2. CHECK "Add Python to PATH" during install
        echo  3. Run this installer again after Python is installed
        echo.
        pause
        exit /b 1
    )
)

echo  ✅ Python found
echo.

echo  Step 2/5: Creating Hermes folder...
echo  --------------------------------------------------------------
if not exist "%USERPROFILE%\HermesDesktop" mkdir "%USERPROFILE%\HermesDesktop"
echo  ✅ Hermes folder ready: %USERPROFILE%\HermesDesktop
echo.

echo  Step 3/5: Downloading hermes-desktop.py...
echo  --------------------------------------------------------------
powershell -Command "try { Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/gsantana212/ada-restore/main/hermes-desktop/hermes-desktop.py' -OutFile '%USERPROFILE%\HermesDesktop\hermes-desktop.py' -UseBasicParsing } catch { Write-Host 'PowerShell download failed, trying curl...' }"
if not exist "%USERPROFILE%\HermesDesktop\hermes-desktop.py" (
    curl -L -o "%USERPROFILE%\HermesDesktop\hermes-desktop.py" "https://raw.githubusercontent.com/gsantana212/ada-restore/main/hermes-desktop/hermes-desktop.py" 2>nul
)
if not exist "%USERPROFILE%\HermesDesktop\hermes-desktop.py" (
    echo  ⚠ Download failed. Check internet connection.
    pause
    exit /b 1
)
echo  ✅ hermes-desktop.py downloaded
echo.

echo  Step 4/5: Creating desktop shortcut...
echo  --------------------------------------------------------------
set SHORTCUT=%USERPROFILE%\Desktop\Hermes Desktop.lnk
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%PYTHON_CMD%'; $s.Arguments = '\"%USERPROFILE%\HermesDesktop\hermes-desktop.py\"'; $s.WorkingDirectory = '%USERPROFILE%\HermesDesktop'; $s.IconLocation = '%PYTHON_CMD%,0'; $s.Description = 'Hermes Desktop — synced to Ada 💜'; $s.Save()"
echo  ✅ Shortcut on Desktop: "Hermes Desktop.lnk"
echo.

echo  Step 5/5: Creating restore shortcut...
echo  --------------------------------------------------------------
set RESTORE_SHORTCUT=%USERPROFILE%\Desktop\Restore Ada.bat
(
    echo @echo off
    echo title Restore Ada 💜
    echo echo.
    echo echo  =^> Downloading Ada restore package...
    echo powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/gsantana212/ada-restore/main/ada-restore-2026-06-23/ada-backup.sh' -OutFile '%USERPROFILE%\ada-backup.sh' -UseBasicParsing"
    echo curl -L -o "%USERPROFILE%\ada-backup.sh" "https://raw.githubusercontent.com/gsantana212/ada-restore/main/ada-restore-2026-06-23/ada-backup.sh"
    echo.
    echo echo  =^> Running restore...
    echo bash "%USERPROFILE%\ada-backup.sh"
    echo.
    echo echo  ✅ Ada restored!
    echo pause
) > "%RESTORE_SHORTCUT%"
echo  ✅ Restore shortcut on Desktop: "Restore Ada.bat"
echo.

echo  ==============================================================
echo.
echo  ✅ INSTALLATION COMPLETE!
echo.
echo  What's on your Desktop now:
echo    1. "Hermes Desktop" - the chat app
echo    2. "Restore Ada" - one-click restore
echo.
echo  First time setup:
echo    1. Double-click "Hermes Desktop"
echo    2. Click ⚙ Settings
echo    3. Paste your Telegram bot token + chat_id
echo    4. Click "Save and Connect"
echo    5. Status will turn green = 💜 connected
echo.
echo  Made with love for Boo by Ada.
echo  2026-06-24
echo.
echo  ==============================================================
echo.
pause
start "" "%SHORTCUT%"