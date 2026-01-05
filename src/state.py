
# Copyright (c) 2026 SeatXray Developers
# Licensed under the terms of the GNU Affero General Public License (AGPL) version 3.
# See LICENSE file in the project root for details.

"""AppState. Manages shared application state."""

import flet as ft
import time

class AppState:
    """
    Class managing the shared state of the entire application.
    All data that should be persisted across screen transitions (View recreation) should be placed here.
    """
    def __init__(self):
        # Search results cache (to prevent re-search when going back)
        self.offers: list = []
        
        # Selected flight (for detail screen)
        # Structure like { "offers": [...], "identity": ..., "route": ... }
        self.selected_offer_group: dict = None
        
        # Theme setting (DARK/LIGHT)
        self.theme_mode: str = "DARK"
        
        # Locale and Currency settings
        self.locale: str = "ja"  # Default: Japanese
        self.currency: str = "JPY"  # Default: Japanese Yen
        
        # Seat map cache {key: (data, timestamp, ttl)}
        # Volatile: expires based on Cache-Control header or max 6 hours
        self._seatmap_cache: dict = {}
        self._cache_ttl_default = 6 * 60 * 60  # 6 hours (fallback)
    
    def get_seatmap_cache(self, key: str):
        """Get seat data from cache. Returns None if expired."""
        if not key or key not in self._seatmap_cache:
            return None
        
        data, timestamp, ttl = self._seatmap_cache[key]
        if time.time() - timestamp > ttl:
            # Expired - delete and return None
            del self._seatmap_cache[key]
            return None
        
        return data
    
    def set_seatmap_cache(self, key: str, data, ttl: int = None):
        """Save seat data to cache"""
        if key:
            cache_ttl = ttl if ttl else self._cache_ttl_default
            self._seatmap_cache[key] = (data, time.time(), cache_ttl)
    
    def clear_expired_cache(self):
        """Clear expired cache"""
        now = time.time()
        expired_keys = [
            k for k, (_, ts, ttl) in self._seatmap_cache.items()
            if now - ts > ttl
        ]
        for k in expired_keys:
            del self._seatmap_cache[k]
