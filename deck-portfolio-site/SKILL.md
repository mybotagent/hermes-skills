---
name: deck-portfolio-site
description: Self-hosted, Apple-style multi-deck presentation portfolio on GitHub Pages for showcasing real work — covers user page setup, multi-deck structure, Reveal.js with inline CSS, content-filtering discipline, and GitHub Pages build-stuck diagnosis.
version: 1.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [creative, deck, portfolio, github-pages, reveal-js, design-system, apple]
    related_skills: [creative/claude-design, creative/popular-web-designs, design-md]
---

# Deck Portfolio Site

Build a persistent, GitHub-Pages-hosted portfolio where the home is a user page and each topic is a self-contained Reveal.js deck. Designed for engineers and builders who want to publish real work, not generic slide decks.

## When To Use

Use when the user asks to:

- "publish my slides as a website"
- "build a portfolio of my work / projects / system"
- "host my deck on GitHub Pages"
- "make a multi-topic presentation site I can extend"
- "show how I use my system, with actual config / code excerpts"
- "apply Apple (or any specific brand) design and deploy"

Do NOT use for:

- one-off standalone HTML decks → use `creative/claude-design`
- browser-only mockups / prototypes → use `creative/claude-design` or `creative/sketch`
- design token spec authoring alone → use `design-md`

## Architecture

```
<user>.github.io/                          ← User page (entry point)
  └─ index.html                           ← Redirect or full homepage

<user>/<portfolio-repo>/                  ← Project page (portfolio root)
  ├─ index.html                            ← Portfolio home (card grid of decks)
  ├─ assets/                               ← Shared CSS / images
  ├─ README.md
  ├─ DESIGN.md
  └─ decks/                                ← One folder per deck
      └─ <deck-name>/
          ├─ index.html                    ← Reveal.js entry + inline CSS
          ├─ all-slides.md                 ← All slide content (single MD file)
          └─ README.md
```

Each deck folder is independent and self-contained. Adding a deck = new folder under `decks/` + one card in the portfolio root. Decks never depend on each other.

## Tech Stack

| Component | Choice | Why |
|---|---|---|
| Slide engine | **Reveal.js 5.x** (CDN) | Mature, markdown plugin, keyboard nav, no build |
| Design system | **`npx getdesign@latest add <brand>`** | One command → full DESIGN.md tokens |
| Markup | **Markdown + inline HTML** | Slides in `.md`; HTML/CSS flows inline |
| Style | **Inline `<style>` in `index.html`** | No separate CSS file = no cache miss |
| Hosting | **GitHub Pages (legacy mode)** | No build, free, HTTPS |
| Deploy | **`git push` to `main`** | Pages auto-rebuilds |

## Content Discipline (CRITICAL — learned through iteration)

The user's repeated emphases, distilled into rules:

1. **Show applied work, not generic explanations.**
   - Include actual `config.yaml`, `soul.md`, `user.md`, `skill.md` excerpts you wrote.
   - For each component, show how YOU configured it in production.

2. **Drop sections about things you haven't actually built.**
   - No "Resolution Plan" / "Future Work" / "What's NOT Applied" sections unless explicitly asked.
   - Drop generic overview slides — show production usage from slide one.

3. **Lots of flowcharts AND lots of body text per slide.**
   - Each slide should have 2-4 HTML/CSS flow nodes + substantive paragraphs.
   - Both, not either-or. The user said "플로우차트도 많으면 좋을 것 같고, 텍스트도 많으면 좋을 것 같아".

4. **Distill ruthlessly.**
   - ≤15 slides per deck. More = filler.
   - Title + 8-12 production slides + links.

5. **No generic system explainers.**
   - "Hermes is an agent with seven components" → drop.
   - "We configured Brain with deepseek-chat because..." → keep.

6. **One deck = one big topic.**
   - Don't index multiple unrelated topics. The user said "대주제 한개임".

7. **Index cards: one card per deck. Clicking is unreliable.**
   - Keyboard nav as primary; cards are visual entry points only.
   - Don't rely on `onclick="Reveal.slide(n)"` in production — it breaks in nested deck contexts.

8. **Apply the design system fully.**
   - User said "디자인 제대로 적용 안 된 것 같음" and "내가 줬단 디자인 템플릿으로" multiple times.
   - Partial application reads as "not Apple". Use tokens verbatim.

9. **Source from existing canonical docs — don't invent frameworks.**
   - When asked to "explain X", build the deck FROM existing primary sources (official docs, existing wiki pages, GitHub READMEs). Never invent your own taxonomy/framework.
   - The user said: "기존 헤르메스 공식문서를 토대로 알려줘" → lead with a citation block / "Primary Sources" section in the deck itself, and quote/condense from those sources, not your own framework.
   - Pattern for docs-as-decks: each slide footer should reference the source (e.g. "Source: hermes-agent.nousresearch.com/docs §X").

10. **English-only output. Strip Korean + personal nicknames from public pages.**
    - `html lang="en"` always. Never `ko`.
    - Strip personal nicknames (e.g. 채니봇) and Korean operator names from deck pages that go on GitHub Pages — those are internal-chat identifiers, not user-facing artifacts.
    - Translate every Korean heading, label, table cell, footnote to natural English. Do not leave fragments: "한글 들어간것은 영어로 수정".
    - User correction trigger (verbatim): "채니봇이라는 글자는 빼고 한글 들어간것은 영어로 수정하고 다른 페이지에서 불필요한 것들 제거해야함".

11. **Readability: full English sentences, not fragments.**
    - User said: "가독성이 안좋은 text 개선이 필요함".
    - Tables: `<td>` content should be a phrase or sentence, never a 1-2 word stub. Compare "memory 한계 90% 알림 (자동 압축 X)" → "90% memory-cap alert (no auto-compression)".
    - Footnotes/small text: write complete micro-sentences, not compressed keywords.
    - Headlines: phrase as questions or claims, not bare nouns ("왜 이 4-Layer인가" → "Why These 4 Layers").

12. **Drop closing/transition slides. No "끝. Push & validate." pages.**
    - User explicit correction: "끝 이라는 페이지도 필요없고 불필요하게 링크 걸지 말아야함".
    - The final slide should be substantive content (e.g. open workstreams, operational assets), not a "thanks/contact/Q&A" filler.
    - Remove redundant footer link bars (Portfolio · hermes-wiki · meeting-notes) on closing slides — links belong only in the assets table where they're load-bearing.

13. **Don't re-include internal jargon in public-facing decks.**
    - Phrases like "단일공식 검증 후 안전화 시", "M3 활용도 criterion 실측 진행 중", "디자인-실행 갭 20% 남음" are internal-session shorthand. They confuse outsiders. Either spell them out in plain English or drop the slide.

## Workflow

1. **DESIGN.md first** — one paragraph: purpose, structure, design source, status.
2. **Bootstrap design system** — `npx getdesign@latest add <brand>` → produces full token reference (see `references/getdesign-bootstrap.md`).
3. **Create user page** — `gh repo create <user>/<user>.github.io --public` for the entry point.
4. **Create portfolio repo** — `gh repo create <user>/<portfolio-repo> --public --homepage https://<user>.github.io/<portfolio-repo>/`.
5. **Activate Pages** — `gh api -X POST /repos/<user>/<portfolio-repo>/pages -f source[branch]=main -f source[path]=/`.
6. **Build directory skeleton** — `decks/<deck-name>/` with single `index.html` + single `all-slides.md`.
7. **Write one `all-slides.md`** — title + production slides + links. `---` separators only.
8. **Inline CSS in `index.html`** — see CSS skeleton below. Use `disableLayout: true` for iOS Safari.
9. **Push & verify** — `git push`, then `curl -I <url>` for HTTP 200; `gh api /repos/.../pages/builds/latest` for build status.
10. **Cache-bust** — `?v=N` on CDN URLs + `<meta http-equiv="Cache-Control">` for instant updates.

## CSS Skeleton (Apple white-mode)

```html
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">

<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css?v=N">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/white.css?v=N">

<style>
:root {
  --primary: #0066cc;
  --primary-focus: #0071e3;
  --ink: #1d1d1f;
  --body: #1d1d1f;
  --body-muted: #6e6e73;
  --canvas: #ffffff;
  --canvas-parchment: #f5f5f7;
  --divider: #d2d2d7;
  --hairline: #e0e0e0;
}

html, body {
  background: var(--canvas);
  color: var(--body);
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  letter-spacing: -0.01em;
  overflow: hidden;
  touch-action: manipulation;
}

/* Reveal container — flat, no transform scale (iOS Safari safe) */
.reveal { width: 100%; height: 100%; position: relative; background: #fff; }
.reveal .slides { width: 100% !important; height: 100% !important; transform: none !important; inset: 0 !important; position: absolute; }
.reveal .slides > section {
  width: 100% !important; height: 100% !important;
  position: absolute !important; top: 0 !important; left: 0 !important;
  display: none !important; padding: 4vh 4vw; text-align: center; overflow: hidden;
  background: #ffffff;
}
.reveal .slides > section.present { display: block !important; }

.reveal h1 { font-family: -apple-system, "SF Pro Display", sans-serif; font-size: clamp(2rem, 5vw, 3.2rem); font-weight: 600; line-height: 1.07; letter-spacing: -0.035em; color: var(--ink); margin: 0 auto 0.5em; max-width: 16ch; }
.reveal h1 em { font-style: italic; color: var(--primary); }
.reveal h2 { font-size: clamp(1.4rem, 3.5vw, 2.2rem); font-weight: 600; line-height: 1.1; letter-spacing: -0.025em; color: var(--ink); margin: 0 auto 0.5em; }
.reveal h3 { font-size: clamp(1rem, 2.2vw, 1.3rem); font-weight: 600; color: var(--ink); margin: 0.5em auto 0.4em; text-align: left; }
.reveal p, .reveal li { font-size: clamp(0.85rem, 1.7vw, 1.05rem); line-height: 1.5; color: var(--body); text-align: left; max-width: 70ch; margin: 0 auto 0.7em; }
.reveal strong { font-weight: 600; color: var(--ink); }
.reveal em { font-style: italic; color: var(--primary); }
.reveal code { background: var(--canvas-parchment); color: var(--primary); padding: 0.1em 0.45em; border-radius: 6px; font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 0.88em; }
.reveal pre { background: var(--canvas-parchment); border: 1px solid var(--hairline); border-radius: 14px; padding: 1em 1.4em; font-size: 0.78rem; line-height: 1.55; margin: 0.5em auto 1em; width: 95%; max-width: 800px; }
.reveal blockquote { background: var(--canvas-parchment); border-left: 3px solid var(--primary); padding: 1em 1.4em; font-style: italic; border-radius: 0 14px 14px 0; margin: 1em auto; max-width: 65ch; text-align: left; }

.reveal table { font-size: clamp(0.7rem, 1.4vw, 0.85rem); border-collapse: separate; border-spacing: 0; margin: 1em auto; max-width: 800px; border: 1px solid var(--divider); border-radius: 14px; overflow: hidden; width: 100%; }
.reveal th { background: var(--canvas-parchment); color: var(--ink); padding: 0.7em 1em; text-align: left; font-weight: 600; border-bottom: 1px solid var(--divider); }
.reveal td { padding: 0.55em 1em; border-bottom: 1px solid var(--hairline); color: var(--body); }
.reveal tr:last-child td { border-bottom: none; }
.reveal tr:nth-child(even) { background: rgba(0,0,0,0.015); }

.reveal .small { display: block; font-size: 0.7em; color: var(--body-muted); font-weight: 300; text-align: center; margin: 0.8em auto 0; }
.reveal .card { background: var(--canvas-parchment); border: 1px solid var(--hairline); border-radius: 18px; padding: 1.4em 1.8em; margin: 1em auto; max-width: 780px; text-align: left; box-shadow: 0 4px 16px rgba(0,0,0,0.04); }

/* Flow chart — Apple cards, inline-block (iOS safe) */
.flow-chart { text-align: center !important; margin: 1em auto; max-width: 880px; font-size: 14px; }
.flow-row { text-align: center !important; line-height: 2.4; word-spacing: 0.4em; margin: 0.4em 0; }
.flow-group { display: block; background: var(--canvas-parchment); border: 1px solid var(--divider); border-radius: 18px; padding: 1em 1.4em; margin: 0.7em auto; max-width: 820px; }
.flow-group-label { display: block; font-size: 0.7em; letter-spacing: 0.2em; text-transform: uppercase; color: var(--body-muted); margin-bottom: 0.6em; text-align: center; }

.flow-node { display: inline-block !important; vertical-align: middle !important; padding: 0.6em 1.1em; border-radius: 12px; font-size: 0.85em; font-weight: 500; text-align: center !important; line-height: 1.35; margin: 0.3em 0.3em; max-width: 240px; background: #ffffff; border: 1px solid var(--divider); color: var(--ink); box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.flow-node .node-label { display: block !important; font-size: 1em; font-weight: 600; margin-bottom: 0.2em; }
.flow-node .node-sub { display: block !important; font-size: 0.78em; font-weight: 400; color: var(--body-muted); margin-top: 0.2em; }
.flow-node.long-term { border-color: var(--primary); background: rgba(0,102,204,0.04); } .flow-node.long-term .node-label { color: var(--primary); }
.flow-node.tooling { border-color: #ff9500; background: rgba(255,149,0,0.04); } .flow-node.tooling .node-label { color: #b86e00; }
.flow-node.compute { border-color: #5856d6; background: rgba(88,86,214,0.04); } .flow-node.compute .node-label { color: #5856d6; }
.flow-node.data    { border-color: #af52de; background: rgba(175,82,222,0.04); } .flow-node.data .node-label    { color: #af52de; }
.flow-node.output  { border-color: #34c759; background: rgba(52,199,89,0.04); }  .flow-node.output .node-label  { color: #2a7d3e; }
.flow-node.simple  { border-color: var(--divider); }

.flow-arrow { display: inline-block !important; vertical-align: middle !important; color: var(--primary); font-size: 1.1em; font-weight: 600; margin: 0 0.25em; line-height: 1; }
.flow-arrow::before { content: "↓"; }
.flow-arrow.right::before { content: "→"; }
.flow-arrow.left::before { content: "←"; }
.flow-arrow.up::before { content: "↑"; }

.reveal .progress { background: rgba(0,0,0,0.06); height: 3px; }
.reveal .progress span { background: var(--primary); }
.reveal .controls { color: var(--primary); opacity: 0.6; }

@media (max-width: 600px) {
  .reveal .slides > section { padding: 3vh 4vw; }
  .flow-node { font-size: 0.7em; padding: 0.45em 0.8em; max-width: 170px; }
  .reveal h1 { font-size: 1.7rem; }
  .reveal h2 { font-size: 1.2rem; }
}
@media (max-height: 500px) and (orientation: landscape) {
  .reveal .slides > section { padding: 2vh 4vw; }
  .flow-node { font-size: 0.65em; padding: 0.35em 0.7em; }
  .reveal h1 { font-size: 1.4rem; }
}
</style>

<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js?v=N"></script>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/markdown/markdown.js?v=N"></script>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/notes/notes.js?v=N"></script>
<script>
Reveal.initialize({
  hash: true, controls: true, progress: true,
  slideNumber: false,          // No "1/8" indicator (always off for portfolio decks)
  overview: true,
  center: false,
  disableLayout: true,         // iOS Safari: avoid transform:scale() breaking inline-block
  transition: 'slide', transitionSpeed: 'fast',
  plugins: [ RevealMarkdown, RevealNotes ],
  markdown: { smartypants: false, gfm: true }
});
</script>

<!-- Defensive CSS: hide slide-number indicators completely (print/export paths) -->
<style>
.reveal .slide-number,
.reveal .slide-number-pdf,
.reveal .slide-suffix { display: none !important; }
</style>
```

A single `<section data-markdown>` is the entire deck source:

```html
<div class="reveal">
  <div class="slides">
    <section data-markdown="slides/all-slides.md"
             data-separator="^---$"
             data-separator-vertical="^----$"
             data-separator-notes="^Note:">
    </section>
  </div>
</div>
```

## Pitfalls

- **`disableLayout: true` is required.** Without it, Reveal.js applies `transform: scale()` to fit slides, which breaks iOS Safari's flexbox/inline-block rendering. Symptoms: nodes overlap, text positioning off.
- **Single `<section data-markdown>` per deck, NOT multiple.** Multiple `<section data-markdown="slides/X.md">` cause Reveal.js to count each section as a slide AND each `---` inside MD as another — the slide count doubles. The user once reported "42 pages" with 7 slides of content. Fix: merge all MD into `all-slides.md` with one `<section>`.
- **`display: inline-block !important` on flow nodes, never `display: flex`.** Same iOS Safari + Reveal.js transform issue. Even with `disableLayout: true`, flex children render unpredictably.
- **GitHub Pages caching is real.** Push not appearing? Check: (a) `gh api /repos/.../pages/builds/latest` → status `built`; (b) CDN URL `?v=N` cache-buster; (c) `<meta http-equiv="Cache-Control" content="no-cache">`. Hard refresh / incognito on the user side.
- **Verifying a Pages CDN update via headers, not just body.** After `git push`, a `curl -I <url>` may still return the OLD page body even though `git ls-remote` shows the new commit. Inspect the response headers:
  - `last-modified: <old GMT>` → CDN still serving old build
  - `last-modified: <new GMT>` (matches commit time) → fresh build served
  - `cache-control: max-age=600` + `expires: <GMT>` → cache TTL window
  - `x-proxy-cache: MISS` → origin was hit, so the response is fresh
  - File size sanity-check: `curl -s <url> -o /tmp/x && wc -c /tmp/x` and compare to the new index.html bytes.
  - This pattern avoids the failure mode of declaring "deployed!" based on a cached body when the build is actually 5–10 min behind.
- **Pages build stuck — diagnose with five signals before declaring anything broken.** When `git push` lands but `last-modified: <old GMT>` and `age: N+` stay frozen on the CDN, the issue may NOT be your repo. Run this sequence:
  1. **Confirm git is fine**: `git ls-remote origin main` returns the new commit hash → repo side OK.
  2. **Inspect build state**: `gh api /repos/<owner>/<repo>/pages/builds/latest` → fields `status`, `duration`, `error.message`. If `status: building` with `duration: 0` for >2 minutes, build is hung. If `status: errored` with `message: "Page build failed."`, the build started and crashed (look for syntax errors in the HTML).
  3. **Check GitHub-wide incident**: `curl -s https://www.githubstatus.com/api/v2/summary.json` → `components[name=Pages].status`. `degraded_performance` or `partial_outage` + active incident title containing "Pages" = **the issue is GitHub-side, not yours**. Stop trying to fix the repo and tell the user "GitHub Pages incident — see status page". Verify on https://www.githubstatus.com.
  4. **Last-resort trigger (don't spam)**: `curl -s -X POST -H "Authorization: token $TOKEN" https://api.github.com/repos/<owner>/<repo>/pages/builds` → returns `{status: queued}`. Use ONLY after confirming step 1-3 show repo OK + Pages incident OR genuine local hang. Don't fire-and-forget — poll `pages/builds/latest` to see if the new build progresses; if it just stays `building` with `duration: 0`, GitHub Pages is genuinely stuck and another trigger won't help.
  5. **Reporting to the user**: lead with what you actually completed (commit SHA, file diff stats, `git ls-remote` hash) and what is blocked on infrastructure. Don't apologize for the platform. Cite https://www.githubstatus.com so the user can verify themselves.
  - See `references/github-pages-stuck-build-diagnosis.md` for the full reproduction recipe (commands + JSON shape + reporting template).
- **PAT workflow scope.** Personal Access Tokens without `workflow` scope can't push `.github/workflows/*.yml`. Workaround: rely on legacy Pages (no build needed for static HTML).
- **Card `onclick="Reveal.slide(n)"` is unreliable.** Cross-deck navigation, nested contexts, and timing make JS-driven slide jumps fragile. Use keyboard nav as primary.
- **`<section class="section-opener">` inside slide MD breaks layout.** Reveal.js treats nested `<section>` as a separate slide and renders it off-position. Use `<div class="section-opener">` instead.
- **User page 404 vs project page 404 are different.** `https://<user>.github.io/` and `https://<user>.github.io/<project>/` are different repos. If `<user>.github.io/` 404s, create the user page repo `<user>.github.io` with its own `index.html` and activate Pages with `gh api -X POST /repos/<user>/<user>.github.io/pages -f source[branch]=main -f source[path]=/`.
- **Apply the design system fully.** When the user says "Apple design", they mean the exact tokens from `getdesign add apple` — `#0066cc` primary, `#f5f5f7` card bg, SF Pro Display/Text, single accent. Partial application reads as "not Apple".
- **Three-tier cache after deploys.** Even with `?v=N` on CDN URLs, the browser still serves stale markdown/SVG because Reveal.js caches the markdown XHR fetch. **Required**: patch BOTH `window.fetch` AND `XMLHttpRequest.prototype.open` BEFORE `Reveal.initialize` to append `&cb={Date.now()}` to any URL matching `all-slides.md` or `.svg`. Without the XHR patch, hard refresh is the only recovery. See `wiki-to-slides/references/three-tier-cache-busting.md` for the working snippet.
- **SVG diagram bugs.** For hand-crafted SVG: (a) use absolute URLs in markdown `<img>` (path is relative to the `.md` file's directory, not the page); (b) verify viewBox math — a `translate()` x offset must leave `(box_width/2 + 20)px` in from each edge; (c) `feDropShadow stdDeviation=N` extends visible bounds by ~3N pixels in every direction — leave 2N gaps or use stdDeviation≤3. Run `wiki-to-slides/scripts/audit-svg-bounds.py` before committing any SVG.
- **Slide number indicators.** Set `slideNumber: false` (JS) AND add defensive CSS (`.reveal .slide-number { display: none !important }`). The JS alone misses print/PDF export paths.

## References

- `references/getdesign-bootstrap.md` — how to use `npx getdesign@latest add <brand>` to bootstrap a design system reference.
- `references/apple-design-tokens.md` — Apple white-mode token cheatsheet (colors, typography, cards, buttons) condensed from `getdesign add apple` output.
- `references/memory-pipeline-deck-cleanup.md` — worked example (2026-07-03) of stripping 채니봇 + Korean + closing slide from an existing deck, with before/after translation table and Pages-CDN-headers verification recipe.
- `references/github-pages-stuck-build-diagnosis.md` — full reproduction recipe for the Pages-stuck scenario (2026-07-03): the 5-step probe, GitHub Status JSON shape, rebuild API call, and the user-reporting template that ended the session productively.

<!--
NOTE: skill_manage does not chmod. After patch/write, ensure all files are 644:
  chmod 644 /home/ubuntu/.hermes/skills/deck-portfolio-site/SKILL.md
  chmod 644 /home/ubuntu/.hermes/skills/deck-portfolio-site/references/*.md
If 600, the /skill autoload registry silently ignores them.