from datetime import datetime
import pytest
from commentary.interpretation import (
    interpret_correlation,
    format_last_updated,
    get_anomaly_algorithm_info,
)


# ── interpret_correlation ─────────────────────────────────────────────────────

def test_interpret_correlation_none_returns_no_data():
    assert interpret_correlation(None) == "데이터 없음"


def test_interpret_correlation_near_zero_is_no_correlation():
    result = interpret_correlation(0.05)
    assert "상관" in result
    assert "없" in result


def test_interpret_correlation_negative_near_zero_is_no_correlation():
    result = interpret_correlation(-0.05)
    assert "상관" in result
    assert "없" in result


def test_interpret_correlation_weak_negative():
    result = interpret_correlation(-0.2)
    assert "약한" in result
    assert "음" in result


def test_interpret_correlation_weak_positive():
    result = interpret_correlation(0.2)
    assert "약한" in result
    assert "양" in result


def test_interpret_correlation_medium_negative():
    result = interpret_correlation(-0.5)
    assert "중간" in result
    assert "음" in result


def test_interpret_correlation_medium_positive():
    result = interpret_correlation(0.5)
    assert "중간" in result
    assert "양" in result


def test_interpret_correlation_strong_negative():
    result = interpret_correlation(-0.9)
    assert "강한" in result
    assert "음" in result


def test_interpret_correlation_strong_positive():
    result = interpret_correlation(0.9)
    assert "강한" in result
    assert "양" in result


def test_interpret_correlation_boundary_01():
    """0.1 경계 — 거의 상관없음 마지막 케이스."""
    result = interpret_correlation(0.099)
    assert "없" in result


def test_interpret_correlation_boundary_03():
    """0.3 경계 — 중간 상관관계 시작."""
    result = interpret_correlation(0.3)
    assert "중간" in result


def test_interpret_correlation_boundary_07():
    """0.7 경계 — 강한 상관관계 시작."""
    result = interpret_correlation(0.7)
    assert "강한" in result


def test_interpret_correlation_returns_string():
    assert isinstance(interpret_correlation(0.5), str)
    assert isinstance(interpret_correlation(None), str)


# ── format_last_updated ───────────────────────────────────────────────────────

def test_format_last_updated_returns_string():
    assert isinstance(format_last_updated(datetime(2026, 3, 22, 9, 0)), str)


def test_format_last_updated_am():
    result = format_last_updated(datetime(2026, 3, 22, 9, 30))
    assert "오전" in result
    assert "9시" in result
    assert "30분" in result
    assert "3월" in result
    assert "22일" in result


def test_format_last_updated_pm():
    result = format_last_updated(datetime(2026, 3, 22, 14, 5))
    assert "오후" in result
    assert "2시" in result
    assert "5분" in result


def test_format_last_updated_noon():
    result = format_last_updated(datetime(2026, 3, 22, 12, 0))
    assert "오후" in result
    assert "12시" in result


def test_format_last_updated_midnight():
    result = format_last_updated(datetime(2026, 3, 22, 0, 0))
    assert "오전" in result
    assert "12시" in result


def test_format_last_updated_contains_suffix():
    result = format_last_updated(datetime(2026, 3, 22, 9, 0))
    assert "기준" in result


# ── get_anomaly_algorithm_info ────────────────────────────────────────────────

def test_get_anomaly_algorithm_info_returns_string():
    assert isinstance(get_anomaly_algorithm_info(), str)


def test_get_anomaly_algorithm_info_contains_algorithm_name():
    result = get_anomaly_algorithm_info()
    assert "Isolation Forest" in result


def test_get_anomaly_algorithm_info_contains_contamination():
    result = get_anomaly_algorithm_info()
    assert "5%" in result


def test_get_anomaly_algorithm_info_contains_random_state():
    result = get_anomaly_algorithm_info()
    assert "이상치" in result
