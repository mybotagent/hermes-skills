# SVG authoring for slide decks

Why: `mmdc` (mermaid-cli) and other diagram-as-code tools frequently fail in sandboxed dev environments (Chromium can't launch, puppeteer permission errors, missing libs). Hand-authored SVG is more reliable, smaller, and gives exact pixel-level control.

## Authoring baseline

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 W H"
     width="W" height="H"
     preserveAspectRatio="xMidYMid meet"
     font-family="-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', sans-serif">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#0066cc"/>
    </marker>
  </defs>
  ...
</svg>
```

`width` and `height` MUST be set explicitly or `<img>` will render at 300×150 (see `reveal-js-mobile-pitfalls.md` §9).

## Reusable patterns

### Arrow with CSS-triangle head

Use a `<marker>` so any line can reference `marker-end="url(#arrow)"`:
```xml
<line x1="100" y1="50" x2="300" y2="50"
      stroke="#0066cc" stroke-width="2"
      marker-end="url(#arrow)"/>
```
For curves/paths:
```xml
<path d="M 100 50 Q 200 0 300 50" stroke="#0066cc" stroke-width="2" fill="none" marker-end="url(#arrow)"/>
```

For dashed/return paths:
```xml
<path d="M 300 100 Q 200 150 100 100" stroke="#0066cc" stroke-width="2"
      stroke-dasharray="5,3" fill="none" marker-end="url(#arrow-d)"/>
```

Define separate markers `arrow` (pointing) and `arrow-d` (different color) for the same direction so the marker direction matches `marker-end`.

### Card node

```xml
<rect x="100" y="50" width="200" height="70" rx="12"
      fill="#ffffff" stroke="#d2d2d7" stroke-width="1.5"/>
<text x="200" y="92" text-anchor="middle" font-size="15"
      font-weight="600" fill="#1d1d1f">Label here</text>
```

Apple-style: white bg, thin `#d2d2d7` border, 12px rounded corners. Use a thicker border (e.g., `stroke="#0066cc"`, `stroke-width="2"`) when the node is the primary actor in the diagram.

### Coordinated grid

For diagrams with multiple aligned rows of boxes (3 loops, 4 components):

| Row | y | use |
|---|---|---|
| Title | 35 | large text-anchor middle |
| Row 1 box | 60 | height 60-80 |
| Row 1 arrows | y_row+30 | inline-block horizontal arrows |
| Row 2 box | 200 | same shape |

Arrows between rows:
```xml
<line x1="W/2" y1="row1_bottom" x2="W/2" y2="row2_top"
      stroke="#0066cc" stroke-width="2" marker-end="url(#arrow)"/>
```

## Coordinate system tips

- Use round numbers (50, 100, 200, 300, 400, 500) — easier to debug later
- Centre horizontally at x=400 in a 800-wide viewBox
- Leave 20-30px padding inside the viewBox so nothing touches the edge
- Keep text vertically centred by `y = box_top + (height/2) + (font-size * 0.35)` — that ~0.35 factor accounts for baseline offset

## Multi-color coding

Apple's system gives a tight palette. Use sparingly:

| Color | Use |
|---|---|
| `#0066cc` | primary — sequence arrows, brand border |
| `#34c759` | success/outcome — terminal node of a chain |
| `#ff9500` | secondary actor / orchestration side |
| `#5856d6` | tertiary actor |
| `#af52de` | data / knowledge layer |
| `#b86e00` | darker amber — secondary actor text (darker for contrast on white) |
| `#2a7d3e` | darker green — terminal node text |
| `#1d1d1f` | body text |
| `#86868b` | muted text (sublabels) |
| `#d2d2d7` | default card border |
| `#f5f5f7` | card group background |
| `#ffffff` | default node fill |

Use `stroke="#XXX"` on rect for border, `fill="#XXX"` on text for label color, matching the rect's border.

## What NOT to do

- Don't use Unicode arrows (`↓`, `→`) inside SVG text — they look bad and don't scale to slide size well.
- Don't use HTML entities inside SVG (`&nbsp;`, `&mdash;`) — use UTF-8 directly.
- Don't declare an `xmlns:xlink` if you're not using xlink (modern browsers don't need it for `<use href=...>`).
- Don't put comments before the `<svg>` tag — browsers are strict about the root element type.
- Don't use `<text>` with `\n` line breaks for multi-line labels — split into multiple `<text>` elements positioned manually.
