# Copyright (c) 2026 SeatXray Developers
# Licensed under the terms of the GNU Affero General Public License (AGPL) version 3.
# See LICENSE file in the project root for details.

"""SeatMap Content. Integrates canvas and details."""

import flet as ft
import asyncio
import traceback
from services.seat_service import SeatService
from components.seat_canvas import SeatCanvas
from theme import get_color_palette, COLOR_ACCENT
from utils.i18n import TranslationService


class SeatMapContent(ft.Column):
    """Seat map content (Embeddable in AppLayout)"""
    
    def __init__(self, page: ft.Page, app_state, amadeus, on_back=None):
        self.i18n = TranslationService.get_instance()
        self.page_ref = page
        self.app_state = app_state
        self.amadeus = amadeus
        self.on_back = on_back
        
        self.is_dark = (app_state.theme_mode == "DARK")
        self.is_mobile = page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]

        self.palette = get_color_palette(self.is_dark)
        self.seat_service = SeatService()
        self.selected_seat = None # Holds selected seat data (for redraw on theme change)
        
        # Components
        self.canvas_container = ft.Container(expand=True, bgcolor=self.palette["bg"])
        self.details_panel = self._build_details_panel()
        
        # Header (Including Back Button)
        self.header = self._build_header()
        
        super().__init__(
            controls=[
                self.header,
                ft.Stack(
                    [
                        self.canvas_container,
                        self.details_panel
                    ],
                    expand=True
                )
            ],
            expand=True,
            spacing=0,
        )
        
        # Load Data
        target_flight = self.app_state.selected_offer_group
        if target_flight:
            asyncio.create_task(self._load_data(target_flight["offers"]))

    def _build_header(self):
        """Header containing the back button"""
        p = self.palette
        
        # Get flight info
        flight_info = ""
        target = self.app_state.selected_offer_group
        if target and "identity" in target:
            identity = target["identity"]
            flight_info = f"{identity.get('carrierCode', '')} {identity.get('flightNumber', '')} | {identity.get('carrierName', '')}"
        
        return ft.Container(
            content=ft.Row([
                ft.IconButton(
                    ft.Icons.ARROW_BACK,
                    on_click=lambda _: self._go_back(),
                    icon_color=p["text"],
                    icon_size=24,
                ),
                ft.Text(
                    flight_info, 
                    size=18, 
                    weight="bold", 
                    color=p["text"],
                    expand=True,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=p["surface"],
            padding=ft.Padding(15, 10, 15, 10),
            border=ft.border.only(bottom=ft.BorderSide(1, p["border_opacity"])),
        )

    def _go_back(self):
        if self.on_back:
            self.on_back()

    def _build_details_panel(self):
        p = self.palette
        return ft.Container(
            visible=False,
            bottom=20, left=20, right=20,
            content=ft.Row([], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.Colors.with_opacity(0.95, p["surface"]),
            border_radius=16,
            padding=20,
            border=ft.border.all(1, p["border_opacity"]),
            blur=ft.Blur(20, 20)
        )

    async def _load_data(self, offers):
        p = self.palette
        
        # Generate cache key
        if offers:
            first_offer = offers[0] if isinstance(offers, list) else offers
            cache_key = f"{first_offer.get('id', '')}_{first_offer.get('source', '')}"
        else:
            cache_key = None
        
        # Check cache
        cached_data = self.app_state.get_seatmap_cache(cache_key) if cache_key else None
        
        if cached_data:
            # Load from cache
            master_map, facilities = cached_data
            self.canvas_container.content = SeatCanvas(
                master_map, 
                facilities, 
                self._on_seat_click, 
                palette=p,
                is_mobile=self.is_mobile
            )
            self.page_ref.update()
            return
        
        # Show loading
        tr = self.i18n.tr
        self.canvas_container.content = ft.Container(
            content=ft.Column([
                ft.ProgressRing(color=COLOR_ACCENT),
                ft.Text(tr("seatmap.loading"), color=p["text"])
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment(0, 0)
        )
        self.page_ref.update()

        try:
            raw_response = await self.amadeus.get_seatmap(offers)
            master_map, facilities = self.seat_service.process_seatmaps_batch(raw_response)
            
            # Get TTL (from API response)
            cache_ttl = raw_response.get("_cache_ttl")
            
            if not master_map:
                self.canvas_container.content = ft.Container(
                    ft.Text(tr("seatmap.fetch_error"), color="red"),
                    alignment=ft.Alignment(0, 0)
                )
            else:
                # Save to cache (Cache-Control header or 6 hours)
                if cache_key:
                    self.app_state.set_seatmap_cache(cache_key, (master_map, facilities), cache_ttl)
                
                self.canvas_container.content = SeatCanvas(
                    master_map, 
                    facilities, 
                    self._on_seat_click, 
                    palette=p,
                    is_mobile=self.is_mobile
                )
        except Exception as e:
            traceback.print_exc()
            self.canvas_container.content = ft.Text(f"Error: {e}", color="red")
            
        self.page_ref.update()

    def _on_seat_click(self, seat_data):
        self.selected_seat = seat_data
        p = self.palette
        number = seat_data.get("number", "??")
        status = seat_data.get("_final_status", "UNKNOWN")
        pricing = seat_data.get("travelerPricing", [{}])[0]
        if status == "UNKNOWN": 
            status = pricing.get("seatAvailabilityStatus", "UNKNOWN")
        
        tr = self.i18n.tr
        STATUS_MAP = {
            "AVAILABLE": tr("seatmap.status_available"), 
            "OCCUPIED": tr("seatmap.status_occupied"), 
            "BLOCKED": tr("seatmap.status_blocked")
        }
        
        codes = seat_data.get("characteristicsCodes", [])
        features = []
        if "E" in codes: features.append((tr("seatmap.feature_exit"), ft.Icons.EMERGENCY))
        if "L" in codes: features.append((tr("seatmap.feature_legroom"), ft.Icons.EXPAND))
        
        feature_layout = []
        for label, icon in features:
            feature_layout.append(ft.Row([ft.Icon(icon), ft.Text(label)]))

        # Detail Panel Content - Mobile: smaller sizes
        title_size = 20 if self.is_mobile else 28
        status_size = 14 if self.is_mobile else 18
        icon_size = 14 if self.is_mobile else 16
        
        info_items = [
            ft.Text(tr("seatmap.seat_number", number=number), size=title_size, weight="bold", color=p["text"]),
            ft.Container(width=8 if self.is_mobile else 10),
            ft.Text(STATUS_MAP.get(status, status), size=status_size, color=COLOR_ACCENT if status=="AVAILABLE" else p["text_secondary"]),
            ft.Container(width=8 if self.is_mobile else 10),
        ]
        
        # Add feature icons
        if features:
            info_items.append(ft.Container(width=1, height=16 if self.is_mobile else 20, bgcolor=p["divider"]))
            info_items.append(ft.Container(width=8 if self.is_mobile else 10))
            for label, icon in features:
                info_items.append(ft.Row([ft.Icon(icon, size=icon_size, color=p["text"]), ft.Text(label, color=p["text"], size=12 if self.is_mobile else 14)], spacing=2))
                info_items.append(ft.Container(width=8 if self.is_mobile else 10))

        # Close Button (Right end)
        self.details_panel.content = ft.Row(
            controls=[
                ft.Row(info_items, alignment=ft.MainAxisAlignment.START, scroll=ft.ScrollMode.HIDDEN, expand=True),
                ft.IconButton(ft.Icons.CLOSE, on_click=lambda e: self._close_panel(), icon_color=p["text"], icon_size=20 if self.is_mobile else 24)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        
        self.details_panel.visible = True
        self.page_ref.update()

    def _close_panel(self):
        self.selected_seat = None
        self.details_panel.visible = False
        self.page_ref.update()

    def update_palette(self, new_palette):
        """Update palette when theme changes"""
        self.palette = new_palette
        p = new_palette
        self.is_dark = (self.app_state.theme_mode == "DARK")
        
        # 1. Canvas Background
        self.canvas_container.bgcolor = p["bg"]
        
        # 2. Header Style & Content
        self.header.bgcolor = p["surface"]
        self.header.border = ft.border.only(bottom=ft.BorderSide(1, p["border_opacity"]))
        
        # Update text and icon colors in header
        if isinstance(self.header.content, ft.Row):
            row = self.header.content
            # Button
            if len(row.controls) > 0 and isinstance(row.controls[0], ft.IconButton):
                row.controls[0].icon_color = p["text"]
            # Title
            if len(row.controls) > 1 and isinstance(row.controls[1], ft.Text):
                row.controls[1].color = p["text"]

        # 3. Details Panel Style
        self.details_panel.bgcolor = ft.Colors.with_opacity(0.95, p["surface"])
        self.details_panel.border = ft.border.all(1, p["border_opacity"])
        
        # Redraw detail panel if seat is selected
        if self.selected_seat:
            self._on_seat_click(self.selected_seat)
        
        # Redraw seat map (to update colors)
        target_flight = self.app_state.selected_offer_group
        if target_flight:
             asyncio.create_task(self._load_data(target_flight["offers"]))
             
        try:
            self.update()
        except:
            pass
