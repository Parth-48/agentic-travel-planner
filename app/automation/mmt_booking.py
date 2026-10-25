import urllib.parse
from datetime import datetime
from typing import Dict, Any
import re

def format_date_for_mmt(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return date_str

def construct_flight_checkout_url(origin: str, destination: str, depart_date: str, passengers: int = 1) -> str:
    formatted_date = format_date_for_mmt(depart_date)
    pax_type = f"A-{passengers}_C-0_I-0"
    return (
        f"https://www.makemytrip.com/flight/search?"
        f"itinerary={origin.upper()}-{destination.upper()}-{formatted_date}&"
        f"tripType=O&paxType={pax_type}&intl=true&cabinClass=E"
    )

def construct_google_hotels_url(hotel_name: str, destination: str, checkin_date: str, checkout_date: str, guests: int = 1) -> str:
    clean_hotel = str(hotel_name).strip() if hotel_name else ""
    clean_dest = str(destination).strip() if destination else ""

    # Strip standalone 3-letter IATA airport codes from hotel name and destination string
    clean_hotel = re.sub(r'\b[A-Z]{3}\b', '', clean_hotel).strip()
    clean_dest = re.sub(r'\b[A-Z]{3}\b', '', clean_dest).strip()

    if clean_hotel and clean_dest:
        if clean_dest.lower() in clean_hotel.lower():
            query_str = clean_hotel
        else:
            query_str = f"{clean_hotel}, {clean_dest}"
    elif clean_hotel:
        query_str = clean_hotel
    elif clean_dest:
        query_str = f"Hotels in {clean_dest}"
    else:
        query_str = "Hotels"

    # Clean double commas and trailing spaces
    query_str = re.sub(r'\s*,\s*', ', ', query_str)
    query_str = re.sub(r'\s+', ' ', query_str).strip(' ,')

    encoded_query = urllib.parse.quote_plus(query_str)
    
    return (
        f"https://www.google.com/travel/hotels?"
        f"q={encoded_query}&"
        f"checkin={checkin_date}&"
        f"checkout={checkout_date}&"
        f"adults={guests}"
    )

async def run_booking_automation_sync(
    origin: str,
    destination: str,
    depart_date: str,
    hotel_name: str = "",
    checkout_date: str = "",
    guests: int = 1,
    city_name: str = "",
    **kwargs
) -> Dict[str, Any]:
    # Flight search strictly uses IATA codes (e.g. BOM -> DED)
    flight_url = construct_flight_checkout_url(origin, destination, depart_date, passengers=guests)
    
    # Hotel search uses clean city name (e.g. Dehradun)
    target_hotel_dest = city_name if city_name else destination
    hotel_url = construct_google_hotels_url(hotel_name, target_hotel_dest, depart_date, checkout_date, guests=guests)
    
    return {
        "checkout_url": flight_url,
        "hotel_checkout_url": hotel_url,
        "google_hotels_url": hotel_url,
        "status": "READY"
    }