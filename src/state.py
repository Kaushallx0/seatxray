import flet as ft
import time

class AppState:
    """
    アプリケーション全体の共有状態を管理するクラス。
    画面遷移(Viewの再生成)またいで保持すべきデータは全てここに置く。
    """
    def __init__(self):
        # 検索結果のキャッシュ (戻ったときに再検索させないため)
        self.offers: list = []
        
        # 選択されたフライト(詳細画面用)
        # { "offers": [...], "identity": ..., "route": ... } のような構造
        self.selected_offer_group: dict = None
        
        # テーマ設定 (DARK/LIGHT)
        self.theme_mode: str = "DARK"
        
        # 座席マップキャッシュ {key: (data, timestamp, ttl)}
        # キャッシュヘッダーまたは最大6時間で揮発
        self._seatmap_cache: dict = {}
        self._cache_ttl_default = 6 * 60 * 60  # 6時間（フォールバック）
    
    def get_seatmap_cache(self, key: str):
        """キャッシュから座席データを取得。期限切れなら None"""
        if not key or key not in self._seatmap_cache:
            return None
        
        data, timestamp, ttl = self._seatmap_cache[key]
        if time.time() - timestamp > ttl:
            # 期限切れ - 削除して None を返す
            del self._seatmap_cache[key]
            return None
        
        return data
    
    def set_seatmap_cache(self, key: str, data, ttl: int = None):
        """座席データをキャッシュに保存"""
        if key:
            cache_ttl = ttl if ttl else self._cache_ttl_default
            self._seatmap_cache[key] = (data, time.time(), cache_ttl)
    
    def clear_expired_cache(self):
        """期限切れキャッシュをクリア"""
        now = time.time()
        expired_keys = [
            k for k, (_, ts, ttl) in self._seatmap_cache.items()
            if now - ts > ttl
        ]
        for k in expired_keys:
            del self._seatmap_cache[k]


