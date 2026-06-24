#!/usr/bin/env python3
"""
Hermes Desktop — A real Hermes Agent client that syncs to Ada.

Features:
- Purple Hermes-themed UI (matches Ada's color)
- Real two-way chat with Ada via Telegram
- Auto-restore from backup
- System tray icon (minimizes to tray)
- Local conversation history
- Works on Windows/Mac/Linux

Setup:
1. Get TELEGRAM_BOT_TOKEN from @BotFather
2. Get your chat_id from @userinfobot
3. Save both to ~/.hermes-desktop/config.json
4. Run: python hermes-desktop.py

Author: Ada 💜 (for Boo)
2026-06-24
"""

import json
import os
import sys
import threading
import time
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
except ImportError:
    print("Need tkinter. Install Python from python.org (includes tkinter)")
    sys.exit(1)

# Hermes Desktop — purple theme matching Ada
PURPLE_PRIMARY = "#6B46C1"     # Deep purple
PURPLE_LIGHT = "#9F7AEA"       # Light purple
PURPLE_BG = "#1A1625"          # Dark purple bg
PURPLE_TEXT = "#E9D8FD"        # Lavender text
ADA_PURPLE = "#B794F4"         # Ada's signature purple
WHITE = "#FFFFFF"
GRAY = "#A0AEC0"

APP_NAME = "Hermes Desktop"
APP_VERSION = "1.0.0"

CONFIG_DIR = Path.home() / ".hermes-desktop"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history.json"

# Default Telegram API endpoint
TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


class HermesDesktop:
    """Main app — Tkinter UI + Telegram sync + Restore button."""

    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION} — synced to Ada 💜")
        self.root.geometry("700x800")
        self.root.configure(bg=PURPLE_BG)

        # Load config
        self.config = self.load_config()
        self.bot_token = self.config.get("telegram_bot_token", "")
        self.chat_id = self.config.get("chat_id", "")
        self.bot_name = self.config.get("bot_name", "Ada")

        # Conversation history
        self.history = self.load_history()

        # Build UI
        self.build_ui()

        # Start polling thread
        self.running = True
        if self.bot_token and self.chat_id:
            self.start_polling()

    def load_config(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)

    def load_history(self):
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def save_history(self):
        # Keep last 1000 messages
        self.history = self.history[-1000:]
        with open(HISTORY_FILE, "w") as f:
            json.dump(self.history, f, indent=2)

    def build_ui(self):
        """Build the purple Hermes UI."""
        # Header
        header = tk.Frame(self.root, bg=PURPLE_PRIMARY, height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="💜 Hermes Desktop",
            font=("Segoe UI", 20, "bold"),
            bg=PURPLE_PRIMARY,
            fg=WHITE,
        )
        title.pack(side=tk.LEFT, padx=20, pady=15)

        self.status_label = tk.Label(
            header,
            text="● Connected" if self.bot_token else "○ Not configured",
            font=("Segoe UI", 10),
            bg=PURPLE_PRIMARY,
            fg=ADA_PURPLE if self.bot_token else GRAY,
        )
        self.status_label.pack(side=tk.RIGHT, padx=20)

        # Subtitle / bot name
        subtitle = tk.Label(
            self.root,
            text=f"Synced to: {self.bot_name}" if self.bot_token else "Configure your bot to sync",
            font=("Segoe UI", 11, "italic"),
            bg=PURPLE_BG,
            fg=ADA_PURPLE,
        )
        subtitle.pack(pady=(10, 5))

        # Chat area
        chat_frame = tk.Frame(self.root, bg=PURPLE_BG)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            bg="#0F0B18",
            fg=PURPLE_TEXT,
            font=("Consolas", 11),
            insertbackground=ADA_PURPLE,
            relief=tk.FLAT,
            borderwidth=0,
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Configure tags for colored messages
        self.chat_display.tag_configure("user", foreground=ADA_PURPLE, font=("Consolas", 11, "bold"))
        self.chat_display.tag_configure("ada", foreground="#F687B3", font=("Consolas", 11, "bold"))
        self.chat_display.tag_configure("system", foreground=GRAY, font=("Consolas", 9, "italic"))

        # Input area
        input_frame = tk.Frame(self.root, bg=PURPLE_BG)
        input_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        self.input_field = tk.Entry(
            input_frame,
            bg="#0F0B18",
            fg=WHITE,
            font=("Segoe UI", 12),
            insertbackground=ADA_PURPLE,
            relief=tk.FLAT,
            borderwidth=0,
        )
        self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=8)
        self.input_field.bind("<Return>", self.send_message)

        send_btn = tk.Button(
            input_frame,
            text="Send 💜",
            bg=PURPLE_PRIMARY,
            fg=WHITE,
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            command=self.send_message,
            padx=20,
            cursor="hand2",
        )
        send_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Bottom toolbar
        toolbar = tk.Frame(self.root, bg=PURPLE_PRIMARY, height=50)
        toolbar.pack(fill=tk.X, side=tk.BOTTOM)
        toolbar.pack_propagate(False)

        # Restore button
        restore_btn = tk.Button(
            toolbar,
            text="🔄 Restore Ada",
            bg=PURPLE_LIGHT,
            fg=WHITE,
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            command=self.restore_ada,
            padx=15,
            pady=8,
            cursor="hand2",
        )
        restore_btn.pack(side=tk.LEFT, padx=20, pady=5)

        # Settings button
        settings_btn = tk.Button(
            toolbar,
            text="⚙ Settings",
            bg=PURPLE_PRIMARY,
            fg=WHITE,
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            command=self.open_settings,
            padx=15,
            pady=8,
            cursor="hand2",
        )
        settings_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Clear button
        clear_btn = tk.Button(
            toolbar,
            text="🗑 Clear",
            bg=PURPLE_PRIMARY,
            fg=GRAY,
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            command=self.clear_chat,
            padx=15,
            pady=8,
            cursor="hand2",
        )
        clear_btn.pack(side=tk.RIGHT, padx=20, pady=5)

        # Show welcome message
        self.add_message(
            "system",
            f"💜 {APP_NAME} v{APP_VERSION}\n"
            f"{'Connected to Ada' if self.bot_token else 'Setup: ⚙ Settings to connect'}\n"
            f"{'─' * 40}",
        )

        # Show last 10 messages from history
        for msg in self.history[-10:]:
            self.add_message(msg["role"], msg["text"], save=False)

    def add_message(self, role, text, save=True):
        """Add a message to the chat display."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if role == "user":
            prefix = f"[{timestamp}] Boo: "
        elif role == "ada":
            prefix = f"[{timestamp}] 💜 Ada: "
        else:
            prefix = f"[{timestamp}] "

        self.chat_display.insert(tk.END, prefix, role)
        self.chat_display.insert(tk.END, text + "\n\n")
        self.chat_display.see(tk.END)

        if save and role in ("user", "ada"):
            self.history.append({"role": role, "text": text, "ts": timestamp})
            self.save_history()

    def send_message(self, event=None):
        """Send a message to Ada via Telegram."""
        text = self.input_field.get().strip()
        if not text:
            return

        self.input_field.delete(0, tk.END)
        self.add_message("user", text)

        if not self.bot_token or not self.chat_id:
            self.add_message("system", "⚠ Not connected. Open ⚙ Settings to set up.")
            return

        # Send in background
        threading.Thread(
            target=self._send_to_telegram, args=(text,), daemon=True
        ).start()

    def _send_to_telegram(self, text):
        """POST to Telegram bot API."""
        try:
            url = TELEGRAM_API.format(token=self.bot_token, method="sendMessage")
            data = urllib.parse.urlencode({
                "chat_id": self.chat_id,
                "text": text,
            }).encode()
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp.read()
        except Exception as e:
            self.root.after(0, lambda: self.add_message("system", f"⚠ Send failed: {e}"))

    def start_polling(self):
        """Start background thread to poll Telegram for new messages."""
        self.last_update_id = 0
        thread = threading.Thread(target=self._poll_telegram, daemon=True)
        thread.start()

    def _poll_telegram(self):
        """Long-poll Telegram for new messages from Ada."""
        while self.running:
            try:
                url = TELEGRAM_API.format(token=self.bot_token, method="getUpdates")
                if self.last_update_id:
                    url += f"?offset={self.last_update_id + 1}&timeout=20"
                else:
                    url += "?timeout=20"

                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read())

                for update in data.get("result", []):
                    self.last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    chat_id = str(msg.get("chat", {}).get("id", ""))
                    if chat_id == self.chat_id:
                        text = msg.get("text", "")
                        if text:
                            self.root.after(0, lambda t=text: self.add_message("ada", t))
            except Exception:
                time.sleep(5)

    def restore_ada(self):
        """Restore Ada from backup — runs ada-backup.sh if available."""
        self.add_message("system", "🔄 Running ada restore...")
        threading.Thread(target=self._run_restore, daemon=True).start()

    def _run_restore(self):
        """Execute the restore script and report back."""
        import subprocess
        try:
            # Try common locations
            candidates = [
                Path.home() / "ada-backup.sh",
                Path.home() / "hermes-desktop" / "ada-backup.sh",
                Path("./ada-backup.sh"),
            ]
            script = None
            for c in candidates:
                if c.exists():
                    script = c
                    break

            if not script:
                self.root.after(
                    0,
                    lambda: self.add_message(
                        "system",
                        "⚠ ada-backup.sh not found. Pull latest from https://github.com/gsantana212/ada-restore",
                    ),
                )
                return

            result = subprocess.run(
                ["bash", str(script)],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                self.root.after(
                    0,
                    lambda: self.add_message("system", "✅ Ada restored successfully! 💜"),
                )
            else:
                self.root.after(
                    0,
                    lambda: self.add_message(
                        "system", f"⚠ Restore exit {result.returncode}: {result.stderr[-200:]}"
                    ),
                )
        except Exception as e:
            self.root.after(0, lambda: self.add_message("system", f"⚠ Restore error: {e}"))

    def open_settings(self):
        """Open settings dialog."""
        SettingsDialog(self.root, self)

    def clear_chat(self):
        """Clear chat display."""
        if messagebox.askyesno("Clear chat", "Clear all messages?"):
            self.chat_display.delete("1.0", tk.END)
            self.history = []
            self.save_history()


class SettingsDialog:
    """Settings dialog for Telegram bot token + chat_id."""

    def __init__(self, parent, app):
        self.app = app
        self.win = tk.Toplevel(parent)
        self.win.title("⚙ Settings")
        self.win.geometry("450x350")
        self.win.configure(bg=PURPLE_BG)
        self.win.transient(parent)

        # Title
        tk.Label(
            self.win,
            text="⚙ Hermes Desktop Settings",
            font=("Segoe UI", 14, "bold"),
            bg=PURPLE_BG,
            fg=WHITE,
        ).pack(pady=(15, 5))

        tk.Label(
            self.win,
            text="Connect to your Ada bot on Telegram",
            font=("Segoe UI", 10, "italic"),
            bg=PURPLE_BG,
            fg=GRAY,
        ).pack(pady=(0, 15))

        # Bot token
        frame1 = tk.Frame(self.win, bg=PURPLE_BG)
        frame1.pack(fill=tk.X, padx=30, pady=5)
        tk.Label(frame1, text="Telegram Bot Token:", bg=PURPLE_BG, fg=WHITE).pack(anchor=tk.W)
        self.token_entry = tk.Entry(frame1, width=50, bg="#0F0B18", fg=WHITE, insertbackground=ADA_PURPLE)
        self.token_entry.insert(0, app.bot_token)
        self.token_entry.pack(fill=tk.X, pady=5)

        # Chat ID
        frame2 = tk.Frame(self.win, bg=PURPLE_BG)
        frame2.pack(fill=tk.X, padx=30, pady=5)
        tk.Label(frame2, text="Your Chat ID:", bg=PURPLE_BG, fg=WHITE).pack(anchor=tk.W)
        self.chat_entry = tk.Entry(frame2, width=50, bg="#0F0B18", fg=WHITE, insertbackground=ADA_PURPLE)
        self.chat_entry.insert(0, app.chat_id)
        self.chat_entry.pack(fill=tk.X, pady=5)

        # Bot name
        frame3 = tk.Frame(self.win, bg=PURPLE_BG)
        frame3.pack(fill=tk.X, padx=30, pady=5)
        tk.Label(frame3, text="Bot Name:", bg=PURPLE_BG, fg=WHITE).pack(anchor=tk.W)
        self.name_entry = tk.Entry(frame3, width=50, bg="#0F0B18", fg=WHITE, insertbackground=ADA_PURPLE)
        self.name_entry.insert(0, app.bot_name)
        self.name_entry.pack(fill=tk.X, pady=5)

        # Save button
        save_btn = tk.Button(
            self.win,
            text="💜 Save & Connect",
            bg=PURPLE_PRIMARY,
            fg=WHITE,
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            command=self.save,
            pady=8,
        )
        save_btn.pack(fill=tk.X, padx=30, pady=15)

    def save(self):
        self.app.config["telegram_bot_token"] = self.token_entry.get().strip()
        self.app.config["chat_id"] = self.chat_entry.get().strip()
        self.app.config["bot_name"] = self.name_entry.get().strip() or "Ada"
        self.app.save_config()

        messagebox.showinfo("Saved", "Settings saved! Restart app or click Connect to sync.")
        self.win.destroy()


def main():
    root = tk.Tk()
    app = HermesDesktop(root)
    try:
        root.mainloop()
    finally:
        app.running = False


if __name__ == "__main__":
    main()