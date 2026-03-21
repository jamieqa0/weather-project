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
        with open(css_path, encoding='utf-8') as f:
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
    pearson_str = f"{corr['pearson']:.4f}" if corr['pearson'] is not None else "데이터 없음"
    spearman_str = f"{corr['spearman']:.4f}" if corr['spearman'] is not None else "데이터 없음"
    col3.metric("Pearson 상관계수", pearson_str)
    col4.metric("Spearman 상관계수", spearman_str)
    col5.metric("분석 표본 수 (평일)", f"{corr['n_samples']}일")

    merged = pd.merge(hist_df, subway_df, on='date')
    if len(merged) >= 2:
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
    else:
        st.info("날씨 데이터와 지하철 데이터의 날짜가 겹치지 않아 차트를 표시할 수 없습니다.")


if __name__ == "__main__":
    main()
