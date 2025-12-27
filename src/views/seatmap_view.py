import flet as ft
from theme import glass_style, COLOR_ACCENT, get_color_palette
from services.seat_service import SeatService
from components.seat_canvas import SeatCanvas
import asyncio
import traceback

class SeatMapView(ft.Stack):
    def __init__(self, page: ft.Page, amadeus, on_back: callable):
        super().__init__(expand=True)
        self.page_ref = page
        self.amadeus = amadeus
        self.on_back = on_back
        
        self.seat_service = SeatService()
        self.is_dark = page.theme_mode == ft.ThemeMode.DARK
        self.palette = get_color_palette(self.is_dark)
        
        self.last_map_data = None
        self.last_facilities = None
        self.last_offers = None
        
        self.canvas_container = ft.Container(expand=True, bgcolor=self.palette["bg"])
        self.details_panel = None
        self.back_button = None
        self.loading_indicator = None
        
        self._build_ui()
        
    def _build_ui(self):
        PALETTE = self.palette
        
        # Back Button
        self.back_button = ft.Container(
            content=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: asyncio.create_task(self.on_back()), icon_color=PALETTE["text"]),
            top=10, left=10,
            bgcolor=ft.Colors.with_opacity(0.8, PALETTE["bg"]),
            border=ft.Border.all(1, PALETTE["border_opacity"]),
            border_radius=50
        )
        
        # Details Panel
        self.details_panel = ft.Container(
            visible=False,
            bottom=20, left=20, right=20,
            content=ft.Row([], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            **glass_style(opacity=0.95, blur=20, dark=self.is_dark, surface_color=PALETTE["surface"])
        )
        
        self.controls = [self.canvas_container, self.back_button, self.details_panel]

    async def load_seatmap(self, offers):
        # Cache Check
        if self.last_offers == offers and self.last_map_data:
            print("[SeatMapView] Cache Hit. Skipping API call.")
            return

        self.last_offers = offers
        
        # Debug: Log offer count being sent
        print(f"[SeatMapView] Sending {len(offers)} offers to SeatMap API.") 

        p = self.palette
        self.canvas_container.content = ft.Container(
            content=ft.Column([
                ft.ProgressRing(color=COLOR_ACCENT),
                ft.Text("座席データを解析中...", color=p["text"])
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment(0, 0)
        )
        self.update()
        
        try:
            raw_response = await self.amadeus.get_seatmap(offers)
            
            # Debug: Log returned cabin types
            cabins_found = set()
            for sm in raw_response.get("data", []):
                for deck in sm.get("decks", []):
                    for seat in deck.get("seats", []):
                        if "cabin" in seat:
                            cabins_found.add(seat["cabin"])
            print(f"[SeatMapView] Cabins in API response: {cabins_found}")
            
            master_map, facilities = self.seat_service.process_seatmaps_batch(raw_response)
            
            if not master_map:
                self.last_map_data = None
                self.canvas_container.content = ft.Container(
                    ft.Text("座席データの取得に失敗しました。\n(該当便の座席表が存在しないか、API制限の可能性があります)", color="red", text_align=ft.TextAlign.CENTER),
                    alignment=ft.Alignment(0, 0)
                )
            else:
                self.last_map_data = master_map
                self.last_facilities = facilities
                self.canvas_container.content = SeatCanvas(master_map, facilities, self.on_seat_click, palette=p)
        except Exception as e:
            self.canvas_container.content = ft.Text(f"解析エラー: {e}", color="red")
            traceback.print_exc()
            
        self.update()

    def on_seat_click(self, seat_data):
        p = self.palette
        number = seat_data.get("number", "??")
        status = seat_data.get("_final_status", "UNKNOWN")
        pricing = seat_data.get("travelerPricing", [{}])[0]
        if status == "UNKNOWN": status = pricing.get("seatAvailabilityStatus", "UNKNOWN")
        
        STATUS_MAP = {"AVAILABLE": "空席 (Available)", "OCCUPIED": "予約済み (Occupied)", "BLOCKED": "ブロック (Blocked)"}
        
        codes = seat_data.get("characteristicsCodes", [])
        features = []
        if "E" in codes: features.append(("非常口", ft.Icons.EMERGENCY))
        if "K" in codes: features.append(("バルクヘッド", ft.Icons.VERTICAL_ALIGN_TOP))
        if "L" in codes: features.append(("足元広め", ft.Icons.EXPAND))
        
        feature_layout = []
        for label, icon in features:
            feature_layout.append(
                ft.Container(
                    ft.Row([ft.Icon(icon, size=20, color=COLOR_ACCENT), ft.Text(label, size=14, weight="bold", color=p["text"])], spacing=8),
                    padding=10, bgcolor=p["surface_container"], border_radius=8,
                    border=ft.Border.all(1, p["border_opacity"])
                )
            )

        self.details_panel.content = ft.Row([
            ft.Column([
                ft.Text(f"座席 {number}", size=28, weight="bold", color=p["text"]),
                ft.Text(STATUS_MAP.get(status, status), size=18, color=COLOR_ACCENT if status=="AVAILABLE" else p["text_secondary"]),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([
                ft.Row(feature_layout, spacing=10),
                ft.Container(width=20),
                ft.IconButton(ft.Icons.CLOSE, on_click=self.close_panel, icon_color=p["text"], icon_size=30)
            ], alignment=ft.MainAxisAlignment.END, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        
        self.details_panel.visible = True
        self.update()

    def close_panel(self, e):
        self.details_panel.visible = False
        self.update()

    def update_theme_mode(self, is_dark):
        self.is_dark = is_dark
        p = get_color_palette(is_dark)
        self.palette = p
        
        self.canvas_container.bgcolor = p["bg"]
        
        # Update Back Button
        self.back_button.bgcolor = ft.Colors.with_opacity(0.8, p["bg"])
        self.back_button.border = ft.Border.all(1, p["border_opacity"])
        self.back_button.content.icon_color = p["text"]
        
        # Update Details Panel logic
        self.details_panel.bgcolor = ft.Colors.with_opacity(0.95, p["surface"]) 
        
        # Re-render canvas if data exists
        if self.last_map_data:
            self.canvas_container.content = SeatCanvas(self.last_map_data, self.last_facilities, self.on_seat_click, palette=p)
            
        self.update()
