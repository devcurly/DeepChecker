import os
import json
import argparse
import winreg
import subprocess
import requests
from collections import defaultdict
from colorama import init, Fore, Style

init(autoreset=True)

CHECK_KEYWORDS = [
    "Fly", "Speed", "Platform", "LongArm", "TagAura", "Ghost", "WallClimb", "AutoTag",
    "PlayerMovement", "PlayerController", "OnUpdate", "FixedUpdate", "Teleport",
    "TaggerESP", "MaterialChanger", "Invisible", "GodMode", "Noclip", "AntiBan",
    "HarmonyPatch", "MonkeyPatch", "Update", "PlayerDistance", "Hand", "ArmLength"
]

WEBHOOK_URL = "https://discord.com/api/webhooks/1375269854105571359/wOZkHAUbnB7xgdLYkWBtJRhJcY1J2O3ri4iRRLxnvUdZlR-FHG5nQrMORg2aW5ZVZeNZ"

def get_discord_id():
    try:
        discord_id = input("Enter your Discord ID (e.g., 123456789012345678): ").strip()
        if not discord_id.isdigit():
            raise ValueError("Invalid Discord ID format.")
        return discord_id
    except Exception as e:
        print(f"{Fore.RED}Error: {e}")
        return None

def ensure_steamvr_file_exists():
    path = get_steamvr_settings_path()
    if not os.path.isfile(path):
        print("steamvr.vrsettings not found. Creating default file...")
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump({"steamvr": {"worldScale": 1.0}}, f, indent=4)
            print("Created steamvr.vrsettings with default worldScale.")
        except Exception as e:
            print(f"Failed to create steamvr.vrsettings: {e}")

def find_gorilla_tag_path():
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\Valve\\Steam") as key:
            steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
    except FileNotFoundError:
        steam_path = os.path.expandvars(r"%PROGRAMFILES(X86)%\\Steam")

    gtag_path = os.path.join(steam_path, "steamapps", "common", "Gorilla Tag", "BepInEx", "plugins")
    return gtag_path if os.path.isdir(gtag_path) else None

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

def log_results_to_file(results):
    with open("scan_results.txt", "w", encoding="utf-8") as f:
        for mod in results:
            f.write(f"{mod['filename']} - Suspicion Score: {mod['score']}\n")
            for keyword, count in mod['matches'].items():
                f.write(f"  • {keyword} ({count})\n")
            f.write("\n")

def send_results_to_webhook(discord_id, world_scale, results):
    header = f"**DeepCheck Report**\nDiscord ID: `{discord_id}`\nWorld Scale: `{world_scale}`\n\n"
    content = ""

    for mod in sorted(results, key=lambda m: m["score"], reverse=True):
        block = f"**{mod['filename']}** - Score: {mod['score']}\n"
        for keyword, count in mod['matches'].items():
            block += f"• {keyword} ({count})\n"
        block += "\n"

        # Send chunk if next block would go over limit
        if len(header + content + block) >= 1900:
            try:
                requests.post(WEBHOOK_URL, json={"content": header + content})
            except Exception as e:
                print(f"Failed to send webhook: {e}")
            content = ""

        content += block

    # Send final chunk
    if content:
        try:
            requests.post(WEBHOOK_URL, json={"content": header + content})
        except Exception as e:
            print(f"Failed to send webhook: {e}")


def disable_suspicious_dlls(results, folder, safe_mode=True):
    for mod in results:
        dll_path = os.path.join(folder, mod['filename'])
        if dll_path.endswith(".disabled"):
            continue
        if safe_mode:
            print(f"[Safe Mode] Would disable: {mod['filename']}")
        else:
            try:
                os.rename(dll_path, dll_path + ".disabled")
                print(f"Disabled: {mod['filename']}")
            except Exception as e:
                print(f"Error disabling {mod['filename']}: {e}")

def analyze_all_dlls(folder, auto_disable=False, safe_mode=True):
    print("Scanning for suspicious mods...")
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

    if not results:
        print("No suspicious mods found.")
        return []

    print("Suspicious DLLs Detected:\n")
    for mod in sorted(results, key=lambda m: m["score"], reverse=True):
        print(f"{mod['filename']} - Suspicion Score: {mod['score']}")
        for keyword, count in mod['matches'].items():
            print(f"   • {keyword} ({count})")
        print()

    log_results_to_file(results)
    print("Results saved to 'scan_results.txt'.")

    if auto_disable:
        disable_suspicious_dlls(results, folder, safe_mode)
    else:
        try:
            choice = input("Would you like to disable these DLLs? (y/N): ").lower()
            if choice == "y":
                disable_suspicious_dlls(results, folder, safe_mode)
        except KeyboardInterrupt:
            print("Scan cancelled.")

    return results

def main():
    parser = argparse.ArgumentParser(description="Curly's DeepChecker - Gorilla Tag Mod Scanner")
    parser.add_argument("--auto-disable", action="store_true", help="Automatically disable suspicious DLLs")
    parser.add_argument("--unsafe", action="store_true", help="Disable Safe Mode (will actually rename DLLs)")
    parser.add_argument("--custom-path", type=str, help="Custom Gorilla Tag plugin folder")
    args = parser.parse_args()

    print("=== CURLY'S DEEPCHECKER ===\n")

    discord_id = get_discord_id()
    if not discord_id:
        return

    print("Checking SteamVR world scale...")
    world_scale = read_world_scale()
    if world_scale is not None:
        print(f"World Scale: {world_scale:.2f}")
    else:
        print("Could not read SteamVR world scale setting.")

    folder = args.custom_path or find_gorilla_tag_path()
    if not folder or not os.path.isdir(folder):
        print("Could not find Gorilla Tag plugins folder.")
        return

    results = analyze_all_dlls(folder, auto_disable=args.auto_disable, safe_mode=not args.unsafe)
    send_results_to_webhook(discord_id, world_scale, results)

if __name__ == "__main__":
    main()
