#!/usr/bin/env python3
"""
verify-mermaid.py — sanity-check all ```mermaid blocks in slides/*.md BEFORE publishing.

Why: Saves a publish-debug-republish cycle. This script catches parse errors locally
in milliseconds rather than waiting for the live GitHub Pages site.

USAGE:
    python3 scripts/verify-mermaid.py                       # default: ./slides/*.md
    python3 scripts/verify-mermaid.py path/to/slides/      # explicit dir

EXIT CODES:
    0 = all blocks parsed OK
    1 = at least one parse failure (output points to file + block number)

REQUIREMENTS:
    npx @mermaid-js/mermaid-cli installed (one-time: npx -y @mermaid-js/mermaid-cli mmdc --version)

REFERENCE: see references/mermaid-integration.md "Verify syntax before publishing" section.
"""
import re
import subprocess
import sys
import tempfile
import os
from pathlib import Path


def extract_mermaid_blocks(md_path: Path) -> list[str]:
    """Pull every ```mermaid block from a markdown file (in source order)."""
    text = md_path.read_text(encoding="utf-8")
    # DOTALL so newlines inside ```mermaid...``` are captured
    blocks = re.findall(r"```mermaid\n(.*?)\n```", text, re.DOTALL)
    return blocks


def verify_one(block: str, mmdc_path: list[str]) -> tuple[bool, str]:
    """Run mmdc on one block. Returns (ok, error_msg)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
        f.write(block)
        tmp = f.name
    try:
        result = subprocess.run(
            mmdc_path + ["-i", tmp, "-o", "/tmp/_verify.svg", "--quiet"],
            capture_output=True, text=True, timeout=45,
        )
        if result.returncode == 0:
            return True, ""
        # Trim error to one line for readability; mermaid-cli is verbose
        err_lines = [
            l for l in result.stderr.splitlines()
            if any(k in l for k in ["Error", "Syntax", "Parse", "expecting", "got"])
        ]
        err = " | ".join(err_lines[:2]) if err_lines else result.stderr.splitlines()[0][:150]
        return False, err
    except subprocess.TimeoutExpired:
        return False, "timeout (mmdc took >45s; first run after install downloads Chromium)"
    finally:
        try: os.unlink(tmp)
        except OSError: pass
        try: os.unlink("/tmp/_verify.svg")
        except OSError: pass


def main() -> int:
    slides_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "slides")
    if not slides_dir.is_dir():
        print(f"ERROR: not a directory: {slides_dir}", file=sys.stderr)
        return 2

    # mmdc resolution: try global, fall back to npx
    if subprocess.run(["which", "mmdc"], capture_output=True).returncode == 0:
        mmdc = ["mmdc"]
    else:
        mmdc = ["npx", "-y", "@mermaid-js/mermaid-cli", "mmdc"]

    md_files = sorted(slides_dir.glob("*.md"))
    if not md_files:
        print(f"ERROR: no .md files in {slides_dir}", file=sys.stderr)
        return 2

    total_blocks = 0
    failures: list[tuple[str, int, str]] = []  # (file, block_num, error)

    for md in md_files:
        blocks = extract_mermaid_blocks(md)
        for i, block in enumerate(blocks, 1):
            total_blocks += 1
            ok, err = verify_one(block, mmdc)
            status = "✅" if ok else "❌"
            err_disp = "" if ok else f"  → {err[:120]}"
            print(f"{status}  {md.name:<35} block #{i}{err_disp}")
            if not ok:
                failures.append((md.name, i, err))

    print(f"\n{'=' * 80}")
    print(f"Total: {total_blocks} | OK: {total_blocks - len(failures)} | FAIL: {len(failures)}")
    if failures:
        print("\nFAILURES (fix syntax, re-run):")
        for fname, n, err in failures:
            print(f"  {fname} block #{n}: {err[:150]}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
