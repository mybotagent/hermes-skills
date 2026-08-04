#!/usr/bin/env python3
"""kanban_health.py — kanban 보드 헬스 체크 (중복/스테일 탐지)

daily-task-suggestion cron에서 사용. cron 모드에서는 execute_code와
파이프-to-인터프리터(| jq, | python3 -c)가 차단되므로 반드시 파일 기반으로 실행:

  hermes kanban list --json > /tmp/kanban_list.json
  python3 scripts/kanban_health.py /tmp/kanban_list.json [--min-stale-days 7]

Output:
  - 상태별 카운트 (todo/ready/in_progress/blocked/done/backlog)
  - 열린 태스크 중 중복 title (count>1) → backlog cleanup 제안 근거
  - 스테일 ready 집계 (>= min-stale-days, 연령 버킷 + P0/P1 목록) → 일괄 archive 제안 근거
  - todo 태스크 title 요약 (중복 여부 파악)

주의: kanban JSON의 created_at은 ISO-8601 문자열이 아니라 Unix epoch(int)이다.
"""
import json
import sys
import time
from collections import Counter


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/kanban_list.json"
    min_stale = 7
    for i, a in enumerate(sys.argv):
        if a == "--min-stale-days" and i + 1 < len(sys.argv):
            min_stale = int(sys.argv[i + 1])

    data = json.load(open(path))
    open_tasks = [t for t in data if t["status"] in ("todo", "ready", "in_progress", "blocked")]
    now = time.time()

    def age_days(t):
        for k in ("created_at", "started_at"):
            v = t.get(k)
            if isinstance(v, (int, float)) and v:
                return (now - v) / 86400
        return None

    print("=== STATUS COUNTS ===")
    for s, c in Counter(t["status"] for t in data).most_common():
        print(f"  {s}: {c}")

    print("\n=== DUPLICATE TITLES (open, count>1) ===")
    titles = Counter(t["title"] for t in open_tasks)
    dup = {title: c for title, c in titles.items() if c > 1}
    if dup:
        for title, c in dup.most_common():
            print(f"  {c}x :: {title[:100]}")
    else:
        print("  (none)")

    ready = [t for t in open_tasks if t["status"] == "ready"]
    stale = [t for t in ready if (age_days(t) or 999) >= min_stale]
    print(f"\n=== STALE READY (>={min_stale}d): {len(stale)}/{len(ready)} ===")
    buckets = Counter()
    for t in ready:
        a = age_days(t) or 999
        if a >= 30:
            buckets["30d+"] += 1
        elif a >= 14:
            buckets["14-30d"] += 1
        elif a >= 7:
            buckets["7-14d"] += 1
        else:
            buckets["<7d"] += 1
    print("  age buckets:", dict(buckets))
    p1_stale = [t for t in stale if t.get("priority") in (0, 1)]
    print(f"  stale P0/P1: {len(p1_stale)}")
    for t in p1_stale[:20]:
        print(f"    {t['id']} P{t.get('priority')} {int(age_days(t))}d :: {t['title'][:70]}")

    todo = [t for t in open_tasks if t["status"] == "todo"]
    print(f"\n=== TODO: {len(todo)} ===")
    for title, c in Counter(t["title"] for t in todo).most_common(10):
        print(f"  {c}x :: {title[:90]}")


if __name__ == "__main__":
    main()
