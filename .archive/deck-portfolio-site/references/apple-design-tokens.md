# Apple Design Tokens — White-Mode Reference

Source: `npx getdesign@latest add apple`. Use these values verbatim — partial application reads as "not Apple".

## Colors

```css
:root {
  --primary: #0066cc;            /* Action Blue — single accent */
  --primary-focus: #0071e3;
  --primary-on-dark: #2997ff;    /* Apple Blue on dark surfaces */

  --ink: #1d1d1f;                /* Apple ink (text on light) */
  --body: #1d1d1f;
  --body-on-dark: #ffffff;
  --body-muted: #86868b;         /* muted text on light bg */
  --body-muted-2: #6e6e73;
  --ink-muted-80: #333333;
  --ink-muted-48: #7a7a7a;

  --canvas: #ffffff;             /* canvas */
  --canvas-parchment: #f5f5f7;   /* Apple's signature light gray */
  --surface-pearl: #fafafc;
  --surface-black: #000000;

  --divider-soft: #f0f0f0;
  --divider: #d2d2d7;            /* Apple hairline */
  --hairline: #e0e0e0;

  --on-primary: #ffffff;
  --on-dark: #ffffff;
}
```

The dark mode tokens (`surface-black`, `body-on-dark`, `primary-on-dark`) are available if you ever mix — but for a portfolio keynote, default to white canvas.

## Typography

Font stack (always):
```css
font-family: -apple-system, BlinkMacSystemFont,
             "SF Pro Display", "SF Pro Text",
             "Helvetica Neue", system-ui, sans-serif;
```

Apple scale — use `clamp()` for fluid slide sizing:

| Token | Slide use | Size (clamp) |
|---|---|---|
| Hero display | Slide titles | `clamp(2rem, 5vw, 3.2rem)` |
| display-lg | Section openers | `clamp(1.6rem, 4vw, 2.4rem)` |
| display-md | Major headings | `clamp(1.4rem, 3.5vw, 2.2rem)` |
| Tagline / h3 | Section titles | `clamp(1rem, 2.2vw, 1.3rem)` |
| Body | Paragraphs | `clamp(0.85rem, 1.7vw, 1.05rem)` |
| Body small | Tables | `clamp(0.7rem, 1.4vw, 0.85rem)` |
| Caption | Sub-notes | `0.7em` |

```css
.reveal h1 { font-weight: 600; line-height: 1.07; letter-spacing: -0.035em; }
.reveal h2 { font-weight: 600; line-height: 1.1;  letter-spacing: -0.025em; }
.reveal h3 { font-weight: 600; }
.reveal em { font-style: italic; color: var(--primary); }
```

## Cards

The signature Apple surface. Single subtle shadow, no gradient, no double-shadow.

```css
.card {
  background: var(--canvas-parchment);   /* #f5f5f7 */
  border: 1px solid var(--hairline);     /* #e0e0e0 */
  border-radius: 18px;
  padding: 1.4em 1.8em;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}
```

Apple uses single drop-shadow only on product imagery, NOT on chrome — don't shadow cards inside cards or buttons.

## Buttons (pill-shaped)

```css
.cta {
  background: var(--primary);      /* #0066cc */
  color: #ffffff;
  border-radius: 980px;            /* pill shape — Apple's signature */
  padding: 0.95em 2.2em;
  font-size: 1.05rem;
  letter-spacing: -0.01em;
  transition: background 0.2s ease, transform 0.2s ease;
}
.cta:hover { background: var(--primary-focus); transform: scale(1.02); }
```

## Hero title (Apple keynote display)

```html
<h1>YuRi's <em>Portfolio</em></h1>
```

```css
.hero-title {
  font-size: clamp(2.5em, 7vw, 5.5em);
  font-weight: 600;
  line-height: 1.05;
  letter-spacing: -0.04em;
  color: var(--ink);
  max-width: 12ch;
}
.hero-title em { font-style: italic; color: var(--primary); font-weight: 500; }
```

## Flow-chart node variants (single accent palette)

Each "type" of node uses the **same template**, just the border / label color changes. One accent (Apple Blue) + secondary accents come from Apple's stock palette (orange, purple, indigo, green).

```css
.flow-node {
  display: inline-block;
  vertical-align: middle;
  padding: 0.6em 1.1em;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: 500;
  text-align: center;
  line-height: 1.35;
  margin: 0.3em;
  max-width: 240px;
  background: #ffffff;
  border: 1px solid var(--divider);
  color: var(--ink);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* Per-type accent — border + matching label color, with very light bg tint */
.flow-node.long-term { border-color: #0066cc; background: rgba(0,102,204,0.04); }  .flow-node.long-term .node-label { color: #0066cc; }
.flow-node.tooling  { border-color: #ff9500; background: rgba(255,149,0,0.04); }   .flow-node.tooling  .node-label { color: #b86e00; }
.flow-node.compute  { border-color: #5856d6; background: rgba(88,86,214,0.04); }   .flow-node.compute  .node-label { color: #5856d6; }
.flow-node.data     { border-color: #af52de; background: rgba(175,82,222,0.04); }  .flow-node.data     .node-label { color: #af52de; }
.flow-node.output   { border-color: #34c759; background: rgba(52,199,89,0.04); }   .flow-node.output   .node-label { color: #2a7d3e; }
.flow-node.simple   { border-color: var(--divider); }                                  .flow-node.simple   .node-label { color: var(--ink); }
```

The Apple-style choice: every node is a white card with a colored 1px border. The bg tint is barely-there (`rgba(..., 0.04)`). The label color is the saturated version of the border. No filled-color blocks, no rainbow palette.

## Tables

```css
table {
  font-size: clamp(0.7rem, 1.4vw, 0.85rem);
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid var(--divider);
  border-radius: 14px;
  overflow: hidden;
  width: 100%;
  max-width: 800px;
}
th { background: var(--canvas-parchment); color: var(--ink); padding: 0.7em 1em; text-align: left; border-bottom: 1px solid var(--divider); font-weight: 600; }
td { padding: 0.55em 1em; border-bottom: 1px solid var(--hairline); color: var(--body); }
tr:last-child td { border-bottom: none; }
tr:nth-child(even) { background: rgba(0,0,0,0.015); }
```

## Don't (Apple explicit anti-patterns)

- No gradients (Apple design explicitly rejects them — even subtle ones)
- No multiple shadows on chrome
- No glassmorphism by default
- No emoji unless the brand uses them
- No decorative SVG illustrations
- No oversized rounded rectangles as a substitute for hierarchy
- No fake metrics / decorative stats / generic feature grids
- No left-border accent callout cards
- No vague labels ("Insights", "Growth", "Scale", "Optimize") without content

## Quick verifier

After applying these tokens, check three things:

1. **One primary accent only**: scan the deck for `#0066cc` (or variants) — should be the only saturated color other than black/white/gray.
2. **All flow nodes are white cards** with thin colored borders, not filled blocks.
3. **No gradients anywhere** in inline CSS or computed styles.

If any check fails, you're not doing Apple design yet. Pull tokens more strictly from `getdesign add apple`.
