import os
import pandas as pd


def save_csv(df: pd.DataFrame, path: str) -> None:
    """DataFrame을 CSV로 저장. 부모 디렉토리가 없으면 생성."""
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    df.to_csv(path, index=False, encoding='utf-8-sig')


def load_csv(path: str) -> pd.DataFrame:
    """CSV를 DataFrame으로 로드."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"파일 없음: {path}")
    return pd.read_csv(path, encoding='utf-8-sig')
