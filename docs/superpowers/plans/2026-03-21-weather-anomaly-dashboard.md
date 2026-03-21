# 기후탐정 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 문정역(서울) ↔ 몬테비데오(우루과이) 날씨 데이터를 수집·분석해 이상 기후를 탐지하고 지하철 상관관계를 시각화하는 Streamlit 웹 대시보드 구축

**Architecture:** Open-Meteo API로 날씨를 수집해 CSV에 저장하고, Isolation Forest로 이상 탐지 + Pearson/Spearman 상관분석을 수행한다. Streamlit app.py가 각 모듈을 조합해 Eridian Horizon 다크 테마로 렌더링한다.

**Tech Stack:** Python 3.11+, Streamlit, Plotly, scikit-learn, pandas, scipy, requests, python-dotenv, pytest

---

## 파일 맵

| 파일 | 역할 |
|------|------|
| `app.py` | Streamlit 메인 — 모든 모듈을 조합해 UI 렌더링 |
| `data/collector.py` | Open-Meteo API 호출 (현재/과거 날씨), 서울 지하철 API + 샘플 폴백 |
| `data/storage.py` | pandas DataFrame ↔ CSV 저장/로드 |
| `data/sample/subway.csv` | 지하철 API 키 없을 때 쓰는 샘플 데이터 |
| `analysis/anomaly.py` | Isolation Forest 이상 탐지 |
| `analysis/correlation.py` | 날씨 × 지하철 Pearson + Spearman 상관계수 계산 |
| `commentary/generator.py` | 규칙 기반 감성 멘트 생성 (추후 LLM 교체 가능 구조) |
| `assets/style.css` | Eridian Horizon 커스텀 CSS (Streamlit 주입용) |
| `tests/test_generator.py` | commentary 단위 테스트 |
| `tests/test_storage.py` | storage 단위 테스트 |
| `tests/test_collector.py` | collector 단위 테스트 (HTTP 모킹) |
| `tests/test_anomaly.py` | 이상 탐지 단위 테스트 |
| `tests/test_correlation.py` | 상관관계 단위 테스트 |

---

## Task 1: 프로젝트 초기화

**Files:**
- Create: `weather-project/requirements.txt`
- Create: `weather-project/.gitignore`
- Create: `weather-project/.env.example`
- Create: `weather-project/data/__init__.py`
- Create: `weather-project/analysis/__init__.py`
- Create: `weather-project/commentary/__init__.py`
- Create: `weather-project/tests/__init__.py`
- Create: `weather-project/data/sample/subway.csv`

- [ ] **Step 1: 프로젝트 폴더 생성**

```bash
cd "C:/Users/이유미/Documents/study"
mkdir -p weather-project/{data/sample,analysis,commentary,assets,tests}
cd weather-project
```

- [ ] **Step 2: requirements.txt 작성**

```
streamlit>=1.32.0
pandas>=2.0.0
plotly>=5.18.0
scikit-learn>=1.4.0
requests>=2.31.0
python-dotenv>=1.0.0
scipy>=1.12.0
statsmodels>=0.14.0
pytest>=8.0.0
```

- [ ] **Step 3: .gitignore 작성**

```
.env
__pycache__/
*.pyc
.pytest_cache/
data/*.csv
!data/sample/*.csv
generate_sample.py
```

- [ ] **Step 4: .env.example 작성**

```
SEOUL_API_KEY=your_key_here
```

- [ ] **Step 5: __init__.py 파일 생성 (모두 빈 파일)**

```bash
touch data/__init__.py analysis/__init__.py commentary/__init__.py tests/__init__.py
```

- [ ] **Step 6: 샘플 지하철 CSV 생성 (스크립트 실행)**

아래 파이썬 스크립트를 임시 실행해서 `data/sample/subway.csv` 생성:

```python
import pandas as pd
import numpy as np

np.random.seed(42)
dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
# 주말 제외한 평일만
weekdays = [d for d in dates if d.weekday() < 5]

df = pd.DataFrame({
    'date': [d.strftime('%Y-%m-%d') for d in weekdays],
    'passengers': np.random.randint(18000, 42000, len(weekdays))
})
df.to_csv('data/sample/subway.csv', index=False, encoding='utf-8-sig')
print(f"생성 완료: {len(df)}개 행")
```

```bash
python generate_sample.py
```

Expected output: `생성 완료: 261개 행`

- [ ] **Step 7: 패키지 설치**

```bash
pip install -r requirements.txt
```

- [ ] **Step 8: git 초기화 + 첫 커밋**

```bash
git init
git add requirements.txt .gitignore .env.example data/__init__.py analysis/__init__.py commentary/__init__.py tests/__init__.py data/sample/subway.csv
git commit -m "chore: 프로젝트 초기화"
```

---

## Task 2: commentary/generator.py — 감성 멘트 생성기

**Files:**
- Create: `tests/test_generator.py`
- Create: `commentary/generator.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_generator.py`:

```python
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
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_generator.py -v
```

Expected: `ModuleNotFoundError: No module named 'commentary.generator'`

- [ ] **Step 3: generator.py 구현**

`commentary/generator.py`:

```python
def generate_comment(temp_c: float, precipitation_mm: float, weather_code: int) -> str:
    """날씨 조건에 따른 감성 멘트 반환. 추후 LLM으로 교체 가능."""
    if temp_c < 0:
        return "오늘은 냉동창고 수준. 나가지 마세요. 진심으로."
    if temp_c >= 35:
        return "폭염 주의. 에어컨 없는 사람은 오늘 하루 용감한 겁니다."
    if precipitation_mm >= 20:
        return "우산은 장식이 아닙니다. 폭우 수준이에요."
    if weather_code in (61, 63, 65, 80, 81, 82):
        return "비 오네요. 우산 챙기셨죠? 안 챙기셨죠?"
    if weather_code in (71, 73, 75):
        return "눈 옵니다. 길 미끄러우니 조심하세요."
    if weather_code == 0 and temp_c >= 18:
        return "날씨만큼은 인생보다 맑네요. 나가세요."
    if temp_c < 5:
        return "꽤 춥습니다. 겉옷 챙기세요."
    return "오늘 날씨: 인생처럼 그럭저럭입니다."
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_generator.py -v
```

Expected: `5 passed`

- [ ] **Step 5: 커밋**

```bash
git add commentary/generator.py tests/test_generator.py
git commit -m "feat: 규칙 기반 감성 멘트 생성기 구현"
```

---

## Task 3: data/storage.py — CSV 저장/로드

**Files:**
- Create: `tests/test_storage.py`
- Create: `data/storage.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_storage.py`:

```python
import os
import tempfile
import pandas as pd
import pytest
from data.storage import save_csv, load_csv


def test_save_creates_file():
    df = pd.DataFrame({'a': [1, 2, 3]})
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'test.csv')
        save_csv(df, path)
        assert os.path.exists(path)


def test_roundtrip():
    df = pd.DataFrame({'date': ['2024-01-01', '2024-01-02'], 'temp': [10.5, 12.3]})
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'test.csv')
        save_csv(df, path)
        loaded = load_csv(path)
    pd.testing.assert_frame_equal(df, loaded)


def test_load_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_csv('/nonexistent/path/test.csv')


def test_save_creates_parent_dirs():
    df = pd.DataFrame({'x': [1]})
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'subdir', 'nested', 'test.csv')
        save_csv(df, path)
        assert os.path.exists(path)
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_storage.py -v
```

Expected: `ModuleNotFoundError: No module named 'data.storage'`

- [ ] **Step 3: storage.py 구현**

`data/storage.py`:

```python
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
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_storage.py -v
```

Expected: `4 passed`

- [ ] **Step 5: 커밋**

```bash
git add data/storage.py tests/test_storage.py
git commit -m "feat: CSV 저장/로드 유틸리티 구현"
```

---

## Task 4: data/collector.py — 현재 날씨 수집

**Files:**
- Create: `tests/test_collector.py`
- Create: `data/collector.py`

Open-Meteo 현재 날씨 API 형식:
```
GET https://api.open-meteo.com/v1/forecast
  ?latitude=37.4946&longitude=127.1237
  &current=temperature_2m,precipitation,relative_humidity_2m,wind_speed_10m,weather_code
```

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_collector.py`:

```python
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
    }
}


def test_fetch_current_weather_keys():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_CURRENT_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        result = fetch_current_weather(lat=37.4946, lon=127.1237)
    assert set(result.keys()) == {'temperature', 'precipitation', 'humidity', 'wind_speed', 'weather_code'}


def test_fetch_current_weather_values():
    with patch('data.collector.requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_CURRENT_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        result = fetch_current_weather(lat=37.4946, lon=127.1237)
    assert result['temperature'] == 12.5
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
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_collector.py -v
```

Expected: `ModuleNotFoundError: No module named 'data.collector'`

- [ ] **Step 3: collector.py 구현 (현재 날씨 부분)**

`data/collector.py`:

```python
import requests
from datetime import date, timedelta
import pandas as pd

BASE_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_current_weather(lat: float, lon: float) -> dict:
    """Open-Meteo API로 현재 날씨 조회. 키 없이 사용 가능."""
    url = (
        f"{BASE_URL}?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,precipitation,relative_humidity_2m,wind_speed_10m,weather_code"
    )
    response = requests.get(url)
    response.raise_for_status()
    current = response.json()["current"]
    return {
        "temperature": current["temperature_2m"],
        "precipitation": current["precipitation"],
        "humidity": current["relative_humidity_2m"],
        "wind_speed": current["wind_speed_10m"],
        "weather_code": current["weather_code"],
    }
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_collector.py -v
```

Expected: `3 passed`

- [ ] **Step 5: 커밋**

```bash
git add data/collector.py tests/test_collector.py
git commit -m "feat: Open-Meteo 현재 날씨 수집 구현"
```

---

## Task 5: data/collector.py — 과거 날씨 + 지하철 폴백

**Files:**
- Modify: `data/collector.py`
- Modify: `tests/test_collector.py`

Open-Meteo 과거 날씨 API 형식:
```
GET https://archive-api.open-meteo.com/v1/archive
  ?latitude=37.4946&longitude=127.1237
  &start_date=2024-01-01&end_date=2024-03-31
  &daily=temperature_2m_max,precipitation_sum,relative_humidity_2m_mean,wind_speed_10m_max
```

- [ ] **Step 1: 테스트 추가**

`tests/test_collector.py` 하단에 추가 (파일 상단의 `from unittest.mock import patch, MagicMock` import는 Task 4에서 이미 선언되어 있으므로 중복 추가 불필요):

```python
import pandas as pd
from data.collector import fetch_historical_weather, fetch_subway_data

MOCK_HISTORICAL_RESPONSE = {
    "daily": {
        "time": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "temperature_2m_max": [5.0, 7.0, 3.0],
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
    assert list(df.columns) == ['date', 'temperature', 'precipitation', 'humidity', 'wind_speed']
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
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_collector.py -v
```

Expected: `ImportError: cannot import name 'fetch_historical_weather'`

- [ ] **Step 3: collector.py에 함수 추가**

`data/collector.py` 하단에 추가:

```python
SAMPLE_SUBWAY_PATH = os.path.join(os.path.dirname(__file__), "sample", "subway.csv")  # import os — 파일 상단에 없으면 추가


def fetch_historical_weather(lat: float, lon: float, days: int = 90) -> pd.DataFrame:
    """Open-Meteo 아카이브 API로 과거 날씨 조회."""
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    url = (
        f"{ARCHIVE_URL}?latitude={lat}&longitude={lon}"
        f"&start_date={start}&end_date={end}"
        "&daily=temperature_2m_max,precipitation_sum,relative_humidity_2m_mean,wind_speed_10m_max"
    )
    response = requests.get(url)
    response.raise_for_status()
    daily = response.json()["daily"]
    return pd.DataFrame({
        "date": daily["time"],
        "temperature": daily["temperature_2m_max"],
        "precipitation": daily["precipitation_sum"],
        "humidity": daily["relative_humidity_2m_mean"],
        "wind_speed": daily["wind_speed_10m_max"],
    })


def fetch_subway_data(api_key: str | None = None) -> pd.DataFrame:
    """서울 지하철 이용객 수 조회. api_key 없으면 샘플 데이터 반환."""
    if api_key is None:
        return pd.read_csv(SAMPLE_SUBWAY_PATH, encoding='utf-8-sig')
    # TODO: 실제 서울 열린데이터광장 API 연동
    raise NotImplementedError("API 연동 미구현 — api_key=None으로 샘플 데이터 사용")
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_collector.py -v
```

Expected: `8 passed`

- [ ] **Step 5: 커밋**

```bash
git add data/collector.py tests/test_collector.py
git commit -m "feat: Open-Meteo 과거 날씨 및 지하철 샘플 폴백 구현"
```

---

## Task 6: analysis/anomaly.py — Isolation Forest 이상 탐지

**Files:**
- Create: `tests/test_anomaly.py`
- Create: `analysis/anomaly.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_anomaly.py`:

```python
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
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_anomaly.py -v
```

Expected: `ModuleNotFoundError: No module named 'analysis.anomaly'`

- [ ] **Step 3: anomaly.py 구현**

`analysis/anomaly.py`:

```python
import pandas as pd
from sklearn.ensemble import IsolationForest

FEATURES = ['temperature', 'precipitation', 'humidity', 'wind_speed']
CONTAMINATION = 0.05


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
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_anomaly.py -v
```

Expected: `6 passed`

- [ ] **Step 5: 커밋**

```bash
git add analysis/anomaly.py tests/test_anomaly.py
git commit -m "feat: Isolation Forest 이상 기후 탐지 구현"
```

---

## Task 7: analysis/correlation.py — 날씨 × 지하철 상관관계

**Files:**
- Create: `tests/test_correlation.py`
- Create: `analysis/correlation.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_correlation.py`:

```python
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
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_correlation.py -v
```

Expected: `ModuleNotFoundError: No module named 'analysis.correlation'`

- [ ] **Step 3: correlation.py 구현**

`analysis/correlation.py`:

```python
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

    x = merged['temperature'].values
    y = merged['passengers'].values

    pearson_r, _ = stats.pearsonr(x, y)
    spearman_r, _ = stats.spearmanr(x, y)

    return {
        'pearson': round(float(pearson_r), 4),
        'spearman': round(float(spearman_r), 4),
        'n_samples': len(merged),
    }
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_correlation.py -v
```

Expected: `5 passed`

- [ ] **Step 5: 커밋**

```bash
git add analysis/correlation.py tests/test_correlation.py
git commit -m "feat: 날씨 × 지하철 Pearson/Spearman 상관관계 분석 구현"
```

---

## Task 8: 전체 테스트 통과 확인

**Files:** 없음 (기존 테스트 전체 실행)

- [ ] **Step 1: 전체 테스트 실행**

```bash
pytest tests/ -v
```

Expected: `28 passed` (모든 테스트 통과)

- [ ] **Step 2: 실패 테스트 있으면 수정 후 재실행**

- [ ] **Step 3: 커밋**

```bash
git add -A
git commit -m "test: 전체 테스트 통과 확인"
```

---

## Task 9: assets/style.css — Eridian Horizon 테마

**Files:**
- Create: `assets/style.css`

테스트 없음 (CSS). 디자인 시스템 토큰 참조: 배경 `#0e0e11`, Primary `#ffe792`, Secondary `#5af8fb`, Tertiary `#cc97ff`.

- [ ] **Step 1: style.css 작성**

`assets/style.css`:

```css
/* Eridian Horizon — Streamlit 주입용 커스텀 CSS */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Manrope:wght@300;400;500;600;700&display=swap');

:root {
  --bg: #0e0e11;
  --surface: #19191d;
  --surface-high: #1f1f23;
  --primary: #ffe792;
  --secondary: #5af8fb;
  --tertiary: #cc97ff;
  --error: #ff7351;
  --on-surface: #f3f0f4;
  --outline: #48474b;
}

/* 전체 배경 */
.stApp { background-color: var(--bg) !important; }

/* 헤더 */
h1, h2, h3 {
  font-family: 'Space Grotesk', sans-serif !important;
  color: var(--primary) !important;
  text-shadow: 0 0 12px rgba(255, 231, 146, 0.4);
}

/* 본문 텍스트 */
p, span, div { font-family: 'Manrope', sans-serif !important; color: var(--on-surface); }

/* 메트릭 값 */
[data-testid="stMetricValue"] {
  color: var(--secondary) !important;
  font-family: 'Space Grotesk', sans-serif !important;
  text-shadow: 0 0 8px rgba(90, 248, 251, 0.4);
}

/* 카드 (glass panel) */
[data-testid="stMetricContainer"],
[data-testid="stVerticalBlock"] > div {
  background: rgba(31, 31, 35, 0.4) !important;
  backdrop-filter: blur(16px);
  border: 1px solid rgba(72, 71, 75, 0.2);
  border-radius: 8px;
}

/* 이상치 강조색 */
.anomaly-text { color: var(--tertiary); text-shadow: 0 0 8px rgba(204, 151, 255, 0.5); }

/* 사이드바 */
[data-testid="stSidebar"] { background-color: var(--surface) !important; }

/* 구분선 */
hr { border-color: var(--outline) !important; }
```

- [ ] **Step 2: 커밋**

```bash
git add assets/style.css
git commit -m "feat: Eridian Horizon 다크 테마 CSS 추가"
```

---

## Task 10: app.py — Streamlit 대시보드 조립

**Files:**
- Create: `app.py`

Streamlit app은 단위 테스트 대신 실행 확인으로 검증.

- [ ] **Step 1: app.py 작성**

`app.py`:

```python
import os
import streamlit as st
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv

from data.collector import fetch_current_weather, fetch_historical_weather, fetch_subway_data
from data.storage import save_csv, load_csv
from analysis.anomaly import detect_anomalies
from analysis.correlation import compute_correlation
from commentary.generator import generate_comment

load_dotenv()

# ── 좌표 상수 ────────────────────────────────────────────
MUNJEONG = {"name": "문정역 (서울)", "lat": 37.4946, "lon": 127.1237}
MONTEVIDEO = {"name": "몬테비데오 (우루과이)", "lat": -34.9011, "lon": -56.1645}

# ── CSS 주입 ─────────────────────────────────────────────
def inject_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def get_current(lat, lon):
    return fetch_current_weather(lat, lon)


@st.cache_data(ttl=3600)
def get_historical(lat, lon, days=90):
    return fetch_historical_weather(lat, lon, days)


@st.cache_data(ttl=3600)
def get_subway():
    api_key = os.getenv("SEOUL_API_KEY")
    return fetch_subway_data(api_key=api_key)


WEATHER_LABELS = {
    0: "맑음", 1: "대체로 맑음", 2: "구름 조금", 3: "흐림",
    45: "안개", 48: "안개",
    51: "이슬비", 53: "이슬비", 55: "이슬비",
    61: "비", 63: "비", 65: "강한 비",
    71: "눈", 73: "눈", 75: "강한 눈",
    80: "소나기", 81: "소나기", 82: "강한 소나기",
    95: "천둥번개",
}


def weather_label(code: int) -> str:
    return WEATHER_LABELS.get(code, f"날씨 코드 {code}")


def main():
    inject_css()
    st.title("🌌 기후탐정")
    st.caption("문정역(서울) ↔ 몬테비데오(우루과이) · 날씨 이상 탐지 대시보드")

    # ── 섹션 1: 양극단 날씨 비교 ──────────────────────────
    st.header("📍 지구 양 끝 날씨")
    col1, col2 = st.columns(2)

    with st.spinner("날씨 불러오는 중..."):
        mj = get_current(MUNJEONG["lat"], MUNJEONG["lon"])
        mv = get_current(MONTEVIDEO["lat"], MONTEVIDEO["lon"])

    with col1:
        st.subheader(MUNJEONG["name"])
        st.metric("기온", f"{mj['temperature']}°C")
        st.metric("강수량", f"{mj['precipitation']} mm")
        st.metric("습도", f"{mj['humidity']}%")
        st.metric("풍속", f"{mj['wind_speed']} m/s")
        st.info(weather_label(mj['weather_code']))
        st.markdown(f"> {generate_comment(mj['temperature'], mj['precipitation'], mj['weather_code'])}")

    with col2:
        st.subheader(MONTEVIDEO["name"])
        st.metric("기온", f"{mv['temperature']}°C")
        st.metric("강수량", f"{mv['precipitation']} mm")
        st.metric("습도", f"{mv['humidity']}%")
        st.metric("풍속", f"{mv['wind_speed']} m/s")
        st.info(weather_label(mv['weather_code']))

    st.divider()

    # ── 섹션 2: 이상 기후 탐지 ────────────────────────────
    st.header("🚨 이상 기후 탐지 (문정역 · 최근 90일)")

    with st.spinner("과거 데이터 분석 중..."):
        hist_df = get_historical(MUNJEONG["lat"], MUNJEONG["lon"], days=90)
        analyzed = detect_anomalies(hist_df)

    fig = px.scatter(
        analyzed, x='date', y='temperature',
        color=analyzed['is_anomaly'].map({True: '이상치', False: '정상'}),
        color_discrete_map={'이상치': '#cc97ff', '정상': '#5af8fb'},
        title='기온 시계열 — 이상치 탐지 결과',
        labels={'temperature': '기온 (°C)', 'date': '날짜'},
    )
    fig.update_layout(
        paper_bgcolor='#0e0e11', plot_bgcolor='#19191d',
        font_color='#f3f0f4', title_font_color='#ffe792',
    )
    st.plotly_chart(fig, use_container_width=True)

    anomaly_count = analyzed['is_anomaly'].sum()
    if anomaly_count > 0:
        st.warning(f"최근 90일간 이상 기후 {anomaly_count}건 탐지됨")
    else:
        st.success("최근 90일간 이상 기후 없음")

    st.divider()

    # ── 섹션 3: 날씨 × 지하철 상관관계 ────────────────────
    st.header("📊 기온 × 지하철 이용객 상관관계")

    with st.spinner("상관관계 분석 중..."):
        subway_df = get_subway()
        corr = compute_correlation(hist_df, subway_df)

    col3, col4, col5 = st.columns(3)
    col3.metric("Pearson 상관계수", f"{corr['pearson']:.4f}")
    col4.metric("Spearman 상관계수", f"{corr['spearman']:.4f}")
    col5.metric("분석 표본 수 (평일)", f"{corr['n_samples']}일")

    merged = pd.merge(hist_df, subway_df, on='date')
    fig2 = px.scatter(
        merged, x='temperature', y='passengers',
        trendline='ols',
        title='기온 vs 지하철 이용객 수 (평일)',
        labels={'temperature': '기온 (°C)', 'passengers': '이용객 수'},
        color_discrete_sequence=['#5af8fb'],
    )
    fig2.update_layout(
        paper_bgcolor='#0e0e11', plot_bgcolor='#19191d',
        font_color='#f3f0f4', title_font_color='#ffe792',
    )
    st.plotly_chart(fig2, use_container_width=True)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 로컬 실행 확인**

```bash
streamlit run app.py
```

Expected: 브라우저에서 대시보드 정상 렌더링

- [ ] **Step 3: 커밋**

```bash
git add app.py
git commit -m "feat: Streamlit 메인 대시보드 구현"
```

---

## Task 11: GitHub 원격 저장소 푸시

**Files:** 없음

- [ ] **Step 1: GitHub에서 새 저장소 생성**

GitHub.com에서 `weather-project` 이름으로 새 빈 저장소 생성 (README 없이).

- [ ] **Step 2: 원격 연결 및 푸시**

```bash
git remote add origin https://github.com/<your-username>/weather-project.git
git branch -M main
git push -u origin main
```

- [ ] **Step 3: 푸시 확인**

```bash
git log --oneline
```

Expected: 모든 커밋이 원격에 반영됨

---

## 최종 검증

```bash
# 전체 테스트
pytest tests/ -v

# 앱 실행
streamlit run app.py
```

모든 테스트 통과 + 브라우저에서 대시보드 정상 확인되면 완료.
