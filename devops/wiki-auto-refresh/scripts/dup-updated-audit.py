#!/usr/bin/env python3
"""
dup-updated-audit.py — Detect duplicate `updated:` keys in YAML frontmatter.

Root cause of the pattern: an early version of auto-fill-dates.py inserted
`updated:` into frontmatter without detecting an existing `updated:` line in
multi-line frontmatter blocks (fixed in skill v1.16.0, but the damage to
already-written pages remained). Result: pages carry TWO `updated:` lines.

YAML semantics: last occurrence wins, so `yaml.safe_load` returns the last
value — meaning the *effective* date is unchanged if we simply drop the
earlier duplicate lines. This script therefore reports the duplicates and
offers --fix to remove all but the last occurrence, which is a
semantics-preserving cleanup.

Usage:
  python3 dup-updated-audit.py [WIKI_ROOT] [--fix]
    Default WIKI_ROOT = ~/.hermes/wiki

Exit codes:
  0 — informational (always 0, even when duplicates are found)
  1 — errors while applying --fix
"""
import glob
import re
import sys
from pathlib import Path

args = [a for a in sys.argv[1:] if not a.startswith('--')]
do_fix = '--fix' in sys.argv

wiki_root = Path(args[0]).expanduser().resolve() if args else Path.home() / ".hermes/wiki"
excluded_prefixes = ('logs/', 'subagents-library/', '.git/', 'trade-pipeline/')

FM_RE = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)
UPD_RE = re.compile(r'^updated:\s*(\d{4}-\d{2}-\d{2})\s*$', re.MULTILINE)

found = []
errors = []

files = sorted(glob.glob(str(wiki_root / '**' / '*.md'), recursive=True))
for path in files:
    p = Path(path)
    rel = str(p.relative_to(wiki_root))
    if any(rel.startswith(e) for e in excluded_prefixes):
        continue
    try:
        text = p.read_text(encoding='utf-8')
    except Exception as e:  # pragma: no cover
        errors.append(f'{rel}: read error: {e}')
        continue
    m = FM_RE.match(text)
    if not m:
        continue
    frontmatter = m.group(1)
    matches = UPD_RE.findall(frontmatter)
    if len(matches) <= 1:
        continue
    found.append((rel, matches, p))

print(f'=== dup-updated-audit: {wiki_root} ===')
print(f'pages scanned: {len(files)}')
print(f'duplicate `updated:` pages: {len(found)}')
print()

for rel, matches, _ in found:
    print(f'  {rel}: {matches}')

if do_fix:
    print()
    print('--- FIXING ---')
    for rel, matches, p in found:
        try:
            text = p.read_text(encoding='utf-8')
            m = FM_RE.match(text)
            frontmatter = m.group(1)
            lines = frontmatter.split('\n')
            # keep the LAST occurrence, drop earlier ones
            idxs = [i for i, l in enumerate(lines) if UPD_RE.match(l)]
            keep = idxs[-1]
            new_lines = [l for i, l in enumerate(lines) if i not in idxs[:-1]]
            new_frontmatter = '\n'.join(new_lines)
            new_text = text[:m.start(1)] + new_frontmatter + text[m.end(1):]
            p.write_text(new_text, encoding='utf-8')
            print(f'  fixed {rel}: kept {matches[-1]}, removed {len(idxs) - 1}')
        except Exception as e:
            errors.append(f'{rel}: fix error: {e}')
            print(f'  ! {rel}: {e}')

print()
if errors:
    print(f'ERRORS: {len(errors)}')
    for e in errors:
        print(f'  ! {e}')
    sys.exit(1)

print('Done. Verify with YAML parse + git diff --check + audits.')
