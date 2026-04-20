# Japanese Editorial Flat

Inspired by a cross-analysis of three Japanese flat-design references: `awahi-magazine.jp`
(soft pastel editorial with rounded pill tags and mixed-column layout),
`beamscreative.jp` (disciplined modular grid on cream-white with black hairlines),
and `tokyu-recruit.jp` (bold flat color-block heroes with flat people illustrations).
The common DNA is "flat-design with editorial rhythm": no shadows, no gradients, generous
negative space, category pills, flat color blocks as section frames, and mixed CJK + Latin
typographic pairing. Tuned for warm, hand-crafted lifestyle brands — cafés, magazines,
boutique retail — where the reader should feel invited, not marketed to.

## When to use
- Lifestyle / café / boutique / editorial brand landings where warmth and calm matter more than density
- Content that benefits from categorization pills, editorial photography, and short prose blocks
- Bilingual (CJK + Latin) layouts where the Latin acts as accent/meta around CJK headlines
- NOT for: dense dashboards, finance/B2B SaaS, hard-sell conversion funnels, maximalist / brutalist briefs, dark-mode-first products

## Grid pairing
- Primary grid: Column Grid (12-col desktop, 6-col tablet) + Baseline overlay for vertical rhythm
- Combinations: Column Grid + Baseline for the editorial sections; Bento break for a feature/menu module; Asymmetric Split for the hero (55/45 with flat color block on one side)

## Color tokens
- --color-bg: #F4EDE2   (warm cream — the "paper" the page sits on)
- --color-surface: #FFFFFF  (card + content blocks)
- --color-text-primary: #1C1713   (warm near-black, never pure #000)
- --color-text-secondary: rgba(28,23,19,0.68)
- --color-text-tertiary: rgba(28,23,19,0.45)
- --color-accent: #B8432B   (terracotta — the dominant flat color block)
- --color-accent-soft: #BFD6C7   (sage mint — secondary flat block, echoes awahi)
- --color-accent-blush: #F1CFC4   (blush pink — tertiary flat block)
- --color-accent-mustard: #D9A441   (warm ochre — rare 4th accent for tags/pills only)
- --color-border: #E2D6C2   (hairline warm neutral, 1px)
- --color-focus: #B8432B

## Typography
- Display font (Latin): Instrument Serif — regular + italic. Google Fonts. Italic used as editorial accent next to CJK.
- Display font (CJK): Noto Serif TC — weights 700/900. Google Fonts. Used for bold editorial headlines in Traditional Chinese.
- Body font (Latin): DM Sans — weights 400/500/600. Google Fonts.
- Body font (CJK): Noto Sans TC — weights 400/500/700. Google Fonts.
- Import method: Google Fonts CDN (single `<link>` with all four families)
- Fallback stack: `"Instrument Serif", "Noto Serif TC", "Songti TC", "PingFang TC", serif` for display; `"DM Sans", "Noto Sans TC", "PingFang TC", -apple-system, sans-serif` for body
- Type scale ratio: 1.333 (perfect fourth — open enough for editorial hierarchy, tight enough for discipline)
- Min body size: 16px; ALL-CAPS meta labels use 11px at 0.18em tracking
- Special: Latin display (Instrument Serif italic) gets tight tracking -0.02em; CJK display (Noto Serif TC 900) gets loose tracking 0.04em for breath; numbers set in DM Sans tabular

## Spacing rhythm
- Base scale: 4px base, with step progression 4 / 8 / 12 / 16 / 24 / 32 / 48 / 72 / 112 / 160
- Notable rhythm: sections separated by step-8 (72px) mobile, step-10 (160px) desktop; inside a card use step-3 to step-5; cross-group jumps never adjacent-step (follows layout-judgment step-jump rule)

## Visual signature
- **Flat color blocks as section frames** — full-bleed terracotta / sage / blush rectangles that hold a photo + headline, zero shadow, zero gradient (from awahi + tokyu)
- **Fully-rounded pill category tags** (border-radius: 999px, 1px border, 6–10px vertical padding, small caps Latin label + CJK) repeated as the dominant rhyming motif (from awahi)
- **Hairline 1px warm borders** separating editorial blocks, plus dotted horizontal rules between list items (from beams)
- **Vertical CJK micro-labels** (writing-mode: vertical-rl) in section corners as decorative meta — one per major section, never more
- **Mixed script typographic pairings** — large CJK serif headline with Instrument Serif italic English subline underneath, sizes contrasting sharply (e.g., 72px / 18px)
- **Numbered section markers** ("01 / 04" in tabular DM Sans) as a quiet navigation spine down the page

## Reference (for human review)
- /Users/dianyi/Downloads/awahi-magazine.jp_.png (pastel editorial, pill tags, mixed grid)
- /Users/dianyi/Downloads/beamscreative.jp_.png (modular grid discipline, hairline borders)
- /Users/dianyi/Downloads/www.tokyu-recruit.jp_.png (bold flat color-block hero)

## Avoid in this style
- No drop shadows of any kind (including soft or colored)
- No gradients — every fill is flat
- No border-radius between 4px and 20px (use either 0, 2px for inputs, or 999px pills — no middle ground)
- No generic sans display fonts (Inter, Roboto, Montserrat, Poppins) — Instrument Serif + Noto Serif TC is the signature
- No purple / neon / cold-blue accents — palette is warm-earth only
- No center-aligned multi-line body text
- No pure black (#000) or pure white on cream background — breaks the warm paper feel
- No decorative swooshes, sparkles, or "AI-gradient-blob" backgrounds
