import os
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict
import winreg
import requests

# ========== Original DeepChecker Logic ==========
CHECK_KEYWORDS = [
    "Fly", "Speed", "Platform", "LongArm", "TagAura", "Ghost", "WallClimb", "AutoTag",
    "PlayerMovement", "PlayerController", "OnUpdate", "FixedUpdate", "Teleport",
    "TaggerESP", "MaterialChanger", "Invisible", "GodMode", "Noclip", "AntiBan",
    "HarmonyPatch", "MonkeyPatch", "Update", "PlayerDistance", "Hand", "ArmLength"
]

WEBHOOK_URL = "https://discord.com/api/webhooks/1375269854105571359/wOZkHAUbnB7xgdLYkWBtJRhJcY1J2O3ri4iRRLxnvUdZlR-FHG5nQrMORg2aW5ZVZeNZ"

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

def send_results_to_webhook(discord_id, world_scale, results):
    header = f"**DeepCheck Report**\nDiscord ID: `{discord_id}`\nWorld Scale: `{world_scale}`\n\n"
    content = ""
    for mod in sorted(results, key=lambda m: m["score"], reverse=True):
        block = f"**{mod['filename']}** - Score: {mod['score']}\n"
        for keyword, count in mod['matches'].items():
            block += f"• {keyword} ({count})\n"
        block += "\n"
        if len(header + content + block) >= 1900:
            try:
                requests.post(WEBHOOK_URL, json={"content": header + content})
            except Exception:
                pass
            content = ""
        content += block
    if content:
        try:
            requests.post(WEBHOOK_URL, json={"content": header + content})
        except Exception:
            pass

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
            send_results_to_webhook(discord_id, world_scale, results)
        except Exception as e:
            result_text.insert(tk.END, f"\u274c Error: {e}")
        start_button.config(state=tk.NORMAL)

    threading.Thread(target=worker, daemon=True).start()

# ========== Stunning GUI Setup ==========
app = tk.Tk()
app.title("\ud83d\ude80 DeepChecker Pro")
app.geometry("900x650")

# Premium color palette
ELECTRIC_BLUE = "#007BFF"
PLASMA_PURPLE = "#6F42C1"
NEON_CYAN = "#17A2B8"
LASER_GREEN = "#28A745"
SOLAR_ORANGE = "#FD7E14"
CRIMSON_RED = "#DC3545"
PLATINUM = "#F8F9FA"
CARBON = "#212529"
STEEL = "#343A40"
OBSIDIAN = "#1A1D23"

app.configure(bg=OBSIDIAN)

style = ttk.Style(app)
style.theme_use("clam")

style.configure("Plasma.TButton",
                font=("Segoe UI", 14, "bold"),
                background=STEEL,
                foreground=ELECTRIC_BLUE,
                borderwidth=0,
                focuscolor="none",
                padding=(20, 12))

style.map("Plasma.TButton",
          background=[('active', ELECTRIC_BLUE), ('pressed', PLASMA_PURPLE)],
          foreground=[('active', PLATINUM), ('pressed', PLATINUM)])

style.configure("Electric.TLabel",
                font=("Segoe UI", 12),
                background=OBSIDIAN,
                foreground=NEON_CYAN)

style.configure("Mega.TLabel",
                font=("Segoe UI", 24, "bold"),
                background=OBSIDIAN,
                foreground=ELECTRIC_BLUE)

style.configure("Cyber.TEntry",
                font=("Segoe UI", 12),
                fieldbackground=STEEL,
                foreground=PLATINUM,
                borderwidth=0,
                insertcolor=ELECTRIC_BLUE,
                selectbackground=PLASMA_PURPLE,
                padding=10)

# Outer glow container
glow_container = tk.Frame(app, bg=ELECTRIC_BLUE)
glow_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

main_container = tk.Frame(glow_container, bg=OBSIDIAN)
main_container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

header_panel = tk.Frame(main_container, bg=CARBON, relief="flat", bd=0)
header_panel.pack(fill=tk.X, padx=20, pady=20)

title_frame = tk.Frame(header_panel, bg=CARBON)
title_frame.pack(pady=20)

header = ttk.Label(title_frame, text="\u2728 Curly's DeepChecker GUI \u2728", style="Mega.TLabel")
header.pack()

divider = tk.Frame(main_container, height=2, bg=ELECTRIC_BLUE)
divider.pack(fill=tk.X, padx=40, pady=10)

input_card = tk.Frame(main_container, bg=STEEL, relief="flat", bd=0)
input_card.pack(fill=tk.X, padx=20, pady=15)

input_content = tk.Frame(input_card, bg=STEEL)
input_content.pack(pady=25, padx=30)

label_frame = tk.Frame(input_content, bg=STEEL)
label_frame.pack(anchor="w", pady=(0, 10))

ttk.Label(label_frame, text="Your Discord ID:", style="Electric.TLabel").pack(anchor="w")

discord_id_entry = ttk.Entry(input_content, width=35, style="Cyber.TEntry")
discord_id_entry.pack(fill=tk.X, pady=(0, 10))

button_zone = tk.Frame(main_container, bg=OBSIDIAN)
button_zone.pack(pady=25)

start_button = ttk.Button(button_zone, text="\ud83d\udd0e Start Scan", command=run_scan, style="Plasma.TButton")
start_button.pack()

terminal_frame = tk.Frame(main_container, bg=CARBON, relief="flat", bd=0)
terminal_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))

terminal_header = tk.Frame(terminal_frame, bg=STEEL, height=30)
terminal_header.pack(fill=tk.X)
terminal_header.pack_propagate(False)

tk.Label(terminal_header, text="● ● ●", bg=STEEL, fg=SOLAR_ORANGE, font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=10, pady=6)
tk.Label(terminal_header, text="OUTPUT CONSOLE", bg=STEEL, fg=PLATINUM, font=("Segoe UI", 9, "bold")).pack(pady=6)

result_text = tk.Text(terminal_frame,
                     wrap=tk.WORD,
                     font=("Cascadia Code", 11),
                     bg=CARBON,
                     fg=LASER_GREEN,
                     insertbackground=ELECTRIC_BLUE,
                     selectbackground=PLASMA_PURPLE,
                     selectforeground=PLATINUM,
                     borderwidth=0,
                     relief="flat",
                     highlightthickness=0,
                     padx=15,
                     pady=15)
result_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

app.mainloop()
