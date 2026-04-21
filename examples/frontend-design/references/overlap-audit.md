# Overlap Audit

Detect and judge unintended element occlusion in a finished design output. Triggered from the Editing Pass in `SKILL.md` when the design uses any overlap-prone technique.

This is a three-layer hybrid, in order: **DOM detection → visual classification → keyboard/focus reachability**. Do not skip to screenshots — pixel inspection alone misses breakpoint-specific issues and burns tokens on every view.

## When to run

Run this audit when ANY of the following is true in the produced code:

- `position: absolute` / `fixed` / `sticky` on content-bearing or decorative elements
- Negative `margin` that pulls elements over each other
- `transform: translate(...)` that shifts an element out of normal flow
- `mask-image`, `clip-path`, `mix-blend-mode`
- Explicit overlap described in the brief or chosen style (e.g. hero image bleeds, editorial overlaps)
- `z-index` values other than the default / framework token

When none of the above apply, skip the audit — normal flow layouts don't produce this class of bug.

## Layer 1 — DOM detection (Playwright MCP)

1. Serve the page:
   - Static HTML → run `python3 -m http.server` (or any static server) in the output folder.
   - Framework project (Next.js, Vite, Astro, etc.) → use the project's existing dev/preview server (`npm run dev`, `vite`, `next dev`). Do not start a second static server on top of built output unless the framework's dev server is unavailable.
2. Use Playwright MCP to navigate to the page.
3. For each viewport in the matrix (see below), run the audit script and collect candidates.

**If Playwright MCP is not configured** (check `.mcp.json` for a `playwright` entry): drop to manual mode — open the page in a real browser at each viewport in the matrix, take screenshots by hand, and apply the Layer 2 rubric directly. Flag the report as "manual-mode, Layer 1 skipped" so the coverage gap is visible.

**Viewport matrix** (run all three; do not assume one width generalizes):

- Desktop: `1440 × 900`
- Tablet: `834 × 1112`
- Mobile: `390 × 844`

For long pages, also sample one scrolled position: halfway down the document.

**How to run the script:**

1. Read `.claude/skills/frontend-design/scripts/overlap-audit.js`.
2. Pass the full file contents as the `function` argument to Playwright MCP's `browser_evaluate` tool.
3. The script returns `{ viewport, summary, candidates }`. Candidates are sorted by `coverageRatio` descending.

**Interactive states:** after the static sweep, for each primary interactive element (nav links, CTAs, form inputs), hover or focus it via Playwright and re-run the script. Reveal-on-hover overlays are the most common state-dependent occlusion source.

## Layer 2 — Visual classification (screenshot + rubric)

For each candidate flagged by Layer 1, take a tight screenshot of the candidate's rect (`rect.x/y/w/h` from the report, padded ~40px) and classify using the rubric below.

### Rubric: intentional mask vs. accidental cover-up

Evaluate in strict order. Rule 1 is a hard floor — Rule 2 only applies once Rule 1 is cleared.

**Rule 1 — Legibility floor (applies to all visible content-bearing elements):**

If any portion of the visible text or visual label of a content-bearing element is occluded such that it cannot be cleanly read, it is a bug. No exceptions for:

- "Still recognizable from the visible fragment"
- "aria-label provides the same information"
- "Consistent across breakpoints"
- "Matches a design motif in the brief"

Content-bearing covers: CTAs, prices, dates, form labels, nav text, status indicators, headings, body copy, metadata that conveys state. An `<img>` inside `<button>Submit</button>` that partially covers "Submit" is a bug even if the image is a designed element. **Legibility is not negotiable.**

**Rule 2 — Intent signals (apply only to purely decorative or fully-redundant elements):**

Rule 2 engages only when the occluded element is:

- **Decorative** — a background shape, ornamental glyph, pure SVG illustration, or pattern whose occlusion loses no information; OR
- **Fully redundant** — the same information is clearly conveyed by another *visible* element on the same screen. A hidden aria-label does NOT make a visible label redundant.

For a decorative-or-redundant candidate, the overlap is intentional when **all** of the following hold:

- Consistent across all tested breakpoints (not just one).
- Documented in the brief, style file, or a named design motif (e.g. "negative-margin image overlaps in hero" in `kohaku-editorial.md`).
- The occluder has a clear design role (not a generic wrapper or accidental layout artifact).

If any of these is missing, treat as bug.

**Clarification: visual vs. accessibility bugs are separate.** Rule 1 is about pixels. Layer 3 (below) is about focus ring visibility and click-path interception. An element can pass Rule 1 (text legible) and still fail Layer 3 (focus ring hidden). Both must pass.

## Layer 3 — Focus-ring and click-path reachability

Scope note: Layer 3 is **occlusion-specific** — it checks whether the overlap breaks focus visibility or click delivery on the flagged candidates. **Global tab order, `Esc` handling, `Enter`/`Space` activation for the whole surface, and modal focus return are covered by the keyboard walk-through (SKILL.md Editing Pass Step 5), not here.** Do not duplicate that work; this layer only inspects the elements Layer 1 flagged.

For every element flagged in Layer 1 that is interactive (`a`, `button`, `input`, `[role="button"]`, `[role="link"]`, form controls):

1. Tab to the element via Playwright.
2. Confirm the focus indicator renders **above** the occluder (not under it).
3. Confirm a click at the element's center reaches the element (the occluder does not intercept pointer events).

If focus lands on the element but the ring is hidden behind the occluder, treat as a bug even if Rule 1 passed — focus visibility is a baseline, not an aesthetic choice.

## Reporting

For each confirmed bug, record:

- Viewport where it reproduces (all / desktop-only / etc.)
- Target selector + short text
- Top occluder selector
- Coverage ratio
- Classification reason (which bug signal triggered)

Fix the highest-coverage content-bearing bugs first. Re-run Layer 1 after fixes to confirm the candidate drops out.

## Limitations (what this audit doesn't catch)

- **True pixel-level rendering bugs** (e.g. font antialiasing, sub-pixel clipping) — outside DOM-sample scope.
- **Canvas / WebGL content** — `elementsFromPoint` returns the canvas as a single node; overlap inside the canvas is invisible to this audit.
- **Animated states** — the script samples one frame. If an overlay animates in/out, capture it mid-animation manually.
- **iframe content** — cross-origin frames are opaque to the script.

When the design relies on any of the above, fall back to manual screenshot review and note it in the report.
