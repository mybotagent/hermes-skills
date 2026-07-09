# Card-Format Index (first-slide navigation hub)

Use when the deck covers 6+ sections and you want one-click navigation instead of arrow-key mashing.

## Why better than text TOC

- One click jumps to the section (vs holding arrow keys)
- Works on touch devices (text TOC requires keyboard)
- Visual card stack is more scannable than a multi-column table
- Hover state (`transform: translateY(-4px)`) gives explicit affordance

## When to use

- 6+ sections in the deck (sparse decks don't need this)
- Public-facing deck (the audience appreciates finding the section quickly)
- Multi-topic decks (mixing engineering + product + business)

Don't use when:
- The deck is one or two topics (linear flow is clearer)
- The deck is meant to be walked through sequentially (a TOC teaches you the order; a card grid hands you a menu)

## Pattern (3 steps)

### Step 1 — Pre-compute global slide indices

Reveal's `Reveal.slide(N)` expects a GLOBAL index (across all sections, including the hero). Build a small mapping table BEFORE writing the index slide:

```
S0.1 = 0   (Hero title)
S0.2 = 1   (Hero card index — this slide)
S1.1 = 2   (Section 1 first slide)
S1.2 = 3
... etc
```

Tip: write each section's slides into its own file, count the `---` separators (each = 1 horizontal slide), accumulate, and put the cumulative count next to each section start in the table.

### Step 2 — Author the first content slide

`slides/00-hero.md` after the title slide — the index. Each card uses `onclick="Reveal.slide(N)"` with the section's START index from Step 1:

```html
<div class="index-grid">

  <div class="index-card" onclick="Reveal.slide(2)">
    <div class="card-icon">🧠</div>
    <div class="card-num">S1</div>
    <div class="card-title">Section Name</div>
    <div class="card-desc">One-line description</div>
    <div class="card-meta">4 slides · 3 mermaid</div>
  </div>

  <div class="index-card" onclick="Reveal.slide(6)">
    <div class="card-icon">🚀</div>
    <div class="card-num">S2</div>
    <!-- ... -->
  </div>

  <!-- repeat per section; last card is often a "← back to title" jump -->

</div>

<p class="click-hint">💡 카드를 클릭하면 해당 섹션으로 이동 · 키보드 ← → 도 사용 가능</p>
```

### Step 3 — Add CSS

`templates/custom.css` already contains the working styles. Key rules:

```css
.reveal .index-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);   /* adjust to repeat(3, 1fr) for 3-col */
  gap: 0.8em;
  margin: 1em 0;
}
.reveal .index-card {
  background: rgba(0, 212, 255, 0.08);
  border: 1px solid var(--hermes-primary);
  border-radius: 12px;
  padding: 1em 0.6em;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 170px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.reveal .index-card:hover {
  background: rgba(0, 212, 255, 0.22);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 212, 255, 0.4);
  border-color: var(--hermes-accent);
}
.reveal .index-card .card-icon  { font-size: 2.2em; }
.reveal .index-card .card-num   { color: var(--hermes-accent); font-weight: 700; }
.reveal .index-card .card-title { font-size: 0.8em; font-weight: 600; }
.reveal .index-card .card-desc  { color: var(--hermes-dim); font-size: 0.55em; font-style: italic; }
.reveal .index-card .card-meta  { color: var(--hermes-secondary); font-size: 0.5em; font-weight: 600; }
```

## Card density rules of thumb

- 4 columns × 2 rows = 8 cards max (works well at 1280×720)
- 3 columns × 3 rows = 9 cards if you have descriptions
- If you exceed 8 cards, add another row or split into "Engineering" / "Product" sub-sections

## Constraints

- Reveal.js markdown plugin renders inline HTML (default ON), so `onclick` and HTML classes pass through.
- `Reveal.slide(N)` is a global function (loaded by reveal.js). Works inside `onclick` because Reveal initializes BEFORE user interaction.
- Caveat: if user is on the LAST horizontal slide of a section, pressing right arrow from the index will navigate to S2 first horizontal slide — that's expected. Recommend adding a "← 처음으로" card as the last index entry to return.

## Working example

https://mybotagent.github.io/hermes-architecture-deck/

First content slide (after title) is the 8-card grid; clicking any card jumps directly to that section.
