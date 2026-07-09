# Pipeline Template — Copy-Paste for New Analyses

## Stage 1: define-analysis template

```markdown
# Analysis Plan — <GOAL>

## Goal
<one-sentence specific + measurable goal>

## Ralph Loop
**Wonder** — What does "<user's word>" mean? 3 candidate readings.
**Reflect** — Compare each to user's intent.
**Restate (goal sentence)** — *<final converged sentence>*

## Framing Questions
1. <question 1>
2. <question 2>
3. <question 3>

## Prediction Target(s)
- <target 1>: <description>
- <target 2>: <description>

## Success Metric
- **Primary**: <metric + acceptance bar>
- **Comparative**: <baseline to beat>

## Environment
**Local** or **Colab** — <rationale>

## Data Source Note
<URL + shape + license + sentinel handling>

## Constraints
- <constraint 1>
- <constraint 2>

## Out of Scope
- <exclusion 1>
- <exclusion 2>
```

## Stage 2: kaggle-discover template

```markdown
# Kaggle Discover

## Round 1 — Search
Kaggle MCP unavailable → manual search of public mirrors.

| # | Source | Rows | Cols | Has Target? | License |
|---|--------|------|------|-------------|---------|

## Selection: Candidate #N
**Rationale**: <3 bullets>

## Files used
- `data/raw/<primary>.csv`
- `data/raw/<secondary>.csv` (optional)

## Provenance
<original Kaggle URL + mirror URL + license>
```

## Stage 4: hypothesis-eda template

```markdown
# Hypothesis EDA

## Pass 1 — Shape & missingness
```
RAW shape: (R, C)
CLEAN shape: (R, C)
```

| Field | Missing / Sentinel |
|-------|---------------------|

## Pass 2 — Top features
<top-N list with coverage %>

## Pass 3 — Target distribution
<summary stats or class counts>

## Pass 4 — Class imbalance (if classification)
<class counts + class_weight strategy>

## Hypotheses
| # | Hypothesis | Direction | Status |
|---|-----------|-----------|--------|
| H1 | <hypothesis> | +/- | ⏳ |
| H2 | <hypothesis> | +/- | ⏳ |

## Pass-5 plan
<bulleted next steps>
```

## Stage 5: analysis-cycle template

```markdown
# Analysis Cycle

## Cycle Configuration
- random_state: 42
- CV: 5-fold (StratifiedKFold for classification)
- split: 80/20

## Iteration log

### iter 1 — <Baseline>
```
<Model>: <metrics>
```
**Takeaway**: <one line>

### iter 2 — <Improvement>
```
<Model>: <metrics>
delta vs prev: <Δ>
```
**Takeaway**: <one line>

## Hypothesis verdicts
| # | Verdict | Evidence |
|---|---------|----------|

## Selected best models
| Task | Model | Metric |
|------|-------|--------|
| Regression | <name> | <value> |
| Classification | <name> | <value> |

## Loop state
```
best_score_reg = {<model>, <metric>}
best_score_clf = {<model>, <metric>}
convergence = True/False
delta_last_iter = <value>
```
```

## Stage 7: trust-metrics-llm template (7-criterion)

```markdown
# Trust Metrics — LLM Judge

## Inputs reviewed
- <list of plan + scratch + report files>

## 7-criterion LLM Judge
1. Goal clarity (0.20): N/5
2. Methodological soundness (0.20): N/5
3. Evidence quality (0.15): N/5
4. Hypothesis-driven reasoning (0.15): N/5
5. Reproducibility (LLM) (0.15): N/5
6. Visual + narrative (0.10): N/5
7. Domain-actionability (0.05): N/5

## Aggregate
<weighted sum> / 5.00

## Verdict
PASS / FAIL — Semantic Trust = <score>
```

## Stage 7: trust-metrics-code template

```markdown
# Trust Metrics — Code Re-execution

## Re-execution
| Metric | Recorded | Re-run | Δ | Within tol? |
|--------|----------|--------|---|-------------|

## Verdict
PASS / FAIL — Computation Trust
```

## Stage 8: qa-review template

```markdown
# QA Review

## Combined verdict
| Dimension | Source | Result |
|-----------|--------|--------|

## Quality gates for PUBLISH
| Gate | Required | Actual | Pass? |
|------|----------|--------|-------|
| <gate 1> | ✅ | ✅ | ✅ |

**Recommendation**: PUBLISH / REVISE / ABORT
```

## Stage 9: head-of-data-decision template

```markdown
# Head-of-Data Decision

## Decision: PUBLISH / REVISE / ABORT

## Rationale
<5 bullets>

## Iron Laws
1-7: ✅ / ❌

## What gets published
<file tree>

## Recommended follow-ups
- <follow-up 1>
```

## Stage 6: verify-report template

```markdown
# Verify Report

## Re-execution
| Stage | Recorded | Re-run | Δ | Pass? |
|-------|----------|--------|---|-------|

## Verdict
PASS — bit-identical reproduction
```