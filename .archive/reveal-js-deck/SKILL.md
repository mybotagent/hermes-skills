---
name: reveal-js-deck
description: Build Reveal.js-based technical presentation decks with Apple-inspired design, GitHub Pages hosting, and a multi-deck portfolio structure. Covers wiki-to-slides conversion, iOS Safari-safe CSS, mermaid-free HTML/CSS flowcharts, and extensibility for adding new decks.
---

# Reveal.js + GitHub Pages Deck

Build a presentation deck from existing technical content (wiki, docs, notes), publish via GitHub Pages, and structure it so adding more decks later is one folder per topic. Default design language: Apple-inspired (SF Pro, dark mode, single Action Blue accent).

## When to use

- The user wants slides from existing prose (architecture write-up, system spec, project notes).
- The user wants a public, zero-build, key-driven deck (no Reveal.js plugin install, no webpack).
- The user wants a **portfolio** that can host multiple topic decks over time.
- The user mentions mermaid, flowcharts, architecture diagrams, system overviews, or "present this as a deck".

## When NOT to use

- One-off marketing hero page → use `creative/claude-design`.
- Real-time plot/3D/visual demo → use `creative/p5js` or `creative/manim-video`.
- Keynote/PowerPoint output requested → wrong tool family.

---

## Architecture (canonical)

```
portfolio/                                # GitHub Pages root
├── index.html                            # Portfolio homepage (deck catalog)
├── assets/
│   └── css/
│       └── deck.css                      # (Optional) shared deck styling
├── decks/
│   └── <deck-name>/
│       ├── index.html                    # Reveal.js entry for this deck
│       ├── slides/                       # One .md per slide series
│       │   ├── 00-hero.md
│       │   ├── 01-*.md
│       │   └── ...
│       └── README.md
└── README.md
```

**Why this shape**: Adding a new deck = new folder under `decks/`. Homepage card updates one block. No coupling between decks.

---

## Workflow (8 phases)

### Phase 1 — Content audit
1. Read source content (wiki/notes/spec).
2. List candidate topics. Ask user to pick **one** for v1 (avoid parallel-topic sprawl).
3. Identify domain-specific content (e.g. trading, finance, internal jargon). **Plan generalization upfront** — stock symbols, ticker names, proprietary terms → abstract to system-level pattern from day one.

### Phase 2 — Design language
1. Get a design system guide:
   ```bash
   npx getdesign@latest add apple --out ./decks/<name>/DESIGN-<brand>.md
   ```
   Available brands include: apple, airbnb, ibm, claude, figma, stripe. List more with `npx getdesign@latest list`.
2. Extract: color tokens, font stack, typography scale, radius, shadow.
3. Write CSS using those tokens, NOT generic defaults.

### Phase 3 — Deck structure
1. Sections: 5–8 (one for each major concept + Hero + Outro).
2. Markdown delimiters: `---` between horizontal slides, `----` for vertical (nested).
3. One deck entry point (`index.html`) referencing all `slides/*.md` files in order.

### Phase 4 — Slidiard content
1. First draft in **plain prose** in the user's language.
2. Identify structural diagrams. **Do NOT default to mermaid** — see pitfalls.
3. Add small explanatory captions under each diagram.

### Phase 5 — GitHub repo + Pages
1. `gh repo create <owner>/<repo> --public` (use `--homepage` to set future URL).
2. `git init` locally, configure user, add remote.
3. `git add . && git commit && git push -u origin main`.
4. **Activate Pages via API** (works around PAT scope issues):
   ```bash
   gh api -X POST /repos/<owner>/<repo>/pages \
     -f source[branch]=main -f source[path]=/
   ```
5. Wait ~60s for build, then `curl -sI <url>` to confirm HTTP 200.

### Phase 6 — Mobile-first CSS
See **Pitfalls → iOS Safari layout break**.

### Phase 7 — Iterative visual fix
User will send screenshots. Expect to:
1. Patch inline CSS in `<style>` block (not external file — see cache pitfall).
2. Switch `display: flex` → `display: inline-block` with `vertical-align: middle`.
3. Use `text-align: center !important` on flow containers.
4. Re-push → ask user to **hard refresh** (Safari: long-press reload, or incognito).

### Phase 8 — Polish
- Speaker notes in `Note:` blocks (Reveal markdown plugin picks these up).
- `hash: true` for deep linking.
- Keyboard shortcuts in slide: `←` `→` `↑` `↓` `ESC` `F` `S`.

---

## Pitfalls (CRITICAL — all hit during real sessions)

### 1. mermaid will silently break — plan HTML/CSS flowcharts from day one
**Symptom**: mermaid blocks render fine in dev, then break in browser with cryptic "too many arguments" / "Failed to launch browser process" errors.
**Why**: mmdc needs Puppeteer + working Chromium. Headless servers, missing libs, or mmdc version-specific bugs (mmdc@11.16 has argv parser bug) make it unreliable.
**Fix**: Replace every diagram concept with **HTML/CSS divs**:

```html
<div class="flow-chart">
  <div class="flow-row">
    <div class="flow-node long-term">
      <span class="node-label">🧠 Brain</span>
      <span class="node-sub">config</span>
    </div>
  </div>
  <div class="flow-arrow"></div>  <!-- ↓ by default -->
  <div class="flow-row">
    <div class="flow-decision">Q1 · Sensitive?</div>
  </div>
</div>
```

CSS pattern (inline-block based, NEVER flexbox):
```css
.flow-chart       { text-align: center !important; }
.flow-row         { text-align: center !important; line-height: 2.2; }
.flow-node        { display: inline-block !important; vertical-align: middle !important; }
.flow-arrow       { display: inline-block !important; vertical-align: middle !important; }
.flow-decision    { display: inline-block !important; }
.flow-group       { display: block; text-align: center; padding: 0.8em 1em; }
```

### 2. iOS Safari layout break (the classic three-strikes bug)
**Symptom**: Flow nodes overlap on iPhone Safari, but look perfect on desktop Chrome.
**Why**: Reveal.js uses `transform: scale()` to fit slides. iOS Safari's transform + flexbox interaction is buggy. Inline-block survives.
**Fix — apply all of these together**:
1. `<div class="section-opener">` not `<section>` — markdown plugin nests them as broken sub-slides.
2. `Reveal.initialize({ disableLayout: true, center: false })` — kill transform scaling entirely.
3. CSS:
   ```css
   .reveal .slides > section {
     position: absolute !important;
     top: 0; left: 0;
     transform: none !important;
     width: 100% !important; height: 100% !important;
     text-align: center;  /* Apple keynote default */
   }
   .reveal p, .reveal li, .reveal table { text-align: left; }
   .reveal h1, .reveal h2, .reveal h3    { text-align: center; }
   ```
4. Mobile viewport:
   ```html
   <meta name="viewport" content="width=device-width, initial-scale=1.0,
                                   maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
   ```
5. `touch-action: manipulation` on body (prevents double-tap zoom interference).

### 3. GitHub Pages CDN cache → users see old version
**Symptom**: User pushes fix, still sees broken layout.
**Why**: GitHub Pages serves `Cache-Control: max-age=600` but user-side cache lives longer.
**Fix**:
- Put all deck CSS **inline** in `<style>` (not external `deck.css`). Bypasses external cache entirely.
- Tell user to hard-refresh: Safari → Develop menu → Empty Caches, or simple incognito tab.
- For external CSS, add `?v=N` query string and bump on every change.

### 4. PAT lacks `workflow` scope → can't push `.github/workflows/*.yml`
**Symptom**: `git push` rejected with "refusing to allow a Personal Access Token to create or update workflow".
**Fix**:
- First commit: omit `.github/workflows/`.
- Push. Optionally add workflow later from the GitHub web UI (which uses the user's OAuth session, not PAT).
- Or use a PAT with `workflow` scope (out of scope if user provides a token).

### 5. Domain-specific content creeps into generic decks
**Symptom**: User asks for "architecture deck" but slides end up showing trading positions, ticker symbols, proprietary strategy names.
**Fix**: During **Phase 4**, scrub:
- Tickers / symbol references
- Buy/Sell/position jargon → "recommendation / alternative"
- Vendor-specific names → "external LLM" / "vector store"
- Money amounts → relative cost ratios

If user later says "remove stock stuff", you've already done 80% of the work.

### 6. Card index with `onclick="Reveal.slide(N)"` silently fails
**Symptom**: Click on card does nothing.
**Why**: Reveal.js doesn't expose `Reveal` as a global when loaded via ESM/type=module.
**Fix**: Use anchor links to separate deck pages instead:
```html
<a class="deck-card" href="decks/<name>/">
  <h3>Deck title</h3>
</a>
```
This is **also** better for multi-deck portfolios (each deck is independently addressable).

### 7. Vertical centering with `center: false`
**Symptom**: Slide content hugs top, overflows bottom.
**Fix**: Either `center: true` (Reveal handle) OR CSS `position: absolute; top: 0; left: 0; height: 100%` + flex/grid centered children. Pair with `disableLayout: true`.

---

## Standard reference deck (one-screen inspiration)

For an Apple-style dark deck with all the patterns above applied, see:
- `references/apple-deck-template.md` — full SKILL.md companion template
- `references/flow-css-cheatsheet.md` — copy-paste CSS for every flow node variant

---

## Quick start template

```bash
mkdir -p deck/slides
cd deck

# 1. Get design guide
npx getdesign@latest add apple --out DESIGN.md

# 2. Create slides/00-hero.md through slides/99-outro.md

# 3. Create index.html using the reveal-js + inline CSS template in references/

# 4. gh repo create <owner>/<repo> --public --homepage https://<owner>.github.io/<repo>/

# 5. Push + activate Pages
git push -u origin main
gh api -X POST /repos/<owner>/<repo>/pages -f source[branch]=main -f source[path]=/
```
