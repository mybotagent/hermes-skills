---
name: repo-intent-reading
description: |
  Before "using" a third-party repo / plugin / skill / framework, READ its intent.
  Multi-file assets (analysis plugins, multi-skill suites, framework repos) carry a
  contract beyond just their functions: an output schema, a philosophy (Iron Laws
  / design principles / invariants), and an intended workflow. Surface that contract
  BEFORE writing code, or you will produce work that is technically correct but
  structurally wrong for the asset's purpose.

  Use this skill when:
  - The user asks to "use X" or "leveraged with X" where X is a non-trivial
    third-party asset (multi-skill repo, framework, plugin suite, multi-stage
    pipeline tool)
  - You are about to invoke `git clone` on a structured repo (>= 5 files, with
    CLAUDE.md / README / SKILL.md / docs/)
  - The asset has explicit pipeline stages, gates, or output paths

  Triggers: 활용해서, 사용해서, by means of, via, with <repo>, workflow 따라,
  pipeline 따라, 산출물 형식, output schema, Iron Laws, design principles
---

# repo-intent-reading — Read the Asset's Contract Before Using It

## Why this skill exists

The single most expensive mistake when working with a structured third-party
asset is **collapsing "use it" → "call its functions"**. Most multi-file
assets (analysis plugins, multi-skill suites, framework repos, multi-stage
pipeline tools) have a **contract** that goes beyond their functions:

- **Output schema**: specific files in specific paths (e.g., `docs/plans/`,
  `scratch/`, `data/raw/`)
- **Philosophy**: design principles, Iron Laws, invariants, gates
- **Intended workflow**: stages, sequencing, dependencies
- **Quality bar**: what counts as "done"

Missing any of these produces work that is **technically correct but
structurally wrong**. The asset's author designed it expecting a specific
shape of output; you delivered something else. They will (rightly) say
"this isn't what I asked for."

## When to apply

Apply this skill BEFORE the first `Bash`, `Write`, or `Edit` against a
non-trivial third-party asset. Specifically:

| Asset shape | Apply? |
|---|---|
| Single-file library (e.g., `numpy`, `lodash`) | ❌ No — just import |
| Repo with CLAUDE.md / README + 1 main entry | ⚠️ Maybe — quick scan |
| Repo with multiple skills / stages / docs / output paths | ✅ Yes |
| Plugin / suite with Iron Laws or invariants | ✅ Yes |
| Multi-stage pipeline tool (analyze-trust-suite, etc.) | ✅ Yes |

## 5-step procedure

### Step 1 — Identify the asset's contract documents

Look for these files in the cloned/symlinked asset:

- `CLAUDE.md` (Claude Code conventions) — most authoritative
- `README.md` — overview, intended use
- `SKILL.md` (per-skill conventions) — if a skill suite
- `docs/` directory — long-form docs, plans, reports
- `plugin.json` / `manifest.json` — schema metadata
- Anything named `IRON-LAWS`, `PRINCIPLES`, `PHILOSOPHY`, `CONTRACT`

**Time budget**: spend 2-3 minutes here before writing any code.

### Step 2 — Extract the output schema

Build a tree of **what files this asset expects to exist** when work is done.

For example, from `analyze-trust-suite/CLAUDE.md`:

```
docs/plans/<goal>.md        # Stage 1
scratch/env.md              # Stage 1 (env choice)
scratch/kaggle-discover.md  # Stage 2
scratch/hypothesis-eda.md   # Stage 4
scratch/analysis-cycle.md   # Stage 5
scratch/trust-metrics-*.md  # Stage 7
scratch/qa-review.md        # Stage 8
scratch/head-of-data-decision.md  # Stage 9
docs/reports/<date>-<goal>.{md,ipynb}  # Stage 6
```

**Action**: list every required output path. The user's request is incomplete
if your final deliverable does not match this schema.

### Step 3 — Extract the philosophy (Iron Laws / invariants)

Most well-designed assets encode their design as **Iron Laws** or invariants:

> "No code execution without plan approval"
> "No 'done' claim without evidence"
> "Conclusions from data only"

These are NOT nice-to-haves. They are gates that the asset's author will
check. Violating them is like submitting a paper without an abstract — the
rest of the work is fine but it doesn't pass review.

**Action**: copy the Iron Laws into your working notes. Before claiming done,
walk each one and confirm compliance.

### Step 4 — Trace the intended workflow

Most multi-stage assets have a **sequencing** constraint. Trying to skip a
stage or do them in parallel breaks the contract:

- Stage N may require artifacts from Stage N-1
- Some stages are read-only (Iron Law: "QA stages are read-only")
- Some stages are user-gated (need explicit approval to proceed)

**Action**: identify the directed graph of stages. Plan execution order.

### Step 5 — Verify your plan against the contract

Before executing, write a short plan:

> "I am going to use <asset> to <user goal>. The asset requires:
> - Output paths: <list>
> - Iron Laws: <list with planned compliance>
> - Stages: <sequence with which I'll do what>
> - Quality bar: <what 'done' means here>"

If you cannot fill these out, **stop and ask the user**, not start coding.

## Pitfalls

### Pitfall 1 — "I'll just skim the README"
Reading only `head -50` of `README.md` is the most common failure mode. The
README is the overview; the contract is usually in `CLAUDE.md`, the SKILL.md
bodies, or a `docs/` subdirectory. **Read at least 3 documents**: README +
CLAUDE.md + the entry-point SKILL.md (if a skill suite).

### Pitfall 2 — "Functions are the contract"
You see `def train(...)`, `def predict(...)`, and think "got it." The actual
contract is what `train()` is expected to write to disk, what JSON schema it
must produce, what gates it must pass. Functions are 30% of the contract;
files + Iron Laws + workflow are the other 70%.

### Pitfall 3 — "Symlinking = using"
Symlinking the asset into `~/.claude/skills/` or `~/.hermes/skills/` is a
**registration** step, not a usage step. The agent must still follow the
contract. Symlinking without reading is just a fancier way to skip the
contract.

### Pitfall 4 — "The user wanted X, not the contract"
If the user's literal request ("analyze this dataset") seems to conflict with
the asset's contract ("you must produce docs/plans/X.md first"), **the
contract wins**. The user said "use X", which implicitly accepts X's contract.
If the conflict is real, ask the user — don't silently ignore the contract.

### Pitfall 5 — "I'll fill in missing files later"
The asset's schema is **all-or-nothing for verification**. Producing the
report but skipping the `scratch/qa-review.md` means the report cannot pass
the trust gate. Better to flag the gap upfront than discover it at submission.

## Anti-pattern: the "execute_code and hope" workflow

```
1. Read 1 paragraph of README
2. Symlink the asset
3. Write code that uses asset's functions
4. Produce output
5. Claim done
```

This is the failure mode that produces technically-correct but
structurally-wrong work. The fix is to **front-load the contract-reading**
(Steps 1-4 above) so that Step 5 actually produces a deliverable matching
the asset's schema.

## Reference: See also

- `references/contract-extraction-template.md` — **copy-paste template**:
  fill in 5 sections before any code; surface gaps to the user explicitly
- `references/example-analyze-trust-suite.md` — **worked example**: real
  session transcript where this skill would have prevented a 9-stage
  pipeline miss; shows the failure mode and the fix