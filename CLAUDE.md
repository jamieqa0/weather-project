# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# 앱 실행 (로컬)
python -m streamlit run app.py

# 전체 테스트 + 커버리지
python -m pytest tests/ -v --cov=. --cov-report=term-missing

# 단일 테스트
python -m pytest tests/test_anomaly.py::test_detects_obvious_outliers -v

# 특정 모듈 커버리지만 확인
python -m pytest tests/ --cov=data.collector --cov-report=term-missing

# 타임라인 마일스톤 기록
python log.py "메시지" --emoji 🎉 --category dev
python log.py --list
```

**배포 (Streamlit Cloud)**:
- Secrets 설정 후 `git push` → 자동 배포
- 배포 전 테스트: 로컬에서 `python -m streamlit run app.py` 실행 후 정상 작동 확인
- 앱 logs 확인: "Manage app" → Logs 탭

## 테스트 (Test-Driven Development)

### 커버리지 상태
- **현재**: 100% (92 테스트, 142개 statement 전부 커버)
- **목표**: 100% 달성 ✅
- **상세 계획**: `docs/test-improvements.md` 참고

### 테스트 구조
```
Phase 1: commentary/generator.py (81% → 100%) ✅
  - 9개 테스트 추가: 비(61,63,65,80,81,82), 눈(73,75), 온도 범위(0~5°C)

Phase 2: analysis/correlation.py (94% → 100%) ✅
  - 4개 테스트 추가: 샘플 부족, 겹치지 않는 날짜

Phase 3: data/collector.py (95% → 100%) ✅
  - 4개 테스트 추가: API 타임아웃, JSON 파싱 에러, 키 누락, 빈 daily 배열

Phase 4: 데이터 정합성 검증 ✅
  - 5개 테스트 추가: 타입 검증, 범위 검증, 날짜 형식, NaN 없음, merge 일관성
```

### 주의사항
- **Pearson 경고**: `test_strong_positive_correlation`에서 강수량 상수 시 경고 발생 — 커버리지에 영향 없음
- **새 코드 추가 시**: 테스트 커버리지 100% 유지해야 함 (미커버 라인 생기면 프로세스에 따라 테스트 추가)

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
- `commentary/interpretation.py` — 상관계수 한국어 해석, 시간 포맷(`format_last_updated` KST 기준, `format_montevideo_time` UTC-3 기준), 알고리즘 정보 반환
- `app.py` — 위 모듈들을 조합해 Streamlit 대시보드 렌더링. 두괄식 UI(결과 → 설명 → 차트 → 상세). 기온/강수량 그래프 좌우 배치, 메트릭 1행 4카드
  - `render_hero()` — 히어로 섹션 전체를 `components.html()`로 렌더링. sunny(code 0) Lottie 4개 인스턴스를 좌우에 크기/opacity 불규칙하게 배치. `st.markdown()` 사용 불가 (`<script>` 제거됨)
  - `render_weather_card_component(wcode, mj, comment)` — 날씨 카드 전체를 `components.html()` iframe으로 렌더링. Lottie 3개 인스턴스를 카드 오른쪽 영역에 절대 위치로 배치 (텍스트 비겹침). comment 텍스트는 `#5af8fb` 시안, font-weight 600
  - `render_lottie_in_expander(code, line1, line2)` — expander 내부에 Lottie 배경 + 텍스트 오버레이를 한 블록으로 렌더링. 텍스트를 파라미터로 받아 animation 위에 겹쳐 표시 (이상 기후 expander에는 미사용)
  - `_lottie_lib()` — `static/lottie.min.js` 파일 내용을 읽어 캐시 (`@st.cache_data`). HTML에 `<script>` 인라인으로 삽입
  - `_lottie_json(code)` — `static/lottie/{name}.json` 읽어 문자열 반환
  - `weather_animation_html(code)` — CSS 기반 배경 애니메이션 (fallback 용도로 유지)
- `pages/about.py` — 소개 페이지. `static/about.html`을 읽어 `components.html()`로 렌더링. `timeline/builder.py`로 타임라인 HTML을 생성해 `<!-- TIMELINE_PLACEHOLDER -->`에 주입
- `timeline/builder.py` — `timeline/log.json`을 읽어 Claude 협업 타임라인 HTML 반환. Streamlit 의존성 없어 단독 테스트 가능
- `apply_ui.py` — `static/about.html`에 CSS/JS 패치를 직접 적용하는 유틸리티 스크립트 (일회성 사용)

## 주요 설계 결정

- **좌표**: 문정역 `(37.4946, 127.1237)`, 몬테비데오 `(-34.9011, -56.1645)`
- **이상 탐지**: `contamination=0.05`, `random_state=42` — 변경 시 `tests/test_anomaly.py`의 샘플 크기(200개) 기준도 함께 검토. Isolation Forest는 7가지 기상 특성(`temp_max`, `temp_min`, `temperature`, `temp_range`, `precipitation`, `humidity`, `wind_speed`)을 사용
- **상관분석**: 기온과 강수량 모두 분석. 평일 데이터만 사용 (요일 효과 통제). `weather_df`와 `subway_df`의 `date` 컬럼이 같은 형식(`YYYY-MM-DD` 문자열)이어야 merge가 동작함. Streamlit `@st.cache_data` Arrow 직렬화로 인해 문자열 날짜가 datetime64로 변환될 수 있음 — 명시적 `.astype(str)` 변환 필수
- **지하철 API 범위**: `SEOUL_API_KEY` 있으면 366일(5~370일 전) 병렬 조회 (`max_workers=20`), 없으면 `data/sample/subway.csv` 사용 (2023~2026 평일 데이터)
- **날씨 API**: Open-Meteo 현재(`current`) + 일일(`daily`) 데이터. 일일 데이터에서 `temperature_2m_min`, `temperature_2m_mean` 함께 조회. daily 배열이 비어있거나 키가 없으면 current 값으로 기본값 설정 (Streamlit Cloud 호환성)
- **CSS 인코딩**: `assets/style.css`를 읽을 때 반드시 `encoding='utf-8'` 명시 (Windows cp949 충돌 방지)
- **CSS 주입 구조**: 툴바 숨김(`stToolbar`, `stAppToolbar`, `stHeader`)과 툴팁 다크 스타일은 `inject_css()` 내부 `st.markdown` 블록에 직접 주입. 나머지 스타일은 `assets/style.css`. Streamlit DOM 선택자가 버전마다 달라질 수 있으므로 두 곳 중 `inject_css()` 블록이 우선 적용됨
- **Lottie 애니메이션**: `st.markdown()`은 `<script>` 태그를 제거하므로 `components.html()`로 전체 렌더링. lottie-web 라이브러리(`static/lottie.min.js`)는 `_lottie_lib()`로 읽어 HTML에 직접 인라인 삽입 — `<script src=...>` 방식은 iframe 내부에서 경로 로딩이 실패하므로 사용 금지. JSON도 Python에서 읽어 `animationData`로 인라인 삽입. 7가지 날씨 JSON: `sunny`, `cloudy`, `overcast`, `rain`, `snow`, `fog`, `thunder`
- **Lottie JSON 소스**: `E:/study/refer/`의 고품질 파일을 `static/lottie/`에 복사해서 사용. 매핑: `sunny.json`←`sunny.json`, `cloudy/overcast`←`Cloud.json`, `rain/thunder`←`Rain drop.json`, `snow`←`Snowing.json`, `fog`←`Fog  Smoke.json`. **`generate.py` 실행 시 고품질 파일이 덮어쓰여지므로 실행 후 refer 파일을 다시 복사해야 함**
- **Streamlit 테마**: `.streamlit/config.toml`에 `[theme]` 설정으로 다크 모드 전역 적용 — dataframe, 차트 등 Streamlit 기본 컴포넌트도 다크로 렌더링됨. `primaryColor = "#5af8fb"`, `backgroundColor = "#0e0e11"`, `secondaryBackgroundColor = "#19191d"`
- **디자인 시스템**: Eridian Horizon — 주요 색상 `#ffe792`(골드), `#5af8fb`(시안), `#cc97ff`(보라), `#ff7351`(오렌지-레드), 배경 `#0e0e11`. 새 UI 요소 추가 시 이 팔레트 준수
- **타임존**: `format_last_updated()`는 KST(UTC+9), `format_montevideo_time()`은 UYT(UTC-3) 기준. 파라미터 없이 호출하면 각 타임존의 현재 시각 반환
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
- `static/lottie/` — 날씨별 Lottie JSON 7종. 소스는 `E:/study/refer/` (고품질 수동 다운로드). `generate.py`는 fallback용이며 실행 시 파일이 덮어쓰이므로 주의
- `static/lottie.min.js` — lottie-web 5.12.2 로컬 번들 (CDN 없이 사용)

## 환경 변수

**로컬 개발** (`.env` 파일):
```
SEOUL_API_KEY=...  # 없으면 샘플 데이터로 자동 폴백
```

**Streamlit Cloud 배포**:
1. 앱 우측 하단 "Manage app" 클릭
2. Settings → Secrets 탭
3. TOML 형식으로 입력:
```toml
SEOUL_API_KEY = "YOUR_API_KEY"
```
저장 후 앱 자동 재시작됨.

## 의존성

코어 패키지 (자동 설치):
```
streamlit         # 대시보드
pandas            # 데이터프레임
numpy             # 수치 계산
scipy             # 통계 (pearsonr, spearmanr)
scikit-learn      # 이상 탐지 (IsolationForest)
plotly            # 상호작용 차트
requests          # HTTP API 호출
python-dotenv     # .env 파일 로드
```

테스트 & 개발:
```
pytest            # 테스트 실행
pytest-cov        # 커버리지 분석
```

## 문제 해결

**문제**: 지하철 데이터가 91일만 나옴
- **원인**: fetch_subway_data의 API 범위가 짧음
- **해결**: `range(5, 371)`로 366일 조회 (max_workers=20 병렬화)

**문제**: Streamlit에서 "KeyError: temperature_max"
- **원인**: Open-Meteo daily 배열이 비어있을 때
- **해결**: fetch_current_weather에서 current 값으로 기본값 설정

**문제**: 지하철/날씨 데이터 merge가 안 됨
- **원인**: Arrow 직렬화 후 date 컬럼이 string → datetime64로 변환됨
- **해결**: get_subway()와 상관분석 전에 `.astype(str)` 명시적 변환

**문제**: 테스트 중 "ConstantInputWarning" 발생
- **원인**: test_strong_positive_correlation에서 precipitation이 상수
- **영향**: 경고일 뿐 커버리지/기능에 영향 없음

**문제**: 날씨 카드에 Lottie 애니메이션이 표시 안 됨 (경고 아이콘)
- **원인**: `st.markdown()`은 `<script>` 제거 → `lottie-player` 웹 컴포넌트 미등록. CDN URL 로딩 실패
- **해결**: `render_weather_card_component()`로 카드 전체를 `components.html()` iframe 내 렌더링, `lottie-web`으로 JSON 인라인 삽입

**문제**: `components.html()` 안에서 Lottie 애니메이션 미동작
- **원인**: `<script src="/app/static/lottie.min.js">` 방식은 iframe 내부에서 경로 해석 실패
- **해결**: `_lottie_lib()`로 파일 내용을 읽어 `<script>` 태그에 직접 인라인 삽입

## UI 구조

**두괄식 패턴** (결과 우선):
1. 메트릭 & 요약 (상단)
2. 해석 텍스트
3. 차트 & 시각화
4. 상세 정보

이를 통해 사용자가 핵심 정보를 먼저 파악할 수 있음.

## 문서

- `docs/test-improvements.md` — 테스트 개선 계획 및 진행 상황 (Phase 1-5, 커버리지 분석)
- `docs/superpowers/specs/` — 설계 문서
- `docs/superpowers/plans/` — 구현 계획
- `docs/review-improvements.md` — 코드 리뷰 반영 내역
- `timeline/log.json` — 프로젝트 마일스톤 기록
