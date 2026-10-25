import re
from typing import List, Dict, Any
from ddgs import DDGS
from app.llm_factory import llm_engine

# Listicle pattern filter to clean scraped landmark names
LISTICLE_PATTERN = re.compile(
    r"\b(\d+|top|best|things to do|places to visit|attractions|sights|must see|guide|tripadvisor|viator|worth|popular|tourist)\b",
    re.IGNORECASE
)

# Comprehensive global vocabulary covering international dining terms
DINING_KEYWORDS = [
    "restaurant", "cafe", "café", "bistro", "pub", "dining", "eatery", "food", 
    "kitchen", "grill", "biergarten", "bräuhaus", "brauhaus", "wirtshaus", "gasthaus", 
    "delicatessen", "deli", "taverna", "tavern", "trattoria", "osteria", "pizzeria", 
    "izakaya", "ramen", "sushi", "bakery", "brasserie", "bar", "steakhouse"
]

def is_valid_poi_name(title: str) -> bool:
    if not title or len(title.strip()) < 3:
        return False
    if LISTICLE_PATTERN.search(title):
        return False
    return True

def clean_title_string(raw_title: str) -> str:
    return raw_title.split("-")[0].split("|")[0].split(":")[0].strip()

def resolve_airport_to_city(clean_dest: str) -> str:
    """Uses LLM parametric memory to resolve ANY IATA airport code globally to its metropolitan area."""
    clean_code = clean_dest.strip().upper()
    try:
        prompt = (
            f"What is the primary major metropolitan city served by airport code '{clean_code}'? "
            "Reply with ONLY the city name in plain text, nothing else (e.g., 'Rome', 'Osaka', 'Chicago', 'Sydney')."
        )
        response = llm_engine.invoke(prompt)
        resolved_city = response.content.strip().replace(".", "").replace('"', '').replace("'", "")
        if resolved_city and len(resolved_city) > 1:
            return resolved_city
    except Exception as err:
        print(f"⚠️ [LLM Resolver Notice]: Failed to resolve '{clean_code}' via LLM ({err}).")
        
    return clean_code.title()

def fetch_attractions_and_cluster(destination: str) -> Dict[str, Any]:
    clean_dest = destination.strip().upper()
    
    # Fully dynamic resolution via LLM (No hardcoded dictionary)
    city_name = resolve_airport_to_city(clean_dest)
    print(f"🌐 [Live Web Engine] Resolved destination: '{clean_dest}' -> Major City: '{city_name}'")
    
    attractions = []
    existing_names = set()
    is_international = clean_dest not in ["BOM", "DEL", "BLR", "GOI", "CCU", "MAA", "HYD", "PNQ", "AMD", "BBI"]
    daily_food_allowance_inr = 3000.0 if is_international else 1000.0

    # Scrapes both iconic sights and local eateries dynamically from live web
    search_queries = [
        f"famous landmarks points of interest monuments in {city_name}",
        f"famous iconic restaurants cafes local food spots in {city_name}"
    ]

    try:
        with DDGS(timeout=8) as ddgs:
            for query in search_queries:
                results = list(ddgs.text(query, max_results=15))
                for item in results:
                    title = item.get("title", "")
                    snippet = item.get("body", "")
                    clean_name = clean_title_string(title)
                    
                    if not is_valid_poi_name(clean_name):
                        continue
                    
                    # Prevent airport deck clutter
                    if any(kw in clean_name.lower() for kw in ["airport", "terminal", "runway deck", "aviation museum"]):
                        continue
                    
                    name_key = clean_name.lower()
                    if name_key in existing_names:
                        continue
                    
                    existing_names.add(name_key)
                    
                    # Classify without hardcoding price values
                    is_food = any(kw in clean_name.lower() or kw in snippet.lower() for kw in DINING_KEYWORDS)
                    cat = "Culinary" if is_food else "Sightseeing"
                    
                    attractions.append({
                        "name": clean_name,
                        "category": cat,
                        "estimated_time_hrs": 1.5 if is_food else 2.5,
                        "snippet": snippet[:100]
                    })
                    
                    if len(attractions) >= 20:
                        break
                if len(attractions) >= 20:
                    break

    except Exception as e:
        print(f"⚠️ [DuckDuckGo Network Notice]: {e}.")

    print(f"✅ [Places Tool] Live extracted {len(attractions)} clean nodes for {city_name}.")
    return {
        "daily_food_allowance_inr": daily_food_allowance_inr,
        "attractions": attractions
    }