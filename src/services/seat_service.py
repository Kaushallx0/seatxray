from datetime import datetime, timedelta

class SeatService:
    """
    Core Logic for SeatXray.
    Handles grouping of flight offers and 'X-ray' synthesis of seatmaps.
    """
    
    # --- Part 1: Offer Grouping & Formatting ---

    def group_offers_by_flight(self, search_response: dict) -> list:
        """
        Groups raw flight offers into unique 'Flight' objects.
        Merges offers for the same flight (different cabins) into one record.
        Resolves dictionary references (Carrier, Aircraft, etc.).
        """
        if not search_response or "data" not in search_response:
            return []

        raw_offers = search_response["data"]
        dictionaries = search_response.get("dictionaries", {})
        
        # Maps for quick lookup
        carrier_map = dictionaries.get("carriers", {})
        aircraft_map = dictionaries.get("aircraft", {})
        location_map = dictionaries.get("locations", {})

        grouped = {}

        for offer in raw_offers:
            # Key definition: Carrier + Number + DepTime
            # We assume the first segment defines the primary flight identity for the list view
            itinerary = offer["itineraries"][0]
            first_seg = itinerary["segments"][0]
            last_seg = itinerary["segments"][-1]
            
            carrier_code = first_seg["carrierCode"]
            flight_number = first_seg["number"]
            dep_time = first_seg["departure"]["at"]
            
            key = f"{carrier_code}_{flight_number}_{dep_time}"
            
            if key not in grouped:
                # Basic Flight Info
                dep_iata = first_seg["departure"]["iataCode"]
                arr_iata = last_seg["arrival"]["iataCode"]
                
                # Format Duration (PT12H30M -> 12h 30m)
                duration_raw = itinerary["duration"] # e.g. PT14H15M
                # New: i18n aware formatting
                from utils.i18n import TranslationService
                i18n = TranslationService.get_instance()
                
                # Simple parser for PTxxHxxM
                import re
                match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?', duration_raw)
                h = match.group(1) if match and match.group(1) else "0"
                m = match.group(2) if match and match.group(2) else "0"
                
                duration_fmt = i18n.tr("common.time_format", h=h, m=m)
                
                # Resolve Names
                carrier_name = carrier_map.get(carrier_code, carrier_code)
                aircraft_code = first_seg.get("aircraft", {}).get("code", "")
                aircraft_name = aircraft_map.get(aircraft_code, aircraft_code)
                
                # Resolve Location Names (e.g. NCE -> NICE)
                dep_name = location_map.get(dep_iata, {}).get("cityCode", dep_iata) # Amadeus loc dict structure varies, try safe access
                # Actually Amadeus dictionary for locations usually returns { "NCE": { "cityCode": "NCE", "countryCode": "FR" } } 
                # or simplified. Let's try to get cityCode or just the code if complex.
                # Ideally we want "Nice". The dictionary might just be code-to-code mapping in some endpoints.
                # If Search V2 returns full objects, we use them.
                # Let's assume the dictionary is { "IATA": { ... } } or { "IATA": "NAME" }?
                # V2 Shopping response 'locations' is usually { "CDG": { "cityCode": "PAR", "countryCode": "FR" } }
                # It doesn't always contain the full name in 'locations' depending on params.
                # BUT, we have our OWN airports.json in SearchView! 
                # SeatService doesn't have access to airports.json easily unless passed.
                # Logic: We will return the codes here, and let UI layer (SearchView) do the final mapping if it has the lookup,
                # OR we try to use what's in 'dictionaries' if it has names.
                # Often 'locations' in search response ONLY has codes.
                
                # Calculate Days Difference for Arrival
                dep_dt = datetime.fromisoformat(dep_time)
                arr_dt = datetime.fromisoformat(last_seg["arrival"]["at"])
                delta = arr_dt.date() - dep_dt.date()
                days_diff = delta.days

                # Terminal Info
                dep_term = first_seg["departure"].get("terminal", "-")
                arr_term = last_seg["arrival"].get("terminal", "-")

                grouped[key] = {
                    "id": key, # Internal ID for grouping
                    "identity": {
                        "carrierCode": carrier_code,
                        "carrierName": carrier_name,
                        "flightNumber": flight_number,
                        "aircraftCode": aircraft_code,
                        "aircraftName": aircraft_name,
                    },
                    "route": {
                        "departure": {"iata": dep_iata, "terminal": dep_term, "at": dep_time},
                        "arrival": {"iata": arr_iata, "terminal": arr_term, "at": last_seg["arrival"]["at"]},
                        "duration": duration_fmt,
                        "days_diff": days_diff # Added for UI
                    },
                    "offers": [], # All raw offers for this flight
                    "pricing": {} # aggregated pricing by cabin
                }
            
            # Aggregate Pricing & Keep Offer
            # Determine Cabin (Economy, Business, etc.)
            # We look at the first segment's cabin for simplicity in labeling
            cabin_breakdown = offer["travelerPricings"][0]["fareDetailsBySegment"][0]["cabin"]
            price_amount = offer["price"]["total"]
            
            # Formatting Price (JPY assumed or convert symbol)
            # Use i18n for formatting
            from utils.i18n import TranslationService
            i18n = TranslationService.get_instance()
            
            try:
                price_float = float(price_amount)
                # Currently simple ¥ format logic
                # Ideally "currency_format" in i18n handles symbol placement
                price_fmt = i18n.tr("common.currency_format", amount=f"{price_float:,.0f}")
            except:
                price_fmt = f"¥{price_amount}"

            # Store absolute simplest lowest price per cabin
            if cabin_breakdown not in grouped[key]["pricing"]:
                grouped[key]["pricing"][cabin_breakdown] = {
                    "amount": float(price_amount), 
                    "formatted": price_fmt
                }
            else:
                if float(price_amount) < grouped[key]["pricing"][cabin_breakdown]["amount"]:
                    grouped[key]["pricing"][cabin_breakdown] = {
                        "amount": float(price_amount), 
                        "formatted": price_fmt
                    }
            
            grouped[key]["offers"].append(offer)

        # Convert to list and sort by departure time
        result_list = list(grouped.values())
        result_list.sort(key=lambda x: x["route"]["departure"]["at"])
        
        # Debug: Show cabin distribution
        for flight in result_list:
            cabins = list(flight["pricing"].keys())
            print(f"[SeatService] Flight {flight['identity']['carrierCode']}{flight['identity']['flightNumber']}: Cabins = {cabins}")
        
        return result_list

    # --- Part 2: SeatMap Synthesis (X-ray Logic) ---

    def process_seatmaps_batch(self, seatmaps_response: dict) -> tuple[dict, list]:
        """
        Merges multiple seatmaps (from different cabin offers) into a single master map.
        Returns: (master_seats_dict, facilities_list)
        """
        if not seatmaps_response or "data" not in seatmaps_response:
            return {}, []

        merged_seats = {}
        facilities = []
        
        # Priority: Occupied > Available > Blocked
        # If we see OCCUPIED in any map, it's OCCUPIED.
        # If we see AVAILABLE in any map, it's AVAILABLE (even if blocked in others).
        # Only if BLOCKED in all, remains BLOCKED.
        
        for seatmap in seatmaps_response["data"]:
            # Capture facilities from the first map (assuming static layout)
            if not facilities and "decks" in seatmap:
                 for deck in seatmap["decks"]:
                     if "facilities" in deck:
                         facilities.extend(deck["facilities"])

            for deck in seatmap.get("decks", []):
                for seat in deck.get("seats", []):
                    number = seat.get("number")
                    if not number: continue
                    
                    status = "UNKNOWN"
                    pricing = seat.get("travelerPricing", [])
                    if pricing:
                        status = pricing[0].get("seatAvailabilityStatus", "UNKNOWN")
                    
                    # Normalize Status
                    # Amadeus sometimes returns different strings? adhering to docs.
                    
                    if number not in merged_seats:
                        merged_seats[number] = seat
                        # Inject a helper field for easy access
                        merged_seats[number]["_final_status"] = status
                    else:
                        current_status = merged_seats[number]["_final_status"]
                        
                        # Synthesis Logic
                        if status == "OCCUPIED":
                            merged_seats[number] = seat
                            merged_seats[number]["_final_status"] = "OCCUPIED"
                            
                        elif status == "AVAILABLE":
                            if current_status != "OCCUPIED":
                                merged_seats[number] = seat
                                merged_seats[number]["_final_status"] = "AVAILABLE"
                                
                        # If status is BLOCKED, we do nothing unless current is UNKNOWN
                        elif status == "BLOCKED":
                            if current_status == "UNKNOWN":
                                merged_seats[number] = seat
                                merged_seats[number]["_final_status"] = "BLOCKED"

        # Final Cleanup: ensuring the travelerPricing reflects data for the UI
        for num, seat in merged_seats.items():
            final_st = seat["_final_status"]
            # Overwrite the travelerPricing to match our resolved status
            if "travelerPricing" not in seat:
                seat["travelerPricing"] = [{}]
            if not seat["travelerPricing"]:
                 seat["travelerPricing"].append({})
            
            seat["travelerPricing"][0]["seatAvailabilityStatus"] = final_st

        return merged_seats, facilities

    # Legacy method wrapper for compatibility if needed, but we aim to replace usage
    def process_seatmaps(self, seatmaps_data):
        return self.process_seatmaps_batch(seatmaps_data if isinstance(seatmaps_data, dict) else {"data": seatmaps_data})[0]

    def get_facilities(self, seatmaps_data):
        return self.process_seatmaps_batch(seatmaps_data if isinstance(seatmaps_data, dict) else {"data": seatmaps_data})[1]
