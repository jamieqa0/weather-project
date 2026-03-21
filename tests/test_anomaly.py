import numpy as np
import pandas as pd
import pytest
from analysis.anomaly import detect_anomalies


def _normal_df(n=100):
    np.random.seed(42)
    return pd.DataFrame({
        'temperature': np.random.normal(15, 3, n),
        'precipitation': np.random.exponential(2, n),
        'humidity': np.random.normal(60, 8, n),
        'wind_speed': np.random.normal(5, 1.5, n),
    })


def test_returns_dataframe():
    result = detect_anomalies(_normal_df())
    assert isinstance(result, pd.DataFrame)


def test_has_is_anomaly_column():
    result = detect_anomalies(_normal_df())
    assert 'is_anomaly' in result.columns


def test_is_anomaly_is_bool():
    result = detect_anomalies(_normal_df())
    assert result['is_anomaly'].dtype == bool


def test_preserves_original_columns():
    df = _normal_df()
    result = detect_anomalies(df)
    for col in df.columns:
        assert col in result.columns


def test_detects_obvious_outliers():
    """명백한 이상치(기온 99도 등) 10개를 포함시키면 탐지해야 함."""
    normal = _normal_df(90)
    outliers = pd.DataFrame({
        'temperature': [99.0] * 10,
        'precipitation': [500.0] * 10,
        'humidity': [99.0] * 10,
        'wind_speed': [100.0] * 10,
    })
    df = pd.concat([normal, outliers], ignore_index=True)
    result = detect_anomalies(df)
    detected = result.iloc[-10:]['is_anomaly'].sum()
    assert detected >= 7  # 10개 중 최소 7개 탐지


def test_anomaly_ratio_approx_contamination():
    """contamination=0.05이면 이상치 비율이 약 5%."""
    result = detect_anomalies(_normal_df(200))
    ratio = result['is_anomaly'].mean()
    assert 0.01 <= ratio <= 0.15  # 1~15% 범위
