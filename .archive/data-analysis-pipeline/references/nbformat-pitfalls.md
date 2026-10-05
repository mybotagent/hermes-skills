# nbformat / nbconvert Pitfalls (concrete fixes)

Real errors hit while generating the Titanic verification ipynb, with the exact
fix that worked. Future agents doing the same should not have to rediscover these.

## Pitfall 1 — `'outputs' is a required property` on code cells

**Error:**
```
nbformat.validator.NotebookValidationError: 'outputs' is a required property
Failed validating 'required' in code_cell:
On instance['cells'][1]:
{'cell_type': 'code', 'execution_count': None, ...}
```

**Cause:** Code cells must have an `outputs` key (even if empty list). nbformat 5.x made this
required where earlier versions tolerated omission.

**Fix — programmatically:**
```python
import nbformat
nb = nbformat.read(path, as_version=4)
for cell in nb.cells:
    if cell.cell_type == "code" and "outputs" not in cell:
        cell.outputs = []
nbformat.write(nb, path)
```

**Fix — when constructing ipynb from scratch:**
Always include `"outputs": []` on every code cell, even ones without execution yet.

## Pitfall 2 — Stream output missing `name`

**Error:**
```
nbformat.validator.NotebookValidationError: 'name' is a required property
Failed validating 'required' in stream:
On instance['cells'][3]['outputs'][0]:
{'output_type': 'stream', 'text': '...'}
```

**Cause:** `stream` output type requires `"name": "stdout"` (or `"stderr"`).

**Fix:** Add the `name` field:
```python
{"output_type": "stream", "name": "stdout", "text": ["line 1\n", "line 2\n"]}
```

## Pitfall 3 — Cell missing `id` field

**Warning (hard error in future nbformat):**
```
MissingIDFieldWarning: Cell is missing an id field, this will become a hard error
in future nbformat versions. You may want to use `normalize()` on your notebooks
before validations
```

**Fix:**
```python
import uuid
for cell in nb.cells:
    if not cell.get("id"):
        cell["id"] = uuid.uuid4().hex[:8]
```

## Pitfall 4 — `nbconvert --execute` runs in wrong cwd

**Symptom:** Code cell fails with `FileNotFoundError: 'data/raw/titanic.csv'` even though
the file exists relative to your project root.

**Cause:** `jupyter nbconvert` sets cwd to `--output-dir` (or the input file's dir if
`--output-dir` not given). Relative paths inside cells are resolved against that.

**Fix options (prefer absolute paths):**
```python
# In your code cell source:
df = pd.read_csv("/home/user/project/data/raw/titanic.csv")

# Or use --output-dir to point at project root:
cd /home/user/project
jupyter nbconvert --to notebook --execute docs/reports/20260703-titanic.ipynb \
  --output 20260703-titanic.ipynb --output-dir docs/reports/
```

## Pitfall 5 — `pd.cut(...).astype(int)` fails on NaN labels

**Error:**
```
ValueError: Cannot convert float NaN to integer
```

**Cause:** `pd.cut` returns NaN for rows outside bin range or with NaN input. `astype(int)`
on NaN fails.

**Fix — use string labels + explicit fillna:**
```python
df["AgeBin"] = pd.cut(
    df["Age"], bins=[-1, 16, 32, 48, 64, 200],
    labels=["child", "young", "mid", "senior", "old"],
).astype("object").fillna("unknown")
```

This is the pattern `analyze-trust-suite/scripts/run.py::engineer()` uses.

## Pitfall 6 — Hermes venv hijacks `python3`

**Symptom:** `pip install scikit-learn` succeeds but `python3 -c "import sklearn"` fails.

**Cause:** The system `python3` symlink may point to a hermes-agent venv with restricted
packages. `pip` defaults to a different interpreter (system 3.12 on Ubuntu).

**Fix — use `uv venv` for project isolation:**
```bash
uv venv .venv
uv pip install --python .venv/bin/python scikit-learn numpy pandas matplotlib jupyter nbformat
.venv/bin/python scripts/run.py
```

NEVER modify `/home/ubuntu/.hermes/hermes-agent/venv/` — that breaks hermes itself.

## Pitfall 7 — nbconvert writes to wrong filename

**Symptom:** After `--execute`, the ipynb has outputs but the source file is unchanged.

**Cause:** `jupyter nbconvert --to notebook` defaults to writing the source file
in-place, but `--output` + `--output-dir` together control destination. If `--output`
matches source name and `--output-dir` differs, you get two files.

**Fix — explicit pattern:**
```bash
# Execute and overwrite source:
jupyter nbconvert --to notebook --execute --inplace docs/reports/20260703-titanic.ipynb

# Execute and write to specific path:
jupyter nbconvert --to notebook --execute \
  docs/reports/20260703-titanic.ipynb \
  --output 20260703-titanic.ipynb \
  --output-dir docs/reports/
```

## Verified-working snippet

```python
import nbformat
from pathlib import Path

# Build ipynb with all required fields
cells = [
    {"cell_type": "markdown", "metadata": {}, "id": "abc12345",
     "source": ["# Title\n"]},
    {"cell_type": "code", "metadata": {}, "id": "def67890",
     "source": ["print('hello')\n"], "execution_count": None, "outputs": []},
]

nb = {
    "cells": cells,
    "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3",
                                 "language": "python"}},
    "nbformat": 4, "nbformat_minor": 5,
}

Path("out.ipynb").write_text(json.dumps(nb), encoding="utf-8")
nb_loaded = nbformat.read("out.ipynb", as_version=4)
nbformat.validate(nb_loaded)  # passes
```