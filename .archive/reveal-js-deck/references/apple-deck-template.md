# Apple-Inspired Deck Template

Drop-in `index.html` template for a single Reveal.js deck with Apple design tokens, iOS-Safari-safe CSS, and inline styling. Adapted from the mybotagent/hermes-architecture-deck working version.

## When to use

- Single deck (not multi-deck portfolio).
- Want one self-contained `.html` file (no separate `deck.css`).
- Dark mode + Apple system fonts.
- Need it to render reliably on iPhone Safari without debugging.

## Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <title>YOUR DECK TITLE</title>

  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/black.css">

  <style>
    :root {
      --apple-primary-on-dark: #2997ff;
      --apple-body-on-dark: #ffffff;
      --apple-body-muted: #86868b;
      --apple-surface-black: #000000;
    }
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    html, body {
      margin: 0; padding: 0; width: 100%; height: 100%;
      background: var(--apple-surface-black);
      color: var(--apple-body-on-dark);
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
                   system-ui, "Helvetica Neue", sans-serif;
      -webkit-font-smoothing: antialiased;
      overflow: hidden;
      touch-action: manipulation;
    }

    .reveal { width: 100%; height: 100%; position: relative; }

    /* Disable Reveal's scale; use absolute positioning */
    .reveal .slides {
      width: 100% !important; height: 100% !important;
      transform: none !important; inset: 0 !important;
      text-align: center; position: absolute;
    }
    .reveal .slides > section {
      width: 100% !important; height: 100% !important;
      transform: none !important; position: absolute !important;
      top: 0 !important; left: 0 !important;
      display: block !important; padding: 3vh 5vw;
      text-align: center; overflow: hidden; visibility: hidden;
    }
    .reveal .slides > section.present { visibility: visible; }

    /* Heading centered; body left-aligned */
    .reveal p, .reveal li, .reveal table, .reveal blockquote, .reveal .small { text-align: left; }
    .reveal h1, .reveal h2, .reveal h3 { text-align: center; }

    /* Typography */
    .reveal h1 { font-size: clamp(1.8rem, 5vw, 2.8rem); font-weight: 600; line-height: 1.08;
                 letter-spacing: -0.035em; margin: 0 auto 0.4em; max-width: 90%; color: #fff; }
    .reveal h2 { font-size: clamp(1.3rem, 3.5vw, 2rem); font-weight: 600; line-height: 1.15;
                 letter-spacing: -0.025em; margin: 0 auto 0.5em; max-width: 90%; color: #fff; }
    .reveal h3 { font-size: clamp(1rem, 2.5vw, 1.3rem); font-weight: 600;
                 color: var(--apple-primary-on-dark); margin: 0 auto 0.5em; max-width: 90%; }
    .reveal p, .reveal li { font-size: clamp(0.8rem, 2vw, 0.95rem); line-height: 1.5; }
    .reveal code { background: rgba(255,255,255,0.08); color: var(--apple-primary-on-dark);
                   padding: 0.1em 0.4em; border-radius: 5px; font-family: ui-monospace, monospace; }

    /* Tables */
    .reveal table { font-size: clamp(0.65rem, 1.6vw, 0.85rem); border-collapse: separate;
                    border-spacing: 0; margin: 1em 0; width: 100%; max-width: 100%;
                    border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; overflow: hidden; }
    .reveal th { background: rgba(255,255,255,0.05); padding: 0.6em 0.8em; text-align: left;
                 font-weight: 600; border-bottom: 1px solid rgba(255,255,255,0.1); color: #fff; }
    .reveal td { padding: 0.5em 0.8em; border-bottom: 1px solid rgba(255,255,255,0.05); color: #fff; }

    /* Flow chart styles — see flow-css-cheatsheet.md for full set */
    .flow-chart { text-align: center !important; margin: 1em 0; font-size: 14px; }
    .flow-row { text-align: center !important; line-height: 2.2; margin: 0.4em 0; word-spacing: 0.3em; }
    .flow-node { display: inline-block !important; vertical-align: middle !important;
                 padding: 0.5em 1em; border-radius: 10px; font-size: 0.85em;
                 text-align: center !important; margin: 0.3em 0.25em; max-width: 220px; }
    .flow-node .node-label { display: block !important; font-size: 1em; font-weight: 600; }
    .flow-node .node-sub { display: block !important; font-size: 0.78em; opacity: 0.8; }
    .flow-arrow { display: inline-block !important; vertical-align: middle !important;
                  color: var(--apple-primary-on-dark); font-size: 1.1em; margin: 0 0.25em; }
    .flow-arrow::before { content: "↓"; }
    .flow-arrow.right::before { content: "→"; }
    .flow-decision { display: inline-block !important; padding: 0.5em 1.1em; border-radius: 14px;
                     background: rgba(255,204,0,0.18); border: 1.5px solid rgba(255,204,0,0.55);
                     color: #fff; font-size: 0.9em; font-style: italic; margin: 0.3em 0.25em; }
    .flow-node.long-term { background: rgba(41,151,255,0.18); border: 1px solid rgba(41,151,255,0.5); color: #fff; }
    .flow-node.tooling  { background: rgba(255,45,85,0.18);  border: 1px solid rgba(255,45,85,0.5);  color: #fff; }
    .flow-node.compute  { background: rgba(255,149,0,0.18);  border: 1px solid rgba(255,149,0,0.5);  color: #fff; }
    .flow-node.data     { background: rgba(175,82,222,0.18); border: 1px solid rgba(175,82,222,0.5); color: #fff; }
    .flow-node.output   { background: rgba(52,199,89,0.18);  border: 1px solid rgba(52,199,89,0.5);  color: #fff; }
    .flow-node.simple   { background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.22); color: #fff; }

    /* Section opener — APPLE KEYNOTE STYLE */
    .section-opener { text-align: center; padding: 1em 0 0.5em; margin: 0 auto 0.5em; max-width: 90%; }
    .section-opener .section-num { font-size: 0.75em; letter-spacing: 0.3em; text-transform: uppercase;
                                    color: var(--apple-body-muted); font-weight: 500;
                                    margin-bottom: 0.6em; display: block; text-align: center; }
    .section-opener h2 { font-size: clamp(1.5rem, 4vw, 2.2rem); margin-bottom: 0.3em; text-align: center; }
    .section-opener .section-lead { font-size: clamp(0.85rem, 2vw, 1.05rem); font-weight: 300;
                                    color: var(--apple-body-muted); line-height: 1.4;
                                    text-align: center; max-width: 60ch; margin: 0 auto; }

    /* Reveal controls */
    .reveal .controls { color: var(--apple-primary-on-dark); opacity: 0.5; }
    .reveal .progress { background: rgba(255,255,255,0.08); height: 3px; }
    .reveal .progress span { background: var(--apple-primary-on-dark); }

    @media (max-width: 600px) {
      .flow-node { font-size: 0.75em; padding: 0.45em 0.8em; max-width: 180px; }
      .flow-arrow { font-size: 1em; }
    }
    @media (max-height: 500px) and (orientation: landscape) {
      .reveal .slides > section { padding: 1.5vh 4vw; }
      .flow-node { font-size: 0.7em; }
    }
  </style>
</head>
<body>
  <div class="reveal">
    <div class="slides">
      <section data-markdown="slides/00-hero.md"
               data-separator="^---$" data-separator-vertical="^----$" data-separator-notes="^Note:">
      </section>
      <section data-markdown="slides/01-topic.md"
               data-separator="^---$" data-separator-vertical="^----$" data-separator-notes="^Note:">
      </section>
      <!-- Add more deck sections here -->
      <section data-markdown="slides/99-outro.md"
               data-separator="^---$" data-separator-vertical="^----$" data-separator-notes="^Note:">
      </section>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/markdown/markdown.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/notes/notes.js"></script>
  <script>
    Reveal.initialize({
      hash: true,
      controls: true,
      controlsTutorial: false,
      progress: true,
      slideNumber: 'c/t',
      overview: true,
      center: false,
      disableLayout: true,    /* KEY: kills transform: scale that breaks iOS Safari */
      transition: 'slide',
      transitionSpeed: 'fast',
      plugins: [ RevealMarkdown, RevealNotes ],
      markdown: { smartypants: false, gfm: true }
    });
  </script>
</body>
</html>
```

## Why this works

1. **No external CSS file** — single self-contained `.html`, zero cache issues.
2. **`disableLayout: true`** — the single most important fix. Without it, iOS Safari layout breaks.
3. **Inline-block everywhere** — survives transform/orientation changes.
4. **`text-align: center` on sections, `text-align: left` on body** — Apple keynote aesthetic.
5. **`visibility: hidden` + `.present`** — Apple's signature slide transition behavior.

## Customization points

| Change | Edit |
|---|---|
| Brand color | `.flow-node.long-term` etc. background/border; `--apple-primary-on-dark` |
| Font | `--apple-` in `:root` + `font-family` on `html, body` |
| Slide size | `padding: 3vh 5vw` on `.reveal .slides > section` |
| Theme (light/dark) | `--apple-surface-black` and text colors |
| Add section | New `<section data-markdown="slides/0X-name.md" ...>` block |
