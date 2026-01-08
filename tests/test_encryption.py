"""
Encryption feature test script.

Usage:
1. Close the app
2. python tests/test_encryption.py <command>
3. Launch the app and verify

Commands:
- show: Show current settings
- clear: Clear all settings (new user test)
- plaintext: Set plaintext keys (migration test)
- delete_secret: Delete secret key only (decryption failure test)
"""

import sys
import os
import json

# Windows shared_preferences path (Flet 1.0)
PREFS_DIR = os.path.expandvars(r"%APPDATA%\Your Company\seatxray")
PREFS_FILE = os.path.join(PREFS_DIR, "shared_preferences.json")
SECRET_KEY_FILE = os.path.join(PREFS_DIR, ".secret_key")

# Flet 1.0 uses flutter. prefix for keys
KEY_PREFIX = "flutter."

def load_prefs():
    if os.path.exists(PREFS_FILE):
        with open(PREFS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_prefs(data):
    os.makedirs(PREFS_DIR, exist_ok=True)
    with open(PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved to {PREFS_FILE}")

def cmd_clear():
    """Clear all settings."""
    removed = []
    if os.path.exists(PREFS_FILE):
        os.remove(PREFS_FILE)
        removed.append("shared_preferences.json")
    if os.path.exists(SECRET_KEY_FILE):
        os.remove(SECRET_KEY_FILE)
        removed.append(".secret_key")
    if removed:
        print(f"[OK] Cleared: {', '.join(removed)}")
    else:
        print("[INFO] No files found")

def cmd_plaintext():
    """Set plaintext keys (for migration test)."""
    prefs = load_prefs()
    prefs[f"{KEY_PREFIX}amadeus_api_key"] = "TEST_PLAINTEXT_KEY_12345"
    prefs[f"{KEY_PREFIX}amadeus_api_secret"] = "TEST_PLAINTEXT_SECRET_67890"
    save_prefs(prefs)
    # Also delete secret key so migration will occur
    if os.path.exists(SECRET_KEY_FILE):
        os.remove(SECRET_KEY_FILE)
        print("[OK] Also deleted .secret_key")
    print("[OK] Set plaintext credentials (no encryption prefix)")
    print("[INFO] Next app launch should auto-migrate to encrypted format")

def cmd_delete_secret():
    """Delete secret key only (for decryption failure test)."""
    if os.path.exists(SECRET_KEY_FILE):
        os.remove(SECRET_KEY_FILE)
        print("[OK] Deleted .secret_key")
        print("[INFO] Next app launch should fail to decrypt -> show warning banner")
    else:
        print("[INFO] No .secret_key file found")

def cmd_show():
    """Show current settings."""
    print("=== Files ===")
    print(f"  shared_preferences.json: {'Exists' if os.path.exists(PREFS_FILE) else 'NOT FOUND'}")
    print(f"  .secret_key: {'Exists' if os.path.exists(SECRET_KEY_FILE) else 'NOT FOUND'}")
    
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, "r") as f:
            secret = f.read().strip()
            print(f"  .secret_key content: {secret[:20]}...")
    
    print("\n=== Preferences ===")
    prefs = load_prefs()
    if not prefs:
        print("  (empty)")
        return
    
    for key, value in prefs.items():
        display_key = key.replace(KEY_PREFIX, "")
        if len(str(value)) > 60:
            print(f"  {display_key}: {str(value)[:60]}...")
        else:
            print(f"  {display_key}: {value}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1].lower()
    
    commands = {
        "clear": cmd_clear,
        "plaintext": cmd_plaintext,
        "delete_secret": cmd_delete_secret,
        "show": cmd_show,
    }
    
    if cmd in commands:
        commands[cmd]()
    else:
        print(f"[ERROR] Unknown command: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
