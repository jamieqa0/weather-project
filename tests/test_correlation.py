import numpy as np
import pandas as pd
import pytest
from analysis.correlation import compute_correlation


def _make_data(n=60, seed=42):
    np.random.seed(seed)
    dates = pd.date_range('2023-01-02', periods=n, freq='B')  # 평일만
    weather = pd.DataFrame({
        'date': dates.strftime('%Y-%m-%d'),
        'temperature': np.random.normal(15, 8, n),
        'precipitation': np.random.exponential(3, n),
    })
    subway = pd.DataFrame({
        'date': dates.strftime('%Y-%m-%d'),
        'passengers': np.random.randint(20000, 40000, n),
    })
    return weather, subway


def test_returns_dict():
    w, s = _make_data()
    result = compute_correlation(w, s)
    assert isinstance(result, dict)


def test_has_pearson_and_spearman():
    w, s = _make_data()
    result = compute_correlation(w, s)
    assert 'pearson' in result
    assert 'spearman' in result


def test_correlation_range():
    w, s = _make_data()
    result = compute_correlation(w, s)
    assert -1.0 <= result['pearson'] <= 1.0
    assert -1.0 <= result['spearman'] <= 1.0


def test_has_n_samples():
    w, s = _make_data()
    result = compute_correlation(w, s)
    assert 'n_samples' in result
    assert result['n_samples'] > 0


def test_strong_positive_correlation():
    """온도와 승객수가 강한 양의 상관관계일 때 탐지."""
    n = 100
    temp = np.linspace(5, 35, n)
    dates = pd.date_range('2023-01-02', periods=n, freq='B').strftime('%Y-%m-%d')
    weather = pd.DataFrame({
        'date': list(dates),
        'temperature': temp,
        'precipitation': [0.0] * n,
    })
    subway = pd.DataFrame({
        'date': list(dates),
        'passengers': (temp * 1000 + 10000).astype(int),
    })
    result = compute_correlation(weather, subway)
    assert result['pearson'] > 0.9
    assert result['spearman'] > 0.9
