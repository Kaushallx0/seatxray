import flet as ft
import asyncio


class WindowControls(ft.Row):
    """
    Windows 11 スタイルのウィンドウコントロール
    全てのボタンを TextButton で統一
    """
    def __init__(self, page: ft.Page):
        self.page_ref = page
        self.max_icon_ref = ft.Ref[ft.Text]()
        
        super().__init__(
            controls=[
                self._create_btn("\uE921", self._minimize, "最小化"),
                self._create_btn("\uE922", self._maximize, "最大化", icon_ref=self.max_icon_ref),
                self._create_btn("\uE8BB", self._close_app, "閉じる", is_close=True),
            ],
            spacing=0,
        )

    def _create_btn(self, glyph: str, on_click, tooltip: str = "", icon_ref=None, is_close=False):
        """全てのボタンを TextButton で作成"""
        # 閉じるボタンは赤いオーバーレイ、それ以外は標準
        overlay = "#c42b1c" if is_close else ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)
        
        return ft.TextButton(
            content=ft.Container(
                content=ft.Text(
                    ref=icon_ref,
                    value=glyph,
                    font_family="Segoe Fluent Icons",
                    size=10,
                    text_align=ft.TextAlign.CENTER,
                ),
                width=46,
                height=32,
                alignment=ft.Alignment(0, 0),
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=0),
                padding=0,
                overlay_color=overlay,
            ),
            on_click=on_click,
            tooltip=tooltip,
        )

    def _minimize(self, e):
        self.page_ref.window.minimized = True
        self.page_ref.update()

    def _maximize(self, e):
        self.page_ref.window.maximized = not self.page_ref.window.maximized
        if self.page_ref.window.maximized:
            self.max_icon_ref.current.value = "\uE923"
        else:
            self.max_icon_ref.current.value = "\uE922"
        self.max_icon_ref.current.update()

    async def _close_app(self, e):
        await self.page_ref.window.close()


class CustomWindowHeader(ft.Stack):
    """
    カスタムウィンドウヘッダー
    Stack レイアウトで WindowDragArea の上に WindowControls を配置
    """
    def __init__(self, page: ft.Page):
        drag_area = ft.WindowDragArea(
            content=ft.Container(
                height=32,
                bgcolor=ft.Colors.TRANSPARENT,
            ),
            expand=True,
        )
        
        controls_container = ft.Container(
            content=WindowControls(page),
            right=0,
            top=0,
        )
        
        super().__init__(
            controls=[drag_area, controls_container],
            height=32,
        )
