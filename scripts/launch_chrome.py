"""Launch Chrome with CDP enabled and a forced default download directory.

Chrome has no CLI flag for the default download directory — the setting lives
inside the profile's Preferences JSON. This script:
  1. Kills any running chrome.exe (patching Preferences while Chrome is open
     gets overwritten on exit).
  2. Writes download.default_directory and prompt_for_download=false into the
     profile's Preferences file (creating it if the profile is fresh).
  3. Launches Chrome with --remote-debugging-port=9222.

After running this, every download triggered from Blackboard (via Ally's
"Download original" button, etc.) lands in <project>/_downloads automatically.

Usage:
    python scripts/launch_chrome.py
"""
import os, sys, json, time, subprocess

sys.path.insert(0, os.path.dirname(__file__))
from bb_utils import BASE_DIR

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = os.path.join(BASE_DIR, "chrome-profile").replace("/", os.sep)
DEFAULT_PROFILE = os.path.join(USER_DATA_DIR, "Default")
PREFS_PATH = os.path.join(DEFAULT_PROFILE, "Preferences")

DOWNLOAD_DIR = os.path.join(BASE_DIR, "_downloads").replace("/", os.sep)
START_URL = "https://blackboard.sc.edu"


def kill_chrome():
    """Kill all chrome.exe processes. Idempotent — silent if none running."""
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"],
                   capture_output=True, text=True)
    time.sleep(2)


def patch_preferences():
    """Write download.default_directory into the profile Preferences file.
    Creates the profile directory and a minimal Preferences file if missing."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(DEFAULT_PROFILE, exist_ok=True)

    if os.path.exists(PREFS_PATH):
        with open(PREFS_PATH, "r", encoding="utf-8") as f:
            try:
                prefs = json.load(f)
            except json.JSONDecodeError:
                prefs = {}
    else:
        prefs = {}

    download = prefs.get("download", {})
    download["default_directory"] = DOWNLOAD_DIR
    download["prompt_for_download"] = False
    download["extensions_to_open"] = ""
    prefs["download"] = download
    # Disable "Ask where to save each file" prompt at the profile level
    prefs["profile"] = prefs.get("profile", {})
    prefs["profile"]["default_content_setting_values"] = prefs["profile"].get("default_content_setting_values", {})
    prefs["profile"]["default_content_setting_values"]["automatic_downloads"] = 1

    savefile = prefs.get("savefile", {})
    savefile["default_directory"] = DOWNLOAD_DIR
    prefs["savefile"] = savefile

    with open(PREFS_PATH, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2)

    print(f"  Patched Preferences: {PREFS_PATH}")
    print(f"  Default download dir: {DOWNLOAD_DIR}")


def launch_chrome():
    """Launch Chrome detached with CDP enabled."""
    args = [
        CHROME_EXE,
        "--remote-debugging-port=9222",
        f"--user-data-dir={USER_DATA_DIR}",
        START_URL,
    ]
    subprocess.Popen(args, creationflags=subprocess.DETACHED_PROCESS
                     if hasattr(subprocess, "DETACHED_PROCESS") else 0)
    print(f"  Launched Chrome -> {START_URL}")


def main():
    print("Step 1: Killing any running Chrome...")
    kill_chrome()
    print("Step 2: Patching Preferences...")
    patch_preferences()
    print("Step 3: Launching Chrome...")
    launch_chrome()
    print("\nDone. Chrome is ready. Log in to Blackboard, then run Phase 5.")


if __name__ == "__main__":
    main()
