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
