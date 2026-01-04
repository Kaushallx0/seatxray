
import os
import json
import time
import asyncio
import httpx
from flet import Page
import aiofiles

# Constants
AMADEUS_BASE_URL = "https://test.api.amadeus.com"  # Use Production for release
TOKEN_URL = f"{AMADEUS_BASE_URL}/v1/security/oauth2/token"
SEARCH_URL = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
SEATMAP_URL = f"{AMADEUS_BASE_URL}/v1/shopping/seatmaps"

class AmadeusAuth(httpx.Auth):
    """
    Handles OAuth2 Token Management with Auto-Refresh (Singleton-like usage per Client)
    """
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = None
        self.expires_at = 0
        self._lock = asyncio.Lock()

    async def async_auth_flow(self, request):
        if self._is_expired():
            async with self._lock:
                if self._is_expired():
                    await self._refresh_token()
        
        request.headers["Authorization"] = f"Bearer {self.access_token}"
        yield request

    def _is_expired(self):
        # Buffer 60 seconds
        return self.access_token is None or time.time() > self.expires_at - 60

    async def _refresh_token(self):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    TOKEN_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.api_key,
                        "client_secret": self.api_secret
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                data = response.json()
                self.access_token = data["access_token"]
                self.expires_at = time.time() + data.get("expires_in", 1799)
                print(f"[AmadeusAuth] Token refreshed. Expires in {data.get('expires_in')}s")
            except Exception as e:
                print(f"[AmadeusAuth] Token refresh failed: {e}")
                # Reset to force retry next time or handle error
                self.access_token = None

class AmadeusClient:
    """
    Main Service for interacting with Amadeus API.
    Supports Demo Mode if no keys are provided.
    """
    def __init__(self, api_key=None, api_secret=None, page=None):
        self.http_client = None
        self.auth = None
        self.page = page  # For stats tracking
        self.update_credentials(api_key, api_secret)

    async def _increment_stat(self, key: str):
        """Increment API call counter in shared_preferences."""
        if not self.page:
            return
        try:
            val_str = await self.page.shared_preferences.get(key) or "0"
            await self.page.shared_preferences.set(key, str(int(val_str) + 1))
        except Exception as e:
            print(f"[AmadeusClient] Stats Error ({key}): {e}")

    def update_credentials(self, api_key=None, api_secret=None):
        """
        Updates API credentials and re-initializes the HTTP client.
        If keys are missing, falls back to Demo Mode.
        """
        self.api_key = api_key or os.getenv("AMADEUS_API_KEY")
        self.api_secret = api_secret or os.getenv("AMADEUS_API_SECRET")
        self.is_demo = not (self.api_key and self.api_secret)
        
        # Cleanup existing client if any
        if self.http_client:
            # We can't easily await here in a sync method, but typically 
            # this is called from an async context or during init.
            # In Flet, we'll call this from an async event handler.
            pass

        if not self.is_demo:
            self.auth = AmadeusAuth(self.api_key, self.api_secret)
            self.http_client = httpx.AsyncClient(
                base_url=AMADEUS_BASE_URL,
                auth=self.auth,
                headers={
                    "X-HTTP-Method-Override": "GET",
                    "Content-Type": "application/vnd.amadeus+json",
                    "Accept": "application/vnd.amadeus+json"
                }
            )
            print(f"[AmadeusClient] Initialized in LIVE mode (Key: {self.api_key[:4]}...)")
        else:
            self.auth = None
            self.http_client = None
            print("[AmadeusClient] Initialized in DEMO mode.")

    async def close(self):
        if self.http_client:
            await self.http_client.aclose()

    async def authenticate(self):
        """
        Manually triggers authentication to verify credentials.
        Returns True if successful.
        """
        if self.is_demo:
            return True
        
        if self.auth:
            try:
                await self.auth._refresh_token()
                return self.auth.access_token is not None
            except Exception as e:
                print(f"[AmadeusClient] Manual auth check failed: {e}")
                return False
        return False

    async def search_flights(self, origin: str, destination: str, date: str, time: str = None, window: str = None, carrier: str = None, currency_code: str = None):
        """
        Executes Flight Offers Search (v2).
        In Demo Mode, returns dummy data.
        In Live Mode, implements Time Slicing.
        """
        if self.is_demo:
            # Simulate network delay
            await asyncio.sleep(1) 
            # Robust path resolution compatible with packaged environments
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(base_dir, "assets", "dummy_data", "flight_offers.json")
            
            try:
                async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
                    content = await f.read()
                    return json.loads(content)
            except FileNotFoundError:
                print(f"[Error] Dummy data not found at {path}")
                return {"data": []}

        # Live Implementation (Basic for now)
        try:
            departure_range = {"date": date}
            if time:
                # API requires HH:MM:SS format
                if len(time) == 5: # e.g. "12:00"
                    time = f"{time}:00"
                departure_range["time"] = time
            if window:
                departure_range["timeWindow"] = window

            payload = {
                "currencyCode": currency_code if currency_code else "JPY",
                "originDestinations": [
                    {
                        "id": "1",
                        "originLocationCode": origin,
                        "destinationLocationCode": destination,
                        "departureDateTimeRange": departure_range
                    }
                ],
                "travelers": [{"id": "1", "travelerType": "ADULT"}],
                "sources": ["GDS"],
                "searchCriteria": {
                    "maxFlightOffers": 250,
                    "flightFilters": {
                        "connectionRestriction": {
                            "maxNumberOfConnections": 0  # Direct flights only
                        }
                    }
                }
            }
            
            # Add Airline filtering if present
            if carrier:
                payload["searchCriteria"]["flightFilters"]["carrierRestrictions"] = {
                    "includedCarrierCodes": [carrier.upper()]
                }
            
            print(f"[AmadeusClient] Search Payload: {json.dumps(payload, indent=2)}")
            
            response = await self.http_client.post(SEARCH_URL, json=payload)
            response.raise_for_status()
            
            # Track API usage
            await self._increment_stat("stats_search")
            
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"[AmadeusClient] HTTP Error: {e}")
            if e.response is not None:
                print(f"[AmadeusClient] Response: {e.response.text}")
                try:
                    return {"data": [], "errors": e.response.json().get("errors", [])}
                except:
                    pass
            return {"data": [], "errors": [str(e)]}
        except Exception as e:
            print(f"[AmadeusClient] Search failed: {e}")
            import traceback
            traceback.print_exc()
            return {"data": [], "errors": [str(e)]}

    async def get_seatmap(self, flight_offer_or_list):
        """
        Executes SeatMap Display (v1).
        Supports both single offer (dict) and batch offers (list).
        
        Args:
            flight_offer_or_list: A single FlightOffer dict or a list of FlightOffer dicts.
        """
        if self.is_demo:
            await asyncio.sleep(0.8) # Slight delay for realism
            # Use dummy wide-body seatmap data
            path = "src/assets/dummy_data/seatmap_wide.json"
            if not os.path.exists(path):
                # Fallback path adjustment
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                path = os.path.join(base_dir, "assets", "dummy_data", "seatmap_wide.json")

            try:
                async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
                    content = await f.read()
                    return json.loads(content)
            except FileNotFoundError:
                print(f"[AmadeusClient] Dummy data not found at {path}")
                return {"data": []}

        # Live Implementation
        try:
            # Prepare payload. The API expects { "data": [ offer1, offer2, ... ] }
            if isinstance(flight_offer_or_list, list):
                payload_data = flight_offer_or_list
            else:
                payload_data = [flight_offer_or_list]

            # SANITIZE: Fix missing operating carrier code (Amadeus API Requirement)
            for offer in payload_data:
                for itin in offer.get("itineraries", []):
                    for seg in itin.get("segments", []):
                        if "operating" not in seg:
                            seg["operating"] = {}
                        op = seg["operating"]
                        if "carrierCode" not in op:
                            op["carrierCode"] = seg.get("carrierCode")

            payload = {"data": payload_data}
            
            response = await self.http_client.post(SEATMAP_URL, json=payload)
            response.raise_for_status()
            
            # Track API usage
            await self._increment_stat("stats_seatmap")
            
            # Parse Cache-Control header for TTL
            cache_ttl = 6 * 60 * 60  # Fallback: 6 hours
            cache_control = response.headers.get("Cache-Control", "")
            if "max-age=" in cache_control:
                try:
                    max_age_str = cache_control.split("max-age=")[1].split(",")[0].strip()
                    cache_ttl = int(max_age_str)
                    print(f"[AmadeusClient] Cache-Control max-age: {cache_ttl}s")
                except:
                    pass
            
            return {"data": response.json().get("data", []), "_cache_ttl": cache_ttl}
        except Exception as e:
            print(f"[AmadeusClient] Seatmap failed: {e}")
            # If it's an HTTP error, try to extract API error message
            if hasattr(e, 'response') and e.response is not None:
                try:
                    err_data = e.response.json()
                    print(f"[AmadeusClient] API Error Details: {err_data}")
                except:
                    pass
            return {"data": [], "errors": [str(e)]}

