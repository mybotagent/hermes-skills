---
name: data-analysis-pipeline
description: |
  End-to-end data analysis workflow: define-analysis → data discovery → setup → hypothesis-EDA →
  modeling loop → verify-report → trust evaluation → vault publishing.
  Covers Kaggle/Colab/local environments, 5-iter modeling with convergence tracking, semantic+computation
  trust panels (LLM Judge + code re-execution), and strict vault minimalism (1 ipynb per analysis, all
  explanation inside the ipynb — no .md/.html/.scratch/.plans/.INDEX.md in destination repo).
  Triggers: data analysis, kaggle, classification, regression, EDA, hypothesis, modeling loop, trust
  evaluation, vault publishing, ipynb generation.
category: data-science
---

# Data Analysis Pipeline — End-to-End Workflow

## When to use

Use this skill when:
- Running a complete data analysis: EDA → model → verification → publish
- Working with a Kaggle/Colab/local dataset for classification or regression
- Evaluating trust/quality of analysis output (LLM Judge + code re-execution)
- Publishing results to a vault/destination repo where one artifact per analysis is required

## Core principle — Vault minimalism (user preference, hard rule)

**The destination vault repo contains exactly ONE ipynb per analysis.** No `.md`, `.html`, `.scratch/`, `.plans/`, `.INDEX.md`, `.scripts/`. Every explanation, code, output, and conclusion lives inside the ipynb's cells.

This is a deliberate user preference. The user explicitly rejected the "markdown soup" anti-pattern
where each analysis generates 5–10 auxiliary files (executed notebook + HTML render + summary md +
plan + 4–7 scratch audit files + INDEX.md + scripts). Strip them — only the executed ipynb publishes.

**Implication for analysis tools/plugins**: when configuring an analysis framework (e.g. `analyze-trust-suite`),
modify the publish step to copy ONLY `*.ipynb`. Remove HTML conversion, remove standalone `.md` summary,
remove vault-side `INDEX.md` regeneration. The ipynb IS the report.

### "But the upstream plugin expects scratch/ files alongside!" — RESIST

The `analyze-trust-suite` pipeline produces intermediate artifacts (`docs/plans/*.md`,
`scratch/{env,kaggle-discover,hypothesis-eda,analysis-cycle,trust-metrics-*,
qa-review,head-of-data-decision}.md`, `docs/charts/*.svg`). These belong to the
**workspace** where analysis runs, NOT to the vault. If you just `cp -r` the whole
`docs/` and `scratch/` tree to the vault because "the pipeline produced them",
you have violated vault-minimalism.

**Correct behavior**:
- Workspace = full pipeline artifacts (plans + scratch + ipynb + svg + processed data)
- Vault = ONLY `docs/reports/<date>-<goal>.ipynb`

The scratch/ files are the *audit trail* of the analysis process — they go in a
process log or wiki, not in the destination repo. The user has separate plumbing
for process archival (`wiki-knowledge-ingest` skill).

## 6-stage pipeline (general shape)

| # | Stage | Output (in workspace) |
|---|---|---|
| 1 | define-analysis | plan (goal, type, success_metric) + env selection |
| 2 | data discovery | data ref (Kaggle URL or local path) |
| 3 | setup | data loaded + integrity check |
| 4 | hypothesis-eda | top hypotheses ranked by signal |
| 5 | analysis-cycle | 5-iter modeling loop with delta tracking |
| 6 | verify-report | executed ipynb (the only artifact) |

Run stages sequentially. Gate at user decision points: plan approval, env selection, hypothesis approval, PUBLISH decision.

Convergence rule: stop when `delta < epsilon` or `delta` becomes marginal. Don't iterate forever.

## 4-stage trust evaluation (after modeling)

Two independent dimensions, **strictly separated**:

| Dimension | Method | What it produces |
|---|---|---|
| Semantic Trust (LLM) | LLM Judge on claims | grounded_LLM%, hallucination risk, insight consistency |
| Computation Trust (code) | Re-execution (3 seeds × 5-fold CV) | Grounded.Numeric%, CV stability, data trust, code verdict |

**Iron Law #6 — Trust evaluators are READ-ONLY**: they cannot execute code, write scripts, run bash,
or train models. They judge existing outputs only. Conflating the two dimensions defeats the
purpose (LLM Judge is the check; code re-execution is the independent check).

**Iron Law #7 — PUBLISH gate**: verify-report requires all four trust files + `decision=PUBLISH` in
`head-of-data-decision.md`. Missing any file → blocked from publishing.

## Publishing to vault

Copy only the executed ipynb. No md/html/scratch/plans/INDEX.

```bash
# Default vault location (override via DATA_ANALYSIS_RESULTS_DIR env var)
DATA_ANALYSIS_RESULTS_DIR=/path/to/vault python scripts/vault-publish.py <goal_slug>
```

For the `analyze-trust-suite` plugin specifically, use:
```bash
DATA_ANALYSIS_RESULTS_DIR=/path/to/vault python scripts/verify_report_step_5_5.py <goal_slug>
```

The script silently skips when vault is absent. No INDEX.md regeneration (deleted by user preference).

## Modeling loop convention

For classification/regression, baseline → rule → linear → tree → boosted:

| iter | typical model |
|---|---|
| 0 | majority-class / mean baseline |
| 1 | single-feature rule (e.g. sex-only for Titanic) |
| 2 | LogReg / linear with basic features |
| 3 | RandomForest with basic features |
| 4 | HistGradientBoosting / XGBoost with engineered features |

Always report `mean ± std` across 5-fold CV (StratifiedKFold for classification, fixed seed=42).
Print `delta vs best` per iteration. Single best score = the only number that matters for go/no-go.

## Common pitfalls

1. **nbformat 5.x validation** — code cells require `outputs: []` (even if empty) and an `id` field.
   Stream outputs require `name: "stdout"`. Without these, `nbconvert --execute` fails with
   `NotebookValidationError`. See `references/nbformat-pitfalls.md` for the exact fix.
2. **nbconvert cwd** — `jupyter nbconvert --execute` runs in `--output-dir` as cwd. Data paths
   inside cells (`pd.read_csv('data/raw/x.csv')`) must be absolute or relative to that cwd.
3. **Python venv isolation** — system `python3` may be a hermes venv with limited packages.
   Use `uv venv .venv` for project work; install with `uv pip install --python .venv/bin/python ...`.
4. **Hardcoded macOS paths** — analysis plugins often hardcode `/Users/<name>/dev/...`.
   Always check + override via env var (`DATA_ANALYSIS_RESULTS_DIR`, `VAULT_DIR`, etc.).
5. **Trust evaluator overreach** — never let trust skills execute code or train models. This
   violates Iron Law #6 and conflates Semantic Trust with Computation Trust.
6. **INDEX.md regeneration** — when vault-minimalism is the rule, do NOT regenerate INDEX.md
   on publish. If the upstream analysis framework regenerates it, remove that call.
7. **Concat duplicate columns silently break downstream** — when merging a feature matrix via
   `pd.concat([clean, skills_with_prefix], axis=1)` where both frames share column names
   (`spark`, `aws`, `excel`, `python`, `r_lang`, `sql` are common between Glassdoor cleaned
   datasets and extracted-skill flags), `add_prefix('sk_')` on the second frame does NOT prevent
   duplicates — pandas keeps the collision and downstream `.sum()`/`.unique()`/groupby behave
   silently wrong. **Fix**: drop overlapping names from the second frame before prefixing:
   ```python
   overlap = {'python', 'r_lang', 'sql', 'spark', 'aws', 'excel'}
   skills_trim = skills[[c for c in skills.columns if c not in overlap]].add_prefix('sk_')
   ```
   Always print `df.shape` and `len(set(df.columns))` after concat to detect.
8. **RandomState in formatted strings** — `np.random.RandomState(f"{str}{int}")` raises
   `TypeError: can only concatenate str (not "int") to str`. Use plain `np.random.seed(i)` +
   `np.random.rand()` instead.
9. **Host terminal output masking** — some sandboxes mask certain pandas column names to `***`
   in stdout (security redaction). Don't trust the displayed key. Read raw CSV with `cat` or
   iterate `df.columns` via Python to get the actual string before writing it into reports.
10. **"Helpful-looking" cp -r to the vault** — when the upstream plugin's `scratch/` tree
    *looks* like a coherent package (plan.md + env.md + 4 trust files + ipynb), the
    obvious move is `cp -r docs scratch` to the vault. **DO NOT**. The vault rule is
    exactly one ipynb per analysis. If you catch yourself thinking "but these scratch
    files are part of the deliverable", re-read "Core principle — Vault minimalism".
    The audit trail belongs in `wiki-knowledge-ingest` or a separate process-log
    destination, not in the vault. (See `references/vault-minimalism-violation-2026-07-04.md`.)
11. **Reverse-filling scratch/ to match an external plugin's expected layout** — when a user
    points out "you skipped the pipeline structure", do NOT generate stub scratch/
    files to *retroactively* match the plugin's convention if those files would then
    be pushed to the vault. Either (a) restructure publish so scratch stays in workspace,
    or (b) load this skill BEFORE starting and follow it from the beginning. Retro-fitting
    fake pipeline state and pushing it to the vault compounds the original violation.

## Reference implementations

- **`analyze-trust-suite`** plugin — primary implementation. 24 skills, single repo. Combines the
  legacy `analyze-orchestrator` + `harness-data-analysis` + `data-team-trust`. Install via:
  `git clone git@github.com:sh-ai-x/analyze-trust-suite.git ~/.claude/skills/analyze-trust-suite`

## Support files

- `references/analyze-trust-suite-titanic-2026-07-03.md` — complete session walkthrough
  (Titanic dataset, 5-iter loop, CV acc 0.8316, full trust eval, vault publish)
- `references/vault-minimalism-violation-2026-07-04.md` — post-mortem of a session where
  the agent pushed plans/scratch/charts to the vault, what went wrong, and the
  remediation sequence (delete the extra files, keep only the ipynb, amend commit)
- `references/nbformat-pitfalls.md` — ipynb generation gotchas with concrete fixes
- `references/svg-charts-pure-python.md` — hand-rolled SVG charts (6 chart types, Apple palette,
  no matplotlib dependency, inline-renderable in markdown/GitHub)
- `references/programmatic-ipynb-construction.md` — building `.ipynb` via JSON when live kernels
  aren't available (data-prep, hermes-cron, sandboxed environments)
- `scripts/vault-publish.py` — standalone ipynb-only vault publisher
- `scripts/build_report_notebook.py` — template for building executed-style ipynb from
  pre-computed artifacts + markdown source