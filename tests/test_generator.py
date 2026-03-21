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
