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
    },
    "daily": {
        "time": ["2026-03-22"],
        "temperature_2m_max": [17.0],
        "temperature_2m_min": [4.0],
        "temperature_2m_mean": [10.5],
        "precipitation_sum": [0.0],
    }
}


def test_fetch_current_weather_keys():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_CURRENT_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        result = fetch_current_weather(lat=37.4946, lon=127.1237)
    assert set(result.keys()) == {
        'temperature', 'temperature_max', 'temperature_min', 'temperature_mean',
        'precipitation', 'precipitation_sum',
        'humidity', 'wind_speed', 'weather_code',
    }


def test_fetch_current_weather_values():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_CURRENT_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        result = fetch_current_weather(lat=37.4946, lon=127.1237)
    assert result['temperature'] == 12.5
    assert result['temperature_max'] == 17.0
    assert result['temperature_min'] == 4.0
    assert result['temperature_mean'] == 10.5
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
from datetime import date
from data.collector import fetch_historical_weather, fetch_subway_data, fetch_weather_on_date

MOCK_HISTORICAL_RESPONSE = {
    "daily": {
        "time": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "temperature_2m_max": [5.0, 7.0, 3.0],
        "temperature_2m_min": [-2.0, 0.0, -4.0],
        "temperature_2m_mean": [1.5, 3.5, -0.5],
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
    assert list(df.columns) == ['date', 'temp_max', 'temp_min', 'temperature', 'precipitation', 'humidity', 'wind_speed', 'temp_range']
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


from data.collector import _fetch_subway_day

MOCK_SEOUL_DAY_RESPONSE = {
    "CardSubwayStatsNew": {
        "list_total_count": 2,
        "RESULT": {"CODE": "INFO-000", "MESSAGE": "정상 처리되었습니다"},
        "row": [
            {"USE_YMD": "20250322", "SBWY_ROUT_LN_NM": "8호선", "SBWY_STNS_NM": "문정", "GTON_TNOPE": "8000", "GTOFF_TNOPE": "7904", "REG_YMD": "20250325"},
            {"USE_YMD": "20250322", "SBWY_ROUT_LN_NM": "5호선", "SBWY_STNS_NM": "장지", "GTON_TNOPE": "10000", "GTOFF_TNOPE": "9500", "REG_YMD": "20250325"},
        ],
    }
}

MOCK_SEOUL_NO_DATA = {"CardSubwayStatsNew": {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다"}}}


# ── _fetch_subway_day 단위 테스트 ─────────────────────────────────────────────

def test_fetch_subway_day_returns_munjeong_record():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_SEOUL_DAY_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        result = _fetch_subway_day("testkey", "20250322")
    assert result is not None
    assert result['date'] == '2025-03-22'


def test_fetch_subway_day_sums_gton_and_gtoff():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_SEOUL_DAY_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        result = _fetch_subway_day("testkey", "20250322")
    assert result['passengers'] == 15904  # 8000 + 7904


def test_fetch_subway_day_filters_munjeong_only():
    """장지역 row가 있어도 문정역만 반환."""
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_SEOUL_DAY_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        result = _fetch_subway_day("testkey", "20250322")
    assert result['date'] == '2025-03-22'  # 장지역 데이터 아님


def test_fetch_subway_day_returns_none_on_no_data():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_SEOUL_NO_DATA
        mock_get.return_value.raise_for_status = MagicMock()
        result = _fetch_subway_day("testkey", "20260322")
    assert result is None


def test_fetch_subway_day_date_format():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_SEOUL_DAY_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        result = _fetch_subway_day("testkey", "20250322")
    import re
    assert re.match(r'\d{4}-\d{2}-\d{2}', result['date'])


# ── fetch_subway_data 통합 테스트 ─────────────────────────────────────────────

def test_fetch_subway_data_with_api_key_returns_dataframe():
    with patch('data.collector._fetch_subway_day') as mock_day:
        mock_day.return_value = {"date": "2025-03-22", "passengers": 15904}
        df = fetch_subway_data(api_key="testkey123")
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ['date', 'passengers']


def test_fetch_subway_data_with_api_key_calls_fetch_day():
    with patch('data.collector._fetch_subway_day') as mock_day:
        mock_day.return_value = None
        fetch_subway_data(api_key="testkey123")
    assert mock_day.called
    # 첫 번째 호출 인자에 API 키 포함
    assert mock_day.call_args_list[0][0][0] == "testkey123"


MOCK_DATE_RESPONSE = {
    "daily": {
        "time": ["2025-03-22"],
        "temperature_2m_max": [8.5],
        "precipitation_sum": [1.2],
        "relative_humidity_2m_mean": [65.0],
        "wind_speed_10m_max": [4.5],
    }
}


def test_fetch_weather_on_date_returns_dict():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_DATE_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        result = fetch_weather_on_date(lat=37.4946, lon=127.1237, target_date=date(2025, 3, 22))
    assert isinstance(result, dict)


def test_fetch_weather_on_date_has_required_keys():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_DATE_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        result = fetch_weather_on_date(lat=37.4946, lon=127.1237, target_date=date(2025, 3, 22))
    assert set(result.keys()) == {'date', 'temperature', 'precipitation', 'humidity', 'wind_speed'}


def test_fetch_weather_on_date_values():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_DATE_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        result = fetch_weather_on_date(lat=37.4946, lon=127.1237, target_date=date(2025, 3, 22))
    assert result['temperature'] == 8.5
    assert result['date'] == '2025-03-22'


def test_fetch_weather_on_date_calls_archive_url_with_date():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_DATE_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        fetch_weather_on_date(lat=37.4946, lon=127.1237, target_date=date(2025, 3, 22))
    call_url = mock_get.call_args[0][0]
    assert 'archive-api.open-meteo.com' in call_url
    assert '2025-03-22' in call_url
