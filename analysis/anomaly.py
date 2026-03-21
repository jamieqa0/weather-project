import pandas as pd
from sklearn.ensemble import IsolationForest

FEATURES = ['temperature', 'precipitation', 'humidity', 'wind_speed']
CONTAMINATION = 0.10


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Isolation Forest로 이상 기후 탐지.
    입력 DataFrame에 'is_anomaly' bool 컬럼을 추가해 반환.
    스케일 정규화 미적용 — 트리 기반 알고리즘은 스케일 불변.
    """
    model = IsolationForest(contamination=CONTAMINATION, random_state=42)
    predictions = model.fit_predict(df[FEATURES])
    result = df.copy()
    result['is_anomaly'] = predictions == -1  # -1 = 이상치
    return result
