import flet as ft
from theme import glass_style, COLOR_ACCENT, COLOR_TEXT_PRIMARY, get_color_palette
from services.seat_service import SeatService
import json
import os
import asyncio
from components.flight_card import FlightCard
from datetime import datetime, timedelta
from datetime import datetime, timedelta

class SearchView(ft.Stack):
    def __init__(self, page_ref: ft.Page, amadeus, on_offer_select, **kwargs):
        super().__init__(**kwargs)
        self.page_ref = page_ref
        self.amadeus = amadeus
        self.on_offer_select = on_offer_select
        self.expand = True
        self.alignment = ft.Alignment(0, -1)
        
        self.seat_service = SeatService()
        self.airports = self._load_airports()
        
        self.flights = [] 
        self.is_dark = self.page_ref.theme_mode == ft.ThemeMode.DARK
        self.palette = get_color_palette(self.is_dark)

        # Components
        self.origin_field = None
        self.dest_field = None
        self.date_field = None
        self.time_field = None
        self.window_field = None
        
        self.header_title = None
        self.header_sub = None
        self.search_bar_container = None
        self.results_col = ft.Column(spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
        self.loading_bar = ft.ProgressBar(width=200, color=COLOR_ACCENT, visible=False)
        
        self.suggestions_overlay = None
        self.overlay_layer = None
        self.suggestions_col = ft.Column(spacing=0)
        
        self._build_ui()

    def _load_airports(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(os.path.dirname(current_dir), "assets", "airports.json")
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    def _get_city_name(self, code):
        for a in self.airports:
            if a["iata"] == code:
                return a.get("city_ja", a.get("city", code))
        return code

    def _build_ui(self):
        INPUT_WIDTH = 180
        self.suggestions_overlay = ft.Container(
            content=self.suggestions_col, visible=True, 
            bgcolor=self.palette["surface_container"], 
            border=ft.Border.all(1, self.palette["border_opacity"]), 
            border_radius=8, padding=0, width=INPUT_WIDTH,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK_54),
        )
        
        self.origin_field = self._create_autocomplete("出発地", "HND", 0, INPUT_WIDTH)
        self.dest_field = self._create_autocomplete("目的地", "LHR", INPUT_WIDTH + 10, INPUT_WIDTH)
        self.date_field = self._create_tf("日付", "2025-02-01", 130)
        self.time_field = self._create_tf("時刻", "10:00", 100)
        self.window_field = ft.Dropdown(
            label="時間幅", value="4H", width=160, 
            border_color=self.palette["border"], color=self.palette["text"],
            text_size=16, label_style=ft.TextStyle(size=20, color=self.palette["text_secondary"]),
            options=[
                ft.dropdown.Option("1H", text="＋ 1時間"),
                ft.dropdown.Option("2H", text="＋ 2時間"),
                ft.dropdown.Option("4H", text="＋ 4時間"),
                ft.dropdown.Option("12H", text="＋ 12時間"),
            ]
        )

        self.search_bar_container = ft.Container(
            content=ft.Row(
                [self.origin_field, self.dest_field, self.date_field, self.time_field, self.window_field, 
                 ft.IconButton(ft.Icons.SEARCH, bgcolor=COLOR_ACCENT, icon_color="white", on_click=self.run_search, width=50, height=50, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)))
                ],
                alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, wrap=True, spacing=10
            ),
            bgcolor=ft.Colors.with_opacity(0.05, self.palette["text"]), blur=ft.Blur(10, 10),
            border=ft.Border.all(1, self.palette["border_opacity"]), border_radius=16, padding=20
        )

        self.header_title = ft.Text("フライト検索", size=32, weight="bold", color=self.palette["text"], font_family="Yu Gothic UI")
        self.header_sub = ft.Text("便を選択して座席表を解析します", size=14, color=self.palette["text_secondary"])

        main_layer = ft.Container(
            content=ft.Column([
                self.header_title, self.header_sub,
                ft.Divider(height=10, color="transparent"),
                self.search_bar_container, self.loading_bar, self.results_col
            ], spacing=15, expand=True),
            expand=True, width=920,
        )

        self.overlay_layer = ft.Container(
            expand=True, visible=False, width=920, alignment=ft.Alignment(0, -1),
            content=ft.Stack([self.suggestions_overlay])
        )
        self.controls = [main_layer, self.overlay_layer]

    def _create_tf(self, label, val, w):
        return ft.TextField(
            label=label, value=val, width=w, border_color=self.palette["border"], 
            color=self.palette["text"], text_size=16, 
            label_style=ft.TextStyle(size=20, color=self.palette["text_secondary"])
        )

    def _create_autocomplete(self, label, initial_val, left_pos, width):
        def on_change(e):
            q = tf.value.upper()
            self.suggestions_col.controls.clear()
            if len(q) >= 1:
                matches = [a for a in self.airports if q in a["iata"] or q in (a.get("city") or "").upper()][:6]
                if matches:
                    for m in matches:
                        self.suggestions_col.controls.append(
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(f"{m['iata']} - {m.get('city_ja', m.get('city'))}", color=self.palette["text"], weight="bold"),
                                    ft.Text(f"{m.get('name_ja', m.get('name'))}", color=self.palette["text_secondary"], size=12, no_wrap=True),
                                ], spacing=2, alignment=ft.MainAxisAlignment.START),
                                padding=10, width=width, bgcolor=ft.Colors.with_opacity(0.01, self.palette["text"]), 
                                on_click=lambda _, c=m["iata"]: select(c), ink=True, border_radius=4
                            )
                        )
                    self.overlay_layer.visible = True
                    self.suggestions_overlay.top = 200 
                    self.suggestions_overlay.left = left_pos + 20
                    self.page_ref.update()
                else: self.overlay_layer.visible = False
            else: self.overlay_layer.visible = False
            self.page_ref.update()

        def select(code):
            tf.value = code
            self.overlay_layer.visible = False
            self.page_ref.update()
        
        def hide(e):
            async def _h():
                await asyncio.sleep(0.2)
                self.overlay_layer.visible = False
                self.page_ref.update()
            asyncio.create_task(_h())

        tf = ft.TextField(
            label=label, value=initial_val, width=width, border_color=self.palette["border"], 
            color=self.palette["text"], text_size=16, 
            label_style=ft.TextStyle(size=20, color=self.palette["text_secondary"]),
            on_change=on_change, on_blur=hide
        )
        return tf

    def update_theme_mode(self, is_dark, should_update=True):
        self.is_dark = is_dark
        self.palette = get_color_palette(is_dark)
        p = self.palette
        
        self.header_title.color = p["text"]
        self.header_sub.color = p["text_secondary"]
        
        # Search Bar: White in Light Mode for clean look, Translucent in Dark
        self.search_bar_container.bgcolor = ft.Colors.with_opacity(0.05, p["text"]) if is_dark else "#f9f9f9"
        self.search_bar_container.border = ft.Border.all(1, p["border_opacity"])
        
        for f in [self.origin_field, self.dest_field, self.date_field, self.time_field, self.window_field]:
            f.border_color = p["border"]
            f.color = p["text"]
            f.label_style.color = p["text_secondary"]
            
        self.suggestions_overlay.bgcolor = p["surface_container"]
        self.suggestions_overlay.border = ft.Border.all(1, p["border_opacity"])
        
        # Results Update (In-Place to preserve scroll)
        for c in self.results_col.controls:
            if isinstance(c, FlightCard):
                c.update_theme(p)
            elif isinstance(c, ft.Text):
                c.color = p["text"]
        
        if should_update:
            self.update()

    async def run_search(self, e):
        self.results_col.controls.clear()
        self.loading_bar.visible = True
        self.page_ref.update()
        
        try:
            t_val = self.time_field.value
            w_val = self.window_field.value
            input_time = datetime.strptime(t_val, "%H:%M")
            shift = int(w_val.replace("H", "")) / 2
            t_fmt = (input_time + timedelta(hours=shift)).strftime("%H:%M") 
            window_param = f"{int(shift)}H" 
            
            resp = await self.amadeus.search_flights(
                self.origin_field.value, self.dest_field.value, self.date_field.value,
                time=t_fmt, window=window_param
            )
        except ValueError:
            resp = await self.amadeus.search_flights(
                self.origin_field.value, self.dest_field.value, self.date_field.value,
                time=self.time_field.value, window=self.window_field.value
            )
        
        self.flights = self.seat_service.group_offers_by_flight(resp)
        self.loading_bar.visible = False
        
        self._render_results()
        self.page_ref.update()

    def _render_results(self):
        self.results_col.controls.clear()
        p = self.palette
        if self.flights:
            self.results_col.controls.append(ft.Text(f"検索結果: {len(self.flights)} 便", size=16, color=p["text"], weight="bold"))
            for f in self.flights:
                card = FlightCard(
                    f, p, 
                    on_select=lambda offers: asyncio.create_task(self.on_offer_select(offers)),
                    get_city_name=self._get_city_name
                )
                self.results_col.controls.append(card)
