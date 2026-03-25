---
name: write-a-skill
description: >
  Create new agent skills with proper structure, progressive disclosure,
  and bundled resources. Use when user wants to create, write, or build
  a new skill.
---

# Writing Skills

## Process

1. **Gather requirements** — ask user:
   - What task/domain does the skill cover?
   - Is it **Reference** (background knowledge) or **Task** (step-by-step action)?
   - Does it have side effects? (deploy, send message, commit)
   - Does it need executable scripts or just instructions?
   - Any reference materials to include?

2. **Choose content type and invocation mode** (see [Content Type Decision](#content-type-decision) and [Invocation Control](#invocation-control))

3. **Draft the skill** — create:
   - SKILL.md with concise instructions (<500 lines)
   - Additional reference files if content exceeds limit
   - Utility scripts if deterministic operations needed

4. **Review with user** — present draft and verify against [Review Checklist](#review-checklist)

## Skill Structure

```
skill-name/
├── SKILL.md              # Main instructions (required, <500 lines)
├── reference/            # Detailed docs (loaded on demand)
│   └── api-details.md
├── examples/             # Usage examples (loaded on demand)
│   └── examples.md
├── templates/            # Output templates
│   └── output.md
└── scripts/              # Executable scripts
    └── helper.py
```

Reference attached files in SKILL.md so Claude knows when to load them:

```markdown
## Additional resources
- For complete API details, see [reference/api-details.md](reference/api-details.md)
```

## SKILL.md Template

Use the template at [templates/skill-template.md](templates/skill-template.md).

## Content Type Decision

| Type | Purpose | Invocation | Example |
|------|---------|------------|---------|
| **Reference** | Background knowledge Claude fuses into current work | `user-invocable: false` (Claude auto-loads when relevant) | coding-style, api-conventions |
| **Task** | Step-by-step action with concrete output | Default or `disable-model-invocation: true` | deploy, create-component, review-pr |

**Rule**: If the skill only provides guidelines with no executable task, do NOT set `context: fork` — a subagent receiving guidelines without a task returns nothing useful.

## Invocation Control

| Scenario | Frontmatter | Reason |
|----------|-------------|--------|
| General tool (no side effects) | (default) | Both user and Claude can trigger |
| **Has side effects** (deploy, commit, send) | `disable-model-invocation: true` | SAFETY: prevent Claude from auto-triggering destructive actions |
| Background knowledge | `user-invocable: false` | Claude auto-loads when relevant, hidden from `/` menu |
| Isolated heavy task | `context: fork` | Runs in subagent, protects main context |

## Description Requirements

The description is **the only thing Claude sees** when deciding which skill to load. It's surfaced in the system prompt alongside all other installed skills.

**Rules**:
- Max 1024 chars
- First sentence: what it does
- Second sentence: "Use when [specific triggers]" — include keywords users would naturally say
- Write trigger conditions, NOT a feature summary

```yaml
# BAD — feature summary, no trigger signals
description: A tool for monitoring pull requests

# GOOD — trigger-oriented, includes user vocabulary
description: >
  Monitor open PRs and report CI status changes.
  Trigger when user says babysit, watch CI, monitor PRs,
  or check pipeline status.
```

## Writing Principles

1. **Don't state the obvious** — Claude already knows programming. Only write what Claude does NOT know by default: team conventions, project-specific context, gotchas, workarounds.

2. **Constrain goals, not paths** — Specify WHAT to achieve, not a rigid step order. Let Claude adapt based on context:

   ```markdown
   # BAD — rigid steps
   1. Run `npm test`  2. Run `npm run lint`  3. Deploy

   # GOOD — goal-oriented
   Ensure code passes all tests and lint checks, then deploy.
   Adapt order based on current state.
   ```

3. **Build a Gotchas section (CRITICAL)** — The highest-signal content in any skill. Only your team has this knowledge. Every time a skill execution hits an unexpected failure, write the failure pattern back into Gotchas. This iteration loop is what makes a skill improve over time — without it, the same mistake repeats forever.

4. **Include completion criteria** — Every task skill MUST define a "Definition of Done" so Claude knows when to stop.

## Frontmatter Quick Reference

| Field | When to use |
|-------|-------------|
| `name` | Always. Lowercase + hyphens, max 64 chars |
| `description` | Always. Trigger-oriented, max 1024 chars |
| `disable-model-invocation: true` | Skill has side effects |
| `user-invocable: false` | Background knowledge only |
| `context: fork` | Heavy task needing context isolation |
| `agent: Explore` | With `context: fork`, specify subagent type |
| `allowed-tools` | ALWAYS for task skills. Least-privilege: only list tools the skill needs |
| `argument-hint` | Skill accepts arguments, e.g. `[environment]`, `[filename]` |
| `effort` | `low` / `medium` / `high` / `max` |
| `model` | Override model for this skill |

## String Substitution Variables

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed when invoking the skill |
| `$ARGUMENTS[N]` / `$N` | Positional argument (0-based) |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_SKILL_DIR}` | Absolute path to this skill's directory |

Use `${CLAUDE_SKILL_DIR}` to reference bundled scripts and config files.

## When to Add Scripts

Add utility scripts when:
- Operation is deterministic (validation, formatting, visualization)
- Same code would be generated repeatedly
- Errors need explicit handling

**Principle**: Package stable capabilities as scripts. Let Claude compose, not reinvent.

## When to Split Files

Split into separate files when:
- SKILL.md exceeds 500 lines
- Content has distinct domains
- Advanced features are rarely needed

Follow progressive disclosure: metadata (~100 tokens) -> body (<5k tokens) -> appendix files (unlimited).

## Security Checklist

- [ ] Side-effect skills set `disable-model-invocation: true`
- [ ] `allowed-tools` restricts to minimum needed tools
- [ ] No hardcoded secrets (API keys, tokens, passwords)
- [ ] Scripts validate inputs before executing
- [ ] `context: fork` for untrusted or heavy operations

## Review Checklist

After drafting, verify:

- [ ] Description includes trigger keywords ("Use when...")
- [ ] Content type correctly identified (Reference vs Task)
- [ ] Invocation mode matches side-effect risk
- [ ] `allowed-tools` set with least privilege (for task skills)
- [ ] SKILL.md under 500 lines, details in reference files
- [ ] Does NOT repeat common knowledge Claude already has
- [ ] Constrains goals, not rigid step sequences
- [ ] Gotchas section included
- [ ] Completion criteria defined (for task skills)
- [ ] No hardcoded secrets or sensitive data
- [ ] String variables used where appropriate (`$ARGUMENTS`, `${CLAUDE_SKILL_DIR}`)
- [ ] Attached files referenced with relative paths

## Advanced Patterns

For stateful skills (config.json), dynamic context injection, and log-based incremental reports, see [reference/advanced-patterns.md](reference/advanced-patterns.md).

## Gotchas

- `context: fork` only works with task content — reference-only skills return empty from subagents
- `disable-model-invocation: true` removes description from context entirely — Claude cannot auto-discover the skill
- Skill descriptions share a budget of ~2% context window; too many skills crowd each other out
- **Iterate this section**: After each skill creation, append new gotchas here
