# AGENTS.md — gsantana212/ada-restore

> Operating contract for any AI agent opening this repo. Read first.

## What this repo is

**The Ada restore kit.** Ships everything needed to bring Ada (Hermes Agent) back
from the dead on any box:

1. A Windows EXE installer
2. The Hermes Desktop Python source
3. The Linux ELF build (historical)
4. The build tools to compile the EXE
5. The 2026-06-23 backup snapshot (the canonical "Ada died, restore this")
6. CI workflows that build the installer on tag push

Per `README.md`:

> Restore Ada chat on any box. This repo ships: the Windows EXE installer, the
> Hermes Desktop Python source, the Linux ELF build output, the build tools, the
> 2026-06-23 backup snapshot, and CI.

## Repo layout (verified 2026-08-31)

| Path | Role | Notes |
|---|---|---|
| `installer/` | Windows installer entry | `Hermes-Desktop-Installer.bat` (4.3 KB) + `README.md` |
| `hermes-desktop/` | Python source | The cross-platform launcher |
| `hermes-desktop-exe/` | Linux ELF build | **Historical artifact only** — do not modify |
| `hermes-desktop-builder/` | Build tools | Compiles the Windows installer |
| `ada-restore-2026-06-23/` | Backup snapshot | Run `bash restore.sh` inside to rehydrate `~/.hermes/` |
| `.github/workflows/` | CI | Builds the installer on `v*` tag push |
| `LICENSE`, `SECURITY.md`, `README.md` | Standard repo glue | — |

## What an agent here can do safely

- **Edit the Python source in `hermes-desktop/`** — the canonical desktop launcher.
- **Update `installer/Hermes-Desktop-Installer.bat`** when the install flow changes.
- **Add or fix CI in `.github/workflows/`** — current pipeline builds the EXE.
- **Document changes in `ada-restore-2026-06-23/STATE.md` or equivalent** if you
  modify the backup snapshot.

## What an agent must NOT do here

- **Do not modify `hermes-desktop-exe/`** — historical artifact, preserved for
  provenance. If you need a new build, run the builder; don't hand-edit.
- **Do not commit credentials** — the restore snapshot contains a tarball that may
  have `~/.hermes/secrets/` references; **scrub `wallets.json`, API keys, and
  Lemonsqueezy/Stripe webhooks** before pushing. The canonical home for secrets is
  `/root/.hermes/secrets/` on the operator's box, never the repo.
- **Do not skip `bash restore.sh` smoke tests** after touching
  `ada-restore-2026-06-23/`.

## Quick start (developer)

```bash
git clone https://github.com/gsantana212/ada-restore
cd ada-restore/hermes-desktop
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python hermes-desktop.py
```

## Quick start (Windows end-user)

Download the latest release: https://github.com/gsantana212/ada-restore/releases/latest
Run the EXE. It installs Ada + the desktop launcher.

## Conventions

- Installer filename: `Hermes-Desktop-Installer.bat` (don't rename; release pipeline
  depends on it).
- Backup snapshots live in `ada-restore-<YYYY-MM-DD>/` directories. **Never overwrite
  an existing snapshot dir** — create a new dated one.
- CI: tag with `vX.Y.Z` to trigger a release build.

## Status snapshot (2026-08-31)

- Last commit on default branch: `913011a fix: close gaps surfaced in 2026-08-28 audit`
- Canonical mirror (local): `/root/work/github-fixes/ada-restore/`
- Duplicate mirrors (will be archived 2026-08-31): `/root/ada-restore/`,
  `/root/ada-mesh-private-restored/projects/` (none here for ada-restore),
  `/root/.hermes/research/manual-patches/ada-restore-patches/`

## Provenance

Generated 2026-08-31 by Hermes subagent during Week-1 consolidation
(`/root/.hermes/research/synthesis-2026-08-31.md` §2 action #2 + §10.1 action #5).
Cited content is from on-disk `README.md`, `ls`, and `git log` at that time.