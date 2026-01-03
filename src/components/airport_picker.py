import flet as ft
import json
import asyncio
import aiofiles
import os

class AirportPicker(ft.Container):
    def __init__(self, label, initial_value, palette, width=150):
        super().__init__()
        self.label = label
        self.initial_value = initial_value
        self.palette = palette
        self.width = width
        self.airports_data = []
        self.filtered_data = []
        
        # State
        self.value = initial_value
        
        # UI Components
        self.search_anchor = ft.SearchAnchor(
            view_hint_text="空港名、都市名、IATAコードで検索...",
            view_elevation=4,
            width=width,
            header_height=60,
            view_height=400,
            divider_color=palette["border"],
            view_bgcolor=palette["surface"],
            bar_bgcolor=palette["surface_container"],
            bar_overlay_color=ft.Colors.with_opacity(0.1, palette["accent"]),
            bar_hint_text=label,
        )
        
        # Set up event handlers
        self.search_anchor.handle_change = self._handle_search_change
        self.search_anchor.handle_tap = self._handle_tap
        self.search_anchor.handle_submit = self._handle_submit

        # Initialize content
        self.content = self.search_anchor
        
        # Set initial label
        self._update_bar_text(initial_value)

        # Load Data
        asyncio.create_task(self._load_data())

    async def _load_data(self):
        try:
            # Robust path finding
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(base_dir, "assets", "airports.json")
            
            async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
                content = await f.read()
                self.airports_data = json.loads(content)
                self.filtered_data = self.airports_data[:50] # Initial subset
        except Exception as e:
            print(f"Error loading airports: {e}")

    def _update_bar_text(self, text):
        # We simulate a "TextField" look with the bar
        # SearchAnchor bar properties
        self.search_anchor.bar_leading = ft.Icon(ft.Icons.FLIGHT_TAKEOFF if "出発" in self.label else ft.Icons.FLIGHT_LAND, color=self.palette["text_secondary"])
        # We can't easily change the bar text value programmaticly in Flet 0.80.0 without opening view?
        # Actually value property exists.
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
        # If user types "HND" and hits enter
        self.value = e.data.upper()
        self.search_anchor.close_view()
        self.update()

    async def _select_airport(self, code):
        self.value = code
        self.search_anchor.value = code
        await self.search_anchor.close_view_async()
        self.update()
