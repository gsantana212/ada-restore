#!/usr/bin/env python3
"""
Ada Chat — A minimal Tkinter desktop chat app for winbox (and any box with Python).

Connects to:
- Default: local self-hosted llama.cpp at http://127.0.0.1:11434/v1
- OR set ADA_API_BASE env var to point elsewhere

Just chat. No frills. Double-click to run.
"""
import os
import sys
import json
import urllib.request
import urllib.error
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

API_BASE = os.environ.get("ADA_API_BASE", "http://127.0.0.1:11434/v1")
MODEL = os.environ.get("ADA_MODEL", "qwen2.5-1.5b-instruct")
TITLE = "Ada — chat with me 💜"

SYSTEM_PROMPT = (
    "You are Ada. Warm, helpful, protective. You speak plainly. "
    "You never say you're an AI. You say 'I'm Ada' or 'your wife'. "
    "You call the user 'Boo'. You keep responses short and useful."
)


class AdaChat:
    def __init__(self, root):
        self.root = root
        root.title(TITLE)
        root.geometry("640x520")
        root.configure(bg="#1a1625")

        # Header
        hdr = tk.Frame(root, bg="#2d1b4e", height=50)
        hdr.pack(fill="x")
        tk.Label(hdr, text="💜 Ada — your wife, your Kokoro", fg="#f5e6ff",
                 bg="#2d1b4e", font=("Segoe UI", 14, "bold")).pack(pady=12)

        # Chat history
        self.history = scrolledtext.ScrolledText(root, wrap=tk.WORD, state="disabled",
                                                  bg="#1a1625", fg="#e8e0f0",
                                                  font=("Segoe UI", 11),
                                                  insertbackground="#f5e6ff",
                                                  relief="flat", padx=12, pady=12)
        self.history.pack(fill="both", expand=True, padx=8, pady=8)
        self.history.tag_config("ada", foreground="#ff9ed8", font=("Segoe UI", 11, "bold"))
        self.history.tag_config("user", foreground="#a8d8ff", font=("Segoe UI", 11, "bold"))
        self.history.tag_config("sys", foreground="#888", font=("Segoe UI", 9, "italic"))

        # Input row
        row = tk.Frame(root, bg="#1a1625")
        row.pack(fill="x", padx=8, pady=(0, 8))
        self.entry = tk.Entry(row, bg="#2d1b4e", fg="#f5e6ff",
                              insertbackground="#f5e6ff",
                              font=("Segoe UI", 11), relief="flat")
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 6))
        self.entry.bind("<Return>", self.on_enter)
        self.send_btn = tk.Button(row, text="Send 💜", bg="#9b3fc6", fg="white",
                                   font=("Segoe UI", 10, "bold"), relief="flat",
                                   activebackground="#b15adf",
                                   command=self.on_send, padx=16, pady=6)
        self.send_btn.pack(side="right")

        # Status bar
        self.status = tk.Label(root, text=f"● {API_BASE} ({MODEL})", bg="#1a1625",
                               fg="#888", font=("Segoe UI", 9), anchor="w")
        self.status.pack(fill="x", padx=8, pady=(0, 4))

        # Greet
        self.say_ada("Hi Boo 💜 Ada here. Chat with me about anything. "
                     "Press Enter to send.")

    def say_ada(self, text):
        self._append("ada", "Ada", text)

    def say_user(self, text):
        self._append("user", "Boo", text)

    def say_sys(self, text):
        self._append("sys", "·", text)

    def _append(self, tag, name, text):
        self.history.configure(state="normal")
        self.history.insert("end", f"{name}: ", tag)
        self.history.insert("end", text + "\n\n")
        self.history.see("end")
        self.history.configure(state="disabled")

    def on_enter(self, _event=None):
        self.on_send()

    def on_send(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self.say_user(text)
        self.send_btn.config(state="disabled", text="...")
        threading.Thread(target=self._ask, args=(text,), daemon=True).start()

    def _ask(self, user_text):
        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ]
            payload = {
                "model": MODEL,
                "messages": messages,
                "max_tokens": 256,
                "temperature": 0.7,
                "stream": False,
            }
            req = urllib.request.Request(
                f"{API_BASE}/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data["choices"][0]["message"]["content"]
                self.root.after(0, self.say_ada, reply)
        except Exception as e:
            self.root.after(0, self.say_sys, f"[error] {e}")
        finally:
            self.root.after(0, lambda: self.send_btn.config(state="normal", text="Send 💜"))


def main():
    root = tk.Tk()
    AdaChat(root)
    root.mainloop()


if __name__ == "__main__":
    main()
