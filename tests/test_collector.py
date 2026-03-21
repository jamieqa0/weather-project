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


# Phase 3: 예외 처리 테스트

def test_fetch_subway_day_returns_none_on_api_timeout():
    """API 타임아웃 시 None 반환 (라인 109-111)"""
    with patch('data.collector.requests.get') as mock_get:
        mock_get.side_effect = TimeoutError("Connection timeout")
        result = _fetch_subway_day("testkey", "20250322")
    assert result is None


def test_fetch_subway_day_returns_none_on_json_error():
    """JSON 파싱 에러 시 None 반환"""
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value.raise_for_status = MagicMock()
        result = _fetch_subway_day("testkey", "20250322")
    assert result is None


def test_fetch_subway_day_returns_none_on_key_error():
    """필수 키 없을 때 None 반환"""
    invalid_response = {
        "CardSubwayStatsNew": {
            "list_total_count": 1,
            "RESULT": {"CODE": "INFO-000"},
            "row": [
                {"USE_YMD": "20250322"}  # SBWY_STNS_NM 누락
            ]
        }
    }
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = invalid_response
        mock_get.return_value.raise_for_status = MagicMock()
        result = _fetch_subway_day("testkey", "20250322")
    assert result is None


def test_fetch_current_weather_handles_missing_daily_data():
    """daily 배열이 비어있을 때도 처리 (collector.py의 에러 처리)"""
    incomplete_response = {
        "current": {
            "temperature_2m": 12.5,
            "precipitation": 0.0,
            "relative_humidity_2m": 70,
            "wind_speed_10m": 5.2,
            "weather_code": 3
        },
        "daily": {
            "temperature_2m_max": [],  # 빈 배열
            "temperature_2m_min": [],
            "temperature_2m_mean": [],
            "precipitation_sum": [],
        }
    }
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = incomplete_response
        mock_get.return_value.raise_for_status = MagicMock()
        result = fetch_current_weather(lat=37.4946, lon=127.1237)

    # current 값으로 기본값이 설정되어야 함
    assert result['temperature'] == 12.5
    assert result['temperature_max'] == 12.5  # current 값으로 폴백
    assert result['temperature_min'] == 12.5
    assert result['temperature_mean'] == 12.5


# Phase 4: 데이터 정합성 및 형식 검증

def test_fetch_current_weather_data_types():
    """반환되는 데이터 타입 검증"""
    w, s = MOCK_CURRENT_RESPONSE, None
    result = fetch_current_weather(37.4946, 127.1237)
    # 모든 온도는 float/int
    assert isinstance(result['temperature'], (int, float))
    assert isinstance(result['temperature_max'], (int, float))
    assert isinstance(result['precipitation'], (int, float))
    assert isinstance(result['humidity'], (int, float))


def test_fetch_current_weather_value_ranges():
    """데이터 범위 검증 (-50°C ~ 50°C, 0% ~ 100% 습도)"""
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_CURRENT_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        result = fetch_current_weather(37.4946, 127.1237)

    # 온도 범위 (-50 ~ 50°C)
    assert -50 <= result['temperature'] <= 50
    assert -50 <= result['temperature_max'] <= 50
    # 습도 범위 (0 ~ 100%)
    assert 0 <= result['humidity'] <= 100
    # 풍속 범위 (0 ~ 100 km/h)
    assert 0 <= result['wind_speed'] <= 100


def test_fetch_historical_weather_date_format_consistency():
    """모든 날짜가 YYYY-MM-DD 문자열 형식"""
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_HISTORICAL_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        df = fetch_historical_weather(37.4946, 127.1237, days=3)

    import re
    for date_str in df['date']:
        assert re.match(r'^\d{4}-\d{2}-\d{2}$', str(date_str))


def test_fetch_historical_weather_no_missing_values():
    """필수 컬럼에 NaN 값 없음"""
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_HISTORICAL_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        df = fetch_historical_weather(37.4946, 127.1237, days=3)

    required_cols = ['date', 'temperature', 'precipitation', 'humidity']
    for col in required_cols:
        assert df[col].notna().all(), f"Column {col} has NaN values"


def test_subway_data_merge_consistency():
    """날씨와 지하철 데이터 병합 후 데이터 일관성"""
    weather_df = pd.DataFrame({
        'date': ['2023-01-02', '2023-01-03', '2023-01-04'],
        'temperature': [10.0, 12.0, 8.0],
        'precipitation': [0.0, 1.5, 0.5],
    })
    subway_df = pd.DataFrame({
        'date': ['2023-01-02', '2023-01-03', '2023-01-04'],
        'passengers': [25000, 26000, 24000],
    })

    merged = pd.merge(weather_df, subway_df, on='date')

    # 모든 행이 유지됨
    assert len(merged) == 3
    # 모든 필수 컬럼 존재
    assert set(['date', 'temperature', 'precipitation', 'passengers']).issubset(merged.columns)
