# GitHub Pages Caching & Cache Busting

> Critical patterns for serving slide decks on github.io. Default CDN
> cache is `max-age=600` (10 min), BUT browsers also cache aggressively
> — both layers must be addressed.

## The Cache Layers

1. **GitHub Pages CDN (Fastly)** — `max-age=600` for HTML, longer for static assets
2. **Browser cache** — caches ALL fetched resources including 404s (!)
3. **Reveal.js XHR cache** — when fetching markdown via `data-markdown`, the browser uses default fetch cache

## The Trap (cost a full debugging session)

When a NEW asset (e.g. SVG) is referenced in markdown but the file doesn't exist yet:
1. Browser fetches markdown → resolves `src=".../foo.svg"` → gets 404
2. Browser caches the 404 response
3. After the asset is added and pushed, browser STILL shows broken image (cached 404)
4. `Ctrl+R` doesn't fix it; only hard refresh (Cmd+Shift+R) or query string change does

**Symptom**: User reports broken image despite `curl` showing the SVG returns HTTP 200.
**Diagnosis**: Browser cache. Fix by bumping `?v=N` on the SVG src.

## Solution: ?v=N on ALL Asset URLs

For every URL pointing to an asset or CDN, append (or bump) `?v=N`:

```html
<!-- Reveal.js CDN links -->
<link rel="stylesheet" href="...?v=N">
<script src="...?v=N"></script>

<!-- SVG / image references in markdown -->
<img src="../../assets/img/foo.svg?v=N">
```

Each push bumps N (v=1, v=2, v=3...). Browser sees a NEW URL → MUST re-fetch.
Hard refresh becomes OPTIONAL, not required.

### When to Bump

Bump whenever:
- You change the file the URL points to
- You fix a broken reference (browser may have cached a 404)
- You change Reveal.js / theme CSS

Don't bump every turn — only when there's an actual change.

## Verification Commands

```bash
# Test asset accessibility directly
curl -sI "https://{org}.github.io/{repo}/path/to/asset.svg"
# Look for: HTTP 200, Content-Type: image/svg+xml

# Check cache state
curl -sI "URL" | grep -iE "cache|age|last-mod"

# Force fresh fetch with a unique cache buster
curl -s "URL?v=$RANDOM"

# Check 404 vs 200 for all SVGs in a deck
for f in compound-loop three-loops wiki-architecture; do
  curl -s -o /dev/null -w "$f: %{http_code} %{size_download}B\n" \
    "https://{org}.github.io/{repo}/.../$f.svg"
done
```

## SVG-Specific Pitfalls

### Pitfall #1: SVGs Not in git

Files created with `write_file` are NOT automatically committed.
A failed `git add` or untracked status silently leaves the file local-only.
The deck looks fine locally, `git push` succeeds, GitHub Pages serves 404.

**Always verify after every commit:**

```bash
git ls-files path/to/img/
# If empty → file is in working tree but not tracked
git add path/to/img/*.svg
git commit --amend --no-edit
```

### Pitfall #2: SVG Renders at Intrinsic Size

SVG with `<svg width="1100" height="680" viewBox="...">` displays at
1100×680 pixels BY DEFAULT if no CSS overrides apply. Overflows mobile.

**Fix**: Always include the CSS img fit pattern (see apple-slides-design.md):
```css
.reveal .slides > section img {
  max-width: 100% !important;
  max-height: calc(100vh - 16vh) !important;
  width: auto !important;
  height: auto !important;
  object-fit: contain;
}
```

ALSO add explicit attributes to SVG for renderers without CSS support:
```xml
<svg viewBox="0 0 1100 680" preserveAspectRatio="xMidYMid meet"
     width="1100" height="680">
```

### Pitfall #3: Bloated Alt Text Breaks Layout

When SVG fails to load, browser shows large alt text. Long alt attributes
wrap into massive paragraphs that push the rest of the slide around.

Keep alt text SHORT (5-10 words):

```html
<!-- BAD -->
<img src="..." alt="LLM Wiki + GitHub submodule architecture: Karpathy
gist → INDEX.md → 5 layers (schema, raw, research, operational, logs) →
4 submodules...">

<!-- GOOD -->
<img src="..." alt="Wiki + submodule architecture">
```

## Migrated Off Mermaid: Why

We moved OFF mermaid for slide flowcharts because:
- Repeated CDN rendering errors (especially on iOS Safari)
- Limited control over colors and typography
- ForeignObject rendering inconsistencies

**Use SVG with `<marker>` elements for arrows** instead of Unicode:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 460">
  <defs>
    <filter id="cardShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="4"
                    flood-color="#000" flood-opacity="0.07"/>
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="8" markerHeight="8" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="#0066cc"/>
    </marker>
  </defs>
  <style>
    .box { fill: #ffffff; stroke: #d2d2d7; stroke-width: 1.2; }
    .title { font-size: 16px; font-weight: 600; fill: #1d1d1f;
             font-family: -apple-system, sans-serif; }
  </style>

  <rect x="100" y="100" width="200" height="60" rx="12" class="box"
        filter="url(#cardShadow)"/>
  <text x="200" y="135" text-anchor="middle" class="title">Node label</text>

  <path d="M 300 130 L 400 130" stroke="#0066cc" stroke-width="2"
        marker-end="url(#arrow)"/>
</svg>
```

This pattern renders identically across all renderers including
GitHub's SVG preview, browser img tags, and Reveal.js img elements.
