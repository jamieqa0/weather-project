import os
import requests
from datetime import date, timedelta
import pandas as pd

BASE_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


SAMPLE_SUBWAY_PATH = os.path.join(os.path.dirname(__file__), "sample", "subway.csv")


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


def fetch_historical_weather(lat: float, lon: float, days: int = 90) -> pd.DataFrame:
    """Open-Meteo 아카이브 API로 과거 날씨 조회."""
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    url = (
        f"{ARCHIVE_URL}?latitude={lat}&longitude={lon}"
        f"&start_date={start}&end_date={end}"
        "&daily=temperature_2m_max,precipitation_sum,relative_humidity_2m_mean,wind_speed_10m_max"
    )
    response = requests.get(url)
    response.raise_for_status()
    daily = response.json()["daily"]
    return pd.DataFrame({
        "date": daily["time"],
        "temperature": daily["temperature_2m_max"],
        "precipitation": daily["precipitation_sum"],
        "humidity": daily["relative_humidity_2m_mean"],
        "wind_speed": daily["wind_speed_10m_max"],
    })


def fetch_subway_data(api_key: str | None = None) -> pd.DataFrame:
    """서울 지하철 이용객 수 조회. api_key 없으면 샘플 데이터 반환."""
    if api_key is None:
        return pd.read_csv(SAMPLE_SUBWAY_PATH, encoding='utf-8-sig')
    # TODO: 실제 서울 열린데이터광장 API 연동
    raise NotImplementedError("API 연동 미구현 — api_key=None으로 샘플 데이터 사용")
