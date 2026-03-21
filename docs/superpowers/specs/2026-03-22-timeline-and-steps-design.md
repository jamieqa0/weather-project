# 설계 문서: Claude 협업 타임라인 + about.html Step 업데이트

**날짜:** 2026-03-22
**범위:** `static/about.html`, `pages/about.py`, `app.py`

---

## 목표

1. `about.html` 구현 과정에 Step 8 · 9 추가 (오늘 작업 반영)
2. `log.json` 데이터를 읽어 `about.html`에 Claude 협업 타임라인 섹션 시각화
3. 푸터의 "Claude 협업 타임라인 (준비 중)" → `/about#timeline` 앵커 링크로 교체

---

## 1. Step 8 · 9 추가 (`about.html`)

기존 Step 7 (Design, primary/20) 바로 아래에 추가.

**Step 8 — Fix: 소개 페이지 디버깅 & 완성**
색상: secondary(cyan), step-connector 있음
내용: Streamlit static 서빙이 HTML을 text/plain으로 서빙하는 문제 발견 →
`pages/about.py`로 전환, Tailwind CDN 제거 후 인라인 CSS로 교체,
Mermaid CDN 제거 후 순수 HTML/CSS 도식으로 교체, `index.html` → `about.html` 이름 변경
스킬 배지: `superpowers:systematic-debugging`

**Step 9 — Improvement: 코드 리뷰 & 리팩토링**
색상: tertiary(purple), step-connector 없음 (마지막 스텝)
내용: 불필요 파일 3개 삭제, `app.py` dead import 제거, Open-Meteo API `timeout=10` 추가, 스킬 배지 UI 추가
스킬 배지: `superpowers:requesting-code-review` · `superpowers:receiving-code-review`

---

## 2. Claude 협업 타임라인 섹션

### 2-1. 삽입 위치 (`about.html`)

`<!-- ── 아키텍처 -->` 섹션 끝(닫는 `</section>`) 직후,
`<!-- ── 링크 -->` 섹션 시작 직전에 삽입.

```html
<!-- ── 타임라인 ──────────────────────────────────────────── -->
<section id="timeline" class="py-16 px-6">
  <div class="max-w-3xl mx-auto">
    <h2 class="text-3xl font-headline font-semibold text-primary glow-gold mb-12 text-center">
      🤖 Claude 협업 타임라인
    </h2>
    <!-- TIMELINE_PLACEHOLDER -->
  </div>
</section>
```

### 2-2. 타임라인 CSS (`about.html` `<style>` 블록 추가)

```css
.tl-list { display: flex; flex-direction: column; gap: 0; }
.tl-item { display: flex; gap: 1rem; }
.tl-spine { display: flex; flex-direction: column; align-items: center; flex-shrink: 0; }
.tl-dot {
  width: 2rem; height: 2rem; border-radius: 9999px;
  background: rgba(90,248,251,.1); border: 1px solid rgba(90,248,251,.3);
  display: flex; align-items: center; justify-content: center;
  font-size: .9rem; flex-shrink: 0;
}
.tl-connector { width: 1px; background: rgba(90,248,251,.2); flex: 1; min-height: 1.5rem; }
.tl-content { padding-bottom: 1.5rem; flex: 1; }
.tl-meta { display: flex; align-items: center; gap: .5rem; margin-bottom: .25rem; flex-wrap: wrap; }
.tl-date { font-size: .72rem; color: #767579; font-family: 'Space Grotesk', monospace; }
.tl-badge {
  font-size: .68rem; font-family: 'Space Grotesk', monospace;
  padding: .1rem .5rem; border-radius: 9999px;
}
.tl-msg { font-size: .85rem; color: rgba(243,240,244,.8); line-height: 1.5; }
/* category별 배지 색상 */
.tl-badge--planning { background: rgba(255,231,146,.08); border: 1px solid rgba(255,231,146,.3); color: #ffe792; }
.tl-badge--dev      { background: rgba(90,248,251,.08);  border: 1px solid rgba(90,248,251,.3);  color: #5af8fb; }
.tl-badge--design   { background: rgba(204,151,255,.08); border: 1px solid rgba(204,151,255,.3); color: #cc97ff; }
.tl-badge--fix      { background: rgba(255,115,81,.08);  border: 1px solid rgba(255,115,81,.3);  color: #ff7351; }
.tl-badge--deploy   { background: rgba(90,248,251,.08);  border: 1px solid rgba(90,248,251,.3);  color: #5af8fb; }
.tl-badge--other    { background: rgba(118,117,121,.08); border: 1px solid rgba(118,117,121,.3); color: #767579; }
```

> `deploy`와 `dev` 배지 색상 동일(cyan) — 의도된 설계. 둘 다 실행/결과물 카테고리.

### 2-3. 항목 HTML 예시 (1개)

```html
<div class="tl-item">
  <div class="tl-spine">
    <div class="tl-dot">🚀</div>
    <div class="tl-connector"></div>   <!-- 마지막 항목은 생략 -->
  </div>
  <div class="tl-content">
    <div class="tl-meta">
      <span class="tl-date">2026-03-22 16:00</span>
      <span class="tl-badge tl-badge--dev">dev</span>
    </div>
    <p class="tl-msg">프로젝트 초기화 — git init, 폴더 구조, 샘플 데이터 생성</p>
  </div>
</div>
```

### 2-4. `pages/about.py` 변경

```python
import json
from datetime import datetime

KNOWN_CATEGORIES = {'planning', 'dev', 'design', 'fix', 'deploy', 'other'}


def build_timeline_html(log_path: str) -> str:
    """log.json을 읽어 타임라인 HTML 문자열 반환."""
    try:
        with open(log_path, encoding='utf-8') as f:
            entries = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        entries = []

    if not entries:
        return '<p style="color:#767579;text-align:center;">기록된 대화가 없습니다.</p>'

    # 최신순 정렬
    entries = sorted(entries, key=lambda e: e.get('timestamp', ''), reverse=True)

    items = []
    for i, e in enumerate(entries):
        emoji = e.get('emoji', '📌')
        message = e.get('message', '')
        category = e.get('category', 'other')
        if category not in KNOWN_CATEGORIES:
            category = 'other'

        # timestamp 파싱: "2026-03-22T14:00:00" → "2026-03-22 14:00"
        try:
            dt = datetime.fromisoformat(e.get('timestamp', ''))
            date_str = dt.strftime('%Y-%m-%d %H:%M')
        except ValueError:
            date_str = e.get('timestamp', '')

        is_last = (i == len(entries) - 1)
        connector = '' if is_last else '<div class="tl-connector"></div>'

        items.append(f"""
        <div class="tl-item">
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


# about.html 로드 후 placeholder 치환
log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "timeline", "log.json")
html_content = html_content.replace('<!-- TIMELINE_PLACEHOLDER -->', build_timeline_html(log_path))
```

**height 조정:** `components.html(height=...)` 값을 `5500`으로 증가.
타임라인 항목 수가 늘어날 경우 `about.py`에서 `len(entries) * 120 + 4500` 공식으로 동적 계산 가능하나, 현재 항목 수(~11개) 기준 5500 고정값으로 충분.

### 2-5. 푸터 링크 변경 (`app.py` line 126-129)

```python
# 변경 전
<span style="color: #48474b; cursor: default;"
   title="Claude와의 대화 타임라인 — 준비 중">
    🤖 Claude 협업 타임라인 (준비 중)
</span>

# 변경 후
<a href="/about#timeline" target="_blank"
   style="color: #5af8fb; text-decoration: none;">
    🤖 Claude 협업 타임라인
</a>
```

---

## 파일 변경 목록

| 파일 | 변경 내용 |
|------|----------|
| `static/about.html` | Step 8 · 9 추가, 타임라인 섹션 + placeholder 삽입, 타임라인 CSS 추가 |
| `pages/about.py` | `build_timeline_html()` 추가, placeholder 치환, height=5500 |
| `app.py` | 푸터 `<span>` → `<a href="/about#timeline">` 교체 |

---

## 엣지 케이스

| 상황 | 처리 |
|------|------|
| `log.json` 없음 또는 파싱 실패 | `"기록된 대화가 없습니다."` 메시지 표시 |
| 빈 배열 `[]` | 동일하게 빈 상태 메시지 |
| `category` 필드 누락 또는 미정의 값 | `'other'`(muted) 폴백 |
| `timestamp` 파싱 실패 | 원본 문자열 그대로 표시 |
| `emoji` / `message` 누락 | 각각 `'📌'` / `''` 기본값 |

---

## 테스트 시나리오

1. `/about` 접속 → 타임라인 섹션 렌더링 확인
2. `python log.py "테스트" --emoji 🧪` 후 `/about` 새로고침 → 자동 반영 확인
3. `/about#timeline` 직접 접속 → 앵커 이동 확인
4. 메인 대시보드 푸터 타임라인 링크 클릭 → `/about#timeline` 이동 확인
5. Step 8 · 9 스킬 배지 색상 및 connector 렌더링 확인
