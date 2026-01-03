import flet as ft
import re

def SeatCanvas(seats: dict, facilities: list, on_seat_click: callable, palette: dict):
    """
    座席表を描画する関数。
    characteristicsCodes (W=窓側, A=通路側) を使用して通路位置を正確に検出。
    """
    
    # --- 定数 ---
    FUSELAGE_WIDTH = 650
    SEAT_GAP = 4
    AISLE_GAP = 20  # 通路は広めに
    MIN_SEAT_SIZE = 40
    MAX_SEAT_SIZE = 56
    
    # --- データ整理ロジック ---
    cabin_rows = {}  # cabin -> { row_num: [seats...] }
    CABIN_ORDER = ["FIRST", "BUSINESS", "PREMIUM_ECONOMY", "ECONOMY"]
    
    # 列文字ごとの特性を収集（通路検出用）
    column_characteristics = {}  # col_letter -> set of characteristics
    
    for seat_num, seat in seats.items():
        cabin = seat.get("cabin", "ECONOMY")
        
        # 座席番号から行番号を抽出 (例: "25A" -> 25)
        match = re.match(r'(\d+)', seat_num)
        if match:
            row = int(match.group(1))
        else:
            row = 0
        
        # 座席番号からカラム文字を抽出 (例: "25A" -> "A")
        col_char = re.sub(r'\d+', '', seat_num).upper()
        if not col_char:
            col_char = "?"
        
        # 特性コードを収集
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
            "col_char": col_char,  # 文字で保持
            "cabin": cabin, 
            "data": seat,
            "chars": chars
        })

    
    # --- UI 構築 ---
    ui_controls = []
    
    for cabin in CABIN_ORDER:
        if cabin not in cabin_rows:
            continue
            
        cabin_names = {
            "FIRST": "ファーストクラス",
            "BUSINESS": "ビジネスクラス", 
            "PREMIUM_ECONOMY": "プレミアムエコノミー",
            "ECONOMY": "エコノミークラス",
        }
        
        header = ft.Container(
            content=ft.Row([
                ft.Container(width=4, height=18, bgcolor="#00b96b", border_radius=2),
                ft.Text(
                    cabin_names.get(cabin, cabin), 
                    size=16, weight="bold", color=palette["text"],
                ),
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            width=FUSELAGE_WIDTH,
            padding=ft.Padding.only(left=4, right=4, top=16, bottom=8),
        )
        ui_controls.append(header)
        
        rows_in_cabin = cabin_rows[cabin]
        sorted_rows = sorted(rows_in_cabin.keys())
        
        # --- このキャビン固有の列情報を収集 ---
        cabin_col_chars = {} # col -> set of characteristics
        for seats_list in rows_in_cabin.values():
            for s in seats_list:
                col = s["col_char"]
                if col not in cabin_col_chars: cabin_col_chars[col] = set()
                cabin_col_chars[col].update(s["chars"])
        
        cabin_col_order = sorted(cabin_col_chars.keys())
        
        # --- キャビンごとの通路検出 (Smart Logic) ---
        cabin_aisles = set()
        for i in range(len(cabin_col_order) - 1):
            col_left = cabin_col_order[i]
            col_right = cabin_col_order[i+1]
            
            # この2列が共存する行を探す
            common_rows = []
            for r in rows_in_cabin:
                seats = rows_in_cabin[r]
                row_cols = {s["col_char"]: s for s in seats}
                if col_left in row_cols and col_right in row_cols:
                    common_rows.append(row_cols)
            
            is_aisle = False
            if common_rows:
                # 共存する行がある場合：
                # 「全ての共存行において、左がAisle かつ 右がAisle」ならば通路とみなす
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
                # 共存する行がない場合（レアケース）
                # デフォルトの挙動：両方が「どこかでAisle」なら通路とする
                left_ever_aisle = 'A' in cabin_col_chars.get(col_left, set())
                right_ever_aisle = 'A' in cabin_col_chars.get(col_right, set())
                if left_ever_aisle and right_ever_aisle:
                    is_aisle = True

            if is_aisle:
                cabin_aisles.add(col_left)
        
        # 座席サイズ計算（通路込み）
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
            # 列文字でマップ化
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
                    # この行にこの列がない場合は空白プレースホルダー
                    seat_widgets.append(ft.Container(width=seat_size, height=seat_size))
                
                # 通路ギャップを追加 (キャビン固有の定義を使用)
                if col in cabin_aisles and i < len(cabin_col_order) - 1:
                    seat_widgets.append(ft.Container(width=AISLE_GAP - SEAT_GAP))

            ui_controls.append(ft.Row(
                controls=seat_widgets, spacing=SEAT_GAP, alignment=ft.MainAxisAlignment.CENTER,
            ))
    
    seat_grid = ft.Column(
        controls=ui_controls, spacing=SEAT_GAP, scroll=ft.ScrollMode.AUTO,
        expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    
    legend = ft.Row(
        controls=[
            ft.Container(width=24, height=24, bgcolor="#00b96b", border_radius=6),
            ft.Text("空席", size=16, color=palette["text"]),
            ft.Container(width=24),
            ft.Container(width=24, height=24, bgcolor="#555555", border_radius=6),
            ft.Text("指定済み", size=16, color=palette["text_secondary"]),
            ft.Container(width=24),
            ft.Container(width=24, height=24, bgcolor="#ffb020", border_radius=6),
            ft.Text("ブロック", size=16, color=palette["text_secondary"]),
            ft.Container(width=24),
            ft.Container(width=24, height=24, border=ft.Border.all(3, "#00ff88"), border_radius=6),
            ft.Text("非常口", size=16, color="#00ff88" if palette["text"] == "white" else "#009944"),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )
    
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
