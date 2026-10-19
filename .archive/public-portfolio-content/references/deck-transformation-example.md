# Memory Pipeline Deck — Before/After Reference

## Concrete before/after from 2026-07-03 session

### Before (user complained: "채니봇 빼고, 한글 빼고, 불필요한 거 제거, 가독성 개선")

Slide count: 8
Korean sections: ~15 lines across multiple slides
Bot name: "채니봇 · a + a-2 · 5-stage verified" (2 occurrences)
Closing slide: "끝. Push & validate." + 3 redundant external links
Readability: 단편 ("전체", "왜 이 4-Layer인가", "실제 작동 결과")

### After (delivered)

Slide count: 7 (closing removed)
Korean sections: 0
Bot name: 0 occurrences
External links: only meaningful ones in assets table
Readability: full sentences, descriptive headers

## Section-by-section transformation examples

### Slide 1 — Title
- Before: `<p class="small">Built 2026-07-02 · mybotagent/Hermes Memory Pipeline v1.0</p>`
- After: same (this one was OK)

### Slide 2 — Architecture diagram header
- Before: `<h2>전체 <em>아키텍처</em> 흐름도</h2>` (Korean)
- After: `<h2>End-to-End <em>Architecture</em> Flow</h2>`

### Slide 3 — Why table
- Before:
  - Headers: "한계 / 해결 / Layer"
  - Rows: "Memory tool 2,200자 / GitHub 영속 무제한 / Layer 0 → 1"
- After:
  - Headers: "Limitation / Solution / Layer"
  - Rows: "Memory tool capped at 2,200 chars / GitHub wiki, unlimited persistence / Layer 0 → 1"

### Slide 4 — Validation results
- Before: `<h2>실제 <em>작동 결과</em> (a 4-step + a-2 검증)</h2>`
- After: `<h2>Validated <em>End-to-End</em></h2>`
- Also added: descriptive subtitle line about each check

### Slide 5 — 5-stage loop
- Before (Korean explanatory text):
  ```
  <em>why</em>: 진짜 필요한가? (가치 검증) → <em>what</em>: 무엇이 일어났나 (수치화) → ...
  ```
- After (English):
  ```
  <em>why</em> — Is this worth doing? (value check) → <em>what</em> — What actually happened? (quantify) → ...
  ```

### Slide 6 — Assets
- Before (Korean column header): "자산 / 용도 / 위치"
- After: "Asset / Purpose / Location"

### Slide 7 — Open workstreams (was last before)
- Before: "열린 의제" with Korean bullet items
- After: "Open Workstreams" with bold phase labels + English rationale

### REMOVED slide 8 — Closing
- Before:
  ```html
  <h1>끝. <em>Push & validate.</em></h1>
  <p>← Portfolio · hermes-wiki · meeting-notes</p>
  <p>2026-07-02 · 채니봇 · a + a-2 · 5-stage verified</p>
  ```
- After: DELETED entirely

## Verification commands used

```bash
# Local
grep -c "채니봇" decks/memory-pipeline/index.html   # → 0
grep -nP "[\x{AC00}-\x{D7A3}]" decks/memory-pipeline/index.html  # → empty
grep "<html lang" decks/memory-pipeline/index.html  # → en
grep -c "<section>" decks/memory-pipeline/index.html  # → 7
```

## What triggered the user correction (cascade of 3 messages)

1. "채니봇이라는 글자는 빼고 한글 들어간것은 영어로 수정하고 다른 페이지에서 불필요한 것들 제거해야함"
2. (asked for clarification on workflow) — "끝 이라는 페이지도 필요없고 불필요하게 링크 걸지 말아야함"
3. "변화 없음" (after push — turned out to be GitHub incident)

Lesson: combine ALL the corrections in one rewrite pass, not piecemeal. Users express preferences cumulatively.