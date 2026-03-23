"""
UI 자산(app.py, assets/style.css, static/about.html) 정적 검증 테스트.

Streamlit을 실행하지 않고 소스 파일 내용을 읽어 검증한다.
- 폰트 일관성: iframe 컴포넌트가 Space Grotesk / Manrope 사용 여부
- backdrop-filter: 모든 블러 적용 요소에 -webkit- prefix 존재 여부
- 툴팁 방향성: 상관계수 +1/-1 설명이 올바른 방향 여부
"""
import pathlib

ROOT = pathlib.Path(__file__).parent.parent


def _read(rel: str) -> str:
    return ROOT.joinpath(rel).read_text(encoding="utf-8")


# ── iframe 폰트 ───────────────────────────────────────────────────────────────

def test_iframes_load_google_fonts():
    """날씨 카드·expander·히어로 3개 iframe 모두 Google Fonts를 로드한다."""
    src = _read("app.py")
    count = src.count("fonts.googleapis.com/css2?family=Space+Grotesk")
    assert count >= 3, f"Google Fonts 링크가 {count}개뿐 (최소 3 필요)"


def test_iframes_use_space_grotesk():
    """iframe html/body font-family에 Space Grotesk가 포함된다."""
    src = _read("app.py")
    assert "'Space Grotesk'" in src


def test_iframes_no_system_font_only_stack():
    """iframe에서 시스템 폰트 단독 스택(-apple-system…)이 사용되지 않는다."""
    src = _read("app.py")
    assert (
        "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
        not in src
    )


def test_expander_t1_uses_manrope():
    """.t1 레이블(부제목)은 Manrope 기반이다."""
    src = _read("app.py")
    assert ".t1" in src and "'Manrope'" in src


def test_expander_t2_uses_space_grotesk():
    """.t2 레이블(수치)은 Space Grotesk 기반이다."""
    src = _read("app.py")
    assert ".t2" in src and "'Space Grotesk'" in src


# ── backdrop-filter webkit prefix ────────────────────────────────────────────

def test_style_css_metric_container_webkit_backdrop_filter():
    """style.css의 .stMetricContainer에 -webkit-backdrop-filter가 있다."""
    css = _read("assets/style.css")
    assert "-webkit-backdrop-filter: blur(16px)" in css


def test_about_html_glass_webkit_backdrop_filter():
    """about.html의 .glass에 -webkit-backdrop-filter가 있다."""
    html = _read("static/about.html")
    lines = html.splitlines()
    in_glass = False
    for line in lines:
        if ".glass {" in line:
            in_glass = True
        if in_glass and "}" in line:
            in_glass = False
        if in_glass and "-webkit-backdrop-filter" in line:
            return
    raise AssertionError(".glass 블록에 -webkit-backdrop-filter 없음")


def test_about_html_modal_content_webkit_backdrop_filter():
    """about.html의 .modal-content 블록에 -webkit-backdrop-filter가 있다."""
    html = _read("static/about.html")
    lines = html.splitlines()
    in_block = False
    for line in lines:
        if ".modal-content {" in line:
            in_block = True
        if in_block:
            if "-webkit-backdrop-filter" in line:
                return
            if line.strip() == "}":
                break
    raise AssertionError(".modal-content 블록에 -webkit-backdrop-filter 없음")


def test_about_html_webkit_backdrop_filter_count():
    """about.html 전체에서 -webkit-backdrop-filter가 최소 4곳 이상 사용된다."""
    html = _read("static/about.html")
    count = html.count("-webkit-backdrop-filter")
    assert count >= 4, f"-webkit-backdrop-filter가 {count}개뿐 (최소 4 필요)"


# ── 강수량 툴팁 방향성 ─────────────────────────────────────────────────────────

def test_precip_pearson_tooltip_positive_crowded():
    """+1 → 비 올수록 붐빔: 양의 상관 방향이 올바르다."""
    src = _read("app.py")
    assert "+1에 가까울수록 → 비 올수록 지하철이 붐벼요" in src


def test_precip_pearson_tooltip_negative_quiet():
    """-1 → 비 오면 한산: 음의 상관 방향이 올바르다."""
    src = _read("app.py")
    assert "-1에 가까울수록 → 비 오면 오히려 한산해요" in src


# ── 기온 툴팁 방향성 ───────────────────────────────────────────────────────────

def test_temp_pearson_tooltip_positive_hot_crowded():
    """+1 → 더울수록 붐빔: 양의 상관 방향이 올바르다."""
    src = _read("app.py")
    assert "+1에 가까울수록 → 더울수록 지하철이 붐벼요" in src


def test_temp_pearson_tooltip_negative_cold_crowded():
    """-1 → 추울수록 붐빔: 음의 상관 방향이 올바르다."""
    src = _read("app.py")
    assert "-1에 가까울수록 → 추울수록 지하철이 붐벼요" in src
