#!/usr/bin/env python3
"""logs/index.md 링크 무결성 양방향 감사 (2026-10-21 추가, P25).

기존 2c-ter bash 루프는 "파일이 index.md에 미등록" (NOTREF) 한 방향만 검사한다.
이 스크립트는 반대 방향도 검사한다:
  - BROKEN  : index.md에 등록된 링크의 대상 파일이 존재하지 않음 (경로 오기 / 삭제된 파일)
  - NOTREF  : index.md에 참조되지 않은 .md 파일 존재 (누락 등록 후보)
  - COVERED : glob 항목(예: [2026-05-31-*](2026/))으로 커버됨 → 조치 불필요
  - AMBIG   : 디렉터리 target이라 glob 패턴을 확정할 수 없는 링크

사용법:
    python3 logs-index-link-audit.py [LOGS_DIR]
    기본 LOGS_DIR=~/.hermes/wiki/logs
    --strict : BROKEN 1건 이상이면 exit 1 (그 외 항상 0 — 정보성)

핵심 설계 — glob 매칭은 target이 아니라 **label**로 한다:
    | 05-31 | Initial wiki setup batch | [2026-05-31-*](2026/) |
    label `2026-05-31-*` 이 진짜 glob이고 target `2026/` 은 그냥 디렉터리.
    target(`2026/`)으로 매칭하면 2026/ 하위 전체가 커버되어
    진짜 NOTREF(미등록 로그)가 모두 묻힌다 → 반드시 label 기준으로 판정.
"""
import os
import re
import sys
from fnmatch import fnmatch

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
SKIP_NAMES = {"index.md", "README.md"}
EXTERNAL_PREFIX = ("http://", "https://", "#", "mailto:")


def parse_links(index_path):
    """index.md에서 (label, target) 링크 목록을 파싱."""
    with open(index_path, encoding="utf-8") as fh:
        content = fh.read()
    return [(m.group(1), m.group(2)) for m in LINK_RE.finditer(content)]


def glob_patterns(label, target):
    """링크가 커버하는 basename glob 패턴 목록.

    - label에 `*`/`?`가 있으면 label 자체가 glob (예: `2026-05-31-*`)
    - target에 `*`가 있으면 target basename도 glob
    - target이 디렉터리(`2026/`)면 basename(`2026`)은 glob 아님 → 제외
      (디렉터리 전체를 커버시키면 진짜 NOTREF가 묻힘)
    """
    pats = []
    for cand in (label, target, os.path.basename(target.rstrip("/"))):
        if "*" in cand or "?" in cand:
            pats.append(cand)
    return pats


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    strict = "--strict" in sys.argv
    root = os.path.expanduser(args[0]) if args else os.path.expanduser("~/.hermes/wiki/logs")
    index_path = os.path.join(root, "index.md")

    if not os.path.isfile(index_path):
        print(f"ERROR: index.md not found at {index_path}")
        return 0

    links = parse_links(index_path)

    resolved = set()   # 실제로 링크가 가리키는 파일
    broken = []        # target 존재하지 않음
    patterns = []      # glob 커버 패턴
    ambiguous = []     # 디렉터리 target — glob 확정 불가

    for label, target in links:
        if target.startswith(EXTERNAL_PREFIX):
            continue
        pats = glob_patterns(label, target)
        if pats:
            patterns.extend(pats)
            continue
        if target.endswith("/"):
            ambiguous.append((label, target))
            continue
        full = os.path.join(root, target)
        if os.path.exists(full):
            resolved.add(os.path.normpath(full))
        else:
            broken.append(target)

    # --- 실제 .md 파일 수집 ---
    all_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in sorted(filenames):
            if name.endswith(".md") and name not in SKIP_NAMES:
                all_files.append(os.path.normpath(os.path.join(dirpath, name)))

    notref = []
    covered = []
    for full in all_files:
        if full in resolved:
            continue
        name = os.path.basename(full)
        if any(fnmatch(name, p) or fnmatch(full, p) for p in patterns):
            covered.append(os.path.relpath(full, root))
            continue
        notref.append(os.path.relpath(full, root))

    print(f"=== logs-index-link-audit: {root} ===")
    print(f"links: {len(links)} / files: {len(all_files)} / glob patterns: {len(set(patterns))}")

    print("\n--- BROKEN: index에 등록됐지만 대상 파일 없음 ---")
    if broken:
        for b in broken:
            print(f"  BROKEN: {b}")
    else:
        print("  (none)")

    print("\n--- NOTREF: 파일은 있지만 index에 미등록 ---")
    if notref:
        for n in notref:
            print(f"  NOTREF: {n}")
    else:
        print("  (none)")

    if covered:
        print(f"\n--- COVERED: glob 항목으로 커버됨 (조치 불필요): {len(covered)}건 ---")
        for c in covered[:20]:
            print(f"  COVERED: {c}")
        if len(covered) > 20:
            print(f"  ... 외 {len(covered) - 20}건")

    if ambiguous:
        print(f"\n--- AMBIG: 디렉터리 target — glob 확정 불가 ({len(ambiguous)}건) ---")
        for label, target in ambiguous:
            print(f"  AMBIG: [{label}]({target})")

    print(f"\nSummary: broken={len(broken)} notref={len(notref)} covered={len(covered)} ambiguous={len(ambiguous)}")
    if strict and broken:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
