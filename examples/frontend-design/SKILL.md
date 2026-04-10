---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, or applications. Generates creative, polished code that avoids generic AI aesthetics.
---

Build production-grade frontend interfaces. The user provides requirements for a component, page, or application.

## Before Coding

Write a 4-line comment block at the top of the file:

1. **Who / where** — who uses this, on what device, how often
2. **Focal point** — the single element the eye hits first; everything else supports it
3. **Mood** — three words (e.g., "warm, editorial, quiet")
4. **Omission** — one decoration or effect you are choosing NOT to add, and why

## Constraints

These prevent the specific failure modes LLMs fall into. Every rule is checkable.

### Palette & Type

- **2 font families max.** One display, one body. If the design is simple, one is better.
- **2 weights only**: 400 and 500–600. Never 700+ unless (a) the brief is explicitly bold/brutalist, or (b) the weight is used on a single hero/display element (≤1 per page) where the font is specifically designed for heavy display use.
- **Type scale**: pick 5–6 sizes from `[12, 14, 16, 18, 20, 24, 32, 42, 48, 64]px`. No sizes outside this set.
- **3 hues + 1 accent max.** All as CSS custom properties with `-bg`, `-border`, `-text` variants. **Exception**: when the design contains multiple parallel items that need independent identity (pricing tiers, team members, category tags), you may use 1 additional hue per item — provided all additional hues share the same saturation and lightness band.
- On colored backgrounds, text uses the darkest shade from that same hue family. No text directly on gradients without a solid backing surface.
- **Decorative icons** (category indicators, visual texture): use tertiary text color. **Semantic icons** (checkmarks in feature lists, status indicators, success/error marks): use primary text color OR the accent color — they carry information, never let them fade into tertiary. Test: if removing the icon loses information, it's semantic.

### Spacing & Layout

- Spacing values only from `[4, 8, 12, 16, 24, 32, 48, 64]px`.
- Container padding ≈ 2× inner gap. Related items in flow ≤8px apart; between groups ≥24px.
- **Parallel choice items** (pricing tiers, feature comparisons, option cards) need ≥16px visible gap between each — they must read as discrete choices, not a continuous block. Never use `gap: 0` on parallel choices. Parallel choice items must share the same base dimensions — differentiate the recommended item through color, weight, or border, not through size. Size mismatch breaks the "choices are comparable" contract.
- One alignment axis per section. Never mix left/center/right in the same visual group.
- **One focal point per viewport.** If everything is emphasized, nothing is.

### Motion

- **Interaction animations** (hover, click, state change): 150–300ms. Easing: `cubic-bezier(0.22, 1, 0.36, 1)` in, `ease-out` out.
- **Ambient animations** (grain, parallax, slow drift, ambient glow): 3000–8000ms, `linear` or very soft easing, transform/opacity range ≤2%. If the user's eye tracks the motion, it's too strong — halve the intensity. Ambient should feel like "something is alive" not "something is happening."
- **At most 1 interactive looping animation** visible at a time (spinners, pulses, attention-getters). Ambient loops (grain, drift, glow) don't count toward this limit but must each stay within ambient intensity rules.
- Hover lift: 2–4px max with shadow deepening. Never exceed 6px.
- Staggered reveals: ≤5 items, 60–100ms increment, total sequence <500ms.

### States

Every interactive element needs at minimum: **Default → Hover → Disabled.** Inputs add: **Focus → Error** (with message). Empty states and success confirmations must exist — never a blank void or silent completion.

### Accessibility

- Contrast ≥4.5:1 body text, ≥3:1 large text (≥24px). Touch targets ≥44×44px.
- Never convey meaning through color alone. Visible focus indicators — never bare `outline: none`.
- Semantic HTML: `<button>` for actions, `<a>` for navigation, headings in order.

## Font Selection

No blacklists — they become stale. Instead, for each font ask:
1. Does it match the mood? (geometric sans ≠ editorial; high-contrast serif ≠ utilitarian dashboard)
2. Is this font the "safe high-design default" for this category? (Inter for SaaS, Cormorant Garamond for editorial, Space Grotesk for tech, Playfair for luxury.) If yes, commit to it only if the design is otherwise restrained — otherwise pick something one step more specific (e.g., for editorial, consider Tiempos, GT Sectra, or Canela instead of Cormorant).
3. Does it render cleanly at the sizes I need?

## The Editing Pass

After the first complete implementation, before delivering:
1. Find one element to **remove**. If removing it doesn't hurt comprehension, delete it.
2. Count your interactive looping animations. If more than one, kill the weakest. For ambient loops, verify each stays within intensity limits — if any makes you want to look at it, halve its strength.
3. Verify: does the focal point actually dominate? Squint at the screen — what do you see first?
