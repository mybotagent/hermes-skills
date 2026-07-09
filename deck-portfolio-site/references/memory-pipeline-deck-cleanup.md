---
title: Memory Pipeline Deck — Cleanup Walkthrough
created: 2026-07-03
tags: [deck, github-pages, content-cleanup, translation, case-study]
---

# Memory Pipeline Deck Cleanup — Worked Example

> **Source deck**: `~/hermes-architecture-deck/decks/memory-pipeline/index.html`
> **Commit**: `ff48536` (pushed to `mybotagent/hermes-architecture-deck`, 2026-07-02)
> **Live URL**: https://mybotagent.github.io/hermes-architecture-deck/decks/memory-pipeline/

This is the canonical reference for the user's 2026-07-03 content-discipline corrections applied to an existing deck. Use it as the worked example when other decks need the same cleanup.

## User Corrections (verbatim, in order)

1. "githubio에서 메모리 관리라는 곳에서 채니봇이라는 말은 빼주고 한글 빼주고 불필요한 내용은 빼줄래?"
2. "끝 이라는 페이지도 필요없고 불필요하게 링크 걸지 말아야함"
3. "그리고 가독성이 안좋은 text 개선이 필요함"

Combined rule: **Strip personal nicknames + Korean + closing/transition slides + redundant external links + improve readability to full English sentences.**

## Before/After Snapshot

| Aspect | Before (commit `9464eb9`) | After (commit `ff48536`) |
|---|---|---|
| Slides | 8 | 7 |
| `html lang` | `ko` | `en` |
| 채니봇 occurrences | 2 | 0 |
| Korean fragments | ~20+ across headings, table cells, footnotes | 0 |
| Final slide | "끝. Push & validate." with 3 footer links | Removed; replaced with substantive "Open Workstreams" slide |
| Table cells | Short keywords (e.g. "memory 한계 90% 알림 (자동 압축 X)") | Full English sentences ("90% memory-cap alert (no auto-compression)") |
| Internal jargon | "단일공식 검증 후", "M3 활용도 criterion" | Removed / replaced |
| File size | 9,793 bytes | 10,086 bytes (+293 — readability gained bytes, content preserved) |

## Key Translation Patterns

| Korean | English |
|---|---|
| 전체 아키텍처 흐름도 | End-to-End Architecture Flow |
| 왜 이 4-Layer인가 | Why These 4 Layers |
| 한계 / 해결 / Layer | Limitation / Solution / Layer |
| 실제 작동 결과 (a 4-step + a-2 검증) | Validated End-to-End |
| 5-Stage 검증 루프 | The 5-Stage Verification Loop |
| Operational 자산 | Operational Assets |
| 열린 의제 | Open Workstreams |
| Memory tool 2,200자 | Memory tool capped at 2,200 chars |
| 검색 불가 | Keyword search only |
| wiki → Neo4j 자동 sync | Wiki → Neo4j auto-sync |
| 디자인-실행 갭 20% 남음 | Design-execution gap ~ 20% · closing via the 5-stage loop |

## Readability Fixes (verbatim edits)

| Before | After | Why |
|---|---|---|
| `<th>한계</th>` | `<th>Limitation</th>` | Bare noun → meaningful English word |
| `<td>검색 불가</td>` | `<td>Keyword search only</td>` | 2-word stub → full phrase |
| `<td>전체 로드 비용</td>` | `<td>Full wiki load is expensive</td>` | Same |
| `<td>반복 토큰 비용</td>` | `<td>Repeated token cost</td>` | Same |
| `매일 21:00 KST` (footnote) | `Daily at 21:00 KST` | Code-mixed → English prefix |
| `<td>memory 한계 90% 알림 (자동 압축 X)</td>` | `<td>90% memory-cap alert (no auto-compression)</td>` | Compressed → fluent sentence |
| `<td>Cron 등록</td>` | `<td>Cron registration</td>` | Verb-noun → noun phrase |
| `단일공식 검증 후 안전화 시` | `gated on single-formula safety review` | Internal jargon → English phrase |
| `디자인-실행 갭 20% 남음 · M3 활용도 criterion 실측 진행 중` | `Design-execution gap ~ 20% · closing via the 5-stage loop` | Internal shorthand → English explanation |

## Removed Closing Slide (verbatim source → deleted)

```html
<section>
  <h1>끝. <em>Push & validate.</em></h1>
  <p style="text-align:center"><a href="../../index.html">← Portfolio</a> · <a href="https://github.com/mybotagent/hermes-wiki">hermes-wiki</a> · <a href="https://github.com/mybotagent/meeting-notes">meeting-notes</a></p>
  <p class="small">2026-07-02 · 채니봇 · a + a-2 · 5-stage verified</p>
</section>
```

**Why deleted**: filler, no substantive content, 3 redundant footer links, and contained both 채니봇 AND Korean text (끝).

## Validation Checklist Used

```bash
# 1. Strip personal nickname
grep -c "채니봇" decks/memory-pipeline/index.html  # → 0

# 2. Strip Korean (regex: Hangul syllables)
grep -nP "[\x{AC00}-\x{D7A3}]" decks/memory-pipeline/index.html  # → empty

# 3. Confirm html lang
grep "html lang" decks/memory-pipeline/index.html  # → <html lang="en">

# 4. Count slides
grep -c "<section>" decks/memory-pipeline/index.html  # → 7 (was 8)

# 5. Confirm closing-slide Korean is gone
grep -c "끝" decks/memory-pipeline/index.html  # → 0
```

## Deployment Verification (Pages CDN headers)

After `git push`, the CDN may still serve the OLD build for 5–10 min. Use this verification recipe before declaring success:

```bash
# 1. GitHub API — confirms commit landed
curl -s "https://api.github.com/repos/<owner>/<repo>/commits?path=decks/<deck>/index.html&per_page=1" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['sha'][:10])"

# 2. CDN freshness — check headers, not body
curl -sI "https://<owner>.github.io/<repo>/decks/<deck>/index.html" \
  | grep -E "last-modified|cache-control|x-proxy-cache"

# Expected:
#   last-modified: Thu, 02 Jul 2026 16:49:52 GMT  (matches commit time)
#   cache-control: max-age=600
#   x-proxy-cache: MISS

# 3. Body byte-size sanity check
curl -s "https://<owner>.github.io/<repo>/decks/<deck>/index.html" | wc -c
# → should equal local file size after cache TTL expires
```

## Pitfall Captured

**Don't trust the body alone.** A `curl <url>` may show OLD content while `git ls-remote` shows NEW commit. Always check `last-modified` header + file size diff against local index.html. The fix is patience + cache TTL expiry (max-age=600), not a re-deploy.

## Reuse Pattern

When cleaning up ANY existing deck the same way:

1. Identify which `<section>` is the closing filler (last + contains "끝/끝./Thank you/Q&A/Contact" + has 2+ footer links). Delete it.
2. Search for personal nicknames (operator-specific: 채니봇, aiprofit bot names) and internal jargon ("단일공식", "M3 활용도", "5-stage verified") — drop or generalize.
3. Translate every Korean fragment. Use the patterns table above as the starter vocab; match verbosity (Korean fragment length ≈ English fragment length, ±20%).
4. Set `html lang="en"`. Confirm with `grep "html lang"`.
5. Improve `<td>` cells: if any cell is ≤ 4 words / contains code-mixed tokens, rewrite as a phrase.
6. Run the validation checklist. Commit + push + verify via headers.