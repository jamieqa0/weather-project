import os
# Force Streamlit to hot-reload HTML changes
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(layout="wide", page_title="문정동 출근, 소개합니다", page_icon="static/favicon.png")

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


if st.query_params.get("scrollTo") == "timeline":
    html_content += """
    <script>
      setTimeout(function() {
        var el = document.getElementById('timeline');
        if (el) el.scrollIntoView({behavior: "smooth", block: "start"});
      }, 500);
    </script>
    """

components.html(html_content, height=9500, scrolling=True)
