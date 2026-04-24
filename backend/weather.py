"""
weather.py — OpenWeatherMap API integration with fallback mock data
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
BASE_URL = "https://api.openweathermap.org/data/2.5"


def get_weather(city: str) -> dict:
    """Fetch current weather + 5-day forecast for a city."""
    if not OPENWEATHER_API_KEY:
        return _mock_weather(city)
    try:
        # Current weather
        r = requests.get(
            f"{BASE_URL}/weather",
            params={"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"},
            timeout=10,
        )
        if r.status_code != 200:
            return _mock_weather(city)
        cur = r.json()

        # 5-day forecast (every 3 hrs, we take first 5 entries)
        rf = requests.get(
            f"{BASE_URL}/forecast",
            params={"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric", "cnt": 5},
            timeout=10,
        )
        forecast_list = []
        if rf.status_code == 200:
            for item in rf.json().get("list", [])[:5]:
                forecast_list.append({
                    "date": item["dt_txt"],
                    "temp": round(item["main"]["temp"]),
                    "condition": item["weather"][0]["description"].title(),
                    "rain_chance": round(item.get("pop", 0) * 100),
                })

        return {
            "city": city,
            "temperature": round(cur["main"]["temp"]),
            "feels_like": round(cur["main"]["feels_like"]),
            "humidity": cur["main"]["humidity"],
            "condition": cur["weather"][0]["description"].title(),
            "wind_speed": round(cur["wind"]["speed"], 1),
            "forecast": forecast_list,
        }
    except Exception:
        return _mock_weather(city)


def _mock_weather(city: str) -> dict:
    """Fallback mock data when API is unavailable."""
    return {
        "city": city,
        "temperature": 28,
        "feels_like": 31,
        "humidity": 65,
        "condition": "Partly Cloudy",
        "wind_speed": 12.5,
        "forecast": [
            {"date": "Day 1", "temp": 28, "condition": "Sunny", "rain_chance": 10},
            {"date": "Day 2", "temp": 26, "condition": "Cloudy", "rain_chance": 30},
            {"date": "Day 3", "temp": 29, "condition": "Clear Sky", "rain_chance": 5},
            {"date": "Day 4", "temp": 27, "condition": "Light Rain", "rain_chance": 60},
            {"date": "Day 5", "temp": 30, "condition": "Sunny", "rain_chance": 15},
        ],
    }
