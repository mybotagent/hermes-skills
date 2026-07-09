# Iron Laws Checklist — Gate-by-Gate Verification

Use this checklist before claiming any analysis is "done".

## Pre-execution (before Stage 3)

- [ ] **Iron Law #1**: `docs/plans/<goal>.md` exists with goal sentence + analysis_type + target + metric
- [ ] **Iron Law #2**: `scratch/env.md` exists with Local/Colab decision + rationale

## During execution (Stages 3-6)

- [ ] **Iron Law #3**: Every "done" claim backed by stdout (paste actual output)
- [ ] **Iron Law #4**: Every number cited in narrative appears in `scratch/analysis-cycle.md` stdout
- [ ] **Iron Law #5**: Loop state updated each iter (best_score, delta, convergence)

## Trust stages (Stages 7-9)

- [ ] **Iron Law #6**: Stages 7-9 performed NO `execute_code`, NO `Write(scripts/*.py)`, NO `Bash(python ...)`, NO model training
- [ ] **Iron Law #7**: All 4 trust files exist + decision=PUBLISH before Stage 6 verify-report

## Final checks (Stage 6)

- [ ] Re-execution Δ on key metrics within tolerance
- [ ] All 6 SVG charts render
- [ ] ipynb opens in Jupyter without errors
- [ ] md report includes all Iron Law compliance notes

## Sanity checklist (always)

- [ ] `random_state=42` everywhere it matters
- [ ] `n_jobs=-1` only with seed set
- [ ] No `datetime.now()` in modeling code
- [ ] No `os.urandom` calls
- [ ] requirements.txt pins sklearn/pandas/numpy versions

## Common failure modes

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Different forest on re-run | `n_jobs=-1` without seed | Add `random_state` before `n_jobs` |
| Different CV folds | `KFold` without `shuffle=True` | Use `StratifiedKFold(shuffle=True, random_state=42)` |
| Different metric on re-run | Parallel backend variance | Set `os.environ['OMP_NUM_THREADS']=1` |
| Notebook won't open | Malformed JSON cell | Validate with `json.load(open(path))` first |
| Chart missing | Wrong relative path | Use `docs/charts/` paths from project root |