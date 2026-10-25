from typing import TypedDict, Optional

class TravelAgentState(TypedDict):
    origin: str
    destination: str
    start_date: str
    end_date: str
    budget_inr: float
    num_passengers: int
    available_flights: list
    available_hotels: list
    selected_flight: Optional[dict]
    selected_hotel: Optional[dict]
    trip_plan: Optional[dict]
    booking_status: str
    checkout_url: str
    error_message: Optional[str]
