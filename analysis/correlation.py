import pandas as pd
from scipy import stats


def compute_correlation(weather_df: pd.DataFrame, subway_df: pd.DataFrame) -> dict:
    """
    날씨(기온) × 지하철 이용객 수 상관계수 계산.
    평일 데이터만 사용 (요일 효과 통제).
    Pearson + Spearman 병행 계산.
    """
    merged = pd.merge(weather_df, subway_df, on='date')
    merged['date'] = pd.to_datetime(merged['date'])
    # 평일만 (월=0 ~ 금=4)
    merged = merged[merged['date'].dt.weekday < 5]

    if len(merged) < 2:
        return {'pearson': None, 'spearman': None, 'n_samples': 0}

    x = merged['temperature'].values
    y = merged['passengers'].values

    pearson_r, _ = stats.pearsonr(x, y)
    spearman_r, _ = stats.spearmanr(x, y)

    return {
        'pearson': round(float(pearson_r), 4),
        'spearman': round(float(spearman_r), 4),
        'n_samples': len(merged),
    }
