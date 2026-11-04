#!/usr/bin/env python3
"""Stale / no-date audit for the SOP wiki (2026-11-03).

Why this exists
---------------
The bundled audit scripts (wikilink/markdown-link/index-md/tag/logs-index)
do NOT report content freshness.  Until now every cron run recomputed
"stale (explicit date 30d+)" and "no date" with an ad-hoc inline python
snippet -- exactly the "audit 인라인 재작성 금지" anti-pattern the skill
warns about (P29).  This script makes the stale census a bundled,
deterministic, re-runnable probe.

Rules encoded (P16 / P14)
-------------------------
1. Date precedence (SSOT): frontmatter `updated:` > frontmatter `created:`
   > inline `**Last updated:**`.  Git activity NEVER overrides an explicit
   date -- a recent link-fix commit does not make a page fresh.
2. `updated:`/`created:`/inline date present and older than --days (default 30)
   => STALE (flag for human review, never auto-bumped).
3. No date field at all => NO_DATE.  Split into:
     - immutable (raw/, sync/, snapshots/, archive/, _archive/) -> expected,
       excluded from auto-fill by design (P16)
     - operational -> candidate for auto-fill-dates.py, but only if the
       git/mtime fallback is under --days
4. index.md / AGENTS.md / SCHEMA.md / README.md are excluded (schema/landing).
5. Submodule trees (logs/, subagents-library/, .git) are excluded (P22/P24).

Usage
-----
    python3 stale-audit.py [WIKI_ROOT] [--days 30]

Exit code is always 0 (informational, like the other bundled audits).
Prints a human-readable summary plus machine-parseable counts.
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

SKIP_FILES = {"index.md", "AGENTS.md", "SCHEMA.md", "README.md"}
SKIP_TOP = {"logs", "subagents-library", ".git"}
IMMUTABLE_PARTS = {"raw", "sync", "snapshots", "archive", "_archive"}

FM_UPDATED = re.compile(r"^updated:\s*(\d{4}-\d{2}-\d{2})", re.M)
FM_CREATED = re.compile(r"^created:\s*(\d{4}-\d{2}-\d{2})", re.M)
INLINE = re.compile(r"\*\*Last updated:\*\*\s*(\d{4}-\d{2}-\d{2})")


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    return m.group(1) if m else ""


def explicit_date(text):
    """Return (date, source_field) or (None, None).  Git is never consulted."""
    fm = frontmatter(text)
    m = FM_UPDATED.search(fm)
    if m:
        return datetime.date.fromisoformat(m.group(1)), "updated"
    m = FM_CREATED.search(fm)
    if m:
        return datetime.date.fromisoformat(m.group(1)), "created"
    m = INLINE.search(text)
    if m:
        return datetime.date.fromisoformat(m.group(1)), "inline"
    return None, None


def is_immutable(rel):
    return any(part in IMMUTABLE_PARTS for part in rel.parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wiki_root", nargs="?", default="~/.hermes/wiki")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--today", default=None, help="YYYY-MM-DD (for deterministic reruns)")
    args = ap.parse_args()

    wiki = Path(args.wiki_root).expanduser().resolve()
    if not wiki.is_dir():
        print(f"stale-audit: WIKI_ROOT not found: {wiki}")
        return 0

    today = (
        datetime.date.fromisoformat(args.today)
        if args.today
        else datetime.date.today()
    )

    stale = []          # (rel, date, age_days, field)
    no_date_ops = []    # operational pages with no date field
    no_date_imm = []    # immutable pages with no date field
    scanned = 0

    for p in sorted(wiki.rglob("*.md")):
        rel = p.relative_to(wiki)
        if rel.parts and rel.parts[0] in SKIP_TOP:
            continue
        if p.name in SKIP_FILES:
            continue
        scanned += 1
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        d, field = explicit_date(text)
        if d is None:
            (no_date_imm if is_immutable(rel) else no_date_ops).append(str(rel))
            continue
        age = (today - d).days
        if age >= args.days:
            stale.append((str(rel), str(d), age, field))

    stale.sort(key=lambda r: -r[2])

    print(f"=== stale-audit: {wiki} ===")
    print(f"today: {today}   threshold: {args.days}d   pages scanned: {scanned}")
    print()
    print(f"--- STALE (explicit date >= {args.days}d): {len(stale)} ---")
    for rel, d, age, field in stale:
        print(f"  {age:>4}d  {d}  [{field}]  {rel}")
    print()
    print(f"--- NO DATE (operational): {len(no_date_ops)} ---")
    for rel in no_date_ops:
        print(f"  {rel}")
    print()
    print(f"--- NO DATE (immutable, expected): {len(no_date_imm)} ---")
    for rel in no_date_imm:
        print(f"  {rel}")
    print()
    print(
        "SUMMARY: stale={} no_date_operational={} no_date_immutable={}".format(
            len(stale), len(no_date_ops), len(no_date_imm)
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
