#!/usr/bin/env python3
"""
index-md-audit.py — P14 (2026-07-08), P17 (2026-07-13)

Detects index.md registration gaps using THREE patterns, not just markdown links.
P17 keeps exclusions consistent across overlapping regex passes so root schema links
(e.g. AGENTS.md/SCHEMA.md) are not re-added by PATTERN B+C after PATTERN A skips them:

  PATTERN A — markdown link:  [text](path/to/file.md) — desc
  PATTERN B — plain text bullet:  - name (path/to/file.md) — desc   ← raw/* section uses this
  PATTERN C — bare name in parens:  (path/to/file.md)                ← most common in our wiki

Why this matters:
  Previous 2a diff step only matched PATTERN A, producing 4 false positives
  on 2026-07-08 (raw/hermes-agent-2026-07-07.md, raw/llm-wiki-pattern-2026-07-07.md,
  raw/llm-wiki-vs-rag-2026-07-07.md, raw/memory-pipeline-design-2026-07-02.md).
  All 4 were plain-text bullets like:
      - hermes-agent (raw/hermes-agent-2026-07-07.md) — Hermes Agent 본체 정의/속성
  They were correctly registered, but markdown-link regex couldn't see them.

Usage:
  python3 index-md-audit.py [WIKI_ROOT]   # default: ~/.hermes/wiki
  exit 0 — always (this is an info/audit script, not a fail-fast gate)

Output:
  - Per-file detection breakdown (which pattern matched)
  - Files NOT in index.md (the real missing ones)
  - Files in index.md but missing on disk (dead links)
  - "Unregistered" list excluding snapshots/sync/raw-sync/archive paths
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Config
EXCLUDE_PARTS = (".git", "logs", "subagents-library")
SKIP_FILES = ("AGENTS.md", "README.md", "SCHEMA.md", "index.md")
SNAPSHOT_HINTS = ("snapshots", "sync", "archive", "_archive", "temp", "tmp")

# Pattern A: markdown link [text](path)
PAT_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
# Pattern B+C: bare path in parens  (path/to/file.md)  — also matches "name (path) — desc"
PAT_PAREN_PATH = re.compile(r"\(([a-zA-Z0-9_\-./]+\.md)(?:#[^)]*)?\)")


def collect_index_targets(wiki: Path) -> set[str]:
    """Return set of wiki-relative .md paths referenced in wiki/index.md (PAT A + B+C)."""
    idx = wiki / "index.md"
    if not idx.exists():
        return set()
    text = idx.read_text()
    targets: set[str] = set()

    # Pattern A: [text](path)
    for m in PAT_MD_LINK.finditer(text):
        path = m.group(2)
        if path.startswith(("http", "https", "mailto:", "#")):
            continue
        path = path.split("#")[0].strip()
        if not path or path.startswith(("AGENTS", "README", "SCHEMA")):
            # bare root files like [hermes-trading-hub](hermes-trading-hub.md)
            if path.startswith(("AGENTS", "README", "SCHEMA")):
                continue
        if path.endswith(".md"):
            targets.add(path)

    # Pattern B+C: (path/to/file.md)
    # This regex also sees the destination part of markdown links such as
    # [AGENTS.md](AGENTS.md), so re-apply the root schema/landing exclusion here.
    # Otherwise PAT A correctly skips it, then PAT B+C adds it back and reports
    # a false "dead link" because collect_actual_files() intentionally excludes it.
    for m in PAT_PAREN_PATH.finditer(text):
        path = m.group(1).strip()
        if path in SKIP_FILES:
            continue
        if path.endswith(".md"):
            targets.add(path)

    return targets


def collect_actual_files(wiki: Path) -> set[str]:
    """Return set of wiki-relative .md paths that physically exist (excluding submodules)."""
    out: set[str] = set()
    for p in wiki.rglob("*.md"):
        if any(part in p.parts for part in EXCLUDE_PARTS):
            continue
        rel = p.relative_to(wiki).as_posix()
        if rel in SKIP_FILES:
            continue
        out.add(rel)
    return out


def is_snapshot(rel: str) -> bool:
    return any(hint in rel for hint in SNAPSHOT_HINTS)


def main() -> int:
    wiki = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / ".hermes/wiki"
    if not wiki.exists():
        print(f"WIKI_ROOT not found: {wiki}", file=sys.stderr)
        return 2

    in_index = collect_index_targets(wiki)
    actual = collect_actual_files(wiki)

    in_index_no_file = in_index - actual
    files_not_in_index = actual - in_index

    print(f"=== index-md-audit: {wiki} ===")
    print(f"index.md registered:  {len(in_index)} files (PAT A + B+C combined)")
    print(f"actual .md files:     {len(actual)} (excluding submodules + AGENTS/README/SCHEMA/index)")
    print()

    print("--- in index.md but file missing (dead link) ---")
    if in_index_no_file:
        for f in sorted(in_index_no_file):
            print(f"  - {f}")
    else:
        print("  (none)")

    print()
    print("--- file exists but NOT in index.md ---")
    if files_not_in_index:
        # separate true-missing from snapshot/archive
        real_missing = sorted(f for f in files_not_in_index if not is_snapshot(f))
        snapshotted = sorted(f for f in files_not_in_index if is_snapshot(f))
        if real_missing:
            print("  REAL MISSING (likely need registration):")
            for f in real_missing:
                print(f"  - {f}")
        if snapshotted:
            print()
            print("  SNAPSHOT/ARCHIVE (expected to be excluded — verify intent):")
            for f in snapshotted:
                print(f"  - {f}")
    else:
        print("  (none — all files registered)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
