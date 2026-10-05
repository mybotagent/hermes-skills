# `npx getdesign@latest` Workflow

A single command that bootstraps a complete design system reference. Use this before building any Apple/Stripe/Linear-styled deliverable.

## Basic usage

```bash
npx getdesign@latest add <brand>                 # adds DESIGN.md in current dir
npx getdesign@latest add <brand> --out <path>    # add to a specific file
npx getdesign@latest list                        # list all available brands
npx getdesign@latest add <brand> --force         # overwrite existing DESIGN.md
```

The command prints:

```
██████╗ ...
  ✓ DESIGN.md inspired by apple installed
    → /path/to/DESIGN.md
```

The output file is typically **30-40 KB of exact token reference** — colors, typography, components, mode guidance. For `apple` it includes:

- Color tokens (light + dark) with hex values
- Typography scales (Hero display, display-lg, body, caption, etc.)
- Component guidance (cards, buttons, surfaces, shadows)
- "Don't" anti-patterns (no gradients, no decorative shadows, etc.)

## After running

The DESIGN.md is the source of truth. Don't invent your own colors/fonts when a brand reference is loaded — lift from the file.

For a slide deck or web page:

1. Read the brand's color tokens
2. Pick **one** primary accent (not all of them)
3. Apply typography scale with `clamp()` for fluid sizing in slides
4. Use card / button patterns verbatim
5. Skip the anti-patterns explicitly called out

The command's tail tells your coding agent exactly what to do:

> Tell your coding agent to use this file as reference before writing any UI. Customize it as your project evolves.

## Available brands

Useful ones (from `npx getdesign@latest list`):

| Brand | Style | Use when |
|---|---|---|
| **apple** | Consumer electronics, premium white space, SF Pro, cinematic imagery | "Apple-style", keynote-style, premium work showcase |
| **stripe** | SaaS / fintech, navy + sky-blue accent, clean documentation | "Like Stripe", SaaS-style |
| **linear** | Ultra-minimal, purple accent, project management | "Linear-style", minimal tools |
| **vercel** | Black + white, motion-first | "Vercel-style", modern web |
| **figma** | Vibrant multi-color, playful yet professional | "Figma-style", design tool |
| **cursor** | Sleek dark, AI tools | "Cursor-style", AI assistant showcase |
| **claude** | Warm terracotta, editorial | "Claude-style", warm/editorial |
| **notion** | Friendly, structured data | "Notion-style", docs/notes |
| **airbnb** | Warm coral, photography-driven | "Airbnb-style", travel/lifestyle |
| **github** | Developer-focused dark | "GitHub-style", code-heavy |

Choose the brand that matches the user's intent. Generic or "premium" → apple. SaaS docs → stripe. Modern web → vercel.

## Compatibility note

Some users already have `getdesign` files committed (`DESIGN.md`, `<brand>-DESIGN.md`). Two ways to handle:

- If user already ran `add apple` before: file exists. Either reuse it (`--force` to overwrite) or move it aside.
- The `<brand>-DESIGN.md` filename pattern means users can keep multiple brands in one repo and tell the agent which to use.

## User's emphasis (from this skill's source session)

The user said "Apple 디자인 제대로 적용해라, 내가 줬단 디자인 템플릿으로" multiple times. Partial application reads as "not Apple". Use the tokens verbatim — `#0066cc` is Action Blue, `#f5f5f7` is canvas-parchment, `#1d1d1f` is ink. Don't substitute similar shades "for variety". Apple design has one accent — use the one.

## Workflow when user wants Apple-design

```bash
# 1. Bootstrap the design system
npx getdesign@latest add apple

# 2. Read the resulting DESIGN.md to extract tokens
# 3. Apply exact tokens to inline CSS in your deck's index.html
# 4. Don't add gradients, multi-accent palettes, or decorative shadows
# 5. Use SF Pro Display for headings, SF Pro Text for body
# 6. White canvas, #f5f5f7 cards, #0066cc single accent, #1d1d1f ink
```
