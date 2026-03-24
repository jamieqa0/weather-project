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
- 앱 logs 확인: "Manage app" → Logs 탭

## 테스트 (Test-Driven Development)

### 커버리지 상태
- **현재**: 100% (100 테스트, statement 전부 커버)
- **상세 계획**: `docs/test-improvements.md` 참고

### 주의사항
- **Pearson 경고**: `test_strong_positive_correlation`에서 강수량 상수 시 경고 발생 — 커버리지에 영향 없음
- **새 코드 추가 시**: 테스트 커버리지 100% 유지해야 함

## 아키텍처

```
data/collector.py  (현재 + 과거 + 지하철 API)
        ↓
    analysis/anomaly.py       analysis/correlation.py
    (이상 탐지)                (기온·강수량 상관도)
        ↓
    commentary/generator.py   commentary/interpretation.py
    (감성 멘트)                (상관계수 해석 · 시간 포맷)
        ↓
    app.py  (Streamlit 대시보드)
    pages/about.py  (소개 페이지 → static/about.html 렌더링)
```

- `data/collector.py` — Open-Meteo API(`fetch_current_weather` 현재+오늘 일일, `fetch_historical_weather` 과거 365일, `fetch_weather_on_date` 특정 날짜), 서울 열린데이터광장 API(지하철 1년 데이터) 수집. 모든 `requests.get()` 호출에 `verify=False` 적용 (회사 네트워크 SSL 프록시 대응)
- `data/storage.py` — CSV 저장/로드 유틸리티. 현재 메인 파이프라인에서 사용되지 않음
- `analysis/anomaly.py` — Isolation Forest 이상 탐지 (7 features, contamination=0.05)
- `analysis/correlation.py` — Pearson + Spearman 상관계수 (기온, 강수량 vs 이용객 수, 평일만)
- `commentary/generator.py` — 기온·강수량·날씨 코드 기반 규칙적 감성 멘트 생성
- `commentary/interpretation.py` — 상관계수 한국어 해석, 시간 포맷(`format_last_updated` KST 기준, `format_montevideo_time` UTC-3 기준), 알고리즘 정보 반환
- `app.py` — 위 모듈들을 조합해 Streamlit 대시보드 렌더링. 두괄식 UI(결과 → 설명 → 차트 → 상세).
  - `render_hero()` — 히어로 섹션 전체를 `components.html()`로 렌더링. sunny(code 0) Lottie **2개** 인스턴스(우측 엣지, opacity 0.20/0.10). 모바일(≤480px)에서 완전 숨김
  - `render_weather_card_component(wcode, mj, comment)` — 날씨 카드를 `components.html()` iframe으로 렌더링. CSS 클래스 기반 레이아웃 (`.card`, `.row`, `.icon`, `.temps`). 모바일에서 아이콘 72px, `flex-wrap:nowrap`, 모바일에서 Lottie 완전 숨김. Lottie 배경은 **우측 엣지에만** 배치(right:4%/16%, opacity 0.18/0.10) — stats 텍스트 침범 방지
  - `render_lottie_in_expander(code, line1, line2)` — expander 내부에 Lottie 배경 + 텍스트 오버레이 렌더링
  - `_lottie_lib()` — `static/lottie.min.js` 내용 캐시 후 HTML에 인라인 삽입
  - `_lottie_json(code)` — `static/lottie/{name}.json` 읽어 문자열 반환
  - `weather_animation_html(code)` — CSS 기반 배경 애니메이션 (fallback 용도로 유지)
- `pages/about.py` — `static/about.html`을 읽어 `components.html(height=9500, scrolling=True)`로 렌더링
- `static/about.html` — 소개 페이지 전체 HTML. 플로팅 TOC JS는 `scrolling=True` iframe 자체 스크롤 감지(`selfScrolling` 변수) 후 `window.scrollTo` / 부모 컨테이너 스크롤 분기 처리. 아키텍처 다이어그램은 `arch-fork-pipes`(두 개의 `.pipe` div를 flex로 배치) + `arch-row`(flex 노드들) 쌍으로 분기 표현 — 새 분기 추가 시 이 패턴 유지, `margin-left` 임시 배치 금지
- `timeline/builder.py` — `timeline/log.json`을 읽어 Claude 협업 타임라인 HTML 반환

## 주요 설계 결정

- **좌표**: 문정역 `(37.4946, 127.1237)`, 몬테비데오 `(-34.9011, -56.1645)`
- **이상 탐지**: `contamination=0.05`, `random_state=42` — 변경 시 `tests/test_anomaly.py`의 샘플 크기(200개) 기준도 함께 검토. 7가지 기상 특성(`temp_max`, `temp_min`, `temperature`, `temp_range`, `precipitation`, `humidity`, `wind_speed`) 사용
- **상관분석**: 평일 데이터만 사용 (요일 효과 통제). `weather_df`와 `subway_df`의 `date` 컬럼이 `YYYY-MM-DD` 문자열이어야 merge 동작. Streamlit `@st.cache_data` Arrow 직렬화로 datetime64 변환 가능 — 명시적 `.astype(str)` 변환 필수
- **지하철 API 범위**: `SEOUL_API_KEY` 있으면 366일(5~370일 전) 병렬 조회 (`max_workers=20`), 없으면 `data/sample/subway.csv` 폴백
- **날씨 API**: Open-Meteo daily 배열이 비어있거나 키가 없으면 current 값으로 기본값 설정
- **SSL 인증서**: `data/collector.py`의 모든 `requests.get()`에 `verify=False` + `urllib3.disable_warnings()` 적용 — 회사 네트워크 자체 서명 인증서 대응
- **CSS 인코딩**: `assets/style.css` 읽을 때 반드시 `encoding='utf-8'` 명시 (Windows cp949 충돌 방지)
- **CSS 주입 구조**: 툴바 숨김·툴팁 다크 스타일·모바일 헤더 줄바꿈은 `inject_css()` 내부 `st.markdown` 블록에 직접 주입. 나머지는 `assets/style.css`. `assets/style.css`에는 `@media (max-width: 640px)` 모바일 미디어 쿼리 포함
- **Lottie 애니메이션**: `st.markdown()`은 `<script>` 제거 → 반드시 `components.html()`로 렌더링. `lottie.min.js` 인라인 삽입 필수 (`<script src=...>` 방식은 iframe 내부 경로 실패). JSON도 Python에서 읽어 `animationData`로 인라인. 날씨 JSON 7종: `sunny`, `cloudy`, `overcast`, `rain`, `snow`, `fog`, `thunder`
- **Lottie JSON 소스**: `E:/study/refer/`의 고품질 파일을 `static/lottie/`에 복사해서 사용. **`generate.py` 실행 시 파일 덮어쓰이므로 주의**. `sunny.json`은 별도 교체 이력 있음 (Happy SUN 적용)
- **Plotly Y축 한글**: 모바일에서 Y축 레이블이 글자 단위로 분리되는 현상 → 차트 제목에 축 정보 포함 후 `yaxis_title=None` 사용
- **Plotly 차트 고정**: 모바일 터치 시 차트가 움직이는 문제 → 모든 `plotly_chart` 호출에 `config={'staticPlot': True}` 적용
- **상관분석 차트**: Pearson 차트(실제값 X/Y) + Spearman 차트(순위 X/Y) 두 세트로 구성. 차트용 `merged` 데이터는 반드시 평일 필터링 후 사용 (`dt.dayofweek < 5`). 오늘 값의 순위는 `(merged['col'] <= today_val).sum()`으로 계산
- **모바일 타이틀 줄바꿈**: `.sec-title .mb { display: none; }` — 모바일 포함 전 구간 숨김 처리. 줄바꿈 필요 시 이 CSS 수정
- **모바일 한글 줄바꿈**: 카드 내 텍스트에 `word-break: keep-all` 적용 — 조사/어절 단위로 자연스럽게 줄바꿈. Streamlit expander 레이블은 CSS 적용 불가이므로 텍스트 자체를 짧게 유지
- **상관분석 카드**: `.subway-card` CSS 클래스로 관리. 모바일(≤480px)에서 이모지 2.2rem, 텍스트 축소
- **git push**: 사용자가 직접 함. Claude는 코드 수정만 하고 push하지 않음
- **상관계수 비선형 안내**: 제거됨 (사용자 요청으로 삭제)
- **about.html 모달**: `selfScrolling=true` 환경에서 모달 위치 계산 시 `getContainer()` 호출 금지 — `window.scrollY` / `window.innerHeight` 사용. 모달 핸들러 조건 반드시 `!selfScrolling` 분기 포함
- **Streamlit 테마**: `.streamlit/config.toml` 다크 모드. `primaryColor = "#5af8fb"`, `backgroundColor = "#0e0e11"`, `secondaryBackgroundColor = "#19191d"`
- **디자인 시스템**: Eridian Horizon — `#ffe792`(골드), `#5af8fb`(시안), `#cc97ff`(보라), `#ff7351`(오렌지-레드), 배경 `#0e0e11`. 새 UI 요소 추가 시 이 팔레트 준수
- **타임존**: `format_last_updated()` KST(UTC+9), `format_montevideo_time()` UYT(UTC-3)
- **Streamlit 캐싱**: 날씨/지하철 API `ttl=3600`, 1년 전 날씨 `ttl=86400`
- **about.html 플로팅 TOC**: `components.html(scrolling=True)` iframe에서 스크롤이 `window` 자체에서 발생. JS의 `selfScrolling` 변수로 감지 후 분기 — 자체 스크롤 시 `window.scrollTo` + `el.offsetTop + iframeOffset` 계산 사용

## 서울 지하철 API

서비스명: `CardSubwayStatsNew`. 날짜(YYYYMMDD) 필수.

응답 필드: `USE_YMD`(날짜), `SBWY_STNS_NM`(역명, 문정역=`"문정"`), `GTON_TNOPE`(승차), `GTOFF_TNOPE`(하차)

`fetch_subway_data` — `ThreadPoolExecutor(max_workers=20)`으로 366일치 병렬 조회. API 응답 지연(3~7일) 고려해 5일 전부터 시작. API 실패 시 sample CSV로 자동 폴백.

## 정적 파일 서빙

`.streamlit/config.toml`에 `enableStaticServing = true`. `static/` → `/app/static/` 경로 서빙.

- **소개 페이지**: `pages/about.py` (`/about`). `static/about.html`이 실제 소스
- `static/lottie/` — 날씨별 Lottie JSON 7종
- `static/lottie.min.js` — lottie-web 5.12.2 로컬 번들

## 환경 변수

**로컬** (`.env`): `SEOUL_API_KEY=...` (없으면 샘플 데이터 폴백)

**Streamlit Cloud**: Settings → Secrets → `SEOUL_API_KEY = "..."` TOML 형식 입력

## 문제 해결

**SSLError: certificate verify failed**
- **원인**: 회사 네트워크/VPN의 자체 서명 인증서
- **해결**: `data/collector.py`에 `verify=False` + `urllib3.disable_warnings()` 적용됨

**날씨 카드 모바일에서 온도 텍스트가 이미지에 가림**
- **원인**: `height=165` 고정 iframe에서 flex wrap 시 콘텐츠 클리핑
- **해결**: CSS 클래스 기반 레이아웃으로 변경. 모바일에서 아이콘 72px, `flex-wrap:nowrap` 유지

**소개 페이지 플로팅 TOC 클릭 시 이상한 위치로 이동**
- **원인**: `scrolling=True` iframe에서 `getBoundingClientRect()`가 iframe 내부 좌표 반환 → 부모 좌표와 혼합 계산 시 오차
- **해결**: `el.offsetTop + iframeOffsetInContainer()`로 좌표 계산. `selfScrolling` 감지로 분기

**지하철/날씨 데이터 merge 안 됨**
- **원인**: Arrow 직렬화 후 date 컬럼이 datetime64로 변환
- **해결**: `get_subway()` 및 상관분석 전에 `.astype(str)` 명시적 변환

**Lottie 애니메이션 미동작**
- **원인**: `st.markdown()`이 `<script>` 제거. `<script src=...>`는 iframe 내부 경로 실패
- **해결**: `components.html()`로 전체 렌더링, JS 라이브러리 인라인 삽입

**Streamlit에서 "KeyError: temperature_max"**
- **원인**: Open-Meteo daily 배열이 비어있을 때
- **해결**: `fetch_current_weather`에서 current 값으로 기본값 설정됨

## 문서

- `docs/test-improvements.md` — 테스트 개선 계획 및 진행 상황
- `docs/superpowers/specs/` — 설계 문서
- `docs/superpowers/plans/` — 구현 계획
- `docs/review-improvements.md` — 코드 리뷰 반영 내역
- `timeline/log.json` — 프로젝트 마일스톤 기록
