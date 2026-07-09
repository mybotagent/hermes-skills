#!/usr/bin/env python3
"""
audit-svg-bounds.py — check that every <g transform="translate(X,Y)"> + child
<rect> stays within its parent <svg> viewBox.

Catches a class of bugs that don't show up in `curl` or in code review but
DO show up the moment a browser renders the SVG (silent clipping at edge,
node overlap with label card, etc.).

Usage:
    python3 audit-svg-bounds.py path/to/diagram.svg [another.svg ...]

Exit codes:
    0 — all nodes inside viewBox
    1 — at least one overflow detected (printed with detail)

Caveats:
    - Only inspects the FIRST <rect> child of each <g transform=...>.
      Nested <g> groups are skipped (use at your own risk for grouped
      diagrams — the audit is conservative for the common case).
    - SVG must declare `viewBox="0 0 W H"` somewhere before the elements.
"""
import re
import sys


def audit(path):
    with open(path, encoding="utf-8") as f:
        s = f.read()

    vb_m = re.search(r'viewBox="0 0 (\d+) (\d+)"', s)
    if not vb_m:
        print(f"⚠️  {path}: no viewBox found, skipping")
        return
    vw, vh = int(vb_m.group(1)), int(vb_m.group(2))

    # match only the FIRST rect that follows a translate(...) g opening
    blocks = re.findall(
        r'<g\s+transform="translate\((\d+),\s*(\d+)\)"[^>]*>\s*'
        r'<rect\s+([^/>]+)/?>',
        s,
    )

    bad = []
    for tx, ty, attrs in blocks:
        rx_m = re.search(r'x="(-?\d+)"', attrs)
        rw_m = re.search(r'width="(\d+)"', attrs)
        ry_m = re.search(r'y="(-?\d+)"', attrs)
        rh_m = re.search(r'height="(\d+)"', attrs)
        if not all([rx_m, rw_m, ry_m, rh_m]):
            continue
        rx, ry, rw, rh = map(int, (
            rx_m.group(1), ry_m.group(1), rw_m.group(1), rh_m.group(1)
        ))
        ax, ay = int(tx) + rx, int(ty) + ry
        ax2, ay2 = ax + rw, ay + rh
        if ax < 0 or ay < 0 or ax2 > vw or ay2 > vh:
            bad.append(
                f"  translate({tx},{ty}) rect({rx},{ry},{rw},{rh}) "
                f"→ abs ({ax},{ay})-({ax2},{ay2}) "
                f"OUT OF viewBox {vw}×{vh}"
            )

    if bad:
        print(f"❌ {path}:")
        for line in bad:
            print(line)
        sys.exit(1)
    print(f"✅ {path}: {len(blocks)} nodes, all within {vw}×{vh}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    for p in sys.argv[1:]:
        audit(p)
