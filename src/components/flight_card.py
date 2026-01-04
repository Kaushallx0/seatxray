import flet as ft
from theme import COLOR_ACCENT, glass_style
from datetime import datetime
from utils.i18n import TranslationService

class FlightCard(ft.Container):
    def __init__(self, flight_data, palette, is_expanded, on_toggle, on_select_seatmap, get_city_name):
        super().__init__()
        self.i18n = TranslationService.get_instance()
        self.flight_data = flight_data
        self.palette = palette
        self.is_expanded = is_expanded
        self.on_toggle = on_toggle
        self.on_select_seatmap = on_select_seatmap
        self.get_city_name = get_city_name
        
        # Apply Glassmorphism using theme helper
        style = glass_style(opacity=0.08, blur=10, dark=(palette["bg"] != "#f0f2f5"), surface_color=palette["surface"])
        self.bgcolor = style["bgcolor"]
        self.border_radius = style["border_radius"]
        self.padding = ft.Padding(15, 10, 15, 10)
        self.border = style["border"]
        self.blur = style["blur"]
        
        self.content = self._build_content()
        self.animate_size = 200
        
        # Card Clickable
        self.on_click = lambda e: self.on_toggle()
        self.ink = True

    def _build_content(self):
        f = self.flight_data
        identity = f["identity"]
        route = f["route"]
        p = self.palette
        
        # Flight Info
        flight_name = f"{identity['carrierCode']} {identity['flightNumber']}"
        carrier_name = identity['carrierName'].upper()
        
        # Cabin Class (First found)
        cabins = list(f["pricing"].keys()) if f["pricing"] else []
        cabin_labels = [self._get_cabin_label(c) for c in cabins]
        cabin_text = " / ".join(cabin_labels) if cabin_labels else ""
        
        # Time
        dep_time = datetime.fromisoformat(route['departure']['at']).strftime("%H:%M")
        arr_time = datetime.fromisoformat(route['arrival']['at']).strftime("%H:%M")
        
        dep_city = self.get_city_name(route['departure']['iata'])
        arr_city = self.get_city_name(route['arrival']['iata'])
        
        # Layout components...
        flight_info = ft.Column([
            ft.Text(flight_name, size=18, weight="bold", color=p["text"]),
            ft.Text(carrier_name, size=12, color=p["text_secondary"])
        ], spacing=0, alignment=ft.MainAxisAlignment.CENTER)
        
        cabin_info = ft.Text(cabin_text, size=14, color=COLOR_ACCENT, weight="w500")
        
        time_info = ft.Column([
            ft.Text(f"{dep_time} - {arr_time}", size=18, weight="bold", color=p["text"]),
            ft.Row([
                ft.Text(f"{dep_city}", size=12, color=p["text_secondary"]),
                ft.Icon(ft.Icons.ARROW_FORWARD, size=12, color=p["text_secondary"]),
                ft.Text(f"{arr_city}", size=12, color=p["text_secondary"]),
            ], spacing=3)
        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END)
        
        top_row = ft.Row([
            flight_info,
            cabin_info,
            ft.Row([
                time_info, 
                ft.IconButton(
                    ft.Icons.KEYBOARD_ARROW_UP if self.is_expanded else ft.Icons.KEYBOARD_ARROW_DOWN,
                    icon_color=p["text_secondary"], icon_size=24,
                    on_click=lambda e: self.on_toggle()
                )
            ])
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        card_content = [top_row]
        
        if self.is_expanded:
            details = self._build_details(f, p, identity, route)
            card_content.append(ft.Container(height=5))
            card_content.append(details)

        return ft.Column(card_content, spacing=5)

    def _get_cabin_label(self, k):
        # i18n lookup
        key = f"flight_card.cabin_{k.lower()}"
        return self.i18n.tr(key)

    def _build_details(self, f, p, identity, route):
        btns = []
        for cabin, price_info in f["pricing"].items():
            label = self._get_cabin_label(cabin)
            amt = price_info["formatted"]
             
            btn = ft.Container(
                padding=10, border_radius=8,
                bgcolor=ft.Colors.with_opacity(0.1, "#6d4aff"),
                border=ft.border.all(1, "#6d4aff"),
                on_click=lambda e, c=cabin: self.on_select_seatmap([o for o in f["offers"] if o["travelerPricings"][0]["fareDetailsBySegment"][0]["cabin"] == c]),
                content=ft.Row([
                    ft.Icon(ft.Icons.EVENT_SEAT, color="#6d4aff", size=18),
                    ft.Text(f"{label}", color=p["text"], weight="bold", size=16),
                    ft.Container(expand=True),
                    ft.Text(amt, color=p["text"], size=16, weight="bold"),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=p["text_secondary"])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ink=True
            )
            btns.append(btn)
        
        ac_name = identity['aircraftName']
        duration = route['duration']
        # Note: SeatService already pre-formatted duration to 日本語 "X時間Y分". 
        # i18n for duration needs SeatService refactor, skipping for now as per plan focus on View.
        
        detail_text = self.i18n.tr("flight_card.details_template", ac_name=ac_name, duration=duration)
        
        return ft.Column([
            ft.Divider(color=p["border_opacity"]),
            ft.Text(detail_text, size=14, color=p["text_secondary"]),
            ft.Container(height=5),
            ft.Column(btns, spacing=8)
        ], spacing=5)
