# Apple Design System — White Background (Portfolio/Recruiter Decks)

> For PUBLIC-facing decks (portfolio submissions, course deliverables, recruiter shares). When the audience is internal/sales, switch to `templates/custom.css` (dark/brand).

Source: distilled from the Hermes architecture deck (https://mybotagent.github.io/hermes-architecture-deck/) on 2026-07-01. Reference doc in `decks/hermes-architecture/APPLE-DESIGN.md` of that repo.

## Install

```bash
# Quickest path to Apple HIG tokens
npx getdesign@latest add apple

# Manual install (if npx is unavailable in the env)
# 1) Load SF Pro Display + SF Pro Text + SF Mono via @fontsource (npm)
# 2) Define CSS custom properties below
# 3) Apply via single inline <style> in index.html
```

## Tokens (copy this block)

```css
:root {
  /* Apple Design Tokens (light mode) */
  --primary:           #0066cc;   /* Action Blue        */
  --primary-focus:     #0071e3;
  --primary-on-light:  #0066cc;
  --ink:               #1d1d1f;   /* primary text       */
  --body:              #1d1d1f;
  --body-muted:        #6e6e73;   /* secondary text     */
  --body-muted-2:      #86868b;
  --canvas:            #ffffff;   /* background         */
  --canvas-parchment:  #f5f5f7;   /* card / code bg     */
  --surface-pearl:     #fafafc;
  --divider:           #d2d2d7;
  --hairline:          #e0e0e0;
  --surface-black:     #000000;
  --on-primary:        #ffffff;
}

* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }

html, body {
  font-family: -apple-system, BlinkMacSystemFont,
               "SF Pro Display", "SF Pro Text", "Helvetica Neue",
               system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  letter-spacing: -0.01em;
  font-feature-settings: "ss01", "ss02";
  background: var(--canvas);
  color: var(--body);
}
```

## Required Reveal.js config (combined with the Pitfall #13 fix)

```js
Reveal.initialize({
  hash: true,
  controls: true,
  progress: true,
  slideNumber: false,             // ← Pitfall #15
  overview: true,
  center: false,                  // we center manually with flex
  disableLayout: true,            // ← Pitfall #13 (iOS Safari)
  transition: 'slide',
  transitionSpeed: 'fast',
  // ...
});
```

```css
/* Pitfall #13 — manual centering */
.reveal .slides > section {
  width: 100% !important; height: 100% !important;
  position: absolute !important;
  top: 0; left: 0;
  padding: 4vh 4vw !important;
  text-align: center !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  -webkit-overflow-scrolling: touch;
  background: #ffffff;
}
.reveal .slides > section.present {
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
  align-items: center !important;
}

/* Pitfall #14 — SVG / image fit */
.reveal .slides > section img {
  display: block !important;
  max-width: 100% !important;
  max-height: calc(100vh - 16vh) !important;
  width: auto !important;
  height: auto !important;
  margin: 0.6em auto !important;
  object-fit: contain;
}

/* Pitfall #15 — defensive slide-number hide */
.reveal .slide-number,
.reveal .slide-number-pdf,
.reveal .slide-suffix { display: none !important; }

/* Apple typography — fluid via clamp */
.reveal h1 { font-size: clamp(2rem, 5vw, 3.2rem);
             font-weight: 600; line-height: 1.07;
             letter-spacing: -0.035em; text-align: center; }
.reveal h2 { font-size: clamp(1.4rem, 3.5vw, 2.2rem);
             font-weight: 600; letter-spacing: -0.025em; }
.reveal p  { font-size: clamp(0.85rem, 1.7vw, 1.05rem);
             line-height: 1.5;  letter-spacing: -0.01em;
             max-width: 70ch; margin: 0 auto 0.7em; }
```

## Component recipes

### Apple card
```css
.reveal .card {
  background: var(--canvas-parchment);
  border: 1px solid var(--hairline);
  border-radius: 18px;
  padding: 1.4em 1.8em;
  margin: 1em auto; max-width: 780px;
  text-align: left;
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
}
```

### Apple TL;DR (blue tint)
```css
.reveal .tldr {
  background: linear-gradient(135deg,
              rgba(0,102,204,0.06) 0%,
              rgba(0,113,227,0.02) 100%);
  border: 1px solid rgba(0,102,204,0.18);
  border-radius: 18px;
  padding: 1.4em 1.8em;
  margin: 1em auto; max-width: 720px;
}
```

### Apple table (spreadsheet aesthetic)
```css
.reveal table {
  border-collapse: separate; border-spacing: 0;
  border: 1px solid var(--divider);
  border-radius: 14px; overflow: hidden;
  width: 100%; max-width: 800px; margin: 1em auto;
}
.reveal th { background: var(--canvas-parchment);
             padding: 0.7em 1em; text-align: left; }
.reveal tr:nth-child(even) { background: rgba(0,0,0,0.015); }
```

### Apple code block
```css
.reveal pre {
  background: var(--canvas-parchment);
  border: 1px solid var(--hairline);
  border-radius: 14px;
  padding: 1em 1.4em;
  font-size: clamp(0.6rem, 1.2vw, 0.78rem);
  line-height: 1.55;
  width: 95%; max-width: 800px;
  text-align: left; margin: 0.5em auto 1em;
}
.reveal code { background: var(--canvas-parchment);
               color: var(--primary);
               padding: 0.1em 0.45em; border-radius: 6px;
               font-family: ui-monospace, "SF Mono", Menlo, monospace;
               font-size: 0.88em; font-weight: 500; }
.reveal pre code { background: transparent; color: var(--body); }
```

## Mobile media queries

```css
@media (max-width: 600px) {
  .reveal .slides > section { padding: 3vh 4vw; }
  .reveal h1 { font-size: 1.7rem; }
  .reveal h2 { font-size: 1.2rem; }
}
@media (max-height: 500px) and (orientation: landscape) {
  .reveal .slides > section { padding: 2vh 4vw; }
  .reveal h1 { font-size: 1.4rem; margin-bottom: 0.2em; }
}
```

## Verification checklist

- [ ] `disableLayout: true` in Reveal config
- [ ] All Apple tokens defined in `:root`
- [ ] `slideNumber: false` AND CSS hide
- [ ] All CDN URLs cache-busted with `?v=N`
- [ ] SVG images have explicit `width`/`height` + `preserveAspectRatio`
- [ ] Mobile viewport meta: `width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover`
- [ ] Cache headers in HTML: `Cache-Control: no-cache, no-store, must-revalidate` + `Pragma: no-cache` + `Expires: 0`
- [ ] 60-second wait after push before reverifying (Pitfall #16)
