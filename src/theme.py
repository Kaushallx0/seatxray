# --- Palette & Theme System ---
import flet as ft

COLOR_BACKGROUND = "#16191d"
COLOR_ACCENT = "#6d4aff"
COLOR_TEXT_PRIMARY = "white"
COLOR_DANGER = "#ff4d4f"
COLOR_SUCCESS = "#00b96b"

def get_color_palette(is_dark: bool):
    """Legacy Palette Helper - migrating to ft.Theme where possible"""
    return {
        "text": "white" if is_dark else "#1a1f2e",
        "text_secondary": "grey" if is_dark else "#666666",
        "bg": COLOR_BACKGROUND if is_dark else "#f0f2f5",
        "surface": "#1e2229" if is_dark else "#ffffff",
        "surface_container": "#2c303a" if is_dark else "#f5f5f5",
        "surface_container_low": "#252830" if is_dark else "#ffffff",
        "border": "white12" if is_dark else "black12",
        "border_opacity": ft.Colors.with_opacity(0.1, "white" if is_dark else "black"),
        "accent": COLOR_ACCENT
    }

def glass_style(opacity=0.1, blur=10, dark=False, surface_color=None):
    """Glassmorphism スタイル。dark=True でダークモード用の暗い背景。"""
    # Dynamic base color calculation
    if surface_color:
        base_color = surface_color
    else:
        base_color = ft.Colors.BLACK if dark else ft.Colors.WHITE
        
    border_color = ft.Colors.WHITE if dark else ft.Colors.BLACK
    
    return {
        "bgcolor": ft.Colors.with_opacity(opacity, base_color),
        "blur": ft.Blur(blur, blur),
        "border": ft.Border.all(1, ft.Colors.with_opacity(0.10, border_color)), # Generic opacity
        "border_radius": ft.BorderRadius.all(16),
        "padding": 20,
    }

    return {
        "text": "#ffffff" if is_dark else "#16191d",
        "text_secondary": "#8b949e" if is_dark else "#57606a",
        "bg": COLOR_BACKGROUND if is_dark else "#f0f2f5",
        "surface": COLOR_SURFACE if is_dark else "#ffffff",
        "surface_container": "#22272e" if is_dark else "#ffffff",
        "surface_container_low": "#2d333b" if is_dark else "#f3f4f6",
        "border": "white" if is_dark else "black", # Stronger contrast for light mode
        "border_opacity": "white10" if is_dark else "black12",
        "accent": COLOR_ACCENT,
    }

def get_app_theme():
    return ft.Theme(
        color_scheme_seed=COLOR_PRIMARY,
        font_family="Yu Gothic UI",
        use_material3=True,
        page_transitions=ft.PageTransitionsTheme(
            windows=ft.PageTransitionTheme.CUPERTINO,
            android=ft.PageTransitionTheme.ZOOM,
            ios=ft.PageTransitionTheme.CUPERTINO,
        ),
    )
