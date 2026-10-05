# SVG Architecture Diagrams (for PUBLIC decks)

> Hand-crafted SVG is preferred over mermaid for portfolio/course/recruiter decks. No CDN, no parse errors, infinite scale, predictable iOS Safari behavior. Source: Hermes architecture deck, 2026-07-01.

## When to choose SVG over mermaid

| Use SVG when | Use mermaid when |
|---|---|
| Audience is external / public | Single user, internal/ephemeral |
| Content includes non-ASCII (Korean, accented) | Mature prototype, both speakers of same language |
| Layout precision matters (boxes, arrows at specific angles) | Layout flexibility matters more than precision |
| iOS Safari must work without quirks | Browser audience only |
| Diagram lives in the deck repo forever | One-off, will be deleted |
| Designer / recruiter cares about aesthetic | Engineer cares about speed |

## Minimum-viable SVG header (Pitfall #14)

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 W H"
     preserveAspectRatio="xMidYMid meet"
     width="W" height="H"
     font-family="-apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif">
```

- `viewBox` — coordinate system; pick a ratio that matches your slide (1000×620 for landscape widescreen)
- `preserveAspectRatio="xMidYMid meet"` — never crop, scale to fit
- Explicit `width`/`height` — required! Without these, browser may size 0 in some flex layouts
- `font-family` on the `<svg>` — so `<text>` elements inherit Apple typography

## Styling blocks

```xml
<defs>
  <filter id="cardShadow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="2" stdDeviation="3"
                  flood-color="#000" flood-opacity="0.07"/>
  </filter>
  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="7" markerHeight="7" orient="auto">
    <path d="M0,0 L10,5 L0,10 z" fill="#0066cc"/>
  </marker>
  <marker id="arrowGray" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="6" markerHeight="6" orient="auto">
    <path d="M0,0 L10,5 L0,10 z" fill="#86868b"/>
  </marker>
</defs>

<style>
  .box          { fill:#fff; stroke:#d2d2d7; stroke-width:1.2; rx:14; ry:14; }
  .box-blue     { fill:#fff; stroke:#0066cc; stroke-width:1.8; rx:14; ry:14; }
  .box-tinted   { fill:rgba(0,102,204,0.04); stroke:#0066cc; stroke-width:1.8;
                  rx:14; ry:14; }
  .box-sub      { fill:#fff; stroke:#86868b; stroke-width:1; rx:8; ry:8;
                  stroke-dasharray:3,3; }                /* external refs */
  .label        { font-size:17px; font-weight:600; fill:#1d1d1f; }
  .label-sm     { font-size:12px; font-weight:500; fill:#6e6e73; }
  .label-xs     { font-size:10px; font-weight:400; fill:#86868b;
                  font-family:ui-monospace,'SF Mono',Menlo,monospace; }
  .label-blue   { font-size:16px; font-weight:600; fill:#0066cc; }
  .label-section{ font-size:11px; font-weight:600; fill:#86868b;
                  letter-spacing:1.5px; text-transform:uppercase; }
  .arrow        { stroke:#0066cc; stroke-width:1.8; fill:none; }
  .arrow-gray   { stroke:#86868b; stroke-width:1.2; fill:none;
                  stroke-dasharray:3,3; }
</style>
```

## 3-column architecture layout (Karpathy + Layers + Submodules)

Used in the Hermes deck slide "How We Remember" (2026-07-01).

```xml
<svg viewBox="0 0 1000 620" width="1000" height="620">
  <!-- 3 section labels at top -->
  <text x="170"  y="50" text-anchor="middle" class="label-section">Karpathy LLM Wiki</text>
  <text x="500"  y="50" text-anchor="middle" class="label-section">5 Layers</text>
  <text x="830"  y="50" text-anchor="middle" class="label-section">GitHub Submodules</text>

  <!-- LEFT column: 3 reference boxes -->
  <g filter="url(#cardShadow)">
    <rect x="40" y="80" width="260" height="120" class="box"/>
    <text x="170" y="115" text-anchor="middle" class="label">Karpathy Gist</text>
    <text x="170" y="145" text-anchor="middle" class="label-sm">LLM-consumable</text>
    ...
  </g>
  <!-- ... more boxes in left column -->

  <!-- CENTER: 5 stacked layers -->
  <g filter="url(#cardShadow)">
    <rect x="380" y="80"  width="240" height="60" class="box-layer"/>
    <text x="500" y="105" text-anchor="middle" class="label">① Schema</text>
  </g>
  <!-- ... 4 more stacked layers -->

  <!-- RIGHT: parent + 4 sub-repos -->
  <g filter="url(#cardShadow)">
    <rect x="680" y="80"  width="280" height="60" class="box-blue"/>
    <text x="820" y="105" text-anchor="middle" class="label-blue">hermes-wiki-super</text>
  </g>
  <!-- ... 4 submodules with class="box-sub" (dashed) -->

  <!-- Connectors with marker-end -->
  <path d="M 300 140 L 375 140" class="arrow" marker-end="url(#arrow)"/>
  <path d="M 620 110 L 678 110" class="arrow" marker-end="url(#arrow)"/>
  <path d="M 620 410 L 678 188" class="arrow" marker-end="url(#arrow)"/>

  <!-- Bottom band for context (e.g. topic repos separate from super) -->
  <g filter="url(#cardShadow)">
    <rect x="40" y="510" width="920" height="80" class="box"
          style="fill:#fafafc;"/>
    <text x="60" y="538" class="label">Topic-specific repos</text>
    ...
  </g>
</svg>
```

Key conventions:
- Section labels at top: `UPPERCASE`, letter-spacing 1.5px, gray fill
- Center column stacks use `box-tinted` for the most important item (e.g. Research layer)
- External/subordinate items use `box-sub` (dashed border)
- Connectors are thin paths with marker-end arrowheads, NOT Unicode glyphs
- Use `text-anchor="middle"` for centered labels in fixed-width boxes

## Embedding in markdown slides

```markdown
<div style="text-align:center; margin:1em 0;">
  <p><img src="../../assets/img/wiki-architecture.svg"
          alt="<descriptive alt text>"
          style="max-width:100%;height:auto;"></p>
</div>
```

The wrapping `<div>` lets the CSS `text-align: center` flow through (Pitfall #14 works hand-in-hand with this). Alt text is mandatory for accessibility AND for SEO of public decks.

## 3-loop compound diagram (used in same deck)

Layout: three horizontal "loop" diagrams stacked vertically, each with a back-arrow connector. SVG dimensions 800×660 viewBox.

```xml
<!-- Loop 1: Manual (workflow run → procedure → next faster) -->
<rect x="80" y="60"  width="220" height="80" class="box-blue"/>
<text x="190" y="105" text-anchor="middle" class="label-blue">Run workflow</text>
<rect x="380" y="60" width="220" height="80" class="box-blue"/>
<text x="490" y="105" text-anchor="middle" class="label-blue">Write procedure</text>
<!-- ... -->
<path d="M 290 100 Q 290 130, 380 130 Q 470 130, 470 100"
      class="arrow" marker-end="url(#arrow)"/>
```

## Iterate-and-verify loop

1. Draw at 1000×600 (or chosen viewBox)
2. Save → render in browser at the target slide size
3. If text wraps badly: shorten labels or increase box width (not font size — readability suffers at <14px)
4. Re-save → push → 60-second CDN wait → verify
5. Don't iterate on font sizes more than twice per element — at small sizes, redesign the layout instead

## Common mistakes

| Mistake | Fix |
|---|---|
| Setting only `viewBox`, no `width`/`height` | Add explicit width/height to both `<svg>` and/or the `<img>` wrapper |
| Using `<path d="..." />` to draw rectangles | Use `<rect>` instead — easier to position, fill, and animate |
| Using Unicode arrows (→ ← ↑ ↓) in text | Use `<marker>` SVG arrowheads — they scale and theme with stroke color |
| Font size 10px | Below 12px is illegible on phone screens; redesign instead |
| One symbol library / npm dep | Pure inline SVG — no deps |
| Forgetting `xmlns` attribute | Required for standalone SVG files |

## Position arithmetic: viewBox overflow & overlap

A class of bugs that does NOT show up in `curl` or in code inspection alone, but DOES show up the moment the browser renders the SVG. Three flavors, all encountered in 2026-07-01 deck work:

### Bug A — viewBox overflow (element clipped at right/bottom edge)

Cause: `<g transform="translate(X, Y)">` containing `<rect x="-A" width="B">` — the rect's right edge becomes `X + (-A + B) = X + B - A`. If this exceeds `viewBox` width, the rect is **silently clipped** on the right.

```xml
<!-- viewBox=0 0 800 460 -->
<!-- BAD: translate(680) + width=180 = right edge at 830, viewBox only 800 -->
<g transform="translate(680, 230)">
  <rect x="-30" width="180" ...>  <!-- right edge: 680-30+180 = 830 -->
</g>

<!-- GOOD: either translate less, or reduce width, or widen viewBox -->
<g transform="translate(620, 230)">
  <rect x="-30" width="180" ...>  <!-- right edge: 620-30+180 = 770 -->
</g>
```

**Rule of thumb**: pick a transform offset that's at least `(box_width / 2) + 20px` in from each edge. If the box is 200 wide, your `translate()` x should be in `[110, viewBox_w - 110]`.

### Bug B — left-label card collides with first node

When you add a label column on the left (e.g. "LOOP 1 · MANUAL") AND data nodes starting at the same vertical position, they will overlap if not planned:

```xml
<!-- viewBox=0 0 1000 600 -->
<!-- BAD: label box 60-240, first node x=120 width=180 → overlap x=120-240 -->
<rect x="60"  y="60"  width="180" height="40" class="label-card"/>
<rect x="120" y="60"  width="180" height="56" class="data-node"/>

<!-- FIX 1: move label ABOVE the row, centered -->
<text x="500" y="50" text-anchor="middle" class="label">LOOP 1 · MANUAL</text>
<rect x="120" y="80"  ... />  <!-- data row now starts at y=80, no collision -->

<!-- FIX 2: allocate a true left column with x gaps that never overlap -->
<rect x="40"  y="60"  width="120" height="40"  class="label-card"/>  <!-- ends at 160 -->
<rect x="200" y="60"  width="180" height="56"  class="data-node"/>   <!-- starts at 200, gap 40 -->
```

### Bug C — `feDropShadow` filter expands visible bounds

A glow filter (`feDropShadow dx="0" stdDeviation="6"`) extends the visible element by ~3× stdDeviation (here ~18px) on every side. A 200-wide rect with stdDeviation=6 filter visually occupies 236px wide. Two of them at x=200 and x=400 appear to overlap.

```xml
<!-- BAD: two boxes each 200w with stdDeviation=6 glow at x=200 and x=400 -->
<rect x="200" width="200" filter="url(#glow)"/>
<rect x="400" width="200" filter="url(#glow)"/>

<!-- FIX 1: leave 2×stdDeviation gap between glow elements -->
<!-- FIX 2: reduce stdDeviation (3 → visible glow = 9px each side, much safer) -->
```

### Pre-commit audit script

Before pushing, run a bounds check on every positioned element. Saved at `scripts/audit-svg-bounds.py`:

```python
#!/usr/bin/env python3
import re, sys

def audit(path):
    with open(path) as f:
        s = f.read()
    vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', s)
    vw, vh = int(vb.group(1)), int(vb.group(2))
    # only the FIRST rect inside each <g transform> (the anchor box)
    blocks = re.findall(
        r'<g\s+transform="translate\((\d+),\s*(\d+)\)"[^>]*>\s*<rect\s+([^/>]+)/?>',
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
        rx, ry, rw, rh = map(int, (rx_m.group(1), ry_m.group(1),
                                   rw_m.group(1), rh_m.group(1)))
        ax, ay = int(tx) + rx, int(ty) + ry
        ax2, ay2 = ax + rw, ay + rh
        if ax < 0 or ay < 0 or ax2 > vw or ay2 > vh:
            bad.append(f"  translate({tx},{ty}) rect({rx},{ry},{rw},{rh}) "
                       f"→ abs ({ax},{ay})-({ax2},{ay2}) OUT OF "
                       f"viewBox {vw}×{vh}")
    if bad:
        print(f"❌ {path}:")
        [print(b) for b in bad]
        sys.exit(1)
    print(f"✅ {path}: {len(blocks)} nodes, all within {vw}×{vh}")

if __name__ == "__main__":
    for p in sys.argv[1:]:
        audit(p)
```

`scripts/verify-svg-cache.sh` should chain this audit BEFORE attempting any commit. Caught all three bug classes above at write-time instead of push-time.

### Layout planning: pick your position grid FIRST

For a 1000×600 viewBox with N nodes per row:

```
left-edge-gap   = 100px   (room for label column or left annotation)
right-edge-gap  = 100px
inter-node-gap  = 60px    (visual breathing room)
inter-row-gap   = 80px    (vertical space between rows)

node_width = (1000 - 200 - (N-1) * 60) / N
```

Example for 3 nodes: `node_width = (1000 - 200 - 120) / 3 = 226px`. Round to 220 with left edges at x = `[100, 380, 660]`. Right edge of last node: 660 + 220 = 880, leaving 120px right margin.

Adopt this grid **before writing any `<rect>` or `<text>`**. The five minutes of arithmetic saves twenty minutes of "looks wrong, move things, looks worse, try again."
