# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| v1.0.0  | :white_check_mark: |

## Reporting a Vulnerability

Email **gsantana212@users.noreply.github.com** with:
- A description of the issue
- Reproduction steps (or a sample input that triggered it)
- Expected vs actual behavior

Response SLA: 48 hours. We will follow up with a remediation timeline.

## Scope

This repo publishes the Hermes Desktop installer (PyInstaller EXE) and the
source for the desktop chat client. The actual Ada runtime is in
[gsantana212/ada-containers-backup](https://github.com/gsantana212/ada-containers-backup)
and the daily deep-dive skill lives at /root/.hermes on each deployment host.

If you find a security issue in the *chat client* itself (not the installer),
that's where the report belongs.