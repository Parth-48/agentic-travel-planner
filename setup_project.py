import os

files = {
    "requirements.txt": """fastapi>=0.110.0
uvicorn>=0.28.0
pydantic>=2.6.0
langgraph>=0.0.26
langchain-core>=0.1.30
langchain-groq>=0.1.0
langchain-google-genai>=1.0.1
requests>=2.31.0
python-dotenv>=1.0.1
streamlit>=1.32.0
""",

    ".env": """GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
SERPAPI_KEY=your_serpapi_key_here
""",

    "app/__init__.py": "",

    "app/config.py": """import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")

settings = Settings()
""",

    "app/schemas.py": """from pydantic import BaseModel
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
""",

    "app/llm_factory.py": """from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings

class ResilientLLM:
    def __init__(self):
        self.primary_llm = ChatGroq(
            temperature=0.2,
            model_name="llama-3.3-70b-versatile",
            api_key=settings.GROQ_API_KEY,
            max_retries=2
        ) if settings.GROQ_API_KEY else None

        self.fallback_llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.2
        ) if settings.GEMINI_API_KEY else None

    def invoke(self, prompt_or_messages):
        if self.primary_llm:
            try:
                return self.primary_llm.invoke(prompt_or_messages)
            except Exception as e:
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    print("⚠️ Groq Rate Limit hit. Switching to Gemini 2.0 Flash fallback...")
                    if self.fallback_llm:
                        return self.fallback_llm.invoke(prompt_or_messages)
                raise e
        elif self.fallback_llm:
            return self.fallback_llm.invoke(prompt_or_messages)
        else:
            raise ValueError("No valid API keys found for Groq or Gemini in .env file!")

llm_engine = ResilientLLM()
""",

    "app/tools/__init__.py": "",

    "app/tools/flight_hotel_tools.py": """import requests
from typing import List
from app.schemas import FlightOption, HotelOption
from app.config import settings

def search_flights_mock_or_api(origin: str, destination: str, date: str) -> List[FlightOption]:
    if settings.SERPAPI_KEY:
        try:
            url = f"https://serpapi.com/search.json?engine=google_flights&departure_id={origin}&arrival_id={destination}&outbound_date={date}&currency=INR&api_key={settings.SERPAPI_KEY}"
            res = requests.get(url, timeout=10).json()
            flights = []
            for item in res.get("best_flights", [])[:3]:
                flight_data = item["flights"][0]
                flights.append(FlightOption(
                    airline=flight_data.get("airline", "IndiGo"),
                    flight_number=flight_data.get("flight_number", "6E-204"),
                    departure_time=flight_data.get("departure_token", "08:00 AM"),
                    arrival_time="10:30 AM",
                    price_inr=float(item.get("price", 4500)),
                    origin=origin,
                    destination=destination
                ))
            if flights:
                return flights
        except Exception as e:
            print(f"SerpAPI Error ({e}), switching to fallback...")

    return [
        FlightOption(airline="IndiGo", flight_number="6E-502", departure_time="07:15 AM", arrival_time="09:45 AM", price_inr=4850.0, origin=origin, destination=destination),
        FlightOption(airline="Air India", flight_number="AI-803", departure_time="11:30 AM", arrival_time="02:00 PM", price_inr=5400.0, origin=origin, destination=destination)
    ]

def search_hotels_mock_or_api(destination: str, checkin: str, checkout: str) -> List[HotelOption]:
    return [
        HotelOption(name=f"Grand Stay Resort {destination}", rating=4.5, price_per_night_inr=3200.0, address=f"Central Ave, {destination}"),
        HotelOption(name=f"Heritage Boutique Hotel", rating=4.2, price_per_night_inr=2400.0, address=f"Beach Road, {destination}")
    ]
""",

    "app/automation/__init__.py": "",

    "app/automation/deeplink_builder.py": """def generate_mmt_deeplink(origin: str, destination: str, depart_date: str, passengers: int = 1) -> str:
    try:
        parts = depart_date.split("-")
        formatted_date = f"{parts[2]}/{parts[1]}/{parts[0]}"
    except Exception:
        formatted_date = "15/11/2026"

    itinerary_str = f"{origin.upper()}-{destination.upper()}-{formatted_date}"
    return f"https://www.makemytrip.com/flight/search?itinerary={itinerary_str}&tripType=O&paxType=A-{passengers}_C-0_I-0&intl=false&cabinClass=E"
""",

    "app/graph/__init__.py": "",

    "app/graph/state.py": """from typing import TypedDict, Optional

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
""",

    "app/graph/nodes.py": """from app.graph.state import TravelAgentState
from app.tools.flight_hotel_tools import search_flights_mock_or_api, search_hotels_mock_or_api
from app.llm_factory import llm_engine
from app.automation.deeplink_builder import generate_mmt_deeplink

def flight_hotel_search_node(state: TravelAgentState) -> TravelAgentState:
    flights = search_flights_mock_or_api(state["origin"], state["destination"], state["start_date"])
    hotels = search_hotels_mock_or_api(state["destination"], state["start_date"], state["end_date"])
    
    state["available_flights"] = [f.model_dump() for f in flights]
    state["available_hotels"] = [h.model_dump() for h in hotels]
    state["selected_flight"] = state["available_flights"][0]
    state["selected_hotel"] = state["available_hotels"][0]
    return state

def itinerary_generator_node(state: TravelAgentState) -> TravelAgentState:
    prompt = f"Create a structured 2-day travel itinerary for {state['destination']}."
    llm_engine.invoke(prompt)
    
    state["trip_plan"] = {
        "origin": state["origin"],
        "destination": state["destination"],
        "daily_itinerary": [
            {
                "day_number": 1,
                "theme": "Arrival & Beachside Relaxation",
                "activities": [
                    {"time_slot": "10:00 AM", "activity_name": f"Check-in at {state['selected_hotel']['name']}", "description": "Unpack and rest.", "estimated_cost_inr": 0},
                    {"time_slot": "04:00 PM", "activity_name": "Sunset Point Visit", "description": "Local sightseeing.", "estimated_cost_inr": 500}
                ]
            }
        ]
    }
    return state

def booking_automation_node(state: TravelAgentState) -> TravelAgentState:
    state["checkout_url"] = generate_mmt_deeplink(state["origin"], state["destination"], state["start_date"], state.get("num_passengers", 1))
    state["booking_status"] = "READY_FOR_PAYMENT"
    return state
""",

    "app/graph/workflow.py": """from langgraph.graph import StateGraph, END
from app.graph.state import TravelAgentState
from app.graph.nodes import flight_hotel_search_node, itinerary_generator_node, booking_automation_node

def build_travel_graph():
    workflow = StateGraph(TravelAgentState)
    workflow.add_node("search_flights_hotels", flight_hotel_search_node)
    workflow.add_node("generate_itinerary", itinerary_generator_node)
    workflow.add_node("execute_booking_link", booking_automation_node)

    workflow.set_entry_point("search_flights_hotels")
    workflow.add_edge("search_flights_hotels", "generate_itinerary")
    workflow.add_edge("generate_itinerary", "execute_booking_link")
    workflow.add_edge("execute_booking_link", END)

    return workflow.compile()

travel_app = build_travel_graph()
""",

    "server.py": """from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.graph.workflow import travel_app

app = FastAPI(title="Agentic Travel Planner API")

class PlanTripRequest(BaseModel):
    origin: str
    destination: str
    start_date: str
    end_date: str
    budget_inr: float
    num_passengers: int = 1

@app.post("/api/v1/plan-trip")
async def plan_trip_endpoint(req: PlanTripRequest):
    initial_state = {
        "origin": req.origin,
        "destination": req.destination,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "budget_inr": req.budget_inr,
        "num_passengers": req.num_passengers,
        "available_flights": [],
        "available_hotels": [],
        "selected_flight": None,
        "selected_hotel": None,
        "trip_plan": None,
        "booking_status": "INITIATED",
        "checkout_url": "",
        "error_message": None
    }
    try:
        final_state = travel_app.invoke(initial_state)
        return {"status": "SUCCESS", "data": final_state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
""",

    "ui.py": """import streamlit as st
import requests

st.set_page_config(page_title="AI Travel Planner", page_icon="✈️", layout="wide")
st.title("✈️ Autonomous Agentic Travel Planner")

with st.sidebar:
    st.header("Trip Specifications")
    origin = st.text_input("Origin Airport Code", value="BLR")
    destination = st.text_input("Destination Airport Code", value="GOI")
    start_date = st.date_input("Departure Date")
    end_date = st.date_input("Return Date")
    budget = st.number_input("Budget (INR)", value=30000)
    passengers = st.slider("Passengers", 1, 5, 1)
    submit_btn = st.button("Plan & Prepare Booking", type="primary")

if submit_btn:
    with st.spinner("Processing..."):
        payload = {
            "origin": origin,
            "destination": destination,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "budget_inr": float(budget),
            "num_passengers": passengers
        }
        try:
            res = requests.post("http://localhost:8000/api/v1/plan-trip", json=payload, timeout=30)
            if res.status_code == 200:
                result = res.json()["data"]
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Selected Flight & Hotel")
                    st.json(result["selected_flight"])
                    st.json(result["selected_hotel"])
                    st.subheader("Booking Link")
                    st.markdown(f"[👉 Open MakeMyTrip Checkout]({result['checkout_url']})")
                with col2:
                    st.subheader("Daily Itinerary")
                    st.json(result["trip_plan"]["daily_itinerary"])
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")
"""
}

# Generate folders and files automatically
for filepath, content in files.items():
    folder = os.path.dirname(filepath)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Project folder structure and source code generated successfully!")