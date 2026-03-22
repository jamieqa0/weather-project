"""
문정동 출근 프로젝트 타임라인 기록 도구

사용법:
  python log.py "메시지"
  python log.py "메시지" --emoji 🎉
  python log.py "메시지" --category deploy
  python log.py --list
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(__file__).parent / "timeline" / "log.json"
CATEGORIES = ["planning", "design", "dev", "fix", "deploy", "other"]


def load_log():
    if LOG_PATH.exists():
        with open(LOG_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_log(entries):
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def add_entry(message, emoji="📌", category="dev"):
    entries = load_log()
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "emoji": emoji,
        "message": message,
        "category": category,
    }
    entries.append(entry)
    save_log(entries)
    print(f"✅ 기록됨: [{entry['timestamp']}] {emoji} {message}")


def list_entries():
    entries = load_log()
    if not entries:
        print("기록 없음")
        return
    for e in entries:
        print(f"  {e['timestamp']}  {e['emoji']}  {e['message']}  [{e['category']}]")


def main():
    parser = argparse.ArgumentParser(description="타임라인 기록 도구")
    parser.add_argument("message", nargs="?", help="기록할 메시지")
    parser.add_argument("--emoji", default="📌", help="이모지 (기본: 📌)")
    parser.add_argument("--category", default="dev", choices=CATEGORIES,
                        help=f"카테고리: {', '.join(CATEGORIES)}")
    parser.add_argument("--list", action="store_true", help="전체 기록 출력")

    args = parser.parse_args()

    if args.list:
        list_entries()
    elif args.message:
        add_entry(args.message, emoji=args.emoji, category=args.category)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
