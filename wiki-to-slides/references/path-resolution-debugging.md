# Path Resolution Debugging for Markdown Slide Decks

> **Symptom**: SVG/image is broken in the browser, BUT `curl` to the same URL
> shows 200 OK and the file exists. The markdown source `grep` shows what
> looks like a correct path.

## Why this happens

The browser resolves relative URLs in markdown content **relative to the
markdown file's URL**, not relative to the page URL. When the deck loads
`slides/all-slides.md`, any `<img src="...">` inside it is resolved from
that markdown file's location.

### Concrete failure case (Hermes architecture deck, 2026-07-01)

```
Page URL:        .../decks/hermes-architecture/
Markdown URL:    .../decks/hermes-architecture/slides/all-slides.md
SVG actual:      .../decks/hermes-architecture/assets/img/wiki-architecture.svg
```

If the markdown contains `<img src="../../assets/img/wiki-architecture.svg">`,
the browser resolves it as:

```
.../decks/hermes-architecture/slides/  +
../../  →  .../decks/  +
assets/img/wiki-architecture.svg
= .../decks/assets/img/wiki-architecture.svg   ← 404, one level too high
```

The correct relative path is `../assets/img/wiki-architecture.svg` (one
`..` up, from `slides/` to `hermes-architecture/`, then into `assets/`).

## Diagnosis recipe (curl-based)

Always verify each `<img src>` in the deployed markdown by curl-resolving
it the way the browser would:

```bash
# Find every img src in the deployed markdown
curl -s "https://{owner}.github.io/{repo}/decks/{name}/slides/all-slides.md" \
  | grep -oE 'src="[^"]+"' | sort -u

# For each src, resolve it against the markdown's base URL and curl
# (use the same `..` rules the browser uses)
curl -sI "https://{owner}.github.io/{repo}/decks/{name}/slides/../assets/img/file.svg"
# Expect: HTTP 200
# If you see HTTP 404 → relative path is wrong, fix it
```

A faster method: **just use absolute URLs everywhere**. They bypass the
relative-path resolution entirely:

```html
<img src="https://{owner}.github.io/{repo}/decks/{name}/assets/img/file.svg?v=N">
```

This is the recommended pattern for PUBLIC deck pushes — it eliminates an
entire class of "works locally, breaks in deploy" bugs.

## When relative paths are still useful

Internal/private decks where the repo might be hosted at multiple base
paths (e.g. user page `mybotagent.github.io/hermes-architecture-deck/`
vs org page `mybotagent.github.io/`). In those cases, keep relative but
verify with the curl-resolve test above before every push.

## Reference

- SKILL.md Pitfall #19 — the original entry that diagnosed this case
- `references/three-tier-cache-busting.md` — companion cache invalidation pattern
