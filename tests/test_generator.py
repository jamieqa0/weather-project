import pytest
from commentary.generator import generate_comment


def test_returns_string():
    result = generate_comment(temp_c=15, precipitation_mm=0, weather_code=0)
    assert isinstance(result, str)
    assert len(result) > 0


def test_cold_weather():
    result = generate_comment(temp_c=-5, precipitation_mm=0, weather_code=71)
    assert any(word in result for word in ["냉동", "춥", "꽁꽁", "나가지"])


def test_heavy_rain():
    result = generate_comment(temp_c=20, precipitation_mm=25, weather_code=63)
    assert any(word in result for word in ["우산", "비", "폭우"])


def test_hot_weather():
    result = generate_comment(temp_c=36, precipitation_mm=0, weather_code=0)
    assert any(word in result for word in ["폭염", "더위", "녹", "에어컨"])


def test_clear_weather():
    result = generate_comment(temp_c=22, precipitation_mm=0, weather_code=0)
    assert any(word in result for word in ["맑", "날씨", "인생"])


# Phase 1: 추가 커버리지 테스트

def test_light_rain_code_61():
    """날씨코드 61 (작은 빗소리)"""
    result = generate_comment(temp_c=15, precipitation_mm=5, weather_code=61)
    assert "우산" in result or "비" in result


def test_moderate_rain_code_65():
    """날씨코드 65 (중간 빗소리)"""
    result = generate_comment(temp_c=18, precipitation_mm=8, weather_code=65)
    assert "우산" in result or "비" in result


def test_rain_shower_code_80():
    """날씨코드 80 (빗방울)"""
    result = generate_comment(temp_c=12, precipitation_mm=3, weather_code=80)
    assert "우산" in result or "비" in result


def test_rain_shower_code_81():
    """날씨코드 81 (빗소리)"""
    result = generate_comment(temp_c=14, precipitation_mm=4, weather_code=81)
    assert "우산" in result or "비" in result


def test_rain_shower_code_82():
    """날씨코드 82 (강한 빗소리)"""
    result = generate_comment(temp_c=16, precipitation_mm=6, weather_code=82)
    assert "우산" in result or "비" in result


def test_snow_code_73():
    """날씨코드 73 (눈입자) - 0°C 이상이어야 라인 11 도달"""
    result = generate_comment(temp_c=0, precipitation_mm=2, weather_code=73)
    assert "눈" in result or "조심" in result


def test_snow_code_75():
    """날씨코드 75 (빙정) - 0°C 이상이어야 라인 11 도달"""
    result = generate_comment(temp_c=1, precipitation_mm=2, weather_code=75)
    assert "눈" in result or "조심" in result


def test_cold_without_freezing():
    """0°C ~ 5°C 범위 (라인 16 커버)"""
    result = generate_comment(temp_c=3, precipitation_mm=0, weather_code=0)
    assert "춥" in result or "겉옷" in result


def test_cold_boundary_5c():
    """정확히 5°C (경계값)"""
    result = generate_comment(temp_c=5, precipitation_mm=0, weather_code=0)
    assert "춥" in result or "겉옷" in result or "그럭저럭" in result
