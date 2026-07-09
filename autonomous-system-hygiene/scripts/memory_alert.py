#!/usr/bin/env python3
"""
memory_alert.py — 정확한 메모리 사용량 측정

memory.md 2,200 chars cap (codepoint, NOT byte). UTF-8 byte size는 chars * ~1.32
(Korean text) 로 ~+32% 오차. 정확히 하려면 wc -m (multibyte safe codepoint count) 사용.

2026-07-07 검증: wc -m 결과 == memory tool 응답 (2,191 chars) 완전 일치. ±0% 오차.

Usage:
  python3 memory_alert.py check     # 측정 → 90%↑ 시 exit 1 (alert)
  python3 memory_alert.py stats     # 상세 통계
  python3 memory_alert.py fix       # 정확한 측정 스크립트 위치 출력
"""

import os
import sys
import subprocess
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"
MEMORY_FILE = HERMES_HOME / "memories" / "MEMORY.md"
USER_FILE = HERMES_HOME / "memories" / "USER.md"
CAP_CHARS = 2200


def count_chars(path: Path) -> int:
    """wc -m: count characters (multibyte safe, codepoint count)."""
    if not path.exists():
        return 0
    try:
        result = subprocess.run(
            ["wc", "-m", str(path)],
            capture_output=True, text=True, timeout=5
        )
        # Output: "<count> <filename>"
        parts = result.stdout.strip().split()
        return int(parts[0]) if parts else 0
    except Exception:
        return 0


def count_bytes(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("check", "stats", "fix"):
        print(__doc__)
        sys.exit(2)

    cmd = sys.argv[1]

    if cmd == "fix":
        print(f"memory_alert.py — 정확한 측정:")
        print(f"  CAP: {CAP_CHARS} chars")
        print(f"  memory file: {MEMORY_FILE}")
        print(f"  user file: {USER_FILE}")
        print(f"  measure: wc -m (codepoint count, NOT byte count)")
        return

    mem_chars = count_chars(MEMORY_FILE)
    mem_bytes = count_bytes(MEMORY_FILE)
    user_chars = count_chars(USER_FILE)
    user_bytes = count_bytes(USER_FILE)

    mem_pct = (mem_chars / CAP_CHARS) * 100

    if cmd == "check":
        if mem_pct >= 90:
            print(f"⚠ MEMORY ALERT: {mem_chars}/{CAP_CHARS} chars ({mem_pct:.1f}%)")
            sys.exit(1)
        else:
            print(f"OK: {mem_chars}/{CAP_CHARS} chars ({mem_pct:.1f}%)")
            sys.exit(0)

    if cmd == "stats":
        print(f"MEMORY.md: {mem_chars} chars / {mem_bytes} bytes ({mem_pct:.1f}% of {CAP_CHARS})")
        print(f"USER.md:   {user_chars} chars / {user_bytes} bytes")
        print(f"Cap:       {CAP_CHARS} chars (memory.md only)")
        print(f"Ratio:     {mem_bytes/mem_chars:.2f} bytes/char (UTF-8 average)")


if __name__ == "__main__":
    main()