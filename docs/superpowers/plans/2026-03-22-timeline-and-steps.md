# Timeline & Steps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `log.json` 데이터를 `about.html`에 Claude 협업 타임라인으로 시각화하고, 구현 과정 Step 8·9를 추가한다.

**Architecture:** `timeline/builder.py`가 `log.json`을 읽어 타임라인 HTML을 생성한다. `pages/about.py`가 이를 import해 `about.html`의 placeholder에 주입한 뒤 `components.html()`로 렌더링한다. `app.py` 푸터 링크를 활성화한다.

**Tech Stack:** Python 3.10+, Streamlit 1.55, HTML/CSS (no external dependencies)

---

## 파일 목록

| 동작 | 파일 |
|------|------|
| Create | `timeline/builder.py` |
| Create | `tests/test_timeline_builder.py` |
| Modify | `pages/about.py` |
| Modify | `static/about.html` |
| Modify | `app.py` |

---

### Task 1: `timeline/builder.py` — TDD

**Files:**
- Create: `timeline/builder.py`
- Create: `tests/test_timeline_builder.py`

- [ ] **Step 1: `timeline/__init__.py` 생성 (import 가능하게)**

```bash
touch timeline/__init__.py
```
(내용 없는 빈 파일)

- [ ] **Step 2: 실패하는 테스트 작성**

`tests/test_timeline_builder.py` 신규 생성:

```python
import json
import os
import pytest
import tempfile
from timeline.builder import build_timeline_html


def write_log(entries, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False)


def test_returns_html_for_normal_entries(tmp_path):
    log = tmp_path / "log.json"
    write_log([
        {"timestamp": "2026-03-22T14:00:00", "emoji": "💬", "message": "시작", "category": "planning"}
    ], log)
    html = build_timeline_html(str(log))
    assert "tl-list" in html
    assert "시작" in html
    assert "💬" in html
    assert "2026-03-22 14:00" in html
    assert "tl-badge--planning" in html


def test_returns_empty_message_for_empty_list(tmp_path):
    log = tmp_path / "log.json"
    write_log([], log)
    html = build_timeline_html(str(log))
    assert "기록된 대화가 없습니다" in html
    assert "tl-list" not in html


def test_returns_empty_message_when_file_not_found():
    html = build_timeline_html("/nonexistent/log.json")
    assert "기록된 대화가 없습니다" in html


def test_returns_empty_message_for_invalid_json(tmp_path):
    log = tmp_path / "log.json"
    log.write_text("NOT JSON", encoding='utf-8')
    html = build_timeline_html(str(log))
    assert "기록된 대화가 없습니다" in html


def test_unknown_category_falls_back_to_other(tmp_path):
    log = tmp_path / "log.json"
    write_log([
        {"timestamp": "2026-03-22T14:00:00", "emoji": "📌", "message": "msg", "category": "unknown_xyz"}
    ], log)
    html = build_timeline_html(str(log))
    assert "tl-badge--other" in html


def test_missing_fields_use_defaults(tmp_path):
    log = tmp_path / "log.json"
    write_log([{}], log)
    html = build_timeline_html(str(log))
    assert "tl-list" in html
    assert "📌" in html


def test_invalid_timestamp_uses_raw_string(tmp_path):
    log = tmp_path / "log.json"
    write_log([
        {"timestamp": "INVALID", "emoji": "📌", "message": "msg", "category": "dev"}
    ], log)
    html = build_timeline_html(str(log))
    assert "INVALID" in html


def test_last_item_has_no_connector(tmp_path):
    log = tmp_path / "log.json"
    write_log([
        {"timestamp": "2026-03-22T15:00:00", "emoji": "🚀", "message": "first", "category": "dev"},
        {"timestamp": "2026-03-22T14:00:00", "emoji": "💬", "message": "last", "category": "planning"},
    ], log)
    html = build_timeline_html(str(log))
    # 최신순 정렬 → 첫 번째가 15:00, 마지막이 14:00
    # 마지막 항목 이후 connector 없어야 함 (총 connector 수 = 항목 수 - 1)
    assert html.count("tl-connector") == 1


def test_sorted_newest_first(tmp_path):
    log = tmp_path / "log.json"
    write_log([
        {"timestamp": "2026-03-22T14:00:00", "emoji": "A", "message": "older", "category": "dev"},
        {"timestamp": "2026-03-22T16:00:00", "emoji": "B", "message": "newer", "category": "dev"},
    ], log)
    html = build_timeline_html(str(log))
    assert html.index("newer") < html.index("older")
```

- [ ] **Step 3: 테스트 실행 — 실패 확인**

```bash
python -m pytest tests/test_timeline_builder.py -v
```
예상: `ImportError: cannot import name 'build_timeline_html'`

- [ ] **Step 4: `timeline/builder.py` 구현**

```python
import json
from datetime import datetime

KNOWN_CATEGORIES = {'planning', 'dev', 'design', 'fix', 'deploy', 'other'}

_EMPTY_MSG = '<p style="color:#767579;text-align:center;font-size:.875rem;">기록된 대화가 없습니다.</p>'


def build_timeline_html(log_path: str) -> str:
    """log.json을 읽어 타임라인 HTML 문자열 반환."""
    try:
        with open(log_path, encoding='utf-8') as f:
            entries = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return _EMPTY_MSG

    if not entries:
        return _EMPTY_MSG

    entries = sorted(entries, key=lambda e: e.get('timestamp', ''), reverse=True)

    items = []
    for i, e in enumerate(entries):
        emoji    = e.get('emoji', '📌')
        message  = e.get('message', '')
        category = e.get('category', 'other')
        if category not in KNOWN_CATEGORIES:
            category = 'other'

        try:
            dt = datetime.fromisoformat(e.get('timestamp', ''))
            date_str = dt.strftime('%Y-%m-%d %H:%M')
        except (ValueError, TypeError):
            date_str = e.get('timestamp', '')

        is_last   = (i == len(entries) - 1)
        connector = '' if is_last else '<div class="tl-connector"></div>'

        items.append(f"""<div class="tl-item">
          <div class="tl-spine">
            <div class="tl-dot">{emoji}</div>
            {connector}
          </div>
          <div class="tl-content">
            <div class="tl-meta">
              <span class="tl-date">{date_str}</span>
              <span class="tl-badge tl-badge--{category}">{category}</span>
            </div>
            <p class="tl-msg">{message}</p>
          </div>
        </div>""")

    return f'<div class="tl-list">{"".join(items)}</div>'
```

- [ ] **Step 5: 테스트 실행 — 통과 확인**

```bash
python -m pytest tests/test_timeline_builder.py -v
```
예상: 9개 PASS

- [ ] **Step 6: 전체 테스트 이상 없는지 확인**

```bash
python -m pytest tests/ -q
```
예상: 기존 61개 + 신규 9개 = 70개 PASS

- [ ] **Step 7: 커밋**

```bash
git add timeline/__init__.py timeline/builder.py tests/test_timeline_builder.py
git commit -m "feat: add build_timeline_html() with TDD (9 tests)"
```

---

### Task 2: `pages/about.py` — 타임라인 주입 + height 업데이트

**Files:**
- Modify: `pages/about.py`

- [ ] **Step 1: import 추가 및 함수 호출 코드 삽입**

현재 `pages/about.py`:
```python
import os
import streamlit as st
import streamlit.components.v1 as components
```

변경 후:
```python
import os
import streamlit as st
import streamlit.components.v1 as components
from timeline.builder import build_timeline_html
```

파일 하단 `components.html(html_content, height=4200, scrolling=True)` 직전에 추가:
```python
log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "timeline", "log.json")
html_content = html_content.replace('<!-- TIMELINE_PLACEHOLDER -->', build_timeline_html(log_path))
```

`height=4200` → `height=5500` 으로 변경.

- [ ] **Step 2: 커밋**

```bash
git add pages/about.py
git commit -m "feat: inject timeline into about page from log.json"
```

---

### Task 3: `static/about.html` — 타임라인 CSS + 섹션 추가

**Files:**
- Modify: `static/about.html`

- [ ] **Step 1: 타임라인 CSS를 `<style>` 블록 끝에 추가**

`</style>` 바로 앞에 삽입:

```css
/* Timeline */
.tl-list { display:flex; flex-direction:column; gap:0; }
.tl-item { display:flex; gap:1rem; }
.tl-spine { display:flex; flex-direction:column; align-items:center; flex-shrink:0; }
.tl-dot {
  width:2rem; height:2rem; border-radius:9999px;
  background:rgba(90,248,251,.1); border:1px solid rgba(90,248,251,.3);
  display:flex; align-items:center; justify-content:center;
  font-size:.9rem; flex-shrink:0;
}
.tl-connector { width:1px; background:rgba(90,248,251,.2); flex:1; min-height:1.5rem; }
.tl-content { padding-bottom:1.5rem; flex:1; }
.tl-meta { display:flex; align-items:center; gap:.5rem; margin-bottom:.25rem; flex-wrap:wrap; }
.tl-date { font-size:.72rem; color:#767579; font-family:'Space Grotesk',monospace; }
.tl-badge { font-size:.68rem; font-family:'Space Grotesk',monospace; padding:.1rem .5rem; border-radius:9999px; }
.tl-badge--planning { background:rgba(255,231,146,.08); border:1px solid rgba(255,231,146,.3); color:#ffe792; }
.tl-badge--dev      { background:rgba(90,248,251,.08);  border:1px solid rgba(90,248,251,.3);  color:#5af8fb; }
.tl-badge--design   { background:rgba(204,151,255,.08); border:1px solid rgba(204,151,255,.3); color:#cc97ff; }
.tl-badge--fix      { background:rgba(255,115,81,.08);  border:1px solid rgba(255,115,81,.3);  color:#ff7351; }
.tl-badge--deploy   { background:rgba(90,248,251,.08);  border:1px solid rgba(90,248,251,.3);  color:#5af8fb; }
.tl-badge--other    { background:rgba(118,117,121,.08); border:1px solid rgba(118,117,121,.3); color:#767579; }
.tl-msg { font-size:.85rem; color:rgba(243,240,244,.8); line-height:1.5; }
```

- [ ] **Step 2: 타임라인 섹션을 `<!-- ── 링크 -->` 바로 앞에 삽입**

```html
<!-- ── 타임라인 ──────────────────────────────────────────── -->
<section id="timeline" class="py-16 px-6" style="background-color:rgba(25,25,29,.3)">
  <div class="max-w-3xl mx-auto">
    <h2 class="text-3xl font-headline font-semibold text-primary glow-gold mb-12 text-center">
      🤖 Claude 협업 타임라인
    </h2>
    <!-- TIMELINE_PLACEHOLDER -->
  </div>
</section>
```

- [ ] **Step 3: 커밋**

```bash
git add static/about.html
git commit -m "feat: add timeline section and CSS to about.html"
```

---

### Task 4: `static/about.html` — Step 8 · 9 추가

**Files:**
- Modify: `static/about.html`

- [ ] **Step 1: 기존 Step 7 블록 끝(`</div>` 닫힘 이후)에 Step 8 추가**

Step 7의 `<div class="w-10 h-10"></div>` (connector 없는 마지막 스텝 표시) 를
`<div class="step-connector h-16 flex-shrink-0"></div>` 로 교체한 뒤
Step 8 블록 추가:

```html
<!-- Step 7의 connector를 살려야 하므로 -->
<!-- 기존: <div class="w-10 h-10"></div> -->
<!-- 변경: <div class="step-connector h-16 flex-shrink-0"></div> -->

<div class="flex gap-6">
  <div class="flex flex-col items-center">
    <div class="w-10 h-10 rounded-full bg-secondary/20 border border-secondary/40 flex items-center justify-center text-secondary font-headline font-bold text-sm flex-shrink-0">
      8</div>
    <div class="step-connector h-16 flex-shrink-0"></div>
  </div>
  <div class="pb-8">
    <p class="text-xs text-muted mb-1 font-body">Fix</p>
    <h4 class="font-headline font-semibold text-on-surface mb-1">소개 페이지 디버깅 & 완성</h4>
    <p class="text-sm text-muted">Streamlit static 서빙의 text/plain 이슈를 발견하고 <code style="color:#5af8fb">pages/about.py</code>로 전환했습니다. Tailwind CDN · Mermaid CDN을 제거하고 인라인 CSS와 순수 HTML 도식으로 교체, <code style="color:#5af8fb">index.html</code> → <code style="color:#5af8fb">about.html</code>로 이름을 변경했습니다.</p>
    <div style="margin-top:.5rem;display:flex;flex-wrap:wrap;gap:.35rem;">
      <span class="skill-badge">superpowers:systematic-debugging</span>
    </div>
  </div>
</div>

<div class="flex gap-6">
  <div class="flex flex-col items-center">
    <div class="w-10 h-10 rounded-full bg-tertiary/20 border border-tertiary/40 flex items-center justify-center text-tertiary font-headline font-bold text-sm flex-shrink-0">
      9</div>
    <div class="w-10 h-10"></div>
  </div>
  <div class="pb-8">
    <p class="text-xs text-muted mb-1 font-body">Improvement</p>
    <h4 class="font-headline font-semibold text-on-surface mb-1">코드 리뷰 & 리팩토링</h4>
    <p class="text-sm text-muted">불필요 파일 3개 삭제, <code style="color:#5af8fb">app.py</code> dead import 제거, Open-Meteo API <code style="color:#5af8fb">timeout=10</code> 추가, 구현 과정 스킬 배지 UI 추가, 테스트 61개 통과.</p>
    <div style="margin-top:.5rem;display:flex;flex-wrap:wrap;gap:.35rem;">
      <span class="skill-badge">superpowers:requesting-code-review</span>
      <span class="skill-badge">superpowers:receiving-code-review</span>
    </div>
  </div>
</div>
```

- [ ] **Step 2: 커밋**

```bash
git add static/about.html
git commit -m "feat: add Step 8 and 9 to implementation timeline in about.html"
```

---

### Task 5: `app.py` — 푸터 타임라인 링크 활성화

**Files:**
- Modify: `app.py` (line 126-129)

- [ ] **Step 1: `<span>` → `<a>` 교체**

현재:
```html
<span style="color: #48474b; cursor: default;"
   title="Claude와의 대화 타임라인 — 준비 중">
    🤖 Claude 협업 타임라인 (준비 중)
</span>
```

변경 후:
```html
<a href="/about#timeline" target="_blank"
   style="color: #5af8fb; text-decoration: none;">
    🤖 Claude 협업 타임라인
</a>
```

- [ ] **Step 2: 전체 테스트 최종 확인**

```bash
python -m pytest tests/ -q
```
예상: 70개 PASS

- [ ] **Step 3: 최종 커밋**

```bash
git add app.py
git commit -m "feat: activate Claude timeline link in footer"
```
