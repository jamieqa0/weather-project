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
