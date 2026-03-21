# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# 앱 실행
python -m streamlit run app.py

# 전체 테스트
python -m pytest tests/ -v

# 단일 테스트
python -m pytest tests/test_anomaly.py::test_detects_obvious_outliers -v

# 타임라인 마일스톤 기록
python log.py "메시지" --emoji 🎉 --category dev
python log.py --list
```

## 아키텍처

데이터는 `data/collector.py`에서 Open-Meteo API로 수집되어 `data/storage.py`로 CSV 저장된다. 분석 모듈 두 개(`analysis/anomaly.py`, `analysis/correlation.py`)가 독립적으로 동작하며, `commentary/generator.py`가 규칙 기반 멘트를 생성한다. `app.py`가 이 모듈들을 조합해 Streamlit 대시보드를 렌더링한다.

```
data/collector.py  →  data/storage.py
                          ↓
          analysis/anomaly.py  +  analysis/correlation.py
                          ↓
               commentary/generator.py
                          ↓
                       app.py
```

## 주요 설계 결정

- **좌표**: 문정역 `(37.4946, 127.1237)`, 몬테비데오 `(-34.9011, -56.1645)`
- **이상 탐지**: `contamination=0.05`, `random_state=42` — 변경 시 `tests/test_anomaly.py`의 샘플 크기(200개) 기준도 함께 검토
- **상관분석**: 평일 데이터만 사용 (요일 효과 통제). `weather_df`와 `subway_df`의 `date` 컬럼이 같은 형식(`YYYY-MM-DD` 문자열)이어야 merge가 동작함
- **지하철 폴백**: `SEOUL_API_KEY` 없으면 `data/sample/subway.csv` 사용 (2023~2026 평일 데이터)
- **CSS 인코딩**: `assets/style.css`를 읽을 때 반드시 `encoding='utf-8'` 명시 (Windows cp949 충돌 방지)
- **Streamlit 캐싱**: API 호출 및 모델 학습은 `@st.cache_data(ttl=3600)` 적용

## 환경 변수

`.env` 파일 (`.env.example` 참고):
```
SEOUL_API_KEY=your_key_here  # 없으면 샘플 데이터로 자동 폴백
```

## 문서

- `docs/superpowers/specs/` — 설계 문서
- `docs/superpowers/plans/` — 구현 계획 (TDD 태스크 11개)
- `timeline/log.json` — 프로젝트 마일스톤 기록
- `index.html` — 기술 소개 웹페이지 (Eridian Horizon 테마)
