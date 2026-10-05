---
name: tech-presentation-deck
description: Author Reveal.js-based technical presentation decks, host on GitHub Pages, render reliably on iOS Safari and desktop. Apple-inspired design (white or dark mode). One-source slides file, inline CSS, hand-authored SVG diagrams. Triggered by "make a deck", "slide deck", "present this content", "wiki → slides", "publish to github.io".
---

# Tech Presentation Deck

Class of work: turn a body of source content (wiki, docs, notes, system architecture) into a Reveal.js presentation deck that lives on GitHub Pages and renders reliably across browsers including iOS Safari.

## When to use

- User asks to publish documentation / wiki / notes as a presentation deck
- User asks to make slides from source material
- User wants a deck hosted on `github.io` (project page or user page)
- User wants Apple-inspired design for a technical deck

## What this skill is NOT for

- Reactive HTML mockups (use `creative/sketch` instead)
- Mermaid-based decks rendered at runtime (use only if Chromium is available locally; otherwise hand-author SVG)
- Spreadsheet-style reports (different format)
- Decks designed to be exported as PDF (use Keynote / `pptx` tooling)

## Pipeline (use in order)

1. **Inventory + strip**: read every source page once. Tag each chunk as `[use]` (actually configured), `[planned]` (intended but not set up), or `[remove]`. Default: keep only `[use]`. The user will repeatedly ask to remove hypotheticals.
2. **Coalesce one source file**: all slides go into `slides/all-slides.md` under a `slides/` directory at the deck root. Single source avoids Reveal.js double-counting when multiple `<section data-markdown="X.md">` blocks are present.
3. **Inline CSS in `index.html`** (do not link external `.css`). External CSS is the single biggest source of cache-related issues on GitHub Pages. Inline CSS survives caching and version-suffix CDN URLs.
4. **Author SVG diagrams directly** instead of using mmdc. mmdc frequently fails in sandboxed dev environments (Chromium permission errors). Hand-authoring SVG is reliable and produces smaller files. Use `<svg viewBox="0 0 W H" width="W" height="H" preserveAspectRatio="xMidYMid meet">` to ensure `<img>` renders correctly.
5. **Apply Apple design tokens** (see Design Tokens section below).
6. **Configure Reveal.js** with `disableLayout: true` — *essential* for iOS Safari. Without it, Reveal applies `transform: scale()` which clips `flexbox`/`inline-block` content on mobile.
7. **Make every section scrollable**: `overflow-y: auto !important` on `.reveal .slides > section`. Better than clipping large tables or long code blocks.
8. **Generalize names** when the deck describes a structural pattern rather than the literal user setup (e.g., `mybotagent` → `org-a`, `hermes-wiki` → `project-i`). The user explicitly requests this when sharing patterns with external audiences.
9. **Cache-bust**: append `?v=N` to CDN URLs (Reveal.js, mermaid if used) and add `<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">` to `<head>`. GitHub Pages legacy mode caches with `max-age=600` by default.
10. **User page repo**: if user wants `https://<username>.github.io/` to render the deck (not `<username>.github.io/<repo>/`), create a separate repo named `<username>.github.io` containing at minimum `index.html` (a redirect or a small landing).

## Reveal.js essentials (verified working pattern)

```js
Reveal.initialize({
  hash: true,
  controls: true,
  progress: true,
  slideNumber: 'c/t',
  overview: true,
  center: false,        // we center via CSS, not Reveal option
  disableLayout: true,  // <-- critical for iOS Safari
  transition: 'slide',
  transitionSpeed: 'fast',
  plugins: [ RevealMarkdown, RevealNotes ],
  markdown: { smartypants: false, gfm: true }
});
```

Required CSS scaffolding for the slide root (must be present, inline):
```css
.reveal { width: 100%; height: 100%; }
.reveal .slides { position: absolute; inset: 0; transform: none !important; }
.reveal .slides > section {
  width: 100% !important; height: 100% !important;
  position: absolute !important; top: 0; left: 0;
  display: none; padding: 3vh 3.5vw !important;
  text-align: center !important;
  overflow-y: auto !important; overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  background: <canvas>;
}
.reveal .slides > section.present { display: block !important; }
```

Flow chart nodes use `display: inline-block; vertical-align: middle;` — **never flexbox**. Arrow connectors are CSS lines + `border-triangle` arrowheads (see `references/reveal-js-mobile-pitfalls.md`).

## Apple design tokens (use these verbatim)

```css
:root {
  --primary:           #0066cc;   /* Apple Action Blue */
  --primary-focus:     #0071e3;
  --primary-on-dark:   #2997ff;   /* Apple Blue on dark */
  --ink:               #1d1d1f;
  --body:              #1d1d1f;
  --body-muted:        #6e6e73;
  --canvas:            #ffffff;
  --canvas-parchment:  #f5f5f7;   /* Apple signature card background */
  --divider:           #d2d2d7;
  --hairline:          #e0e0e0;
  --surface-black:     #000000;
}
.reveal { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", sans-serif; }
```

## User-style corrections specific to this class

These were corrections the user *repeatedly* made during deck iteration. Embed them so the next deck starts well:

- **No emoji** in any slide text (AI-tells the user dislikes)
- **No verbose subtitle `<p>` that just restates the h1** — drop them. The user calls these "unnecessary pages" and asks to delete them.
- **Strip mentions of systems/tools that aren't actually configured** (e.g., don't talk about Ollama/GraphRAG/Neo4j/pgvector in a deck that doesn't use them). The user explicitly says "remove the things we don't actually use".
- **Strip planning content** ("Resolution Plan", "Next Steps", "Series Expansion", future-state forecasts). Show current state only.
- **Generalize proper nouns** when the deck is meant to be a structural reference (org names, repo names, persona names → `org-a`, `project-a`, `the assistant`, `the user`). The user does this every time the deck is intended for external/structural audiences.
- **Reveal.js `transform: scale()` clips content on iOS Safari**. Always use `inline-block` for nodes/arrows. Never flexbox inside slides.
- **Cards on hover scale badly**. If you must, use `transform: scale(1.04)` on node:hover with explicit `display: inline-block`.
- **Reveal.js markdown plugin + `display: flex` on sections breaks layout.** Use `display: block` on `.flow-chart` / `.flow-row`, and `inline-block` on children.

## Pitfalls (extended)

See `references/reveal-js-mobile-pitfalls.md` for the full collection of iOS Safari / Reveal.js interaction bugs.

See `references/github-pages-cache-busting.md` for the cache behavior GitHub Pages exhibits and how to defeat it.

See `references/svg-authoring-pitfalls.md` for hand-authored SVG tips and what mmdc does that you can replicate manually.

## Directory layout (recommended)

```
<repo>/
├── index.html                      # portfolio homepage (if any)
├── decks/
│   └── <deck-name>/
│       ├── index.html              # Reveal.js deck entry (single one-pager)
│       ├── DESIGN.md               # design notes
│       ├── README.md               # deck-specific notes
│       └── slides/
│           └── all-slides.md       # single source of all slide content
└── assets/
    ├── img/                        # SVG diagrams referenced by slides
    │   ├── flow-1.svg
    │   ├── flow-2.svg
    │   └── ...
    └── css/                        # optional external CSS (avoid if possible)
```

## Templates

- `templates/deck-index-html.template` — known-good Reveal.js + inline CSS skeleton
- `templates/deck-all-slides-md.template` — known-good slide content skeleton
- `templates/deck-portfolio-index-html.template` — minimal Apple-style portfolio landing page

## Verification

After every push, verify in order:

1. Wait at least 60s (GitHub Pages legacy mode build + edge cache)
2. `curl -s -o /dev/null -w '%{http_code}' https://<owner>.github.io/<repo>/` → must be 200
3. For each SVG: `curl -s -o /dev/null -w '%{http_code}'` on the SVG path → must be 200
4. In a **private/incognito window** (not cached), open the URL — confirm slide count and content render
5. On mobile (or via Safari UA dev tools), confirm no clipping at the bottom of slides

If slide count > expected: usually a fragment conflict (e.g., user typed `#/13` and there are only 10 slides). Coalescing all slides into one `.md` file fixes this.

## Don't-capture list

- Don't record "GitHub Pages doesn't work" or "Reveal.js is broken" as blanket statements. Record the specific fix (`disableLayout: true`, `Cache-Control` headers, CDN cache-buster).
- Don't record per-deck content. The templates are the durable part; specific slide text is session-scoped.
- Don't assume Reveal.js versions are stable forever. Pin versions in CDN URLs (e.g., `reveal.js@5.1.0`) and bump deliberately.
