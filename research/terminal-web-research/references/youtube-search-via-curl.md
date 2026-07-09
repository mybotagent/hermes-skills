# YouTube / Video Search via curl (No Browser)

Search YouTube and get video metadata using only terminal tools (curl, grep, Python).
Use when `browser_navigate` fails (Chrome not installed) or for quick, targeted lookups.

## Step 1: Search for Videos

```bash
# Basic search — returns /watch?v=... IDs
curl -s "https://www.youtube.com/results?search_query=Hermes+Agent+Claude" |
  grep -oP '/watch\?v=[^"&]+' | sort -u | head -10
```

### Korean Query Encoding
YouTube encodes non-ASCII characters naturally in the URL — just write them raw:

```bash
curl -s "https://www.youtube.com/results?search_query=Hermes+Agent+%EB%94%94%EC%8A%A4%EC%BD%94%EB%93%9C+%ED%98%91%EC%97%85" |
  grep -oP '/watch\?v=[^"&]+' | sort -u | head -10
```

The `%EB%94%94...` is URL-encoded Korean. You can also paste raw Korean chars like `search_query=디스코드+협업`.

## Step 2: Get Video Metadata (Title, Channel, Thumbnail)

YouTube's oEmbed API returns structured JSON without auth:

```bash
curl -s "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=VIDEO_ID&format=json"
```

**Key fields returned:**
- `title` — Video title
- `author_name` — Channel name
- `author_url` — Channel URL
- `thumbnail_url` — Thumbnail image URL (e.g., `https://i.ytimg.com/vi/VIDEO_ID/hqdefault.jpg`)

### Bulk Lookup Loop
```bash
for vid in "ID1" "ID2" "ID3"; do
  echo "=== $vid ==="
  curl -s "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=$vid&format=json" |
    python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('title','?'), '-', d.get('author_name','?'))"
done
```

## Pitfalls

1. **YouTube search results page has rate limits** — for very heavy usage, consider the official YouTube Data API v3.
2. **The oEmbed API returns only the FIRST result** — you need a separate call per video ID.
3. **Some videos may be region-restricted** — the oEmbed API may return empty for those.
4. **The `grep -oP` pattern assumes YouTube's HTML structure** — if YouTube changes its markup, the regex may need updating.
5. **Pipe to interpreter security warning** — `curl | python3` triggers Hermes' high-security scanner. Pre-write a Python script file or use intermediate files for repeated queries.

## When to Use This vs Browser

| Situation | Tool |
|-----------|------|
| Quick search + metadata lookup | curl + oEmbed (this technique) |
| Need to read video description | browser_navigate (renders JS) |
| Need to watch/interact with page | browser_navigate |
| Bulk search + filter | curl + Python script |
