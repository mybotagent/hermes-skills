#!/usr/bin/env python3
"""
wikilink-audit.py — Wiki wikilink/markdown link health audit

Findings (per file):
  - BROKEN:     target file does not exist (and is not detected as cross-domain)
  - CROSSDOM:   target matches a cross-domain suffix pattern (-hub, -strategy, ...)
                AND/OR sits in a "Related Wikis" / "Cross-Domain" section,
                BUT only if the file does not exist locally (P12)
  - BARENAME:   target resolves via basename lookup, but is referenced as a bare
                name without its directory prefix (e.g. [[aiprofit]] where the
                file lives at people/aiprofit.md)
  - MDEXT:      target has an explicit `.md` extension (e.g. [[foo.md]]) which
                the real resolver would treat as `foo.md.md` → BROKEN. Auto-fix:
                strip the trailing .md, preserve anchor if present.
  - OK:         link resolves to an existing file

P12 (2026-07-06): A locally-existing file is NEVER classified as cross-domain
even if its name ends in a cross-domain suffix. Example:
  [[solopreneur/upwork-strategy]]   →   RESOLVED (solopreneur/upwork-strategy.md exists)
  [[macro-strategy]]                →   CROSSDOM (macro-strategy.md does NOT exist locally)
The `is_cross_domain()` function now takes `wiki: Path` and short-circuits to
False if the target resolves locally.

Usage:
  python3 wikilink-audit.py [WIKI_ROOT]

Default WIKI_ROOT: ~/.hermes/wiki

Exit code: 0 if no BROKEN, 1 otherwise. CROSSDOM / BARENAME / MDEXT are
reported but do not affect the exit code (they require human judgment or
are auto-fixable).
"""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SKIP_DIRS = {"logs", "trade-pipeline", "subagents-library", ".git"}
SKIP_FILES = {"index.md", "AGENTS.md", "SCHEMA.md", "README.md"}

# Cross-domain signals (P7)
CROSS_DOMAIN_SUFFIXES = ("-hub", "-strategy", "-indicators-hub", "-calendar-hub")
CROSS_DOMAIN_SECTIONS = (
    "related wikis",
    "cross-domain",
    "external wikis",
    "see also",
    "cross domain",
)

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_cross_domain(target: str, lines: list[str], line_no: int, wiki: Path) -> bool:
    """Check if a wikilink target is an intentional cross-domain reference.

    P7 signals (any one is enough):
      1. Suffix matches (e.g. -hub, -strategy)
      2. Link sits in a "Related Wikis" / "Cross-Domain" section header

    P12 (2026-07-06): existence check is MANDATORY first.
    If `wiki/<target>.md` exists locally, the link is resolved regardless of
    any cross-domain suffix — never classify a locally-existing file as
    cross-domain. Example: `[[solopreneur/upwork-strategy]]` ends in
    `-strategy` but the file `solopreneur/upwork-strategy.md` lives in this
    wiki, so it's resolved-local, NOT cross-domain.
    """
    # P12: local existence check FIRST — short-circuit on resolve
    if (wiki / (target + ".md")).exists():
        return False

    # Suffix signal (only meaningful when local doesn't exist)
    if any(target.endswith(s) for s in CROSS_DOMAIN_SUFFIXES):
        return True
    # Section signal: look back to most recent heading
    for i in range(line_no, -1, -1):
        line = lines[i].lstrip()
        if line.startswith("#"):
            return any(sec in line.lower() for sec in CROSS_DOMAIN_SECTIONS)
    return False


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

def collect_files(wiki: Path) -> list[Path]:
    out: list[Path] = []
    for root, dirs, files in os.walk(wiki):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".md"):
                out.append(Path(root) / f)
    return sorted(out)


def build_basename_index(files: list[Path], wiki: Path) -> dict[str, list[str]]:
    idx: dict[str, list[str]] = defaultdict(list)
    for f in files:
        rel = str(f.relative_to(wiki))
        if f.stem not in idx:
            idx[f.stem] = [rel]
        else:
            idx[f.stem].append(rel)
    return idx


def audit_file(
    f: Path,
    wiki: Path,
    basename_idx: dict[str, list[str]],
) -> dict:
    rel = str(f.relative_to(wiki))
    content = f.read_text(encoding="utf-8")
    # P8: strip code blocks first, then inline code
    content_no_code = CODE_BLOCK_RE.sub("", content)
    content_no_code = INLINE_CODE_RE.sub("", content_no_code)
    lines = content_no_code.split("\n")

    findings = {
        "broken_md": [],
        "broken_wl": [],
        "crossdom": [],
        "barename": [],
        "mdext": [],  # P10: explicit .md extension
    }

    # Markdown links
    for m in LINK_RE.finditer(content_no_code):
        target = m.group(2).split("#")[0]
        if not target or target.startswith(("http", "mailto:")):
            continue
        resolved = (f.parent / target).resolve()
        if not resolved.exists():
            findings["broken_md"].append((m.group(0), target))

    # Wikilinks
    line_offsets = [0]
    for line in lines[:-1]:
        line_offsets.append(line_offsets[-1] + len(line) + 1)

    for m in WIKILINK_RE.finditer(content_no_code):
        raw_full = m.group(1).strip()
        if not raw_full:
            continue
        # Preserve anchor; strip it for path lookup
        anchor = ""
        body = raw_full
        if "#" in raw_full:
            body, anchor = raw_full.split("#", 1)
            anchor = "#" + anchor

        # Which line are we on?
        line_no = 0
        for i, off in enumerate(line_offsets):
            if off > m.start():
                line_no = i - 1
                break
        else:
            line_no = len(lines) - 1

        if is_cross_domain(body, lines, line_no, wiki):
            findings["crossdom"].append((m.group(0), raw_full))
            continue

        # P10 fix: always normalize by stripping trailing .md BEFORE lookup
        # (regardless of whether it was present originally)
        normalized = body[:-3] if body.endswith(".md") else body

        candidate = wiki / (normalized + ".md")
        if candidate.exists():
            # Check if the ORIGINAL target had a .md that needs stripping
            if body != normalized:
                # MDEXT: original had .md, stripped version resolves
                findings["mdext"].append((m.group(0), raw_full, normalized + anchor))
            # else: OK, no action needed
            continue

        # P9: bare-name that resolves via basename lookup
        if body in basename_idx:
            findings["barename"].append((m.group(0), body, basename_idx[body][0]))
            continue

        findings["broken_wl"].append((m.group(0), raw_full))

    return {"rel": rel, **findings}


def main() -> int:
    wiki = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / ".hermes/wiki"
    if not wiki.is_dir():
        print(f"ERROR: {wiki} is not a directory", file=sys.stderr)
        return 2

    files = [f for f in collect_files(wiki) if f.name not in SKIP_FILES]
    basename_idx = build_basename_index(files, wiki)

    summary = defaultdict(int)
    print(f"Auditing {len(files)} .md files in {wiki}\n")
    print(f"{'File':<55} {'MD':<4} {'WL':<4} {'CD':<4} {'BN':<4} {'MDX':<4}")
    print("-" * 79)

    for f in files:
        r = audit_file(f, wiki, basename_idx)
        n_md = len(r["broken_md"])
        n_wl = len(r["broken_wl"])
        n_cd = len(r["crossdom"])
        n_bn = len(r["barename"])
        n_mx = len(r["mdext"])
        summary["md"] += n_md
        summary["wl"] += n_wl
        summary["cd"] += n_cd
        summary["bn"] += n_bn
        summary["mx"] += n_mx

        if n_md or n_wl or n_bn or n_mx:
            print(f"  {r['rel']:<53} {n_md:<4} {n_wl:<4} {n_cd:<4} {n_bn:<4} {n_mx:<4}")
            for link, tgt in r["broken_md"]:
                print(f"      MD BROKEN:   {link} -> {tgt}")
            for link, tgt in r["broken_wl"]:
                print(f"      WL BROKEN:   {link} -> [[{tgt}]]")
            for link, tgt, real_path in r["barename"]:
                fix = real_path[:-3] if real_path.endswith(".md") else real_path
                print(f"      WL BARENAME: {link}  ->  fix to [[{fix}]]")
            for link, orig, fix in r["mdext"]:
                print(f"      WL MDEXT:    {link}  ->  fix to [[{fix}]]")

    print("-" * 79)
    print(f"  {'TOTAL':<53} {summary['md']:<4} {summary['wl']:<4} {summary['cd']:<4} {summary['bn']:<4} {summary['mx']:<4}")
    print()
    print(f"  Cross-domain (intentional, P7):  {summary['cd']}")
    print(f"  Bare-name (auto-fixable, P9):    {summary['bn']}")
    print(f"  .md extension (auto-fixable, P10): {summary['mx']}")
    print(f"  Broken MD links:                 {summary['md']}")
    print(f"  Broken wikilinks:                {summary['wl']}")

    return 1 if (summary["md"] or summary["wl"]) else 0


if __name__ == "__main__":
    sys.exit(main())
