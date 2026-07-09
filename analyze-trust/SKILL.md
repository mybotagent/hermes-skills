---
name: analyze-trust
description: |
  End-to-end data analysis pipeline with Trust evaluation. 6-stage analysis
  (define-analysis → kaggle-discover → local-setup → hypothesis-eda →
  analysis-cycle → verify-report) + 4-stage Trust pipeline (trust-metrics-llm ∥
  trust-metrics-code → qa-reviewer → head-of-data PUBLISH gate).
  Use this skill for any structured data analysis with reproducibility + Trust.
  Triggers: data analysis, kaggle, eda, hypothesis, classification, regression,
  모델링, 가설, 데이터 분석, 신뢰도 평가
  Private Hermes port of sh-ai-x/analyze-trust-suite (24 skills compressed to
  one orchestrator skill with sub-skill references).
---

# analyze-trust — End-to-End Data Analysis with Trust Evaluation

## When to use this skill

Use this skill when the user wants:
- Structured data analysis with reproducibility + Trust evaluation
- Kaggle / public dataset → cleaning → EDA → modeling → report pipeline
- Pre-registered hypothesis testing with semantic + computation trust gates
- A final PUBLISH decision gated by Iron Laws

Do NOT use this skill when:
- User wants quick EDA without Trust gates → use data-science skills directly
- User wants production ML deployment → use mlops/serving-llms-vllm instead
- User has no dataset → stop and ask for data source

## Inputs (ask if missing)

1. **Goal** — single sentence describing the analysis objective (e.g., "predict
   Titanic survival")
2. **Dataset source** — Kaggle dataset name / URL / local file path
3. **analysis_type** — regression / classification / clustering / descriptive
4. **target_variable** — column name (or "none" for clustering/descriptive)
5. **success_metric** — RMSE / MAE / AUC / F1 / silhouette / p-value / business KPI

## 6-Stage Pipeline (Analysis)

### Stage 1: define-analysis → `docs/plans/<goal>.md`

Run the Ralph Loop (Wonder → Reflect → Restate) to converge on goal. Then capture:
- Goal sentence (one line, specific + measurable)
- analysis_type, target_variable, success_metric
- Environment choice: **Local** (CPU, small data) vs **Colab** (GPU, large data)
- Constraints, out-of-scope

**Output**: `docs/plans/<goal>.md`
**Iron Law gate**: #1 (no execution without plan)

### Stage 2: kaggle-discover → `scratch/kaggle-discover.md`

Search Kaggle for matching datasets. Prefer:
- High signal density (cleaned, with target + features)
- Public mirror available (in case Kaggle MCP is unavailable)
- Compatible license (CC0, MIT, public domain)

Document 3-5 candidates with size + key columns; pick one with rationale.
**Output**: `scratch/kaggle-discover.md`

### Stage 3: local-setup → `data/raw/`

Download selected dataset to `data/raw/`. Verify shape + checksum. Document
sentinels (-1, Unknown, etc.) for downstream handling.
**Output**: data files in `data/raw/`

### Stage 4: hypothesis-eda → `scratch/hypothesis-eda.md`

Run 4-5 EDA passes:
1. Shape + missingness
2. Top feature coverage (for text: regex extraction)
3. Target distribution
4. Class imbalance (if classification)
5. Top categorical breakdowns

Generate 3-7 pre-registered hypotheses with expected direction.
**Output**: `scratch/hypothesis-eda.md`

### Stage 5: analysis-cycle → `scratch/analysis-cycle.md`

Iterate on models:
- Baseline (Ridge / LogReg / majority-class)
- Tree ensemble (RandomForest, GradientBoost)
- Best by CV-MAE / CV-Acc

For each iter record: model, metric, delta vs prev best.
Loop state per Iron Law #5: best_score, convergence, delta_last_iter.
Close every hypothesis from Stage 4 with verdict + evidence.
**Output**: `scratch/analysis-cycle.md` + `data/processed/*.csv`

### Stage 6: verify-report → `docs/reports/<date>-<goal>.{md,ipynb}`

Re-execute all `.py` scripts; compare output to recorded metrics within tolerance.
Emit final report:
- `docs/reports/<date>-<goal>.md` — narrative report
- `docs/reports/<date>-<goal>.ipynb` — executable notebook
- 4-6 SVG visualizations in `docs/charts/`

**Output**: 3 files (md + ipynb + charts/)

## 4-Stage Trust Pipeline (Evaluation)

### Stage 7: trust-metrics-llm ∥ trust-metrics-code

Run **in parallel** (Iron Law #6: both are read-only / re-execution only):

**trust-metrics-llm**: LLM Judge, 7-criterion rubric
1. Goal clarity
2. Methodological soundness
3. Evidence quality
4. Hypothesis-driven reasoning
5. Reproducibility (LLM eval)
6. Visual + narrative quality
7. Domain-actionability

Pass threshold: aggregate score ≥ 4.0/5.0

**trust-metrics-code**: Re-execute all `.py` with same seed; compare output.
Pass threshold: Δ MAE ≤ $0.50K, Δ R² ≤ 0.005, Δ Acc ≤ 0.005

**Outputs**: `scratch/trust-metrics-llm.md`, `scratch/trust-metrics-code.md`

### Stage 8: qa-reviewer → `scratch/qa-review.md`

Read-only synthesis. Combine LLM + Code trust verdicts. Issue PUBLISH / REVISE /
ABORT recommendation based on quality gates.
**Output**: `scratch/qa-review.md`

### Stage 9: head-of-data → `scratch/head-of-data-decision.md`

User decision gate. Iron Law #7 — PUBLISH only if all 4 files exist + decision=PUBLISH.
**Output**: `scratch/head-of-data-decision.md`

## Iron Laws (7)

1. **No execution without plan** — `docs/plans/<goal>.md` required
2. **No execution without env selection** — `scratch/env.md` required
3. **No "done" without evidence** — stdout required for every claim
4. **Conclusions from data only** — no speculative numbers
5. **No iter without loop_state update** — record delta + convergence
6. **QA + trust stages are read-only** — no execute_code, no Write(scripts/*.py),
   no Bash(python ...), no model training
7. **PUBLISH gate** — all 4 trust files + decision=PUBLISH

## Reference: directory layout

```
<project_root>/
├── docs/
│   ├── plans/<goal>.md                 # Stage 1
│   ├── reports/<date>-<goal>.md        # Stage 6
│   ├── reports/<date>-<goal>.ipynb     # Stage 6
│   └── charts/0{1..N}_*.svg            # Stage 6
├── scratch/
│   ├── env.md                          # Stage 1 (env choice)
│   ├── kaggle-discover.md              # Stage 2
│   ├── hypothesis-eda.md               # Stage 4
│   ├── analysis-cycle.md               # Stage 5
│   ├── trust-metrics-llm.md            # Stage 7
│   ├── trust-metrics-code.md           # Stage 7
│   ├── qa-review.md                    # Stage 8
│   ├── head-of-data-decision.md        # Stage 9
│   └── *.py                            # Executable scripts (read-only in stages 7-9)
└── data/
    ├── raw/<dataset>.csv                # Stage 3
    └── processed/<artifact>.csv         # Stage 5
```

## Reference: See also

- `references/pipeline-template.md` — copy-paste template for new analyses
- `references/iron-laws-checklist.md` — gate-by-gate verification
- `scripts/init-analysis.sh` — bootstrap a new analysis project