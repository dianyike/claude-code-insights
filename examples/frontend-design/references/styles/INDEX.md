# Style Library Index

Saved styles the user has used and approved. Each entry is one line so this index can be scanned cheaply on every invocation.

## How to use this index

When the user requests a style by name (e.g., "use editorial-minimal", "design with the flat-bold style"), look for it below. If it exists, load the matching file at `references/styles/<slug>.md` before designing. If it does not exist, ask the user whether to design fresh or recall a similar saved style.

## How to add a style

After completing a design the user explicitly approves, ask: "Should I save this as a reusable style?" If yes:

1. Pick a short slug (kebab-case, ≤3 words): `editorial-minimal`, `flat-bold`, `neo-brutalist`
2. Create `references/styles/<slug>.md` using the template below
3. Add a one-line entry to this index in alphabetical order

## Index

<!-- Format: `- <slug> — one-line description (grid pairing, dominant feel) -->
<!-- Example: `- editorial-minimal — magazine feel, generous white space, serif display, single accent color -->

- japanese-editorial-flat — flat-design Japanese editorial on warm cream, terracotta + sage + blush color blocks, pill tags, Instrument Serif × Noto Serif TC bilingual display
- kohaku-editorial — warm Japanese-editorial modular grid, cream + copper palette, Fraunces × Shippori Mincho bilingual display, numbered craft sections

---

## Style file template

When creating a new style at `references/styles/<slug>.md`, use this structure. Every field must be filled — vague style files create vague designs.

```markdown
# <Style Name>

## When to use
- <Concrete trigger conditions: what kind of project, audience, tone>
- <When NOT to use this style>

## Grid pairing
- Primary grid: <one of the 10 grids from layout-judgment.md>
- Combinations: <e.g., Editorial Multi-Column + Baseline>

## Color tokens
- --color-bg: <hex>
- --color-surface: <hex>
- --color-text-primary: <hex>
- --color-text-secondary: <hex or opacity>
- --color-text-tertiary: <hex or opacity>
- --color-accent: <hex>  (one only)
- --color-border: <hex>
- --color-focus: <hex>

## Typography
- Display font: <name + source + license, e.g., Söhne via Klim Type Foundry — paid commercial license>
- Body font: <name + source + license>
- Import method: <self-hosted woff2 / Google Fonts CDN / Adobe Fonts kit / variable font URL>
- Fallback stack: <system-safe fallback for both fonts, e.g., "Söhne", -apple-system, BlinkMacSystemFont, sans-serif>
- Type scale ratio: <e.g., 1.333>
- Min body size: <e.g., 16px>
- Special: <e.g., display uses tight tracking -0.03em>

## Spacing rhythm
- Base scale: <4-base / 8-base / Fibonacci>
- Notable rhythm: <e.g., always 8 / 24 / 64 / 128 sequence>

## Visual signature
- <The 1-3 motifs that make this style recognizable>
- <e.g., "thin 1px borders, no shadows, single off-white background, serif display + sans body, one warm accent color">

## Reference (optional — for human review, not required for execution)
- <URL or file path to the case that inspired this style>
- <Optional: screenshot path>

## Avoid in this style
- <Specific patterns that would break the style — e.g., "no gradients, no rounded corners ≥4px, no multiple accent colors">
```
