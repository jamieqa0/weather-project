# 기후탐정 내러티브 통합 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `app.py`의 UI 텍스트와 레이아웃을 수정해 "박보닥씨의 오늘 출근길" 스토리로 통합한다.

**Architecture:** `app.py`만 수정. 분석 로직(`analysis/`, `data/`, `commentary/`)은 건드리지 않는다. 섹션 1에서 `st.columns(2)` 구조를 단일 컬럼 + `st.expander`로 교체하고, 나머지 섹션은 헤더/캡션/결과 멘트 텍스트만 변경한다.

**Tech Stack:** Python, Streamlit

---

## 수정 파일

- Modify: `app.py` (render_hero, main 함수)
- Tests: 기존 `tests/` 그대로 유지 (UI 텍스트는 단위 테스트 대상 아님)

---

### Task 1: 히어로 텍스트 변경

**Files:**
- Modify: `app.py:58-78`

- [ ] **Step 1: 현재 render_hero 내용 확인**

```bash
python -m pytest tests/ -v
```
Expected: 27개 전부 PASS (기준선 확인)

- [ ] **Step 2: render_hero 수정**

`app.py`의 `render_hero()` 함수를 아래로 교체:

```python
def render_hero():
    st.markdown("""
    <div style="
        text-align: center;
        padding: 3rem 1rem 2rem;
        background: linear-gradient(180deg, rgba(255,231,146,0.06) 0%, transparent 100%);
        border-bottom: 1px solid rgba(72,71,75,0.3);
        margin-bottom: 2rem;
    ">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">🚇</div>
        <h1 style="font-size: 2.8rem; margin: 0; letter-spacing: -0.02em;">기후탐정</h1>
        <p style="color: #acaaae; font-size: 1.05rem; margin-top: 0.6rem;">
            박보닥씨의 오늘 출근길을 분석했어요
        </p>
        <div style="display: flex; justify-content: center; gap: 1.5rem; margin-top: 1.2rem; font-size: 0.85rem; color: #767579;">
            <span>📍 문정역, 서울 출근 날씨 리포트</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
```

- [ ] **Step 3: 테스트 실행**

```bash
python -m pytest tests/ -v
```
Expected: 27개 전부 PASS

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: 히어로 — 박보닥씨 출근 스토리 내러티브로 변경"
```

---

### Task 2: 섹션 1 — 단일 컬럼 + 몬테비데오 expander

**Files:**
- Modify: `app.py:126-151`

섹션 1에서 `st.columns(2)` 구조를 제거하고, 문정역을 단일 컬럼으로 크게 표시한 뒤, 몬테비데오는 `st.expander`로 축소한다.

- [ ] **Step 1: main() 내 섹션 1 블록 교체**

`app.py`에서 아래 블록을:
```python
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
```

아래로 교체:
```python
    # ── 섹션 1: 오늘 날씨 ─────────────────────────────────
    st.header("☀️ 박보닥씨, 오늘 문정역 날씨예요")

    with st.spinner("날씨 불러오는 중..."):
        mj = get_current(MUNJEONG["lat"], MUNJEONG["lon"])
        mv = get_current(MONTEVIDEO["lat"], MONTEVIDEO["lon"])

    st.subheader(MUNJEONG["name"])
    st.metric("기온", f"{mj['temperature']}°C")
    st.metric("강수량", f"{mj['precipitation']} mm")
    st.metric("습도", f"{mj['humidity']}%")
    st.metric("풍속", f"{mj['wind_speed']} m/s")
    st.info(weather_label(mj['weather_code']))
    st.markdown(f"> {generate_comment(mj['temperature'], mj['precipitation'], mj['weather_code'])}")

    with st.expander("🌏 지구 반대편은?"):
        st.caption(f"몬테비데오 (우루과이) · {mv['temperature']}°C · {weather_label(mv['weather_code'])}")
```

- [ ] **Step 2: 테스트 실행**

```bash
python -m pytest tests/ -v
```
Expected: 27개 전부 PASS

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: 섹션1 — 문정역 단일 컬럼, 몬테비데오 expander로 축소"
```

---

### Task 3: 섹션 2, 3 텍스트 변경

**Files:**
- Modify: `app.py:153-184`

- [ ] **Step 1: 섹션 2 텍스트 교체**

```python
    # ── 섹션 2: 이상 기후 탐지 ────────────────────────────
    st.header("🚨 근데 오늘 좀 이상한 날씨 아닌가요?")
    st.caption("박보닥씨의 최근 90일 출근길 날씨를 AI가 분석했어요. 보라색 점이 많을수록 요즘 날씨가 심상치 않아요.")
```

결과 멘트도 변경:
```python
    anomaly_count = analyzed['is_anomaly'].sum()
    if anomaly_count > 0:
        st.warning(f"최근 90일간 {anomaly_count}번의 이상한 날씨가 있었어요. 오늘 출근길, 조심하세요!")
    else:
        st.success("최근 90일간 날씨는 평온했어요. 오늘도 무난한 하루 될 것 같아요 😊")
```

- [ ] **Step 2: 섹션 3 텍스트 교체**

```python
    # ── 섹션 3: 날씨 × 지하철 상관관계 ────────────────────
    st.header("🚇 이 날씨에 지하철 얼마나 붐빌까요?")
    st.caption("날씨와 문정역 지하철 이용객 수를 분석했어요. 오늘 같은 날씨, 지하철이 더 붐빌까요?")
```

- [ ] **Step 3: 테스트 실행**

```bash
python -m pytest tests/ -v
```
Expected: 27개 전부 PASS

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: 섹션2·3 — 박보닥씨 말 거는 톤으로 헤더·캡션·결과 멘트 변경"
```
