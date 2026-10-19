# 30-Minute Validate Checklist

> Use this when a design decision is converged and you need ≥1 validate before session ends.
> Goal: close the design-execution gap with minimal time investment.

## When to Use

- After git push (design commit)
- After meeting conclusion (4-files pushed)
- After cron job creation
- After Linear/Kanban task creation
- After any "합의 완료" moment

## 30-Minute Plan

### 0-5min: Read state
- [ ] `git ls-remote origin <branch>` — confirm push (private repo returns 404 on raw.githubusercontent.com — use ls-remote)
- [ ] Check Kanban/Linear task status
- [ ] Read prior error logs (agent.log, errors.log, gateway.log)

### 5-15min: Run smallest validate
Pick ONE — smallest unit that proves design works:
- [ ] **Script**: `python3 <script>.py` with simple input
- [ ] **Cron**: trigger manually with `--dry-run` or short timeout
- [ ] **API**: `curl -s ... | jq .` to verify response shape
- [ ] **Query**: `python3 query.py "test"` for search-related changes
- [ ] **File**: `cat` or `head` to verify content / frontmatter

### 15-25min: Capture result
- [ ] **Negative result** → record in meeting-note/wiki Pitfalls section (REQUIRED)
- [ ] **Positive result** → record as "validate 통과" with timestamp + commit hash
- [ ] **Partial result** → record both halves explicitly

### 25-30min: Confirm and report
- [ ] 1-paragraph summary: "Validate 결과: ... (commit hash: ...)"
- [ ] Update relevant task status (Kanban, Linear, meeting-note)
- [ ] If validate failed: add Phase N+1 to meeting-note's next_steps.md

## Negative Result Pattern (정직한 negative result)

```
## Validate 결과 (negative)

- Expected: <what should have happened>
- Actual: <what actually happened>
- Evidence: <commit hash, log line, output capture>
- Root cause: <hypothesis with reference to docs/source>
- Next step: <concrete follow-up: file/line or Phase N+1>
```

This pattern is REQUIRED when validate fails. It is the highest-value capture of the validate cycle.

## Worked Example (2026-07-02)

```bash
# 1. Read state
git ls-remote origin main  # commit b785d5b confirmed pushed

# 2. Run smallest validate (script smoke test)
python3 ~/.hermes/skills/research/wiki-knowledge-search/scripts/query.py "test"

# 3. Capture result — in this case NEGATIVE
# Expected: new page returned in search
# Actual: only existing 3 architecture/ pages in Neo4j
# Evidence: Neo4j direct query returned 3 pages only
# Root cause: hermes-wiki-super submodule HEAD stale (f07a8feb3c39 vs actual 83c79bf)
# Next step: cd ~/hermes-wiki-super/wiki/hermes-wiki && git reset --hard origin/main
```

After fix: re-ran incremental → 11.9s → query returned new page at rank #1 (similarity 0.856).

## Related

- `execution-discipline` umbrella skill
- 5-stage verify (why→what→whether→what→how→validate) — Memory entry
- `meeting-documentation` — Critical Rule 7 (Execution Gate)
- `wiki-knowledge-search` — Submodule HEAD stale pitfall