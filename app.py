import os
from datetime import datetime, date, timedelta
import streamlit as st
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv

from data.collector import fetch_current_weather, fetch_historical_weather, fetch_subway_data, fetch_weather_on_date
from analysis.anomaly import detect_anomalies
from analysis.correlation import compute_correlation
from commentary.generator import generate_comment
from commentary.interpretation import interpret_correlation, format_last_updated, get_anomaly_algorithm_info

load_dotenv()

# ── 좌표 상수 ────────────────────────────────────────────
MUNJEONG = {"name": "문정역 (서울)", "lat": 37.4946, "lon": 127.1237}
MONTEVIDEO = {"name": "몬테비데오 (우루과이)", "lat": -34.9011, "lon": -56.1645}

# ── CSS 주입 ─────────────────────────────────────────────
def inject_css():
    # pages/ 폴더로 인해 자동 생성되는 사이드 네비게이션 숨기기
    st.markdown("""
    <style>
      [data-testid="stSidebar"] { display: none; }
      [data-testid="collapsedControl"] { display: none; }
    </style>
    """, unsafe_allow_html=True)
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


@st.cache_data(ttl=86400)
def get_year_ago(lat, lon):
    target = date.today() - timedelta(days=365)
    return fetch_weather_on_date(lat, lon, target)


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


def render_footer():
    st.markdown("""
    <div style="
        text-align: center;
        padding: 2rem 1rem;
        margin-top: 3rem;
        border-top: 1px solid rgba(72,71,75,0.3);
        color: #767579;
        font-size: 0.82rem;
        line-height: 1.8;
    ">
        <p style="margin: 0 0 0.8rem; font-size: 0.95rem; color: #acaaae;">기후탐정 · <span style="color:#cc97ff;">Job-Stealer</span> 사내 스터디</p>
        <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; margin-bottom: 0.6rem;">
            <a href="https://open-meteo.com" target="_blank"
               style="color: #5af8fb; text-decoration: none;">
                🌤 Open-Meteo API
            </a>
            <a href="https://data.seoul.go.kr" target="_blank"
               style="color: #5af8fb; text-decoration: none;">
                🚇 서울 열린데이터광장
            </a>
            <a href="https://stitch.withgoogle.com/projects/10551746938995651396" target="_blank"
               style="color: #5af8fb; text-decoration: none;">
                🎨 디자인 시스템 (Google Stitch)
            </a>
            <a href="https://github.com/jamieqa0/weather-project" target="_blank"
               style="color: #5af8fb; text-decoration: none;">
                💻 GitHub
            </a>
            <a href="/about" target="_blank"
               style="color: #ffe792; text-decoration: none;">
                🌌 프로젝트 소개 페이지
            </a>
            <a href="/about#timeline" target="_blank"
               style="color: #5af8fb; text-decoration: none;">
                🤖 Claude 협업 타임라인
            </a>
        </div>
        <p style="margin: 0; color: #48474b; font-size: 0.75rem;">
            Built with Python · Streamlit · Plotly · scikit-learn
        </p>
    </div>
    """, unsafe_allow_html=True)


def main():
    st.set_page_config(layout="wide", page_title="기후탐정", page_icon="🚇")
    inject_css()
    render_hero()

    # ── 섹션 1: 오늘 날씨 ─────────────────────────────────
    st.header("☀️ 박보닥씨, 오늘 문정역 날씨예요")
    st.caption(f"🕐 {format_last_updated(datetime.now())}")

    if os.getenv("SEOUL_API_KEY") is None:
        st.toast("💡 안내: 지하철 혼잡도는 과거 샘플 데이터를 기준으로 보여드려요.")

    with st.spinner("날씨 불러오는 중..."):
        mj = get_current(MUNJEONG["lat"], MUNJEONG["lon"])
        mv = get_current(MONTEVIDEO["lat"], MONTEVIDEO["lon"])
        ly = get_year_ago(MUNJEONG["lat"], MUNJEONG["lon"])

    _ya = date.today() - timedelta(days=365)
    year_ago_date = f"{_ya.year}년 {_ya.month}월 {_ya.day}일"

    st.subheader(MUNJEONG["name"])
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("기온", f"{mj['temperature']}°C",
                delta=f"{mj['temperature'] - ly['temperature']:+.1f}°C")
    col2.metric("강수량", f"{mj['precipitation']} mm",
                delta=f"{mj['precipitation'] - ly['precipitation']:+.1f} mm",
                delta_color="inverse")
    col3.metric("습도", f"{mj['humidity']}%",
                delta=f"{mj['humidity'] - ly['humidity']:+.0f}%",
                delta_color="off")
    col4.metric("풍속", f"{mj['wind_speed']} m/s",
                delta=f"{mj['wind_speed'] - ly['wind_speed']:+.1f} m/s",
                delta_color="off")
    
    temp_diff = mj['temperature'] - ly['temperature']
    prec_diff = mj['precipitation'] - ly['precipitation']
    st.info(f"📅 **1년 전 오늘과 비교해 볼까요?** 작년 이맘때({year_ago_date})에 비해 기온은 **{abs(temp_diff):.1f}도 {'높아요' if temp_diff > 0 else '낮아요'}**, 강수량은 **{abs(prec_diff):.1f}mm {'많아요' if prec_diff > 0 else '적어요'}!**")
    st.info(weather_label(mj['weather_code']))
    st.markdown(f"> {generate_comment(mj['temperature'], mj['precipitation'], mj['weather_code'])}")

    with st.expander("🌏 지구 반대편은?"):
        st.caption(f"몬테비데오 (우루과이) · {mv['temperature']}°C · {weather_label(mv['weather_code'])}")

    st.divider()

    # ── 섹션 2: 이상 기후 탐지 ────────────────────────────
    st.header("🚨 근데 오늘 좀 이상한 날씨 아닌가요?")
    st.info("🚨 **AI가 찾아낸 요주의 날씨!**\n\n"
            "최근 3달 동안 유독 비가 많이 오거나 기온이 널뛰었던 **상위 5%의 특이한 날**들만 콕 집어냈어요. 오늘 그래프에 **보라색 점**이 찍혔다면 단단히 대비하고 나가세요!")

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
        legend_title_text='구분',
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption(f"알고리즘: {get_anomaly_algorithm_info()}")

    anomaly_count = analyzed['is_anomaly'].sum()
    if anomaly_count > 0:
        st.warning(f"최근 90일간 {anomaly_count}번의 이상한 날씨가 있었어요. 오늘 출근길, 조심하세요!")
    else:
        st.success("최근 90일간 날씨는 평온했어요. 오늘도 무난한 하루 될 것 같아요 😊")

    st.divider()

    # ── 섹션 3: 날씨 × 지하철 상관관계 ────────────────────
    st.header("🚇 이 날씨에 지하철 얼마나 붐빌까요?")
    st.caption("날씨와 문정역 지하철 이용객 수를 분석했어요. 오늘 같은 날씨, 지하철이 더 붐빌까요?")

    with st.spinner("상관관계 분석 중..."):
        subway_df = get_subway()
        corr = compute_correlation(hist_df, subway_df)

    col3, col4, col5 = st.columns(3)
    pearson_str = f"{corr['pearson']:.4f}" if corr['pearson'] is not None else "데이터 없음"
    spearman_str = f"{corr['spearman']:.4f}" if corr['spearman'] is not None else "데이터 없음"
    col3.metric("선형 상관도 (Pearson)", pearson_str)
    col4.metric("순위 상관도 (Spearman)", spearman_str)
    col5.metric("분석 표본 수 (평일)", f"{corr['n_samples']}일")
    
    st.info("💡 **그래서 지하철이 붐빈다는 건가요?**\n\n"
            "숫자가 **+1에 가까울수록** 기온이 오를 때 지옥철이 되고, **-1에 가까울수록** 쾌적해진다는 뜻이에요.\n"
            "*(※ AI가 2가지 방식으로 교차 검증한 결과입니다 😎)*")

    st.caption(f"📊 해석: {interpret_correlation(corr['pearson'])}")

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

    render_footer()


if __name__ == "__main__":
    main()
