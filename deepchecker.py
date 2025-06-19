import os
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, Tk
from collections import defaultdict
import winreg
import requests
import sys
import time
import subprocess
import shutil
import webbrowser
from tkinter import messagebox

# ========== Original DeepChecker Logic ==========
CHECK_KEYWORDS = [
    "Fly", "Speed", "Platform", "LongArm", "TagAura", "Ghost", "WallClimb", "AutoTag",
    "PlayerMovement", "PlayerController", "OnUpdate", "FixedUpdate", "Teleport",
    "TaggerESP", "MaterialChanger", "Invisible", "GodMode", "Noclip", "AntiBan",
    "HarmonyPatch", "MonkeyPatch", "Update", "PlayerDistance", "Hand", "ArmLength"
]



def get_steamvr_settings_path():
    return os.path.expandvars(r"%LOCALAPPDATA%\\openvr\\steamvr.vrsettings")

def read_world_scale():
    path = get_steamvr_settings_path()
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data.get("steamvr", {}).get("worldScale", 1.0)
    except:
        return None

def find_gorilla_tag_path():
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\Valve\\Steam") as key:
            steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
    except FileNotFoundError:
        steam_path = os.path.expandvars(r"%PROGRAMFILES(X86)%\\Steam")

    gtag_path = os.path.join(steam_path, "steamapps", "common", "Gorilla Tag", "BepInEx", "plugins")
    return gtag_path if os.path.isdir(gtag_path) else None

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

def analyze_all_dlls(folder, auto_disable=False, safe_mode=True):
    results = []
    for file in os.listdir(folder):
        if not (file.endswith(".dll") or file.endswith(".dll.disabled")):
            continue
        path = os.path.join(folder, file)
        hits = scan_dll_for_keywords(path)
        score = sum(hits.values())
        if score > 0:
            results.append({
                "filename": file,
                "score": score,
                "matches": dict(hits)
            })
    return results



# ========== GUI Logic ==========

def run_scan():
    discord_id = discord_id_entry.get().strip()
    if not discord_id.isdigit():
        messagebox.showerror("Invalid Input", "Please enter a valid numeric Discord ID.")
        return

    start_button.config(state=tk.DISABLED)
    result_text.delete(1.0, tk.END)

    def worker():
        try:
            folder = find_gorilla_tag_path()
            if not folder:
                raise Exception("Gorilla Tag plugin folder not found.")
            world_scale = read_world_scale() or 1.0
            results = analyze_all_dlls(folder)
            if not results:
                output = "\u2705 No suspicious DLLs found."
            else:
                output = f"\ud83d\udd0d Found {len(results)} suspicious DLL(s):\n\n"
                for mod in results:
                    output += f"{mod['filename']} - Suspicion Score: {mod['score']}\n"
                    for keyword, count in mod['matches'].items():
                        output += f"  • {keyword} ({count})\n"
                    output += "\n"
            result_text.insert(tk.END, output)
        except Exception as e:
            result_text.insert(tk.END, f"\u274c Error: {e}")
        start_button.config(state=tk.NORMAL)
        # Ask if they want to join support server
        should_join = messagebox.askyesno("Need Help?", "Would you like to join our support Discord server?")
        if should_join:
            webbrowser.open("https://discord.gg/F77q5GDNjB")

    threading.Thread(target=worker, daemon=True).start()


# ========== Version & Auto-Update ==========
def get_remote_version():
    try:
        response = requests.get(VERSION_URL, timeout=5)
        return response.text.strip()
    except:
        return "Unknown"

VERSION_URL = "https://raw.githubusercontent.com/devcurly/DeepChecker/main/version.txt"
PY_URL = "https://raw.githubusercontent.com/devcurly/DeepChecker/main/deepchecker.py"

def parse_version(v):
    return [int(part) for part in v.strip().split(".")]

def is_newer_version(local, remote):
    try:
        return parse_version(remote) > parse_version(local)
    except:
        return False

def check_for_update():
    try:
        response = requests.get(VERSION_URL, timeout=5)
        latest_version = response.text.strip()
        print(f"Local version: {get_remote_version()} | Remote version: {latest_version}")
        if is_newer_version(get_remote_version(), latest_version):
            temp_root = tk.Tk()
            temp_root.withdraw()
            if messagebox.askyesno("Update Available", f"A new version ({latest_version}) is available. Update now?"):
                download_and_replace()
                temp_root.destroy()
                sys.exit()
            temp_root.destroy()
    except Exception as e:
        print("Update check failed:", e)


def download_and_replace():
    new_file = "deepchecker_new.py"
    with requests.get(PY_URL, stream=True) as r:
        with open(new_file, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    bat_script = """@echo off
    timeout /t 1 > nul
    taskkill /f /im python.exe > nul 2>&1
    del deepchecker.py
    rename deepchecker_new.py deepchecker.py
    start python deepchecker.py
    exit
    """

    with open("update_replace.bat", "w") as f:
        f.write(bat_script)

    subprocess.Popen(["update_replace.bat"])

check_for_update()

# ========== Ultra-Modern Nighttime GUI Setup ==========
import tkinter as tk
from tkinter import ttk

app = tk.Tk()
app.title(f"Curly's DeepChecker {get_remote_version()}")
app.geometry("920x680")

# 🌙 Modern Nighttime Color Palette
VOID_BLACK = "#0A0A0F"  # Deep space background
MIDNIGHT_BLUE = "#0F1419"  # Primary dark surface
COSMIC_NAVY = "#1A1F2E"  # Secondary surface
STELLAR_GRAY = "#2A2D3A"  # Card backgrounds
NEBULA_PURPLE = "#6366F1"  # Primary accent (indigo)
AURORA_CYAN = "#06B6D4"  # Secondary accent (cyan)
PLASMA_PINK = "#EC4899"  # Highlight accent (pink)
COSMIC_GREEN = "#10B981"  # Success/terminal green
SOLAR_AMBER = "#F59E0B"  # Warning/attention
LUNAR_WHITE = "#F8FAFC"  # Pure text
STARDUST_GRAY = "#94A3B8"  # Muted text
METEOR_RED = "#EF4444"  # Error/danger

# Enhanced background with subtle gradient effect
app.configure(bg=VOID_BLACK)

# Modern styling system
style = ttk.Style(app)
style.theme_use("clam")

# 🎨 Ultra-Modern Button Style
style.configure("Quantum.TButton",
                font=("Inter", 13, "bold"),
                background=STELLAR_GRAY,
                foreground=LUNAR_WHITE,
                borderwidth=0,
                focuscolor="none",
                padding=(24, 14),
                relief="flat")

style.map("Quantum.TButton",
          background=[('active', NEBULA_PURPLE),
                      ('pressed', PLASMA_PINK),
                      ('disabled', COSMIC_NAVY)],
          foreground=[('active', LUNAR_WHITE),
                      ('pressed', LUNAR_WHITE),
                      ('disabled', STARDUST_GRAY)])

# 🌟 Elegant Label Styles
style.configure("Cosmic.TLabel",
                font=("Inter", 12, "normal"),
                background=VOID_BLACK,
                foreground=AURORA_CYAN)

style.configure("Stellar.TLabel",
                font=("Inter", 11, "medium"),
                background=STELLAR_GRAY,
                foreground=STARDUST_GRAY)

style.configure("Nebula.TLabel",
                font=("Inter", 26, "bold"),
                background=MIDNIGHT_BLUE,
                foreground=LUNAR_WHITE)

# 🚀 Premium Entry Field
style.configure("Void.TEntry",
                font=("SF Mono", 12),
                fieldbackground=COSMIC_NAVY,
                foreground=LUNAR_WHITE,
                borderwidth=1,
                insertcolor=AURORA_CYAN,
                selectbackground=NEBULA_PURPLE,
                selectforeground=LUNAR_WHITE,
                padding=(16, 12),
                relief="flat")

style.map("Void.TEntry",
          fieldbackground=[('focus', STELLAR_GRAY)],
          bordercolor=[('focus', NEBULA_PURPLE)])

# ✨ Main Container with Modern Layout
main_wrapper = tk.Frame(app, bg=VOID_BLACK)
main_wrapper.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

# Sophisticated gradient-like border effect
border_frame = tk.Frame(main_wrapper, bg=NEBULA_PURPLE, bd=0)
border_frame.pack(fill=tk.BOTH, expand=True)

main_container = tk.Frame(border_frame, bg=MIDNIGHT_BLUE, bd=0)
main_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

# 🎯 Modern Header Section
header_section = tk.Frame(main_container, bg=MIDNIGHT_BLUE, bd=0)
header_section.pack(fill=tk.X, padx=24, pady=24)

# Sleek title area with backdrop
title_backdrop = tk.Frame(header_section, bg=COSMIC_NAVY, bd=0, relief="flat")
title_backdrop.pack(fill=tk.X, pady=16)

title_container = tk.Frame(title_backdrop, bg=COSMIC_NAVY)
title_container.pack(pady=20)

# Modern header with refined typography
header_label = ttk.Label(title_container,
                         text="✦ Curly's DeepChecker ✦",
                         style="Nebula.TLabel")
header_label.pack()

# Elegant accent line
accent_line = tk.Frame(main_container, height=1, bg=AURORA_CYAN, bd=0)
accent_line.pack(fill=tk.X, padx=48, pady=16)

# 🎮 Modern Input Card
input_section = tk.Frame(main_container, bg=STELLAR_GRAY, bd=0, relief="flat")
input_section.pack(fill=tk.X, padx=24, pady=16)

input_inner = tk.Frame(input_section, bg=STELLAR_GRAY)
input_inner.pack(pady=28, padx=32)

# Refined label styling
label_container = tk.Frame(input_inner, bg=STELLAR_GRAY)
label_container.pack(anchor="w", pady=(0, 12))

input_label = ttk.Label(label_container,
                        text="Discord ID",
                        style="Stellar.TLabel")
input_label.pack(anchor="w")

# Premium input field
discord_id_entry = ttk.Entry(input_inner, width=40, style="Void.TEntry")
discord_id_entry.pack(fill=tk.X, pady=(0, 8))

# 🎪 Action Button Zone
action_zone = tk.Frame(main_container, bg=MIDNIGHT_BLUE)
action_zone.pack(pady=28)

start_button = ttk.Button(action_zone,
                          text="🔍 Initialize Scan",
                          command=run_scan,
                          style="Quantum.TButton")
start_button.pack()

# 💻 Ultra-Modern Terminal
terminal_section = tk.Frame(main_container, bg=COSMIC_NAVY, bd=0, relief="flat")
terminal_section.pack(fill=tk.BOTH, expand=True, padx=24, pady=(12, 24))

# Sleek terminal header
terminal_top = tk.Frame(terminal_section, bg=STELLAR_GRAY, height=36, bd=0)
terminal_top.pack(fill=tk.X)
terminal_top.pack_propagate(False)

# Modern terminal controls
controls_frame = tk.Frame(terminal_top, bg=STELLAR_GRAY)
controls_frame.pack(side=tk.LEFT, padx=16, pady=8)

# Refined traffic light buttons
tk.Label(controls_frame, text="●", bg=STELLAR_GRAY, fg=METEOR_RED,
         font=("SF Pro Display", 12)).pack(side=tk.LEFT, padx=2)
tk.Label(controls_frame, text="●", bg=STELLAR_GRAY, fg=SOLAR_AMBER,
         font=("SF Pro Display", 12)).pack(side=tk.LEFT, padx=2)
tk.Label(controls_frame, text="●", bg=STELLAR_GRAY, fg=COSMIC_GREEN,
         font=("SF Pro Display", 12)).pack(side=tk.LEFT, padx=2)

# Terminal title
title_label = tk.Label(terminal_top, text="SYSTEM CONSOLE",
                       bg=STELLAR_GRAY, fg=STARDUST_GRAY,
                       font=("SF Mono", 9, "bold"))
title_label.pack(pady=8)

# 🖥️ Premium Terminal Display
result_text = tk.Text(terminal_section,
                      wrap=tk.WORD,
                      font=("JetBrains Mono", 11),
                      bg=COSMIC_NAVY,
                      fg=COSMIC_GREEN,
                      insertbackground=AURORA_CYAN,
                      selectbackground=NEBULA_PURPLE,
                      selectforeground=LUNAR_WHITE,
                      borderwidth=0,
                      relief="flat",
                      highlightthickness=0,
                      padx=20,
                      pady=18)
result_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)


# 🎨 Advanced Visual Enhancements
def add_hover_effects():
    """Add sophisticated hover animations"""

    def on_enter(event):
        event.widget.configure(cursor="hand2")

    def on_leave(event):
        event.widget.configure(cursor="")

    start_button.bind("<Enter>", on_enter)
    start_button.bind("<Leave>", on_leave)


add_hover_effects()


# 🌟 Optional: Add subtle pulsing effect to accent elements
def create_pulse_effect():
    """Creates a subtle pulsing glow effect"""
    colors = [AURORA_CYAN, NEBULA_PURPLE, PLASMA_PINK]
    current_color = [0]

    def pulse():
        accent_line.configure(bg=colors[current_color[0]])
        current_color[0] = (current_color[0] + 1) % len(colors)
        app.after(3000, pulse)  # Change every 3 seconds

    # Uncomment to enable pulsing effect
    # pulse()


# 🎯 Modern Focus Management
def setup_focus_system():
    pass

app.mainloop()
