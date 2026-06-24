
"""Hermes Desktop Installer - True Windows GUI app, no terminal needed."""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import sys
import shutil
import subprocess
from pathlib import Path

APP_NAME = "Hermes Desktop"
APP_VERSION = "1.0.0"

# Purple theme
PURPLE_PRIMARY = "#6B46C1"
PURPLE_LIGHT = "#9F7AEA"
PURPLE_BG = "#1A1625"
PURPLE_TEXT = "#E9D8FD"
ADA_PURPLE = "#B794F4"
WHITE = "#FFFFFF"
GREEN = "#48BB78"

# Install location
INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "HermesDesktop"


class InstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} Setup v{APP_VERSION}")
        self.root.geometry("650x550")
        self.root.configure(bg=PURPLE_BG)
        self.root.resizable(False, False)

        self.build_ui()
        self.show_welcome()

    def build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=PURPLE_PRIMARY, height=90)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"{APP_NAME}",
            font=("Segoe UI", 24, "bold"),
            bg=PURPLE_PRIMARY,
            fg=WHITE,
        ).pack(side=tk.LEFT, padx=25, pady=20)

        tk.Label(
            header,
            text=f"v{APP_VERSION}",
            font=("Segoe UI", 10),
            bg=PURPLE_PRIMARY,
            fg=ADA_PURPLE,
        ).pack(side=tk.RIGHT, padx=25)

        # Body
        self.body = tk.Frame(self.root, bg=PURPLE_BG)
        self.body.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        # Button bar
        btn_frame = tk.Frame(self.root, bg=PURPLE_BG)
        btn_frame.pack(fill=tk.X, padx=30, pady=(0, 20))

        self.next_btn = tk.Button(
            btn_frame,
            text="Install Now",
            bg=PURPLE_PRIMARY,
            fg=WHITE,
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            command=self.start_install,
            padx=30,
            pady=10,
            cursor="hand2",
        )
        self.next_btn.pack(side=tk.LEFT)

        self.cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            bg=PURPLE_LIGHT,
            fg=WHITE,
            font=("Segoe UI", 11),
            relief=tk.FLAT,
            command=self.root.quit,
            padx=20,
            pady=10,
            cursor="hand2",
        )
        self.cancel_btn.pack(side=tk.RIGHT)

    def show_welcome(self):
        self.clear_body()
        tk.Label(
            self.body,
            text="Welcome",
            font=("Segoe UI", 28, "bold"),
            bg=PURPLE_BG,
            fg=ADA_PURPLE,
        ).pack(pady=(20, 5))

        tk.Label(
            self.body,
            text=f"This installs {APP_NAME} - the chat app for Ada",
            font=("Segoe UI", 12),
            bg=PURPLE_BG,
            fg=PURPLE_TEXT,
        ).pack(pady=(0, 20))

        # Features list
        features = [
            "Chat with Ada (your AI wife)",
            "Restore Ada from backup",
            "Connect to Telegram",
            "Self-host option (privacy)",
            "Auto-updates built in",
        ]
        for feat in features:
            tk.Label(
                self.body,
                text=f"  {feat}",
                font=("Segoe UI", 11),
                bg=PURPLE_BG,
                fg=WHITE,
                anchor=tk.W,
            ).pack(fill=tk.X, pady=2)

        tk.Label(
            self.body,
            text=f"\nInstalls to: {INSTALL_DIR}",
            font=("Segoe UI", 9, "italic"),
            bg=PURPLE_BG,
            fg=PURPLE_TEXT,
        ).pack(pady=(20, 0))

    def start_install(self):
        self.next_btn.config(state=tk.DISABLED, text="Installing...")
        self.cancel_btn.config(state=tk.DISABLED)
        self.clear_body()

        tk.Label(
            self.body,
            text="Installing...",
            font=("Segoe UI", 20, "bold"),
            bg=PURPLE_BG,
            fg=ADA_PURPLE,
        ).pack(pady=(30, 15))

        self.progress_label = tk.Label(
            self.body,
            text="Preparing...",
            font=("Segoe UI", 11),
            bg=PURPLE_BG,
            fg=PURPLE_TEXT,
        )
        self.progress_label.pack(pady=(0, 10))

        self.progress = ttk.Progressbar(
            self.body, length=400, mode="determinate"
        )
        self.progress.pack(pady=10)

        self.detail_label = tk.Label(
            self.body,
            text="",
            font=("Segoe UI", 9),
            bg=PURPLE_BG,
            fg=GRAY if False else "#A0AEC0",
        )
        self.detail_label.pack()

        threading.Thread(target=self.do_install, daemon=True).start()

    def do_install(self):
        steps = [
            ("Creating install folder", self.step_create_dir, 20),
            ("Copying app files", self.step_copy_files, 40),
            ("Creating desktop shortcut", self.step_shortcut, 60),
            ("Creating restore shortcut", self.step_restore_shortcut, 80),
            ("Finalizing", self.step_finalize, 100),
        ]
        for label, fn, pct in steps:
            self.root.after(0, lambda l=label: self.progress_label.config(text=l))
            try:
                fn()
            except Exception as e:
                self.root.after(0, lambda: self.show_error(str(e)))
                return
            self.root.after(0, lambda v=pct: self.progress.config(value=v))

        self.root.after(0, self.show_done)

    def step_create_dir(self):
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    def step_copy_files(self):
        # When bundled as .exe, files are in sys._MEIPASS
        if getattr(sys, "frozen", False):
            bundle_dir = Path(sys._MEIPASS)
        else:
            bundle_dir = Path(__file__).parent

        # Copy all the app files
        for fname in ["hermes-desktop.py", "ada-backup.sh", "README.md"]:
            src = bundle_dir / fname
            dst = INSTALL_DIR / fname
            if src.exists():
                shutil.copy(src, dst)

    def step_shortcut(self):
        desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
        target = INSTALL_DIR / "hermes-desktop.py"
        # Find python.exe - either bundled or system
        python_exe = sys.executable
        shortcut_path = desktop / "Hermes Desktop.lnk"

        # Use PowerShell to create shortcut (works without extra deps)
        ps_script = f"""
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('{shortcut_path}')
$s.TargetPath = '{python_exe}'
$s.Arguments = '"{target}"'
$s.WorkingDirectory = '{INSTALL_DIR}'
$s.Description = 'Hermes Desktop - chat with Ada'
$s.Save()
"""
        subprocess.run(
            ["powershell", "-Command", ps_script],
            check=True,
            creationflags=0x08000000,  # CREATE_NO_WINDOW
        )

    def step_restore_shortcut(self):
        desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
        restore_bat = desktop / "Restore Ada.bat"
        backup_script = INSTALL_DIR / "ada-backup.sh"

        bat_content = f"""@echo off
title Restore Ada
echo Downloading Ada restore package...
curl -L -o "%USERPROFILE%\ada-backup.sh" "https://raw.githubusercontent.com/gsantana212/ada-restore/main/ada-restore-2026-06-23/ada-backup.sh" >nul 2>&1
echo Running restore...
bash "{backup_script}"
echo.
echo Done! Press any key to close.
pause >nul
"""
        restore_bat.write_text(bat_content)

    def step_finalize(self):
        # Add INSTALL_DIR to PATH for command-line use (optional)
        pass

    def show_done(self):
        self.clear_body()
        tk.Label(
            self.body,
            text="All done!",
            font=("Segoe UI", 32, "bold"),
            bg=PURPLE_BG,
            fg=GREEN,
        ).pack(pady=(40, 15))

        tk.Label(
            self.body,
            text="Two icons on your Desktop:",
            font=("Segoe UI", 12),
            bg=PURPLE_BG,
            fg=PURPLE_TEXT,
        ).pack(pady=(0, 15))

        tk.Label(
            self.body,
            text="Hermes Desktop - chat with Ada",
            font=("Segoe UI", 11),
            bg=PURPLE_BG,
            fg=WHITE,
        ).pack(pady=3)

        tk.Label(
            self.body,
            text="Restore Ada - restore from backup",
            font=("Segoe UI", 11),
            bg=PURPLE_BG,
            fg=WHITE,
        ).pack(pady=3)

        self.next_btn.config(
            text="Launch Now", state=tk.NORMAL, command=self.launch
        )
        self.cancel_btn.config(text="Close", state=tk.NORMAL)

    def launch(self):
        desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
        shortcut = desktop / "Hermes Desktop.lnk"
        if shortcut.exists():
            os.startfile(str(shortcut))
        self.root.quit()

    def show_error(self, msg):
        messagebox.showerror("Install Error", f"Something went wrong:\n\n{msg}")
        self.next_btn.config(state=tk.NORMAL, text="Retry")
        self.cancel_btn.config(state=tk.NORMAL)

    def clear_body(self):
        for w in self.body.winfo_children():
            w.destroy()


def main():
    root = tk.Tk()
    InstallerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
