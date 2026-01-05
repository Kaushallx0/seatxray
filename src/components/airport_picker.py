# Copyright (c) 2026 SeatXray Developers
# Licensed under the terms of the GNU Affero General Public License (AGPL) version 3.
# See LICENSE file in the project root for details.

"""Airport Picker. Autocomplete airport search."""

import flet as ft
from utils.i18n import TranslationService

class AirportPicker(ft.Container):
    def __init__(self, label_key, initial_value, palette, width=150):
        super().__init__()
        self.i18n = TranslationService.get_instance()
        self.label_key = label_key # Store key, not translated text
        self.initial_value = initial_value
        self.palette = palette
        self.width = width
        self.airports_data = [] # Will be fetched from service
        self.filtered_data = []
        
        # State
        self.value = initial_value
        
        # UI Components
        self.search_anchor = ft.SearchAnchor(
            view_hint_text=self.i18n.tr("search.hint_airport"),
            view_elevation=4,
            width=width,
            header_height=60,
            view_height=400,
            divider_color=palette["border"],
            view_bgcolor=palette["surface"],
            bar_bgcolor=palette["surface_container"],
            bar_overlay_color=ft.Colors.with_opacity(0.1, palette["accent"]),
            bar_hint_text=self.i18n.tr(label_key),
        )
        
        # Set up event handlers
        self.search_anchor.handle_change = self._handle_search_change
        self.search_anchor.handle_tap = self._handle_tap
        self.search_anchor.handle_submit = self._handle_submit

        # Initialize content
        self.content = self.search_anchor
        
        # Set initial label
        self._update_bar_text(initial_value)

        # Load Data from Service (Immediate, as it's already loaded in main)
        self.airports_data = self.i18n.get_airports()
        self.filtered_data = self.airports_data[:50]

    def _update_bar_text(self, text):
        icon = ft.Icons.FLIGHT_TAKEOFF if "origin" in self.label_key else ft.Icons.FLIGHT_LAND
        self.search_anchor.bar_leading = ft.Icon(icon, color=self.palette["text_secondary"])
        self.search_anchor.value = text

    async def _handle_tap(self, e):
        await self.search_anchor.open_view_async()

    async def _handle_search_change(self, e):
        keyword = e.data.lower().strip()
        if not keyword:
            self.filtered_data = self.airports_data[:50]
        else:
            self.filtered_data = [
                a for a in self.airports_data 
                if keyword in a["iata"].lower() 
                or keyword in a["city"].lower() 
                or keyword in a["name"].lower()
            ][:50]
        
        self.search_anchor.controls.clear()
        
        for a in self.filtered_data:
            self.search_anchor.controls.append(
                ft.ListTile(
                    title=ft.Text(f"{a['city']} ({a['iata']})", color=self.palette["text"]),
                    subtitle=ft.Text(a['name'], color=self.palette["text_secondary"]),
                    on_click=lambda e, code=a['iata']: self._select_airport(code)
                )
            )
        self.search_anchor.update()

    async def _handle_submit(self, e):
        self.value = e.data.upper()
        self.search_anchor.close_view()
        self.update()

    async def _select_airport(self, code):
        self.value = code
        self.search_anchor.value = code
        await self.search_anchor.close_view_async()
        self.update()
