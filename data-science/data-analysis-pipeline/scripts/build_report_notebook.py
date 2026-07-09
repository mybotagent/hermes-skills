"""Build an ipynb from pre-computed artifacts.

Usage:
    1. Run your analysis pipeline as a script (analyze.py) → produces artifacts in data/processed/
    2. Edit the BUILD CELLS section below with your title, EDA, modeling, conclusion markdown
    3. Run: python3 scripts/build_report_notebook.py

Output: docs/reports/<DATE>-<slug>.ipynb (single artifact, ready for vault publish)
"""
import json
import os
import datetime as dt

# ── Config ──
DATE = '2026-07-04'
SLUG = 'my-analysis'  # short kebab-case identifier
TITLE = 'My Analysis Title'
NOTEBOOK_PATH = f'docs/reports/{DATE}-{SLUG}.ipynb'
os.makedirs(os.path.dirname(NOTEBOOK_PATH), exist_ok=True)

cells = []

def add_md(text):
    """Add a markdown cell. text can be a single string or a list of lines."""
    if isinstance(text, list):
        cells.append({'cell_type': 'markdown', 'metadata': {}, 'source': text})
    else:
        cells.append({'cell_type': 'markdown', 'metadata': {}, 'source': [text]})

def add_code(text, exec_count=1):
    """Add a code cell. text can be a single string or a list of lines."""
    if isinstance(text, list):
        src = [l + '\n' if not l.endswith('\n') else l for l in text]
    else:
        src = [l + '\n' for l in text.split('\n')]
    cells.append({
        'cell_type': 'code',
        'metadata': {},
        'execution_count': exec_count,
        'outputs': [],
        'source': src,
    })

# ╔════════════════════════════════════════════════════════════════════════╗
# ║  BUILD CELLS — edit this section for each analysis                      ║
# ╚════════════════════════════════════════════════════════════════════════╝

# ── Title ──
add_md(f'# {TITLE}\n\n**Goal**: <one-line goal>\n**Best Model**: <name + score>\n**Reproducibility**: OK\n**Date**: {DATE}')

# ── Imports ──
add_code("""import warnings, json
warnings.filterwarnings('ignore')
import pandas as pd, numpy as np
from sklearn.model_selection import train_test_split, cross_val_score""")

# ── Data Overview ──
add_md('## 📌 데이터 개요\n\n- **소스**: `data/raw/<file>.csv` (<n> rows × <m> cols)\n- **타깃**: <target>')
add_code("df = pd.read_csv('data/raw/<file>.csv')\nprint('SHAPE:', df.shape)")

# ── EDA ──
add_md('## 📌 EDA\n\nKey insight: ...')
add_code("print(df.describe().round(2))")

# ── Hypothesis ──
add_md('## 🔬 가설 검증\n\n| # | 가설 | 결과 |\n|---|---|---|\n| H1 | ... | ✅ ... |')

# ── Modeling ──
add_md('## 📌 Modeling\n\nModel comparison:')
add_code("""models = {'Ridge': Ridge(), 'RF': RandomForestRegressor()}
for name, m in models.items():
    m.fit(X_tr, y_tr)
    print(name, m.score(X_te, y_te))""")

# ── Conclusion ──
add_md('## 📌 결론\n\n- Bullet 1\n- Bullet 2\n\n**PUBLISH**: ✅')

# ╔════════════════════════════════════════════════════════════════════════╗
# ║  END BUILD CELLS — do not edit below                                    ║
# ╚════════════════════════════════════════════════════════════════════════╝

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
with open(NOTEBOOK_PATH, 'w') as f:
    json.dump(nb, f, indent=2)
print(f"✅ Notebook saved: {NOTEBOOK_PATH} ({len(cells)} cells, {sum(1 for c in cells if c['cell_type']=='markdown')} md / {sum(1 for c in cells if c['cell_type']=='code')} code)")