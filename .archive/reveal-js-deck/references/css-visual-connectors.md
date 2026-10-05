# CSS Visual Connectors Cheatsheet

Replacing Unicode arrow glyphs (↓ → ← ↑) with pure-CSS shapes. Required when the user explicitly rejects emoji-style arrows ("no Unicode arrows, use a real flow-chart shape instead").

## Vertical connector (between two stacked nodes)

```css
.flow-arrow {
  display: block;
  width: 2px;
  height: 28px;
  background: var(--primary);   /* the line itself */
  margin: 6px auto;
  position: relative;
}
.flow-arrow::before { content: "" !important; }  /* never show Unicode glyph */
.flow-arrow::after {
  content: "";
  position: absolute;
  bottom: -1px; left: 50%;
  transform: translateX(-50%);
  width: 0; height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 6px solid var(--primary);    /* triangle arrowhead */
}
```

## Horizontal connector (inside `.flow-row`)

When the connector sits between two `inline-block` nodes in a row, swap dimensions and reorient the triangle:

```css
.flow-row > .flow-arrow {
  display: inline-block;
  width: 28px;
  height: 2px;
  background: var(--primary);
  margin: 0 6px;
  vertical-align: middle;
}
.flow-row > .flow-arrow::after {
  content: "";
  position: absolute;
  top: 50%; right: -1px; left: auto; bottom: auto;
  transform: translateY(-50%);
  width: 0; height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-left: 6px var(--primary);    /* triangle points right */
}
```

## Direction variants

| Class | Direction | Triangle edge |
|---|---|---|
| `.flow-arrow` (default) | down | `border-top` |
| `.flow-arrow.right` | right | `border-left` |
| `.flow-arrow.left` | left | `border-right` |
| `.flow-arrow.up` | up | `border-bottom` |

Example for "up":

```css
.flow-arrow.up::after {
  content: "";
  position: absolute;
  top: -1px; left: 50%; right: auto; bottom: auto;
  transform: translateX(-50%);
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: none;
  border-bottom: 6px solid var(--primary);  /* triangle points up */
}
```

## Pairing with inline-block nodes

Connectors only flow correctly when the nodes themselves are `inline-block` (not `inline`):

```css
.flow-node {
  display: inline-block;
  vertical-align: middle;
  /* …border, padding, font-size… */
}
```

If anything is `flex` inside the Reveal.js slide, iOS Safari layout will break — see SKILL.md pitfall #2.

## Why this beats mermaid / Unicode glyphs

- **No glyph dependency** — text-only md files, no font glyph required to render the line.
- **iOS Safari safe** — pure CSS shape survives `transform: scale()` that Reveal.js applies.
- **No external library** — mmdc, mermaid.live, headless Chromium not required; works offline.
- **Stylable** — color via CSS variable; arrowhead size via border widths; direction via which border-edge is non-transparent.
- **Print-safe** — SVG export not needed; what you see is what you get.

## Trigger condition

This cheatsheet was added because the user for this portfolio rejected `.flow-arrow::before { content: "↓" }` style with "no Unicode arrows, use a real flow-chart shape instead." Apply this pattern any time the user says "no arrows" or "real flow chart form" in slide context.
