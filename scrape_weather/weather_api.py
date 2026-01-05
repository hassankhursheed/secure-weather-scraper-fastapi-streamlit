import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not API_KEY:
    raise RuntimeError("OPENWEATHER_API_KEY is not set")

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def fetch_weather(city, units="metric"):
    parameters = {
        "q": city,
        "appid": API_KEY,
        "units": units
    }

    response = requests.get(BASE_URL, params=parameters)

    if response.status_code == 200:
        return response.json()
    else:
        return None