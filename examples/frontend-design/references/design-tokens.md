# Design Tokens

Numerical scales for spacing, typography, and rhythm. Used by `layout-judgment.md` and the main SKILL.md.

These are not "the answers" — they are calibrated options. Pick a scale that matches the chosen grid and aesthetic. Mixing scales within a single design causes visual incoherence; commit to one per project.

---

## Naming conventions

Token names are the interface between design decisions and the code that consumes them. Bad names lock the system to a specific visual moment; good names survive redesigns.

### Four-layer architecture

| Layer | Purpose | Example |
|-------|---------|---------|
| Primitives | Raw values, never used directly by components | `blue-50`, `blue-900`, `space-16` |
| Semantics | Purpose-led aliases that components reference | `--color-primary`, `--color-danger`, `--space-section` |
| Components | Scoped to a specific UI element | `--button-bg`, `--card-border`, `--input-focus` |
| Pages | Page-specific overrides (use sparingly) | `--hero-bg`, `--footer-divider` |

Components reference semantics; semantics reference primitives. A component token should not hardcode a primitive value directly — if it does, rename the semantic or add one.

### Rules

- **Never name by appearance.** `--color-red-button` rots the moment the button turns blue. Use `--color-button-danger`.
- **Don't over-generalize.** `--color-1` carries no meaning — whoever edits next will guess wrong.
- **Don't over-specify.** `--color-signup-button-hover-large-screen` is a dead end. Keep tokens reusable.
- **Primitives use a brightness scale.** `blue-50` (lightest) → `blue-900` (darkest), Adobe Spectrum style. Numeric steps make relationships legible.

### Anti-patterns to reject

- `primary` — primary what? Color? Button? Heading?
- `dark-gray` — what does this become in dark mode?
- `button-color` — split into `button-bg`, `button-text`, `button-border` so each is addressable

---

## Spacing scales

Pick one base unit and stick with it. The base unit determines the rhythm of the entire interface.

### 4-base (compact, functional)
Best for: dashboards, data-dense UIs, dense editorial layouts, mobile-first products.

```
space-0:  0
space-1:  4px
space-2:  8px
space-3:  12px
space-4:  16px
space-5:  24px
space-6:  32px
space-7:  48px
space-8:  64px
space-9:  96px
space-10: 128px
```

### 8-base (default for marketing and brand)
Best for: most landing pages, product pages, brand sites, hero-led layouts.

```
space-0:  0
space-1:  8px
space-2:  16px
space-3:  24px
space-4:  32px
space-5:  48px
space-6:  64px
space-7:  96px
space-8:  128px
space-9:  192px
space-10: 256px
```

### Fibonacci (organic, editorial)
Best for: long-form editorial, fashion, gallery sites, anywhere "natural rhythm" matters.

```
space-0:  0
space-1:  8px
space-2:  13px
space-3:  21px
space-4:  34px
space-5:  55px
space-6:  89px
space-7:  144px
space-8:  233px
```

### Selection rule
- If the design will repeat hundreds of times (cards, list items, table rows) → 4-base
- If the design is a one-time hero/landing/brand surface → 8-base
- If the design wants to feel hand-drawn or organic → Fibonacci

---

## Type scales (modular)

Each scale defines the ratio between adjacent type sizes. Pick one ratio, then build the scale from a base size (usually 16px).

### Tight scales — dense layouts, multi-column editorial, dashboards
- **1.125 (major second)** — very subtle hierarchy; for content where rank matters less than rhythm
- **1.2 (minor third)** — clean editorial, magazine-style multi-column
- **1.25 (major third)** — UI defaults; comfortable for most product surfaces

### Open scales — marketing, brand, hierarchical layouts
- **1.333 (perfect fourth)** — strong but not aggressive hierarchy; default for landing pages
- **1.414 (augmented fourth)** — distinct levels, design-led marketing pages

### Dramatic scales — centered monument, broken editorial, hero-led
- **1.5 (perfect fifth)** — display-heavy designs; one big level dominates
- **1.618 (golden ratio)** — extreme hierarchy; used in brand and luxury surfaces
- **1.778 (minor seventh)** — extreme contrast; only for poster-style hierarchical grids

### Worked example (base 16, ratio 1.333)

Built up from the body floor (16px) and the caption floor (14px). Sizes below 14px are mathematically possible from the same ratio (≈9px, ≈12px) but are reserved for legal copy or decorative micro-labels — never for normal UI reading.

```
text-xs:    14px     (floor)              — captions, meta
text-base:  16px                          — body
text-lg:    21px     (16 × 1.333)         — lead paragraph, large body
text-xl:    28px     (16 × 1.333²)        — h4 / section title
text-2xl:   38px     (16 × 1.333³)        — h3
text-3xl:   50px     (16 × 1.333⁴)        — h2
text-4xl:   67px     (16 × 1.333⁵)        — h1
text-5xl:   89px     (16 × 1.333⁶)        — display
text-6xl:   119px    (16 × 1.333⁷)        — hero display
```

### Floor and ceiling
- **Body floor**: 16px for any mixed-case reading copy
- **Caption floor**: 14px for inline meta, picture captions, short supporting copy
- **All-caps label floor**: 11px, but only when tracking ≥ 0.15em (editorial convention; wide tracking restores legibility at small sizes)
- **Absolute floor**: 11px — never below, even for decorative copy the user is expected to read
- **Ceiling**: no maximum — let display sizes go to 200px+ when the grid demands it

### Selection rule
Match the ratio to the grid:
- Manuscript / Column / Modular / Bento → 1.25 to 1.333
- Hierarchical / Asymmetric Split → 1.333 to 1.5
- Centered Monument / Broken Editorial → 1.5 to 1.778
- Rail + Stage → 1.2 to 1.333 (rail needs tight scale; stage can use larger)

---

## Readability (measure / line length)

Line length — often called *measure* — controls how easily the eye tracks from the end of one line back to the start of the next. Too long and the eye loses its place; too short and reading feels choppy.

| Context | Characters per line (CPL) |
|---------|---------------------------|
| Desktop body text | 45–75 |
| Mobile body text | 35–50 |
| Ideal for long-form reading | 50–60 |

### How to enforce

- Cap `max-width` on text blocks using `ch` units: `max-width: 65ch` holds across most body sizes.
- When the column is wider than the measure allows, indent the text block or split into multi-column.
- Verify with real content at the chosen size — not lorem ipsum, which has artificial word lengths.

### Relation to line-height

Longer lines need more line-height to prevent the eye from losing its row. If a layout pushes CPL above 75, raise line-height toward 1.7. If CPL is short (40–50), line-height can stay around 1.5.

---

## Line-height scales

Line-height should match the role of the text, not the size.

| Role | Line-height multiplier | Why |
|------|----------------------|-----|
| Display headings (≥48px) | 1.0 to 1.1 | Tight, monumental, no air between lines |
| Section headings (24–48px) | 1.1 to 1.25 | Compact but readable |
| Body text (14–20px) | 1.5 to 1.7 | Comfortable reading rhythm |
| Long-form body (manuscript, editorial) | 1.6 to 1.8 | Eye-tracking ease over many paragraphs |
| Captions / meta (≤14px) | 1.3 to 1.4 | Avoid loose feel at small sizes |

### Baseline alignment
If using a Baseline Grid (4 or 8px), round all line-heights so the resulting `font-size × line-height` is a multiple of the baseline unit. Example:
- 16px body × 1.5 = 24px (snaps to 8px baseline ✓)
- 18px body × 1.5 = 27px (does not snap — adjust to 1.555 → 28px)

---

## Letter-spacing (tracking)

| Context | Tracking | Why |
|---------|----------|-----|
| Display headings | -0.02em to -0.04em | Tight tracking compensates for visual gaps at large sizes |
| Body text | 0 (default) | Designed by the typeface; don't override |
| All-caps labels | +0.05em to +0.1em | Caps need extra space to remain readable |
| Chinese / CJK | 0 to +0.05em | CJK rarely needs negative tracking |

---

## Color tokens (structure, not values)

Color values belong in style files (`references/styles/<style>.md`), not here. But every style should define these slots:

```
--color-bg              page background
--color-surface         elevated surface (card, modal)
--color-text-primary    main text (≥4.5:1 contrast against bg)
--color-text-secondary  reduced emphasis (use opacity 70% of primary OR a separate hex; verify final contrast ≥4.5:1 against actual bg)
--color-text-tertiary   minimal emphasis (opacity 45%; for non-essential reading only; verify ≥3:1 against actual bg; never use for body, primary CTAs, or interactive labels)
--color-accent          single dominant accent (one only — sharp accents beat distributed palettes)
--color-border          dividers, borders
--color-focus           focus ring (must be visible against all backgrounds)
```

### Selection rule
- Light mode: bg = near-white (off-white better than pure #ffffff for editorial)
- Dark mode: bg = near-black (#0a0a0a or similar; pure black is harsh)
- Accent: one color, used sparingly — accent works because it's rare

---

## Radius scales

Pick one. Mixing radius values within a design breaks visual rhyming.

| Style | Radius | Use for |
|-------|--------|---------|
| Brutalist / editorial | 0 | Sharp corners, no softening |
| Modern functional | 4–8px | UI defaults, cards, inputs |
| Friendly / playful | 12–24px | Marketing surfaces, brand sites |
| Pill / fully rounded | 9999px | Tags, badges, single-purpose buttons |

---

## Shadow scales

Shadows are a depth language. Pick a system, not individual values.

### Realistic (elevation-based)
```
shadow-1: 0 1px 2px rgba(0,0,0,0.05)
shadow-2: 0 4px 8px rgba(0,0,0,0.08)
shadow-3: 0 12px 24px rgba(0,0,0,0.10)
shadow-4: 0 24px 48px rgba(0,0,0,0.12)
```

### Hard-shadow (brutalist, illustrative)
```
shadow-hard-1: 4px 4px 0 currentColor
shadow-hard-2: 8px 8px 0 currentColor
```

### No shadow (flat, brutalist, editorial)
Use borders or background contrast for depth instead.

---

## Animation tokens (use sparingly)

The user has explicitly asked for layout-led, not motion-led design. These are minimums for accessibility, not creative ambition.

| Token | Value | Use |
|-------|-------|-----|
| duration-fast | 150ms | Hover, focus, active state changes |
| duration-base | 250ms | Modals, dropdowns, panel toggles |
| duration-slow | 400ms | Page transitions, hero reveals |
| ease-default | cubic-bezier(0.4, 0, 0.2, 1) | All UI transitions |

---

## Validation checklist

Before delivering, verify:
- [ ] Tokens follow the four-layer naming structure (primitives → semantics → components)
- [ ] No token name encodes appearance (no `-red-`, `-dark-`, `-large-screen-`, etc.)
- [ ] Spacing values come from one scale (no ad-hoc pixel values)
- [ ] Type scale uses one ratio; sizes derive from it (not invented)
- [ ] Body line length 45–75 CPL desktop / 35–50 CPL mobile
- [ ] Line-heights snap to baseline if Baseline Grid is in use
- [ ] Body text ≥16px; captions ≥14px; all-caps tracked labels ≥11px; nothing readable below 11px
- [ ] Single accent color used sparingly (appears on the focal element + at most one other element per viewport)
- [ ] Radius is consistent across all elements of the same kind
- [ ] Contrast ratios meet WCAG AA (4.5:1 body, 3:1 large)
