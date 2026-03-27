# Claude Code Insights

English | [繁體中文](README.zh-TW.md)

A best practices guide for Claude Code CLAUDE.md, Skills, and Subagents.

This repository compiles and organizes content primarily from Anthropic's official documentation, community articles, and popular GitHub repositories — credit goes to the original authors. This is a curated collection of what I've learned along the way, not **original research**.

## Who Is This For

Developers ranging from Claude Code beginners to those looking to master Skills and Subagent design patterns.

- **Beginners**: Start with the CLAUDE.md guide to build a solid foundation
- **Advanced**: The Skills and Subagent guides cover design patterns and architectural strategies

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
| [examples/security-reviewer](examples/security-reviewer) | Dual-verification security review Subagent — Semgrep + Codex cross-validation with Fix-Verify loop, confidence scoring, and conflict resolution | Advanced |

### Hook Examples

| Example | Description | Difficulty |
|---------|-------------|------------|
| [examples/npm-supply-chain-defense](examples/npm-supply-chain-defense) | npm supply chain three-layer defense — `.npmrc` script blocking + PreToolUse Hook checks (registry, OSV.dev, version resolution, CLI syntax validation) + Semgrep supply chain scanning. Includes 42 regression tests | Advanced |

### Skills Examples

The following Skills are adapted from [mattpocock/skills](https://github.com/mattpocock/skills) (implementing concepts like design trees and TDD vertical slices), reworked according to this repository's best practices guide: templates extracted to `templates/`, reference materials moved to `reference/`, and Gotchas sections added.

| Example | Description | Use Case |
|---------|-------------|----------|
| [examples/grill-me](examples/grill-me) | Design Interrogation — traverses every branch of a decision tree, resolving design decision dependencies one by one | Pre-coding design stress test |
| [examples/tdd](examples/tdd) | TDD Workflow — red-green-refactor vertical slices with test examples, mock guidelines, and deep module design reference | Feature development and bug fixes |
| [examples/prd-to-plan](examples/prd-to-plan) | PRD to Implementation Plan — breaks requirements into tracer bullet vertical slices, outputs to `./plans/` | Requirements decomposition and phase planning |
| [examples/write-a-skill](examples/write-a-skill) | Skill Builder Meta-Skill — content type decisions, invocation control, security configuration, Gotchas iteration loop. Includes eval workflow reference | Creating new Skills |
| [examples/skill-eval-toolkit](examples/skill-eval-toolkit) | Skill Eval Toolkit — eval-driven testing, quantitative benchmarking, blind A/B comparison, description trigger optimization with automated iteration loop | Validating and optimizing existing Skills |

**Solo Development Workflow**: `/grill-me` (interrogate the design) → `/prd-to-plan` (break into phases) → `/tdd` (implement one by one)

**Skill Development Workflow**: `/write-a-skill` (author the skill) → `/skill-eval-toolkit` (evaluate and optimize)

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

The workflow: create test prompts → run with-skill and baseline in parallel → grade → aggregate benchmarks → interactive viewer for human review → improve → repeat. Also includes automated description trigger optimization (train/test split, iterative improvement).

```
You: "Evaluate my json-diff skill and tell me if it actually adds value"
Claude: (loads skill-eval-toolkit, creates test cases, spawns parallel runs,
         grades outputs, launches viewer, shows you the results)
```

> **When to use which**: If the question is "how should I structure this skill?" → `write-a-skill`. If the question is "is this skill actually working well?" → `skill-eval-toolkit`. Most skills start with the former and graduate to the latter when you need quantitative rigor.

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

## License

[MIT](LICENSE)
