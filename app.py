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
from commentary.interpretation import format_last_updated, format_montevideo_time

import base64
import streamlit.components.v1 as components
load_dotenv()

@st.cache_data
def get_base64_image(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

# ── 좌표 상수 ────────────────────────────────────────────
MUNJEONG = {"name": "문정동 (서울)", "lat": 37.4946, "lon": 127.1237}
MONTEVIDEO = {"name": "몬테비데오 (우루과이)", "lat": -34.9011, "lon": -56.1645}

# ── CSS 주입 ─────────────────────────────────────────────
def inject_css():
    # pages/ 폴더로 인해 자동 생성되는 사이드 네비게이션 숨기기 + 툴바/툴팁 오버라이드
    st.markdown("""
    <style>
      /* 초기 흰 화면 방지 */
      html, body { background-color: #0e0e11 !important; }

      [data-testid="stSidebar"] { display: none; }
      [data-testid="collapsedControl"] { display: none; }

      /* 상단 툴바 숨기기 + 여백 제거 */
      [data-testid="stToolbar"],
      [data-testid="stAppToolbar"],
      header[data-testid="stHeader"],
      .stAppToolbar { display: none !important; }
      .block-container { padding-top: 0 !important; }
      [data-testid="stAppViewContainer"] { padding-top: 0 !important; }
      [data-testid="stMainBlockContainer"] { padding-top: 0 !important; }

      /* 툴팁 개선: 컴팩트한 크기 & 일관된 스타일 */
      div[role="tooltip"] {
        background-color: rgba(31, 31, 35, 0.95) !important;
        backdrop-filter: blur(8px) !important;
        color: #f3f0f4 !important;
        border: 1px solid rgba(90, 248, 251, 0.25) !important;
        border-radius: 4px !important;
        padding: 0.5rem 0.75rem !important;
        font-size: 0.8rem !important;
        line-height: 1.4 !important;
        max-width: 320px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5) !important;
      }
      div[role="tooltip"] * {
        background-color: transparent !important;
        color: #f3f0f4 !important;
        border: none !important;
        font-size: inherit !important;
      }
      /* 툴팁 호버 시 위치 고정성 향상 보조 */
      [data-testid="stTooltipHoverTarget"] {
        display: inline-block !important;
        cursor: help !important;
      }

      /* 모바일 헤더 줄바꿈 비활성화 */
      .sec-title { line-height: 1.35; }
      .sec-title .mb { display: none; }

      /* 대시보드 메인 레이아웃: 적절한 너비로 조정 */
      [data-testid="stMainBlockContainer"] {
        max-width: 1050px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-right: 2rem !important;
      }
      @media (min-width: 1550px) {
        /* 플로팅 TOC(약 200px)를 충분히 고려한 미세 조정 */
        [data-testid="stMainBlockContainer"] {
           margin-right: calc(50% - 525px + 9rem) !important;
        }
      }
      @media (max-width: 1050px) {
        [data-testid="stMainBlockContainer"] {
          max-width: 100% !important;
          padding-right: 1rem !important;
          padding-left: 1rem !important;
        }
      }

      /* 익스팬더 애니메이션 레이어 */
      [data-testid="stExpanderDetails"] {
        position: relative;
        overflow: hidden;
      }

      /* expander 레이블 — 보조 정보라 작게 */
      [data-testid="stExpander"] summary p {
        font-size: 0.82rem !important;
        color: #767579 !important;
      }

      /* 모바일: 차트 컬럼 1열 스택 */
      @media (max-width: 640px) {
        [data-testid="stColumns"]:has([data-testid="stPlotlyChart"]) {
          flex-wrap: wrap !important;
        }
        [data-testid="stColumns"]:has([data-testid="stPlotlyChart"]) > [data-testid="stColumn"] {
          min-width: 100% !important;
        }
      }
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
    0: "sunny.png", 1: "partly_cloudy.png", 2: "partly_cloudy.png", 3: "cloudy.png",
    45: "cloudy.png", 48: "cloudy.png",
    51: "rainy.png", 53: "rainy.png", 55: "rainy.png",
    61: "rainy.png", 63: "rainy.png", 65: "rainy.png",
    71: "snowy.png", 73: "snowy.png", 75: "snowy.png",
    80: "rainy.png", 81: "rainy.png", 82: "thunderstorm.png",
    95: "thunderstorm.png",
}


def weather_label(code: int) -> str:
    return WEATHER_LABELS.get(code, f"날씨 코드 {code}")



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


def _lottie_name(code: int) -> str | None:
    """날씨 코드 → Lottie 파일명 매핑."""
    if code == 0:
        return "sunny.json"
    elif code in (1, 2):
        return "cloudy.json"
    elif code == 3:
        return "overcast.json"
    elif code in (45, 48):
        return "fog.json"
    elif code in (51, 53, 55, 61, 63, 65, 80, 81, 82):
        return "rain.json"
    elif code in (71, 73, 75):
        return "snow.json"
    elif code == 95:
        return "thunder.json"
    return None

@st.cache_data
def _lottie_lib() -> str:
    """lottie.min.js 파일 내용을 읽어 캐시."""
    path = os.path.join(os.path.dirname(__file__), "static", "lottie.min.js")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

@st.cache_data(ttl=86400)
def _lottie_json(code: int) -> str:
    """날씨 코드에 해당하는 Lottie JSON 문자열 반환. 없으면 빈 문자열."""
    fname = _lottie_name(code)
    if not fname:
        return ""
    path = os.path.join(os.path.dirname(__file__), "static", "lottie", fname)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def render_weather_card_component(wcode: int, mj: dict, comment: str) -> None:
    """날씨 카드 전체를 components.html()로 렌더링 — lottie-web으로 JSON 인라인 삽입."""

    _bg, _border = WEATHER_CARD_BG.get(wcode, ("rgba(90,248,251,0.06)", "rgba(90,248,251,0.2)"))
    _label = weather_label(wcode)

    icon_name = WEATHER_ICONS.get(wcode, "sunny.png")
    icon_b64 = get_base64_image(os.path.join("assets", "icons", icon_name))
    icon_img = (f'<img src="data:image/png;base64,{icon_b64}">') if icon_b64 else "🌡️"

    lottie_json = _lottie_json(wcode)
    lottie_layer = ""
    lottie_script = ""
    if lottie_json:
        lottie_layer = '''<div id="lottie-bg" style="position:absolute;top:0;bottom:0;right:0;width:42%;pointer-events:none;z-index:0;overflow:hidden;">
  <div id="lottie-anim-0" style="position:absolute;width:190px;height:190px;right:-30px;top:-40px;opacity:0.30;border-radius:50%;overflow:hidden;"></div>
  <div id="lottie-anim-1" style="position:absolute;width:120px;height:120px;right:100px;top:-20px;opacity:0.20;border-radius:50%;overflow:hidden;"></div>
  <div id="lottie-anim-2" style="position:absolute;width:90px;height:90px;right:30px;top:70px;opacity:0.16;border-radius:50%;overflow:hidden;"></div>
  <div id="lottie-anim-3" style="position:absolute;width:65px;height:65px;right:150px;top:55px;opacity:0.12;border-radius:50%;overflow:hidden;"></div>
  <div id="lottie-anim-4" style="position:absolute;width:75px;height:75px;right:185px;top:-10px;opacity:0.11;border-radius:50%;overflow:hidden;"></div>
</div>'''
        lottie_script = f"""<script>
var _data = {lottie_json};
[0,1,2,3,4].forEach(function(i) {{
  var a = lottie.loadAnimation({{
    container: document.getElementById('lottie-anim-'+i),
    renderer: 'svg', loop: true, autoplay: true,
    animationData: JSON.parse(JSON.stringify(_data))
  }});
  a.goToAndPlay(i * 18, true);
}});
</script>"""

    _lottie_lib_js = _lottie_lib()
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Manrope:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script>{_lottie_lib_js}</script>
<style>* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ background: #0e0e11; font-family: 'Space Grotesk', 'Manrope', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; }}
.card {{ position:relative;overflow:hidden;background:{_bg};border:1px solid {_border};
    border-radius:0.75rem;padding:1.5rem 1.75rem;margin:2px 0; }}
.row {{ position:relative;z-index:1;display:flex;align-items:center;gap:1.5rem;flex-wrap:nowrap; }}
.icon img {{ width:110px;height:110px;object-fit:contain;filter:drop-shadow(0 0 15px rgba(255,255,255,0.2)); }}
.temps {{ font-size:2.8rem;font-weight:700;color:#f3f0f4;line-height:1.1; }}
.label {{ font-size:1.05rem;font-weight:600;color:#ffe792;margin-top:0.2rem; }}
.comment {{ font-size:0.9rem;font-weight:600;color:#5af8fb;margin-top:0.25rem;letter-spacing:0.01em; }}
.stats {{ font-size:0.78rem;color:#acaaae;margin-top:0.35rem;letter-spacing:0.01em; }}
.stats span {{ color:#f3f0f4;font-weight:600; }}
@media (max-width: 480px) {{
  .card {{ padding:1rem 1rem; }}
  .row {{ gap:0.8rem; }}
  .icon img {{ width:72px !important; height:72px !important; }}
  .temps {{ font-size:2rem; }}
  .label {{ font-size:0.9rem; }}
  .comment {{ font-size:0.78rem; }}
  .stats {{ font-size:0.72rem; }}
  #lottie-anim-0 {{ width:70px !important; height:70px !important; right:-5px !important; top:-5px !important; opacity:0.20 !important; }}
  #lottie-anim-1 {{ width:50px !important; height:50px !important; right:60px !important; top:10px !important; opacity:0.13 !important; }}
  #lottie-anim-2, #lottie-anim-3, #lottie-anim-4 {{ display:none; }}
}}
</style></head>
<body>
<div class="card">
  {lottie_layer}
  <div class="row">
    <div class="icon" style="line-height:0;flex-shrink:0;">{icon_img}</div>
    <div>
      <div class="temps">{mj['temperature']}°C</div>
      <div class="label">{_label}</div>
      <div class="comment">{comment}</div>
      <div class="stats">최고 <span>{mj['temperature_max']}°C</span> &nbsp;·&nbsp; 최저 <span>{mj['temperature_min']}°C</span> &nbsp;·&nbsp; 평균 <span>{mj['temperature_mean']}°C</span></div>
    </div>
  </div>
</div>
{lottie_script}
</body></html>"""

    components.html(html, height=165)


def render_lottie_in_expander(code: int, line1: str = "", line2: str = "") -> None:
    """expander 내부에 Lottie 배경 + 텍스트 오버레이를 한 블록으로 렌더링."""
    lottie_json = _lottie_json(code)
    if not lottie_json:
        if line1:
            st.caption(line1)
        if line2:
            st.caption(line2)
        return
    _lottie_lib_js = _lottie_lib()
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Manrope:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script>{_lottie_lib_js}</script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ background: transparent; }}
.wrap {{ position:relative; width:100%; height:88px; overflow:hidden; border-radius:0.5rem; }}
.lottie-zone {{ position:absolute;top:0;bottom:0;right:0;width:55%;pointer-events:none;z-index:0;overflow:hidden; }}
.lottie-zone div {{ position:absolute;border-radius:50%;overflow:hidden; }}
.overlay {{ position:absolute;inset:0;display:flex;flex-direction:column;
            justify-content:center;padding:0 1.2rem;z-index:1;
            background:linear-gradient(90deg,rgba(14,14,17,0.65) 0%,rgba(14,14,17,0.25) 60%,transparent 100%); }}
.t1 {{ font-size:0.78rem;color:#acaaae;font-family:'Manrope','Apple SD Gothic Neo','Malgun Gothic',sans-serif; }}
.t2 {{ font-size:1rem;font-weight:600;color:#f3f0f4;font-family:'Space Grotesk','Apple SD Gothic Neo','Malgun Gothic',sans-serif;margin-top:0.2rem; }}
@media (max-width:480px) {{ #la2,#la3,#la4 {{ display:none; }} }}
</style>
</head><body>
<div class="wrap">
  <div class="lottie-zone">
    <div id="la0" style="width:130px;height:130px;right:-20px;top:-25px;opacity:0.32;"></div>
    <div id="la1" style="width:85px;height:85px;right:90px;top:-15px;opacity:0.22;"></div>
    <div id="la2" style="width:65px;height:65px;right:165px;top:10px;opacity:0.15;"></div>
    <div id="la3" style="width:70px;height:70px;right:50px;top:35px;opacity:0.16;"></div>
    <div id="la4" style="width:50px;height:50px;right:200px;top:-8px;opacity:0.11;"></div>
  </div>
  <div class="overlay">
    <div class="t1">{line1}</div>
    <div class="t2">{line2}</div>
  </div>
</div>
<script>
var _d = {lottie_json};
['la0','la1','la2','la3','la4'].forEach(function(id,i) {{
  var el = document.getElementById(id);
  if (!el) return;
  var a = lottie.loadAnimation({{
    container:el, renderer:'svg', loop:true, autoplay:true,
    animationData:JSON.parse(JSON.stringify(_d))
  }});
  a.goToAndPlay(i*18, true);
}});
</script>
</body></html>"""
    components.html(html, height=92)

def weather_animation_html(code: int) -> str:
    """날씨 코드에 맞는 배경 애니메이션 HTML 반환. 랜덤 시드를 코드로 고정해 리렌더 시 위치 일정."""
    rng = random.Random(code * 7919)
    els = []

    if code == 0:  # ☀️ 맑음 — 태양 + 회전 광선 + 반짝이
        css = """
        @keyframes sun-pulse{0%,100%{opacity:.85;transform:scale(1)}50%{opacity:1;transform:scale(1.1)}}
        @keyframes sun-outer{0%,100%{opacity:.4;transform:scale(1)}50%{opacity:.65;transform:scale(1.15)}}
        @keyframes sun-spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
        @keyframes ray-flash{0%,100%{opacity:.5}50%{opacity:.9}}
        @keyframes sparkle{0%,100%{opacity:0;transform:scale(.4)}45%,55%{opacity:.85;transform:scale(1)}}"""
        # 외곽 글로우
        els.append('<div style="position:absolute;right:-8px;top:-8px;width:105px;height:105px;border-radius:50%;background:radial-gradient(circle,rgba(255,231,146,.35) 0%,transparent 68%);animation:sun-outer 3s ease-in-out .4s infinite;pointer-events:none;"></div>')
        # 태양 원판
        els.append('<div style="position:absolute;right:15px;top:12px;width:65px;height:65px;border-radius:50%;background:radial-gradient(circle,rgba(255,231,146,.95) 25%,rgba(255,200,60,.55) 55%,transparent 78%);animation:sun-pulse 2.5s ease-in-out infinite;pointer-events:none;"></div>')
        # 회전하는 광선 레이어
        ray_els = '<div style="position:absolute;right:15px;top:12px;width:65px;height:65px;animation:sun-spin 10s linear infinite;pointer-events:none;">'
        for i in range(8):
            ang = i * 45
            ray_els += f'<div style="position:absolute;left:50%;top:50%;width:42px;height:3px;background:linear-gradient(to right,rgba(255,231,146,.85),transparent);transform-origin:0 50%;transform:translateY(-50%) rotate({ang}deg);border-radius:3px;animation:ray-flash 2s ease-in-out {i*0.25:.2f}s infinite;"></div>'
        ray_els += '</div>'
        els.append(ray_els)
        # 반짝이 파티클
        for i in range(5):
            lx, ty = rng.randint(5, 72), rng.randint(8, 82)
            d = rng.uniform(0, 2.5)
            sz = rng.randint(3, 6)
            els.append(f'<div style="position:absolute;left:{lx}%;top:{ty}%;width:{sz}px;height:{sz}px;border-radius:50%;background:rgba(255,231,146,.9);animation:sparkle {1.4+i*0.35:.2f}s ease-in-out {d:.2f}s infinite;pointer-events:none;"></div>')

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
    lottie_json = _lottie_json(0)  # sunny
    lottie_lib_js = _lottie_lib()

    lottie_bg = ""
    lottie_script = ""
    if lottie_json:
        lottie_bg = '''
  <div id="lottie-anim-0" style="position:absolute;width:200px;height:200px;right:5%;top:-20px;opacity:0.20;pointer-events:none;border-radius:50%;overflow:hidden;"></div>
  <div id="lottie-anim-1" style="position:absolute;width:120px;height:120px;right:22%;top:30px;opacity:0.10;pointer-events:none;border-radius:50%;overflow:hidden;"></div>'''
        lottie_script = f"""<script>
var _data = {lottie_json};
[0,1].forEach(function(i) {{
  var a = lottie.loadAnimation({{
    container: document.getElementById('lottie-anim-'+i),
    renderer: 'svg', loop: true, autoplay: true,
    animationData: JSON.parse(JSON.stringify(_data))
  }});
  a.goToAndPlay(i * 20, true);
}});
</script>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Manrope:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script>{lottie_lib_js}</script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ background: #0e0e11; font-family: 'Space Grotesk', 'Manrope', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; }}
.hero {{
  position: relative; overflow: hidden;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; padding: 3.5rem 2rem;
  background: radial-gradient(circle at center, rgba(255,231,146,0.07) 0%, transparent 70%);
  border-bottom: 1px solid rgba(72,71,75,0.15);
  min-height: 240px;
}}
h1 {{ font-size: clamp(2rem, 6vw, 3.2rem); font-weight: 800; color: #ffe792;
      text-shadow: 0 0 25px rgba(255,231,146,0.3); letter-spacing: -0.02em; line-height: 1.1; }}
p  {{ color: #acaaae; font-size: 1rem; margin-top: 0.9rem; line-height: 1.6; max-width: 560px; }}
@media (max-width: 480px) {{
  .hero {{ padding: 2rem 1.2rem; min-height: 180px; }}
  #lottie-anim-0 {{ width: 90px !important; height: 90px !important; right: 2% !important; top: 0 !important; opacity: 0.15 !important; }}
  #lottie-anim-1 {{ display: none; }}
}}
</style>
</head><body>
<div class="hero">
  {lottie_bg}
  <div style="position:relative;z-index:1;">
    <h1>문정동, 출근해볼까?</h1>
    <p>데이터로 분석한 문정동의 실시간 날씨와<br>지하철 혼잡도를 출근 전에 체크하세요</p>
  </div>
</div>
{lottie_script}
<script>
window.addEventListener('load', function() {{
  window.parent.postMessage({{type: 'streamlit:setFrameHeight', height: document.body.scrollHeight}}, '*');
}});
</script>
</body></html>"""

    components.html(html, height=280)


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
      /* 앵커 도달 시 상단 여백 */
      a[id="today-weather"], a[id="anomaly"], a[id="subway"] {
        display: block;
        scroll-margin-top: 8px;
      }

    </style>
    <nav class="ftoc" id="main-ftoc" aria-label="페이지 목차">
      <div class="ftoc-title">목차</div>
      <a data-sec="today-weather" href="#today-weather"><span class="ftoc-dot"></span>오늘 날씨</a>
      <a data-sec="anomaly" href="#anomaly"><span class="ftoc-dot"></span>이상 기후</a>
      <a data-sec="subway" href="#subway"><span class="ftoc-dot"></span>지하철 혼잡도</a>
    </nav>
    """, unsafe_allow_html=True)

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
    <style>
    .footer-section {
        margin-top: 6rem;
        padding: 4rem 1rem;
        border-top: 1px solid var(--outline);
        background: linear-gradient(to bottom, transparent, rgba(25, 25, 29, 0.4));
        text-align: center;
    }
    .footer-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1.25rem;
        max-width: 1000px;
        margin: 2.5rem auto;
    }
    .footer-pill {
        background: rgba(31, 31, 35, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(72, 71, 75, 0.2);
        border-radius: 999px;
        padding: 0.6rem 1.25rem;
        color: var(--on-surface);
        text-decoration: none !important;
        font-size: 0.82rem;
        font-family: 'Space Grotesk', sans-serif;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }
    .footer-pill:hover {
        background: rgba(90, 248, 251, 0.1);
        border-color: var(--secondary);
        color: var(--secondary);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(90, 248, 251, 0.1);
    }
    .footer-pill.highlight {
        border-color: rgba(255, 231, 146, 0.3);
        color: var(--primary);
    }
    .footer-pill.highlight:hover {
        background: rgba(255, 231, 146, 0.1);
        border-color: var(--primary);
        box-shadow: 0 5px 15px rgba(255, 231, 146, 0.1);
    }
    .footer-copyright {
        font-family: 'Manrope', sans-serif;
        font-size: 0.9rem;
        color: var(--on-surface);
        opacity: 0.8;
        margin-bottom: 0.5rem;
    }
    .footer-tagline {
        font-size: 0.72rem;
        color: #767579;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    @media (max-width: 640px) {
        .footer-grid { grid-template-columns: 1fr 1fr; gap: 0.75rem; }
        .footer-pill { padding: 0.5rem 0.8rem; font-size: 0.75rem; }
    }
    </style>
    <div class="footer-section" style="position: relative; z-index: 9999;">
        <div class="footer-copyright">
            문정동, 출근해볼까? <span style="opacity:0.4; margin:0 0.5rem;">|</span> <span style="color:var(--tertiary);">Job-Stealer</span>
        </div>
        <div class="footer-grid">
            <a href="https://open-meteo.com" target="_blank" class="footer-pill">🌤 Open-Meteo</a>
            <a href="https://data.seoul.go.kr" target="_blank" class="footer-pill">🚇 서울데이터광장</a>
            <a href="https://github.com/jamieqa0/weather-project" target="_blank" class="footer-pill">💻 GitHub</a>
            <a href="/about" target="_self" class="footer-pill highlight">🌌 프로젝트 소개</a>
            <a href="/about?scrollTo=timeline" target="_self" class="footer-pill">🤖 개발 타임라인</a>
            <a href="https://stitch.withgoogle.com/projects/10551746938995651396" target="_blank" class="footer-pill">🎨 디자인시스템</a>
        </div>
        <div class="footer-tagline">
            Built with Python · Streamlit · Plotly · scikit-learn · Claude AI
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    favicon_path = os.path.join("assets", "icons", "favicon.png")
    st.set_page_config(layout="wide", page_title="문정동, 출근해볼까?", page_icon=favicon_path)
    st.markdown("""
    <meta property="og:title" content="문정동, 출근해볼까?" />
    <meta property="og:description" content="문정동 실시간 날씨 · 이상 기후 탐지 · 지하철 혼잡도 분석" />
    <meta property="og:site_name" content="문정동, 출근해볼까?" />
    <meta name="title" content="문정동, 출근해볼까?" />
    <meta name="description" content="문정동 실시간 날씨 · 이상 기후 탐지 · 지하철 혼잡도 분석" />
    """, unsafe_allow_html=True)
    inject_css()
    render_floating_toc()
    render_hero()

    # ── 섹션 1: 오늘 날씨 ─────────────────────────────────
    st.markdown('<a id="today-weather"></a>', unsafe_allow_html=True)
    st.markdown('<h2 class="sec-title">☀️ 오늘 문정동<span class="mb"></span> 날씨예요</h2>', unsafe_allow_html=True)
    st.caption(f"🕐 {format_last_updated()}")

    if os.getenv("SEOUL_API_KEY") is None:
        st.toast("💡 안내: 지하철 혼잡도는 과거 샘플 데이터를 기준으로 보여드려요.")

    with st.spinner("날씨 불러오는 중..."):
        mj = get_current(MUNJEONG["lat"], MUNJEONG["lon"])
        mv = get_current(MONTEVIDEO["lat"], MONTEVIDEO["lon"])
        ly = get_year_ago(MUNJEONG["lat"], MUNJEONG["lon"])

    _ya = date.today() - timedelta(days=365)
    year_ago_date = f"{_ya.year}년 {_ya.month}월 {_ya.day}일"

    _wcode = mj['weather_code']

    # ① 핵심 하이라이트 카드
    render_weather_card_component(_wcode, mj, generate_comment(mj['temperature'], mj['precipitation'], _wcode))

    # ② 나머지 수치
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.5rem;margin:0.5rem 0;">
      <div style="background:#19191d;border-radius:0.5rem;padding:0.75rem 0.5rem;text-align:center;">
        <div style="font-size:0.72rem;color:#767579;margin-bottom:0.2rem;">강수량</div>
        <div style="font-size:1.1rem;font-weight:700;color:#f3f0f4;white-space:nowrap;">{mj['precipitation_sum']} mm</div>
      </div>
      <div style="background:#19191d;border-radius:0.5rem;padding:0.75rem 0.5rem;text-align:center;">
        <div style="font-size:0.72rem;color:#767579;margin-bottom:0.2rem;">습도</div>
        <div style="font-size:1.1rem;font-weight:700;color:#f3f0f4;white-space:nowrap;">{mj['humidity']}%</div>
      </div>
      <div style="background:#19191d;border-radius:0.5rem;padding:0.75rem 0.5rem;text-align:center;">
        <div style="font-size:0.72rem;color:#767579;margin-bottom:0.2rem;">풍속</div>
        <div style="font-size:1.1rem;font-weight:700;color:#f3f0f4;white-space:nowrap;">{mj['wind_speed']} m/s</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    temp_diff = mj['temperature_max'] - ly['temperature']
    prec_diff = mj['precipitation_sum'] - ly['precipitation']
    temp_str = f"{abs(temp_diff):.1f}도 {'더 높음' if temp_diff > 0 else '더 낮음'}" if abs(temp_diff) >= 0.1 else "비슷함"
    prec_str = f"{abs(prec_diff):.1f}mm {'더 많음' if prec_diff > 0 else '더 적음'}" if abs(prec_diff) >= 0.1 else "비슷함"
    _tc = "#ff7351" if temp_diff > 0.1 else "#5af8fb" if temp_diff < -0.1 else "#5af8fb"
    _pc = "#ff7351" if prec_diff > 0.1 else "#5af8fb" if prec_diff < -0.1 else "#5af8fb"
    _ta = "▲" if temp_diff > 0.1 else "▼" if temp_diff < -0.1 else "━"
    _pa = "▲" if prec_diff > 0.1 else "▼" if prec_diff < -0.1 else "━"
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;
                padding:0.65rem 1rem;margin:0.4rem 0;
                background:rgba(72,71,75,0.15);border-radius:0.5rem;
                font-size:0.78rem;color:#767579;">
      <span>📅 1년 전 오늘 <strong style="color:#acaaae;">({year_ago_date})</strong> 과 비교</span>
      <span>최고기온 &nbsp;<strong style="color:{_tc};">{_ta} {temp_str}</strong></span>
      <span>강수량 &nbsp;<strong style="color:{_pc};">{_pa} {prec_str}</strong></span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🌏 지구 반대편은 어떨까?"):
        render_lottie_in_expander(
            mv['weather_code'],
            line1=f"몬테비데오 (우루과이) · 🕐 {format_montevideo_time()}",
            line2=f"{mv['temperature']}°C · {weather_label(mv['weather_code'])}",
        )

    st.divider()

    # ── 섹션 2: 이상 기후 탐지 ────────────────────────────
    st.markdown('<a id="anomaly"></a>', unsafe_allow_html=True)
    st.markdown('<h2 class="sec-title">🚨 근데, 오늘 날씨<span class="mb"></span> 이상하진 않을까요?</h2>', unsafe_allow_html=True)

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
            "rgba(90,248,251,0.08)", "#5af8fb", "🌿",
            "오늘은 평범한 날씨예요.",
            f"최근 1년간 이상 기후는 {anomaly_count}번 있었지만, 오늘은 해당 없어요 😌"
        )
    else:
        bg, border, icon, title, body = (
            "rgba(90,248,251,0.08)", "#5af8fb", "🌿",
            "오늘도, 요즘도 무난해요.",
            "최근 1년간 이상 기후가 없었어요 😊"
        )
    st.markdown(f"""
    <div style="
        background:{bg}; border:1px solid {border};
        border-radius:0.75rem; padding:1.5rem 1.75rem; margin:0.5rem 0;
    ">
      <div style="display:flex;align-items:center;gap:1.25rem;">
        <span style="font-size:2.2rem;line-height:1;flex-shrink:0;">{icon}</span>
        <div>
          <div style="font-size:1.2rem;font-weight:700;color:#f3f0f4;margin-bottom:0.3rem;">{title}</div>
          <div style="font-size:0.95rem;color:#acaaae;">{body}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ② 분석 방법 설명 — 작게
    st.markdown("🤖 **어떻게 판단했냐고요?**<br><span style='color:#acaaae;font-size:0.875rem;'>Isolation Forest AI가 최근 1년치 최고·최저·평균기온, 일교차, 강수량, 습도, 풍속 7가지를 종합 분석해 상위 5%의 극단적인 날을 이상 기후로 분류했어요. 그래프의 <span style='color:#cc97ff;font-weight:700;'>보라색 다이아몬드</span>가 그 날들이에요.</span>", unsafe_allow_html=True)

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
        height=320,
        paper_bgcolor='#0e0e11', plot_bgcolor='#19191d',
        font_color='#f3f0f4',
        title='',
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
    st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})
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

        with st.expander(f"🔍 이상 기후 {len(anomaly_days)}일 — 수치 보기"):
            display_df = anomaly_days[['date', 'temp_max', 'temp_min', 'temperature', 'precipitation', 'humidity', 'wind_speed']].copy()
            display_df['이상 원인'] = anomaly_days.apply(explain, axis=1)
            display_df.columns = ['날짜', '최고기온 (°C)', '최저기온 (°C)', '일평균기온 (°C)', '강수량 (mm)', '평균습도 (%)', '최대풍속 (m/s)', '이상 원인']
            display_df = display_df.reset_index(drop=True)
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()

    # ── 섹션 3: 날씨 × 지하철 상관관계 ────────────────────
    st.markdown('<a id="subway"></a>', unsafe_allow_html=True)
    st.markdown('<h2 class="sec-title">📊 이 날씨에<span class="mb"></span> 지하철 얼마나 붐빌까요?</h2>', unsafe_allow_html=True)

    with st.spinner("상관관계 분석 중..."):
        subway_df = get_subway()
        hist_df['date'] = hist_df['date'].astype(str)
        corr = compute_correlation(hist_df, subway_df)


    # ① 결과 먼저
    # 기온과 강수량의 상관도를 모두 반영한 해석
    def get_combined_correlation_text(temp_r, precip_r):
        """기온과 강수량의 상관도를 통합해서 한 문장으로 표현."""
        if not temp_r or not precip_r:
            return "데이터 없음"

        avg_r = (abs(temp_r) + abs(precip_r)) / 2

        if avg_r < 0.1:
            level = "거의 영향 없음"
        elif avg_r < 0.3:
            level = "약한 영향"
        elif avg_r < 0.7:
            level = "중간 정도의 영향"
        else:
            level = "큰 영향"

        return f"비가 오나 눈이 오나 건조주의보가 내리나, 오늘도 문정역 출근러는 지하철을 탑니다. 날씨와 지하철의 상관관계는 <span style='color:#5af8fb;font-weight:700;'>{level}</span>."

    combined_interp = get_combined_correlation_text(corr['pearson'], corr['precipitation_pearson'])

    st.markdown(f"""
    <style>
    .subway-card {{ background:rgba(90,248,251,0.08); border:1px solid #5af8fb;
        border-radius:0.75rem; padding:1.5rem 1.75rem; margin:0.5rem 0; }}
    .subway-card .inner {{ display:flex; align-items:center; gap:1.25rem; }}
    .subway-card .icon {{ font-size:3.5rem; line-height:1; flex-shrink:0; }}
    .subway-card .title {{ font-size:1.2rem; font-weight:700; color:#f3f0f4;
        margin-bottom:0.3rem; word-break:keep-all; }}
    .subway-card .body {{ font-size:0.95rem; color:#acaaae; word-break:keep-all; }}
    @media (max-width: 480px) {{
        .subway-card {{ padding:1rem 1rem; }}
        .subway-card .icon {{ font-size:2.2rem; }}
        .subway-card .title {{ font-size:1rem; }}
        .subway-card .body {{ font-size:0.85rem; }}
    }}
    </style>
    <div class="subway-card">
      <div class="inner">
        <span class="icon">🚇</span>
        <div>
          <div class="title">오늘 같은 날씨, 지하철은?</div>
          <div class="body">{combined_interp}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ② 수치 근거 — 1행 4카드 배치
    pearson_str = f"{corr['pearson']:.2f}" if corr['pearson'] is not None else "데이터 없음"
    spearman_str = f"{corr['spearman']:.2f}" if corr['spearman'] is not None else "데이터 없음"
    precip_pearson_str = f"{corr['precipitation_pearson']:.2f}" if corr['precipitation_pearson'] is not None else "데이터 없음"
    precip_spearman_str = f"{corr['precipitation_spearman']:.2f}" if corr['precipitation_spearman'] is not None else "데이터 없음"

    st.markdown(f"""
    <style>
      .corr-grid {{ display:grid;grid-template-columns:repeat(2,1fr);gap:0.5rem;margin:0.5rem 0; }}
      .corr-card {{ position:relative;background:#19191d;border-radius:0.5rem;padding:0.75rem 0.75rem; }}
      .corr-label {{ font-size:0.72rem;color:#767579;margin-bottom:0.2rem;display:flex;align-items:center;gap:0.3rem; }}
      .corr-value {{ font-size:1.4rem;font-weight:700;color:#f3f0f4; }}
      .corr-tip {{ position:relative;display:inline-flex;align-items:center;justify-content:center;
                   width:13px;height:13px;border-radius:50%;background:#3a3a3f;
                   color:#acaaae;font-size:9px;cursor:default;flex-shrink:0; }}
      .corr-tip:hover .corr-tip-text {{ display:block; }}
      .corr-tip-text {{ display:none;position:absolute;bottom:calc(100% + 6px);left:50%;transform:translateX(-50%);
                        width:220px;background:#2a2a2f;border:1px solid #3a3a3f;border-radius:0.4rem;
                        padding:0.5rem 0.6rem;font-size:0.72rem;color:#acaaae;line-height:1.5;
                        white-space:normal;z-index:999;pointer-events:none; }}
      .corr-tip-text p {{ margin:0 0 0.35rem 0; }}
      .corr-tip-text ul {{ margin:0;padding-left:1rem; }}
      .corr-tip-text li {{ margin:0.1rem 0; }}
    </style>
    <div class="corr-grid">
      <div class="corr-card">
        <div class="corr-label">기온 선형 (Pearson)
          <span class="corr-tip">?<span class="corr-tip-text"><p>기온이 오를수록 지하철이 얼마나 더 붐비는지 측정한 숫자예요.</p><ul><li>+1 → 더울수록 붐벼요</li><li>-1 → 추울수록 붐벼요</li><li>0 → 기온과 무관해요</li></ul></span></span>
        </div>
        <div class="corr-value">{pearson_str}</div>
      </div>
      <div class="corr-card">
        <div class="corr-label">기온 순위 (Spearman)
          <span class="corr-tip">?<span class="corr-tip-text"><p>'더운 날 순위'와 '붐비는 날 순위'가 얼마나 일치하는지 봐요.</p><ul><li>선형이랑 방향이 같을수록 → 신뢰도 높아요</li><li>방향이 다르면 → 예외적인 날이 섞여 있어요</li></ul></span></span>
        </div>
        <div class="corr-value">{spearman_str}</div>
      </div>
      <div class="corr-card">
        <div class="corr-label">강수량 선형 (Pearson)
          <span class="corr-tip">?<span class="corr-tip-text"><p>비가 많이 올수록 지하철이 얼마나 더 붐비는지 측정한 숫자예요.</p><ul><li>+1 → 비 올수록 붐벼요</li><li>-1 → 비 오면 한산해요</li><li>0 → 강수량과 무관해요</li></ul></span></span>
        </div>
        <div class="corr-value">{precip_pearson_str}</div>
      </div>
      <div class="corr-card">
        <div class="corr-label">강수량 순위 (Spearman)
          <span class="corr-tip">?<span class="corr-tip-text"><p>'비 많은 날 순위'와 '붐비는 날 순위'가 얼마나 일치하는지 봐요.</p><ul><li>선형이랑 방향이 같을수록 → 신뢰도 높아요</li><li>방향이 다르면 → 예외적인 날이 섞여 있어요</li></ul></span></span>
        </div>
        <div class="corr-value">{precip_spearman_str}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.caption("📌 **숫자 해석 방법** — 각 수치는 -1 ~ +1 사이예요. **선형**과 **순위** 두 값이 비슷한 방향을 가리킬수록 신뢰도가 높아요.")

    merged = pd.merge(hist_df, subway_df, on='date')
    merged = merged[pd.to_datetime(merged['date']).dt.dayofweek < 5].reset_index(drop=True)
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
        fig_temp.update_traces(
            hovertemplate='일평균기온: %{x:.1f}°C<br>이용객 수: %{y:,.0f}명<extra></extra>',
            selector=dict(mode='markers'),
        )
        fig_temp.update_layout(
            height=320,
            paper_bgcolor='#0e0e11', plot_bgcolor='#19191d',
            font_color='#f3f0f4', title_font_color='#ffe792',
            yaxis_title='이용객 수 (명)',
        )

        # 강수량 그래프
        fig_precip = px.scatter(
            merged, x='precipitation', y='passengers',
            trendline='ols',
            title='강수량 vs 지하철 이용객 수 (평일)',
            labels={'precipitation': '강수량 (mm)', 'passengers': '이용객 수'},
            color_discrete_sequence=['#ff7351'],
        )
        fig_precip.add_vline(
            x=mj['precipitation_sum'],
            line_width=2, line_dash='dash', line_color='#ffe792',
            annotation_text=f"오늘 강수량 {mj['precipitation_sum']}mm",
            annotation_position='top',
            annotation_font_color='#ffe792',
        )
        fig_precip.update_traces(
            hovertemplate='강수량: %{x:.1f}mm<br>이용객 수: %{y:,.0f}명<extra></extra>',
            selector=dict(mode='markers'),
        )
        fig_precip.update_layout(
            height=320,
            paper_bgcolor='#0e0e11', plot_bgcolor='#19191d',
            font_color='#f3f0f4', title_font_color='#ffe792',
            yaxis_title='이용객 수 (명)',
        )

        # 기온 차트 — 선형 + 순위 한 줄

        # Spearman 차트 — 순위 기반
        merged['rank_temp'] = merged['temperature'].rank()
        merged['rank_precip'] = merged['precipitation'].rank()
        merged['rank_passengers'] = merged['passengers'].rank()

        # 오늘 값의 순위 계산 — rank()의 average 방식과 동일하게
        def _today_rank(series, val):
            below = (series < val).sum()
            equal = (series == val).sum()
            return float(below + (equal + 1) / 2) if equal > 0 else float(below)
        rank_today_temp = _today_rank(merged['temperature'], mj['temperature_mean'])
        rank_today_precip = _today_rank(merged['precipitation'], mj['precipitation_sum'])

        fig_sp_temp = px.scatter(
            merged, x='rank_temp', y='rank_passengers',
            trendline='ols',
            title='기온 순위 vs 이용객 순위 (Spearman)',
            labels={'rank_temp': '기온 순위 (1위=가장 추운 날)', 'rank_passengers': '이용객 순위'},
            color_discrete_sequence=['#5af8fb'],
        )
        fig_sp_temp.update_traces(
            hovertemplate='기온 순위: %{x:.0f}<br>이용객 순위: %{y:.0f}<extra></extra>',
            selector=dict(mode='markers'),
        )
        fig_sp_temp.add_vline(
            x=rank_today_temp,
            line_width=2, line_dash='dash', line_color='#ffe792',
            annotation_text=f"오늘 평균 {mj['temperature_mean']}°C (순위 {rank_today_temp}위)",
            annotation_position='top',
            annotation_font_color='#ffe792',
        )
        fig_sp_temp.update_layout(
            height=320,
            paper_bgcolor='#0e0e11', plot_bgcolor='#19191d',
            font_color='#f3f0f4', title_font_color='#ffe792',
            yaxis_title='이용객 순위',
        )

        fig_sp_precip = px.scatter(
            merged, x='rank_precip', y='rank_passengers',
            trendline='ols',
            title='강수량 순위 vs 이용객 순위 (Spearman)',
            labels={'rank_precip': '강수량 순위 (1위=가장 적게 온 날)', 'rank_passengers': '이용객 순위'},
            color_discrete_sequence=['#ff7351'],
        )
        fig_sp_precip.update_traces(
            hovertemplate='강수량 순위: %{x:.0f}<br>이용객 순위: %{y:.0f}<extra></extra>',
            selector=dict(mode='markers'),
        )
        fig_sp_precip.add_vline(
            x=rank_today_precip,
            line_width=2, line_dash='dash', line_color='#ffe792',
            annotation_text=f"오늘 강수량 {mj['precipitation_sum']}mm (순위 {rank_today_precip}위)",
            annotation_position='top',
            annotation_font_color='#ffe792',
        )
        fig_sp_precip.update_layout(
            height=320,
            paper_bgcolor='#0e0e11', plot_bgcolor='#19191d',
            font_color='#f3f0f4', title_font_color='#ffe792',
            yaxis_title='이용객 순위',
        )

        col_l1, col_r1 = st.columns(2)
        col_l1.plotly_chart(fig_temp, use_container_width=True, config={'staticPlot': True})
        col_r1.plotly_chart(fig_sp_temp, use_container_width=True, config={'staticPlot': True})

        col_l2, col_r2 = st.columns(2)
        col_l2.plotly_chart(fig_precip, use_container_width=True, config={'staticPlot': True})
        col_r2.plotly_chart(fig_sp_precip, use_container_width=True, config={'staticPlot': True})

        _s = datetime.strptime(merged['date'].min(), '%Y-%m-%d')
        _e = datetime.strptime(merged['date'].max(), '%Y-%m-%d')
        st.caption(f"📅 분석 기간: {_s.strftime('%Y년 %m월 %d일')} ~ {_e.strftime('%Y년 %m월 %d일')} ({corr['n_samples']}일, 평일 기준)")
    else:
        st.info("날씨 데이터와 지하철 데이터의 날짜가 겹치지 않아 차트를 표시할 수 없습니다.")

    render_footer()


if __name__ == "__main__":
    main()
