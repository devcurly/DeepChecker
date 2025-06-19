import os
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict
import winreg
import requests
import sys
import time
import subprocess
import shutil
import webbrowser
from ttkbootstrap import Style
from ttkbootstrap.constants import *

# ====== CONFIG ======
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/devcurly/DeepChecker/main/"
VERSION_FILE = "version.txt"
LOCAL_VERSION = "BETA 0.d"
DISCORD_SERVER_URL = "https://discord.gg/a4b2X8sg9r"
ICON_PATH = "deepchecker.ico"
SCRIPT_NAME = "deepchecker.py"
SHORTCUT_NAME = "DeepChecker.lnk"

# ====== SCANNER KEYWORDS ======
CHECK_KEYWORDS = [
    "Fly", "Speed", "Platform", "LongArm", "TagAura", "Ghost", "WallClimb", "AutoTag",
    "PlayerMovement", "PlayerController", "OnUpdate", "FixedUpdate", "Teleport",
    "TaggerESP", "MaterialChanger", "Invisible", "GodMode", "Noclip", "AntiBan",
    "HarmonyPatch", "MonkeyPatch", "Update", "PlayerDistance", "Hand", "ArmLength"
]

# ====== UTILS ======
def get_steamvr_settings_path():
    return os.path.expandvars(r"%LOCALAPPDATA%\\openvr\\steamvr.vrsettings")

def read_world_scale():
    try:
        with open(get_steamvr_settings_path(), "r") as f:
            data = json.load(f)
        return data.get("steamvr", {}).get("worldScale", 1.0)
    except:
        return None

def find_gorilla_tag_path():
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\Valve\\Steam") as key:
            steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
    except:
        steam_path = os.path.expandvars(r"%PROGRAMFILES(X86)%\\Steam")
    path = os.path.join(steam_path, "steamapps", "common", "Gorilla Tag", "BepInEx", "plugins")
    return path if os.path.isdir(path) else None

def read_dll_text(path):
    try:
        with open(path, 'rb') as f:
            return f.read().decode('utf-8', errors='ignore').lower()
    except:
        return ""

def scan_dll_for_keywords(dll_path):
    content = read_dll_text(dll_path)
    hits = defaultdict(int)
    for keyword in CHECK_KEYWORDS:
        count = content.count(keyword.lower())
        if count > 0:
            hits[keyword] = count
    return hits

def analyze_all_dlls(folder):
    results = []
    for file in os.listdir(folder):
        if not file.endswith(".dll"):
            continue
        path = os.path.join(folder, file)
        hits = scan_dll_for_keywords(path)
        score = sum(hits.values())
        if score > 0:
            results.append({"filename": file, "score": score, "matches": dict(hits)})
    return results

# ====== AUTO-UPDATER ======
def get_remote_version():
    try:
        resp = requests.get(GITHUB_RAW_BASE + VERSION_FILE)
        return resp.text.strip()
    except:
        return LOCAL_VERSION

def update_script():
    try:
        py_url = GITHUB_RAW_BASE + SCRIPT_NAME
        new_code = requests.get(py_url).text
        with open(SCRIPT_NAME, 'w', encoding='utf-8') as f:
            f.write(new_code)
        subprocess.Popen([sys.executable, SCRIPT_NAME])
        sys.exit()
    except Exception as e:
        messagebox.showerror("Update Failed", str(e))

# ====== UNINSTALLER ======
def uninstall():
    script = f"""@echo off
    timeout /t 1 >nul
    del "{SCRIPT_NAME}"
    del "{VERSION_FILE}"
    del "%USERPROFILE%\\Desktop\\{SHORTCUT_NAME}"
    del %0
    """
    with open("uninstall.bat", "w") as f:
        f.write(script)
    os.startfile("uninstall.bat")
    sys.exit()

# ====== GUI APP ======
class DeepCheckerApp:
    def __init__(self, root):
        self.themes = ["darkly", "flatly", "cyborg", "superhero", "solar"]
        self.theme_index = 0
        self.style = Style(theme=self.themes[self.theme_index])
        self.root = self.style.master
        self.root.title(f"🧠 DeepChecker v{LOCAL_VERSION}")
        self.root.geometry("650x480")
        try:
            self.root.iconbitmap(ICON_PATH)
        except:
            pass

        self.discord_id = tk.StringVar()

        frame = ttk.Frame(self.root, padding=15)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(frame, text="DeepChecker", font=("Segoe UI", 14, "bold")).pack(pady=(0, 10))

        ttk.Label(frame, text="Enter your Discord ID:").pack(anchor="w")
        ttk.Entry(frame, textvariable=self.discord_id, width=40).pack(pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="🔍 Start Scan", command=self.start_scan, bootstyle="success").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑 Uninstall", command=uninstall, bootstyle="danger").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="💬 Support Server", command=lambda: webbrowser.open(DISCORD_SERVER_URL), bootstyle="info").pack(side=LEFT, padx=5)

        self.theme_button = ttk.Button(btn_frame, text=f"🎨 Theme: {self.themes[self.theme_index]}", command=self.toggle_theme, bootstyle="secondary")
        self.theme_button.pack(side=LEFT, padx=5)

        ttk.Label(frame, text="Scan Results:").pack(anchor="w", pady=(10, 0))

        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=BOTH, expand=True)

        self.output = tk.Text(text_frame, wrap="word", height=10, relief="sunken", borderwidth=2, bg=self.style.colors.bg, fg=self.style.colors.fg)
        self.output.pack(side=LEFT, fill=BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.output.yview)
        scrollbar.pack(side=RIGHT, fill="y")
        self.output.config(yscrollcommand=scrollbar.set)

        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def toggle_theme(self):
        self.theme_index = (self.theme_index + 1) % len(self.themes)
        new_theme = self.themes[self.theme_index]
        self.style.theme_use(new_theme)
        self.output.config(bg=self.style.colors.bg, fg=self.style.colors.fg)
        self.theme_button.config(text=f"🎨 Theme: {new_theme}")

    def start_scan(self):
        self.output.delete(1.0, tk.END)
        gtag_path = find_gorilla_tag_path()
        if not gtag_path:
            self.output.insert(tk.END, "🚫 Gorilla Tag path not found.\n")
            return
        results = analyze_all_dlls(gtag_path)
        if not results:
            self.output.insert(tk.END, "✅ No suspicious DLLs found.\n")
        for result in results:
            self.output.insert(tk.END, f"🔍 {result['filename']} | Score: {result['score']}\n")
            for k, v in result['matches'].items():
                self.output.insert(tk.END, f"   - {k}: {v}\n")

    def check_for_updates(self):
        remote = get_remote_version()
        if remote != LOCAL_VERSION:
            if messagebox.askyesno("Update Available", f"A new version ({remote}) is available.\nUpdate now?"):
                update_script()

# ====== MAIN ======
if __name__ == '__main__':
    root = tk.Tk()
    app = DeepCheckerApp(root)
    root.mainloop()
