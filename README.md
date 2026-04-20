# Claude Code Insights

English | [繁體中文](README.zh-TW.md)

**The most comprehensive advanced Claude Code guide in the Chinese-speaking community** — covering CLAUDE.md architecture, Skills authoring, Subagent orchestration, with ready-to-use practical examples.

> Maintained by **dianyike / 典億創研工作室**. Freelance engineer specializing in web development, web scraping automation, and API integration. This repo is a distillation of my real-world experience using Claude Code in client projects.
>
> <!-- TODO: Replace with your actual links -->
> [Website](https://dianyistudio.com/) · [Threads](https://www.threads.com/@dianyike1013) · [Contact](mailto:service@dianyistudio.com)

## Who Is This For

| You are... | Start here | What you'll get |
|------------|-----------|-----------------|
| **New to Claude Code** | [CLAUDE.md Guide](claude-md-best-practices.md) | Understand the three-layer architecture, Hooks, and how to avoid common anti-patterns |
| **Experienced, looking to level up** | [Skills Guide](skills-best-practices.md) → [Subagent Guide](subagent-best-practices.md) | Hub-and-Spoke architecture, decision matrices, black-box problem solutions |
| **Freelancer / Solo developer** | [Practical Examples](#practical-examples): grill-me → write-prd → prd-to-plan → tdd | A complete workflow from design interrogation to TDD implementation |

## Contents

| File | Description | Audience |
|------|-------------|----------|
| [claude-md-best-practices.md](claude-md-best-practices.md) | CLAUDE.md Best Practices — why not to use `/init`, the three-layer architecture model, Hooks over directives, anti-patterns | Beginners |
| [skills-best-practices.md](skills-best-practices.md) | Skills Best Practices — file format, loading mechanics, content writing principles, advanced patterns, design templates | Advanced |
| [subagent-best-practices.md](subagent-best-practices.md) | Subagent Best Practices — the black-box problem and solutions, result persistence, tool scoping strategies, architectural patterns | Advanced |

The three guides cross-reference each other. Recommended reading order: CLAUDE.md → Skills → Subagent.

## Practical Examples

### Subagent Examples

| Example | Description | Difficulty |
|---------|-------------|------------|
| [examples/security-reviewer](examples/security-reviewer) | Dual-verification security audit — read-only `/security:review` (Semgrep + Codex cross-validation, confidence scoring) + opt-in `/security:fix` (convergence-hardened Fix-Verify Loop with falsifiable predictions, tiered rollback, hypothesis ledger). Strict review/fix boundary: review is always read-only; fix requires explicit user opt-in and runs in main conversation. Implements [Harness Engineering](https://openai.com/index/harness-engineering/) methodology | Advanced |

### Hook Examples

| Example | Description | Difficulty |
|---------|-------------|------------|
| [examples/npm-supply-chain-defense](examples/npm-supply-chain-defense) | npm supply chain three-layer defense — `.npmrc` script blocking + PreToolUse Hook checks (registry, OSV.dev, version resolution, CLI syntax validation) + Semgrep supply chain scanning. Includes 42 regression tests | Advanced |

### Rules Examples

| Example | Description | Difficulty |
|---------|-------------|------------|
| [examples/rules](examples/rules) | Production-tested `.claude/rules/` starter kit — 6 rule files + localization template. Features a **pragmatism layer** (risk-tier meta-rule that scopes enforcement), violation signals for self-detection, and a "Why" line on every rule so Claude follows intent, not just the letter. Ready to copy into any project. | Beginner |

### Skills Examples

The following Skills are adapted from [mattpocock/skills](https://github.com/mattpocock/skills), reworked with templates extracted to `templates/`, reference materials moved to `reference/`, and Gotchas sections added.

| Example | Description | Use Case |
|---------|-------------|----------|
| [examples/grill-me](examples/grill-me) | Design Interrogation — traverses every branch of a decision tree, resolving design decision dependencies one by one | Pre-coding design stress test |
| [examples/write-prd](examples/write-prd) | Write PRD — turns design decisions or rough ideas into a structured requirements document, bridging grill-me and prd-to-plan | Requirements authoring and structuring |
| [examples/tdd](examples/tdd) | TDD Workflow — red-green-refactor vertical slices with test examples, mock guidelines, and deep module design reference | Feature development and bug fixes |
| [examples/prd-to-plan](examples/prd-to-plan) | PRD to Implementation Plan — breaks requirements into tracer bullet vertical slices, outputs to `./plans/`, with optional Codex review for high-risk plans | Requirements decomposition and phase planning |
| [examples/write-a-skill](examples/write-a-skill) | Skill Builder Meta-Skill — content type decisions, invocation control, security configuration, Gotchas iteration loop. Includes eval workflow reference | Creating new Skills |
| [examples/skill-eval-toolkit](examples/skill-eval-toolkit) | Skill Eval Toolkit — eval-driven testing, quantitative benchmarking, blind A/B comparison, description trigger optimization, and SKILL.md body autopilot keep/revert loop | Validating and optimizing existing Skills |
| [examples/frontend-design](examples/frontend-design) | Frontend Design — layout-led skill for distinctive UI that avoids generic AI aesthetics. 3-layer decision flow (Purpose → Structure → Elements), 10-grid catalog, design-token scales, and a reusable **style library** populated from reference images. Enforces style-file-before-design with a bundled script + PreToolUse hook that blocks design-output writes until the style is complete. See the [cafe-kantsu demo](examples/frontend-design/test-output/index.html) under `test-output/` | Building distinctive frontend interfaces |

**Solo Development Workflow**: `/grill-me` (interrogate the design) → `/write-prd` (write the PRD) → `/prd-to-plan` (break into phases, optionally review with Codex) → `/tdd` (implement one by one)

**Skill Development Workflow**: `/write-a-skill` (author the skill) → `/skill-eval-toolkit` (evaluate and optimize)

#### write-prd — PRD Authoring Skill

Fills the gap between `/grill-me` and `/prd-to-plan` — turns design decisions or rough ideas into a structured PRD:

- One-question-per-turn structured interview (target user → success state → non-goals)
- Enforces P0/P1/P2 priority tiers, References citing decision records, `docs/prds/` output convention
- Stays at product / system-contract level — no implementation details leak (httpOnly cookies, SDK pinning, etc.)
- Delegated/Eval Mode — distinguishes draft artifacts from canonical PRD files
- Includes 4 functional eval cases + 12 trigger tests (validated through 2 iterations with skill-eval-toolkit, 90% pass rate)

```
You: "Write a PRD based on docs/decisions/login-redesign.md"
Claude: (loads write-prd, reads decision record, identifies gaps,
         produces PRD draft with user stories + traceability, asks to confirm)
```

#### write-a-skill — Skill Authoring Guide

Use when you want to **create a new skill from scratch**. Covers the full authoring lifecycle:

- Content type decision (Reference vs Task) and invocation control (`disable-model-invocation`, `context: fork`, etc.)
- Frontmatter schema, progressive disclosure (metadata → body → bundled resources)
- Description writing — trigger-oriented keywords, not feature summaries
- Security checklist and review process
- Gotchas iteration loop — the feedback mechanism that makes skills more accurate over time

```
You: "I want to create a skill that generates API documentation from OpenAPI specs"
Claude: (loads write-a-skill, interviews you, drafts SKILL.md, runs smoke tests)
```

#### skill-eval-toolkit — Eval-Driven Testing and Optimization

Use when you have **an existing skill and want to measure or improve it**. Provides a structured eval loop with 4 specialized subagents:

| Subagent | Role |
|----------|------|
| **grader** | Evaluate assertions against outputs, critique eval quality |
| **comparator** | Blind A/B comparison — scores two outputs without knowing which is which |
| **comparison-analyzer** | Post-hoc analysis — unblinds results, identifies why the winner won |
| **benchmark-analyzer** | Surface patterns in benchmark data that aggregate stats hide |

The workflow: create test prompts → run with-skill and baseline in parallel → grade → aggregate benchmarks → interactive viewer for human review → improve → repeat. Also includes automated description trigger optimization (train/test split, iterative improvement) and an eval-driven body autopilot loop for small `SKILL.md` mutations.

```
You: "Evaluate my json-diff skill and tell me if it actually adds value"
Claude: (loads skill-eval-toolkit, creates test cases, spawns parallel runs,
         grades outputs, launches viewer, shows you the results)
```

> **When to use which**: If the question is "how should I structure this skill?" → `write-a-skill`. If the question is "is this skill actually working well?" → `skill-eval-toolkit`. Most skills start with the former and graduate to the latter when you need quantitative rigor.

#### frontend-design — Layout-Led Design with Enforced Style Library

Use when building distinctive, production-grade frontend interfaces that need **layout discipline and reusable style memory**, not just one-off visual flair. Combines three architectural patterns:

**Three-layer decision framework (decision-shell)** — SKILL.md stays lean; references load on demand:

- **Layer 1 Purpose** — reader intent / success criteria / information density (discrete options, not vague prose)
- **Layer 2 Structure** — grid selection from a 10-grid catalog in [`references/layout-judgment.md`](examples/frontend-design/references/layout-judgment.md): Manuscript, Column, Modular, Hierarchical, Baseline, Bento, Asymmetric Split, Centered Monument, Broken/Off-Grid Editorial, Rail + Stage. Each entry includes use-when / avoid-when / core rules / mobile-collapse behaviour
- **Layer 3 Elements** — spacing / type / line-height scales from [`references/design-tokens.md`](examples/frontend-design/references/design-tokens.md): 4-base / 8-base / Fibonacci spacing, 1.125–1.778 type ratios, with selection guidance per grid

**Reusable style library** — reference images become persistent assets:

- User drops N reference images → Claude cross-analyzes for grid / palette / typography / motifs
- Produces a style file at `references/styles/<slug>.md` with 11 structured fields (when-to-use, grid pairing, color tokens, typography + import method + fallback stack, spacing rhythm, visual signature, avoid list, etc.)
- Future sessions: `"use <slug>"` loads the style as a brief constraint — no re-explanation needed

**Script + PreToolUse hook enforcement** — prose instructions get interpreted loosely; this layer turns "should" into "cannot":

- [`scripts/style.sh new <slug>`](examples/frontend-design/scripts/style.sh) creates a style skeleton with `??` placeholders and activates a marker file
- A PreToolUse hook (registered in SKILL.md frontmatter) intercepts Write/Edit on design-output files (HTML/CSS/JSX/TSX/Vue/Svelte under `demos/`, `app/`, `pages/`, `src/`, `components/`, `public/`) and blocks while any `??` remains
- `scripts/style.sh done` validates completeness before clearing the marker

```
You: "Design a café landing page" + [3 reference images]
Claude: (runs style.sh new → cross-image analysis → fills style file →
         shows for approval → updates INDEX → style.sh done → writes HTML)
```

This enforcement layer addresses a subtle skill failure mode: when a skill says "first do X, then do Y", AI often treats the order as advisory and reorders. A bash hook makes the ordering non-negotiable, raising procedure compliance measurably across real runs.

See [examples/frontend-design/test-output/index.html](examples/frontend-design/test-output/index.html) for a complete page (the **cafe-kantsu** demo) built using the `japanese-editorial-flat` style extracted from three Japanese flat-design references.

> **Gotchas Are the Soul of a Skill**: The strongest signal in any Skill isn't the tutorial — it's the pitfalls the team has hit. Every time a Skill execution encounters an unexpected failure, write the failure pattern back into Gotchas — this feedback loop makes the Skill more accurate over time. See [skills-best-practices.md § 4.3](skills-best-practices.md#43-building-the-gotchas-section) for details.

> **Note**: These examples can be copied directly into `.claude/skills/` for use. We recommend reading both guides first to understand the design rationale and adapt them to your needs.

## Quick Overview

### CLAUDE.md Guide Highlights

- Why you shouldn't use `/init` for auto-generation (with supporting research data)
- The right approach from scratch: start with nothing, add rules only when problems arise
- Three-layer architecture model: Enforcement Layer / High-Frequency Recall Layer / On-Demand Reference Layer
- Using Hooks instead of CLAUDE.md directives (determinism > suggestions)
- Five major anti-patterns and maintenance practices

### Skills Guide Highlights

- What a Skill is and how it differs from CLAUDE.md
- Complete Frontmatter field reference
- Auto-trigger vs manual invocation control methods
- Skill vs Subagent vs CLAUDE.md decision matrix
- Security guidelines and iteration methodology

### Subagent Guide Highlights

- When to use a Subagent (Anthropic's official stance: most scenarios don't need one)
- Four solutions for black-box and one-shot problems
- Research-type and review-type Agent design templates
- Hub-and-Spoke architectural pattern
- The Early Victory Problem and mitigation strategies

## About / Freelance Services

<!-- TODO: Replace with your actual links and content -->

I'm **dianyike**, running **典億創研工作室** (Dianyi Studio) as a freelance engineer.

| Service | Description |
|---------|-------------|
| Web Design & Development | Responsive websites, landing pages, admin dashboards |
| Web Scraping Automation | Data extraction, scheduled jobs, anti-bot strategies |
| API Integration | Third-party API connections, data sync, webhook design |

Interested in working together?

- [Website](https://dianyistudio.com/)
- [Threads](https://threads.net/@dianyike1013)
- [Email](mailto:service@dianyistudio.com)

## Acknowledgments

This repository compiles and organizes content from Anthropic's official documentation, community articles, and popular GitHub repositories — credit goes to the original authors. My contribution is the Chinese localization, structured curation, and practical decision frameworks drawn from real project experience.

Skills examples are adapted from [mattpocock/skills](https://github.com/mattpocock/skills), reworked according to this repository's best practices guide.

## License

[MIT](LICENSE)
