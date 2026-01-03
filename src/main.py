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
    # --- 1. Global Setup ---
    page.title = "SeatXray"
    page.window.min_width = 1000
    page.window.min_height = 800
    
    
    # Hide native title bar (we use CustomWindowHeader in views)
    page.window.title_bar_hidden = True
    page.window.title_bar_buttons_hidden = True # Custom buttons in Header
    
    # Default Theme
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = COLOR_BACKGROUND
    page.window.bgcolor = COLOR_BACKGROUND
    page.padding = 0
    
    # --- 2. State Initialization ---
    app_state = AppState()
    
    # Load Theme pref
    saved_theme = await page.shared_preferences.get("theme_mode")
    if saved_theme:
        app_state.theme_mode = saved_theme
        page.theme_mode = ft.ThemeMode.DARK if saved_theme == "DARK" else ft.ThemeMode.LIGHT
    
    # Load Credentials for Global Service
    key = await page.shared_preferences.get("amadeus_api_key")
    secret = await page.shared_preferences.get("amadeus_api_secret")
    
    # Global Service (Single Instance)
    amadeus = AmadeusClient(key, secret, page=page)
    
    # --- 3. Routing Logic ---
    
    def route_change(route):
        page.views.clear()
        
        try:
            if page.route == "/seatmap":
                 page.views.append(
                    SeatMapView(page, app_state, amadeus)
                 )
            else:
                 # Main App Shell (handles Search/Settings internally)
                 layout = AppLayout(page, app_state, amadeus)
                 page.views.append(layout)
            
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
    
    # --- 4. Launch ---
    # Trigger initial route
    print("DEBUG: Executing page.go('/')")
    page.go("/")
    print("DEBUG: page.go('/') executed")

    
    # Force initial render manually because page.go("/") might not trigger if already at "/"
    route_change(None)

    # Ensure window is visible
    page.window.visible = True

if __name__ == "__main__":
    ft.run(main)
