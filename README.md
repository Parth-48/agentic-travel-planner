# Agentic Travel Planner 

A dynamic AI travel planning agent powered by FastAPI, LangGraph, and Streamlit. Uses live web scraping and LLM memory to dynamically generate personalized itineraries, resolve airport codes to metropolitan areas, estimate realistic expenses, and format booking links without hardcoded data.

## Features

- **Dynamic Airport & City Resolution:** Maps raw IATA airport codes to metropolitan areas via LLM memory.
- **Live Search & Scraped Attractions:** Integrates SerpApi (Google Flights/Hotels) and live web scraping for POIs and dining spots.
- **Categorized Itineraries:** Automatically separates sightseeing landmarks from culinary spots.
- **Direct Link Formatting:** Generates clean checkout URLs for MakeMyTrip (flights) and Google Hotels (accommodation).

## Tech Stack

- **Backend:** Python, FastAPI, LangGraph
- **Frontend:** Streamlit
- **LLMs & Scraping:** Groq / Gemini, DuckDuckGo Scraper (`ddgs`), SerpApi

## Quickstart

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YourUsername/agentic-travel-planner.git](https://github.com/YourUsername/agentic-travel-planner.git)
   cd agentic-travel-planner
