from unittest.mock import patch, MagicMock
import pytest
from data.collector import fetch_current_weather


MOCK_CURRENT_RESPONSE = {
    "current": {
        "temperature_2m": 12.5,
        "precipitation": 0.0,
        "relative_humidity_2m": 70,
        "wind_speed_10m": 5.2,
        "weather_code": 3
    }
}


def test_fetch_current_weather_keys():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_CURRENT_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        result = fetch_current_weather(lat=37.4946, lon=127.1237)
    assert set(result.keys()) == {'temperature', 'precipitation', 'humidity', 'wind_speed', 'weather_code'}


def test_fetch_current_weather_values():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_CURRENT_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        result = fetch_current_weather(lat=37.4946, lon=127.1237)
    assert result['temperature'] == 12.5
    assert result['humidity'] == 70
    assert result['weather_code'] == 3


def test_fetch_current_weather_calls_correct_url():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_CURRENT_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        fetch_current_weather(lat=37.4946, lon=127.1237)
    call_url = mock_get.call_args[0][0]
    assert 'open-meteo.com' in call_url
    assert '37.4946' in call_url


import pandas as pd
from data.collector import fetch_historical_weather, fetch_subway_data

MOCK_HISTORICAL_RESPONSE = {
    "daily": {
        "time": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "temperature_2m_max": [5.0, 7.0, 3.0],
        "precipitation_sum": [0.0, 5.2, 0.0],
        "relative_humidity_2m_mean": [60.0, 70.0, 55.0],
        "wind_speed_10m_max": [3.0, 8.0, 5.0],
    }
}


def test_fetch_historical_weather_returns_dataframe():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_HISTORICAL_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        df = fetch_historical_weather(lat=37.4946, lon=127.1237, days=3)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ['date', 'temperature', 'precipitation', 'humidity', 'wind_speed']
    assert len(df) == 3


def test_fetch_historical_weather_date_column_is_string():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_HISTORICAL_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        df = fetch_historical_weather(lat=37.4946, lon=127.1237, days=3)
    assert df['date'].dtype == object  # string


def test_fetch_subway_data_fallback_no_key():
    """API 키 없을 때 샘플 CSV 반환"""
    df = fetch_subway_data(api_key=None)
    assert isinstance(df, pd.DataFrame)
    assert 'date' in df.columns
    assert 'passengers' in df.columns
    assert len(df) > 0


def test_fetch_subway_data_fallback_columns():
    df = fetch_subway_data(api_key=None)
    assert df['passengers'].dtype in ['int64', 'int32', 'float64']
