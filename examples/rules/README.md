# Claude Code Rules — Starter Kit

A battle-tested set of `.claude/rules/` files for guiding Claude Code's behavior on real projects. Copy what's useful, delete what isn't.

## Design Philosophy

Most rule sets fall into one of two failure modes: **too strict** (every rule enforced everywhere, slowing prototyping to a crawl) or **too loose** (rules exist on paper but get silently ignored). This kit solves it with a **pragmatism layer** — a meta-rule (`pragmatism.md`) that defines three risk tiers and scopes enforcement accordingly:

| Tier | Example Scope | Enforcement |
|------|--------------|-------------|
| Critical | Auth, payments, data migrations | Maximum strictness, no shortcuts |
| Standard | Product features, APIs | Full enforcement, documented exceptions OK |
| Exploratory | Prototypes, scripts, spikes | Relaxed testing, tagged as tech debt |

This means `security.md` hits hard on auth code but doesn't block a throwaway script. `testing.md` demands 80% coverage on business logic but won't nag about a one-off migration helper. The rules stay the same — what changes is how strictly they're applied.

### Other key design decisions

- **Every rule has a "Why"** — Claude follows the spirit of a rule better when it understands the rationale. Naked directives get gamed or over-applied.
- **Violation signals** — Golden rules include observable signals ("two files with identical logic") so Claude can self-detect when it's about to break a rule.
- **Separation of concerns** — Localization is its own file, not buried in workflow rules. Teams swap one file instead of hunting through paragraphs.

## File Overview

| File | Purpose |
|------|---------|
| `golden-rules.md` | Hard constraints that apply everywhere (DRY, scope discipline, validated access) |
| `pragmatism.md` | Meta-rule: risk tiers that scope how strictly other rules are enforced |
| `workflow.md` | Day-to-day habits: read-before-write, retry discipline, verification-first |
| `coding-style.md` | Code patterns: immutability, error handling, syntax preferences |
| `testing.md` | TDD workflow, coverage targets, anti-patterns |
| `security.md` | Security checklist, secret management, destructive-op guardrails |
| `localization.md` | Language preferences template — replace placeholders with your team's languages |

### Dependency graph

```
golden-rules.md ──references──► pragmatism.md
workflow.md     ──references──► testing.md
```

All other files are standalone.

## Installation

### Option A: Project-level (recommended for teams)

```bash
# From your project root
mkdir -p .claude/rules
cp path/to/examples/rules/*.md .claude/rules/

# Edit localization.md with your team's languages
$EDITOR .claude/rules/localization.md
```

Rules in `.claude/rules/` are automatically loaded by Claude Code for that project. They apply to everyone who works in the repo (if committed) or just you (if gitignored).

### Option B: User-level (personal defaults)

```bash
# Global rules apply to all your projects
mkdir -p ~/.claude/rules
cp path/to/examples/rules/*.md ~/.claude/rules/

$EDITOR ~/.claude/rules/localization.md
```

### Option C: Cherry-pick

You don't need all 7 files. The highest-value subset for a quick start:

1. `golden-rules.md` + `pragmatism.md` — the core constraint system
2. `workflow.md` — stops the most common AI coding mistakes
3. Everything else — add as needed

## What's been validated

This rule set has been used on:

- **Languages**: TypeScript/JavaScript, Python, Go, Rust
- **Frameworks**: React, Next.js, Express, FastAPI
- **Project types**: Full-stack web apps, CLI tools, documentation repos, MCP servers
- **Team sizes**: Solo developer to small team (1-5)

The rules are language-agnostic by design. `coding-style.md` has a slight JS/TS lean in syntax preferences — adapt or remove that section for other stacks.

## Customization Guide

**To add a rule**: Add it to the most relevant file, include a "Why:" line, and if it's a hard constraint, add a "Violation signal" line.

**To remove a rule**: Just delete it. No other file will break (except the two cross-references noted in the dependency graph).

**To adjust strictness**: Edit the risk tier table in `pragmatism.md`. For example, if your team treats all API work as critical:

```markdown
| **Critical** | Core business logic, payment flows, auth/identity, data migrations, **all API endpoints** | ... |
```

**To add a new tier**: Some teams add a "Legacy" tier for code they can't refactor yet but need to touch:

```markdown
| **Legacy** | Code in `src/old/`, third-party forks | Minimal enforcement — survive and escape |
```
