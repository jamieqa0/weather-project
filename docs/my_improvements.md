2026-03-22 오전 1시 26분 개선사항

index.html 페이지에 관한점
- [x] 기후탐정 대시보드 푸터에 링크 넣어줘 - 타이틀은 니가 알맞게 해주고
- [x] 아키텍처는 문자열 말고 도식으로 해줘
- [x] 타임라인도 업데이트 해주고
- [x] 페이지 타이틀과 파비콘도 변경해줘


기후탐정 대시보드에 관한점
- [x] Pearson 상관계수, Spearman 상관계수 - 이게 뭔지 사용자는 모르잖아. 쉽게 설명해줘
- [x] 이상치 탐지 - 어떤 기준으로 이상치를 탐지했는지 알려줘 (caption에 Isolation Forest 기준 설명 포함)
- [ ] Open-Meteo API, 서울 열린데이터광장 데이터 맞아? 더미데이터 아닌지 확인 필요해 (직접 확인 필요)
- [x] 박보닥씨, 오늘 문정역 날씨예요 - 1년 전 날짜와 비교기능 추가


2026-03-22 오후 2시 2분 개선사항
기후탐정 대시보드에 관한점
- [x] http://localhost:8501/ 접속하면 맨 위 상단에 stAppToolbar 흰 영역 노출시키지 말아줘
- [x] 기온 선형, 기온 순위 마우스 오버하면 툴팁 노출되는데 - 배경도 흰색, 텍스트도 흰색 이라 잘 안보여! 스타일에 맞게 수정해줘
- [x] 전반적인 스타일이 Eridian Horizon 이거랑 맞는거 맞지? 검토해줘 (강수량 그래프 색상 #ff9999 → #ff7351 수정)
- [x] 오늘 날씨 부분 stMarkdownContainer 안에 에니메니션 넣어준다고 했는데 그대로거든 - 적용된거 맞는지 봐줘 (이미 구현됨 확인)
- [x] 기온 선형, 기온 순위 - 굳이 소숫점 네째자리까지 나와야 할까? 아니라면 조정해줘!
- [x] 기온 선형, 기온 순위 - 툴팁 내용이 이해가 안되니까 가독성 좋게 줄바꿈처리를 해줘, 글 톤엔매너를 맞춰줘.
- [x] ● weather_animation_html 함수 내용
    ● 애니메이션은 이미 코드에 구현되어 있습니다 — weather_animation_html(_wcode)가
    날씨 코드별로 CSS animation HTML을 생성해서 카드 안에 주입하고 있어요.
    다만 맑음(☀️) 날씨일 때는 효과가 매우 미묘해서 (opacity 0.1~0.35 수준) 잘 안 보인다. 개선 필요한데 내가 레퍼런스좀 찾아볼게- https://app.lottiefiles.com/animation/9c582ed5-a26c-4c9a-82d9-f51a445d277c 이러한 방식으로 적용해줘
- [x] 에니메이션 적용 비교군이 필요해서- stExpanderDetails 부분에도 같은 방식 https://app.lottiefiles.com/animation/9c582ed5-a26c-4c9a-82d9-f51a445d277c 이러한 방식으로 적용해줘



2026-03-23 오전 1시 15분 개선사항
기후탐정 대시보드에 관한점
- [x] 날씨 코드별 Lottie 애니메이션 구현 (sunny / cloudy / overcast / rain / snow / fog / thunder — 로컬 static/lottie/ 파일 기반)
- [x] 기존 CSS 애니메이션은 fallback으로 유지 (weather_animation_html 병행)
- [x] lottie-player 웹 컴포넌트 방식으로 구현 (inject_lottie_script → components.html height=0)
- [x] 오늘 날씨 카드 내부에 position:absolute 배경 오버레이로 적용 (glass 스타일과 어울리도록)
- [x] stExpanderDetails 영역에도 동일한 Lottie 애니메이션 배경 적용 (지구 반대편 / 이상 기후 목록 expander)

요구사항:
1. [x] stExpanderDetails 내부에도 동일한 Lottie 애니메이션 삽입
2. [x] 메인 카드와 stExpanderDetails 간 애니메이션 표현 차이를 비교할 수 있도록 구성
3. [x] UI 일관성 유지 (크기/정렬/여백 포함)

[x] 목표:
기존 "거의 안 보이는 CSS 애니메이션" →
"명확하게 인지되는 인터랙티브 Lottie 애니메이션"으로 개선

---

# 🌤️ 바로 쓰는 Lottie 날씨 세트
[x] ☀️ 맑음 (해 아이콘 + 빛 퍼짐)
SUN = "https://assets10.lottiefiles.com/packages/lf20_7v5qkz.json"
[x] ☁️ 흐림 (구름 움직임)
CLOUD = "https://assets10.lottiefiles.com/packages/lf20_dgjK9i.json"
[x] 🌧️ 비 (비 떨어지는 애니메이션)
RAIN = "https://assets10.lottiefiles.com/packages/lf20_xd9ypluc.json"
[x] ❄️ 눈 (눈 내리는 효과)
SNOW = "https://assets10.lottiefiles.com/packages/lf20_9cyyl8i6.json"

[x] 🌫️ 안개 (안개 효과)
FOG = "https://assets10.lottiefiles.com/packages/lf20_9cyyl8i6.json"
[x] ⛈️ 뇌우 (천둥 효과)
THUNDER = "https://assets10.lottiefiles.com/packages/lf20_9cyyl8i6.json"

# [x]🚀 1️⃣ 공통 함수 (이거 먼저 추가) ※ _lottie_lib() + _lottie_json()으로 구현 (로컬 파일 기반)

```python
import requests
from streamlit_lottie import st_lottie

def load_lottie(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()
```

---

# [x]🚀 2️⃣ 날씨 코드 → 애니메이션 매핑 ※ _lottie_name(code)으로 구현

```python
def get_weather_lottie(weather):
    if "맑" in weather:
        return load_lottie(SUN)
    elif "비" in weather:
        return load_lottie(RAIN)
    elif "눈" in weather:
        return load_lottie(SNOW)
    else:
        return load_lottie(CLOUD)
```

---

# [x]🚀 3️⃣ 기존 함수 교체 (핵심🔥) ※ render_weather_card_component()로 구현

👉 기존 `weather_animation_html()` 대신 이렇게

```python
def render_weather_animation(weather):
    lottie = get_weather_lottie(weather)

    if lottie:
        st_lottie(
            lottie,
            height=180,
            loop=True,
            speed=1,
        )
```

---

# [x] 🚀 4️⃣ 카드 영역내에 적용 ※ render_lottie_in_expander(code, line1, line2)로 구현

```python
st.subheader("☀️ 오늘 날씨")

col1, col2 = st.columns([1, 2])

with col1:
    render_weather_animation(weather)

with col2:
    st.write(f"{location}")
    st.write(f"{temperature}°C")
    st.write(weather)
```

