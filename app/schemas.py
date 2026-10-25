from pydantic import BaseModel
from typing import List, Optional

class FlightOption(BaseModel):
    airline: str
    flight_number: str
    departure_time: str
    arrival_time: str
    price_inr: float
    origin: str
    destination: str

class HotelOption(BaseModel):
    name: str
    rating: float
    price_per_night_inr: float
    address: str

class ItineraryActivity(BaseModel):
    time_slot: str
    activity_name: str
    description: str
    estimated_cost_inr: float

class DayItinerary(BaseModel):
    day_number: int
    theme: str
    activities: List[ItineraryActivity]

class TripPlan(BaseModel):
    origin: str
    destination: str
    start_date: str
    end_date: str
    budget_inr: float
    selected_flight: Optional[FlightOption] = None
    selected_hotel: Optional[HotelOption] = None
    daily_itinerary: List[DayItinerary] = []
