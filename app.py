import os
import random
from datetime import datetime, date, timedelta
import streamlit as st
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv

from data.collector import fetch_current_weather, fetch_historical_weather, fetch_subway_data, fetch_weather_on_date
from analysis.anomaly import detect_anomalies
from analysis.correlation import compute_correlation
from commentary.generator import generate_comment
from commentary.interpretation import interpret_correlation, format_last_updated

load_dotenv()

# ── 좌표 상수 ────────────────────────────────────────────
MUNJEONG = {"name": "문정동 (서울)", "lat": 37.4946, "lon": 127.1237}
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
    df = fetch_subway_data(api_key=api_key)
    df['date'] = df['date'].astype(str)  # Arrow 직렬화 후 타입 보장
    return df


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

WEATHER_ICONS = {
    0: "☀️", 1: "🌤", 2: "⛅", 3: "☁️",
    45: "🌫", 48: "🌫",
    51: "🌦", 53: "🌦", 55: "🌦",
    61: "🌧", 63: "🌧", 65: "🌧",
    71: "🌨", 73: "🌨", 75: "❄️",
    80: "🌦", 81: "🌦", 82: "⛈",
    95: "⛈",
}


def weather_label(code: int) -> str:
    return WEATHER_LABELS.get(code, f"날씨 코드 {code}")


def weather_icon(code: int) -> str:
    return WEATHER_ICONS.get(code, "🌡️")


WEATHER_CARD_BG = {
    0: ("rgba(255,231,146,0.08)", "rgba(255,231,146,0.25)"),   # 맑음 - 골드
    1: ("rgba(255,231,146,0.05)", "rgba(255,231,146,0.15)"),   # 대체로 맑음
    2: ("rgba(90,248,251,0.05)",  "rgba(90,248,251,0.15)"),    # 구름 조금
    3: ("rgba(72,71,75,0.15)",    "rgba(72,71,75,0.35)"),      # 흐림 - 회색
    45: ("rgba(130,130,140,0.1)", "rgba(130,130,140,0.25)"),   # 안개
    48: ("rgba(130,130,140,0.1)", "rgba(130,130,140,0.25)"),
    51: ("rgba(26,86,178,0.08)",  "rgba(90,248,251,0.2)"),     # 이슬비
    53: ("rgba(26,86,178,0.08)",  "rgba(90,248,251,0.2)"),
    55: ("rgba(26,86,178,0.08)",  "rgba(90,248,251,0.2)"),
    61: ("rgba(26,86,178,0.1)",   "rgba(90,248,251,0.25)"),    # 비
    63: ("rgba(26,86,178,0.1)",   "rgba(90,248,251,0.25)"),
    65: ("rgba(26,86,178,0.14)",  "rgba(90,248,251,0.3)"),     # 강한 비
    71: ("rgba(173,216,230,0.08)","rgba(200,230,255,0.2)"),    # 눈
    73: ("rgba(173,216,230,0.08)","rgba(200,230,255,0.2)"),
    75: ("rgba(173,216,230,0.12)","rgba(200,230,255,0.3)"),    # 강한 눈
    80: ("rgba(26,86,178,0.1)",   "rgba(90,248,251,0.25)"),    # 소나기
    81: ("rgba(26,86,178,0.1)",   "rgba(90,248,251,0.25)"),
    82: ("rgba(26,86,178,0.14)",  "rgba(90,248,251,0.3)"),
    95: ("rgba(204,151,255,0.08)","rgba(204,151,255,0.3)"),    # 천둥번개 - 보라
}


def weather_animation_html(code: int) -> str:
    """날씨 코드에 맞는 배경 애니메이션 HTML 반환. 랜덤 시드를 코드로 고정해 리렌더 시 위치 일정."""
    rng = random.Random(code * 7919)
    els = []

    if code == 0:  # ☀️ 맑음 — 태양 광선
        css = """
        @keyframes sun-glow{0%,100%{opacity:.35;transform:scale(1)}50%{opacity:.6;transform:scale(1.08)}}
        @keyframes sun-ray{0%,100%{opacity:.1}50%{opacity:.22}}"""
        els.append('<div style="position:absolute;right:-15px;top:-15px;width:110px;height:110px;border-radius:50%;background:radial-gradient(circle,rgba(255,231,146,.35) 0%,transparent 70%);animation:sun-glow 3s ease-in-out infinite;pointer-events:none;"></div>')
        for i in range(8):
            ang = i * 45
            els.append(f'<div style="position:absolute;right:33px;top:18px;width:55px;height:2px;background:rgba(255,231,146,.18);transform-origin:0 50%;transform:rotate({ang}deg);animation:sun-ray 4s ease-in-out {i*0.4:.1f}s infinite;border-radius:2px;pointer-events:none;"></div>')

    elif code in (1, 2):  # 🌤⛅ 대체로 맑음 / 구름 조금
        css = """
        @keyframes cloud-drift{from{transform:translateX(0)}to{transform:translateX(18px)}}
        @keyframes sun-peek{0%,100%{opacity:.18}50%{opacity:.35}}"""
        els.append('<div style="position:absolute;right:-10px;top:-10px;width:80px;height:80px;border-radius:50%;background:radial-gradient(circle,rgba(255,231,146,.25) 0%,transparent 70%);animation:sun-peek 4s ease-in-out infinite;pointer-events:none;"></div>')
        for i in range(2):
            l, t = rng.randint(55, 85), rng.randint(10, 65)
            w = rng.randint(45, 75)
            d = rng.uniform(0, 2)
            els.append(f'<div style="position:absolute;left:{l}%;top:{t}%;width:{w}px;height:{w//3}px;background:rgba(200,215,230,.1);border-radius:50px;animation:cloud-drift {3+i}s ease-in-out {d:.1f}s infinite alternate;filter:blur(3px);pointer-events:none;"></div>')

    elif code == 3:  # ☁️ 흐림 — 구름 여러 층
        css = "@keyframes cloud-move{from{transform:translateX(0)}to{transform:translateX(25px)}}"
        for i in range(5):
            l, t = rng.randint(-5, 85), rng.randint(5, 80)
            w = rng.randint(55, 105)
            dur = rng.uniform(6, 11)
            d = rng.uniform(0, 3)
            op = rng.uniform(0.06, 0.13)
            els.append(f'<div style="position:absolute;left:{l}%;top:{t}%;width:{w}px;height:{w//3}px;background:rgba(155,165,175,{op:.2f});border-radius:50px;animation:cloud-move {dur:.1f}s ease-in-out {d:.1f}s infinite alternate;filter:blur(5px);pointer-events:none;"></div>')

    elif code in (45, 48):  # 🌫 안개
        css = "@keyframes fog{0%,100%{transform:translateX(0);opacity:.07}50%{transform:translateX(12px);opacity:.14}}"
        for i in range(4):
            t = rng.randint(8, 82)
            d = i * 1.8
            els.append(f'<div style="position:absolute;left:-5%;top:{t}%;width:110%;height:18px;background:rgba(195,205,215,.12);border-radius:50%;animation:fog {5+i}s ease-in-out {d:.1f}s infinite;filter:blur(9px);pointer-events:none;"></div>')

    elif code in (51, 53, 55, 61, 63, 65, 80, 81, 82):  # 🌧 비 계열
        n = 45 if code in (65, 82) else 20 if code in (51, 53, 55) else 32
        css = "@keyframes rain{0%{transform:translateY(-8px) rotate(12deg);opacity:0}10%{opacity:.55}90%{opacity:.35}100%{transform:translateY(95px) rotate(12deg);opacity:0}}"
        for _ in range(n):
            l = rng.uniform(0, 100)
            d = rng.uniform(0, 1.6)
            dur = rng.uniform(0.5, 1.1)
            h = rng.randint(8, 17)
            op = rng.uniform(0.3, 0.6)
            els.append(f'<div style="position:absolute;left:{l:.1f}%;top:-5%;width:1px;height:{h}px;background:linear-gradient(to bottom,transparent,rgba(90,248,251,{op:.2f}));animation:rain {dur:.2f}s linear {d:.2f}s infinite;border-radius:1px;pointer-events:none;"></div>')

    elif code in (71, 73, 75):  # 🌨❄️ 눈
        n = 28 if code == 75 else 16
        css = "@keyframes snow{0%{transform:translateY(-8px) translateX(0);opacity:0}15%{opacity:.65}85%{opacity:.45}100%{transform:translateY(95px) translateX(8px);opacity:0}}"
        for _ in range(n):
            l = rng.uniform(0, 100)
            d = rng.uniform(0, 3.5)
            dur = rng.uniform(2.5, 5)
            sz = rng.randint(3, 7)
            op = rng.uniform(0.45, 0.8)
            els.append(f'<div style="position:absolute;left:{l:.1f}%;top:-5%;width:{sz}px;height:{sz}px;background:rgba(210,230,255,{op:.2f});border-radius:50%;animation:snow {dur:.1f}s ease-in {d:.1f}s infinite;pointer-events:none;"></div>')

    elif code == 95:  # ⛈ 천둥번개
        css = """
        @keyframes bolt1{0%,88%,100%{opacity:0}90%,94%{opacity:.18}92%,96%{opacity:0}}
        @keyframes bolt2{0%,70%,100%{opacity:0}72%,76%{opacity:.12}74%,78%{opacity:0}}"""
        els.append('<div style="position:absolute;inset:0;background:rgba(240,240,180,.25);border-radius:.75rem;animation:bolt1 5s ease-in-out 0s infinite;pointer-events:none;"></div>')
        els.append('<div style="position:absolute;inset:0;background:rgba(204,151,255,.18);border-radius:.75rem;animation:bolt2 7s ease-in-out 2s infinite;pointer-events:none;"></div>')

    else:
        return ""

    return f"<style>{css}</style>" + "".join(els)


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
        <h1 style="font-size: 2.8rem; margin: 0; letter-spacing: -0.02em;">문정동 Jamie | 오늘 나갈까?</h1>
        <p style="color: #acaaae; font-size: 1.05rem; margin-top: 0.6rem;">
            오늘 문정동 날씨, 출근 전에 미리 확인해요
        </p>
        <div style="display: flex; justify-content: center; gap: 1.5rem; margin-top: 1.2rem; font-size: 0.85rem; color: #767579;">
            <span>📍 문정동, 서울 출근 날씨 리포트</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_floating_toc():
    st.markdown("""
    <style>
      .ftoc {
        position: fixed;
        right: 1.2rem;
        top: 50%;
        transform: translateY(-50%);
        z-index: 1000;
        background: rgba(25,25,29,0.88);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(72,71,75,0.35);
        border-radius: 0.75rem;
        padding: 0.75rem 0.625rem;
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
      }
      .ftoc-title {
        font-size: 0.6rem;
        color: #48474b;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        text-align: center;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid rgba(72,71,75,0.3);
        margin-bottom: 0.2rem;
      }
      .ftoc a {
        display: flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.28rem 0.5rem;
        border-radius: 0.375rem;
        font-size: 0.72rem;
        color: #767579;
        text-decoration: none !important;
        transition: all 150ms ease;
        white-space: nowrap;
      }
      .ftoc a:hover { color: #acaaae; background: rgba(72,71,75,0.2); }
      .ftoc-dot { width:4px; height:4px; border-radius:50%; background:currentColor; flex-shrink:0; }
      @media (max-width: 900px) { .ftoc { display: none; } }
      /* 앵커 도달 시 상단 여백 확보 (타이틀이 넉넉하게 보이도록 여백 증가) */
      a[id="today-weather"], a[id="anomaly"], a[id="subway"] {
        display: block;
        scroll-margin-top: 100px;
      }

      /* =========================================
         Streamlit 순차 페이드인 애니메이션 (유저 요청)
         ========================================= */
      @keyframes fadeInUp {
        from { opacity: 0; transform: translate3d(0, 30px, 0); }
        to { opacity: 1; transform: translate3d(0, 0, 0); }
      }
      
      /* 모든 메인 블록의 자식 요소들에 지연 애니메이션 적용 */
      [data-testid="stVerticalBlock"] > div {
        animation: fadeInUp 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
      }
      
      [data-testid="stVerticalBlock"] > div:nth-child(1) { animation-delay: 0.05s; }
      [data-testid="stVerticalBlock"] > div:nth-child(2) { animation-delay: 0.15s; }
      [data-testid="stVerticalBlock"] > div:nth-child(3) { animation-delay: 0.25s; }
      [data-testid="stVerticalBlock"] > div:nth-child(4) { animation-delay: 0.35s; }
      [data-testid="stVerticalBlock"] > div:nth-child(5) { animation-delay: 0.45s; }
      [data-testid="stVerticalBlock"] > div:nth-child(6) { animation-delay: 0.55s; }
      [data-testid="stVerticalBlock"] > div:nth-child(7) { animation-delay: 0.65s; }
      [data-testid="stVerticalBlock"] > div:nth-child(8) { animation-delay: 0.75s; }
      [data-testid="stVerticalBlock"] > div:nth-child(9) { animation-delay: 0.85s; }
      [data-testid="stVerticalBlock"] > div:nth-child(10) { animation-delay: 0.95s; }
      [data-testid="stVerticalBlock"] > div:nth-child(n+11) { animation-delay: 1.05s; }
      
      /* TOC 래퍼의 애니메이션 해제 (position: fixed & transform 충돌 방지) */
      [data-testid="stVerticalBlock"] > div:has(.ftoc) {
        animation: none !important;
        transform: none !important;
      }
      
      /* Metric 컨테이너 호버 3D 효과 (보너스) */
      [data-testid="stMetric"] {
        transition: transform 0.25s ease, background 0.25s ease;
        padding: 0.5rem 1rem; border-radius: 0.5rem;
      }
      [data-testid="stMetric"]:hover {
        transform: translateY(-3px) scale(1.02);
        background: rgba(255, 231, 146, 0.03);
      }
    </style>
    <nav class="ftoc" id="main-ftoc" aria-label="페이지 목차">
      <div class="ftoc-title">목차</div>
      <a data-sec="today-weather" href="#today-weather"><span class="ftoc-dot"></span>오늘 날씨</a>
      <a data-sec="anomaly" href="#anomaly"><span class="ftoc-dot"></span>이상 기후</a>
      <a data-sec="subway" href="#subway"><span class="ftoc-dot"></span>지하철 혼잡도</a>
    </nav>
    """, unsafe_allow_html=True)

    import streamlit.components.v1 as components
    components.html("""
    <script>
    (function () {
      var p = window.parent;
      var SECTIONS = ['today-weather', 'anomaly', 'subway'];

      function getScrollContainer() {
        // Streamlit의 실제 스크롤 컨테이너들을 탐색하여 scroll 이벤트 포착
        var container = p.document.querySelector('[data-testid="stAppViewContainer"]') || 
                        p.document.querySelector('.main') || 
                        p.document.querySelector('[data-testid="stMainBlockContainer"]') || 
                        p;
        return container;
      }

      function updateHighlight() {
        var current = SECTIONS[0];
        // getBoundingClientRect는 내부 컨테이너 스크롤에 관계없이 뷰포트 기준 절대좌표를 반환합니다.
        SECTIONS.forEach(function (id) {
          var el = p.document.getElementById(id);
          if (el) {
            var rect = el.getBoundingClientRect();
            // 요소의 top이 윈도우 상단 35% 지점 이내로 들어오면 현재 보고 있는 챕터로 간주
            if (rect.top <= p.innerHeight * 0.35) {
              current = id;
            }
          }
        });

        SECTIONS.forEach(function (id) {
          var link = p.document.querySelector('.ftoc a[data-sec="' + id + '"]');
          if (link) {
            if (id === current) link.classList.add('toc-active');
            else link.classList.remove('toc-active');
            
            // 앵커 클릭 시 부드러운 스크롤 + 타이틀 여백 확보
            if (!link.dataset.clickBound) {
              link.dataset.clickBound = "true";
              link.addEventListener('click', function(e) {
                e.preventDefault();
                var targetId = this.getAttribute('data-sec');
                var targetEl = p.document.getElementById(targetId);
                // scrollIntoView가 CSS의 scroll-margin-top:72px를 자동 반영해 타이틀을 가리지 않게 스크롤해줍니다.
                if (targetEl) {
                  targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
              });
            }
          }
        });
      }

      function init() {
        if (p.document.getElementById('today-weather')) {
          var scroller = getScrollContainer();
          scroller.addEventListener('scroll', updateHighlight, { passive: true });
          updateHighlight();
        } else {
          setTimeout(init, 300);
        }
      }
      setTimeout(init, 600);
    })();
    </script>
    """, height=0)


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
        <p style="margin: 0 0 0.8rem; font-size: 0.95rem; color: #acaaae;">문정동 Jamie | 오늘 나갈까? · <span style="color:#cc97ff;">Job-Stealer</span> 사내 스터디</p>
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
            <a href="/about" target="_self"
               style="color: #ffe792; text-decoration: none;">
                🌌 프로젝트 소개 페이지
            </a>
            <a href="/about?scrollTo=timeline" target="_self"
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
    st.set_page_config(layout="wide", page_title="Jamie | 오늘 나갈까?", page_icon="🚇")
    inject_css()
    render_floating_toc()
    render_hero()

    # ── 섹션 1: 오늘 날씨 ─────────────────────────────────
    st.markdown('<a id="today-weather"></a>', unsafe_allow_html=True)
    st.header("☀️ Jamie, 오늘 문정동 날씨예요")
    st.caption(f"🕐 {format_last_updated(datetime.now())}")

    if os.getenv("SEOUL_API_KEY") is None:
        st.toast("💡 안내: 지하철 혼잡도는 과거 샘플 데이터를 기준으로 보여드려요.")

    with st.spinner("날씨 불러오는 중..."):
        mj = get_current(MUNJEONG["lat"], MUNJEONG["lon"])
        mv = get_current(MONTEVIDEO["lat"], MONTEVIDEO["lon"])
        ly = get_year_ago(MUNJEONG["lat"], MUNJEONG["lon"])

    _ya = date.today() - timedelta(days=365)
    year_ago_date = f"{_ya.year}년 {_ya.month}월 {_ya.day}일"

    _wcode = mj['weather_code']
    _bg, _border = WEATHER_CARD_BG.get(_wcode, ("rgba(90,248,251,0.06)", "rgba(90,248,251,0.2)"))

    # ① 핵심 하이라이트 카드
    st.markdown(f"""
    <div style="
        position: relative; overflow: hidden;
        background: {_bg}; border: 1px solid {_border};
        border-radius: 0.75rem; padding: 1.5rem 1.75rem; margin: 0.5rem 0;
    ">
      {weather_animation_html(_wcode)}
      <div style="position:relative;z-index:1;display:flex;align-items:center;gap:1.25rem;flex-wrap:wrap;">
        <span style="font-size:3.5rem;line-height:1;">{weather_icon(_wcode)}</span>
        <div>
          <div style="font-size:2.8rem;font-weight:700;color:#f3f0f4;line-height:1.1;">{mj['temperature']}°C</div>
          <div style="font-size:1.05rem;font-weight:600;color:#acaaae;margin-top:0.2rem;">{weather_label(_wcode)}</div>
          <div style="font-size:0.85rem;color:#767579;margin-top:0.15rem;">{generate_comment(mj['temperature'], mj['precipitation'], _wcode)}</div>
        </div>
        <div style="margin-left:auto;text-align:right;font-size:0.9rem;color:#acaaae;line-height:2;">
          <div>최고 <strong style="color:#f3f0f4;">{mj['temperature_max']}°C</strong></div>
          <div>최저 <strong style="color:#f3f0f4;">{mj['temperature_min']}°C</strong></div>
          <div>평균 <strong style="color:#f3f0f4;">{mj['temperature_mean']}°C</strong></div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ② 나머지 수치
    col1, col2, col3 = st.columns(3)
    col1.metric("강수량 (오늘 합계)", f"{mj['precipitation_sum']} mm",
                delta=f"{mj['precipitation_sum'] - ly['precipitation']:+.1f} mm vs 1년전",
                delta_color="inverse")
    col2.metric("습도", f"{mj['humidity']}%")
    col3.metric("풍속", f"{mj['wind_speed']} m/s")
    temp_diff = mj['temperature_max'] - ly['temperature']
    prec_diff = mj['precipitation_sum'] - ly['precipitation']
    temp_str = f"{abs(temp_diff):.1f}도 {'높아요' if temp_diff > 0 else '낮아요'}" if abs(temp_diff) >= 0.1 else "비슷해요"
    prec_str = f"{abs(prec_diff):.1f}mm {'많아요' if prec_diff > 0 else '적어요'}" if abs(prec_diff) >= 0.1 else "똑같이 맑아요 ☀️" if ly['precipitation'] == 0 else "비슷해요"
    st.caption(f"📅 **1년 전 오늘({year_ago_date})과 비교하면** — 최고기온 {temp_str}, 강수량 {prec_str}")

    with st.expander("🌏 지구 반대편은?"):
        st.caption(f"몬테비데오 (우루과이) · {mv['temperature']}°C · {weather_label(mv['weather_code'])}")

    st.divider()

    # ── 섹션 2: 이상 기후 탐지 ────────────────────────────
    st.markdown('<a id="anomaly"></a>', unsafe_allow_html=True)
    st.header("🚨 근데, 오늘 좀 이상한 날씨는 아닐까요?")

    with st.spinner("과거 데이터 분석 중..."):
        hist_df = get_historical(MUNJEONG["lat"], MUNJEONG["lon"], days=365)
        analyzed = detect_anomalies(hist_df)

    anomaly_count = analyzed['is_anomaly'].sum()
    today_str = date.today().isoformat()
    today_row = analyzed[analyzed['date'] == today_str]
    today_is_anomaly = bool(not today_row.empty and today_row.iloc[0]['is_anomaly'])

    # ① 결과 먼저 — 크게 강조
    if today_is_anomaly:
        bg, border, icon, title, body = (
            "rgba(204,151,255,0.12)", "#cc97ff", "🚨",
            "오늘이 바로 그날입니다!",
            f"최근 1년 중 이상 기후로 분류된 날이에요. 오늘 출근길, 단단히 대비하세요!"
        )
    elif anomaly_count > 0:
        bg, border, icon, title, body = (
            "rgba(90,248,251,0.08)", "#5af8fb", "✅",
            "오늘은 평범한 날씨예요.",
            f"최근 1년간 이상 기후는 {anomaly_count}번 있었지만, 오늘은 해당 없어요 😌"
        )
    else:
        bg, border, icon, title, body = (
            "rgba(90,248,251,0.08)", "#5af8fb", "✅",
            "오늘도, 요즘도 무난해요.",
            "최근 1년간 이상 기후가 없었어요 😊"
        )
    st.markdown(f"""
    <div style="
        background:{bg}; border:1px solid {border};
        border-radius:0.75rem; padding:1.5rem 1.75rem; margin:0.5rem 0;
    ">
      <div style="display:flex;align-items:center;gap:1.25rem;">
        <span style="font-size:3.5rem;line-height:1;flex-shrink:0;">{icon}</span>
        <div>
          <div style="font-size:1.2rem;font-weight:700;color:#f3f0f4;margin-bottom:0.3rem;">{title}</div>
          <div style="font-size:0.95rem;color:#acaaae;">{body}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ② 분석 방법 설명 — 작게
    st.caption("🤖 **어떻게 판단했냐고요?** Isolation Forest AI가 최근 1년치 최고·최저·평균기온, 일교차, 강수량, 습도, 풍속 7가지를 종합 분석해 상위 5%의 극단적인 날을 이상 기후로 분류했어요. 그래프의 보라색 다이아몬드가 그 날들이에요.")

    # ③ 근거: 그래프
    analyzed['구분'] = analyzed['is_anomaly'].map({True: '이상 기후', False: '정상'})
    fig = px.scatter(
        analyzed, x='date', y='temperature',
        color='구분',
        color_discrete_map={'이상 기후': '#cc97ff', '정상': '#5af8fb'},
        labels={'temperature': '일평균기온 (°C)', 'date': '날짜', '구분': ''},
        custom_data=['temp_min', 'temp_max', 'temp_range'],
    )
    fig.update_traces(
        hovertemplate='%{x}<br>평균: %{y:.1f}°C<br>최고: %{customdata[1]:.1f}°C  최저: %{customdata[0]:.1f}°C<br>일교차: %{customdata[2]:.1f}°C<extra></extra>',
    )
    fig.update_traces(
        marker=dict(size=8, opacity=0.8, line=dict(width=1, color='rgba(0,0,0,0.25)')),
        selector=dict(name='정상'),
    )
    fig.update_traces(
        marker=dict(size=14, opacity=1, symbol='diamond',
                    line=dict(width=2, color='#cc97ff')),
        selector=dict(name='이상 기후'),
    )
    fig.update_layout(
        paper_bgcolor='#0e0e11', plot_bgcolor='#19191d',
        font_color='#f3f0f4',
        title=None,
        xaxis=dict(
            title='날짜', tickformat='%m/%d',
            gridcolor='rgba(72,71,75,0.3)', tickfont=dict(size=11),
        ),
        yaxis=dict(
            title='기온 (°C)',
            gridcolor='rgba(72,71,75,0.3)', zeroline=False, tickfont=dict(size=11),
        ),
        legend=dict(
            title=None,
            orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0,
            font=dict(size=13, color='#f3f0f4'),
            bgcolor='rgba(25,25,29,0.7)', bordercolor='rgba(72,71,75,0.4)', borderwidth=1,
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        hoverlabel=dict(bgcolor='#19191d', font_color='#f3f0f4', bordercolor='#48474b'),
    )
    _range_end = date.today() - timedelta(days=1)
    _range_start = _range_end - timedelta(days=364)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"📅 분석 기간: {_range_start.strftime('%Y년 %m월 %d일')} ~ {_range_end.strftime('%Y년 %m월 %d일')} (1년)")

    # ③ 상세: 이상 기후 날 목록
    anomaly_days = analyzed[analyzed['is_anomaly']].sort_values('date', ascending=False)
    if not anomaly_days.empty:
        FEATURE_LABELS = {
            'temp_max':     ('🌡️ 최고기온 높음', '🌡️ 최고기온 낮음'),
            'temp_min':     ('🌡️ 최저기온 높음', '🌡️ 최저기온 낮음'),
            'temperature':  ('🌡️ 평균기온 높음', '🌡️ 평균기온 낮음'),
            'temp_range':   ('↕️ 일교차 큼', None),
            'precipitation': ('🌧️ 강수량 많음', None),
            'humidity':     ('💧 습도 높음', '💧 습도 낮음'),
            'wind_speed':   ('💨 강풍', None),
        }
        stats = analyzed[['temp_max', 'temp_min', 'temperature', 'temp_range', 'precipitation', 'humidity', 'wind_speed']].agg(['mean', 'std'])

        def explain(row):
            reasons = []
            for col, (pos, neg) in FEATURE_LABELS.items():
                std = stats.loc['std', col]
                if std == 0:
                    continue
                z = (row[col] - stats.loc['mean', col]) / std
                if z > 1.5 and pos:
                    reasons.append(pos)
                elif z < -1.5 and neg:
                    reasons.append(neg)
            return ' · '.join(reasons) if reasons else '복합 요인'

        with st.expander(f"🔍 이상 기후로 분류된 {len(anomaly_days)}일의 실제 수치 보기"):
            display_df = anomaly_days[['date', 'temp_max', 'temp_min', 'temperature', 'precipitation', 'humidity', 'wind_speed']].copy()
            display_df['이상 원인'] = anomaly_days.apply(explain, axis=1)
            display_df.columns = ['날짜', '최고기온 (°C)', '최저기온 (°C)', '일평균기온 (°C)', '강수량 (mm)', '평균습도 (%)', '최대풍속 (m/s)', '이상 원인']
            display_df = display_df.reset_index(drop=True)
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()

    # ── 섹션 3: 날씨 × 지하철 상관관계 ────────────────────
    st.markdown('<a id="subway"></a>', unsafe_allow_html=True)
    st.header("🚇 이 날씨에 지하철 얼마나 붐빌까요?")

    with st.spinner("상관관계 분석 중..."):
        subway_df = get_subway()
        hist_df['date'] = hist_df['date'].astype(str)
        corr = compute_correlation(hist_df, subway_df)


    # ① 결과 먼저
    # 기온과 강수량의 상관도를 모두 반영한 해석
    def get_combined_correlation_text(temp_r, precip_r):
        """기온과 강수량의 상관도를 통합해서 한 문장으로 표현."""
        avg_r = (abs(temp_r) + abs(precip_r)) / 2 if temp_r and precip_r else None

        if not temp_r or not precip_r:
            return "데이터 없음"

        if avg_r < 0.1:
            level = "거의 영향 없음"
        elif avg_r < 0.3:
            level = "약한 영향"
        elif avg_r < 0.7:
            level = "중간 정도의 영향"
        else:
            level = "큰 영향"

        return f"기온과 강수량 둘 다 {level} — 지하철 이용객 수는 날씨 변화와 큰 관련이 없는 것으로 보여요."

    combined_interp = get_combined_correlation_text(corr['pearson'], corr['precipitation_pearson'])

    st.markdown(f"""
    <div style="
        background:rgba(90,248,251,0.08); border:1px solid #5af8fb;
        border-radius:0.75rem; padding:1.5rem 1.75rem; margin:0.5rem 0;
    ">
      <div style="display:flex;align-items:center;gap:1.25rem;">
        <span style="font-size:3.5rem;line-height:1;flex-shrink:0;">🚇</span>
        <div>
          <div style="font-size:1.2rem;font-weight:700;color:#f3f0f4;margin-bottom:0.3rem;">오늘 같은 날씨, 지하철은?</div>
          <div style="font-size:0.95rem;color:#acaaae;">{combined_interp}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ② 수치 근거 — 1행 4카드 배치
    pearson_str = f"{corr['pearson']:.4f}" if corr['pearson'] is not None else "데이터 없음"
    spearman_str = f"{corr['spearman']:.4f}" if corr['spearman'] is not None else "데이터 없음"
    precip_pearson_str = f"{corr['precipitation_pearson']:.4f}" if corr['precipitation_pearson'] is not None else "데이터 없음"
    precip_spearman_str = f"{corr['precipitation_spearman']:.4f}" if corr['precipitation_spearman'] is not None else "데이터 없음"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("기온 선형\n(Pearson)", pearson_str,
                help="기온과 이용객 수의 직선적 관계")
    col2.metric("기온 순위\n(Spearman)", spearman_str,
                help="기온 순위와 이용객 순위의 일치도")
    col3.metric("강수량 선형\n(Pearson)", precip_pearson_str,
                help="강수량과 이용객 수의 직선적 관계")
    col4.metric("강수량 순위\n(Spearman)", precip_spearman_str,
                help="강수량 순위와 이용객 순위의 일치도")

    st.caption("**Pearson**과 **Spearman**은 기온·강수량과 지하철 이용객 수의 관계를 각각 직선적, 순위 기반으로 측정해요. 기온은 +1에 가까울수록 따뜻할 때 붐비고, 강수량은 -1에 가까울수록 비올 때 적어진다는 의미입니다. 두 값이 비슷한 방향을 가리킬수록 신뢰도가 높아요.")

    merged = pd.merge(hist_df, subway_df, on='date')
    if len(merged) >= 2:
        # 기온 그래프
        fig_temp = px.scatter(
            merged, x='temperature', y='passengers',
            trendline='ols',
            title='일평균기온 vs 지하철 이용객 수 (평일)',
            labels={'temperature': '일평균기온 (°C)', 'passengers': '이용객 수'},
            color_discrete_sequence=['#5af8fb'],
        )
        fig_temp.add_vline(
            x=mj['temperature_mean'],
            line_width=2, line_dash='dash', line_color='#ffe792',
            annotation_text=f"오늘 평균 {mj['temperature_mean']}°C",
            annotation_position='top',
            annotation_font_color='#ffe792',
        )
        fig_temp.update_layout(
            paper_bgcolor='#0e0e11', plot_bgcolor='#19191d',
            font_color='#f3f0f4', title_font_color='#ffe792',
        )

        # 강수량 그래프
        fig_precip = px.scatter(
            merged, x='precipitation', y='passengers',
            trendline='ols',
            title='강수량 vs 지하철 이용객 수 (평일)',
            labels={'precipitation': '강수량 (mm)', 'passengers': '이용객 수'},
            color_discrete_sequence=['#ff9999'],
        )
        fig_precip.add_vline(
            x=mj['precipitation_sum'],
            line_width=2, line_dash='dash', line_color='#ffe792',
            annotation_text=f"오늘 강수량 {mj['precipitation_sum']}mm",
            annotation_position='top',
            annotation_font_color='#ffe792',
        )
        fig_precip.update_layout(
            paper_bgcolor='#0e0e11', plot_bgcolor='#19191d',
            font_color='#f3f0f4', title_font_color='#ffe792',
        )

        # 좌우 배치
        col_left, col_right = st.columns(2)
        col_left.plotly_chart(fig_temp, use_container_width=True)
        col_right.plotly_chart(fig_precip, use_container_width=True)

        _s = datetime.strptime(merged['date'].min(), '%Y-%m-%d')
        _e = datetime.strptime(merged['date'].max(), '%Y-%m-%d')
        st.caption(f"📅 분석 기간: {_s.strftime('%Y년 %m월 %d일')} ~ {_e.strftime('%Y년 %m월 %d일')} ({corr['n_samples']}일, 평일 기준)")
    else:
        st.info("날씨 데이터와 지하철 데이터의 날짜가 겹치지 않아 차트를 표시할 수 없습니다.")

    render_footer()


if __name__ == "__main__":
    main()
