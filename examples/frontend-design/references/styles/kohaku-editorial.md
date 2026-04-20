# Kohaku Editorial

Warm Japanese-editorial aesthetic built around a 12-column modular grid, cream paper ground, copper/espresso palette, and bilingual display typography. Derived from e-729.com, luminaireauthentik.com, momentia.jp, fujiwara-i.com.

## When to use
- Craft / artisan brands (coffee, ceramics, boutique apparel, small-batch products)
- Editorial landing pages with narrative sections (process, philosophy, journal)
- Bilingual (JP/EN or CJK/EN) content where typography pairing carries atmosphere
- Brands that want warmth, slowness, and quiet authority over tech-sharpness
- NOT for: SaaS dashboards, data-dense UIs, playful/toy brands, high-contrast editorial (brutalist, neon), flat B2B marketing

## Grid pairing
- Primary grid: Modular Grid (12-col) with staggered row offsets
- Combinations: Modular + Hierarchical (mega wordmarks), Modular + Asymmetric Split (hero + inverted Visit section)
- Signature moves: numbered 01–05 section labels, alternating card `padding-top` for rhythm, negative-margin image overlaps in hero, 8-cell asymmetric masonry for gallery sections

## Color tokens
- --color-bg: #EFE6D6              (cream paper)
- --color-surface: #F7F1E5         (lighter paper, used for raised sections)
- --color-surface-alt: #E4D8C1     (placeholder/fallback for image blocks)
- --color-text-primary: #1E1710    (espresso, body + headlines on light bg)
- --color-text-secondary: #4A3423  (wood, secondary body)
- --color-text-tertiary: #6A5B47   (taupe, small labels — AA-compliant at 5:1)
- --color-text-soft: #9A8874       (decorative only, use on dark bg or ≥18px)
- --color-accent: #B06B3D          (copper, single accent)
- --color-accent-ink: #8C4E25      (copper-ink, for accent text on cream — 5.9:1)
- --color-accent-lt: #D89868       (copper-lt, for accent text on espresso bg)
- --color-inverse-bg: #1E1710      (espresso, for inverted sections)
- --color-border: #CFBFA3          (warm line, 1px dividers)
- --color-focus: #B06B3D           (copper, 2px outline, 4px offset)

## Typography
- Display font: Fraunces — Google Fonts, OFL (variable: opsz 9–144, wght 300–900, italic, SOFT axis)
- JP display font: Shippori Mincho — Google Fonts, OFL (weights 400/500/600/700)
- Body font: Archivo — Google Fonts, OFL (weights 300/400/500/600)
- Mono/meta font: JetBrains Mono — Google Fonts, OFL (weights 300/400/500)
- Import method: Google Fonts CDN (single `<link>` with `&family=` combined)
- Fallback stack: `'Fraunces', 'Shippori Mincho', serif` for display; `'Archivo', 'Shippori Mincho', sans-serif` for body
- Type scale ratio: ~1.333 (major third), with display exaggerated via `clamp(64px, 10.5vw, 172px)` for hero
- Min body size: 15px body, 13.5px dense card copy, 10px mono meta (uppercase, letter-spacing 0.24em+)
- Special:
  - Display uses `font-variation-settings: 'opsz' 144, 'SOFT' 40` (light) and `'SOFT' 100` for italic accents
  - Italic + copper-ink pairing marks emphasis words inside display headlines
  - JP subtitles always at ~18–24% the size of their EN title, with letter-spacing 0.22em+
  - Meta labels: JetBrains Mono uppercase 10–11px, letter-spacing 0.22em–0.28em

## Spacing rhythm
- Base scale: 4-base, emphasizing 12 / 24 / 36 / 56 / 80 / 120
- Section padding: top 100–130px, bottom 100–120px
- Grid column-gap: 24px; row-gap: 24–56px depending on density
- Notable rhythm: alternating card `padding-top` (0 / 48–64px) creates staggered editorial feel
- Image aspect ratios: 3/4 (portrait), 4/5 (standard), 5/3 (landscape band), 4/3 (hero media)

## Visual signature
- Numbered section labels: `§ 01 / Process` with a small rotated-square `::before` marker in copper
- Bilingual title stack: English Fraunces + a Japanese Shippori Mincho subtitle underneath
- Numbered craft cards (01–05) with tabular-nums and `sm` sub-label in mono
- Staggered card heights in shop/journal grids (every-other offset)
- Negative-margin image overlaps in hero for editorial depth
- Rotating circular badge motif (`Since · 2017 · Kyoto · Kohaku ·` on an `animation: spin`)
- Infinite horizontal marquee band with JP/EN/dot rhythm between sections
- Mega footer wordmark at clamp(80px, 18vw, 280px) with italic accent + JP inline
- Paper grain SVG overlay (5% opacity, mix-blend-mode: multiply)

## Reference
- e-729.com (numbered service grid, warm photo + serif pairing)
- luminaireauthentik.com (Shop by Mood grid, cream palette, copper accents)
- momentia.jp (JP product grid, time-of-day categorization)
- fujiwara-i.com (asymmetric masonry, JP editorial restraint)
- Implementation: `demos/kohaku-coffee/index.html`

## Avoid in this style
- No pure white (#FFFFFF) — always warm cream
- No cool blues, teals, or greys in accent role (copper-only)
- No drop shadows; use 1px warm borders and subtle overlays instead
- No border-radius > 6px on images/cards; pills (999px) only on chip-style CTAs
- No more than one accent color at a time (copper OR olive, never both as accents)
- No sans-serif display — headlines must be Fraunces or Shippori Mincho
- No dense bullet lists; prefer numbered craft cards or short editorial paragraphs
- No stock "AI gradient" backgrounds (purple→pink, blue→teal)
- No Inter, Roboto, Poppins, Space Grotesk
