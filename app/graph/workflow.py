from langgraph.graph import StateGraph, END
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
