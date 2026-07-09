# GitHub Pages caching and how to defeat it

GitHub Pages adds edge cache headers and you cannot directly override them via HTML meta tags — you can only *instruct browsers* via `<meta>`. The CDN URLs serve cached versions for ~5-10 minutes by default. This file lists the cache layers and how to handle each.

## Cache layers, in order

1. **Browser cache** — the user's local browser. Most persistent and sticky on iOS Safari.
2. **GitHub Pages edge cache** — intermediate, valid for `max-age=600` by default for `.html`/`.css`/`.js` URLs.
3. **GitHub Pages build cache** — newly-pushed commits must be built into a Pages artifact; ~30s typical.

## What works

### Inline your CSS

If your deck CSS lives in `<style>` inside `<head>` (no external `.css`), then GitHub Pages doesn't serve a stale `.css` file — the cache applies only to `index.html`, and your CSS ships fresh on every push.

This is the single biggest defense. Do this.

### Cache-bust CDN URLs

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css?v=2">
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js?v=2"></script>
```

Bump the `?v=N` suffix deliberately each push. The CDN treats `?v=2` and `?v=3` as different URLs — both will be cached, but the new one is fresh.

### Add cache-busting headers in your HTML

```html
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
```

This tells the *browser* not to cache. Doesn't directly affect edge cache but is cheap insurance.

### Self-host assets

If the deck references any non-CDN asset, put it in the repo (`assets/`) rather than fetching from a third party. GitHub Pages serves the same way for both, but you control version pinning.

## What doesn't work

- Trying to set `Cache-Control` headers from repo files — Pages controls them, you cannot override.
- Busting cache with `?v=N` on Pages-served `.html` — Pages edge ignores the query string for cache key (they treat `X.html` and `X.html?v=N` as the same).
- Pushing to a different branch — Pages only serves the configured branch.
- Pushing an empty commit to trigger a rebuild — Pages only rebuilds on content change to the configured branch; an empty commit triggers but cache is still involved.

## Verification cadence

After push:
1. Wait at least 60s before testing (Pages build + edge cache)
2. `curl -s -o /dev/null -w '%{http_code}'` to check it serves
3. **Always test in a private/incognito window** (Safari private mode, Chrome incognito). The user's main browser cache is sticky and not representative.
4. On iOS Safari, force-reload via Settings → Safari → Clear History & Website Data, then revisit. (The clearest cache there.)

## If the deck still shows old content after push

1. Check `gh api /repos/<owner>/<repo>/pages/builds/latest` — should show `"status": "built"` with the new commit SHA.
2. If `built` but old content visible: hard reload, then try a different browser entirely.
3. If GitHub Pages build is failing: check the build log via `gh api /repos/<owner>/<repo>/pages/builds/latest` for an `error` field; often a syntax error in index.html breaks the build silently.
