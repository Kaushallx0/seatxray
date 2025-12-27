import flet as ft
from theme import get_color_palette
from services.amadeus_client import AmadeusClient

class SettingsView(ft.Container):
    def __init__(self, page: ft.Page, amadeus: AmadeusClient, saved_id: str, saved_secret: str, on_reset: callable = None, on_theme_change: callable = None, **kwargs):
        super().__init__(expand=True, **kwargs)
        self.page_ref = page
        self.amadeus = amadeus
        self.saved_id = saved_id
        self.saved_secret = saved_secret
        self.on_reset = on_reset
        self.on_theme_change = on_theme_change
        
        self.is_dark = page.theme_mode == ft.ThemeMode.DARK
        self.palette = get_color_palette(self.is_dark)

        # Controls
        self.client_id_field = None
        self.client_secret_field = None
        self.status_text = None
        self.theme_switch = None
        self.header_title = None
        self.header_sub = None
        self.group_title = None
        self.group_desc = None
        self.mode_label = None

        self._build_ui()

    def _build_ui(self):
        PALETTE = self.palette
        
        # UI Constants
        LABEL_SIZE = 16
        
        self.client_id_field = ft.TextField(
            label="API Key (Client ID)", 
            value=self.saved_id if self.saved_id else "",
            password=True, can_reveal_password=True,
            border_color=PALETTE["border"], color=PALETTE["text"],
            label_style=ft.TextStyle(size=LABEL_SIZE, color=PALETTE["text_secondary"])
        )
        
        self.client_secret_field = ft.TextField(
            label="API Secret", 
            value=self.saved_secret if self.saved_secret else "",
            password=True, can_reveal_password=True,
            border_color=PALETTE["border"], color=PALETTE["text"],
            label_style=ft.TextStyle(size=LABEL_SIZE, color=PALETTE["text_secondary"])
        )
        
        self.status_text = ft.Text("", color=PALETTE["text"])
        
        self.theme_switch = ft.Switch(
            value=self.is_dark,
            on_change=self._handle_theme_toggle,
            active_color=ft.Colors.BLUE,
        )

        self.header_title = ft.Text("設定", size=40, weight="bold", color=PALETTE["text"])
        self.header_sub = ft.Text("API接続設定とモード管理", size=16, color=PALETTE["text_secondary"])
        
        self.group_title = ft.Text("Amadeus Developers API", size=24, weight="bold", color=PALETTE["text"])
        self.group_desc = ft.Text("本番データを使用するには有効な API Key を入力してください。", size=14, color=PALETTE["text_secondary"])
        self.mode_label = ft.Text("ダークモード", size=18, color=PALETTE["text"])

        # Appearance Card
        self.appearance_card = ft.Container(
            content=ft.Column([
                ft.Text("表示設定", size=24, weight="bold", color=PALETTE["text"]),
                ft.Container(height=10),
                ft.Row([
                    ft.Icon(ft.Icons.DARK_MODE, color=PALETTE["text"]),
                    self.mode_label,
                    ft.Container(expand=True),
                    self.theme_switch
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]),
            padding=20, border_radius=10,
            border=ft.Border.all(1, PALETTE["border_opacity"]),
            bgcolor=ft.Colors.with_opacity(0.05, PALETTE["surface"])
        )

        # Stats Card
        self.stats_text_search = ft.Text("-", size=20, weight="bold", color=PALETTE["text"])
        self.stats_text_seatmap = ft.Text("-", size=20, weight="bold", color=PALETTE["text"])
        
        self.stats_note = ft.Text(
            "※ この数値は目安です。正確な利用回数はAmadeus開発者ポータルで確認してください。",
            size=12, color=PALETTE["text_secondary"]
        )
        
        self.stats_link = ft.TextButton(
            "Amadeus My Apps を開く",
            icon=ft.Icons.OPEN_IN_NEW,
            url="https://developers.amadeus.com/my-apps/"
        )
        
        self.stats_card = ft.Container(
            content=ft.Column([
                ft.Text("API利用統計", size=24, weight="bold", color=PALETTE["text"]),
                ft.Container(height=10),
                ft.Row([
                    ft.Column([ft.Text("検索実行", size=14, color=PALETTE["text_secondary"]), self.stats_text_search], expand=True),
                    ft.Container(width=20),
                    ft.Column([ft.Text("座席表取得", size=14, color=PALETTE["text_secondary"]), self.stats_text_seatmap], expand=True),
                ]),
                ft.Container(height=10),
                self.stats_note,
                self.stats_link
            ]),
            padding=20, border_radius=10,
            border=ft.Border.all(1, PALETTE["border_opacity"]),
            bgcolor=ft.Colors.with_opacity(0.05, PALETTE["surface"])
        )

        # Layout
        self.content = ft.Column(
            controls=[
                self.header_title,
                self.header_sub,
                ft.Divider(height=30, color="transparent"),
                
                ft.Container(
                    content=ft.Column([
                        self.group_title,
                        self.group_desc,
                        ft.Container(height=10),
                        self.client_id_field,
                        self.client_secret_field,
                        ft.Container(height=10),
                        ft.Row([
                            ft.FilledButton("接続テスト", icon=ft.Icons.NETWORK_CHECK, on_click=self.test_connection),
                            ft.FilledButton("保存", icon=ft.Icons.SAVE, on_click=self.save_credentials),
                            ft.OutlinedButton("デモモードに戻す", icon=ft.Icons.RESTORE, on_click=self.reset_to_demo, style=ft.ButtonStyle(color=ft.Colors.RED))
                        ]),
                        ft.Container(height=10),
                        self.status_text
                    ]),
                    padding=20, border_radius=10, 
                    border=ft.Border.all(1, PALETTE["border_opacity"]),
                    bgcolor=ft.Colors.with_opacity(0.05, PALETTE["surface"])
                ),
                
                ft.Divider(height=20, color="transparent"),
                self.appearance_card,
                ft.Divider(height=20, color="transparent"),
                self.stats_card
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

    async def refresh_stats(self):
        s = await self.page_ref.shared_preferences.get("stats_search") or 0
        m = await self.page_ref.shared_preferences.get("stats_seatmap") or 0
        self.stats_text_search.value = f"{s} 回"
        self.stats_text_seatmap.value = f"{m} 回"
        self.update()

    def _handle_theme_toggle(self, e):
        if self.on_theme_change:
            import asyncio
            asyncio.create_task(self.on_theme_change(e)) 

    def update_theme_mode(self, is_dark):
        self.is_dark = is_dark
        p = get_color_palette(is_dark)
        self.palette = p
        
        # update controls
        self.client_id_field.border_color = p["border"]
        self.client_id_field.color = p["text"]
        self.client_id_field.label_style.color = p["text_secondary"]
        
        self.client_secret_field.border_color = p["border"]
        self.client_secret_field.color = p["text"]
        self.client_secret_field.label_style.color = p["text_secondary"]
        
        self.header_title.color = p["text"]
        self.header_sub.color = p["text_secondary"]
        self.group_title.color = p["text"]
        self.group_desc.color = p["text_secondary"]
        self.mode_label.color = p["text"]
        self.status_text.color = p["text"]
        
        # API Card
        api_card = self.content.controls[3]
        api_card.border = ft.Border.all(1, p["border_opacity"])
        api_card.bgcolor = ft.Colors.with_opacity(0.05, p["surface"])
        
        # Appearance Card
        app_card = self.appearance_card
        app_card.border = ft.Border.all(1, p["border_opacity"])
        app_card.bgcolor = ft.Colors.with_opacity(0.05, p["surface"])
        app_card.content.controls[0].color = p["text"] # Title
        app_card.content.controls[2].controls[0].color = p["text"] # Icon

        # Stats Card
        st_card = self.stats_card
        st_card.border = ft.Border.all(1, p["border_opacity"])
        st_card.bgcolor = ft.Colors.with_opacity(0.05, p["surface"])
        st_card.content.controls[0].color = p["text"]
        
        row = st_card.content.controls[2]
        row.controls[0].controls[0].color = p["text_secondary"]
        row.controls[2].controls[0].color = p["text_secondary"]
        
        self.stats_text_search.color = p["text"]
        self.stats_text_seatmap.color = p["text"]

        self.theme_switch.value = is_dark
        self.update()

    async def test_connection(self, e):
        self.status_text.value = "接続テスト中..."
        self.status_text.color = self.palette["text"]
        self.update()
        
        test_id = self.client_id_field.value
        test_secret = self.client_secret_field.value
        
        if not test_id or not test_secret:
            self.status_text.value = "エラー: API KeyとSecretを入力してください。"
            self.status_text.color = ft.Colors.RED
            self.update()
            return
        
        # Create a temporary client to test creds
        temp_client = AmadeusClient(test_id, test_secret)
        # Even with args, AmadeusClient might fallback to Demo if args are empty strings? 
        # But we checked 'not test_id'.
        # However AmadeusClient doesn't authenticate on init.
        
        success = await temp_client.authenticate()
        
        if success:
            self.status_text.value = "接続成功！有効な認証情報です。"
            self.status_text.color = ft.Colors.GREEN
        else:
            self.status_text.value = "接続失敗。IDまたはSecretを確認してください。"
            self.status_text.color = ft.Colors.RED
        self.update()

    async def save_credentials(self, e):
        await self.page_ref.shared_preferences.set("amadeus_client_id", self.client_id_field.value)
        await self.page_ref.shared_preferences.set("amadeus_client_secret", self.client_secret_field.value)
        
        self.status_text.value = "設定を保存し、即時反映しました。"
        self.status_text.color = ft.Colors.GREEN
        self.update()
        
        # Update current client if possible
        if self.amadeus:
            self.amadeus.update_credentials(self.client_id_field.value, self.client_secret_field.value)
            await self.amadeus.authenticate()

    async def reset_to_demo(self, e):
        # 認証情報をクリア
        await self.page_ref.shared_preferences.remove("amadeus_client_id")
        await self.page_ref.shared_preferences.remove("amadeus_client_secret")
        
        # フィールドをクリア
        self.client_id_field.value = ""
        self.client_secret_field.value = ""
        
        # AmadeusClientを即座にデモモードに切り替え
        if self.amadeus:
            self.amadeus.update_credentials(None, None)
        
        self.status_text.value = "デモモードに切り替えました。保存済みです。"
        self.status_text.color = ft.Colors.ORANGE
        self.update()
        
        if self.on_reset:
            await self.on_reset()
