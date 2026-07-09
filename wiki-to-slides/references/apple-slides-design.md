# Apple-Style Slide Design (Reveal.js)

> The visual system we converged on for portfolio-ready wiki-to-slide
> decks: SF Pro typography, action blue accent, white background,
> card-based layout with subtle drop shadows. User's stated preference.

## Color Tokens (light mode)

| Token | Hex | Usage |
|-------|-----|-------|
| `--primary` | `#0066cc` | Apple Action Blue — accents, links, focus |
| `--primary-focus` | `#0071e3` | Hover state |
| `--ink` | `#1d1d1f` | Headings, strong text |
| `--body` | `#1d1d1f` | Body text |
| `--body-muted` | `#6e6e73` | Sub-text, labels |
| `--body-muted-2` | `#86868b` | Mono captions |
| `--canvas` | `#ffffff` | Page background |
| `--canvas-parchment` | `#f5f5f7` | Code blocks, cards, quotes |
| `--surface-pearl` | `#fafafc` | Layer cards |
| `--divider` | `#d2d2d7` | Borders, table separators |
| `--hairline` | `#e0e0e0` | Subtle dividers |

## Typography

```css
font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
             "SF Pro Text", "Helvetica Neue", system-ui, sans-serif;
-webkit-font-smoothing: antialiased;
font-feature-settings: "ss01", "ss02";
```

Fluid sizes (use `clamp()`):
- `h1`: `clamp(2rem, 5vw, 3.2rem)` — slide titles
- `h2`: `clamp(1.4rem, 3.5vw, 2.2rem)` — section titles
- `h3`: `clamp(1rem, 2.2vw, 1.3rem)` — card titles
- `body`: `clamp(0.85rem, 1.7vw, 1.05rem)` — paragraphs
- `code`: `0.88em` of body
- `.small`: `0.7em` of body, muted color

## Reveal.js Init (the user's preference)

```js
Reveal.initialize({
  hash: true,
  controls: true,         // arrow buttons (keep for desktop)
  progress: true,         // subtle 3px progress bar at top
  slideNumber: false,     // NEVER show "1/9" — user explicitly removed
  overview: true,         // ESC for slide overview
  center: false,
  disableLayout: true,    // bypass iOS Safari transform: scale() bug
  transition: 'slide',
  transitionSpeed: 'fast',
  plugins: [RevealMarkdown, RevealNotes],
  markdown: { smartypants: false, gfm: true }
});
```

## CSS Patterns

### Vertical + Horizontal Center on Slide

The single most important pattern — without this, h1 floats to top-left:

```css
.reveal .slides > section {
  width: 100% !important;
  height: 100% !important;
  position: absolute !important;
  top: 0 !important; left: 0 !important;
  display: none !important;
  padding: 4vh 4vw !important;
  text-align: center !important;
  overflow-y: auto !important;       /* per-slide scroll */
  overflow-x: hidden !important;
  -webkit-overflow-scrolling: touch;
  background: #ffffff;
}
.reveal .slides > section.present {
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;  /* vertical center */
  align-items: center !important;       /* horizontal center */
}
```

### Image / SVG Fitting (cap to viewport)

Without `max-height`, big SVGs (1100×680) overflow on mobile:

```css
.reveal .slides > section img {
  display: block !important;
  max-width: 100% !important;
  max-height: calc(100vh - 16vh) !important;  /* 16vh = top+bottom padding */
  width: auto !important;
  height: auto !important;
  margin: 0.6em auto !important;
  object-fit: contain;
}
```

### Defensive Slide-Number Hiding

Even with `slideNumber: false`, some themes re-add it. Belt + suspenders:

```css
.reveal .slide-number,
.reveal .slide-number-pdf,
.reveal .slide-suffix { display: none !important; }
```

### Apple Card

```css
.reveal .card {
  background: var(--canvas-parchment);
  border: 1px solid var(--hairline);
  border-radius: 18px;
  padding: 1.4em 1.8em;
  margin: 1em auto;
  max-width: 780px;
  text-align: left;
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
}
```

### Apple Table (spreadsheet aesthetic)

```css
.reveal table {
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid var(--divider);
  border-radius: 14px;
  overflow: hidden;
}
.reveal th { background: var(--canvas-parchment); }
.reveal tr:last-child td { border-bottom: none; }
.reveal tr:nth-child(even) { background: rgba(0,0,0,0.015); }
```

## Mobile Optimization

```css
@media (max-width: 600px) {
  .reveal .slides > section { padding: 3vh 4vw; }
  .flow-node { font-size: 0.7em; padding: 0.45em 0.8em; max-width: 170px; }
  .reveal h1 { font-size: 1.7rem; }
  .reveal h2 { font-size: 1.2rem; }
}
@media (max-height: 500px) and (orientation: landscape) {
  .reveal .slides > section { padding: 2vh 4vw; }
}
```

## Mobile Meta Tags (essential)

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0,
                               maximum-scale=1.0, user-scalable=no,
                               viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">

<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
```
