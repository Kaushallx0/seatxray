import flet as ft
from theme import get_color_palette, COLOR_ACCENT
from services.seat_service import SeatService
from components.flight_card import FlightCard
import json
import os
import asyncio
from datetime import datetime, timedelta
from utils.i18n import TranslationService

class SearchContent(ft.Column):
    """Content for the Search View"""
    
    def __init__(self, page: ft.Page, app_state, amadeus, on_navigate_seatmap, **kwargs):
        self.i18n = TranslationService.get_instance()
        self.page_ref = page
        self.app_state = app_state
        self.amadeus = amadeus
        self.on_offer_select = on_navigate_seatmap
        
        self.is_dark = (app_state.theme_mode == "DARK")
        self.palette = get_color_palette(self.is_dark)
        
        self.seat_service = SeatService()
        self.airports = self.i18n.get_airports()
        self.flights = getattr(app_state, "offers", []) or []
        self.has_searched = bool(self.flights) 
        self.expanded_flight_id = None
        self.saved_input_state = kwargs.get("input_state", {})
        
        # For autocomplete
        self._active_field = None
        self._suggestions_overlay = None
        
        # Refs
        self.origin_ref = ft.Ref[ft.TextField]()
        self.dest_ref = ft.Ref[ft.TextField]()
        self.date_ref = ft.Ref[ft.TextField]()
        self.time_ref = ft.Ref[ft.TextField]()
        self.window_ref = ft.Ref[ft.Dropdown]()
        self.loading_ref = ft.Ref[ft.ProgressBar]()
        self.results_ref = ft.Ref[ft.Column]()
        
        p = self.palette
        tr = self.i18n.tr
        
        # Default values
        def_ori = self.saved_input_state.get("origin", "HND")
        def_dst = self.saved_input_state.get("dest", "LHR")
        default_date_obj = datetime.now() + timedelta(days=30)
        def_dat = self.saved_input_state.get("date", default_date_obj.strftime("%Y-%m-%d"))
        def_tim = self.saved_input_state.get("time", "10:00")
        def_win = self.saved_input_state.get("window", "4H")
        
        # Header
        header = ft.Column([
            ft.Text(tr("search.header_title"), size=48, weight="bold", color=p["text"]),
            ft.Text(tr("search.header_subtitle"), size=18, color=p["text_secondary"]),
        ], spacing=5)
        
        # Search Bar
        search_bar = ft.Container(
            content=ft.Row([
                ft.TextField(
                    ref=self.origin_ref,
                    label=tr("search.label_origin"),
                    value=def_ori,
                    width=160,
                    border_color=p["border"],
                    color=p["text"],
                    text_size=18,
                    on_change=lambda e: self._on_airport_change(e, "origin"),
                    on_focus=lambda e: self._on_airport_focus(e, "origin"),
                ),
                ft.TextField(
                    ref=self.dest_ref,
                    label=tr("search.label_dest"),
                    value=def_dst,
                    width=160,
                    border_color=p["border"],
                    color=p["text"],
                    text_size=18,
                    on_change=lambda e: self._on_airport_change(e, "dest"),
                    on_focus=lambda e: self._on_airport_focus(e, "dest"),
                ),
                ft.TextField(
                    ref=self.date_ref,
                    label=tr("common.date"), 
                    value=def_dat, 
                    width=140,
                    border_color=p["border"],
                    color=p["text"],
                    text_size=18,
                ),
                ft.TextField(
                    ref=self.time_ref,
                    label=tr("common.time"), 
                    value=def_tim, 
                    width=100,
                    border_color=p["border"],
                    color=p["text"],
                    text_size=18,
                ),
                ft.Dropdown(
                    ref=self.window_ref,
                    label=tr("search.label_search_range"),
                    value=def_win,
                    width=160,
                    border_color=p["border"],
                    color=p["text"],
                    text_size=18,
                    options=[
                        ft.dropdown.Option("1H", text=tr("search.range_1h")),
                        ft.dropdown.Option("2H", text=tr("search.range_2h")),
                        ft.dropdown.Option("4H", text=tr("search.range_4h")),
                        ft.dropdown.Option("12H", text=tr("search.range_12h")),
                    ],
                ),
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.SEARCH, color="white", size=20),
                            ft.Text(tr("common.search"), size=16, color="white"),
                        ], spacing=8),
                        bgcolor=COLOR_ACCENT,
                        on_click=self.run_search,
                        height=50,
                    ),
                    width=120,
                ),
            ], spacing=15, wrap=True, run_spacing=15, vertical_alignment=ft.CrossAxisAlignment.START),
            bgcolor=ft.Colors.with_opacity(0.05, p["text"]) if self.is_dark else "#f9f9f9",
            border=ft.border.all(1, p["border_opacity"]),
            border_radius=16,
            padding=20,
        )
        
        # Loading Bar
        loading_bar = ft.ProgressBar(
            ref=self.loading_ref,
            width=300,
            color=COLOR_ACCENT,
            visible=False,
        )
        
        # Results Area
        results_column = ft.Column(
            ref=self.results_ref,
            controls=[],
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        
        super().__init__(
            controls=[
                ft.Container(
                    content=ft.Column([
                        header,
                        ft.Container(height=20),
                        search_bar,
                        ft.Container(height=20),
                        loading_bar,
                        results_column,
                    ], spacing=0, expand=True),
                    padding=40,
                    expand=True,
                )
            ],
            expand=True,
        )
        
        if self.flights:
            self._render_results()

    def update_palette(self, new_palette):
        """Update palette when theme changes (without view recreation)"""
        self.palette = new_palette
        self.is_dark = (self.app_state.theme_mode == "DARK")
        
        # Update header text color
        main_container = self.controls[0]
        inner_column = main_container.content
        header = inner_column.controls[0]  # ft.Column containing header texts
        header.controls[0].color = new_palette["text"]  # Title
        header.controls[1].color = new_palette["text_secondary"]  # Subtitle
        
        # Update search bar background and border
        search_bar = inner_column.controls[2]  # ft.Container
        search_bar.bgcolor = ft.Colors.with_opacity(0.05, new_palette["text"]) if self.is_dark else "#f9f9f9"
        search_bar.border = ft.border.all(1, new_palette["border_opacity"])
        
        # Update input field color
        search_row = search_bar.content
        for control in search_row.controls:
            if isinstance(control, ft.TextField):
                control.border_color = new_palette["border"]
                control.color = new_palette["text"]
            elif isinstance(control, ft.Dropdown):
                control.border_color = new_palette["border"]
                control.color = new_palette["text"]
        
        # Redraw results
        self._render_results()
        
        try:
            self.update()
        except:
            pass

    def _on_airport_focus(self, e, field_type):
        self._active_field = field_type
        if e.control.value:
            self._show_suggestions(e.control.value, e.control)

    def _on_airport_change(self, e, field_type):
        self._active_field = field_type
        self._show_suggestions(e.control.value, e.control)

    def _show_suggestions(self, query, text_field):
        # Remove existing overlay
        self._hide_suggestions()
        
        q = (query or "").upper()
        if len(q) < 1:
            return
        
        matches = [a for a in self.airports if 
                   q in a["iata"] or 
                   q in (a.get("city") or "").upper()][:5]
        
        if not matches:
            return
        
        p = self.palette
        
        # Create suggestion list
        suggestions = ft.Column([], spacing=0)
        for m in matches:
            code = m["iata"]
            city = m.get('city', '')
            name = m.get('name', '')
            
            tile = ft.ListTile(
                title=ft.Text(f"{code} - {city}", size=13, weight="bold", color=p["text"]),
                subtitle=ft.Text(name, size=11, color=p["text_secondary"]),
                dense=True,
                bgcolor=p["surface_container"],
                on_click=lambda e, c=code: self._select_airport(c),
            )
            suggestions.controls.append(tile)
        
        # Position calculation:
        # NavigationRail (100px) + VerticalDivider (1px) + padding (40px) + search_bar padding (20px)
        base_left = 100 + 1 + 40 + 20  # 161px
        field_width = 160
        
        if self._active_field == "origin":
            left_pos = base_left
        else:  # dest
            left_pos = base_left + field_width + 15  # spacing 15px
        
        # Vertical: Directly below the input field
        # Consider the entire search bar position
        top_pos = 265  # Below the input field
        
        # Suggestion box
        suggestions_box = ft.Container(
            content=suggestions,
            bgcolor=p["surface_container"],
            border=ft.border.all(1, p["border_opacity"]),
            border_radius=8,
            width=field_width,  # Same width as input field
            left=left_pos,
            top=top_pos,
        )
        
        self._suggestions_overlay = ft.Stack([
            ft.GestureDetector(
                content=ft.Container(bgcolor=ft.Colors.TRANSPARENT, expand=True),
                on_tap=lambda e: self._hide_suggestions(),
            ),
            suggestions_box,
        ], expand=True)
        
        self.page_ref.overlay.append(self._suggestions_overlay)
        self.page_ref.update()

    def _select_airport(self, code):
        if self._active_field == "origin":
            self.origin_ref.current.value = code
            self.origin_ref.current.update()
        elif self._active_field == "dest":
            self.dest_ref.current.value = code
            self.dest_ref.current.update()
        self._hide_suggestions()

    def _hide_suggestions(self):
        if self._suggestions_overlay and self._suggestions_overlay in self.page_ref.overlay:
            self.page_ref.overlay.remove(self._suggestions_overlay)
            self.page_ref.update()
        self._suggestions_overlay = None

    def _get_city_name(self, code):
        for a in self.airports:
            if a["iata"] == code:
                return a.get("city", code)
        return code

    def get_input_state(self):
        return {
            "origin": self.origin_ref.current.value if self.origin_ref.current else "",
            "dest": self.dest_ref.current.value if self.dest_ref.current else "",
            "date": self.date_ref.current.value if self.date_ref.current else "",
            "time": self.time_ref.current.value if self.time_ref.current else "",
            "window": self.window_ref.current.value if self.window_ref.current else "4H",
        }

    def _handle_toggle(self, flight_id):
        if self.expanded_flight_id == flight_id:
            self.expanded_flight_id = None
        else:
            self.expanded_flight_id = flight_id
        self._render_results()
        self.page_ref.update()

    async def run_search(self, e):
        self._hide_suggestions()
        self.loading_ref.current.visible = True
        self.loading_ref.current.update()
        self.results_ref.current.controls.clear()
        
        self.has_searched = True # Set search executed flag
        
        origin = self.origin_ref.current.value
        dest = self.dest_ref.current.value
        
        try:
            t_val = self.time_ref.current.value
            w_val = self.window_ref.current.value
            shift = int(w_val.replace("H", "")) / 2
            input_time = datetime.strptime(t_val, "%H:%M")
            t_fmt = (input_time + timedelta(hours=shift)).strftime("%H:%M")
            window_param = f"{int(shift*2)}H"
            
            resp = await self.amadeus.search_flights(
                origin,
                dest,
                self.date_ref.current.value,
                time=t_fmt,
                window=window_param
            )
        except Exception as err:
            print(f"Search error: {err}")
            resp = await self.amadeus.search_flights(
                origin,
                dest,
                self.date_ref.current.value
            )
        
        if resp and "data" in resp:
            self.flights = self.seat_service.group_offers_by_flight(resp)
            self.app_state.offers = self.flights
        else:
            self.flights = []
        
        self.loading_ref.current.visible = False
        self._render_results()
        self.page_ref.update()

    def _render_results(self):
        col = self.results_ref.current
        if not col:
            return
        col.controls.clear()
        p = self.palette
        tr = self.i18n.tr
        
        if self.flights:
            col.controls.append(
                ft.Text(tr("search.results_count", count=len(self.flights)), size=20, color=p["text"], weight="bold")
            )
            for f in self.flights:
                is_expanded = (f["id"] == self.expanded_flight_id)
                card = FlightCard(
                    flight_data=f,
                    palette=p,
                    is_expanded=is_expanded,
                    on_toggle=lambda fd=f: self._handle_toggle(fd["id"]),
                    on_select_seatmap=lambda offers, fd=f: self._handle_select(offers, fd),
                    get_city_name=self._get_city_name
                )
                col.controls.append(card)
        elif self.has_searched:
            col.controls.append(
                ft.Text(tr("search.no_results"), size=18, color=p["text"])
            )

    def _handle_select(self, offers, flight_data):
        self.app_state.selected_offer_group = flight_data
        self.on_offer_select(offers)
