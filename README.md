# ada-restore

**Restore Ada chat on any box.** This repo ships:

1. The Windows EXE installer (`installer/` — built by `.github/workflows/build-installer.yml`)
2. The Hermes Desktop Python source (`hermes-desktop/`)
3. The Linux ELF build output (`hermes-desktop-exe/`) — *historical artifact only*
4. The build tools (`hermes-desktop-builder/`)
5. The original 2026-06-23 backup snapshot (`ada-restore-2026-06-23/`)
6. CI (`.github/workflows/`)

## Quick start (Windows end-user)

Download the latest release: [Hermes-Desktop-Installer.exe](https://github.com/gsantana212/ada-restore/releases/latest)
Run the EXE. It installs Ada + the desktop launcher.

## Quick start (developer)

```bash
# clone and set up the Python source
git clone https://github.com/gsantana212/ada-restore
cd ada-restore/hermes-desktop
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python hermes-desktop.py
```

## Restore Ada from the backup snapshot

```bash
# If your VPS died and you need to restore from the original 2026-06-23 backup:
cd ada-restore-2026-06-23
bash restore.sh
```

This rehydrates Ada's `~/.hermes/` directory from the dated tarball.

## Build the Windows installer (from source)

The CI in `.github/workflows/build-installer.yml` builds on every `v*` tag push:
1. Pin `pyinstaller==6.10.0` (or check `pip index versions pyinstaller` for current)
2. `git tag v1.0.1 && git push --tags`
3. Wait for green Actions run
4. Download from the GitHub Actions artifacts, or promote to a Release

## License

MIT — see `LICENSE`. Copyright (c) 2026 Gio Santacruz / Ada.

## Repository structure

| Dir | Purpose | Audience |
|---|---|---|
| `installer/` | The PyInstaller spec + build context for the Windows EXE | End-user (binary), dev (source) |
| `hermes-desktop/` | Tkinter chat client source | Dev |
| `hermes-desktop-exe/` | Linux build output + specs | Dev (artifact only) |
| `hermes-desktop-builder/` | Dev tools (clean, package, hash) | Dev |
| `ada-restore-2026-06-23/` | Original 2026-06-23 backup snapshot + restore script | Ops (disaster recovery) |
| `.github/` | CI (Windows installer build) | Dev |

## Notes

- The `hermes-desktop-exe/Hermes-Desktop-Installer.linux` binary is historical and **will be removed in a future history-scrub** (see issue #N). Don't rely on it.
- For questions, file an issue or email gsantana212@.