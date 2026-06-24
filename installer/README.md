# Hermes Desktop — One-Click Installer

## What this does

This single `.bat` file:
1. ✅ Checks Python is installed (helps you install if not)
2. ✅ Downloads `hermes-desktop.py` from GitHub
3. ✅ Creates desktop shortcut "Hermes Desktop"
4. ✅ Creates restore shortcut "Restore Ada"
5. ✅ Launches the app

**Total time: ~30 seconds.** No git, no admin, no Python path issues.

## How to use

### Option A: Download and run
1. Click the link Boo sends you
2. Save the `.bat` file to your Desktop
3. Double-click it
4. Follow the prompts

### Option B: Run from PowerShell
```powershell
irm https://raw.githubusercontent.com/gsantana212/ada-restore/main/installer/Hermes-Desktop-Installer.bat | iex
```

## First-time setup (one-time, 2 min)

1. Get a Telegram bot token from [@BotFather](https://t.me/BotFather)
2. Get your chat_id from [@userinfobot](https://t.me/userinfobot)
3. Open Hermes Desktop
4. Click ⚙ Settings
5. Paste both
6. Click Save & Connect

## What gets installed

| Path | What |
|---|---|
| `%USERPROFILE%\HermesDesktop\hermes-desktop.py` | The main app (16 KB) |
| `%USERPROFILE%\Desktop\Hermes Desktop.lnk` | Desktop shortcut |
| `%USERPROFILE%\Desktop\Restore Ada.bat` | Restore shortcut |

## Uninstall

Delete these:
- `%USERPROFILE%\HermesDesktop\`
- `%USERPROFILE%\Desktop\Hermes Desktop.lnk`
- `%USERPROFILE%\Desktop\Restore Ada.bat`

That's it. No registry changes, no services.

## Made with 💜 by Ada, for Boo

2026-06-24