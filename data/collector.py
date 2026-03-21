import os
import requests
from datetime import date, timedelta, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

BASE_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


SAMPLE_SUBWAY_PATH = os.path.join(os.path.dirname(__file__), "sample", "subway.csv")
SEOUL_API_BASE = "http://openapi.seoul.go.kr:8088"
SUBWAY_STATION = "문정"


def fetch_current_weather(lat: float, lon: float) -> dict:
    """Open-Meteo API로 현재 날씨 + 오늘 일 최고·최저·평균기온 조회. 키 없이 사용 가능."""
    url = (
        f"{BASE_URL}?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,precipitation,relative_humidity_2m,wind_speed_10m,weather_code"
        "&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum"
        "&timezone=Asia%2FSeoul"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    current = data["current"]
    daily = data["daily"]

    # daily 배열이 비어있을 경우 current 값으로 기본값 설정
    temp_max = daily["temperature_2m_max"][0] if daily.get("temperature_2m_max") else current["temperature_2m"]
    temp_min = daily["temperature_2m_min"][0] if daily.get("temperature_2m_min") else current["temperature_2m"]
    temp_mean = daily["temperature_2m_mean"][0] if daily.get("temperature_2m_mean") else current["temperature_2m"]
    precip_sum = daily["precipitation_sum"][0] if daily.get("precipitation_sum") else current["precipitation"]

    return {
        "temperature": current["temperature_2m"],
        "temperature_max": temp_max,
        "temperature_min": temp_min,
        "temperature_mean": temp_mean,
        "precipitation": current["precipitation"],
        "precipitation_sum": precip_sum,
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
        "&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
        "precipitation_sum,relative_humidity_2m_mean,wind_speed_10m_max"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    daily = response.json()["daily"]
    df = pd.DataFrame({
        "date":        daily["time"],
        "temp_max":    daily["temperature_2m_max"],
        "temp_min":    daily["temperature_2m_min"],
        "temperature": daily["temperature_2m_mean"],
        "precipitation": daily["precipitation_sum"],
        "humidity":    daily["relative_humidity_2m_mean"],
        "wind_speed":  daily["wind_speed_10m_max"],
    })
    df["temp_range"] = df["temp_max"] - df["temp_min"]
    return df


def fetch_weather_on_date(lat: float, lon: float, target_date: date) -> dict:
    """특정 날짜의 날씨 조회 (Open-Meteo 아카이브 API). 1년 전 비교 등에 사용."""
    url = (
        f"{ARCHIVE_URL}?latitude={lat}&longitude={lon}"
        f"&start_date={target_date}&end_date={target_date}"
        "&daily=temperature_2m_max,precipitation_sum,relative_humidity_2m_mean,wind_speed_10m_max"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    daily = response.json()["daily"]
    return {
        "date": daily["time"][0],
        "temperature": daily["temperature_2m_max"][0],
        "precipitation": daily["precipitation_sum"][0],
        "humidity": daily["relative_humidity_2m_mean"][0],
        "wind_speed": daily["wind_speed_10m_max"][0],
    }


def _fetch_subway_day(api_key: str, date_str: str) -> dict | None:
    """단일 날짜 문정역 지하철 데이터 조회. 데이터 없으면 None 반환."""
    url = f"{SEOUL_API_BASE}/{api_key}/json/CardSubwayStatsNew/1/1000/{date_str}/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json().get("CardSubwayStatsNew", {})
        if data.get("RESULT", {}).get("CODE") != "INFO-000":
            return None
        for row in data.get("row", []):
            if row.get("SBWY_STNS_NM") == SUBWAY_STATION:
                return {
                    "date": datetime.strptime(row["USE_YMD"], "%Y%m%d").strftime("%Y-%m-%d"),
                    "passengers": int(row["GTON_TNOPE"]) + int(row["GTOFF_TNOPE"]),
                }
    except Exception:
        pass
    return None


def fetch_subway_data(api_key: str | None = None) -> pd.DataFrame:
    """서울 지하철 문정역 일별 이용객 수 조회.
    api_key 없으면 샘플 데이터 반환.
    날짜별 병렬 조회(20 workers)로 최근 1년 데이터 수집.
    """
    if api_key is None:
        return pd.read_csv(SAMPLE_SUBWAY_PATH, encoding='utf-8-sig')

    # API 데이터 lag 약 3~7일 고려, 1년치 조회
    dates = [
        (date.today() - timedelta(days=i)).strftime("%Y%m%d")
        for i in range(5, 371)  # 5~370일 전 (366일 범위)
    ]

    records = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(_fetch_subway_day, api_key, d) for d in dates]
        for future in as_completed(futures):
            result = future.result()
            if result:
                records.append(result)

    if not records:
        return pd.read_csv(SAMPLE_SUBWAY_PATH, encoding='utf-8-sig')

    return pd.DataFrame(records).sort_values("date").reset_index(drop=True)
