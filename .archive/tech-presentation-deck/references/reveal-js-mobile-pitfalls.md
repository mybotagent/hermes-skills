# Reveal.js + iOS Safari / mobile pitfalls

Collected bugs and their fixes from real deck debugging.

## 1. Reveal.js `transform: scale()` clips slides on mobile

**Symptom**: Slide looks correct on desktop, but on iPhone Safari (and sometimes Chrome Android) the bottom half of every slide is cut off, and flow-chart nodes overlap in a pile near the slide top.

**Cause**: Reveal.js wraps every slide in `transform: scale(N) translate3d(...)` to fit the slide to the viewport. That scale transform is broken by iOS Safari's grid/flexbox implementation in subtle ways — children that use flex + gap + transform render outside the clipped region.

**Fix**: Disable the layout transform entirely. In `Reveal.initialize`:
```js
Reveal.initialize({
  disableLayout: true,   // <-- non-negotiable
  ...
});
```
Then manually size each slide via CSS:
```css
.reveal .slides { position: absolute; inset: 0; transform: none !important; }
.reveal .slides > section {
  width: 100% !important; height: 100% !important;
  position: absolute !important; top: 0; left: 0;
  display: none;
}
.reveal .slides > section.present { display: block !important; }
```

## 2. Flexbox inside slides breaks under transform

**Symptom**: Flow-chart nodes render stacked on top of each other in a single position.

**Cause**: Safari + transform + flex = various bug paths, depends on iOS version.

**Fix**: Never use `display: flex` for slide-internal layout. Use:
- `text-align: center` + `display: inline-block` for horizontal flow rows
- `display: block` for vertical containers
- Inline children with `vertical-align: middle`

## 3. Card hover `transform: scale()` interacts badly with parent transform

**Symptom**: Hovering a node card looks fine on desktop but causes ghosting on mobile.

**Fix**: Either remove the hover transform, or apply it to a child element not the node itself.

## 4. Slide section padding too tight — content hidden behind status bar / nav

**Symptom**: On iPhone, the top 40px of every slide is hidden behind the status bar / address bar.

**Fix**: Use percentage-based padding (e.g., `padding: 4vh 4vw`) not absolute padding. Add `viewport-fit=cover` to viewport meta tag. Apple status bar overlap is real; leave breathing room.

## 5. Touch tap through card/button to underlying slide

**Symptom**: Tapping a card or button on touch devices triggers slide transition instead of card action.

**Fix**: `touch-action: manipulation` on `html, body`. This prevents iOS double-tap zoom and pointer event surprise.

## 6. Vertical slides count as separate slides in hash routing

**Symptom**: User navigates to `#/13` and sees blank because there are only 10 horizontal slides.

**Cause**: Reveal.js URL hash is `#/H` or `#/H/V`. If a slide has vertical children (`----` separator), the count increments for each. Some browsers also count nested `<section>` markup if your markdown plugin nests them.

**Fix**: Use one external `<section data-markdown="X.md">` containing all slides in `X.md`, separated by horizontal `---` only. Don't use `----` (4-dash) vertical separators unless you actually want vertical slides. Don't have multiple `<section data-markdown>` blocks at the top level of `.slides`.

## 7. Markdown plugin `smartypants` mangles typography

**Symptom**: `--` becomes an em-dash, straight quotes become curly, breaking copy-paste from code blocks.

**Fix**:
```js
markdown: { smartypants: false, gfm: true }
```

## 8. iOS Safari `100vh` ≠ actual viewport height

**Symptom**: Slide content bottom-aligned to wrong position; overflow scrolls unexpectedly.

**Fix**: Use `max-height: calc(100vh - Nvh)` where N is the cumulative top+bottom padding of the section. Do not use `100dvh` — Reveal's layout handles the actual viewport.

## 9. Inline SVG `<img>` renders at default 300×150

**Symptom**: A 1600×900 SVG diagram renders as a tiny 300×150 image in the slide.

**Cause**: When SVG file has only `viewBox=` and no explicit `width=` / `height=` attributes, browsers default to 300×150 (the default replaced element size).

**Fix**: Add explicit dimensions to the `<svg>` root:
```xml
<svg viewBox="0 0 800 400" width="800" height="400"
     preserveAspectRatio="xMidYMid meet" ...>
```
Then in CSS:
```css
.reveal .slides > section img {
  display: block !important;
  max-width: 100% !important;
  max-height: calc(100vh - 16vh) !important;
  margin: 0.6em auto !important;
  object-fit: contain;
}
```

## 10. Custom fonts (`@font-face`) blank on mobile

**Symptom**: Apple-style font loads on desktop, falls back to serif on mobile.

**Fix**: Don't `@font-face` SF Pro. The system `-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue"` stack is what Apple devices have natively. Add fallbacks (`system-ui, sans-serif`) for non-Apple clients.
