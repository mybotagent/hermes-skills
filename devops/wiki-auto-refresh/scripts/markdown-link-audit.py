#!/usr/bin/env python3
"""
markdown-link-audit.py — P11 sibling README cross-reference detector

Scans all .md files in ~/.hermes/wiki (excluding submodules) for broken markdown
links [text](path) and proposes auto-fixes:

  - bare-name in subdir  → ../<name>.md  (P11)
  - reports index.md dead links separately

Usage:
  python3 scripts/markdown-link-audit.py          # audit only
  python3 scripts/markdown-link-audit.py --fix    # audit + auto-fix (writes files)

Companion to scripts/wikilink-audit.py — this only checks markdown links, not wikilinks.
"""
import argparse
import re
import sys
from pathlib import Path

WIKI = Path.home() / ".hermes/wiki"
EXCLUDE = {"logs", "subagents-library", ".git", "trade-pipeline"}
SKIP_FILES = {"AGENTS.md", "SCHEMA.md", "index.md"}  # index.md has absolute refs

MD_LINK = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
CODE_BLOCK = re.compile(r'```[\s\S]*?```')
INLINE_CODE = re.compile(r'`[^`\n]+`')


def strip_code(content: str) -> str:
    content = CODE_BLOCK.sub('', content)
    content = INLINE_CODE.sub('', content)
    return content


def find_audit_files():
    files = []
    for p in WIKI.rglob('*.md'):
        rel = p.relative_to(WIKI)
        if any(part in EXCLUDE for part in rel.parts):
            continue
        if p.name in SKIP_FILES:
            continue
        files.append(p)
    return files


def audit(apply_fix: bool = False):
    broken = []
    fixed = []
    skipped = []

    for page in find_audit_files():
        content = page.read_text()
        stripped = strip_code(content)
        page_dir = page.parent
        page_rel = str(page.relative_to(WIKI))

        new_content = content
        page_had_change = False
        for m in MD_LINK.finditer(stripped):
            text, target = m.group(1), m.group(2)
            if target.startswith(('http://', 'https://', 'mailto:', '#')):
                continue
            target_path, _, anchor = target.partition('#')
            if not target_path:
                continue

            # Try resolving from current dir
            try:
                resolved = (page_dir / target_path).resolve()
            except (OSError, ValueError):
                resolved = None

            if resolved and resolved.exists():
                continue  # OK

            # Try parent dir (../)
            try:
                resolved_parent = (page_dir.parent / target_path).resolve()
            except (OSError, ValueError):
                resolved_parent = None

            if resolved_parent and resolved_parent.exists():
                new_target = f"../{target_path}" + (f"#{anchor}" if anchor else "")
                broken.append((page_rel, text, target, new_target, 'P11'))
                if apply_fix:
                    # Replace ONLY in the actual content (not stripped) — match the original [text](target) literally
                    old_str = f"[{text}]({target})"
                    new_str = f"[{text}]({new_target})"
                    if old_str in new_content:
                        new_content = new_content.replace(old_str, new_str)
                        page_had_change = True
                        fixed.append((page_rel, text, target, new_target))
            else:
                broken.append((page_rel, text, target, None, 'BROKEN'))

        if apply_fix and page_had_change:
            page.write_text(new_content)

    return broken, fixed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fix', action='store_true', help='apply auto-fix (modifies files)')
    args = ap.parse_args()

    broken, fixed = audit(apply_fix=args.fix)

    p11_fixes = [b for b in broken if b[4] == 'P11']
    real_broken = [b for b in broken if b[4] == 'BROKEN']

    print(f"=== markdown-link-audit ===")
    print(f"P11 (sibling cross-ref, ../ prefix): {len(p11_fixes)}")
    print(f"  Real broken: {len(real_broken)}")
    if p11_fixes:
        for page, text, target, new_target, _ in p11_fixes:
            print(f"  {page}: [{text}]({target}) -> [{text}]({new_target})")
    if real_broken:
        print()
        print("=== Real broken markdown links ===")
        for page, text, target, _, _ in real_broken:
            print(f"  {page}: [{text}]({target})")

    if args.fix and fixed:
        print()
        print(f"=== Applied {len(fixed)} fixes ===")
        sys.exit(0)
    elif p11_fixes and not args.fix:
        print()
        print("Run with --fix to apply.")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
