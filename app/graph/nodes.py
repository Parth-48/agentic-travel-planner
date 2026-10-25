import json
import re
from datetime import datetime
from typing import List, Set
from pydantic import BaseModel, Field

from app.graph.state import TravelAgentState
from app.tools.flight_hotel_tools import search_flights_mock_or_api, search_hotels_mock_or_api
from app.tools.places_tools import fetch_attractions_and_cluster, resolve_airport_to_city
from app.automation.mmt_booking import run_booking_automation_sync
from app.llm_factory import llm_engine

class ActivitySchema(BaseModel):
    time_slot: str = Field(description="Format: HH:MM AM/PM")
    activity_name: str = Field(description="Specific physical landmark or restaurant name without quotes")
    category: str = Field(description="MUST be strictly either 'Culinary' for food/dining/cafes or 'Sightseeing' for museums/parks/landmarks")
    description: str = Field(description="Max 5 words explanation")
    estimated_cost_inr: float = Field(description="Dynamic estimated expense in INR")

class DailyItinerarySchema(BaseModel):
    day_number: int
    theme: str
    activities: List[ActivitySchema]

class ItineraryOutputSchema(BaseModel):
    daily_itinerary: List[DailyItinerarySchema]


def flight_hotel_search_node(state: TravelAgentState) -> TravelAgentState:
    origin_code = state["origin"].upper().strip()
    dest_code = state["destination"].upper().strip()
    
    # Dynamically resolve airport code to metropolitan city name (e.g. SYD -> Sydney, BBI -> Bhubaneswar)
    dest_city = resolve_airport_to_city(dest_code)
    
    # 1. Search flights using raw IATA codes
    flights = search_flights_mock_or_api(
        origin_code, dest_code, state["start_date"]
    )
    
    # 2. Search hotels strictly using the resolved city name
    hotels = search_hotels_mock_or_api(
        dest_city, state["start_date"], state["end_date"]
    )
    
    flight_dicts = [f.model_dump() for f in flights]
    hotel_dicts = [h.model_dump() for h in hotels]
    
    hotel_dicts = sorted(hotel_dicts, key=lambda x: float(x.get("price_per_night_inr") or 0))
    
    selected_flight = flight_dicts[0] if flight_dicts else {}
    selected_hotel = hotel_dicts[0] if hotel_dicts else {}

    state["available_flights"] = flight_dicts
    state["available_hotels"] = hotel_dicts
    state["selected_flight"] = selected_flight
    state["selected_hotel"] = selected_hotel
    return state


def itinerary_generator_node(state: TravelAgentState) -> TravelAgentState:
    dest = state["destination"].upper().strip()
    origin = state["origin"].upper().strip()
    
    try:
        d1 = datetime.strptime(state["start_date"], "%Y-%m-%d")
        d2 = datetime.strptime(state["end_date"], "%Y-%m-%d")
        num_days = max(1, (d2 - d1).days + 1)
    except Exception:
        num_days = 3

    places_data = fetch_attractions_and_cluster(dest)
    attractions = places_data.get("attractions", [])
    daily_food_allowance = places_data.get("daily_food_allowance_inr", 1500.0)
    daily_transport_allowance = places_data.get("daily_transport_allowance_inr", 800.0)
    
    search_context_snippets = "\n".join([
        f"- {a['name']} ({a.get('category', 'Sights')})"
        for a in attractions[:20]
    ])

    prompt = f"""
    Create a unique {num_days}-day travel itinerary for {dest}.
    Origin: {origin} (DO NOT include any sights from {origin}).
    Destination: {dest}
    Hotel Base: {state['selected_hotel'].get('name', 'Central Hotel')}
    
    Verified Sights & Dining Options in {dest}:
    {search_context_snippets}

    CRITICAL RULES:
    1. Generate exactly {num_days} days (4 activities/day: 09:00 AM, 01:00 PM, 03:30 PM, 07:30 PM).
    2. The 01:00 PM and 07:30 PM slots MUST be specific real restaurant, cafe, tavern, or dining venue names from {dest}, and their `category` field MUST be set strictly to "Culinary".
    3. The 09:00 AM and 03:30 PM slots MUST be landmarks or sights, and their `category` field MUST be set strictly to "Sightseeing".
    4. Keep ALL description fields under 5 words to prevent JSON truncation.
    5. Do NOT repeat activity names across days.
    6. DYNAMIC PRICING: Calculate realistic costs in INR (`estimated_cost_inr`) for each place based on local prices in {dest}:
       - Set to 0.0 for free public places (e.g. parks, squares, bridges, free monuments).
       - Estimate realistic meal costs per person in INR for restaurants/cafes based on city tier.
       - Estimate realistic converted entry fees in INR for museums, theme parks, and paid landmarks.
    7. ASCII ONLY: Use plain ASCII characters only. DO NOT output special dashes (‑, —, –), curly apostrophes (’), or non-breaking spaces. Use standard hyphens (-) and simple single quotes (').
    8. CONCISENESS: Keep all string field values short so the total JSON response fits completely within token limits.
    """

    daily_itinerary = []
    
    # Tier 1: Structured Binding
    try:
        structured_llm = llm_engine.with_structured_output(ItineraryOutputSchema)
        structured_response = structured_llm.invoke(prompt)
        daily_itinerary = [day.model_dump() for day in structured_response.daily_itinerary]
    except Exception as structured_err:
        print(f"🔄 [JSON Auto-Repair Strategy Active]: {structured_err}")
        
        try:
            raw_response = llm_engine.invoke(prompt)
            raw_text = raw_response.content.strip()
            cleaned_json = re.sub(r"^```(?:json)?|```$", "", raw_text, flags=re.MULTILINE).strip()
            
            if not cleaned_json.endswith("]}"):
                cleaned_json = re.sub(r',?\s*\{[^}]*$', '', cleaned_json)
                if not cleaned_json.endswith("]"):
                    cleaned_json += "]}"
                elif not cleaned_json.endswith("}"):
                    cleaned_json += "}"

            parsed = json.loads(cleaned_json)
            daily_itinerary = parsed.get("daily_itinerary", [])
        except Exception as json_err:
            print(f"⚠️ [Emergency Resilient Assembly Active]: {json_err}")

    # Tier 2: Pure Dynamic Non-Repeating Fallback Assembly
    used_names: Set[str] = set()
    has_duplicates = False
    
    for day in daily_itinerary:
        for act in day.get("activities", []):
            name_lower = act.get("activity_name", "").lower()
            if name_lower in used_names:
                has_duplicates = True
                break
            used_names.add(name_lower)
            
    if len(daily_itinerary) < num_days or has_duplicates:
        print(f"🔧 [Assembling Complete {num_days}-Day Plan purely from live scraped POI data]...")
        
        food_pool = [a for a in attractions if a.get("category") == "Culinary"]
        sight_pool = [a for a in attractions if a.get("category") != "Culinary"]
        
        if not food_pool:
            food_pool = attractions
        if not sight_pool:
            sight_pool = attractions
            
        used_names = set()
        daily_itinerary = []
        s_idx_counter = 0
        f_idx_counter = 0
        
        slot_times = ["09:00 AM", "01:00 PM", "03:30 PM", "07:30 PM"]
        
        for i in range(num_days):
            day_num = i + 1
            day_activities = []
            
            for slot_i in range(4):
                is_dining_slot = slot_i in [1, 3]
                target_pool = food_pool if is_dining_slot else sight_pool
                
                selected_item = None
                attempts = 0
                while attempts < len(target_pool):
                    idx = (f_idx_counter if is_dining_slot else s_idx_counter) % len(target_pool)
                    if is_dining_slot:
                        f_idx_counter += 1
                    else:
                        s_idx_counter += 1
                    attempts += 1
                    
                    candidate = target_pool[idx]
                    if candidate["name"].lower() not in used_names:
                        selected_item = candidate
                        used_names.add(candidate["name"].lower())
                        break
                        
                if not selected_item:
                    fallback_title = f"Local Dining Spot {i+1}" if is_dining_slot else f"Cultural District Sights {i+1}"
                    selected_item = {"name": fallback_title, "category": "Culinary" if is_dining_slot else "Sightseeing"}

                day_activities.append({
                    "time_slot": slot_times[slot_i],
                    "activity_name": selected_item["name"],
                    "category": selected_item.get("category", "Culinary" if is_dining_slot else "Sightseeing"),
                    "description": "Sample local dining." if is_dining_slot else "Explore local landmarks.",
                    "estimated_cost_inr": 0.0
                })
                
            daily_itinerary.append({
                "day_number": day_num,
                "theme": f"Day {day_num}: {day_activities[0]['activity_name']}",
                "activities": day_activities
            })

    state["trip_plan"] = {
        "origin": origin,
        "destination": dest,
        "start_date": state["start_date"],
        "end_date": state["end_date"],
        "budget_inr": state["budget_inr"],
        "selected_flight": state["selected_flight"],
        "selected_hotel": state["selected_hotel"],
        "daily_itinerary": daily_itinerary,
        "daily_food_allowance_inr": daily_food_allowance,
        "daily_transport_allowance_inr": daily_transport_allowance
    }
    return state


async def booking_automation_node(state: TravelAgentState) -> TravelAgentState:
    selected_hotel = state.get("selected_hotel") or {}
    
    hotel_name = (
        selected_hotel.get("name") 
        or selected_hotel.get("hotel_name") 
        or selected_hotel.get("title")
        or selected_hotel.get("property_name", "")
    )
    
    raw_origin = state.get("origin", "").upper().strip()
    raw_destination = state.get("destination", "").upper().strip()
    
    # Resolve city name strictly for hotels (e.g., DED -> Dehradun)
    clean_city = resolve_airport_to_city(raw_destination)
    passengers = state.get("num_passengers") or state.get("passengers", 1)
    
    automation_result = await run_booking_automation_sync(
        origin=raw_origin,             # MUST be "BOM" for MMT
        destination=raw_destination,   # MUST be "DED" for MMT
        depart_date=state.get("start_date", ""),
        hotel_name=hotel_name,
        checkout_date=state.get("end_date", ""),
        guests=int(passengers),
        city_name=clean_city           # Passed explicitly for Google Hotels
    )
    
    state["checkout_url"] = automation_result["checkout_url"]
    state["hotel_checkout_url"] = automation_result["hotel_checkout_url"]
    state["google_hotels_url"] = automation_result.get("google_hotels_url", automation_result["hotel_checkout_url"])
    state["booking_status"] = "READY_FOR_PAYMENT"
    return state