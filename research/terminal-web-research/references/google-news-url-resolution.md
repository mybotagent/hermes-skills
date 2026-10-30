# Google News RSS → Original Publisher URL (resolved attempts, Oct 2026)

Task class: user asks for news headlines **plus the original media URL** ("Google News 리다이렉트 URL 말고 원본 매체 URL이 있으면 그것, 없으면 Google News URL").

## What the RSS actually gives you (free, no decoding)

```xml
<item>
  <title>삼성전자 3분기 영업이익 107조 4천 원 - MBC 뉴스</title>
  <link>https://news.google.com/rss/articles/CBMidEFVX3lx... ?oc=5</link>
  <guid isPermaLink="false">CBMidEFVX3lx...</guid>
  <pubDate>Thu, 29 Oct 2026 00:57:20 GMT</pubDate>
  <description>&lt;ol&gt;&lt;li&gt;&lt;a href="https://news.google.com/rss/articles/..."&gt;headline&lt;/a&gt;
    &nbsp;&nbsp;&lt;font color="#6f6f6f"&gt;MBC 뉴스&lt;/font&gt;&lt;/li&gt;...&lt;/ol&gt;</description>
  <source url="https://imnews.imbc.com">MBC 뉴스</source>
</item>
```

Key facts:
- `<title>` = headline **+ " - 매체명"** suffix. Strip it with `re.sub(r"\s*-\s*[^-]+$", ...)` or read media name from `<source>`.
- `<source>` element has a **`url` attribute = the publisher's own domain** (`https://imnews.imbc.com`). This is the cheapest "원본 매체 URL" approximation — the publisher homepage, not the deep article link.
- `<description>` contains an `<ol>` of 1–3 **sibling headlines** from the same query, each with a `<font color="#6f6f6f">media name</font>`. Good for cross-checking and for grabbing extra related headlines.
- `<description>` contains **no article body** and **no original article URLs** — every `<a href>` is another Google News wrapper.

## The Google News ID is base64, but NOT a URL

```python
base64.urlsafe_b64decode(gid + '==')
# b'\x08\x13"tAU_yqLPHn8vJTMsxD-vom...' — two opaque tokens, no embedded URL
```
Modern IDs (`CBMi...`) are opaque. Old-style IDs (pre-2024, `AU_yqL...`) *did* embed the URL in protobuf bytes — try decoding those first, but new IDs need the RPC path below.

## Getting `data-n-a-ts` / `data-n-a-sg` (needed for the RPC)

```python
html = urllib.request.urlopen(
    urllib.request.Request(f"https://news.google.com/articles/{gid}",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"})
).read().decode()
ts = re.search(r'data-n-a-ts="([^"]+)"', html).group(1)
sg = re.search(r'data-n-a-sg="([^"]+)"', html).group(1)
```

**Locale-param gotcha:** `news.google.com/articles/{gid}` **without** `hl/gl/ceid` returns 200 with the attributes. **With** `?hl=ko&gl=KR&ceid=KR:ko` it 302-redirects to the same path (and then the params page 200s). `/read/{gid}` and `/rss/articles/{gid}` behave the same way. Either variant works, but the no-param form is the one that returned 200 on every attempt here.

## The batchexecute RPC (the standard decoder path)

Endpoint: `POST https://news.google.com/_/DotsSplashUi/data/batchexecute`
Body: `f.req=` + urlencoded `[[["Fbv4je", <inner json string>, null, "generic"]]]`

`inner` shape (this is the canonical one, matching the `googlenewsdecoder` PyPI package):
```python
CTX = ["X","X",["X","X"],None,None,1,1,"US:en",None,1,None,None,None,None,None,0,1]
inner = ["garturlreq", CTX, gid, int(ts), sig]
```
Success response contains `"garturlres","<original url>"`.

### What FAILED in Oct 2026 (don't repeat these)
- Swapping `CTX` for the newer `["en-US","US",["FINANCE_TOP_INDICES","WEB_TEST_1_0_0"],...]` form → response is `["wrb.fr","Fbv4je",null,null,null,[3],"generic"]` (null payload).
- Passing `sig` where an int was expected (`int(sg)`) → `ValueError`. **`sg` is NOT an int** — it is a base64-ish token string; only `ts` is numeric.
- Adding `?rpcids=Fbv4je`, `&source-path=...`, `X-Same-Domain: 1` headers, `hl=ko&gl=KR&ceid=KR:ko` variants → all returned the same null-payload envelope.
- Piping `ts`/`sg` as `["X","X",...,[ts, sg]]` inside CTX instead of as trailing positional args → null payload.
- `pip install googlenewsdecoder` (v0.2.2, needs `httpx` + `selectolax`) → its `gnewsdecoder()` returns `{'success': False, 'message': 'No decoded URL in batchexecute response.'}` — the same null payload. The package is not a workaround.
- `browser_navigate` on the same URL hung/timed out (Chromium not installed) → terminal-only path required.

**Diagnosis signal:** the response envelope `["wrb.fr","Fbv4je",null,...,["di",N],["af.httprm",...]]` with `null` in slot 2 means Google accepted the request shape but refused to resolve that ID — often because the `ts`/`sg` pair was fetched from a *different* page load than the one used for the RPC, or because the ID/signature are stale. **Re-fetch `ts`/`sg` immediately before the POST, in the same session (same cookie jar), and send them in one request.**

## Practical fallback ladder (what to actually ship)

1. Try `batchexecute` decode for **all** ids **in ONE batched POST** (collect ts/sg first, then one POST for the whole list). One round trip, not N.
2. If the RPC returns nulls (as it did here), fall back to `<source url="...">` — the publisher's own domain — as the "media URL", and keep the Google News wrapper as the article link.
3. If even that is unavailable, keep the Google News URL and note it.

## Budget rule (learned the hard way)

Resolving URLs is the **most expensive** part of a "headlines + URLs" task and it is optional. The user's own instruction was "원본 매체 URL이 있으면 그것, **없으면 Google News URL**" — Google News URL is an acceptable deliverable.

**Spend at most ~6 tool calls on URL resolution, then ship.** Collect and parse **all** headlines first (cheap: one RSS fetch per query, stdlib `xml.etree`), format the JSON, and only then attempt URL decoding as an enhancement. In this session, 20+ calls went into decoding and the run still ended with only one item emitted — the per-item delivery contract (10 entities × 2–3 items each) was never met.

Related: `references/korean-stock-news-rss-2026-09.md`, `references/korean-stock-news-batch-2026.md`.
