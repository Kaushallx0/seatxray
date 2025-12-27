import flet as ft
from theme import glass_style, COLOR_ACCENT

class FlightCard(ft.Container):
    def __init__(self, flight_data, palette, on_select, get_city_name):
        super().__init__()
        self.flight_data = flight_data
        self.palette = palette
        self.on_select = on_select
        self.get_city_name = get_city_name
        self.ink = True
        self.on_click = self.toggle_expand
        
        # Components references for theme updates
        self.text_controls = []
        self.container_controls = []
        self.icon_controls = []
        self.border_controls = []
        
        self.expanded_view = None
        self.expand_icon = None
        
        self.content = self._build_content()
        self._apply_theme()

    def _build_content(self):
        f = self.flight_data
        identity = f["identity"]
        route = f["route"]
        offers = f["offers"]
        
        # Build Badges
        price_badges = []
        for cabin, p_info in f["pricing"].items():
            label = cabin.replace("_", " ").title()
            if "ECONOMY" in cabin: label = "エコノミー"
            if "PREMIUM" in cabin: label = "プレエコ"
            if "BUSINESS" in cabin: label = "ビジネス"
            if "FIRST" in cabin: label = "ファースト"
            
            t1 = ft.Text(label, size=13)
            t2 = ft.Text(p_info["formatted"], size=15, weight="bold", color=COLOR_ACCENT)
            self.text_controls.append((t1, "text_secondary"))
            # t2 is always accent color
            
            c = ft.Container(
                content=ft.Row([t1, t2], spacing=5),
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                border_radius=4
            )
            self.container_controls.append((c, "surface_container_low"))
            self.border_controls.append(c)
            price_badges.append(c)

        # Expanded View
        t_aircraft_label = ft.Text("機材:", size=13)
        t_aircraft_val = ft.Text(identity["aircraftName"], size=15, weight="bold")
        t_duration_label = ft.Text("時間:", size=13)
        t_duration_val = ft.Text(route["duration"], size=15, weight="bold")
        
        self.text_controls.extend([
            (t_aircraft_label, "text_secondary"), (t_aircraft_val, "text"),
            (t_duration_label, "text_secondary"), (t_duration_val, "text")
        ])
        
        self.expanded_view = ft.Container(
            visible=False,
            padding=ft.Padding.only(top=15),
            content=ft.Column([
                ft.Divider(), # Border color to be set
                ft.Row([
                    ft.Row([t_aircraft_label, t_aircraft_val]),
                    ft.Row([t_duration_label, t_duration_val]),
                ], spacing=30),
                ft.FilledButton("座席表を解析する", icon=ft.Icons.GRID_ON, bgcolor=COLOR_ACCENT, color="white", width=250, height=45,
                    on_click=lambda e: self.on_select(offers)
                )
            ])
        )
        # Store divider for theme update
        self.divider = self.expanded_view.content.controls[0]

        # Main Layout
        t_flight_no = ft.Text(f"{identity['carrierCode']} {identity['flightNumber']}", weight="bold", size=18)
        t_carrier = ft.Text(identity["carrierName"], size=12)
        
        t_time = ft.Text(f"{route['departure']['at'][11:16]} - {route['arrival']['at'][11:16]}", size=20, weight="bold")
        t_route = ft.Text(f"{self.get_city_name(route['departure']['iata'])} ➔ {self.get_city_name(route['arrival']['iata'])}", size=14)
        
        self.text_controls.extend([
            (t_flight_no, "text"), (t_carrier, "text_secondary"),
            (t_time, "text"), (t_route, "text_secondary")
        ])

        self.expand_icon = ft.IconButton(ft.Icons.EXPAND_MORE, on_click=self.toggle_expand)
        
        return ft.Column([
            ft.Row([
                ft.Row([
                    ft.Container(ft.Icon(ft.Icons.AIRPLANEMODE_ACTIVE, color="white"), padding=10, bgcolor=COLOR_ACCENT, border_radius=8),
                    ft.Column([t_flight_no, t_carrier], spacing=2)
                ]),
                ft.Column([t_time, t_route], alignment=ft.MainAxisAlignment.CENTER),
                self.expand_icon
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row(price_badges, wrap=True, spacing=10),
            self.expanded_view
        ], spacing=10)

    def toggle_expand(self, e):
        self.expanded_view.visible = not self.expanded_view.visible
        self.update()

    def update_theme(self, palette):
        self.palette = palette
        self._apply_theme()
        self.update()

    def _apply_theme(self):
        p = self.palette
        # Update Texts
        for t, key in self.text_controls:
            t.color = p[key]
        
        # Update Containers
        for c, key in self.container_controls:
            c.bgcolor = p[key]
            
        # Update Borders
        for c in self.border_controls:
            c.border = ft.Border.all(1, p["border_opacity"])
            
        # Update Divider
        self.divider.color = p["border_opacity"]
        
        # Update Icon
        self.expand_icon.icon_color = p["text"]
        
        # Self (Glass Style)
        # Re-apply glass style properties manually or helpers
        # glass_style returns dict.
        self.bgcolor = ft.Colors.with_opacity(0.08, p["surface"])
        self.border_radius = 16
        self.padding = 20
        self.border = ft.Border.all(1, p["border_opacity"])
        self.blur = ft.Blur(10, 10)
