# Three-Tier Cache Busting for Hosted Slide Decks

> **Symptom**: Fixed a missing-file / wrong-path bug, pushed, but the browser
> still shows the old broken image, even after `?v=N+1` URL bump.

## The three caches

When a markdown-based deck is hosted on GitHub Pages (or any HTTPS CDN),
**three independent cache layers** can each serve stale content:

| Tier | Cache | TTL | How to bust |
|---|---|---|---|
| **1. CDN edge** | GitHub Pages CDN (`cache-control: max-age=600`) | ~10 minutes | Wait, or hit a unique-URL edge |
| **2. Browser HTTP** | Browser caches `.md`, `.html`, `.svg` per URL | Hours to days | `?v=N` query string with bumped N |
| **3. Reveal.js XHR** | The markdown plugin's `XMLHttpRequest` is cached at the browser layer, separately from `<img>` cache | Hours to days | Patch `window.fetch` BEFORE `Reveal.initialize` |

The CDN edge usually clears itself in 10 minutes. The other two survive
page reloads and survive `?v=N` bumps on other resources — they only clear
when the **specific URL** changes.

## Working fix (verified, 2026-07-01 Hermes architecture deck)

### 1. Absolute URLs + `?v=N` on every CDN/asset reference

```html
<!-- index.html -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css?v=7">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/white.css?v=7">
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js?v=7"></script>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/markdown/markdown.js?v=7"></script>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/notes/notes.js?v=7"></script>
```

```html
<!-- slides/all-slides.md -->
<img src="https://{owner}.github.io/{repo}/decks/{name}/assets/img/x.svg?v=7" ...>
```

Bump `?v=N+1` on every push. Never re-use the same N.

### 2. Patch `window.fetch` BEFORE `Reveal.initialize`

Reveal.js's markdown plugin uses `XMLHttpRequest` (internally), but its
asset-loader uses `fetch`. Intercept **both** to add a per-load cache
buster for the markdown and any SVG:

```html
<script>
  // Patch fetch to bypass cache for markdown + SVG (cache-bust v=7)
  (function() {
    const origFetch = window.fetch;
    window.fetch = function(input, init) {
      let url = typeof input === 'string' ? input : (input && input.url) || '';
      if (url.includes('all-slides.md') || url.includes('.svg')) {
        const sep = url.includes('?') ? '&' : '?';
        const newUrl = url + sep + 'cb=' + Date.now();
        return origFetch(typeof input === 'string' ? newUrl : new Request(newUrl, input), init);
      }
      return origFetch.apply(this, arguments);
    };
  })();

  // Same patch for XMLHttpRequest (Reveal.js md plugin uses XHR, not fetch)
  (function() {
    const origOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, ...rest) {
      if (typeof url === 'string' && (url.includes('all-slides.md') || url.includes('.svg'))) {
        const sep = url.includes('?') ? '&' : '?';
        url = url + sep + 'cb=' + Date.now();
      }
      return origOpen.call(this, method, url, ...rest);
    };
  })();

  Reveal.initialize({ ... });
</script>
```

The XHR patch is critical — without it, Reveal.js will hit a cached
`all-slides.md` and your `?v=N` bumps are useless.

### 3. Verification after push

Don't trust the browser for 5–10 minutes after push (CDN lag):

```bash
# Wait, then verify the deployed files actually have the new content
sleep 60
curl -s "https://{owner}.github.io/{repo}/decks/{name}/slides/all-slides.md" \
  | grep -E "\.svg"
# Expect: ?v=7 query strings, absolute URLs

curl -s "https://{owner}.github.io/{repo}/decks/{name}/" \
  | grep -c "origFetch"
# Expect: 3 (the patch block appears 3 times across the script)
```

If those return the OLD pattern (`../../assets/img/...`, `?v=6`), the CDN
hasn't refreshed — wait another 60s and retry. **Do not trust the
browser as the verification tool.**

## Common mistakes

- Bumping `?v=N` on CDNs but **forgetting the markdown fetch** — the
  browser fetches the OLD markdown, sees the OLD src, fetches the OLD
  cached SVG. Net result: still broken.
- Bumping `?v=N` everywhere but **using relative paths** — if the
  browser cached a 404 response on the old relative path, the `?v=N`
  bump won't matter (the URL itself is different but the response is the
  same 404 from a fresh fetch). See
  `references/path-resolution-debugging.md`.
- Trusting `browser_navigate` for verification — it consistently
  60s-times-out on github.io / CDN pages. Use `curl -I` instead.

## Reference

- SKILL.md Pitfall #20 — the original entry
- `references/path-resolution-debugging.md` — the companion path-bug guide
