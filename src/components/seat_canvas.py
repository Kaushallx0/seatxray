# Copyright (c) 2026 SeatXray Developers
# Licensed under the terms of the GNU Affero General Public License (AGPL) version 3.
# See LICENSE file in the project root for details.

"""Seat Canvas. Renders seat map via Flet Canvas."""

import flet as ft
import re
from utils.i18n import TranslationService

def SeatCanvas(seats: dict, facilities: list, on_seat_click: callable, palette: dict, is_mobile: bool = False):
    """
    Function to render the seat map.
    Uses characteristicsCodes (W=Window, A=Aisle) to accurately detect aisle positions.
    """
    i18n = TranslationService.get_instance()
    
    # --- Constants (adjusted for mobile) ---
    if is_mobile:
        FUSELAGE_WIDTH = 540  # Increased for wide rows
        SEAT_GAP = 3
        AISLE_GAP = 14
        MIN_SEAT_SIZE = 44  # Larger seats for easy touch
        MAX_SEAT_SIZE = 52
    else:
        FUSELAGE_WIDTH = 650
        SEAT_GAP = 4
        AISLE_GAP = 20
        MIN_SEAT_SIZE = 40
        MAX_SEAT_SIZE = 56
    
    # --- Data Organization Logic ---
    cabin_rows = {}  # cabin -> { row_num: [seats...] }
    CABIN_ORDER = ["FIRST", "BUSINESS", "PREMIUM_ECONOMY", "ECONOMY"]
    
    # Collect characteristics for each column character (for aisle detection)
    column_characteristics = {}  # col_letter -> set of characteristics
    
    for seat_num, seat in seats.items():
        cabin = seat.get("cabin", "ECONOMY")
        
        # Extract row number from seat number (e.g. "25A" -> 25)
        match = re.match(r'(\d+)', seat_num)
        if match:
            row = int(match.group(1))
        else:
            row = 0
        
        # Extract column character from seat number (e.g. "25A" -> "A")
        col_char = re.sub(r'\d+', '', seat_num).upper()
        if not col_char:
            col_char = "?"
        
        # Collect characteristic codes
        chars = seat.get("characteristicsCodes", [])
        if col_char not in column_characteristics:
            column_characteristics[col_char] = set()
        column_characteristics[col_char].update(chars)
        
        if cabin not in cabin_rows:
            cabin_rows[cabin] = {}
        if row not in cabin_rows[cabin]:
            cabin_rows[cabin][row] = []
            
        cabin_rows[cabin][row].append({
            "num": seat_num, 
            "row": row, 
            "col_char": col_char,  # Keep as char
            "cabin": cabin, 
            "data": seat,
            "chars": chars
        })

    
    # --- UI Construction ---
    ui_controls = []
    
    for cabin in CABIN_ORDER:
        if cabin not in cabin_rows:
            continue
            
        cabin_header_key = f"seatmap.cabin_{cabin.lower()}"
        cabin_name = i18n.tr(cabin_header_key)
        
        header = ft.Container(
            content=ft.Row([
                ft.Container(width=4, height=18, bgcolor="#00b96b", border_radius=2),
                ft.Text(
                    cabin_name, 
                    size=16, weight="bold", color=palette["text"],
                ),
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            width=FUSELAGE_WIDTH,
            padding=ft.Padding.only(left=4, right=4, top=16, bottom=8),
        )
        ui_controls.append(header)
        
        rows_in_cabin = cabin_rows[cabin]
        sorted_rows = sorted(rows_in_cabin.keys())
        
        # --- Collect column info specific to this cabin ---
        cabin_col_chars = {} # col -> set of characteristics
        for seats_list in rows_in_cabin.values():
            for s in seats_list:
                col = s["col_char"]
                if col not in cabin_col_chars: cabin_col_chars[col] = set()
                cabin_col_chars[col].update(s["chars"])
        
        cabin_col_order = sorted(cabin_col_chars.keys())
        
        # --- Per-cabin aisle detection ---
        cabin_aisles = set()
        for i in range(len(cabin_col_order) - 1):
            col_left = cabin_col_order[i]
            col_right = cabin_col_order[i+1]
            
            # Find a row where these two columns coexist
            common_rows = []
            for r in rows_in_cabin:
                seats = rows_in_cabin[r]
                row_cols = {s["col_char"]: s for s in seats}
                if col_left in row_cols and col_right in row_cols:
                    common_rows.append(row_cols)
            
            is_aisle = False
            if common_rows:
                # If a coexisting row exists:
                # If "Left is Aisle AND Right is Aisle" in all coexisting rows, assume an aisle
                all_separated = True
                for row_map in common_rows:
                    left_is_aisle = 'A' in row_map[col_left]["chars"]
                    right_is_aisle = 'A' in row_map[col_right]["chars"]
                    
                    if not (left_is_aisle and right_is_aisle):
                        all_separated = False
                        break
                
                if all_separated:
                    is_aisle = True
            else:
                # If no coexisting row (rare case)
                # Default behavior: If both are "Aisle somewhere", treat as aisle
                left_ever_aisle = 'A' in cabin_col_chars.get(col_left, set())
                right_ever_aisle = 'A' in cabin_col_chars.get(col_right, set())
                if left_ever_aisle and right_ever_aisle:
                    is_aisle = True

            if is_aisle:
                cabin_aisles.add(col_left)
        
        # Calculate seat size (including aisles)
        num_cols = len(cabin_col_order)
        num_aisles = len(cabin_aisles)
        total_gaps = (num_cols - 1) * SEAT_GAP + num_aisles * (AISLE_GAP - SEAT_GAP)
        
        if num_cols > 0:
            raw_size = (FUSELAGE_WIDTH - total_gaps) / num_cols
            seat_size = int(max(MIN_SEAT_SIZE, min(MAX_SEAT_SIZE, raw_size)))
        else:
            seat_size = 50
        
        for row_num in sorted_rows:
            row_seats = rows_in_cabin[row_num]
            # Map by column char
            row_map = {s["col_char"]: s for s in row_seats}
            
            seat_widgets = []
            for i, col in enumerate(cabin_col_order):
                if col in row_map:
                    s = row_map[col]
                    seat_data = s["data"]
                    seat_num_str = s["num"]
                    chars = s["chars"]
                    
                    status = "AVAILABLE"
                    pricing = seat_data.get("travelerPricing", [])
                    if pricing:
                        status = pricing[0].get("seatAvailabilityStatus", "AVAILABLE")
                    
                    if status == "AVAILABLE":
                        bg_color = "#00b96b"; text_color = "white"
                    elif status == "OCCUPIED":
                        bg_color = "#555555"; text_color = "#999999"
                    else:
                        bg_color = "#ffb020"; text_color = "black"
                    
                    is_exit = "E" in chars
                    border_style = ft.Border.all(3, "#00ff88") if is_exit else None
                    
                    seat_widgets.append(ft.Container(
                        content=ft.Text(seat_num_str, size=int(seat_size * 0.30), weight="bold", color=text_color),
                        width=seat_size, height=seat_size, bgcolor=bg_color,
                        border_radius=int(seat_size * 0.15), border=border_style,
                        alignment=ft.Alignment(0, 0),
                        on_click=lambda e, sd=seat_data: on_seat_click(sd),
                        ink=True,
                    ))
                else:
                    # Empty placeholder if this column doesn't exist in this row
                    seat_widgets.append(ft.Container(width=seat_size, height=seat_size))
                
                # Add aisle gap (using cabin-specific definition)
                if col in cabin_aisles and i < len(cabin_col_order) - 1:
                    seat_widgets.append(ft.Container(width=AISLE_GAP - SEAT_GAP))

            ui_controls.append(ft.Row(
                controls=seat_widgets, spacing=SEAT_GAP, alignment=ft.MainAxisAlignment.CENTER,
            ))
    
    # Seat grid - on mobile, enable 2D scrolling by wrapping in scrollable containers
    if is_mobile:
        # Create a Column with vertical scroll that contains all rows
        # Each row has fixed width (FUSELAGE_WIDTH) to enable horizontal scroll at parent level
        inner_column = ft.Column(
            controls=ui_controls, 
            spacing=SEAT_GAP, 
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )
        # Wrap in container with fixed width for horizontal scroll
        seat_grid = ft.Container(
            content=inner_column,
            width=FUSELAGE_WIDTH,
        )
        # Outer container: horizontal scroll + vertical scroll
        seat_grid = ft.Column(
            controls=[
                ft.Row(
                    controls=[seat_grid],
                    scroll=ft.ScrollMode.AUTO,  # Horizontal scroll
                )
            ],
            scroll=ft.ScrollMode.AUTO,  # Vertical scroll
            expand=True,
        )
    else:
        seat_grid = ft.Column(
            controls=ui_controls, spacing=SEAT_GAP, scroll=ft.ScrollMode.AUTO,
            expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    
    # Legend (responsive for mobile - larger but horizontally scrollable)
    legend_icon_size = 20 if is_mobile else 24
    legend_text_size = 14 if is_mobile else 16
    legend_spacing = 12 if is_mobile else 24
    
    legend_row = ft.Row(
        controls=[
            ft.Container(width=legend_icon_size, height=legend_icon_size, bgcolor="#00b96b", border_radius=4),
            ft.Text(i18n.tr("seatmap.status_available"), size=legend_text_size, color=palette["text"]),
            ft.Container(width=legend_spacing),
            ft.Container(width=legend_icon_size, height=legend_icon_size, bgcolor="#555555", border_radius=4),
            ft.Text(i18n.tr("seatmap.status_occupied"), size=legend_text_size, color=palette["text_secondary"]),
            ft.Container(width=legend_spacing),
            ft.Container(width=legend_icon_size, height=legend_icon_size, bgcolor="#ffb020", border_radius=4),
            ft.Text(i18n.tr("seatmap.status_blocked"), size=legend_text_size, color=palette["text_secondary"]),
        ],
        alignment=ft.MainAxisAlignment.CENTER if not is_mobile else ft.MainAxisAlignment.START,
        spacing=6,
    )
    
    # Wrap in horizontal scroll container for mobile
    if is_mobile:
        legend = ft.Container(
            content=ft.Row([legend_row], scroll=ft.ScrollMode.AUTO),
            padding=ft.Padding(8, 8, 8, 8),
        )
    else:
        legend = legend_row
    
    return ft.Column(
        controls=[
            ft.Container(
                content=legend, padding=ft.Padding.symmetric(vertical=14, horizontal=20),
                bgcolor=ft.Colors.with_opacity(0.08, palette["text"]), border_radius=12,
            ),
            ft.Container(height=16),
            seat_grid,
        ],
        expand=True, spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
