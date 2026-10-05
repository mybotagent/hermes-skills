# Contract-Extraction Template

Use this template BEFORE writing any code against a third-party multi-file
asset. Time budget: 5-10 minutes.

## Asset metadata

```
Asset name       : <repo / plugin / framework>
Source URL       : <git clone URL or local path>
Discovered via   : <user request, search, link in chat>
Date             : <YYYY-MM-DD>
Asset shape      : <single-file | multi-skill | framework | pipeline tool>
Symlink target   : <~/.hermes/skills/X or ~/.claude/skills/X — if registered>
```

## Step 1 — Contract documents

List every document you read:

| Path | Read full? | Key takeaway |
|------|-----------|--------------|
| `README.md` | yes/no | <1 line> |
| `CLAUDE.md` | yes/no | <1 line> |
| `skills/<entry-point>/SKILL.md` | yes/no | <1 line> |
| `docs/` | yes/no | <1 line> |
| `plugin.json` / manifest | yes/no | <1 line> |

**Gate**: did you read at least 3 documents (README + CLAUDE.md + entry-point
SKILL.md if a skill suite)? If no, stop and read more.

## Step 2 — Output schema

List every file this asset expects when work is done:

```
<path>             <purpose>
<path>             <purpose>
...
```

Compare to what the user is asking for. If the user's deliverable does not
match, surface that gap explicitly to the user.

## Step 3 — Philosophy (Iron Laws / invariants)

Copy verbatim from the asset's docs:

```
1. <Iron Law 1>
2. <Iron Law 2>
3. <Iron Law 3>
...
```

For each, plan how your work will comply:

| Iron Law | Compliance plan |
|----------|-----------------|
| 1 | <how I'll satisfy it> |
| 2 | <how I'll satisfy it> |

## Step 4 — Workflow

Map the directed graph of stages:

```
Stage 1: <name> → <output>
Stage 2: <name> → <output>  (requires Stage 1)
Stage 3: <name> → <output>  (requires Stage 2)
...
```

Identify:
- **Sequential gates**: which stages block the next
- **Read-only stages**: which stages cannot modify earlier artifacts
- **User gates**: which stages require explicit user approval
- **Skip-if-exists**: which stages can be skipped if their output already exists

## Step 5 — Plan against contract

Write the plan before executing:

> I am going to use `<asset>` to `<user goal>`.
>
> **Output paths required**:
> - <list>
>
> **Iron Laws I must satisfy**:
> - <list>
>
> **Stages I will run in this order**:
> 1. <stage>
> 2. <stage>
> 3. ...
>
> **Stages I will skip** (and why):
> - <stage>: <reason — e.g., "not relevant for descriptive analysis">
>
> **Quality bar for "done"**:
> - <e.g., "trust-metrics pass + qa-reviewer PUBLISH + head-of-data decision">
>
> **Time budget**: <estimated hours>

## Common pitfalls (re-checklist before executing)

- [ ] I read at least 3 documents, not just the README
- [ ] I extracted the output schema, not just the function names
- [ ] I noted every Iron Law and planned compliance
- [ ] I traced the workflow DAG and identified user gates
- [ ] I am NOT symlinking without reading (Pitfall 3)
- [ ] I am NOT planning to "fill in missing files later" (Pitfall 5)
- [ ] The user's literal request is compatible with the asset's contract
  (if not, I have flagged it)