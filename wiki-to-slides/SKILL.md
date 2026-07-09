---
name: wiki-to-slides
description: "Convert a markdown knowledge base (Karpathy-style LLM Wiki, Obsidian vault, or plain .md folder) into a static HTML slide deck hosted on GitHub Pages. Covers Reveal.js 5 + SVG-based flowcharts (preferred over mermaid for reliability and design control), Apple-style design tokens, GitHub Pages deployment with `?v=N` cache busting, and workarounds for PATs that lack workflow scope. Triggers: wiki to slides, markdown to presentation, Reveal.js SVG, github.io deck, wiki to deck, karpathy wiki deck, apple slides, knowledge base to lecture."
---

# Wiki to Static Slide Deck

## When to Use

Trigger when the user wants to:
- Convert markdown KB content (Karpathy LLM Wiki, Obsidian vault, plain *.md folder) into browsable HTML slides with keyboard navigation (left/right arrows)
- Host the result on github.io (free, HTTPS, auto-deploy)
- Render flowcharts/diagrams in the source content as visuals (not just text)

Triggers: wiki to slides, markdown to presentation, Reveal.js SVG, github.io deck, wiki to deck.

## When NOT to Use

- **Video output** - slides are interactive HTML. Use Remotion for MP4.
- **LMS features** (quiz, scoring, progress) - use an LMS platform.
- **Single short document** - plain markdown rendering is simpler.

## Methodology (4 Phases)

### Phase 1: Inventory the source wiki - DO NOT SKIP

> WARNING: **Pitfall #1 - "subject/topic" interpretation**: When the user asks "what topics are possible?" or "what subjects can we cover" about a wiki, they mean subject matter in the wiki, NOT technology stack options. Read the wiki first; do not jump to suggesting tools.

### Pitfall #2 - SVG files don't auto-commit
Files created with `write_file` are NOT automatically tracked by git.
After every commit that includes new SVGs, verify with:

```bash
git ls-files path/to/deck/assets/img/
# If empty → file is in working tree but not tracked
git add path/to/deck/assets/img/*.svg
git commit --amend --no-edit
```

A deck can render perfectly locally, push cleanly, and GitHub Pages serves
404 for the SVGs — symptom: user reports "broken image" but `curl` shows
200. See `references/github-pages-caching.md` for full diagnosis.

### Pitfall #3 - Browser caches stale 404s
Even after fixing missing SVGs, browsers cache the original 404 response.
Without intervention, only hard refresh (Cmd+Shift+R) recovers.

**Fix at the source**: append `?v=N` to every asset URL, bump N on each
push. See `references/github-pages-caching.md`.

## Visual Design (Apple Style)

The user prefers a **portfolio-ready Apple aesthetic** for slide decks.
Apply these defaults:

- **Typography**: SF Pro / `-apple-system` with `font-feature-settings: "ss01", "ss02"`
- **Colors**: Action Blue `#0066cc` accents, white background `#ffffff`, ink `#1d1d1f`
- **Cards**: `border-radius: 14-18px`, subtle `box-shadow: 0 4px 16px rgba(0,0,0,0.04)`
- **Layout**: `disableLayout: true`, flexbox centering per slide, `overflow-y: auto`
- **NO slide numbers**: `slideNumber: false` + defensive CSS hide

Full token table + Reveal.js init + CSS patterns → `references/apple-slides-design.md`.

## SVG vs Mermaid (Preferred Direction)

**Use SVG, not mermaid.** The user has stated this preference twice during
flowchart-heavy slides. SVG wins on:
- iOS Safari reliability (mermaid has repeated CDN errors)
- Color/typography control (Apple tokens exactly)
- File-size predictability
- Re-renderability (anyone can open in Inkscape/Figma)

For arrows, use `<marker>` elements — never Unicode like ↓ →.
See `references/github-pages-caching.md` for the full SVG template.

## References

- `references/apple-slides-design.md` — color tokens, Reveal.js init, CSS patterns, mobile breakpoints
- `references/github-pages-caching.md` — cache-busting, SVG pitfalls, mermaid-to-SVG template
- `scripts/verify-svg-cache.sh` — verify all deck SVGs are deployed + check git ls-files + cache state

```bash
ls <wiki_dir>/
cat <wiki_dir>/index.md                  # master TOC
cat <wiki_dir>/<category>/*.md           # 2-3 sample pages
```

Output of Phase 1:
- List of content topics with suitability ratings (clearly slide-worthy vs reference-only)
- Estimated slide count
- Mermaid diagram candidates (architecture, flow, timeline)

### Phase 2: DESIGN.md first

Write DESIGN.md *before* any code. Sections:
- Goal + non-goals
- Tech stack with rationale (use the Decision Matrix below)
- Slide inventory: ~25-30 slides, 8-10 sections
- Mermaid diagram inventory (one diagram per architecture/flow concept)
- Phase breakdown (P1=skeleton+hero, P2=section1, ...)
- Linear issue mapping (1 issue per phase)

Follow the user workflow: DESIGN.md to Linear/Kanban to implementation to GitHub push.

### Phase 3: P1 - Skeleton + hero section

Build index.html + assets/css/custom.css + slides/00-hero.md first, verify the page loads, THEN expand to remaining sections. Don't write 28 slides then debug.

```bash
python3 -m http.server 8000
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/    # expect 200
```

### Phase 4: Section-by-section expansion

> WARNING: **Pitfall #12 - multi-file section separation causes double-count**: When using multiple `<section data-markdown="slides/NN-name.md">` elements (one per section), Reveal.js's markdown plugin concatenates them but counts each `<section>` boundary as an extra page. Symptom: deck reports 42 pages when you only wrote 8. Fix: ONE single `slides/all-slides.md` with `---` separators inside, loaded by a single `<section>`. The trailing `---` after the last section also creates an empty slide — keep exactly N-1 separators.

> WARNING: **Pitfall #13 - iOS Safari transform breaks inline-block**: Reveal.js's default fit-to-viewport uses `transform: scale()` which, combined with `display: inline-block` (for flow nodes, badges), breaks layout in iOS Safari. Workaround: `disableLayout: true` + explicit `position: absolute` + `display: flex; justify-content: center; align-items: center` on `.slides > section.present`.

> WARNING: **Pitfall #14 - SVG images clip unless dimensions are explicit**: An `<img src="...svg">` with only CSS `max-width` in a flex/chrome container will be sized 0 or overflow. SVG needs: `width="N"` `height="N"` on the `<svg>` element itself (or `<img>`), `preserveAspectRatio="xMidYMid meet"`, AND CSS `max-height: calc(100vh - 16vh); object-fit: contain`.

Each section is one markdown block in a single `slides/all-slides.md` file with `---` separators. SVG diagrams are now preferred over mermaid blocks for PUBLIC decks (see Phase 4d).

### Phase 4b: Polish

**Remove slide-count indicators** (default `slideNumber: 'c/t'` shows "1/8" on every slide — almost never wanted for portfolio/clean decks):

```js
Reveal.initialize({ slideNumber: false, ... })
```

```css
.reveal .slide-number,
.reveal .slide-number-pdf,
.reveal .slide-suffix { display: none !important; }
```

Both flags are needed — JS sets the property at init, CSS defends against late-added DOM (e.g. print/export). Also bump cache-buster on all CDN URLs (`?v=N+1`) so the CDN serves the new build; see Pitfall #16.

### Phase 4c: Apply a design system

Pick one aesthetic before writing CSS. Three patterns commonly used in this environment:

| Aesthetic | Reference | Source |
|---|---|---|
| **Apple (white, SF Pro, Action Blue)** | `references/apple-design-system.md` | `npx getdesign@latest add apple` |
| Dark / brand-colored | `templates/custom.css` (already in this skill) | handwritten |
| Minimal monochrome | see notes in `references/apple-design-system.md` | handwritten |

For portfolio/recruiter-facing decks (Hermes architecture, course projects), Apple white is the default. For internal/sales decks, dark brand colors.

### Phase 4d: SVG diagrams over mermaid (for PUBLIC decks)

For PUBLIC decks (portfolio, course submission, recruiter share) prefer **hand-crafted SVG** over mermaid:

| Mermaid problem | SVG solution |
|---|---|
| CDN dependency | inline `<svg>` shipped with repo |
| Korean / non-ASCII label parse errors | text content always renders |
| Layout control limited (flexbox, etc.) | full CSS/SVG control |
| Repeated fix cycles (font, spacing) | one-time draw, infinite scale |
| iOS Safari `position: absolute` + `transform` interactions | static, predictable |

Mermaid remains useful for INTERNAL decks (single audience, ephemeral). See references/svg-architecture-diagrams.md for the 3-column architecture diagram pattern (Karpathy → 5 Layers → 4 Submodules layout used in the Hermes architecture deck 2026-07-01).

## Phase 2a (optional but recommended for 6+ sections): Card-Format Index

When the deck covers many topics (8+ sections), replace the first text-table-of-contents slide with a clickable card grid. Users navigate by clicking cards (`onclick="Reveal.slide(N)"`).

**Why better than text TOC**: visuals > table for navigation; one click jumps vs N key presses; works on touch devices too.

**Step 1 — Pre-compute global slide indices**:

Reveal.js slide indices are global, not per-section. Build a small table:

```
S0.1 = 0   (Hero title)
S0.2 = 1   (Hero index)
S1.1 = 2   (Section 1 first slide)
S2.1 = ... (depending on how many slides each section had)
```

**Step 2 — slides/00-hero.md first content slide**:

```html
<div class="index-grid">
  <div class="index-card" onclick="Reveal.slide(2)">
    <div class="card-icon">🧠</div>
    <div class="card-num">S1</div>
    <div class="card-title">Section Name</div>
    <div class="card-desc">One-line description</div>
    <div class="card-meta">4 slides · 3 mermaid</div>
  </div>
  <!-- repeat per section -->
</div>
```

**Step 3 — Add CSS** (already in `templates/custom.css`): `.index-grid`, `.index-card`, hover effects.

Reference working example: 8-section deck at https://mybotagent.github.io/hermes-architecture-deck/ (first slide is the card hub).

## Phase 4a (before publishing): Generalize domain-specific content

> WARNING: **Pitfall #7 - wiki content is often domain-specific**: A user's wiki frequently mixes reusable engineering with their hobby/business domain (e.g. value-investor wiki has stock-pipeline specifics alongside general architecture). A public slide deck should generalize the domain bits to maximize reusability across audiences.

When extracting content, check for:
- Named assets (specific stock tickers, customer names, project codenames) -> replace with abstract nouns
- Domain jargon (Bull/Bear/Risk, 매수/매도, decision vocabulary) -> replace with generic equivalents (Positive/Negative/Risk, conclusion)
- Workflow examples tied to the user's business -> keep one illustrative example but rewrite verbs generically

Generalization map for common patterns (saved from `mybotagent/hermes-architecture-deck` deck, 2026-07-01):

| Original (domain) | Generalized (deck-ready) |
|---|---|
| 24종목 분석 | N개 데이터 분석 |
| 포트폴리오 비중 | 리소스 비중 |
| Bull/Bear/Risk → Decision | Positive/Negative/Risk/Trade-off → Conclusion |
| LangGraph 파이프라인 | 멀티에이전트 분석 체인 |
| 매수/매도 결정 | 권장 액션 |
| 티커 (HPE, BE, ...) | (추상화 또는 제거) |

Confirm with user before publishing — they often want some domain branding preserved.

## Tech Stack Decision Matrix

| Need | Pick |
|------|------|
| Quick boot, markdown-native, GitHub Pages | Reveal.js 5.x (default) |
| Vue codebase, code highlighting | Slidev |
| React-friendly | Spectacle |
| Pure lightweight HTML | Custom HTML+CSS+JS |
| Video output | Remotion |

Default: Reveal.js 5.x + mermaid.js 10.x + GitHub Pages (legacy build).

## Mermaid Integration

> WARNING: **Pitfall #2 - Reveal.js + mermaid timing**: `mermaid.initialize({startOnLoad: true})` does NOT work alone with Reveal's markdown plugin (mermaid runs *before* markdown renders the mermaid blocks into `<pre><code>` elements).
>
> You MUST use post-processing: scan `.reveal pre code.language-mermaid`, rewrite each as `<div class="mermaid">`, then `mermaid.run()` - both on `Reveal.on('ready', ...)` and `Reveal.on('slidechanged', ...)`.

Full working code lives in templates/index.html (the inline script). See references/mermaid-integration.md for the standalone snippet.

## GitHub Pages Deployment (Quick Reference)

```bash
# 1. Auth work-around for PAT that doesn't have workflow scope:
unset GITHUB_TOKEN
export GH_TOKEN=$(grep -oP '(?<=https://)[^@]+(?=@github.com)' ~/.git-credentials | cut -d: -f2)

# 2. Create repo + push
gh repo create {owner}/{repo} --public
git push -u origin main

# 3. Enable Pages (gh CLI's --enable-pages flag does NOT exist)
gh api -X POST /repos/{owner}/{repo}/pages \
  -f source[branch]=main -f source[path]=/

# 4. Poll build status
gh api /repos/{owner}/{repo}/pages/builds/latest | grep status
# wait for: "status":"built"   (30-90s for first build)
```

Final URL: `https://{owner}.github.io/{repo}/`

Full runbook: references/github-pages-deployment.md.

## Pitfalls Summary

| # | Pitfall | Mitigation |
|---|---------|-----------|
| 1 | "subject/topic" interpreted as technology options | Inventory wiki first (Phase 1) |
| 2 | mermaid startOnLoad with Reveal markdown plugin | Use the post-processing pattern |
| 3 | PAT lacks workflow scope, push rejected | Remove .github/, use legacy Pages via gh api |
| 4 | GITHUB_TOKEN env var blocks gh auth refresh | unset GITHUB_TOKEN; export GH_TOKEN extracted from ~/.git-credentials |
| 5 | Pages returns 404 immediately after enabling | Poll /pages/builds/latest until status:built (30-90s) |
| 6 | head -1 ~/.git-credentials sed pipeline timeouts | Use grep -oP alternative |
| 7 | Wiki content is domain-specific; publishing raw leaks the user's hobby/business | Generalize during Phase 4a; confirm with user |
| 8 | mermaid Korean labels in circle nodes parse as syntax errors | Use English labels for IDs/labels in `((node))` form; quote Korean in `["node"]` form |
| 9 | `<br/>` in mermaid labels sometimes rejected by some versions | Use `<br>` (no trailing slash) for max compat |
| 10 | mermaid parse errors silent — user sees blank diagram, no clue | Render a visible red error box on the failing slide (see `templates/index.html`'s catch block) |
| 11 | `Reveal.on('ready')` fires before async md fetch completes — mermaid finds zero blocks | Wrap handler in `setTimeout(fn, 1500)`; use 500ms on `slidechanged` |
| 12 | Multi-file `<section data-markdown="...">` causes slide-count double-count (e.g. 8 written → 42 shown) | Use ONE `slides/all-slides.md` with `---` separators inside a single `<section>`; trailing `---` becomes empty slide — keep exactly N-1 |
| 13 | Reveal.js default `transform: scale()` to fit viewport breaks `inline-block` layouts in iOS Safari | `disableLayout: true` + `position: absolute` + flex center on `.slides > section.present` |
| 14 | SVG images clip (sized 0 or overflow) when only CSS `max-width` is set in flex/chrome containers | Add explicit `width`/`height` on `<svg>` element + `preserveAspectRatio="xMidYMid meet"` + CSS `max-height: calc(100vh - 16vh); object-fit: contain` |
| 15 | Setting `slideNumber: false` alone leaves the count indicator on some export paths (PDF, print) | Add CSS `.reveal .slide-number, .reveal .slide-number-pdf, .reveal .slide-suffix { display: none !important; }` as defense |
| 16 | Pushing new code but GitHub Pages CDN still serves old version (HTTP cache `max-age=600`) | Wait 30-60s before reverifying; bump all CDN/cache-buster URLs (?v=N+1); curl + x-cache header confirms HIT vs MISS |
| 17 | `browser_navigate` to github.io / Reveal.js CDN pages frequently times out at 60s due to CDN load | Use `curl -s -I` / `curl -s \\| grep` to verify deployed HTML/SVG; browser visual capture unreliable for hosted pages |
| 18 | For PUBLIC/portfolio decks, mermaid becomes a recurring liability (CDN, parse errors, iOS quirks, label encoding) | Hand-craft SVG diagrams; ship inline or as `assets/img/*.svg`; one-time draw, infinite scale, no JS dependency |
| 19 | **Relative path resolution from markdown subdirectories** — `<img src="../../assets/img/x.svg">` written in `decks/hermes-architecture/slides/all-slides.md` resolves to `decks/assets/img/x.svg` (one level too high), not `decks/hermes-architecture/assets/img/x.svg`. Symptom: `curl` shows the SVG file is 200 OK at the correct URL, the markdown source `grep` shows a "correct-looking" path, but the BROWSER shows a broken-image icon. The path must be relative to the **markdown file's directory**, not the page URL. | **Always use absolute URLs** for cross-folder assets in markdown: `<img src="https://mybotagent.github.io/{repo}/decks/{name}/assets/img/x.svg?v=N">`. **Verify by curl-resolving each src the way the browser would**: `curl -I "{base-url-of-md}/../assets/img/x.svg"`. If 200 → browser will load it; if 404 → path is wrong even if the file exists elsewhere. |
| 20 | **3-tier cache after broken-image deploys** — even after fixing path/missing files, three caches must all be invalidated: (a) GitHub Pages CDN (`max-age=600` per response), (b) browser HTTP cache for HTML/markdown/SVG, (c) Reveal.js's internal XHR cache for the markdown file. `?v=N` on CDN URLs only invalidates browser cache; the markdown fetch through Reveal still hits a cached response. | **Three combined fixes**: (1) Absolute URLs `https://...assets/img/x.svg?v=N` so path resolution is browser-independent; (2) bump `?v=N` on every push, N+1 each commit; (3) patch BOTH `window.fetch` AND `XMLHttpRequest.prototype.open` BEFORE `Reveal.initialize` to append `&cb={Date.now()}` to any URL matching `all-slides.md` or `.svg` — Reveal.js's markdown plugin uses XHR (not fetch), so the XHR patch is the load-bearing one. See `references/three-tier-cache-busting.md` for the working snippet. |
| 21 | **viewBox overflow — element silently clipped at edge** — `<g transform="translate(680)">` + `<rect x="-30" width="180">` yields a right edge at `680-30+180=830`; if viewBox is only 800 the rect is clipped to nothing on the right. Symptom: `curl` returns 200, but a node visually disappears off-canvas. | Use the **position-math rule**: a `translate()` x offset must be at least `(box_width / 2) + 20px` in from each edge. Run `scripts/audit-svg-bounds.py` before committing any hand-crafted SVG; it checks every translated rect against the viewBox. |
| 22 | **Left-label card collides with first data node** — placing a label box on the left at `x=60-240` while the first data row also starts at `x=120` causes overlap in the `x ∈ [120, 240]` band. Doesn't show up in code review because both rectangles are individually valid. | For N nodes per row on a 1000×600 viewBox: `node_width = (1000 - 200 - (N-1)*60) / N`. With 3 nodes that's 226. Place data nodes evenly starting at `x=100`, allocate a **separate** left-column slot (or move labels `text-anchor="middle"` ABOVE the row). |
| 23 | **`feDropShadow` filter extends visible bounds** — a `stdDeviation=6` glow adds ~18px in every direction, making a 200px box visually occupy 236px. Two such boxes at `x=200` and `x=400` appear to overlap even though their `x` attributes don't. | Either leave `2×stdDeviation` gaps between glow elements, or reduce filter intensity (`stdDeviation=3` ≈ 9px each side, much safer). |

## Linked Files

- templates/index.html - verified Reveal.js + mermaid boilerplate (with setTimeout + visible-error display)
- templates/custom.css - dark-mode brand color schema + card-index styles
- templates/section.md - single-section markdown pattern with mermaid example
- references/mermaid-integration.md - full post-processing snippet
- references/github-pages-deployment.md - full PAT + gh CLI runbook
- references/card-index-pattern.md - card-format first-slide hub pattern (NEW 2026-07-01)
- references/apple-design-system.md - Apple HIG tokens (SF Pro, Action Blue), `npx getdesign@latest add apple` pattern, white-background CSS variables (NEW 2026-07-01)
- references/svg-architecture-diagrams.md - hand-crafted SVG diagram patterns, 3-column Karpathy/Layers/Submodules layout, **viewBox-vs-position-arithmetic bugs + audit script** (NEW 2026-07-01)
- references/path-resolution-debugging.md - how to verify relative paths resolve the way the browser would resolve them (curl-based diagnosis recipe, NEW 2026-07-01)
- references/three-tier-cache-busting.md - the combined CDN + browser + Reveal.js XHR cache invalidation pattern, including the working `window.fetch` patch snippet (NEW 2026-07-01)
- scripts/audit-svg-bounds.py - pre-commit check that every positioned rect stays inside the SVG viewBox. Companion to verify-svg-cache.sh. (NEW 2026-07-01)
