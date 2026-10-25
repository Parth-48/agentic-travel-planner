import hashlib
import re
import requests
from typing import List
from app.config import settings
from app.schemas import FlightOption, HotelOption
from app.tools.places_tools import resolve_airport_to_city

def search_flights_mock_or_api(origin: str, destination: str, date: str) -> List[FlightOption]:
    # 1. Live Flights Search via SerpApi Google Flights Engine
    if settings.SERPAPI_KEY and settings.SERPAPI_KEY.strip():
        try:
            print(f"🔍 [SerpApi] Fetching live flights for {origin} -> {destination} on {date}...")
            
            params = {
                "engine": "google_flights",
                "departure_id": origin.upper().strip(),
                "arrival_id": destination.upper().strip(),
                "outbound_date": date,
                "type": "2",  # One-way search (prevents return_date requirement)
                "currency": "INR",
                "hl": "en",
                "api_key": settings.SERPAPI_KEY.strip()
            }
            
            response = requests.get("https://serpapi.com/search.json", params=params, timeout=12)
            res = response.json()
            
            if "error" in res:
                print(f"⚠️ [SerpApi Flights Error]: {res['error']}")
            else:
                flights = []
                flight_groups = res.get("best_flights", []) or res.get("other_flights", [])
                
                for group in flight_groups[:3]:
                    legs = group.get("flights", [])
                    if not legs:
                        continue
                    
                    first_leg = legs[0]
                    last_leg = legs[-1]
                    
                    price = group.get("price", 5000)
                    airline = first_leg.get("airline", "IndiGo")
                    flight_num = first_leg.get("flight_number", "6E-101")
                    
                    dep_time = "08:00 AM"
                    if "departure_time" in first_leg.get("departure_airport", {}):
                        dep_time = first_leg["departure_airport"]["departure_time"]
                        
                    arr_time = "10:30 AM"
                    if "arrival_time" in last_leg.get("arrival_airport", {}):
                        arr_time = last_leg["arrival_airport"]["arrival_time"]

                    flights.append(FlightOption(
                        airline=str(airline),
                        flight_number=str(flight_num),
                        departure_time=str(dep_time),
                        arrival_time=str(arr_time),
                        price_inr=float(price),
                        origin=origin.upper(),
                        destination=destination.upper()
                    ))
                
                if flights:
                    print(f"✅ [SerpApi Success] Retrieved {len(flights)} live flight options!")
                    return flights
                else:
                    print("⚠️ [SerpApi Warning] No flights in response. Switching to dynamic route generator.")
                    
        except Exception as e:
            print(f"⚠️ [SerpApi Flight Exception]: {str(e)}. Switching to dynamic route fallback.")

    # 2. Dynamic Route Hash Fallback for Flights
    print("ℹ️ Generating route-calculated flight data...")
    route_hash = int(hashlib.md5(f"{origin}-{destination}-{date}".encode()).hexdigest(), 16)
    base_price = 3500 + (route_hash % 4500)
    
    return [
        FlightOption(
            airline="IndiGo",
            flight_number=f"6E-{(route_hash % 800) + 100}",
            departure_time="07:15 AM",
            arrival_time="09:45 AM",
            price_inr=float(base_price),
            origin=origin.upper(),
            destination=destination.upper()
        ),
        FlightOption(
            airline="Air India",
            flight_number=f"AI-{((route_hash + 50) % 800) + 200}",
            departure_time="11:30 AM",
            arrival_time="02:00 PM",
            price_inr=float(base_price + 850),
            origin=origin.upper(),
            destination=destination.upper()
        )
    ]


def search_hotels_mock_or_api(destination: str, checkin: str, checkout: str) -> List[HotelOption]:
    # Resolve airport code (e.g. "DED") to city name ("Dehradun")
    dest_clean = resolve_airport_to_city(destination)
    
    # 1. Live Hotels Search via SerpApi Google Hotels Engine
    if settings.SERPAPI_KEY and settings.SERPAPI_KEY.strip():
        try:
            print(f"🏨 [SerpApi] Fetching live hotel options for {dest_clean} ({checkin} to {checkout})...")

            params = {
                "engine": "google_hotels",
                "q": f"Hotels in {dest_clean}",  # Clean search string without raw IATA codes
                "check_in_date": checkin,
                "check_out_date": checkout,
                "currency": "INR",
                "gl": "in",
                "hl": "en",
                "api_key": settings.SERPAPI_KEY.strip()
            }
            
            response = requests.get("https://serpapi.com/search.json", params=params, timeout=12)
            if response.status_code == 200:
                res = response.json()
                
                if "error" in res:
                    print(f"⚠️ [SerpApi Hotel Error]: {res['error']}")
                else:
                    properties = res.get("properties", [])
                    hotels = []
                    
                    for prop in properties[:3]:
                        raw_name = prop.get("name", f"Boutique Hotel {dest_clean}")
                        
                        # Strip any trailing 3-letter IATA airport codes that Google Hotels might attach
                        clean_name = re.sub(r'\b[A-Z]{3}\b', '', raw_name).strip()
                        clean_name = re.sub(r'\s*,\s*$', '', clean_name)

                        rating = float(prop.get("overall_rating", 4.3))
                        rate_info = prop.get("rate_per_night", {})
                        price = float(rate_info.get("extracted_before_taxes", rate_info.get("extracted_lowest", 6500)))
                        address = prop.get("description", f"Central Quarter, {dest_clean}")
                        
                        hotels.append(HotelOption(
                            name=str(clean_name),
                            rating=rating,
                            price_per_night_inr=price,
                            address=str(address)[:65]
                        ))
                    
                    if hotels:
                        print(f"✅ [SerpApi Success] Retrieved {len(hotels)} live hotels for {dest_clean}!")
                        return hotels
                    else:
                        print(f"⚠️ [SerpApi Warning] No hotel properties found in response for {dest_clean}.")

        except Exception as e:
            print(f"⚠️ [SerpApi Hotel Exception]: {str(e)}. Falling back to location-calculated hotel generator.")

    # 2. Dynamic Location-Aware Fallback for Hotels
    print(f"ℹ️ Generating location-calculated hotel data for {dest_clean}...")
    route_hash = int(hashlib.md5(f"{dest_clean}-hotel".encode()).hexdigest(), 16)
    base_tariff = 4500 + (route_hash % 6500)
    
    return [
        HotelOption(
            name=f"Grand Central Hotel {dest_clean}",
            rating=4.5,
            price_per_night_inr=float(base_tariff),
            address=f"City Center, {dest_clean}"
        ),
        HotelOption(
            name=f"Heritage Boutique Suites {dest_clean}",
            rating=4.2,
            price_per_night_inr=float(base_tariff * 0.8),
            address=f"Historic Quarter, {dest_clean}"
        )
    ]