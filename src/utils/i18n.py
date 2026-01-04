import json
import os
import aiofiles
from flet import Page

class TranslationService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TranslationService, cls).__new__(cls)
            cls._instance.current_locale = "ja"
            cls._instance.translations = {}
            cls._instance.airports = []
        return cls._instance

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls()
        return cls._instance

    async def init_locale(self, page: Page):
        """
        Detects locale from preference or system, then loads translations.
        Priority:
        1. User Preference (client_storage 'seatxray_locale')
        2. System Locale (locale.getdefaultlocale)
        3. Default (en)
        """
        target_locale = "en" # Default fallback
        
        # 1. Try Preference
        try:
            # Use shared_preferences for persistence across sessions (Flet 1.0)
            pref = await page.shared_preferences.get("seatxray_locale")
            if pref and pref in ["ja", "en"]: 
                target_locale = pref
                print(f"[I18n] Used user preference: {target_locale}")
                await self.load_translations(target_locale)
                return
        except Exception as e:
            print(f"[I18n] Failed to read preference: {e}")

        # 2. Try System Locale
        try:
            import locale
            # getdefaultlocale is deprecated but still standard for this use case in non-GUI apps
            # For robust GUI scenarios, we might check page.client_IP or headers if web.
            # But for Desktop Flet:
            sys_lang_code, _ = locale.getdefaultlocale()
            print(f"[I18n] Detected system locale: {sys_lang_code}")
            
            if sys_lang_code:
                if sys_lang_code.startswith("ja"):
                    target_locale = "ja"
                # Future expansion:
                # elif sys_lang_code.startswith("de"): target_locale = "de"
                else:
                    target_locale = "en"
        except Exception as e:
            print(f"[I18n] System locale detection failed: {e}")

        print(f"[I18n] Auto-detected locale: {target_locale}")
        await self.load_translations(target_locale)

    async def load_translations(self, locale: str, assets_dir: str = "assets"):
        """
        Loads the main translation dictionary (e.g., ja.json)
        and the airport database (e.g., locales/ja/airports.json).
        """
        self.current_locale = locale
        
        # 1. Load UI Strings
        # Robust path resolution
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # src/
        locale_path = os.path.join(base_dir, "assets", "locales", f"{locale}.json")
        
        try:
            async with aiofiles.open(locale_path, mode='r', encoding='utf-8') as f:
                content = await f.read()
                self.translations = json.loads(content)
        except Exception as e:
            print(f"[I18n] Failed to load UI strings for {locale}: {e}")
            self.translations = {}

        # 2. Load Airport Database
        airport_path = os.path.join(base_dir, "assets", "locales", locale, "airports.json")
        try:
            async with aiofiles.open(airport_path, mode='r', encoding='utf-8') as f:
                content = await f.read()
                self.airports = json.loads(content)
                print(f"[I18n] Loaded {len(self.airports)} airports for {locale}")
        except Exception as e:
            print(f"[I18n] Failed to load airports for {locale}: {e}")
            self.airports = []

    def tr(self, key: str, **kwargs) -> str:
        """
        Translate a key (e.g., 'search.header_title').
        Supports nested keys with dot notation.
        Supports format arguments (e.g., {count}).
        """
        keys = key.split('.')
        value = self.translations
        
        try:
            for k in keys:
                value = value[k]
            
            if isinstance(value, str):
                return value.format(**kwargs)
            return str(value)
        except (KeyError, TypeError):
            return key

    def get_airports(self):
        return self.airports

def get_default_currency(locale: str) -> str:
    """
    Maps locale to default currency.
    """
    currency_map = {
        "ja": "JPY",
        "en": "USD",
        "ko": "KRW",
        "zh": "CNY",
        "th": "THB",
        "sg": "SGD",
    }
    return currency_map.get(locale, "USD")

def format_currency(amount: float, currency: str) -> str:
    """
    Formats currency with symbol and appropriate decimal places.
    """
    currency_symbols = {
        "JPY": "¥",
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "AUD": "A$",
        "CAD": "C$",
        "KRW": "₩",
        "CNY": "¥",
        "SGD": "S$",
        "THB": "฿",
    }
    
    # Currencies without decimal places
    no_decimal = ["JPY", "KRW"]
    
    symbol = currency_symbols.get(currency, currency)
    
    if currency in no_decimal:
        return f"{symbol}{int(amount):,}"
    else:
        return f"{symbol}{amount:,.2f}"
