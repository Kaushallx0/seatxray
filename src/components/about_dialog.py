# Copyright (c) 2026 SeatXray Developers
# Licensed under the terms of the GNU Affero General Public License (AGPL) version 3.
# See LICENSE file in the project root for details.

"""About Dialog. Shows app info and license."""

import flet as ft
import os
import platform
from theme import get_color_palette, COLOR_ACCENT, glass_style
from utils.i18n import TranslationService

class AboutDialog(ft.Container):
    """
    Custom "About" dialog for SeatXray
    """
    def __init__(self, page: ft.Page, on_close: callable, palette: dict, is_mobile: bool = False):
        super().__init__()
        self.i18n = TranslationService.get_instance()
        self._page_ref = page
        self.on_close_callback = on_close
        self.palette = palette
        self.is_mobile = is_mobile
        
        # Design settings
        is_dark = (palette["bg"] != "#f0f2f5")
        style = glass_style(opacity=0.95, blur=20, dark=is_dark, surface_color=palette["surface"])
        
        self.bgcolor = style["bgcolor"]
        self.blur = style["blur"]
        self.border = style["border"]
        self.border_radius = ft.border_radius.all(16)
        self.padding = 20 if is_mobile else 30
        # Responsive size: mobile uses smaller dimensions
        self.width = 340 if is_mobile else 500
        self.height = 500 if is_mobile else 600
        self.shadow = ft.BoxShadow(
            blur_radius=50,
            color=ft.Colors.with_opacity(0.5, "black")
        )
        
        self.content = self._build_content()
        
    def _build_content(self):
        p = self.palette
        tr = self.i18n.tr
        
        # App Logo (Text based)
        # Header info (Placed inside scroll area)
        header_items = [
            ft.Image(src="/icon.png", width=64, height=64),
            ft.Text(tr("app_title"), size=32, weight="bold", color=p["text"]),
            ft.Text(tr("about.version"), size=16, color=p["text_secondary"]),
            ft.Row([
                ft.Text(tr("about.license_label"), size=14, color=p["text_secondary"]),
                ft.IconButton(
                    icon=ft.Icons.DESCRIPTION_OUTLINED,
                    icon_size=18,
                    tooltip=tr("about.tooltip_license"),
                    icon_color=COLOR_ACCENT,
                    on_click=self._show_license_viewer,
                    style=ft.ButtonStyle(padding=0)
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=10), # Spacer
        ]
        
        # License and Credit info
        credits = [
            self._build_section(tr("about.section_tech"), [
                "Amadeus for Developers",
                "Flet (Flutter) - Apache-2.0 License",
            ]),
            self._build_section(tr("about.section_libs"), [
                f"Python {platform.python_version()} - PSF License",
                "httpx - BSD-3-Clause License",
                "Pillow - HPND License (Standard PIL License)",
                "aiofiles - Apache-2.0 License",
                "cryptography - Apache-2.0 / BSD-3-Clause License",
                "toml - MIT License",
            ]),
            self._build_section(tr("about.section_legal"), [
                tr("about.legal_text"),
                tr("about.warranty_disclaimer"),
            ])
        ]
        
        # Integrate into one column
        all_content = ft.Column(
            header_items + credits,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            spacing=20
        )
        
        # Footer (Copyright & Close)
        footer = ft.Column([
            ft.Divider(color=p["divider"]),
            ft.Container(height=5),
            ft.ElevatedButton(
                tr("common.close"),
                on_click=self._close,
                bgcolor=COLOR_ACCENT,
                color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                height=45,
                width=200
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)
        
        return ft.Column([
            ft.Container(
                content=ft.IconButton(ft.Icons.CLOSE, on_click=self._close, icon_color=p["text_secondary"]),
                alignment=ft.Alignment(1.0, -1.0)
            ),
            all_content, # Integrated scroll area
            ft.Container(height=10),
            footer
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)

    def _show_license_viewer(self, e):
        self._license_overlay = ft.Stack([
            ft.GestureDetector(
                content=ft.Container(expand=True, bgcolor=ft.Colors.with_opacity(0.6, "black")),
                on_tap=lambda _: self._hide_license_viewer()
            ),
            ft.Container(
                content=LicenseViewer(self._page_ref, self._hide_license_viewer, self.palette, is_mobile=self.is_mobile),
                alignment=ft.Alignment(0, 0)
            )
        ], expand=True)
        
        self._page_ref.overlay.append(self._license_overlay)
        self._page_ref.update()

    def _hide_license_viewer(self, e=None):
        if hasattr(self, '_license_overlay') and self._license_overlay in self._page_ref.overlay:
            self._page_ref.overlay.remove(self._license_overlay)
            self._page_ref.update()

    def _build_section(self, title, items):
        p = self.palette
        row_items = [
            ft.Text(title, size=14, weight="bold", color=COLOR_ACCENT),
            ft.Container(height=5)
        ]
        for item in items:
            row_items.append(ft.Text(f"• {item}", size=13, color=p["text"]))
            
        return ft.Column(row_items, spacing=2)

    def _close(self, e):
        if self.on_close_callback:
            self.on_close_callback()

class LicenseViewer(ft.Container):
    """Dialog displaying full license text"""
    def __init__(self, page: ft.Page, on_close: callable, palette: dict, is_mobile: bool = False):
        super().__init__()
        self.i18n = TranslationService.get_instance()
        self._page_ref = page
        self.on_close = on_close
        self.palette = palette
        self.is_mobile = is_mobile
        
        # Design settings
        is_dark = (palette["bg"] != "#f0f2f5")
        style = glass_style(opacity=0.98, blur=20, dark=is_dark, surface_color=palette["surface"])
        
        self.bgcolor = style["bgcolor"]
        self.blur = style["blur"]
        self.border = style["border"]
        self.border_radius = ft.border_radius.all(16)
        self.padding = 15 if is_mobile else 20
        self.item_padding = 10
        # Responsive size: mobile uses smaller dimensions
        self.width = 340 if is_mobile else 520
        self.height = 550 if is_mobile else 700
        self.shadow = ft.BoxShadow(blur_radius=50, color=ft.Colors.with_opacity(0.5, "black"))
        
        self.content = self._build_content()
        self._load_license_text()

    def _build_content(self):
        p = self.palette
        
        self.text_view = ft.Text(
            self.i18n.tr("common.loading"), 
            color=p["text"], 
            size=12, 
            font_family="Consolas, monospace",
            selectable=True
        )
        
        return ft.Column([
            ft.Row([
                ft.Text(
                    "GNU Affero General Public License v3.0", 
                    size=16 if self.is_mobile else 18, 
                    weight="bold", 
                    color=p["text"],
                    expand=True,  # Allow expanding/wrapping
                    no_wrap=False  # Allow wrapping
                ),
                # ft.Container(expand=True),  # Removed spacer since Text expands
                ft.IconButton(ft.Icons.CLOSE, on_click=lambda e: self.on_close(), icon_color=p["text_secondary"])
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Divider(color=p["divider"]),
            ft.Container(
                content=ft.Column([self.text_view], scroll=ft.ScrollMode.ALWAYS),
                expand=True,
                bgcolor=ft.Colors.with_opacity(0.05, "black") if p["bg"] == "#f0f2f5" else ft.Colors.with_opacity(0.2, "black"),
                border_radius=8,
                padding=10
            )
        ], spacing=10)

    def _load_license_text(self):
        try:
            # Resolve path relative to this file to find src/assets/LICENSE
            # This file is in src/components, so ../assets/LICENSE points to src/assets/LICENSE
            current_dir = os.path.dirname(os.path.abspath(__file__))
            license_path = os.path.join(current_dir, "..", "assets", "LICENSE")
            
            with open(license_path, "r", encoding="utf-8") as f:
                self.text_view.value = f.read()
        except Exception as e:
            self.text_view.value = f"{self.i18n.tr('common.error')}:\n{e}"
            self.text_view.color = "red"
        if self._page_ref:
             self._page_ref.update()

