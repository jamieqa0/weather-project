import os
import requests
from datetime import date, timedelta
import pandas as pd

BASE_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_current_weather(lat: float, lon: float) -> dict:
    """Open-Meteo API로 현재 날씨 조회. 키 없이 사용 가능."""
    url = (
        f"{BASE_URL}?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,precipitation,relative_humidity_2m,wind_speed_10m,weather_code"
    )
    response = requests.get(url)
    response.raise_for_status()
    current = response.json()["current"]
    return {
        "temperature": current["temperature_2m"],
        "precipitation": current["precipitation"],
        "humidity": current["relative_humidity_2m"],
        "wind_speed": current["wind_speed_10m"],
        "weather_code": current["weather_code"],
    }
