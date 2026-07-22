#!/usr/bin/env python3
"""
tag-audit.py — SCHEMA.md Lint ⑧ Tag Audit

Extracts the tag taxonomy from SCHEMA.md and checks all wiki pages for
unregistered tags. Reports per-file unknowns grouped by directory.

Usage:
  python3 tag-audit.py [WIKI_ROOT]
    Default WIKI_ROOT = ~/.hermes/wiki

Exit codes:
  0 — All tags registered (or info only)
  0 — Unknown tags found (informational, not a blocker)
      Output always shows remaining unknowns for human review.

Taxonomy extension (not individual page fix) is the right action when:
  - Unknown tags appear in 3+ files (repeated pattern)
  - Unknown tags concentrate in a specific section (infra/, analysis/, etc.)
Individual page fix is the right action when:
  - Unknown tag appears in exactly 1 file AND is cryptic/abbreviation
  - Tag is a typo/misspelling
"""
import re
import sys
from pathlib import Path

# --- Configuration ---
wiki_root = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path.home() / ".hermes/wiki"
excluded_prefixes = ('logs/', 'subagents-library/', '.git/', 'trade-pipeline/')

# --- Extract taxonomy from SCHEMA.md ---
taxonomy = set()
schema_path = wiki_root / 'SCHEMA.md'
if not schema_path.exists():
    print(f"ERROR: SCHEMA.md not found at {schema_path}")
    sys.exit(1)

text = schema_path.read_text(encoding='utf-8')
for line in text.split('\n'):
    # Match: | `tag1`, `tag2`, ... | description | dir |
    m = re.match(r'^\|\s*(`[^`]+`(?:,\s*`[^`]+`)*)\s*\|', line)
    if m:
        tags_str = m.group(1)
        tags = [t.strip().strip('`').strip("'").strip('"') for t in tags_str.split(',')]
        taxonomy.update(tags)

# Remove header row false positive
taxonomy.discard('태그')

# --- Collect tags from all wiki pages ---
all_tags = set()
unknown_per_file = {}

for f in sorted(wiki_root.rglob('*.md')):
    rel = str(f.relative_to(wiki_root))
    if any(rel.startswith(e) for e in excluded_prefixes):
        continue
    content = f.read_text(encoding='utf-8')
    m = re.search(r'^---\ntags:\s*\[(.*?)\]\n', content, re.MULTILINE)
    if m:
        tags = [t.strip().strip('"').strip("'") for t in m.group(1).split(',')]
        unknown = [t for t in tags if t not in taxonomy]
        if unknown:
            unknown_per_file[rel] = unknown
        all_tags.update(tags)

# --- Report ---
unknown_all = sorted(all_tags - taxonomy)
known_all = sorted(all_tags & taxonomy)

print(f'SCHEMA:        {schema_path}')
print(f'Taxonomy tags: {len(taxonomy)}')
print(f'All tags used: {len(all_tags)}')
print(f'Registered:    {len(known_all)}')
print(f'Unknown:       {len(unknown_all)}')
print()

if unknown_all:
    print(f'--- UNKNOWN TAGS (count per file) ---')
    for t in unknown_all:
        count = sum(1 for u in unknown_per_file.values() if t in u)
        # Show first file that uses this tag
        first_file = ''
        for fname, tags in sorted(unknown_per_file.items()):
            if t in tags:
                first_file = fname
                break
        print(f'  {t:30s}  {count:2d} file(s)  (e.g. {first_file})')

    print()
    print(f'--- PER-FILE DETAIL ---')
    for fname, tags in sorted(unknown_per_file.items()):
        print(f'  {fname}: {tags}')

    print()
else:
    print('All tags registered in SCHEMA.md taxonomy. ✓')
