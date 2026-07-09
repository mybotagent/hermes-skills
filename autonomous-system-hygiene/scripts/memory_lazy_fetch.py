#!/usr/bin/env python3
"""
memory_lazy_fetch.py — memory.md fact → wiki 페이지 on-demand 로드 (lazy indexing)

memory.md의 § fact이 위키 페이지 링크를 가리키면, 해당 페이지를 읽어서
요약을 stdout으로 출력. memory에 들어가지 않은 상세 정보 lazy fetch.

사용법:
    python3 memory_lazy_fetch.py              # 모든 fact fetch (verbose)
    python3 memory_lazy_fetch.py --fact 5     # 단일 fact (#5)
    python3 memory_lazy_fetch.py --search deepseek  # 검색
    python3 memory_lazy_fetch.py --list       # 전체 fact 목록
"""
import argparse
import re
import sys
from pathlib import Path

WIKI_HOME = Path.home() / ".hermes" / "wiki"
MEMORY_FILE = Path.home() / ".hermes" / "memories" / "MEMORY.md"
MEMORY_MAP = Path.home() / ".mybotagent" / "memory-map" / "README.md"

# fact → wiki 경로 (MEMORY_MAP.md와 동기 필수)
FACT_MAP = {
    1: ("TZ/cron", "infra/cron-jobs.md"),
    2: ("SYS 단일소스", "architecture/ssot-single-source-of-truth.md"),
    3: ("API keys", "infra/environment.md"),
    4: ("매크로 6단계", "analysis/methodology.md"),
    5: ("watchlist 단일소스", "watchlist/README.md"),
    6: ("deepseek/GCal", "code/scripts.md"),
    7: ("Dashboard nginx", "architecture/how-to-use-hermes/06-messaging-platforms.md"),
    8: ("Linear API", "infra/environment.md"),
    9: ("스레드/설문", "infra/discord-gateway.md"),
    10: ("Bot IDs", "infra/bot-architecture.md"),
    11: ("Multi-bot 80%", "infra/bot-architecture.md"),
    12: ("5-stage verify", "architecture/5-stage-verify.md"),
    13: ("게이트웨이 fix", "infra/discord-gateway.md"),
    14: ("Speculation cascade", "architecture/speculation-cascade-rule.md"),
    15: ("Discord-only", "infra/discord-gateway.md"),
    16: ("user-style", "people/aiprofit.md"),
    17: ("GitHub PR 정책", "infra/github-pr-automation-policy.md"),
}


def fetch_page(wiki_path: str) -> str:
    """위키 페이지 본문 fetch (lazy)"""
    full = WIKI_HOME / wiki_path
    if not full.exists():
        return f"[NOT FOUND] {wiki_path}"
    try:
        text = full.read_text(encoding="utf-8")
        # frontmatter 제거
        body = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)
        return body[:500] + ("..." if len(body) > 500 else "")
    except Exception as e:
        return f"[ERROR] {e}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fact", type=int, help="단일 fact fetch")
    parser.add_argument("--search", help="검색 (대소문자 무시)")
    parser.add_argument("--list", action="store_true", help="전체 fact 목록")
    args = parser.parse_args()

    if args.list:
        for n, (label, path) in FACT_MAP.items():
            print(f"  {n:2d}. {label:25s} → {path}")
        return 0

    if args.fact:
        if args.fact not in FACT_MAP:
            print(f"[ERROR] fact #{args.fact} not in map", file=sys.stderr)
            return 1
        label, path = FACT_MAP[args.fact]
        print(f"=== Fact #{args.fact}: {label} ===")
        print(f"Path: {path}")
        print(f"---")
        print(fetch_page(path))
        return 0

    if args.search:
        q = args.search.lower()
        for n, (label, path) in FACT_MAP.items():
            if q in label.lower() or q in path.lower():
                print(f"  {n:2d}. {label} → {path}")
        return 0

    # 기본: 모든 fact 짧은 요약
    try:
        size = len(MEMORY_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        size = 0
    print(f"=== Memory Lazy Fetch ({len(FACT_MAP)} facts) ===")
    print(f"memory.md: {size} chars (lazy indexed)")
    print(f"---")
    for n, (label, path) in FACT_MAP.items():
        full = WIKI_HOME / path
        exists = "✓" if full.exists() else "✗"
        print(f"  {exists} {n:2d}. {label:25s} → {path}")
    print(f"---")
    print(f"Use --fact <N> to fetch, --search <q> to filter")
    return 0


if __name__ == "__main__":
    sys.exit(main())