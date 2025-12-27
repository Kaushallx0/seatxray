import flet as ft
import asyncio
import traceback
import warnings

# Suppress Flet deprecation warnings regarding shared_preferences
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*shared_preferences.*")

from services.amadeus_client import AmadeusClient
from theme import COLOR_BACKGROUND, get_color_palette
from components.window_header import CustomWindowHeader
from views.search_view import SearchView
from views.seatmap_view import SeatMapView
from views.settings_view import SettingsView

def build_app_layout(page: ft.Page, nav_rail: ft.NavigationRail, divider: ft.VerticalDivider, body_container: ft.Stack):
    """Layout construction helper"""
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    bg_start = COLOR_BACKGROUND if is_dark else "#f0f2f5"
    bg_end = "#1a1f2e" if is_dark else "#ffffff"

    return ft.Container(
         ft.Row(
            [
                nav_rail, 
                divider,
                ft.Container(
                    ft.Column([
                        CustomWindowHeader(page), 
                        ft.Container(body_container, expand=True, padding=20)
                    ], spacing=0),
                    expand=True
                )
            ],
            spacing=0, expand=True
         ),
         gradient=ft.LinearGradient(
            colors=[bg_start, bg_end],
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1)
         ), 
         expand=True
    )

async def main(page: ft.Page):
    # --- Critical Startup Settings (Flash Prevention) ---
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = COLOR_BACKGROUND
    page.window.bgcolor = COLOR_BACKGROUND
    page.padding = 0
    page.update() 
    
    page.title = "SeatXray"
    page.window.title_bar_hidden = True
    page.window.title_bar_buttons_hidden = True
    page.window.min_width = 1000
    page.window.min_height = 800

    # --- Global State ---
    saved_id = await page.shared_preferences.get("amadeus_client_id")
    saved_secret = await page.shared_preferences.get("amadeus_client_secret")
    amadeus = AmadeusClient(saved_id, saved_secret, page=page)
    
    # --- Navigation Logic ---
    
    # We use a Stack to keep all views in memory (persistent state)
    # 0: SearchView, 1: SeatMapView, 2: SettingsView, 3: SavedView
    views_stack = ft.Stack(expand=True)
    seat_map_active = False # Tracks if we are "in" the seatmap sub-view
    
    # Placeholders for view instances
    search_view: SearchView = None
    seat_map_view: SeatMapView = None
    settings_view: SettingsView = None
    saved_view_placeholder = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CONSTRUCTION, size=64, color="grey"),
            ft.Text("保存済み機能は準備中です", size=20, color="grey")
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
        alignment=ft.Alignment(0, 0),
        visible=False
    )

    # --- Nav Functions (Forward Declared) ---
    
    async def nav_to_search(e=None):
        # Resume SeatMap if it was active
        if seat_map_active:
            _switch_tab(seat_map_view)
        else:
            _switch_tab(search_view)

    async def nav_to_settings(e=None):
        await settings_view.refresh_stats()
        _switch_tab(settings_view)

    async def nav_to_saved(e=None):
        _switch_tab(saved_view_placeholder)

    async def nav_to_seatmap(offers):
        nonlocal seat_map_active
        seat_map_active = True
        # 1. Show SeatMapView (so loader is visible)
        _switch_tab(seat_map_view)
        # 2. Load Data
        await seat_map_view.load_seatmap(offers)
        
    async def exit_seatmap(e=None):
        nonlocal seat_map_active
        seat_map_active = False
        await nav_to_search()

    def _switch_tab(target_control):
        # Hide all, Show target
        for v in [search_view, seat_map_view, settings_view, saved_view_placeholder]:
            v.visible = (v == target_control)
        page.update()

    async def handle_theme_change(e):
        if isinstance(e, str): is_dark = (e == "DARK")
        else: is_dark = e.control.value
        
        page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
        mode_str = "DARK" if is_dark else "LIGHT"
        
        update_theme_visuals(is_dark)
        await page.shared_preferences.set("theme_mode", mode_str)

        # Propagate to all views
        search_view.update_theme_mode(is_dark, should_update=False)
        seat_map_view.update_theme_mode(is_dark)
        settings_view.update_theme_mode(is_dark)
        
        page.update()

    # --- Init Views ---
    search_view = SearchView(page, amadeus, on_offer_select=nav_to_seatmap, visible=True)
    
    seat_map_view = SeatMapView(page, amadeus, on_back=exit_seatmap)
    seat_map_view.visible = False # Hidden by default
    
    sid = await page.shared_preferences.get("amadeus_client_id")
    ssec = await page.shared_preferences.get("amadeus_client_secret")
    settings_view = SettingsView(page, amadeus, sid, ssec, on_theme_change=handle_theme_change, visible=False)
    
    views_stack.controls = [search_view, seat_map_view, settings_view, saved_view_placeholder]

    # --- Sidebar ---
    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.SEARCH, selected_icon=ft.Icons.SEARCH, label="検索"),
            ft.NavigationRailDestination(icon=ft.Icons.AIRLINE_SEAT_RECLINE_EXTRA, selected_icon=ft.Icons.AIRLINE_SEAT_RECLINE_EXTRA, label="保存済み"),
            ft.NavigationRailDestination(icon=ft.Icons.SETTINGS, selected_icon=ft.Icons.SETTINGS, label="設定"),
        ],
        min_width=100, group_alignment=-0.9,
    )

    def on_nav_change(e):
        idx = e.control.selected_index
        if idx == 0: asyncio.create_task(nav_to_search())
        elif idx == 1: asyncio.create_task(nav_to_saved())
        elif idx == 2: asyncio.create_task(nav_to_settings())

    nav_rail.on_change = on_nav_change
    
    divider = ft.VerticalDivider(width=1, color="white10")

    # --- Dynamic Theme Updater ---
    def update_theme_visuals(is_dark):
        p = get_color_palette(is_dark)
        main_layout.gradient.colors = [p["bg"], "#1a1f2e" if is_dark else "#ffffff"]
        nav_rail.bgcolor = p["surface"]
        divider.color = p["border"]
        page.bgcolor = p["bg"]
        page.window.bgcolor = p["bg"]

    # --- Bootstrap ---
    main_layout = build_app_layout(page, nav_rail, divider, views_stack)
    page.add(main_layout)
    
    # Final Theme Init
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    update_theme_visuals(is_dark)
    
    # Sync initial state
    search_view.update_theme_mode(is_dark, should_update=False)
    settings_view.update_theme_mode(is_dark) 
    
    page.update()

if __name__ == "__main__":
    ft.run(main)
