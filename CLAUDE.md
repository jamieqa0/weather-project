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
data/collector.py  →  data/storage.py
                            ↓
     analysis/anomaly.py  +  analysis/correlation.py
                            ↓
          commentary/generator.py  +  commentary/interpretation.py
                            ↓
                         app.py  (Streamlit)
```

- `data/collector.py` — Open-Meteo API(날씨), 서울 열린데이터광장 API(지하철) 수집
- `analysis/` — 이상 탐지, 상관분석. 서로 독립적으로 동작
- `commentary/generator.py` — 규칙 기반 감성 멘트
- `commentary/interpretation.py` — 상관계수 한국어 해석, 시간 포맷, 알고리즘 정보 반환
- `app.py` — 위 모듈들을 조합해 Streamlit 대시보드 렌더링

## 주요 설계 결정

- **좌표**: 문정역 `(37.4946, 127.1237)`, 몬테비데오 `(-34.9011, -56.1645)`
- **이상 탐지**: `contamination=0.05`, `random_state=42` — 변경 시 `tests/test_anomaly.py`의 샘플 크기(200개) 기준도 함께 검토
- **상관분석**: 평일 데이터만 사용 (요일 효과 통제). `weather_df`와 `subway_df`의 `date` 컬럼이 같은 형식(`YYYY-MM-DD` 문자열)이어야 merge가 동작함
- **지하철 폴백**: `SEOUL_API_KEY` 없으면 `data/sample/subway.csv` 사용 (2023~2026 평일 데이터)
- **CSS 인코딩**: `assets/style.css`를 읽을 때 반드시 `encoding='utf-8'` 명시 (Windows cp949 충돌 방지)
- **Streamlit 캐싱**: 날씨/지하철 API는 `ttl=3600`, 1년 전 날씨는 `ttl=86400`

## 서울 지하철 API

서비스명: `CardSubwayStatsNew`. 날짜(YYYYMMDD) 필수, 날짜별로 최대 1000건 반환.

실제 응답 필드명:
- `USE_YMD` — 날짜 (YYYYMMDD)
- `SBWY_STNS_NM` — 역명 (문정역 = `"문정"`)
- `GTON_TNOPE` — 승차 인원
- `GTOFF_TNOPE` — 하차 인원

`fetch_subway_data`는 `ThreadPoolExecutor(max_workers=10)`으로 91일치를 병렬 조회. `_fetch_subway_day`가 단일 날짜 단위 조회의 단위 함수.

## 정적 파일 서빙

`.streamlit/config.toml`에 `enableStaticServing = true` 설정. `static/` 폴더의 파일이 `/app/static/` 경로로 서빙됨.

- **프로젝트 소개 페이지**: `static/about.html` (정식 소스, 루트의 `index.html`은 redirect만)
- 대시보드 푸터에서 `/app/static/index.html`로 링크

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
