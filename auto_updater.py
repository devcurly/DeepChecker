import os
import requests
import time
import subprocess

VERSION_URL = "https://raw.githubusercontent.com/YourUser/YourRepo/main/version.txt"
EXE_URL = "https://github.com/YourUser/YourRepo/releases/latest/download/deepchecker.exe"
LOCAL_VERSION_FILE = "version.txt"
EXE_NAME = "deepchecker.exe"

def get_remote_version():
    try:
        r = requests.get(VERSION_URL, timeout=5)
        return r.text.strip()
    except:
        return None

def get_local_version():
    if not os.path.exists(LOCAL_VERSION_FILE):
        return None
    with open(LOCAL_VERSION_FILE, "r") as f:
        return f.read().strip()

def download_new_exe():
    print("Downloading update...")

    # Download deepchecker.exe
    with requests.get(EXE_URL, stream=True) as r:
        with open("deepchecker_new.exe", "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)



def replace_and_restart():
    if os.path.exists(EXE_NAME):
        os.rename(EXE_NAME, "deepchecker_backup.exe")
    os.rename("deepchecker_new.exe", EXE_NAME)
    with open(LOCAL_VERSION_FILE, "w") as f:
        f.write(get_remote_version())
    print("Launching updated version...")
    subprocess.Popen([EXE_NAME])
    time.sleep(1)
    exit()

def main():
    remote_version = get_remote_version()
    local_version = get_local_version()

    if remote_version and remote_version != local_version:
        download_new_exe()
        replace_and_restart()
    else:
        print("You're up to date.")
        # ✅ Launch the app even if already up to date
        if os.path.exists("deepchecker.exe"):
            subprocess.Popen(["deepchecker.exe"])
        elif os.path.exists("deepchecker.py"):
            subprocess.Popen(["python", "deepchecker.py"])
        else:
            print("❌ No DeepChecker file found to launch.")


if __name__ == "__main__":
    main()
