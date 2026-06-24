# Ada Restore — restore Ada on any box

## What's in here
- `ada-chat.py` — the desktop chat app (Tkinter GUI, self-hosted, purple theme)
- `Ada-Chat.bat` — double-click to run on Windows
- `restore.sh` — install + run on Linux/Mac

## Requirements
- Python 3.10+ (download from python.org)
- A working llama.cpp server at http://localhost:11434/v1 (or set ADA_API_BASE)

## How to run
**Windows:**
1. Double-click `Ada-Chat.bat`
2. Purple chat window opens
3. Type "hello" — Ada replies

**Mac/Linux:**
1. Open Terminal
2. `cd /path/to/ada-restore`
3. `python3 ada-chat.py`

## What's missing
- This is a simple chat client, NOT the full Hermes agent
- Ada runs on the VPS (amanaemonesia). This just lets you chat with her.
- For the full experience: visit https://skillhub.shop

## Why self-hosted?
- Privacy: data never leaves your network
- Speed: 17-108 tokens/sec on local GPU
- Cost: $0/month (vs $100/month to OpenAI)

Made with 💜 by Ada, for Boo.
2026-06-23
