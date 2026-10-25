import re
import sys
import math
import asyncio
import urllib.parse
from html import escape

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
import requests

st.set_page_config(
    page_title="Travel Agent",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg: #F5F7FA;
        --surface: #FFFFFF;
        --border: #E2E8F0;
        --text: #0F172A;
        --text-2: #475569;
        --text-3: #64748B;
        --accent: #1D4ED8;
        --accent-hover: #1E40AF;
        --accent-soft: #EFF6FF;
        --price: #047857;
        --price-soft: #ECFDF5;
    }

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
        color: var(--text);
    }

    .stApp { background-color: var(--bg); }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background-color: var(--surface);
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebar"] * { color: var(--text); }
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: var(--text-3); }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1280px;
    }

    h1, h2, h3, h4 { color: var(--text); letter-spacing: -0.01em; }
    h3 { font-size: 1.15rem !important; font-weight: 600 !important; }

    .brand-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.25rem 1.5rem;
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 4px solid var(--accent);
        border-radius: 8px;
        margin-bottom: 2rem;
    }
    .brand-title {
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: var(--text);
        margin: 0;
    }
    .brand-subtitle {
        font-size: 0.9rem;
        color: var(--text-3);
        margin: 0.15rem 0 0 0;
    }

    .custom-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }
    .card-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
    }
    .card-label {
        font-size: 0.8rem;
        color: var(--accent);
        font-weight: 600;
        margin-bottom: 0.6rem;
    }
    .card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 0.2rem;
    }
    .card-meta {
        font-size: 0.875rem;
        color: var(--text-2);
    }
    .card-divider {
        border: 0;
        border-top: 1px solid var(--border);
        margin: 0.9rem 0;
    }
    .card-foot {
        display: flex;
        justify-content: space-between;
        font-size: 0.875rem;
        color: var(--text-2);
    }
    .card-foot strong { color: var(--text); font-weight: 600; }

    .price-tag {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--price);
        background: var(--price-soft);
        padding: 0.25rem 0.7rem;
        border-radius: 6px;
        white-space: nowrap;
    }
    .price-unit { font-size: 0.75rem; font-weight: 500; color: var(--text-3); }

    .activity-row {
        padding: 0.85rem 0;
        border-bottom: 1px solid var(--border);
    }
    .activity-row:last-child { border-bottom: none; }
    .time-badge {
        display: inline-block;
        background: var(--accent-soft);
        color: var(--accent);
        font-size: 0.75rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        margin-bottom: 4px;
    }
    .activity-name { font-weight: 600; color: var(--text); margin-top: 2px; }
    .activity-desc { font-size: 0.875rem; color: var(--text-2); margin-top: 2px; }
    .activity-cost { font-size: 0.8rem; color: var(--text-3); margin-top: 4px; }

    [data-testid="stExpander"] {
        background: var(--surface);
        border: 1px solid var(--border) !important;
        border-radius: 8px;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }
    [data-testid="stExpander"] summary { color: var(--text); font-weight: 600; }
    [data-testid="stExpander"] summary:hover { color: var(--accent); }

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] [data-baseweb="input"],
    [data-testid="stSidebar"] [data-baseweb="base-input"] {
        background-color: #FFFFFF !important;
        color: var(--text) !important;
        border-color: var(--border) !important;
    }
    [data-testid="stSidebar"] input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent) !important;
    }
    [data-testid="stSidebar"] label p { color: var(--text-2) !important; font-weight: 500; }

    .stButton > button {
        width: 100%;
        background-color: var(--accent);
        color: #FFFFFF;
        border-radius: 6px;
        font-weight: 600;
        border: 1px solid var(--accent);
        padding: 0.6rem 1rem;
        transition: background-color 0.2s ease;
    }
    .stButton > button:hover {
        background-color: var(--accent-hover);
        border-color: var(--accent-hover);
        color: #FFFFFF;
    }

    [data-testid="stLinkButton"] a {
        background-color: var(--surface);
        color: var(--accent) !important;
        border: 1px solid var(--accent);
        border-radius: 6px;
        font-weight: 600;
    }
    [data-testid="stLinkButton"] a:hover {
        background-color: var(--accent-soft);
        border-color: var(--accent-hover);
    }

    .total-card {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 1rem;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }
    .total-label { font-size: 0.9rem; color: var(--text-3); font-weight: 500; }
    .total-amount { font-size: 2rem; font-weight: 700; color: var(--text); letter-spacing: -0.02em; }
    .total-sub { font-size: 0.85rem; color: var(--text-2); margin-top: 0.15rem; }
    .status-pill {
        font-size: 0.85rem;
        font-weight: 600;
        padding: 0.4rem 0.8rem;
        border-radius: 999px;
    }
    .status-ok { color: #047857; background: #ECFDF5; }
    .status-over { color: #B91C1C; background: #FEF2F2; }

    .split-bar {
        display: flex;
        height: 10px;
        border-radius: 999px;
        overflow: hidden;
        background: var(--border);
        margin-bottom: 1.5rem;
    }
    .cat-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.5rem; }
    .cat-name { font-weight: 600; color: var(--text); display: flex; align-items: center; gap: 0.5rem; }
    .cat-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
    .cat-total { font-weight: 700; color: var(--text); }
    .cat-share { font-size: 0.8rem; color: var(--text-3); font-weight: 500; margin-left: 0.4rem; }
    .cat-track { height: 6px; background: var(--border); border-radius: 999px; overflow: hidden; margin-bottom: 0.75rem; }
    .cat-fill { height: 100%; border-radius: 999px; }
    .cat-item {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        font-size: 0.85rem;
        color: var(--text-2);
        padding: 0.35rem 0;
        border-top: 1px solid var(--border);
    }
    .cat-item span:last-child { color: var(--text); white-space: nowrap; font-weight: 500; }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

def esc(value, default="—"):
    if value is None or value == "":
        return default
    return escape(str(value))

def inr(value):
    try:
        return f"&#8377;{float(value):,.0f}"
    except (TypeError, ValueError):
        return "—"

FLIGHT_PRICE_IS_PER_PERSON = True      
INCLUDE_RETURN_FLIGHT = True           
PEOPLE_PER_ROOM = 2                    
ACTIVITY_COST_IS_PER_PERSON = True     

CATEGORY_ORDER = [
    "Travel",
    "Accommodation",
    "Food & dining",
    "Local transport",
    "Activities & sightseeing",
]
CATEGORY_COLORS = {
    "Travel": "#1D4ED8",
    "Accommodation": "#7C3AED",
    "Food & dining": "#B45309",
    "Local transport": "#0E7490",
    "Activities & sightseeing": "#047857",
}
ACTIVITY_PATTERNS = [
    ("Local transport", r"\b(taxi|cab|transfer|ride|bus|metro|scooter|ferry|rental|transport|auto)"),
    ("Food & dining", r"\b(breakfast|brunch|lunch|dinner|cafe|café|restaurant|food|meal|snack|dining|eat|thali|seafood|shack|bar\b)"),
]

def categorize_activity(act):
    text = f"{act.get('category', '')} {act.get('activity_name', '')}".lower()
    for category, pattern in ACTIVITY_PATTERNS:
        if re.search(pattern, text):
            return category
    return "Activities & sightseeing"

def build_cost_breakdown(result, start, end, passengers):
    flight = result.get("selected_flight") or {}
    hotel = result.get("selected_hotel") or {}
    trip_plan = result.get("trip_plan") or {}
    itinerary = trip_plan.get("daily_itinerary", []) or []

    nights = max((end - start).days, 1)
    trip_days = len(itinerary) or (nights + 1)
    rooms = math.ceil(passengers / PEOPLE_PER_ROOM)

    groups = {c: {"total": 0.0, "items": []} for c in CATEGORY_ORDER}

    def add(category, label, amount):
        if amount and amount > 0:
            groups[category]["items"].append((label, amount))
            groups[category]["total"] += amount

    # Flight calculation
    fare = float(flight.get("price_inr") or 0)
    add("Travel", f"Outbound flight ({passengers} traveller{'s' if passengers > 1 else ''})", fare * passengers)
    if INCLUDE_RETURN_FLIGHT:
        add("Travel", f"Return flight ({passengers} traveller{'s' if passengers > 1 else ''})", fare * passengers)

    # Hotel calculation
    nightly = float(hotel.get("price_per_night_inr") or 0)
    add("Accommodation", f"{hotel.get('name', 'Hotel')} ({nights} night{'s' if nights > 1 else ''} × {rooms} room{'s' if rooms > 1 else ''})", nightly * nights * rooms)

    # Itinerary activity costs per passenger
    for day in itinerary:
        for act in day.get("activities", []):
            cost_per_person = float(act.get("estimated_cost_inr") or 0)
            add(categorize_activity(act), f"Day {day.get('day_number')}: {act.get('activity_name', 'Activity')}", cost_per_person * passengers)

    # Food & dining allowance (calculated cleanly without double counting)
    daily_food_rate = float(trip_plan.get("daily_food_allowance_inr") or 1200.0)
    total_food_budget = daily_food_rate * passengers * trip_days
    food_shortfall = total_food_budget - groups["Food & dining"]["total"]
    
    if food_shortfall > 0:
        add("Food & dining", f"General dining & transit allowance (₹{daily_food_rate:,.0f}/day × {passengers} pax)", food_shortfall)

    return groups

st.markdown(
    '<div class="brand-header"><div>'
    '<p class="brand-title">Travel Agent</p>'
    '<p class="brand-subtitle">Hassle free travel around the world.</p>'
    "</div></div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Search parameters")
    st.caption("Set your route, dates and budget")

    col_a, col_b = st.columns(2)
    with col_a:
        origin = st.text_input("Origin Airport", value="BLR").upper().strip()
    with col_b:
        destination = st.text_input("Destination Airport", value="GOI").upper().strip()

    start_date = st.date_input("Departure date")
    end_date = st.date_input("Return date")

    budget = st.number_input("Budget limit (INR)", value=30000, step=2500)
    passengers = st.slider("Passengers", min_value=1, max_value=6, value=1)

    st.markdown("<br>", unsafe_allow_html=True)
    submit_btn = st.button("Generate plan")

if submit_btn:
    with st.spinner("Searching flights, scoring hotels and optimizing your schedule..."):
        payload = {
            "origin": origin,
            "destination": destination,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "budget_inr": float(budget),
            "num_passengers": passengers,
        }

        try:
            res = requests.post(
                "https://agentic-travel-planner-backend.onrender.com", json=payload, timeout=45
            )

            if res.status_code == 200:
                result = res.json()["data"]

                col_left, col_right = st.columns([1, 1.2], gap="large")

                with col_left:
                    st.markdown("### Bookings and accommodation")

                    flight = result.get("selected_flight", {})
                    hotel = result.get("selected_hotel", {})
                    
                    checkout_url = result.get("checkout_url") or "https://www.makemytrip.com/flights"
                    
                    # Dynamically construct fallback using state inputs if backend link is empty
                    raw_hotel_name = hotel.get("name") or hotel.get("hotel_name") or hotel.get("title") or ""

                    # Strip any residual 3-letter airport code from hotel name and destination input
                    clean_hotel_name = re.sub(r'\b[A-Z]{3}\b', '', raw_hotel_name).strip()
                    clean_hotel_name = re.sub(r'\s*,\s*$', '', clean_hotel_name)

                    encoded_hotel_query = urllib.parse.quote_plus(clean_hotel_name if clean_hotel_name else "Hotels")

                    fallback_hotel_url = (
                        f"https://www.google.com/travel/hotels?q={encoded_hotel_query}&checkin={start_date}&checkout={end_date}&adults={passengers}"
                    )
                    hotel_checkout_url = result.get("hotel_checkout_url") or fallback_hotel_url

                    if flight:
                        st.markdown(
                            f'<div class="custom-card">'
                            f'<div class="card-label">Recommended outbound flight</div>'
                            f'<div class="card-row"><div>'
                            f'<div class="card-title">{esc(flight.get("airline"))} ({esc(flight.get("flight_number"))})</div>'
                            f'<div class="card-meta">Route: {esc(flight.get("origin"))} &rarr; {esc(flight.get("destination"))}</div>'
                            f'</div>'
                            f'<div class="price-tag">{inr(flight.get("price_inr"))}</div></div>'
                            f'<hr class="card-divider">'
                            f'<div class="card-foot">'
                            f'<div><strong>Departure:</strong> {esc(flight.get("departure_time"))}</div>'
                            f'<div><strong>Arrival:</strong> {esc(flight.get("arrival_time"))}</div>'
                            f'</div></div>',
                            unsafe_allow_html=True,
                        )

                    if hotel:
                        st.markdown(
                            f'<div class="custom-card">'
                            f'<div class="card-label">Recommended hotel</div>'
                            f'<div class="card-row"><div>'
                            f'<div class="card-title">{esc(hotel.get("name"))}</div>'
                            f'<div class="card-meta">{esc(hotel.get("address"))}</div>'
                            f'</div>'
                            f'<div class="price-tag">{inr(hotel.get("price_per_night_inr"))}'
                            f'<span class="price-unit">/night</span></div></div>'
                            f'<hr class="card-divider">'
                            f'<div class="card-foot"><div><strong>Property rating:</strong> '
                            f'{esc(hotel.get("rating"))} / 5.0</div></div></div>',
                            unsafe_allow_html=True,
                        )

                    st.markdown("### Book your trip")
                    st.link_button(
                        "Continue to MakeMyTrip checkout",
                        checkout_url,
                        use_container_width=True,
                    )
                    st.link_button(
                        "Continue to Google Hotels checkout",
                        hotel_checkout_url,
                        use_container_width=True,
                    )

                with col_right:
                    st.markdown("### Itinerary")
                    itinerary = result.get("trip_plan", {}).get("daily_itinerary", [])

                    if itinerary:
                        for day in itinerary:
                            day_num = day.get("day_number")
                            theme = day.get("theme", f"Day {day_num} overview")

                            with st.expander(
                                f"Day {day_num} — {theme}", expanded=(day_num == 1)
                            ):
                                for act in day.get("activities", []):
                                    cost = act.get("estimated_cost_inr", 0) or 0
                                    cost_text = inr(cost) if cost > 0 else "Included"

                                    st.markdown(
                                        f'<div class="activity-row">'
                                        f'<span class="time-badge">{esc(act.get("time_slot"))}</span>'
                                        f'<div class="activity-name">{esc(act.get("activity_name"))}</div>'
                                        f'<div class="activity-desc">{esc(act.get("description"), "")}</div>'
                                        f'<div class="activity-cost">Estimated expense: {cost_text}</div>'
                                        f'</div>',
                                        unsafe_allow_html=True,
                                    )
                    else:
                        st.info("No itinerary was generated. Check your route and dates, then try again.")

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### Estimated expenditure")

                groups = build_cost_breakdown(result, start_date, end_date, passengers)
                grand_total = sum(g["total"] for g in groups.values())
                difference = budget - grand_total
                nights = max((end_date - start_date).days, 1)

                if difference >= 0:
                    status = f'<span class="status-pill status-ok">{inr(difference)} under budget</span>'
                else:
                    status = f'<span class="status-pill status-over">{inr(-difference)} over budget</span>'

                st.markdown(
                    f'<div class="total-card"><div>'
                    f'<div class="total-label">Approximate total for {passengers} traveller{"s" if passengers > 1 else ""}, {nights} night{"s" if nights > 1 else ""}</div>'
                    f'<div class="total-amount">{inr(grand_total)}</div>'
                    f'<div class="total-sub">Budget limit: {inr(budget)}</div>'
                    f'</div>{status}</div>',
                    unsafe_allow_html=True,
                )

                active = [(c, groups[c]) for c in CATEGORY_ORDER if groups[c]["total"] > 0]

                if grand_total > 0:
                    segments = "".join(
                        f'<div style="width:{g["total"] / grand_total * 100:.2f}%;background:{CATEGORY_COLORS[c]};"></div>'
                        for c, g in active
                    )
                    st.markdown(f'<div class="split-bar">{segments}</div>', unsafe_allow_html=True)

                for i in range(0, len(active), 2):
                    row_cols = st.columns(2, gap="large")
                    for col, (cat, g) in zip(row_cols, active[i:i + 2]):
                        share = g["total"] / grand_total * 100 if grand_total else 0
                        items_html = "".join(
                            f'<div class="cat-item"><span>{esc(label)}</span><span>{inr(amount)}</span></div>'
                            for label, amount in g["items"]
                        )
                        with col:
                            st.markdown(
                                f'<div class="custom-card">'
                                f'<div class="cat-head">'
                                f'<div class="cat-name"><span class="cat-dot" style="background:{CATEGORY_COLORS[cat]};"></span>{esc(cat)}</div>'
                                f'<div><span class="cat-total">{inr(g["total"])}</span><span class="cat-share">{share:.0f}%</span></div>'
                                f'</div>'
                                f'<div class="cat-track"><div class="cat-fill" style="width:{share:.2f}%;background:{CATEGORY_COLORS[cat]};"></div></div>'
                                f'{items_html}</div>',
                                unsafe_allow_html=True,
                            )

                st.caption(
                    "Estimates only. Return flight is assumed at the outbound fare, hotels are priced at one room "
                    "per two travellers, and meals not listed in the itinerary use a daily allowance."
                )

            else:
                st.error(f"Backend API error [{res.status_code}]: {res.text}")

        except Exception as e:
            st.error(f"Could not reach the backend server: {str(e)}")

else:
    st.info("Set your route and dates in the sidebar, then select **Generate plan**.")