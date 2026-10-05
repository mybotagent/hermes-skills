# Worked Example: Extracting Contract from `sh-ai-x/analyze-trust-suite`

This is a real session transcript showing how `repo-intent-reading` would have
prevented a failure mode that occurred in practice.

## The user's request

> "https://github.com/sh-ai-x/analyze-trust-suite 그리고
> https://github.com/sh-ai-x/data-analysis-results 를 활용해서 취업에
> 도움이 될만한 데이터 분석 리포트를 결과 레포에 올려주고 이 쓰레드에
> 분석 내용을 보고해"

## What went wrong without the skill

The agent:
1. Cloned both repos to `/tmp/`
2. Did `head -100 CLAUDE.md` and `head -100 README.md` of the suite
3. Skipped `SKILL.md` files in `skills/*/`
4. Skimmed `docs/plans/titanic-survival.md` and one existing ipynb
5. Wrote Python scripts in `/tmp/ds_jobs/scratch/*.py` directly
6. Produced a notebook + charts + .md report — all "looks right"
7. Pushed to data-analysis-results via local git commit

The user came back:

> "analyze-trust스킬을 써서 data-analysis-resul에 결과를 저장하는 건데
> 이해를 못했어?"

The agent had produced technically-correct work but missed the entire
**9-stage pipeline schema** the suite requires:
- `docs/plans/<goal>.md` (define-analysis artifact)
- `scratch/env.md`, `scratch/kaggle-discover.md`,
  `scratch/hypothesis-eda.md`, `scratch/analysis-cycle.md`
- `scratch/trust-metrics-{llm,code}.md`
- `scratch/qa-review.md`, `scratch/head-of-data-decision.md`

Plus 7 **Iron Laws** the suite enforces (no execution without plan, no
"done" without evidence, etc.).

## What the skill would have done differently

### Step 1 — Identify contract documents

After `git clone`, the agent should have read **all of**:

- `README.md` (full — overview of 6 stages + 4 trust stages + 7 Iron Laws)
- `CLAUDE.md` (full — pipeline tables, Iron Law text, meta-orchestrator)
- `skills/define-analysis/SKILL.md` (entry-point skill semantics)
- `skills/head-of-data/SKILL.md` (PUBLISH gate semantics)
- One existing `docs/plans/*.md` (real shape of plan file)
- One existing `docs/reports/*.md` (real shape of report file)

**Time budget**: 5-7 minutes.

### Step 2 — Extract the output schema

From `CLAUDE.md`:

```
Stage 1: define-analysis  → docs/plans/<goal>.md + scratch/env.md
Stage 2: kaggle-discover  → scratch/kaggle-discover.md
Stage 3: colab/local-setup → data/raw/
Stage 4: hypothesis-eda   → scratch/hypothesis-eda.md
Stage 5: analysis-cycle   → scratch/analysis-cycle.md
Stage 6: verify-report    → docs/reports/<date>-<goal>.{md,ipynb,html}
Stage 7: trust-metrics-{llm,code} → scratch/trust-metrics-{llm,code}.md
Stage 8: qa-reviewer      → scratch/qa-review.md
Stage 9: head-of-data     → scratch/head-of-data-decision.md
```

**Action**: the agent should have produced a 9-file deliverable, not a 3-file
one (notebook + .md + charts).

### Step 3 — Extract the philosophy (Iron Laws)

From `README.md` and `CLAUDE.md`:

1. No code execution without plan approval
2. No execution without env selection
3. No "done" claim without evidence (stdout required)
4. Conclusions from data only (no speculative numbers)
5. No iteration without loop_state update
6. QA Reviewer and trust-metrics-llm are read-only
7. PUBLISH gate — verify-report requires all 4 files + decision=PUBLISH

**Action**: the agent's first-pass deliverable violated at least #1 (no
plan file), #3 (no stdout evidence for "done"), and #7 (no PUBLISH gate).

### Step 4 — Trace the intended workflow

The 6+3 stages form a DAG with strict ordering:

```
define-analysis → kaggle-discover → (colab|local)-setup → hypothesis-eda
              → analysis-cycle → verify-report → trust-metrics
              → qa-reviewer → head-of-data [PUBLISH gate]
```

Stages 7-9 are **read-only** (Iron Law #6) — they evaluate Stages 1-6, they
do not modify them.

**Action**: the agent's "I'll just write code, then write a report" skipped
4 stages entirely (hypothesis-eda, analysis-cycle, qa-reviewer, head-of-data).

### Step 5 — Verify plan against contract

A correct plan would have been:

> "I am going to use analyze-trust-suite to produce a job-market analysis
> for the user. The suite requires:
>
> - **Output paths**: 9 files (1 plan + 8 scratch + reports + charts)
> - **Iron Laws**: all 7 must be satisfied before PUBLISH
> - **Stages**: run all 9 in order, stages 7-9 read-only
> - **Quality bar**: trust-metrics pass + qa-reviewer PUBLISH + head-of-data
>   decision=PUBLISH
>
> I will produce the deliverable in `/tmp/ds_jobs/`, then push the
> `docs/reports/<date>-<goal>.{md,ipynb}` to data-analysis-results."

## The fix that was applied (late)

After the user's correction, the agent backfilled all 9 scratch files to
match the suite's schema. The local commit `93756a2` was then valid against
the contract. But the better outcome would have been to do this from the
start.

## Lessons encoded in the parent skill

- **Step 1 budget**: 5-7 minutes of reading is acceptable; saves hours of
  rework.
- **Multi-skill suites are 1 contract, not 24 contracts**: 24 individual
  skills in `skills/*/` are one workflow; reading 1 well is better than
  reading 24 superficially.
- **Symlink ≠ use**: the agent cloned to `/tmp/ats` and never symlinked
  into `~/.claude/skills/` or `~/.hermes/skills/`. Without that symlink,
  the agent cannot invoke the skill — it can only read its source.

## When the parent skill would NOT apply

- The user gives you a single-purpose library (e.g., `requests`, `pandas`):
  no contract beyond functions.
- The user explicitly says "don't worry about their conventions, just do
  X": contract is overridden.
- The repo is your own (you wrote it): you already know the contract.