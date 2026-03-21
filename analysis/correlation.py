import pandas as pd
from scipy import stats


def compute_correlation(weather_df: pd.DataFrame, subway_df: pd.DataFrame) -> dict:
    """
    날씨(기온, 강수량) × 지하철 이용객 수 상관계수 계산.
    평일 데이터만 사용 (요일 효과 통제).
    Pearson + Spearman 병행 계산.
    """
    merged = pd.merge(weather_df, subway_df, on='date')
    merged['date'] = pd.to_datetime(merged['date'])
    # 평일만 (월=0 ~ 금=4)
    merged = merged[merged['date'].dt.weekday < 5]

    if len(merged) < 2:
        return {
            'pearson': None, 'spearman': None,
            'precipitation_pearson': None, 'precipitation_spearman': None,
            'n_samples': 0
        }

    # 기온과 지하철 이용객 수의 상관계수
    temp = merged['temperature'].values
    passengers = merged['passengers'].values
    temp_pearson, _ = stats.pearsonr(temp, passengers)
    temp_spearman, _ = stats.spearmanr(temp, passengers)

    # 강수량과 지하철 이용객 수의 상관계수
    precip = merged['precipitation'].values
    precip_pearson, _ = stats.pearsonr(precip, passengers)
    precip_spearman, _ = stats.spearmanr(precip, passengers)

    return {
        'pearson': round(float(temp_pearson), 4),
        'spearman': round(float(temp_spearman), 4),
        'precipitation_pearson': round(float(precip_pearson), 4),
        'precipitation_spearman': round(float(precip_spearman), 4),
        'n_samples': len(merged),
    }
