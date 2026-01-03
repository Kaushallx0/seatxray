import flet as ft
from services.amadeus_client import AmadeusClient
from theme import get_color_palette, COLOR_ACCENT
import asyncio


def create_card(title, subtitle, content_list, palette):
    """カードUIを生成するヘルパー関数"""
    p = palette
    return ft.Container(
        bgcolor=p["surface"],
        border_radius=12,
        padding=24,
        margin=ft.margin.only(bottom=15),
        width=700,  # 固定幅でカードを適切なサイズに
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.CIRCLE, size=12, color=COLOR_ACCENT),
                ft.Text(title, size=22, weight="bold", color=p["text"]),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            (subtitle if isinstance(subtitle, ft.Control) else ft.Text(subtitle, size=16, color=p["text_secondary"])) if subtitle else ft.Container(),
            ft.Container(height=10),
            *content_list
        ], spacing=8)
    )


class SettingsContent(ft.Column):
    def __init__(self, page: ft.Page, app_state, amadeus: AmadeusClient, on_theme_toggle=None):
        self.page_ref = page
        self.app_state = app_state
        self.amadeus = amadeus
        self.on_theme_toggle = on_theme_toggle
        
        self.is_dark = (app_state.theme_mode == "DARK")
        self.palette = get_color_palette(self.is_dark)
        
        # Refs
        self.api_key_ref = ft.Ref[ft.TextField]()
        self.api_secret_ref = ft.Ref[ft.TextField]()
        self.status_text_ref = ft.Ref[ft.Text]()
        self.status_container_ref = ft.Ref[ft.Container]()
        self.stats_search_ref = ft.Ref[ft.Text]()
        self.stats_seatmap_ref = ft.Ref[ft.Text]()

        # UI構築
        controls_list = self._build_controls()

        super().__init__(
            controls=controls_list,
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )
        
        asyncio.create_task(self._load_settings())
        asyncio.create_task(self._refresh_stats())

    def _build_controls(self):
        p = self.palette
        
        # API Card
        api_card = create_card(
            "Amadeus API 接続設定",
            ft.Text("Amadeus APIキーを取得し、以下に入力してください。", color=p["text_secondary"]),
            [
                ft.TextField(
                    ref=self.api_key_ref,
                    label="API Key",
                    password=True,
                    can_reveal_password=True,
                    border_color=p["border"],
                    color=p["text"],
                    text_size=18,
                    width=500,
                ),
                ft.TextField(
                    ref=self.api_secret_ref,
                    label="API Secret",
                    password=True,
                    can_reveal_password=True,
                    border_color=p["border"],
                    color=p["text"],
                    text_size=18,
                    width=500,
                ),
                ft.Row([
                    ft.ElevatedButton(
                        content=ft.Text("保存して接続テスト", size=16),
                        on_click=self._on_save,
                        bgcolor=COLOR_ACCENT,
                        color="white",
                        height=45
                    ),
                    ft.OutlinedButton(
                        content=ft.Text("設定を削除", size=16),
                        on_click=self._on_reset,
                        style=ft.ButtonStyle(color=p["text"]),
                        height=45
                    ),
                ]),
                ft.Container(
                    ref=self.status_container_ref,
                    content=ft.Text("", ref=self.status_text_ref, size=16, color=p["text"]),
                    visible=False,
                    height=30,
                )
            ],
            palette=p
        )

        # Appearance Card
        appearance_card = create_card(
            "表示設定",
            None,
            [
                ft.Row([
                    ft.Icon(ft.Icons.DARK_MODE, color=p["text"], size=24),
                    ft.Text("ダークモード", size=20, color=p["text"]),
                    ft.Container(expand=True),
                    ft.Switch(
                        value=self.is_dark,
                        on_change=self._on_theme_change,
                        active_color=ft.Colors.BLUE
                    )
                ], alignment=ft.MainAxisAlignment.START)
            ],
            palette=p
        )

        # Stats Card
        stats_card = create_card(
            "API利用統計",
            None,
            [
                ft.Row([
                    ft.Column([
                        ft.Text("検索実行", size=16, color=p["text_secondary"]),
                        ft.Text("-", ref=self.stats_search_ref, size=24, weight="bold", color=p["text"])
                    ]),
                    ft.Container(width=50),
                    ft.Column([
                        ft.Text("座席表取得", size=16, color=p["text_secondary"]),
                        ft.Text("-", ref=self.stats_seatmap_ref, size=24, weight="bold", color=p["text"])
                    ]),
                ]),
                ft.Container(height=10),
                ft.Text(
                    "※ この数値は目安です。正確な利用回数はAmadeus開発者ポータルで確認してください。",
                    size=14,
                    color=p["text_secondary"]
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Text("Amadeus for Developers API Usage", color=COLOR_ACCENT, size=16),
                        ft.Icon(ft.Icons.OPEN_IN_NEW, color=COLOR_ACCENT, size=16)
                    ], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    on_click=self._on_url_click,
                    on_hover=self._on_link_hover,
                    padding=ft.Padding(10, 5, 10, 5),
                    border_radius=8,
                    ink=True
                )
            ],
            palette=p
        )

        return [
            ft.Container(
                content=ft.Column([
                    ft.Text("設定", size=48, weight="bold", color=p["text"]),
                    ft.Text("API接続設定とモード管理", size=20, color=p["text_secondary"]),
                    ft.Divider(height=30, color="transparent"),
                    api_card,
                    appearance_card,
                    stats_card,
                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.START),
                padding=40,
            )
        ]

    def update_palette(self, new_palette):
        """テーマ変更時にパレットを更新（ビュー再作成なし）"""
        self.palette = new_palette
        self.is_dark = (self.app_state.theme_mode == "DARK")
        
        # コントロールを再構築
        new_controls = self._build_controls()
        self.controls.clear()
        self.controls.extend(new_controls)
        
        # データを再ロード（UI再構築で値が消えるため）
        asyncio.create_task(self._load_settings())
        asyncio.create_task(self._refresh_stats())
        
        try:
            self.update()
        except:
            pass

    async def _refresh_stats(self):
        # 遅延なしで即座に読み込み
        s = await self.page_ref.shared_preferences.get("stats_search") or 0
        m = await self.page_ref.shared_preferences.get("stats_seatmap") or 0
        if self.stats_search_ref.current:
            self.stats_search_ref.current.value = f"{s} 回"
            self.stats_search_ref.current.update()
        if self.stats_seatmap_ref.current:
            self.stats_seatmap_ref.current.value = f"{m} 回"
            self.stats_seatmap_ref.current.update()

    async def _load_settings(self):
        # 遅延なしで即座に読み込み
        key = await self.page_ref.shared_preferences.get("amadeus_api_key")
        sec = await self.page_ref.shared_preferences.get("amadeus_api_secret")
        if self.api_key_ref.current:
            self.api_key_ref.current.value = key if key else ""
            self.api_key_ref.current.update()
        if self.api_secret_ref.current:
            self.api_secret_ref.current.value = sec if sec else ""
            self.api_secret_ref.current.update()

    async def _on_save(self, e):
        key = self.api_key_ref.current.value
        sec = self.api_secret_ref.current.value
        
        self.status_container_ref.current.visible = True
        self.status_text_ref.current.value = "接続テスト中..."
        self.status_text_ref.current.color = self.palette["text"]
        self.status_container_ref.current.update()
        
        await self.page_ref.shared_preferences.set("amadeus_api_key", key)
        await self.page_ref.shared_preferences.set("amadeus_api_secret", sec)
        
        self.amadeus.update_credentials(key, sec)
        success = await self.amadeus.authenticate()
        
        if success:
            self.status_text_ref.current.value = "接続成功！設定を保存しました。"
            self.status_text_ref.current.color = ft.Colors.GREEN
        else:
            self.status_text_ref.current.value = "認証エラー: キーを確認してください。"
            self.status_text_ref.current.color = ft.Colors.RED
        self.status_text_ref.current.update()
        self.status_container_ref.current.update()

    async def _on_reset(self, e):
        await self.page_ref.shared_preferences.remove("amadeus_api_key")
        await self.page_ref.shared_preferences.remove("amadeus_api_secret")
        self.api_key_ref.current.value = ""
        self.api_secret_ref.current.value = ""
        self.api_key_ref.current.update()
        self.api_secret_ref.current.update()
        
        self.amadeus.update_credentials(None, None)
        self.status_container_ref.current.visible = True
        self.status_text_ref.current.value = "デモモードにリセットしました。"
        self.status_text_ref.current.color = self.palette["text"]
        self.status_container_ref.current.update()

    async def _on_theme_change(self, e):
        is_dark = e.control.value
        self.app_state.theme_mode = "DARK" if is_dark else "LIGHT"
        await self.page_ref.shared_preferences.set("theme_mode", self.app_state.theme_mode)
        if self.on_theme_toggle:
            await self.on_theme_toggle()
    async def _on_url_click(self, e):
        await e.page.launch_url("https://developers.amadeus.com/my-apps/api-usage")

    def _on_link_hover(self, e):
        e.control.bgcolor = ft.Colors.with_opacity(0.1, COLOR_ACCENT) if e.data == "true" else None
        e.control.update()
