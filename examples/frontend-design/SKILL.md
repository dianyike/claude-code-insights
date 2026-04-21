---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, or applications. Generates creative, polished code that avoids generic AI aesthetics.
hooks:
  PreToolUse:
    - matcher: Write|Edit
      command: bash "${CLAUDE_SKILL_DIR}/scripts/style.sh" check
---

This skill guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

The user provides frontend requirements: a component, page, application, or interface to build. They may include context about the purpose, audience, or technical constraints.

## Workflow

Design happens in three layers — Purpose → Structure → Elements. Walk them in order; never skip ahead. Each layer's output constrains the next.

1. **Purpose** — Before any visual choice, answer the Layer 1 triad explicitly in your response: reader intent, success criteria, information density. For any layout-led, page, hero, landing, or editorial task, use the discrete options defined in `references/layout-judgment.md` (Layer 1) — vague answers must trigger a clarifying question to the user. See also "Design Thinking" below.
2. **Structure** — Choose a grid before placing any element. For layout-led, editorial, brand-heavy, or Awwwards-quality typographic work, read `references/layout-judgment.md` for the grid catalog and selection criteria.
3. **Elements** — Apply typography, color, spacing. See "Frontend Aesthetics Guidelines" below; use `references/design-tokens.md` for spacing scales, type ramps, line-height, and other numerical decisions.
4. **Edit Pass** — See "The Editing Pass" at the end of this file.

**Reusable styles**: If the user references a saved style by name (e.g., "use editorial-minimal"), check `references/styles/INDEX.md` first and load the matching style file before designing. After completing a design the user explicitly approves, ask whether to save it as a reusable style — if yes, follow the template in `INDEX.md`. **When a saved style and the current brief conflict, the brief wins** unless the user explicitly says to preserve the style strictly.

**Reference images**: When the user provides reference images of a target style, run the procedure below in order. Do NOT reorder. Do NOT skip to design.

1. Cross-analyze all images together (single-image inferences are unreliable). Identify: grid type (match to one of the 10 in `references/layout-judgment.md`), color palette, typography characteristics, spacing rhythm, and 2-3 repeated visual motifs.
2. Run: `bash ${CLAUDE_SKILL_DIR}/scripts/style.sh new <slug>` — this creates a style-file skeleton at `references/styles/<slug>.md` with all fields set to `??`, and activates the style-extraction guard.
3. Edit the generated file: replace every `??` with the value from your analysis. Leave `??` only where you genuinely need user confirmation, and call it out explicitly.
4. Show the filled style to the user for approval or edits.
5. Add a one-line entry for the new style to `references/styles/INDEX.md` in alphabetical order. Do this while the guard is still active so INDEX hygiene isn't forgotten after the guard clears.
6. After user approves (and every `??` is resolved), run: `bash ${CLAUDE_SKILL_DIR}/scripts/style.sh done`.
7. Only now begin designing. The saved style is the brief constraint for the session.

**Enforcement**: This skill registers a PreToolUse hook (see frontmatter) that blocks Write/Edit on design-output files (HTML/CSS/JSX/TSX/Vue/Svelte under `demos/`, `test-output/`, `app/`, `pages/`, `src/`, `components/`, `public/`) while the guard is active. If a Write is blocked, return to step 3. Do not attempt to bypass the hook by deleting the marker file — the guard exists to protect the source of truth.

## Design Thinking

Before coding, understand the context and commit to a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. There are so many flavors to choose from. Use these for inspiration but design one that is true to the aesthetic direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?
- **Star Element**: Every design needs a visual protagonist — one element that commands attention. It must connect to the content's story or brand identity, not just look impressive in isolation. Everything else supports, frames, or contrasts with this star.

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work - the key is intentionality, not intensity.

Then implement working code (HTML/CSS/JS, React, Vue, etc.) that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Frontend Aesthetics Guidelines

Focus on:
- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics; unexpected, characterful font choices. Pair a distinctive display font with a refined body font. **Minimum readable sizes**: 16px (1rem) for body text (mixed-case reading copy); 14px (0.875rem) for captions and inline meta; **11px only for ALL-CAPS labels with tracking ≥ 0.15em** (editorial convention — wide tracking preserves legibility at smaller sizes). Never go below 11px for any text a user is expected to read. There is no maximum — titles can be as enormous as the design demands. Maintain a clear type hierarchy (typically 4–6 distinct sizes) rather than inventing arbitrary sizes for each element. The scale itself is a creative choice; the floor is not. Use **text opacity variations** (e.g., 100% → 70% → 45%) as a hierarchy tool alongside size — primary content at full opacity, secondary at reduced, tertiary nearly muted. This creates breathing room without needing more font sizes. Verify the resulting contrast against the actual background; never reduce opacity on essential reading copy, primary CTAs, or interactive labels.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Motion is opt-in. Default to static composition — well-executed layout and typography deliver more impact than motion. Only add motion when (a) the user asks for it, (b) interactive feedback would be unclear without it (focus, hover, error, loading states), or (c) the chosen aesthetic explicitly requires it. When motion is used: prioritize CSS-only for HTML, Motion library for React; one well-orchestrated page load beats scattered micro-interactions.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density. **Never let decorative or structural elements unintentionally obscure content-carrying elements** (dates, CTAs, metadata). Overlap is a deliberate compositional tool — if an element carries information, it must remain legible. Before finalizing layout, verify every text element is readable against its actual stacking context, not just in theory.
- **Visual Rhyming**: Repeat small visual motifs — a border radius, a gradient angle, a decorative shape, a line weight — across unrelated elements to create subconscious coherence. The repetition should feel discovered, not forced. Pick 2-3 motifs and echo them throughout; this is what separates "collection of nice elements" from "designed system."
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Add contextual effects and textures that match the overall aesthetic. Apply creative forms like gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, and grain overlays.

NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. No design should be the same. Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, for example) across generations.

**IMPORTANT**: Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Elegance comes from executing the vision well.

## Non-Negotiable Baselines

Creative boldness does not excuse broken fundamentals. These are not aesthetic choices — they are baseline requirements that apply regardless of visual direction.

### Accessibility

- Contrast ratio ≥ 4.5:1 for body text, ≥ 3:1 for large text (≥ 24px). Verify against your actual background — gradients and textures don't get a free pass. Check contrast during the Elements phase, not at the end.
- Touch targets ≥ 44×44px on interactive elements.
- Visible focus indicators on every focusable element. `outline: none` without a replacement is never acceptable.
- Never convey meaning through color alone. Semantic HTML: `<button>` for actions (anything that changes state, submits, opens a dialog), `<a>` for navigation (anything that changes the URL or loads a new document). Link text must make sense out of context — never bare "click here" or "read more". Word count and verb-leading are useful heuristics for CTA copy, not the semantic rule.
- For `prefers-reduced-motion`, icon buttons, skip links, and modal focus management, apply the patterns in `references/accessibility-core.md`.

### Interactive States

Every interactive element must have at minimum: **Default → Hover → Focus**, plus **Disabled** when the control can be disabled. Inputs add **Error** (with visible message). Empty states and success confirmations must exist — never a blank void or silent completion. A bold visual design with broken interactive feedback feels unfinished.

**Disabled is a last resort.** Prefer keeping the control enabled and showing inline validation that explains what's wrong — a disabled button with no explanation is a dead end for the user. Only disable when the action is genuinely unavailable (waiting on upstream data, prerequisites not met). When you do disable, pick the right tool: native `disabled` removes the control from keyboard and assistive tech entirely (fine for form fields gated by a checkbox), while `aria-disabled="true"` keeps focus and announcement but requires you to guard activation in your handler. Use `aria-disabled` when the user needs to *hear why* the control is unavailable (e.g. a submit button waiting on validation); use native `disabled` when the inert state is self-explanatory. Never disable silently.

## The Editing Pass

After the first complete implementation, before delivering:

1. Find the **weakest** element — the one that feels safe, generic, or forgettable. Ask: is this bold enough? Push it further or cut it entirely.
2. Check that your focal point actually dominates. Squint at the screen — what do you see first? If the answer isn't your intended focal point, fix the hierarchy.
3. Verify that boldness didn't break the baselines above. Focus states, touch targets, and link text that stands on its own — confirm them last, fix without compromising the vision. Contrast should already have been checked during Elements; re-verify only if colors shifted during this pass.
4. **Overlap audit (conditional).** If the design uses `position: absolute/fixed/sticky`, negative margins, `transform` translation, `mask-image`/`clip-path`/`mix-blend-mode`, explicit overlap in the brief, or `z-index` beyond default/framework tokens — run the procedure in `references/overlap-audit.md`. This is a DOM-based Playwright sweep + screenshot classification + focus-reachability check, not a mental simulation. Mental-only overlap review has shipped bugs before; trust the automated pass. Skip only when the layout is purely normal flow.
5. **Keyboard walk-through.** Tab through the entire surface with the mouse unplugged (or ignored) and verify: every interactive element is reachable in a sensible order, focus indicators are visible against their actual background, `Esc` closes modals and menus, `Enter` / `Space` activate the focused control, and focus returns to the trigger when a modal or popover closes. If step 4 ran, it already covered focus-ring visibility and click-path interception for the flagged elements — do not re-check those; this step handles the global concerns (tab order, modal return, `Esc`).

Remember: Claude is capable of extraordinary creative work. Don't hold back, show what can truly be created when thinking outside the box and committing fully to a distinctive vision.
