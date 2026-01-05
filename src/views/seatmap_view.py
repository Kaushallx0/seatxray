# Copyright (c) 2026 SeatXray Developers
# Licensed under the terms of the GNU Affero General Public License (AGPL) version 3.
# See LICENSE file in the project root for details.

"""SeatMap View. Root container for seat map."""

import flet as ft
import asyncio
import traceback
from services.seat_service import SeatService
from components.seat_canvas import SeatCanvas
from components.window_header import CustomWindowHeader
from theme import get_color_palette, COLOR_ACCENT, glass_style
from utils.i18n import TranslationService

class SeatMapView(ft.View):
    def __init__(self, page: ft.Page, app_state, amadeus):
        self.i18n = TranslationService.get_instance()
        self.page_ref = page
        self.app_state = app_state
        self.amadeus = amadeus
        
        self.is_dark = (app_state.theme_mode == "DARK")
        self.palette = get_color_palette(self.is_dark)
        self.seat_service = SeatService()
        
        # Components
        self.canvas_container = ft.Container(expand=True, bgcolor=self.palette["bg"])
        self.details_panel = self._build_details_panel()
        
        # Trigger data load
        # Get FlightOffer from navigation
        target_flight = self.app_state.selected_offer_group
        if target_flight:
            # We can start loading immediately
            # If flight info is missing (e.g. reload), show error
            asyncio.create_task(self._load_data(target_flight["offers"]))
        
        super().__init__(
            route="/seatmap",
            padding=0,
            bgcolor=self.palette["bg"],
            controls=[
                CustomWindowHeader(page),
                ft.Stack(
                    [
                        self.canvas_container,
                        self._build_back_button(),
                        self.details_panel
                    ],
                    expand=True
                )
            ]
        )

    def _build_back_button(self):
        p = self.palette
        return ft.Container(
            content=ft.IconButton(
                ft.Icons.ARROW_BACK, 
                on_click=lambda _: self.page_ref.go("/"), # Go back to root
                icon_color=p["text"]
            ),
            top=10, left=10,
            bgcolor=ft.Colors.with_opacity(0.8, p["bg"]),
            border=ft.Border.all(1, p["border_opacity"]),
            border_radius=50
        )

    def _build_details_panel(self):
        p = self.palette
        return ft.Container(
            visible=False,
            bottom=20, left=20, right=20,
            content=ft.Row([], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            # Glass style manually applied since helper might need update
            bgcolor=ft.Colors.with_opacity(0.95, p["surface"]),
            border_radius=16,
            padding=20,
            border=ft.Border.all(1, p["border_opacity"]),
            blur=ft.Blur(20, 20)
        )

    async def _load_data(self, offers):
        p = self.palette
        tr = self.i18n.tr
        
        self.canvas_container.content = ft.Container(
            content=ft.Column([
                ft.ProgressRing(color=COLOR_ACCENT),
                ft.Text(tr("seatmap.loading"), color=p["text"])
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment(0, 0) # Corrected alignment
        )
        self.page_ref.update()

        try:
            raw_response = await self.amadeus.get_seatmap(offers)
            master_map, facilities = self.seat_service.process_seatmaps_batch(raw_response)
            
            if not master_map:
                self.canvas_container.content = ft.Container(
                    ft.Text(tr("seatmap.fetch_error"), color="red"),
                    alignment=ft.Alignment(0, 0)
                )
            else:
                self.canvas_container.content = SeatCanvas(
                    master_map, 
                    facilities, 
                    self._on_seat_click, 
                    palette=p
                )
        except Exception as e:
            traceback.print_exc()
            self.canvas_container.content = ft.Text(f"{tr('common.error')}: {e}", color="red")
            
        self.page_ref.update()

    def _on_seat_click(self, seat_data):
        p = self.palette
        tr = self.i18n.tr
        number = seat_data.get("number", "??")
        status = seat_data.get("_final_status", "UNKNOWN")
        pricing = seat_data.get("travelerPricing", [{}])[0]
        if status == "UNKNOWN": status = pricing.get("seatAvailabilityStatus", "UNKNOWN")
        
        STATUS_MAP = {
            "AVAILABLE": tr("seatmap.status_available"), 
            "OCCUPIED": tr("seatmap.status_occupied"), 
            "BLOCKED": tr("seatmap.status_blocked")
        }
        codes = seat_data.get("characteristicsCodes", [])
        features = []
        if "E" in codes: features.append((tr("seatmap.feature_exit"), ft.Icons.EMERGENCY))
        if "L" in codes: features.append((tr("seatmap.feature_legroom"), ft.Icons.EXPAND))

        # Old simple layout restored
        feature_layout = []
        for label, icon in features:
             feature_layout.append(ft.Row([ft.Icon(icon), ft.Text(label)]))

        self.details_panel.content = ft.Row([
            ft.Column([
                ft.Text(tr("seatmap.seat_number", number=number), size=28, weight="bold", color=p["text"]),
                ft.Text(STATUS_MAP.get(status, status), size=18, color=COLOR_ACCENT if status=="AVAILABLE" else p["text_secondary"]),
                ft.Column(feature_layout, spacing=2)
            ]),
            ft.IconButton(ft.Icons.CLOSE, on_click=lambda e: self._close_panel(), icon_color=p["text"])
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        self.details_panel.visible = True
        self.page_ref.update()

    def _close_panel(self):
        self.details_panel.visible = False
        self.page_ref.update()
