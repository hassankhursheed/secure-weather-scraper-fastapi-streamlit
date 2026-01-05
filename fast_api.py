from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

from weather_api import fetch_weather
from database import create_table, insert_weather_data

# load environment variables
load_dotenv()
API_KEY = os.getenv("INTERNAL_API_KEY")
if not API_KEY:
    raise RuntimeError("INTERNAL_API_KEY environment variable not set")

# fastapi app configuration
app = FastAPI(
    title="Weather Scraper API",
    description="REST API to fetch and store real-time weather data"
)

# create database
create_table()

# pydantic model for weather request
class WeatherRequest(BaseModel):
    city: str
    unit: Optional[str] = "metric"

# root endpoint
@app.get("/")
def root():
    return {"message": "Weather API is running"}

# weather scraper endpoint
@app.post("/scraper")
def scrape_weather(
    request: WeatherRequest,
    x_api_key: str = Header(...)
):
    # Validate API key
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized/Invalid API key")

    # Fetch weather data from OpenWeatherMap
    data = fetch_weather(request.city, request.unit)
    if not data:
        raise HTTPException(status_code=404, detail="City not found")

    # Prepare weather data
    unit_symbol = "°C" if request.unit == "metric" else "°F"
    speed_unit = "m/s" if request.unit == "metric" else "mph"

    weather_data = {
        "City": data["name"],
        "Country Code": data["sys"]["country"],
        "Temperature": f"{data['main']['temp']} {unit_symbol}",
        "Feels Like": f"{data['main']['feels_like']} {unit_symbol}",
        "Min Temperature": f"{data['main']['temp_min']} {unit_symbol}",
        "Max Temperature": f"{data['main']['temp_max']} {unit_symbol}",
        "Humidity": f"{data['main']['humidity']}%",
        "Weather": data["weather"][0]["description"].title(),
        "Wind Speed": f"{data['wind']['speed']} {speed_unit}",
        "Pressure": f"{data['main']['pressure']} hPa",
        "Visibility": f"{data.get('visibility', 'N/A')} meters",
        "Latitude": data["coord"]["lat"],
        "Longitude": data["coord"]["lon"],
        "Fetched At": datetime.now(timezone.utc).isoformat()
    }

    # Save to database
    insert_weather_data(weather_data)

    # Return response
    return weather_data
