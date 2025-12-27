
import sys
import os
import asyncio
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from services.amadeus_client import AmadeusClient
from services.seat_service import SeatService

async def verify():
    print("[Test] Starting End-to-End Service Verification (Demo Mode)...")
    
    # 1. Initialize Client
    client = AmadeusClient()
    if not client.is_demo:
        print("[Warning] Client not in Demo Mode but expected request to be local.")
        
    # 2. Search Flights (Mock)
    print("[Test] Searching Flights...")
    offers = await client.search_flights("NCE", "ORY", "2023-08-01")
    
    if not offers or "data" not in offers:
        print("[FAIL] No flight offers returned.")
        return
        
    print(f"[Test] Found {len(offers['data'])} offers.")
    offer = offers["data"][0]
    
    # 3. Get SeatMap
    print("[Test] Fetching SeatMap...")
    seatmaps = await client.get_seatmap(offer)
    
    if not seatmaps or "data" not in seatmaps:
        print("[FAIL] No seatmap data returned.")
        return
        
    raw_maps_count = len(seatmaps["data"])
    print(f"[Test] Received {raw_maps_count} raw seatmaps.")
    
    # 4. Process (Merge)
    print("[Test] Processing/Merging SeatMaps...")
    service = SeatService()
    master_map = service.process_seatmaps(seatmaps)
    
    seat_count = len(master_map)
    print(f"[Test] Merged into {seat_count} unique seats.")
    
    # 5. Check Facilities
    facilities = service.get_facilities(seatmaps)
    print(f"[Test] Found {len(facilities)} facilities.")
    
    # Assertions
    if seat_count > 0 and raw_maps_count > 0:
        print("[SUCCESS] Verification Passed.")
    else:
        print("[FAIL] Seat count is 0.")

if __name__ == "__main__":
    asyncio.run(verify())
