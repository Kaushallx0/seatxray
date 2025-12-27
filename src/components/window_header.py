import flet as ft
from theme import COLOR_BACKGROUND, COLOR_TEXT_PRIMARY

def WindowControls(page: ft.Page):
    # State for maximize icon
    max_icon_ref = ft.Ref[ft.IconButton]()

    def minimize(e):
        page.window.minimized = True
        page.update()

    def maximize(e):
        page.window.maximized = not page.window.maximized
        # Toggle icon based on state
        if max_icon_ref.current:
            if page.window.maximized:
                max_icon_ref.current.icon = ft.Icons.FILTER_NONE  # Restore icon
                max_icon_ref.current.icon_size = 12 # Visually smaller to balance complexity
            else:
                max_icon_ref.current.icon = ft.Icons.CROP_SQUARE  # Maximize icon
                max_icon_ref.current.icon_size = 14 # Standard size
        page.update()

    async def close_app(e):
        try:
            # Flet 1.0 での推奨されるウィンドウ終了処理
            await page.window.close()
        except Exception:
            # 万が一のフォールバック
            import sys
            sys.exit(0)

    # Style for buttons (Windows 11 Native Look)
    def button_style(icon, on_click, is_close=False, ref=None):
        hover_col = "#c42b1c" if is_close else "#10ffffff"
        
        return ft.IconButton(
            ref=ref,
            icon=icon,
            icon_size=14, # Revert to 14px as base size
            icon_color=ft.Colors.ON_SURFACE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=0),
                bgcolor={ft.ControlState.HOVERED: hover_col},
                padding=0,
            ),
            width=46,
            height=32,
            on_click=on_click,
            tooltip=None
        )

    return ft.Row(
        [
            button_style(ft.Icons.REMOVE, minimize),
            button_style(ft.Icons.CROP_SQUARE, maximize, ref=max_icon_ref),
            button_style(ft.Icons.CLOSE, close_app, is_close=True),
        ],
        spacing=0
    )

# Minimal Header: Just a drag area + window controls on the right
def CustomWindowHeader(page: ft.Page, title="SeatXray"):
    """
    main_single.py の MinimalWindowHeader と同等ですが、
    既存コードとの互換性のためにコンポーネント名を維持。
    """
    return ft.Container(
        content=ft.Row(
            [
                ft.WindowDragArea(
                    ft.Container(expand=True, bgcolor=ft.Colors.TRANSPARENT),
                    expand=True,
                ),
                WindowControls(page)
            ],
            spacing=0,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        bgcolor=ft.Colors.TRANSPARENT, # Blend with main content background
        height=32,
    )
