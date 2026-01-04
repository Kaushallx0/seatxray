import flet as ft
import asyncio
from views.settings_view import SettingsContent
from views.search_view import SearchContent
from views.seatmap_content import SeatMapContent
from components.window_header import CustomWindowHeader
from theme import get_color_palette
from utils.i18n import TranslationService

class AppLayout(ft.View):
    def __init__(self, page: ft.Page, app_state, amadeus):
        # 1. State Init
        self.i18n = TranslationService.get_instance()
        self.page_ref = page
        self.app_state = app_state
        self.amadeus = amadeus
        
        self.is_dark = (app_state.theme_mode == "DARK")
        self.palette = get_color_palette(self.is_dark)
        
        self.current_idx = 0
        self.search_input_state = {}
        
        # View cache (prevent recreating views on tab switch)
        self._view_cache = {}
        self._in_seatmap = False  # Whether seatmap is currently displayed
        
        # 2. Controls Init
        self.content_area = ft.Container(expand=True, bgcolor=self.palette["bg"])
        print(f"DEBUG: AppLayout content_area initialized with bgcolor={self.palette['bg']}")
        self.nav_rail = self._build_sidebar()
        
        # 2b. Platform Check
        self.is_mobile = page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]
        
        # 3. Super Init
        super().__init__(
            route="/", 
            padding=0,
        )

        if self.is_mobile:
            # === Mobile Layout ===
            self.navigation_bar = self._build_bottom_bar()
            self.controls = [
                ft.SafeArea(self.content_area, expand=True)
            ]
        else:
            # === Desktop Layout ===
            self.nav_rail = self._build_sidebar()
            self.controls = [
                ft.Row(
                    [
                        self.nav_rail,
                        ft.VerticalDivider(width=1, color=self.palette["border"]),
                        ft.Column([
                            CustomWindowHeader(page),
                            self.content_area
                        ], spacing=0, expand=True)
                    ],
                    expand=True,
                    spacing=0
                ) 
            ]
        
        # 4. Set Initial Content (Do not call update() in init!)
        self._set_initial_view()

    def _set_initial_view(self):
        self.current_idx = 0
        self._set_view(0)

    def _build_sidebar(self):
        tr = self.i18n.tr
        return ft.NavigationRail(
            selected_index=self.current_idx, 
            label_type=ft.NavigationRailLabelType.ALL,
            leading=ft.Container(height=10),
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.SEARCH, 
                    selected_icon=ft.Icons.SEARCH, 
                    label=tr("nav.search")
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SETTINGS, 
                    selected_icon=ft.Icons.SETTINGS, 
                    label=tr("nav.settings")
                ),
            ],
            min_width=100,
            group_alignment=-0.9,
            bgcolor=self.palette["surface"],
            on_change=self._on_nav_change
        )

    def _build_bottom_bar(self):
        tr = self.i18n.tr
        return ft.NavigationBar(
            selected_index=self.current_idx,
            destinations=[
                ft.NavigationDestination(
                    icon=ft.Icons.SEARCH, 
                    selected_icon=ft.Icons.SEARCH, 
                    label=tr("nav.search")
                ),
                ft.NavigationDestination(
                    icon=ft.Icons.SETTINGS, 
                    selected_icon=ft.Icons.SETTINGS, 
                    label=tr("nav.settings")
                ),
            ],
            bgcolor=self.palette["surface"],
            on_change=self._on_nav_change
        )

    def _on_nav_change(self, e):
        idx = e.control.selected_index
        self._set_view(idx)

    def _save_search_state(self):
        # If current content is Search, save state
        if isinstance(self.content_area.content, SearchContent):
            self.search_input_state = self.content_area.content.get_input_state()

    def _navigate_to_seatmap(self, offers):
        """Navigate from Search to SeatMap (Navigation bar remains unchanged)"""
        self._in_seatmap = True
        # Cache the seatmap view
        self._view_cache["seatmap"] = SeatMapContent(
            self.page_ref, 
            self.app_state, 
            self.amadeus,
            on_back=self._back_from_seatmap
        )
        self.content_area.content = self._view_cache["seatmap"]
        self.content_area.update()

    def _back_from_seatmap(self):
        """Return from SeatMap"""
        self._in_seatmap = False
        self._set_view(0)

    def _set_view(self, idx):
        self.current_idx = idx
        self._save_search_state()
        
        if idx == 0:  # Search or Seatmap
            # specific logic to restore state if needed
            if self._in_seatmap and "seatmap" in self._view_cache:
                self.content_area.content = self._view_cache["seatmap"]
            else:
                if 0 not in self._view_cache:
                    self._view_cache[0] = SearchContent(
                        self.page_ref, 
                        self.app_state, 
                        self.amadeus,
                        on_navigate_seatmap=self._navigate_to_seatmap,
                        input_state=self.search_input_state
                    )
                self.content_area.content = self._view_cache[0]
            
        elif idx == 1:  # Settings
            self.content_area.content = SettingsContent(
                self.page_ref, 
                self.app_state, 
                self.amadeus,
                on_theme_toggle=self._rebuild_app
            )
        
        try:
            self.content_area.update()
        except:
            pass

    async def _rebuild_app(self):
        # Update Palette
        self.is_dark = (self.app_state.theme_mode == "DARK")
        self.palette = get_color_palette(self.is_dark)
        
        # Update page theme
        self.page_ref.theme_mode = ft.ThemeMode.DARK if self.is_dark else ft.ThemeMode.LIGHT
        self.page_ref.bgcolor = self.palette["bg"]
        self.page_ref.window.bgcolor = self.palette["bg"]
        
        # Recreate navigation
        if self.is_mobile:
             self.navigation_bar = self._build_bottom_bar()
        else:
            self.controls[0].controls[0] = self._build_sidebar()
            self.controls[0].controls[0].selected_index = self.current_idx
            # Update divider color
            self.controls[0].controls[1].color = self.palette["border"]
        
        # Update content_area background color
        self.content_area.bgcolor = self.palette["bg"]
        
        # Update palette in view cache (keep without clearing)
        for view in self._view_cache.values():
            if hasattr(view, 'update_palette'):
                view.update_palette(self.palette)
        
        # Update palette for current view (if outside cache, e.g. Settings)
        curr = self.content_area.content
        if curr and (curr not in self._view_cache.values()):
             if hasattr(curr, 'update_palette'):
                 curr.update_palette(self.palette)
        
        # Update palette for current view
        # if hasattr(self.content_area.content, 'update_palette'):
        #     self.content_area.content.update_palette(self.palette)
        
        # Update everything
        self.page_ref.update()
