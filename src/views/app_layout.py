import flet as ft
import asyncio
from views.settings_view import SettingsContent
from views.search_view import SearchContent
from views.seatmap_content import SeatMapContent
from components.window_header import CustomWindowHeader
from theme import get_color_palette

class AppLayout(ft.View):
    def __init__(self, page: ft.Page, app_state, amadeus):
        # 1. State Init
        self.page_ref = page
        self.app_state = app_state
        self.amadeus = amadeus
        
        self.is_dark = (app_state.theme_mode == "DARK")
        self.palette = get_color_palette(self.is_dark)
        
        self.current_idx = 0
        self.search_input_state = {}
        
        # ビューのキャッシュ（タブ切り替え時に再作成しない）
        self._view_cache = {}
        self._in_seatmap = False  # 座席表を表示中かどうか
        
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
        return ft.NavigationRail(
            selected_index=self.current_idx, 
            label_type=ft.NavigationRailLabelType.ALL,
            leading=ft.Container(height=10),
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.SEARCH, 
                    selected_icon=ft.Icons.SEARCH, 
                    label="検索"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SETTINGS, 
                    selected_icon=ft.Icons.SETTINGS, 
                    label="設定"
                ),
            ],
            min_width=100,
            group_alignment=-0.9,
            bgcolor=self.palette["surface"],
            on_change=self._on_nav_change
        )

    def _build_bottom_bar(self):
        return ft.NavigationBar(
            selected_index=self.current_idx,
            destinations=[
                ft.NavigationDestination(
                    icon=ft.Icons.SEARCH, 
                    selected_icon=ft.Icons.SEARCH, 
                    label="検索"
                ),
                ft.NavigationDestination(
                    icon=ft.Icons.SETTINGS, 
                    selected_icon=ft.Icons.SETTINGS, 
                    label="設定"
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
        """検索画面から座席マップへ遷移（ナビゲーションバーは変更しない）"""
        self._in_seatmap = True
        # 座席表ビューをキャッシュ
        self._view_cache["seatmap"] = SeatMapContent(
            self.page_ref, 
            self.app_state, 
            self.amadeus,
            on_back=self._back_from_seatmap
        )
        self.content_area.content = self._view_cache["seatmap"]
        self.content_area.update()

    def _back_from_seatmap(self):
        """座席表から戻る"""
        self._in_seatmap = False
        self._set_view(0)

    def _set_view(self, idx):
        self.current_idx = idx
        self._save_search_state()
        
        if idx == 0:  # Search or Seatmap
            # 座席表を表示中ならキャッシュから復元
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
        # パレット更新
        self.is_dark = (self.app_state.theme_mode == "DARK")
        self.palette = get_color_palette(self.is_dark)
        
        # ページテーマを更新
        self.page_ref.theme_mode = ft.ThemeMode.DARK if self.is_dark else ft.ThemeMode.LIGHT
        self.page_ref.bgcolor = self.palette["bg"]
        self.page_ref.window.bgcolor = self.palette["bg"]
        
        # ナビゲーションを再作成
        if self.is_mobile:
             self.navigation_bar = self._build_bottom_bar()
        else:
            self.controls[0].controls[0] = self._build_sidebar()
            self.controls[0].controls[0].selected_index = self.current_idx
            # ディバイダーの色を更新
            self.controls[0].controls[1].color = self.palette["border"]
        
        # content_area の背景色を更新
        self.content_area.bgcolor = self.palette["bg"]
        
        # ビューキャッシュのパレットを更新（クリアせずに保持）
        for view in self._view_cache.values():
            if hasattr(view, 'update_palette'):
                view.update_palette(self.palette)
        
        # 現在のビュー（キャッシュ外の場合、例：Settings）のパレットを更新
        curr = self.content_area.content
        if curr and (curr not in self._view_cache.values()):
             if hasattr(curr, 'update_palette'):
                 curr.update_palette(self.palette)
        
        # 現在のビューのパレットを更新
        # if hasattr(self.content_area.content, 'update_palette'):
        #     self.content_area.content.update_palette(self.palette)
        
        # 全体を更新
        self.page_ref.update()
