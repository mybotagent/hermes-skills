# Programmatic ipynb Construction

When to use: building a `.ipynb` from pre-computed artifacts in a sandboxed environment
(no Jupyter kernel, no execute_code, hermes cron/scheduled jobs, fresh CI runners).

## Why this exists

The standard flow is "analyze in notebook → save notebook → publish notebook." But many
analysis pipelines run as scripts (`analyze.py`, `make_charts.py`) and produce artifacts
(CSVs, JSONs, SVGs, PNGs). The user wants the **shape of a notebook** (markdown + code cells,
in order) in the destination vault, but the actual computation happened elsewhere.

## Minimal valid ipynb (nbformat 4.5)

```python
import json
import datetime as dt

cells = []

def add_md(text):
    cells.append({
        'cell_type': 'markdown',
        'metadata': {},
        'source': [text],  # OR text.split('\n') if multi-line
    })

def add_code(text, exec_count=1):
    cells.append({
        'cell_type': 'code',
        'metadata': {},
        'execution_count': exec_count,
        'outputs': [],
        'source': [l + '\n' for l in text.split('\n')],
    })

# ── Build cells ──
add_md('# Title\n**Goal**: ...\n**Best Model**: ...')
add_code('import warnings\nwarnings.filterwarnings("ignore")\nimport pandas as pd')
add_md('## EDA\nKey finding: ...')
add_code("df = pd.read_csv('data/raw/x.csv')\nprint(df.shape)")

# ── Save ──
nb = {
    'cells': cells,
    'metadata': {
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python', 'version': '3.11'},
    },
    'nbformat': 4,
    'nbformat_minor': 5,
}
with open('docs/reports/20260704-foo.ipynb', 'w') as f:
    json.dump(nb, f, indent=2)
```

## Source-list format

`source` MUST be a list of strings, each ending with `\n`. The `.split('\n') + '\n'` idiom is the
most reliable:

```python
'source': [l + '\n' for l in text.split('\n')]
```

A single-line string also works:

```python
'source': [text + '\n']
```

A raw string without trailing newline is fragile — some validators reject it.

## Populating outputs (optional)

If the goal is an **executed** notebook for the vault, populate `outputs`:

```python
cells.append({
    'cell_type': 'code',
    'metadata': {},
    'execution_count': 1,
    'outputs': [{
        'name': 'stdout',
        'output_type': 'stream',
        'text': ['DATASET SHAPE: (891, 12)\n'],
    }],
    'source': [l + '\n' for l in source],
})
```

Common `output_type` shapes:
- `stream` (stdout/stderr) — `{'name': 'stdout', 'output_type': 'stream', 'text': [...]}`
- `execute_result` — `{'data': {'text/plain': ['...']}, 'execution_count': 1, 'output_type': 'execute_result'}`
- `display_data` — `{'data': {'image/png': 'base64...'}, 'output_type': 'display_data'}`

For text-only reports, empty `outputs: []` is fine — `nbconvert --execute` will fill them in
if the user later runs the notebook.

## Matching existing report style

When the destination repo already has ipynb reports (e.g. `data-analysis-results`), read one
first to match format:

```python
import json
with open('docs/reports/20260703-titanic-survival.ipynb') as f:
    template = json.load(f)
print("Cell types:", set(c['cell_type'] for c in template['cells']))
print("nbformat:", template.get('nbformat'), template.get('nbformat_minor'))
```

This session's reports use:
- `nbformat: 4, nbformat_minor: 5`
- `kernelspec: {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}`
- Cell `id` field absent (older nbformat didn't require it)
- Empty `outputs: []` + populated `execution_count`
- Date in title cell uses ISO format

## Pitfalls

1. **`outputs` field cannot be null** — must be `[]` (empty list), not absent, not `None`.
2. **`source` must be a list, not a string** — older versions allowed strings; nbformat 4.5+ requires lists.
3. **`id` field is optional in nbformat 4.5, required in 5.0+** — match the destination repo's nbformat_minor.
4. **Don't escape backslashes in source** — `pd.read_csv('data\\raw\\x.csv')` literal in source is
   fine; do NOT pre-escape.
5. **Long single-line strings** — if a markdown cell has 50+ lines, break it into a list with one
   line per element for cleaner diff/git-blame.
6. **Cell ordering matters** — markdown headers should precede the code cells they describe, like
   a real notebook.

## Reference implementation

This session built `scratch/build_notebook.py` for the DS-job-market analysis: 29 cells
(15 markdown, 14 code), built from pre-computed artifacts in `/tmp/ds_jobs/scratch/analyze.py`.
Pattern: run the full pipeline as a script → build notebook → publish single ipynb to vault.