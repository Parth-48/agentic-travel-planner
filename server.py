import os
import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.graph.workflow import travel_app

# Enforce Windows Proactor Loop policy for Playwright subprocesses
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

@asynccontextmanager
async def lifespan(app: FastAPI):
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    yield

app = FastAPI(title="Agentic Travel Planner API", version="1.0", lifespan=lifespan)

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
        "hotel_checkout_url": "",
        "google_hotels_url": "",
        "error_message": None
    }
    
    try:
        final_state = await travel_app.ainvoke(initial_state)
        return {"status": "SUCCESS", "data": final_state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)