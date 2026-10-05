# Flow Chart CSS Cheatsheet

Copy-paste ready CSS for the HTML/CSS flow node system. Use with `class="flow-chart"`, `flow-row`, `flow-node`, `flow-arrow`, `flow-decision`, `flow-group`, `flow-label`.

**Never use `display: flex` for any of these. Inline-block only.**

## Core containers

```css
.flow-chart {
  text-align: center !important;
  margin: 1em 0;
  font-family: -apple-system, "SF Pro Text", system-ui, sans-serif;
  font-size: 14px;  /* base for em-scaling of children */
}

.flow-row {
  text-align: center !important;
  line-height: 2.2;
  margin: 0.4em 0;
  word-spacing: 0.3em;  /* visual breathing room between inline-block nodes */
}

.flow-group {
  display: block;  /* NOT flex */
  text-align: center;
  background: rgba(255,255,255,0.03);
  border: 1px dashed rgba(255,255,255,0.15);
  border-radius: 14px;
  padding: 0.8em 1em;
  margin: 0.6em 0;
}

.flow-group-label {
  display: block;
  font-size: 0.65em;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--apple-body-muted, #86868b);
  font-weight: 500;
  margin-bottom: 0.6em;
}
```

## Nodes

```css
.flow-node {
  display: inline-block !important;
  vertical-align: middle !important;
  padding: 0.5em 1em;
  border-radius: 10px;
  font-size: 0.85em;
  font-weight: 500;
  text-align: center !important;
  line-height: 1.35;
  margin: 0.3em 0.25em;
  max-width: 220px;       /* prevent runaway widths */
  word-wrap: break-word;
}

.flow-node .node-label {
  display: block !important;  /* label on its own line */
  font-size: 1em;
  font-weight: 600;
  margin-bottom: 0.2em;
}

.flow-node .node-sub {
  display: block !important;  /* subtitle on its own line */
  font-size: 0.78em;
  font-weight: 400;
  opacity: 0.8;
  margin-top: 0.2em;
}
```

## Color variants (Apple system colors)

```css
/* Long-term / persistent (cyan/blue) */
.flow-node.long-term  { background: rgba(41,151,255,0.18); border: 1px solid rgba(41,151,255,0.5);  color: #fff; }

/* Tooling / interface (pink) */
.flow-node.tooling   { background: rgba(255,45,85,0.18);  border: 1px solid rgba(255,45,85,0.5);   color: #fff; }

/* Compute / processing (orange) */
.flow-node.compute   { background: rgba(255,149,0,0.18);  border: 1px solid rgba(255,149,0,0.5);   color: #fff; }

/* Data / storage (purple) */
.flow-node.data      { background: rgba(175,82,222,0.18); border: 1px solid rgba(175,82,222,0.5);  color: #fff; }

/* Output / success (green) */
.flow-node.output    { background: rgba(52,199,89,0.18);  border: 1px solid rgba(52,199,89,0.5);   color: #fff; }

/* Generic / fallback (gray) */
.flow-node.simple    { background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.22); color: #fff; }
```

## Arrows

```css
.flow-arrow {
  display: inline-block !important;
  vertical-align: middle !important;
  color: var(--apple-primary-on-dark, #2997ff);
  font-size: 1.1em;
  font-weight: 600;
  margin: 0 0.25em;
  line-height: 1;
  user-select: none;
}

.flow-arrow::before { content: "↓"; }
.flow-arrow.right::before { content: "→"; }
.flow-arrow.left::before  { content: "←"; }
.flow-arrow.up::before    { content: "↑"; }
.flow-arrow.branch::before { content: "↙"; }
```

## Decision diamonds

```css
.flow-decision {
  display: inline-block !important;
  padding: 0.5em 1.1em;
  border-radius: 14px;  /* diamond in spirit, rounded in practice */
  background: rgba(255,204,0,0.18);
  border: 1.5px solid rgba(255,204,0,0.55);
  color: #fff;
  font-size: 0.9em;
  font-weight: 500;
  font-style: italic;
  vertical-align: middle;
  margin: 0.3em 0.25em;
}
```

## Labels (under/over nodes)

```css
.flow-label {
  display: block;
  font-size: 0.7em;
  color: var(--apple-body-muted, #86868b);
  font-style: italic;
  text-align: center;
  margin: 0.3em 0;
}
```

---

## Common usage patterns

### Vertical pipeline

```html
<div class="flow-chart">
  <div class="flow-row">
    <div class="flow-node compute">
      <span class="node-label">Step 1</span>
    </div>
  </div>
  <div class="flow-arrow"></div>
  <div class="flow-row">
    <div class="flow-node data">
      <span class="node-label">Step 2</span>
    </div>
  </div>
  <div class="flow-arrow"></div>
  ...
</div>
```

### Horizontal fan-in (groups + inline-blocks)

```html
<div class="flow-row">
  <div class="flow-node long-term">A</div>
  <div class="flow-node tooling">B</div>
  <div class="flow-node compute">C</div>
</div>
```

### Decision tree

```html
<div class="flow-chart">
  <div class="flow-row">
    <div class="flow-decision">Q1 · Sensitive?</div>
  </div>
  <div class="flow-arrow"></div>
  <div class="flow-row">
    <div class="flow-node data">Yes → Local</div>
    <div class="flow-decision">No → Q2</div>
  </div>
</div>
```

### Grouped subsystem with labeled container

```html
<div class="flow-group">
  <span class="flow-group-label">Long-term organs</span>
  <div class="flow-row">
    <div class="flow-node long-term">Brain</div>
    <div class="flow-node long-term">Soul</div>
    <div class="flow-node long-term">Memory</div>
  </div>
</div>
```

### Horizontal pipeline variant

```html
<div class="flow-horizontal">
  <div class="flow-node">A</div>
  <div class="flow-arrow right"></div>
  <div class="flow-node">B</div>
  <div class="flow-arrow right"></div>
  <div class="flow-node">C</div>
</div>
```

---

## Why inline-block (recap)

| Mode | iOS Safari | Desktop | Verdict |
|---|---|---|---|
| `display: flex` | Breaks under `transform: scale()` (Reveal.js's fit mode) | Works | ❌ Avoid |
| `display: grid` | Works but `<grid>` can't wrap long `<span>` text well | Works | ⚠️ Use only for explicit 2D layouts |
| `display: inline-block + text-align: center` | Works | Works | ✅ Always |
| `float: left/right` | Works but breaks text flow | Works | ⚠️ Use only for sidebar layouts |

**Default**: `inline-block` on the node, `text-align: center` on the parent. That's it.
