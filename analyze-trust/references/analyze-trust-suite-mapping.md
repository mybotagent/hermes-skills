# analyze-trust-suite → analyze-trust mapping

When this skill was ported from `sh-ai-x/analyze-trust-suite` (24 skills)
to a single Hermes skill, the following mapping was applied. Reference
this when the user expects behavior from the original suite.

## 24 → 1 compression table

| Original skill | Mapped to | How |
|---|---|---|
| `define-analysis` | Stage 1 section in SKILL.md | Ralph Loop instructions embedded in body |
| `kaggle-discover` | Stage 2 section | Workflow steps preserved |
| `colab-setup` | Stage 3 section | "Colab" branch in env choice |
| `local-setup` | Stage 3 section | "Local" branch in env choice |
| `hypothesis-eda` | Stage 4 section | 4-5 EDA pass instructions |
| `analysis-cycle` | Stage 5 section | Iter log + loop state per Iron Law #5 |
| `verify-report` | Stage 6 section | Re-execution + emit md/ipynb/charts |
| `trust-metrics-llm` | Stage 7 (LLM branch) | 7-criterion rubric preserved verbatim |
| `trust-metrics-code` | Stage 7 (Code branch) | Tolerance policy preserved |
| `qa-reviewer` | Stage 8 section | Read-only synthesis instructions |
| `head-of-data` | Stage 9 section | PUBLISH gate logic preserved |
| `analyze` | (consolidated) | All-in-one entry — covered by loading this skill |
| `analyze-trust` | (consolidated) | Meta-orchestrator — covered by SKILL.md body |
| `wonder` | Stage 1 step | Embedded as "Step 1 — Wonder" in define-analysis |
| `reflect` | Stage 1 step | Embedded as "Step 2 — Reflect" |
| `restate` | Stage 1 step | Embedded as "Step 3 — Restate" |
| `ralph` | Stage 1 group | All 3 wonder/reflect/restate steps together |
| `verification-before-completion` | Cross-cutting | Embedded in every stage's "Output" line |
| `review/` (5 sub-skills) | Optional Stage 7.5 | Skill provides SKILL.md pointers, agent runs as needed |
| `migrate-to-dashboard` | Optional | Not ported — separate concern |

## What was NOT ported

- **Plugin metadata** (`plugin.json`, `marketplace.json`) — not needed in
  Hermes native format
- **Cross-repo dependency resolution** — original suite referenced 3 repos;
  the consolidation was already done in the source
- **MCP integrations** (`mcp__kaggle-mcp__search_kaggle_datasets`,
  `mcp__colab-mcp__execute_code`) — replaced with "use Python directly" in
  the workflow instructions

## What was preserved exactly

- 7 Iron Laws (verbatim from `CLAUDE.md`)
- 6-stage pipeline ordering
- 4-stage trust pipeline ordering (parallel stage 7)
- Output schema (`docs/plans/`, `scratch/`, `docs/reports/`, `docs/charts/`,
  `data/raw/`, `data/processed/`)
- 7-criterion LLM Judge rubric with weights
- Tolerance policy for code trust metrics
- Loop state format (best_score, convergence, delta_last_iter)

## When to fall back to the original suite

If the user explicitly asks for "the analyze-trust-suite" (verbatim), or
expects MCP integrations or cross-repo coordination, this single skill
is insufficient — recommend using the original suite or symlinking
`~/.hermes/skills/analyze-trust-suite/` from a fresh clone.