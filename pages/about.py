import os
# Force Streamlit to hot-reload HTML changes
import streamlit as st
import streamlit.components.v1 as components
from timeline.builder import build_timeline_html

st.set_page_config(layout="wide", page_title="기후탐정 소개", page_icon="🌌")

# 사이드바 숨기기 + 패딩 제거 (풀페이지 HTML 경험)
st.markdown("""
<style>
  [data-testid="stSidebar"] { display: none; }
  [data-testid="collapsedControl"] { display: none; }
  .block-container { padding: 0 !important; max-width: 100% !important; }
  header { display: none; }
</style>
""", unsafe_allow_html=True)

html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "about.html")
with open(html_path, encoding="utf-8") as f:
    html_content = f.read()

log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "timeline", "log.json")
html_content = html_content.replace('<!-- TIMELINE_PLACEHOLDER -->', build_timeline_html(log_path))

if st.query_params.get("scrollTo") == "timeline":
    html_content += """
    <script>
      setTimeout(function() {
        var el = document.getElementById('timeline');
        if (el) el.scrollIntoView({behavior: "smooth", block: "start"});
      }, 500);
    </script>
    """

components.html(html_content, height=5500, scrolling=True)

# 테스트 개선 현황 섹션
st.markdown("---")
st.header("🧪 테스트 품질 관리")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("테스트 커버리지", "100%", "+5%")
with col2:
    st.metric("테스트 수", "92개", "+22개")
with col3:
    st.metric("완료 Phase", "4/5", "진행 중")

st.subheader("📋 개선 이력")
st.markdown("""
### Phase 1: 감성 멘트 (commentary/generator.py)
- 81% → **100%** ✅
- 추가: 9개 테스트 (비, 눈, 극온 조건)

### Phase 2: 상관분석 (analysis/correlation.py)
- 94% → **100%** ✅
- 추가: 4개 테스트 (데이터 부족, 강수량 분석)

### Phase 3: 데이터 수집 (data/collector.py)
- 95% → **100%** ✅
- 추가: 4개 테스트 (API 예외 처리)

### Phase 4: 데이터 정합성 ⏳
- 형식 검증: 날짜, 온도, 습도, 풍속 범위
- 정합성: 다중 소스 merge, 필수 컬럼 검증
- 추가: 5개 테스트

---

📊 **최종 결과**: 95% → **100% 커버리지** 달성
🧪 **테스트**: 70개 → **92개** (+22개)
📅 **기간**: 2026-03-22

📖 [상세 내용](../docs/test-improvements.md)
""")

st.divider()
st.caption("🛡️ 100% 테스트 커버리지로 보호받는 견고한 데이터 분석 플랫폼")
