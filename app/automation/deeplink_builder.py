def generate_mmt_deeplink(origin: str, destination: str, depart_date: str, passengers: int = 1) -> str:
    try:
        parts = depart_date.split("-")
        formatted_date = f"{parts[2]}/{parts[1]}/{parts[0]}"
    except Exception:
        formatted_date = "15/11/2026"

    itinerary_str = f"{origin.upper()}-{destination.upper()}-{formatted_date}"
    return f"https://www.makemytrip.com/flight/search?itinerary={itinerary_str}&tripType=O&paxType=A-{passengers}_C-0_I-0&intl=false&cabinClass=E"
