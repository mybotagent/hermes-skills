#!/usr/bin/env python3
"""vault-publish.py — copy executed ipynb to destination vault repo.

Usage:
    python vault-publish.py <goal_slug>
    DATA_ANALYSIS_RESULTS_DIR=/path/to/vault python vault-publish.py <goal_slug>

Behavior:
    - Copies docs/reports/<date>-<goal_slug>.ipynb to <vault>/docs/reports/
    - Does NOT copy .md, .html, scratch/, plans/, or regenerate INDEX.md
    - Silently skips if vault or source ipynb is absent

This script is the canonical example of vault-minimalism publishing: one ipynb
per analysis, nothing else. Use as a template when adding vault publish to a
new analysis framework.
"""
from __future__ import annotations

import datetime
import os
import shutil
import sys
from pathlib import Path


DEFAULT_VAULT = os.path.expanduser("~/dev/data-analysis-results")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: vault-publish.py <goal_slug>")
        return 1

    goal = sys.argv[1]
    vault = Path(os.environ.get("DATA_ANALYSIS_RESULTS_DIR", DEFAULT_VAULT))
    reports_dst = vault / "docs" / "reports"

    if not reports_dst.exists():
        print(f"[skip] vault 레포 미설정: {vault}")
        return 0

    src_reports = Path("docs/reports")
    if not src_reports.exists():
        print(f"[skip] 분석 산출물 없음: {src_reports}")
        return 0

    # Find all ipynb matching the goal suffix
    pattern = f"*-{goal}.ipynb"
    matches = sorted(src_reports.glob(pattern))

    if not matches:
        print(f"[skip] ipynb 없음: {src_reports}/{pattern}")
        return 0

    copied = 0
    for src in matches:
        dst = reports_dst / src.name
        shutil.copy(src, dst)
        print(f"  copy: {src} → {dst}")
        copied += 1

    print(f"[vault] {goal} → {vault} ({copied} ipynb)")
    return 0


if __name__ == "__main__":
    sys.exit(main())