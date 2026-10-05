# Pure-Python SVG Charts for Analysis Reports

Why this exists: matplotlib charts require a display backend, slow with seaborn, and produce
PNG/SVG-with-embedded-fonts that bloat git repos. For static analysis reports that need to render
in markdown/GitHub/Hermes, hand-rolled SVG is faster, smaller, and 100% reproducible.

## When to use

- Static analysis reports (ipynb + standalone .md in vault repos)
- When matplotlib isn't installed or is slow
- When you need pixel-perfect control over layout (Apple-style, brand-aligned)
- When SVG must be inline-viewable in markdown via `![](charts/...svg)` (GitHub renders it)

## Anatomy of a single chart

```python
PALETTE = {
    'bg': '#FFFFFF',
    'text': '#1D1D1F',
    'muted': '#6E6E73',
    'primary': '#0071E3',
    'secondary': '#34C759',
    'accent': '#FF9500',
    'warn': '#FF3B30',
    'grid': '#E5E5EA',
}

def svg_header(w=900, h=600):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="-apple-system, 'SF Pro Display', system-ui, sans-serif">
<rect width="100%" height="100%" fill="{PALETTE['bg']}"/>
<style>
  .title {{ font-size: 18px; font-weight: 600; fill: {PALETTE['text']}; }}
  .subtitle {{ font-size: 12px; fill: {PALETTE['muted']}; }}
  .label {{ font-size: 11px; fill: {PALETTE['text']}; }}
  .label-sm {{ font-size: 10px; fill: {PALETTE['muted']}; }}
  .value {{ font-size: 11px; fill: {PALETTE['text']}; font-weight: 500; }}
</style>
'''
```

## 6 chart types that cover 95% of analysis

### 1. Horizontal bar (top-N ranking)

```python
# Inputs: Series indexed by name, values to plot
items = top_skills  # already sorted desc
n = len(items)
W, H = 900, 600
ml, mr, mt, mb = 180, 60, 80, 50
plot_w, plot_h = W - ml - mr, H - mt - mb
bar_h, gap = plot_h / n * 0.7, plot_h / n * 0.3

svg = svg_header(W, H)
svg += f'<text x="{ml}" y="35" class="title">Title</text>\n'
svg += f'<text x="{ml}" y="55" class="subtitle">Subtitle</text>\n'

mx = items.max()
for i, (name, v) in enumerate(items.items()):
    y = mt + i * (bar_h + gap)
    blen = v / mx * plot_w
    color = PALETTE['primary'] if i < 5 else PALETTE['accent'] if i < 10 else PALETTE['muted']
    svg += f'<rect x="{ml}" y="{y:.1f}" width="{blen:.1f}" height="{bar_h:.1f}" fill="{color}" rx="2"/>\n'
    svg += f'<text x="{ml - 8}" y="{y + bar_h/2 + 4:.1f}" class="label" text-anchor="end">{name}</text>\n'
    svg += f'<text x="{ml + blen + 8:.1f}" y="{y + bar_h/2 + 4:.1f}" class="value">{v:.1f}%</text>\n'

with open('out.svg', 'w') as f:
    f.write(svg + '</svg>')
```

### 2. Diverging bar (positive/negative)

For uplift-style charts with zero baseline:

```python
zero_x = ml + (0 - min_v) / (max_v - min_v) * plot_w
# ... inside loop:
if val >= 0:
    x, color = zero_x, PALETTE['secondary']
else:
    x, color = zero_x - bar_len, PALETTE['warn']
svg += f'<line x1="{zero_x:.1f}" y1="{mt}" x2="{zero_x:.1f}" y2="{H-mb}" stroke="{PALETTE["text"]}"/>\n'
```

### 3. Vertical bar (grouped means)

```python
# Each group is one position along x-axis
group_w = plot_w / n_groups
bar_w = group_w * 0.7
for i, (label, val) in enumerate(groups):
    x = ml + i * group_w + (group_w - bar_w) / 2
    bh = (val / max_v) * plot_h
    svg += f'<rect x="{x:.1f}" y="{H - mb - bh:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" fill="{PALETTE["primary"]}" rx="2"/>\n'
    svg += f'<text x="{x + bar_w/2:.1f}" y="{H - mb - bh - 6:.1f}" class="value" text-anchor="middle">${val:.0f}K</text>\n'
```

### 4. Strip plot / jittered scatter (salary by category)

```python
np.random.seed(group_idx)
for j, v in enumerate(values):
    if j > 80: break  # cap dots for readability
    jx = cx + (np.random.rand() - 0.5) * bar_w * 0.6
    svg += f'<circle cx="{jx:.1f}" cy="{H-mb - (v/range_max)*plot_h:.1f}" r="2.5" fill="{PALETTE["primary"]}" opacity="0.35"/>\n'
# Overlay mean bar and median dot
svg += f'<line x1="{cx-bar_w/2}" y1="{mean_y}" x2="{cx+bar_w/2}" y2="{mean_y}" stroke="{PALETTE["accent"]}" stroke-width="3"/>\n'
svg += f'<circle cx="{cx}" cy="{med_y}" r="5" fill="{PALETTE["text"]}"/>\n'
```

### 5. Feature importance (horizontal bar, sorted ascending)

Same as chart 1 but `items = items.sort_values()` so the largest importance appears at top.

### 6. Grouped comparison (sector/state distribution)

Same as chart 3.

## Y-axis grid + ticks

```python
for v in [0, 50, 100, 150]:
    y = H - mb - (v/range_max) * plot_h
    svg += f'<line x1="{ml}" y1="{y:.1f}" x2="{W-mr}" y2="{y:.1f}" stroke="{PALETTE["grid"]}" stroke-width="1"/>\n'
    svg += f'<text x="{ml - 8}" y="{y + 4:.1f}" class="label-sm" text-anchor="end">${v}K</text>\n'
```

## Reference in markdown

Once saved to `docs/charts/NN_name.svg`, reference inline:

```markdown
![Top Skills](charts/01_top_skills.svg)
```

GitHub renders this in markdown. For notebooks, embed via HTML cell or markdown cell with same syntax.

## Pitfalls

1. **rx="2"** on `<rect>` gives rounded corners — visual polish with no perf cost.
2. **`text-anchor="end"`** for left-aligned labels at right edge of plot.
3. **`viewBox="0 0 W H"`** + matching `width`/`height` ensures responsive scaling.
4. **Color cycling**: pick top-N=primary, next-N=accent, rest=muted. Don't pick from a 12-color palette every bar.
5. **Jitter dots**: cap at 80 per group, opacity 0.35 — full data overwhelms the eye.
6. **Font** `-apple-system, 'SF Pro Display', system-ui, sans-serif` falls back gracefully on Linux.
7. **f-strings with `{{` escaping** — when embedding CSS in SVG header, double braces for literal `{`.

## Reference implementation

See `scratch/make_charts.py` in the DS-job-market analysis session
(`/tmp/ds_jobs/scratch/make_charts.py`) — generates 6 SVGs covering all the chart types above
in ~200 lines of pure Python, no matplotlib.