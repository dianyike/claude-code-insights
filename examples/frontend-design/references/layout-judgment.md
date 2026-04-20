# Layout Judgment

This file is the layout-led decision spine for the `frontend-design` skill. Use it when the task is layout-driven, editorial, brand-led, or aims for Awwwards-quality typographic composition.

Walk the three layers in order. Each layer's output constrains the next — never skip ahead.

---

## Layer 1 — Purpose (decide before any visual choice)

Answer all three before touching grid or typography. Write the answers in the response so they constrain the rest of the decisions.

1. **Reader's intent** (pick one):
   - `acquire-info` — find a fact, complete a task
   - `be-persuaded` — accept a claim, move toward conversion
   - `make-decision` — compare options, choose between paths
   - `feel-atmosphere` — absorb mood, brand, or aesthetic

2. **Success criteria** (one specific behaviour):
   - "Within 3s, reader understands X"
   - "Reader clicks Y" / "Reader scrolls past Z"
   - "Reader remembers W after closing the tab"

3. **Information density** (pick one):
   - `high` — functional surfaces (dashboards, tables, forms, search)
   - `medium` — product pages, marketing pages with proof
   - `low` — brand surfaces, hero pages, single-message landings

These three answers map directly onto Layer 2's grid choice. If the answers are vague, ask the user before moving on.

---

## Layer 2 — Structure (choose the grid)

### Selection cheat sheet

| Density | Intent | Default grid |
|---------|--------|--------------|
| low | feel-atmosphere | Centered Monument |
| low | be-persuaded | Asymmetric Split |
| medium | be-persuaded | Asymmetric Split / Hierarchical |
| medium | make-decision | Bento / Modular |
| medium | acquire-info | Column Grid |
| high | acquire-info | Rail + Stage / Modular |
| any | feel-atmosphere + editorial tone | Broken / Off-Grid Editorial |
| long-form text | acquire-info | Manuscript (+ Baseline) |

`Baseline Grid` is not a standalone choice — it overlays any of the above to enforce vertical rhythm. Always pair Baseline with a column or modular grid when typography matters.

### Grid catalog

Each entry uses the same seven fields so they can be compared and combined.

#### 1. Manuscript (Single Column)
- **Use when**: long-form reading, essays, documentation, single-narrative landing
- **Avoid when**: multiple parallel modules, comparison views, dashboards
- **Signals this is the right choice**: reader is here to read; line length matters more than navigation
- **Core composition rules**: one centered or left-aligned text column, max line length 60–75 characters, generous top/bottom padding, single dominant typeface for body
- **Allowed grid breaks**: full-bleed images or pull quotes that span beyond the column
- **Common failure mode**: column too wide (loss of reading rhythm); too many sidebars distract from the spine
- **Mobile collapse**: already single column — only adjust margins and font size

#### 2. Column Grid (Multi-Column)
- **Use when**: news, magazines, structured editorial content with parallel sections
- **Avoid when**: long single-narrative reading; conversion-focused pages with one CTA
- **Signals this is the right choice**: content has natural parallel categories or a need for scannable density
- **Core composition rules**: 2–4 text columns sharing a baseline, repeated left edges, consistent gutter (16–32px desktop)
- **Allowed grid breaks**: a feature image, pull quote, or stat that spans 2+ columns
- **Common failure mode**: too many columns at small breakpoints (text becomes unreadable)
- **Mobile collapse**: stack to one column; preserve hierarchy through spacing, not effects

#### 3. Modular Grid
- **Use when**: portfolios, product galleries, image-heavy catalogs, design systems documentation
- **Avoid when**: long-form text; single-message marketing pages
- **Signals this is the right choice**: many items of similar weight need equal visual treatment
- **Core composition rules**: equal-size cells, fixed aspect ratios, consistent gutter, repeating typographic block per cell
- **Allowed grid breaks**: a single oversized cell (2×2) to anchor the grid and break monotony
- **Common failure mode**: every cell looks identical → flat, lifeless; no visual entry point
- **Mobile collapse**: collapse based on minimum readable card width (target ≥160px per cell). 2 columns when content allows; 1 column when card width or content density requires

#### 4. Hierarchical Grid
- **Use when**: posters, art-direction-led landing pages, campaign sites, feature announcements
- **Avoid when**: dense functional UIs; comparison or list-heavy pages
- **Signals this is the right choice**: one element must dominate; the rest support it without competing
- **Core composition rules**: one anchor element occupying ≥40% of the visible area, supporting elements aligned to anchor edges (not to a uniform grid), intentional asymmetry
- **Allowed grid breaks**: this grid IS the break — but supporting elements must still align to the anchor
- **Common failure mode**: secondary elements rival the anchor → no visual hierarchy
- **Mobile collapse**: anchor first and full-width; supporting elements stack below in original order

#### 5. Baseline Grid (Overlay)
- **Use when**: any layout where typography carries the design (editorial, manuscript, magazine)
- **Avoid when**: poster-style hierarchical layouts where typographic rhythm doesn't apply
- **Signals this is the right choice**: multiple text blocks need to feel typographically united
- **Core composition rules**: vertical rhythm of 4 or 8px; line-height + margin-top all snap to baseline; headings align to the same baseline as adjacent body
- **Allowed grid breaks**: display headings can ignore baseline if the rest of the page snaps strictly
- **Common failure mode**: each block has its own line-height → page feels typographically loose
- **Mobile collapse**: keep the same baseline unit; adjust font sizes within it

#### 6. Bento Grid
- **Use when**: product feature showcases, dashboards, marketing pages with mixed content types (image + stat + quote + chart)
- **Avoid when**: pure long-form content; single-focal landings
- **Signals this is the right choice**: 4–9 distinct content types need to coexist with intentional weight differences
- **Core composition rules**: cells of varying sizes (1×1, 2×1, 1×2, 2×2 in CSS Grid terms) on a shared underlying grid, consistent gutter, every cell self-contained, alignment to grid lines is non-negotiable
- **Allowed grid breaks**: a cell that bleeds to one screen edge for emphasis
- **Common failure mode**: random sizing without underlying grid → looks chaotic; too many large cells → loses contrast
- **Mobile collapse**: stack into one or two columns; preserve relative size hierarchy through height

#### 7. Asymmetric Split (Two-Zone)
- **Use when**: hero sections, brand pages, "feature + supporting visual" layouts
- **Avoid when**: both sides need equal weight (use a symmetric split or Modular instead); comparison pages where each side must read as equal in importance; high-density content
- **Signals this is the right choice**: one side carries the message, the other supports it (image, secondary content)
- **Core composition rules**: 2 unequal vertical fields (e.g., 60/40 or 65/35), one side leads visually, hard edge alignment between zones, type on the dominant side starts at top
- **Allowed grid breaks**: image bleeds across the split line, or one element overlaps both zones
- **Common failure mode**: 50/50 split (kills hierarchy); equal visual weight on both sides
- **Mobile collapse**: stack with dominant zone first; preserve dominance through size and spacing

#### 8. Centered Monument
- **Use when**: prestige/luxury brand pages, single-message announcements, conference/event landings
- **Avoid when**: high information density; functional surfaces; comparison content
- **Signals this is the right choice**: one statement must own the entire viewport
- **Core composition rules**: one centered focal axis, oversized type (often display weight), strict vertical rhythm, ≤3 element widths total, generous negative space on all sides
- **Allowed grid breaks**: a single intentional offset element (one corner, one edge) — never more than one
- **Common failure mode**: adding too many secondary elements → focal point dilutes; off-center "balance" attempts that look accidental
- **Mobile collapse**: keep single-column centered; preserve type dominance even if size shrinks

#### 9. Broken / Off-Grid Editorial
- **Use when**: fashion, art, gallery, photography, music, awwwards-style editorial brand experiences
- **Avoid when**: any context where misalignment reads as a bug (finance, healthcare, government, B2B SaaS)
- **Signals this is the right choice**: aesthetic experimentation is part of the brief; reader expects designed-ness
- **Core composition rules**: an underlying grid still exists, but selected elements deliberately violate it (rotated, offset, overlapping); violations are intentional and patterned (e.g., "every third heading rotates 4°")
- **Allowed grid breaks**: this is the break — but at least 60% of the page must still respect the underlying grid for the violations to read as intentional
- **Common failure mode**: random violations without an underlying grid → reads as broken, not designed
- **Mobile collapse**: drop most violations; keep one or two signature breaks to preserve identity

#### 10. Rail + Stage
- **Use when**: documentation, dashboards, admin panels, file browsers, long-form reading with persistent navigation
- **Avoid when**: marketing pages; single-message landings; mobile-first products
- **Signals this is the right choice**: navigation or filters must remain visible while content scrolls
- **Core composition rules**: persistent narrow rail (200–280px), dominant content stage (≥70% of width), clear alignment contract between rail and stage, one fixed visual boundary
- **Allowed grid breaks**: hero media can cross the rail boundary once at top of stage
- **Common failure mode**: rail too wide → competes with stage; rail too sparse → wastes space
- **Mobile collapse**: rail becomes top meta-band, drawer, or collapsible section; stage becomes full width

### Breakpoint translation rule

When collapsing for smaller viewports, do not just shrink the desktop grid — re-decide. The Layer 2 grid choice may change at smaller sizes.

- **Trigger**: collapse one breakpoint earlier than expected if any text column would fall below ~32 characters per line, or any card would fall below ~160px wide
- **Re-decide rule**: if collapsing leaves only one column wide enough to use, the grid is no longer the original choice — switch grid (e.g., a desktop Bento collapsed to one cell wide is now Manuscript; treat it as Manuscript)
- **Hierarchy preservation**: always preserve the Layer 1 dominant element first; reorder secondary content to match the original scan order

### Common combinations

- **Column Grid + Baseline** → magazine and journalism standard
- **Manuscript + Baseline** → long-form reading at typographic excellence
- **Hierarchical + Bento** → marketing landing with one hero and supporting feature grid below
- **Asymmetric Split + Modular** → hero followed by product grid

---

## Layer 3 — Elements (executable rules)

Once the grid is chosen, every element-level decision below should be traceable to a rule. If a choice does not match a rule here, name the deviation explicitly.

### Spacing (the step-jump rule)

Group spacing by relationship strength. Use scale steps from `design-tokens.md` — pick by step index, not raw pixel value.

- **Tight (within one element)**: label-to-input, icon-to-text → `space-1` to `space-2`
- **Group internal (related items)**: card content, list items → `space-2` to `space-3`
- **Cross-group (different sections)**: between sections of a page → `space-5` to `space-7`
- **Cross-zone (between major regions)**: hero → next section → `space-8` and up

The single most important rule: **cross-group spacing must be at least 3 scale steps higher than group-internal**. Adjacent step values (e.g., 16px next to 24px) read as one continuous group; the eye needs the step gap to perceive separation. If you find yourself at adjacent steps for items meant to be separate groups, jump further up the scale.

### Alignment defaults

| Content type | Default alignment | Why |
|--------------|-------------------|-----|
| Body text | Left (LTR) / Right (RTL) | Stable starting edge for scanning |
| Single-line headings | Left or center | Center only if visually balanced and short |
| Numbers in tables | Right | Compare digit places vertically |
| UI labels | Left | Predictable scan position |
| Hero display text | Left, or offset to a chosen grid line | Center only with Centered Monument grid; never use ad-hoc "asymmetric" without naming the grid reference |

Center-aligned multi-line body text is almost always wrong. The only exceptions: short hero copy (≤2 lines) and intentionally symmetric brand layouts.

### Typography hierarchy

Use ≤6 distinct sizes per page. Pick a modular scale from `design-tokens.md` based on chosen grid:

- Tight scales (1.125, 1.25) → dense layouts, dashboards, editorial multi-column
- Open scales (1.333, 1.414) → marketing, brand, hierarchical grids
- Dramatic scales (1.5, 1.618) → centered monument, broken editorial, hero-led landings

Combine size hierarchy with **opacity hierarchy**: primary 100% → secondary 70% → tertiary 45%. Three opacity tiers buy you three more hierarchy levels without inventing new sizes.

### Decoration filter

Every visual element must answer "yes" to at least one:
- Does it carry information?
- Does it guide the eye toward the focal point?
- Does it establish hierarchy?
- Does it carry brand identity?

If the answer to all four is no, delete it. "Looks nice" is not a function.

---

## Failure modes across all grids

- **Grid present but ignored**: elements placed near grid lines but not on them; reads as sloppy
- **Multiple competing grids**: two grid systems overlaid without one clearly dominant
- **Hierarchy by default**: every element gets equal weight because no decision was made
- **Mobile-as-afterthought**: desktop grid forced into mobile without re-deciding the layer-2 choice
- **Decoration without function**: ornaments added because the layout feels empty (the fix is more space, not more elements)

---

## Output requirement

When delivering a layout, restate at the top of the response:
- Layer 1 answers (intent / success criteria / density)
- Layer 2 grid choice and why it matches Layer 1
- Layer 3 deviations from defaults, if any, with reasoning

This makes the design auditable. The user can challenge any layer without re-litigating the others.
