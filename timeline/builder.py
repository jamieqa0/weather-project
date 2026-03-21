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
