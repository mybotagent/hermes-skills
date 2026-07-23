#!/usr/bin/env python3
"""
auto-fill-dates.py — Batch auto-fill `updated:` frontmatter for pages missing dates.

Scans all wiki pages for those without any date field (updated/created/inline),
gets the latest git commit date as fallback, and adds `updated: YYYY-MM-DD` to
frontmatter if the git date is <30 days old and the page is not in an
immutable directory (raw/, sync/, snapshots/, archive/).

Usage:
  python3 auto-fill-dates.py [WIKI_ROOT]
    Default WIKI_ROOT = ~/.hermes/wiki

Exit codes:
  0 — All done (or nothing to fill)
  0 — No errors (always informational)

Safety:
  - Respects P16: explicit updated/created/inline dates take priority
  - Respects immutable directories (raw/, sync/, snapshots/, archive/, _archive/)
  - Skips system files (index.md, AGENTS.md, SCHEMA.md, README.md)
  - Skips submodules (logs/, subagents-library/, trade-pipeline/)
  - Only fills pages with git log date <30 days
  - Validates YAML after insertion
"""
import re
import subprocess
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path

# --- Configuration ---
wiki_root = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path.home() / ".hermes/wiki"
excluded_prefixes = ('logs/', 'subagents-library/', '.git/', 'trade-pipeline/')
immutable_prefixes = ('raw/',)
immutable_patterns = ('/sync/', '/snapshots/', '/archive/', '/_archive/')
system_files = {'index.md', 'AGENTS.md', 'SCHEMA.md', 'README.md'}
STALE_THRESHOLD = 30  # days

filled = []
skipped = []
errors = []

for f in sorted(wiki_root.rglob('*.md')):
    rel = str(f.relative_to(wiki_root))

    # Skip submodules
    if any(rel.startswith(e) for e in excluded_prefixes):
        continue
    # Skip system files
    if f.name in system_files:
        continue
    # Skip immutable directories
    is_immutable = any(rel.startswith(e) for e in immutable_prefixes)
    for pat in immutable_patterns:
        if pat in '/' + rel:
            is_immutable = True
            break
    if is_immutable:
        skipped.append((rel, 'immutable'))
        continue

    text = f.read_text(encoding='utf-8')

    # Extract frontmatter block first (between --- and ---)
    fm_match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    has_updated = False
    has_created = False
    if fm_match:
        frontmatter = fm_match.group(1)
        has_updated = bool(re.search(
            r'^updated:\s*\d{4}-\d{2}-\d{2}\s*$', frontmatter, re.MULTILINE
        ))
        has_created = bool(re.search(
            r'^created:\s*\d{4}-\d{2}-\d{2}\s*$', frontmatter, re.MULTILINE
        ))
    has_inline = bool(re.search(
        r'\*\*Last updated:\*\*\s*\d{4}-\d{2}-\d{2}', text
    ))

    if has_updated or has_created or has_inline:
        continue  # Already has date info — P16: explicit dates are SSOT

    # Get latest git commit date
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cs', '--', rel],
            capture_output=True, text=True, cwd=wiki_root, timeout=10
        )
        git_date_str = result.stdout.strip()
    except subprocess.TimeoutExpired:
        git_date_str = ''
    except FileNotFoundError:
        git_date_str = ''

    if not git_date_str:
        # Fallback to file mtime
        mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
        git_date_str = mtime.strftime('%Y-%m-%d')

    # Check staleness
    try:
        git_date = datetime.strptime(git_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    except ValueError:
        skipped.append((rel, f'invalid date: {git_date_str}'))
        continue

    days_old = (datetime.now(timezone.utc) - git_date).days
    if days_old >= STALE_THRESHOLD:
        skipped.append((rel, f'{days_old}d old (manual review)'))
        continue

    # --- Insert updated: into frontmatter ---
    has_frontmatter = bool(re.match(r'^---\n', text))

    if has_frontmatter:
        lines = text.split('\n')
        new_lines = []
        in_fm = False
        added = False
        for i, line in enumerate(lines):
            if i == 0 and line.strip() == '---':
                in_fm = True
                new_lines.append(line)
                continue
            if in_fm and line.strip() == '---':
                if not added:
                    new_lines.append(f'updated: {git_date_str}')
                    added = True
                new_lines.append(line)
                in_fm = False
                continue
            if in_fm:
                new_lines.append(line)
                continue
            new_lines.append(line)
        new_text = '\n'.join(new_lines)
    else:
        # No frontmatter — insert before first heading (or at top)
        heading_match = re.search(r'^(#{1,6}\s)', text, re.MULTILINE)
        if heading_match:
            pos = heading_match.start()
            new_text = f'---\nupdated: {git_date_str}\n---\n\n' + text
        else:
            new_text = f'---\nupdated: {git_date_str}\n---\n\n' + text

    # Write back
    f.write_text(new_text, encoding='utf-8')
    filled.append((rel, git_date_str))

# --- Verify YAML of filled files ---
for rel, date in filled:
    try:
        text = (wiki_root / rel).read_text(encoding='utf-8')
        if text.startswith('---'):
            end = text.find('---', 3)
            if end != -1:
                yaml.safe_load(text[3:end])
    except yaml.YAMLError as e:
        errors.append(f'{rel}: YAML error after fill: {e}')
        # Rollback? For now just report.

# --- Report ---
print(f'Filled:     {len(filled)} pages')
print(f'Skipped:    {len(skipped)} pages')
print(f'Errors:     {len(errors)}')
print()

if filled:
    print('--- FILLED ---')
    for rel, date in sorted(filled):
        print(f'  + {date}  {rel}')

if skipped:
    print()
    print('--- SKIPPED ---')
    for rel, reason in sorted(skipped):
        print(f'  - {rel}  ({reason})')

if errors:
    print()
    print('--- ERRORS ---')
    for e in errors:
        print(f'  ! {e}')
    sys.exit(1)

print()
print('Done. Run git diff --check and 3 audit scripts to verify.')
