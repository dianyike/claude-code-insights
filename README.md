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
| [examples/write-a-skill](examples/write-a-skill) | Skill Builder Meta-Skill — content type decisions, invocation control, security configuration, Gotchas iteration loop | Creating new Skills |

**Solo Development Workflow**: `/grill-me` (interrogate the design) → `/prd-to-plan` (break into phases) → `/tdd` (implement one by one)

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
