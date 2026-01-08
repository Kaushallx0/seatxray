# Copyright (c) 2026 SeatXray Developers
# Licensed under the terms of the GNU Affero General Public License (AGPL) version 3.
# See LICENSE file in the project root for details.

"""Secure credential storage with encryption and auto-migration."""

import flet.security as security
import secrets
import uuid
import hashlib
import os
import sys

_ENCRYPTED_PREFIX = "ENC:v1:"
_SECRET_KEY_NAME = "_sx_internal_secret_v1"

# Cache for secret key (avoid repeated file reads)
_cached_secret = None


def _is_android() -> bool:
    """Check if running on Android."""
    # Android has 'linux' as platform but has specific env vars
    return 'ANDROID_ROOT' in os.environ or 'ANDROID_DATA' in os.environ


def _get_secret_key_path() -> str:
    """Get path to secret key file (desktop only)."""
    if sys.platform.startswith('win'):
        base_dir = os.path.expandvars(r"%APPDATA%\Your Company\seatxray")
    elif sys.platform == 'darwin':
        base_dir = os.path.expanduser("~/Library/Application Support/seatxray")
    else:
        # Linux desktop
        base_dir = os.path.expanduser("~/.local/share/seatxray")
    
    return os.path.join(base_dir, ".secret_key")


def _get_device_seed() -> str:
    """Generate device-specific seed with fallback."""
    try:
        mac = uuid.getnode()
        if (mac >> 40) & 1:
            return "fallback"
        return hashlib.sha256(str(mac).encode()).hexdigest()[:16]
    except Exception:
        return "fallback"


def _generate_new_secret() -> str:
    """Generate a new secret key."""
    device_seed = _get_device_seed()
    random_part = secrets.token_urlsafe(24)
    return f"{device_seed}-{random_part}"


async def _get_or_create_secret(page) -> str:
    """Get or create secret key. Uses file on desktop, shared_preferences on Android."""
    global _cached_secret
    
    if _cached_secret:
        return _cached_secret
    
    if _is_android():
        # Android: Use shared_preferences (can't reliably write to filesystem)
        existing = await page.shared_preferences.get(_SECRET_KEY_NAME)
        if existing:
            _cached_secret = existing
            return existing
        
        secret = _generate_new_secret()
        await page.shared_preferences.set(_SECRET_KEY_NAME, secret)
        _cached_secret = secret
        return secret
    else:
        # Desktop: Use separate file
        key_path = _get_secret_key_path()
        
        if os.path.exists(key_path):
            try:
                with open(key_path, "r", encoding="utf-8") as f:
                    secret = f.read().strip()
                    _cached_secret = secret
                    return secret
            except Exception:
                pass
        
        secret = _generate_new_secret()
        os.makedirs(os.path.dirname(key_path), exist_ok=True)
        with open(key_path, "w", encoding="utf-8") as f:
            f.write(secret)
        
        _cached_secret = secret
        return secret


def _is_encrypted(value: str | None) -> bool:
    """Check if value has encryption prefix."""
    return bool(value and value.startswith(_ENCRYPTED_PREFIX))


async def save_credential(page, key_name: str, plaintext: str) -> None:
    """Encrypt and save credential."""
    if not plaintext:
        return
    secret = await _get_or_create_secret(page)
    encrypted = security.encrypt(plaintext, secret)
    await page.shared_preferences.set(key_name, f"{_ENCRYPTED_PREFIX}{encrypted}")


async def load_credential(page, key_name: str) -> tuple[str | None, bool]:
    """Load credential with auto-migration. Returns (value, decryption_failed)."""
    stored = await page.shared_preferences.get(key_name)
    if not stored:
        return None, False
    
    secret = await _get_or_create_secret(page)
    
    if _is_encrypted(stored):
        encrypted_data = stored[len(_ENCRYPTED_PREFIX):]
        try:
            return security.decrypt(encrypted_data, secret), False
        except Exception:
            await page.shared_preferences.remove(key_name)
            return None, True
    else:
        # Plaintext detected - auto-migrate
        await save_credential(page, key_name, stored)
        return stored, False


async def clear_credential(page, key_name: str) -> None:
    """Delete credential."""
    await page.shared_preferences.remove(key_name)


def delete_secret_key() -> bool:
    """Delete secret key file (for testing, desktop only)."""
    if _is_android():
        return False
    
    key_path = _get_secret_key_path()
    if os.path.exists(key_path):
        os.remove(key_path)
        global _cached_secret
        _cached_secret = None
        return True
    return False
