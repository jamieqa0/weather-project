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

```
data/collector.py  (현재 + 과거 + 지하철 API)
        ↓
    analysis/anomaly.py (이상 탐지)
    analysis/correlation.py (기온·강수량 상관도)
        ↓
    commentary/interpretation.py (한국어 해석)
        ↓
    app.py  (Streamlit 대시보드)
    pages/about.py  (소개 페이지)
```

- `data/collector.py` — Open-Meteo API(`fetch_current_weather` 현재+오늘 일일, `fetch_historical_weather` 과거 365일, `fetch_weather_on_date` 특정 날짜), 서울 열린데이터광장 API(지하철 1년 데이터) 수집
- `analysis/anomaly.py` — Isolation Forest 이상 탐지 (7 features, contamination=0.05)
- `analysis/correlation.py` — Pearson + Spearman 상관계수 (기온, 강수량 vs 이용객 수, 평일만)
- `commentary/generator.py` — 기온·강수량·날씨 코드 기반 규칙적 감성 멘트 생성
- `commentary/interpretation.py` — 상관계수 한국어 해석, 시간 포맷, 알고리즘 정보 반환
- `app.py` — 위 모듈들을 조합해 Streamlit 대시보드 렌더링. 두괄식 UI(결과 → 설명 → 차트 → 상세). 기온/강수량 그래프 좌우 배치, 메트릭 1행 4카드
- `pages/about.py` — 소개 페이지. `static/about.html`을 읽어 `components.html()`로 렌더링. `timeline/builder.py`로 타임라인 HTML을 생성해 `<!-- TIMELINE_PLACEHOLDER -->`에 주입
- `timeline/builder.py` — `timeline/log.json`을 읽어 Claude 협업 타임라인 HTML 반환. Streamlit 의존성 없어 단독 테스트 가능

## 주요 설계 결정

- **좌표**: 문정역 `(37.4946, 127.1237)`, 몬테비데오 `(-34.9011, -56.1645)`
- **이상 탐지**: `contamination=0.05`, `random_state=42` — 변경 시 `tests/test_anomaly.py`의 샘플 크기(200개) 기준도 함께 검토. Isolation Forest는 7가지 기상 특성(`temp_max`, `temp_min`, `temperature`, `temp_range`, `precipitation`, `humidity`, `wind_speed`)을 사용
- **상관분석**: 기온과 강수량 모두 분석. 평일 데이터만 사용 (요일 효과 통제). `weather_df`와 `subway_df`의 `date` 컬럼이 같은 형식(`YYYY-MM-DD` 문자열)이어야 merge가 동작함. Streamlit `@st.cache_data` Arrow 직렬화로 인해 문자열 날짜가 datetime64로 변환될 수 있음 — 명시적 `.astype(str)` 변환 필수
- **지하철 API 범위**: `SEOUL_API_KEY` 있으면 366일(5~370일 전) 병렬 조회 (`max_workers=20`), 없으면 `data/sample/subway.csv` 사용 (2023~2026 평일 데이터)
- **날씨 API**: Open-Meteo 현재(`current`) + 일일(`daily`) 데이터. 일일 데이터에서 `temperature_2m_min`, `temperature_2m_mean` 함께 조회
- **CSS 인코딩**: `assets/style.css`를 읽을 때 반드시 `encoding='utf-8'` 명시 (Windows cp949 충돌 방지)
- **Streamlit 캐싱**: 날씨/지하철 API는 `ttl=3600`, 1년 전 날씨는 `ttl=86400`

## 서울 지하철 API

서비스명: `CardSubwayStatsNew`. 날짜(YYYYMMDD) 필수, 날짜별로 최대 1000건 반환.

실제 응답 필드명:
- `USE_YMD` — 날짜 (YYYYMMDD)
- `SBWY_STNS_NM` — 역명 (문정역 = `"문정"`)
- `GTON_TNOPE` — 승차 인원
- `GTOFF_TNOPE` — 하차 인원

`fetch_subway_data`는 `ThreadPoolExecutor(max_workers=20)`으로 **366일치**(5~370일 전) 병렬 조회하여 약 1년 데이터 수집. API 응답 지연(3~7일)을 고려해 5일부터 시작. `_fetch_subway_day`가 단일 날짜 단위 조회의 단위 함수. API 실패 시 sample CSV로 자동 폴백.

## 정적 파일 서빙

`.streamlit/config.toml`에 `enableStaticServing = true` 설정. `static/` 폴더의 파일이 `/app/static/` 경로로 서빙됨.

- **프로젝트 소개 페이지**: `pages/about.py`로 렌더링 (`/about`). `static/about.html`이 실제 소스, 루트의 `index.html`은 redirect만
- 대시보드 푸터에서 `/about`, `/about#timeline`으로 링크
- `static/` 직접 접근(`/app/static/about.html`)은 MIME 타입 문제로 사용하지 않음

## 환경 변수

`.env` 파일:
```
SEOUL_API_KEY=...  # 없으면 샘플 데이터로 자동 폴백
```

## 문서

- `docs/superpowers/specs/` — 설계 문서
- `docs/superpowers/plans/` — 구현 계획
- `docs/review-improvements.md` — 코드 리뷰 반영 내역
- `timeline/log.json` — 프로젝트 마일스톤 기록
