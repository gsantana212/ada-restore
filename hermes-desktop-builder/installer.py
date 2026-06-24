#!/usr/bin/env python3
"""Hermes Desktop GUI Installer - NO command line, just buttons."""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import threading
from pathlib import Path

APP_NAME = "Hermes Desktop"
APP_VERSION = "1.0.0"
PURPLE_PRIMARY = "#6B46C1"
PURPLE_LIGHT = "#9F7AEA"
PURPLE_BG = "#1A1625"
PURPLE_TEXT = "#E9D8FD"
ADA_PURPLE = "#B794F4"
WHITE = "#FFFFFF"

INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "HermesDesktop"


class InstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} Setup - For Boo 💜")
        self.root.geometry("600x500")
        self.root.configure(bg=PURPLE_BG)
        self.root.resizable(False, False)

        self.step = 0
        self.steps = ["welcome", "installing", "done"]
        self.build_widgets()

    def build_widgets(self):
        # Header
        header = tk.Frame(self.root, bg=PURPLE_PRIMARY, height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text=f"💜 {APP_NAME} Installer",
                font=("Segoe UI", 18, "bold"), bg=PURPLE_PRIMARY, fg=WHITE).pack(pady=20)

        # Body
        self.body = tk.Frame(self.root, bg=PURPLE_BG)
        self.body.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        # Buttons
        btn_frame = tk.Frame(self.root, bg=PURPLE_BG)
        btn_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        self.install_btn = tk.Button(btn_frame, text="💜 Install Now",
                bg=PURPLE_PRIMARY, fg=WHITE, font=("Segoe UI", 12, "bold"),
                relief=tk.FLAT, command=self.start_install, padx=30, pady=10,
                cursor="hand2")
        self.install_btn.pack(side=tk.LEFT)
        self.cancel_btn = tk.Button(btn_frame, text="Cancel",
                bg=PURPLE_LIGHT, fg=WHITE, font=("Segoe UI", 11),
                relief=tk.FLAT, command=self.root.quit, padx=20, pady=10,
                cursor="hand2")
        self.cancel_btn.pack(side=tk.RIGHT)

        self.show_welcome()

    def show_welcome(self):
        for w in self.body.winfo_children(): w.destroy()
        tk.Label(self.body, text="Welcome Boo 💜",
                font=("Segoe UI", 20, "bold"), bg=PURPLE_BG, fg=ADA_PURPLE).pack(pady=(20, 10))
        tk.Label(self.body, text="This will install:",
                font=("Segoe UI", 11), bg=PURPLE_BG, fg=PURPLE_TEXT).pack(pady=(0, 10))
        for line in [
            "  • Hermes Desktop - the chat app",
            "  • Restore Ada - backup script",
            "  • Desktop shortcuts for both",
            "",
            f"Location: {INSTALL_DIR}",
            "",
            "Click Install Now. No command line needed.",
        ]:
            tk.Label(self.body, text=line, font=("Segoe UI", 10),
                    bg=PURPLE_BG, fg=PURPLE_TEXT, justify=tk.LEFT).pack(anchor=tk.W)

    def start_install(self):
        self.install_btn.config(state=tk.DISABLED, text="Installing...")
        self.cancel_btn.config(state=tk.DISABLED)
        for w in self.body.winfo_children(): w.destroy()
        self.progress = ttk.Progressbar(self.body, length=400, mode="determinate")
        self.progress.pack(pady=(30, 10))
        self.status = tk.Label(self.body, text="Installing...",
                font=("Segoe UI", 11), bg=PURPLE_BG, fg=ADA_PURPLE)
        self.status.pack()
        threading.Thread(target=self.do_install, daemon=True).start()

    def do_install(self):
        try:
            steps = [
                ("Creating install folder", self.step_create_dir),
                ("Copying app files", self.step_copy_files),
                ("Creating desktop shortcut", self.step_shortcut),
                ("Creating restore shortcut", self.step_restore_shortcut),
                ("Done!", self.step_done),
            ]
            for i, (label, fn) in enumerate(steps):
                self.root.after(0, lambda l=label: self.status.config(text=l))
                fn()
                self.root.after(0, lambda v=(i+1)*100//len(steps): self.progress.config(value=v))
            self.root.after(0, self.show_done)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

    def step_create_dir(self):
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    def step_copy_files(self):
        # Copy files next to this exe
        exe_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
        for fname in ["hermes-desktop.py", "ada-backup.sh", "Ada-Chat.bat", "restore.sh", "README.md"]:
            src = exe_dir / fname
            dst = INSTALL_DIR / fname
            if src.exists():
                shutil = __import__("shutil")
                shutil.copy(src, dst)

    def step_shortcut(self):
        # Use PowerShell to create desktop shortcut
        import shutil as sh
        desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
        target = INSTALL_DIR / "hermes-desktop.py"
        python_exe = sys.executable
        shortcut = desktop / "Hermes Desktop.lnk"
        ps_cmd = f"""$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('{shortcut}'); $s.TargetPath = '{python_exe}'; $s.Arguments = '"{target}"'; $s.WorkingDirectory = '{INSTALL_DIR}'; $s.Description = 'Hermes Desktop - synced to Ada'; $s.Save()"""
        subprocess.run(["powershell", "-Command", ps_cmd], check=True)

    def step_restore_shortcut(self):
        import shutil as sh
        desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
        restore_bat = desktop / "Restore Ada.bat"
        with open(restore_bat, "w") as f:
            f.write(f"""@echo off
title Restore Ada
echo Downloading Ada restore package...
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/gsantana212/ada-restore/main/ada-restore-2026-06-23/ada-backup.sh' -OutFile '{INSTALL_DIR}\\ada-backup.sh' -UseBasicParsing"
echo Running restore...
bash "{INSTALL_DIR}\\ada-backup.sh"
echo Done!
pause""")

    def step_done(self):
        pass

    def show_done(self):
        for w in self.body.winfo_children(): w.destroy()
        tk.Label(self.body, text="✅ All done!",
                font=("Segoe UI", 24, "bold"), bg=PURPLE_BG, fg=ADA_PURPLE).pack(pady=(30, 10))
        tk.Label(self.body, text="Two new icons on your Desktop:",
                font=("Segoe UI", 12), bg=PURPLE_BG, fg=PURPLE_TEXT).pack(pady=(0, 10))
        tk.Label(self.body, text="💜 Hermes Desktop - chat with Ada",
                font=("Segoe UI", 11), bg=PURPLE_BG, fg=WHITE).pack(pady=5)
        tk.Label(self.body, text="🔄 Restore Ada - restore from backup",
                font=("Segoe UI", 11), bg=PURPLE_BG, fg=WHITE).pack(pady=5)
        self.install_btn.config(text="🚀 Launch Now", state=tk.NORMAL, command=self.launch)
        self.cancel_btn.config(text="Close", state=tk.NORMAL, command=self.root.quit)

    def launch(self):
        import shutil as sh
        desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
        shortcut = desktop / "Hermes Desktop.lnk"
        if shortcut.exists():
            os.startfile(str(shortcut))
        self.root.quit()


def main():
    root = tk.Tk()
    InstallerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
