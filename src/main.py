# Copyright (c) 2026 SeatXray Developers
# Licensed under the terms of the GNU Affero General Public License (AGPL) version 3.
# See LICENSE file in the project root for details.

"""SeatXray Entry Point. Manages lifecycle and routing."""

import sys
import os

# --- HOTFIX: Repair file structure on Android/Flet debug ---
# Flet debug on Windows packages files with backslashes in filenames
# instead of creating directories. We fix this at runtime before imports.
if not sys.platform.startswith('win'):
    for filename in os.listdir('.'):
        if '\\' in filename:
            try:
                proper_path = filename.replace('\\', '/')
                directory = os.path.dirname(proper_path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                os.rename(filename, proper_path)
            except Exception:
                pass

import flet as ft
import warnings
from state import AppState
from services.amadeus_client import AmadeusClient
from views.seatmap_view import SeatMapView
from views.app_layout import AppLayout
from theme import COLOR_BACKGROUND

# Suppress Flet deprecation warnings regarding shared_preferences
warnings.filterwarnings("ignore", category=DeprecationWarning)

async def main(page: ft.Page):
    # --- 1. Platform Detection ---
    is_mobile = page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]
    print(f"[Platform] Detected: {page.platform}, is_mobile={is_mobile}")
    
    # --- 2. Global Setup ---
    from utils.i18n import TranslationService
    i18n = TranslationService.get_instance()
    await i18n.init_locale(page)
    
    page.title = i18n.tr("app_title")
    
    # Platform-specific window settings
    if is_mobile:
        # Mobile: Standard window, no frameless
        page.bgcolor = COLOR_BACKGROUND
        page.padding = 0
    else:
        # Desktop: Frameless window with custom title bar
        page.window.min_width = 1000
        page.window.min_height = 800
        page.window.frameless = True
        page.window.title_bar_hidden = True
        page.window.title_bar_buttons_hidden = True
        page.bgcolor = ft.Colors.TRANSPARENT
        page.window.bgcolor = ft.Colors.TRANSPARENT
    
    # Default Theme
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = COLOR_BACKGROUND
    page.window.bgcolor = COLOR_BACKGROUND
    page.padding = 0

    # Fonts configuration
    page.fonts = {
        "NotoSansJP": "assets/fonts/NotoSansJP-Regular.ttf",
        "NotoSansJP-Bold": "assets/fonts/NotoSansJP-Bold.ttf"
    }
    
    # Apply font to theme
    page.theme = ft.Theme(font_family="NotoSansJP")
    
    # --- 3. State Initialization ---
    app_state = AppState()
    
    # Load Theme pref
    saved_theme = await page.shared_preferences.get("theme_mode")
    if saved_theme:
        app_state.theme_mode = saved_theme
        page.theme_mode = ft.ThemeMode.DARK if saved_theme == "DARK" else ft.ThemeMode.LIGHT
    
    # Load Locale and Currency preferences
    from utils.i18n import get_default_currency
    saved_locale = await page.shared_preferences.get("seatxray_locale")
    saved_currency = await page.shared_preferences.get("seatxray_currency")
    
    if saved_locale:
        app_state.locale = saved_locale
    else:
        app_state.locale = i18n.current_locale
    
    if saved_currency:
        app_state.currency = saved_currency
    else:
        app_state.currency = get_default_currency(app_state.locale)
    
    # Load Credentials for Global Service
    key = await page.shared_preferences.get("amadeus_api_key")
    secret = await page.shared_preferences.get("amadeus_api_secret")
    
    # Global Service (Single Instance)
    amadeus = AmadeusClient(key, secret, page=page)
    
    # --- 4. Platform-Specific Routing ---
    
    if is_mobile:
        # ===== MOBILE: Use page.add() based approach =====
        # On Android, page.views (View objects) don't render properly.
        # We create AppLayout but add its CONTROLS to page, not the View itself.
        
        app_layout = AppLayout(page, app_state, amadeus)
        
        # Extract controls from the View and add them directly to page
        # Also set navigation_bar if present
        for control in app_layout.controls:
            page.add(control)
        
        if app_layout.navigation_bar:
            page.navigation_bar = app_layout.navigation_bar
        
        page.update()
        
    else:
        # ===== DESKTOP: Use page.views based approach =====
        # This works well with frameless windows and custom title bars.
        
        def route_change(route):
            page.views.clear()
            
            try:
                if page.route == "/seatmap":
                    page.views.append(SeatMapView(page, app_state, amadeus))
                else:
                    page.views.append(AppLayout(page, app_state, amadeus))
                
                page.update()
            except Exception as e:
                print(f"CRITICAL ERROR in route_change: {e}")
                import traceback
                traceback.print_exc()
        
        def view_pop(view):
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)
        
        page.on_route_change = route_change
        page.on_view_pop = view_pop
        
        # Trigger initial route
        page.go("/")
        
        # Force initial render
        route_change(None)
        
        # Show window after initialization
        page.window.visible = True
        page.update()

# Export for app reload functionality
main_app = main

# Entry point guard: only run ft.app() on first module load, not on re-import
# Check if we're being run as the main entry point (not imported for reload)
import sys
if "flet.app" not in sys.modules.get("__main__", "").__class__.__name__:
    # Only start if not already running
    if not hasattr(sys, '_seatxray_started'):
        sys._seatxray_started = True
        ft.app(target=main, assets_dir="assets")
