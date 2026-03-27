---
name: write-a-skill
description: >
  Create new agent skills with proper structure, progressive disclosure,
  and bundled resources. Use when user wants to create, write, or build
  a new skill, improve an existing skill, or optimize skill triggering.
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

4. **Validate** — smoke-test with 2-3 realistic prompts (see [Validate & Iterate](#validate--iterate))

5. **Review with user** — present draft and verify against [Review Checklist](#review-checklist)

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

Reference-only skills should not set `context: fork` — a subagent receiving guidelines without a concrete task returns nothing useful. Fork is for executable tasks that need context isolation.

## Invocation Control

| Scenario | Frontmatter | Why |
|----------|-------------|-----|
| General tool (no side effects) | (default) | Both user and Claude can trigger |
| **Has side effects** (deploy, commit, send) | `disable-model-invocation: true` | Prevents Claude from auto-triggering destructive actions without user intent |
| Background knowledge | `user-invocable: false` | Claude auto-loads when relevant, hidden from `/` menu |
| Isolated heavy task | `context: fork` | Runs in subagent to protect main context from token bloat |

## Description as Testable Hypothesis

For auto-triggerable skills (the default and `user-invocable: false`), the description is **the only thing Claude sees** when deciding which skill to load. It's surfaced in the system prompt alongside all other installed skills — treat it as a testable hypothesis, not a one-time label. (Skills with `disable-model-invocation: true` are never auto-discovered by Claude, so description quality matters less for triggering — but still write a clear one for humans browsing the `/` menu.)

**Writing rules**:
- Max 1024 chars
- First sentence: what it does
- Second sentence: "Use when [specific triggers]" — include keywords users would naturally say
- Write trigger conditions, NOT a feature summary
- For auto-triggerable skills, lean slightly "pushy" — Claude tends to under-trigger, so err on the side of broader matching

```yaml
# BAD — feature summary, no trigger signals
description: A tool for monitoring pull requests

# GOOD — trigger-oriented, includes user vocabulary
description: >
  Monitor open PRs and report CI status changes.
  Use when user says babysit, watch CI, monitor PRs,
  or check pipeline status.
```

**Verifying triggers**: After writing the description, mentally test it against a few prompts — would Claude choose this skill for "hey can you keep an eye on my PR"? What about "check if CI passed"? If the answer is unclear, revise. For formal trigger optimization with train/test splits, see [reference/eval-workflow.md](reference/eval-workflow.md).

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

3. **Explain the why, not just the rule** — When you need Claude to follow a constraint, explain the reasoning behind it. Claude has good theory of mind — understanding *why* something matters produces better results than rigid directives. If you find yourself writing ALWAYS or NEVER in all caps, that's a signal to reframe: explain the reasoning so Claude understands the intent and can apply good judgment in edge cases.

   ```markdown
   # Weaker — bare directive
   ALWAYS use the legacy API endpoint.

   # Stronger — explains why
   Use the legacy API endpoint — the v2 endpoint doesn't support
   batch operations yet, and our workflow depends on batching.
   ```

4. **Build a Gotchas section** — The highest-signal content in any skill. Only your team has this knowledge. Every time a skill execution hits an unexpected failure, write the failure pattern back into Gotchas. This iteration loop is what makes a skill improve over time — without it, the same mistake repeats forever.

5. **Include completion criteria** — Every task skill should define a "Definition of Done" so Claude knows when to stop. Without this, Claude may over-deliver or leave work incomplete because it has no signal for "enough."

6. **Extract repeated patterns into scripts** — If you notice Claude independently writing similar helper code across multiple uses of the skill (e.g., every invocation creates a `parse_data.py`), that's a strong signal to bundle the script. Write it once in `scripts/`, reference it from SKILL.md. This saves every future invocation from reinventing the wheel and reduces error variance.

## Validate & Iterate

A skill is a hypothesis about how to guide Claude. Validate it before shipping.

1. **Smoke test** — Run the skill on 2-3 prompts yourself. Does it produce the right output? Does Claude follow the instructions or ignore them? Read the execution trace, not just the final output — wasted steps reveal instruction problems.

2. **Side-by-side check** — Manually invoke the skill on a prompt, then try the same prompt without the skill. If the outputs are indistinguishable, the skill instructions aren't adding value — focus on improving the skill body, not the description. (Description triggering is a separate concern — see [reference/eval-workflow.md](reference/eval-workflow.md) for trigger optimization.)

3. **Iterate from observation** — When something goes wrong, resist the urge to add another rigid rule. Instead, understand *why* Claude made that choice and reframe the instruction to convey intent. Generalize from specific failures rather than patching each one individually — a skill that only works for your test cases is useless at scale.

For formal eval workflows (structured assertions, baseline comparisons, quantitative benchmarks, description optimization), see [reference/eval-workflow.md](reference/eval-workflow.md).

## Frontmatter Quick Reference

| Field | When to use |
|-------|-------------|
| `name` | Always. Lowercase + hyphens, max 64 chars |
| `description` | Always. Trigger-oriented, max 1024 chars |
| `disable-model-invocation: true` | Skill has side effects |
| `user-invocable: false` | Background knowledge only |
| `context: fork` | Heavy task needing context isolation |
| `agent: Explore` | With `context: fork`, specify subagent type |
| `allowed-tools` | Set for task skills — least-privilege: only list tools the skill needs |
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
- Same code would be generated repeatedly across invocations
- Errors need explicit handling with known edge cases

**Signal to watch for**: If you test the skill 3 times and Claude writes a similar helper script each time, extract it into `scripts/`. The pattern is: observe repeated agent behavior, then solidify it as bundled infrastructure.

## When to Split Files

Split into separate files when:
- SKILL.md exceeds 500 lines
- Content has distinct domains (e.g., AWS vs GCP deployment)
- Advanced features are rarely needed by most invocations

Follow progressive disclosure: metadata (~100 tokens) -> body (<5k tokens) -> appendix files (unlimited).

## Security & Review Checklist

**Security**:
- [ ] Side-effect skills set `disable-model-invocation: true`
- [ ] `allowed-tools` restricts to minimum needed tools
- [ ] No hardcoded secrets (API keys, tokens, passwords)
- [ ] Scripts validate inputs before executing
- [ ] `context: fork` for untrusted or heavy operations

**Quality**:
- [ ] Description includes trigger keywords ("Use when...")
- [ ] For auto-triggerable skills: description tested against a few realistic prompts (would it trigger? would it false-trigger?)
- [ ] Content type correctly identified (Reference vs Task)
- [ ] Invocation mode matches side-effect risk
- [ ] SKILL.md under 500 lines, details in reference files
- [ ] Does NOT repeat common knowledge Claude already has
- [ ] Constrains goals, not rigid step sequences
- [ ] Instructions explain *why*, not just *what*
- [ ] Gotchas section included
- [ ] Completion criteria defined (for task skills)
- [ ] String variables used where appropriate (`$ARGUMENTS`, `${CLAUDE_SKILL_DIR}`)
- [ ] Attached files referenced with relative paths
- [ ] Frontmatter schema consistent with template

## Advanced Patterns

For stateful skills (config.json), dynamic context injection, log-based incremental reports, and session-scoped hooks, see [reference/advanced-patterns.md](reference/advanced-patterns.md).

## Gotchas

- `context: fork` only works with task content — reference-only skills return empty from subagents
- `disable-model-invocation: true` removes description from context entirely — Claude cannot auto-discover the skill
- Skill descriptions share a budget of ~2% context window; too many skills crowd each other out
- Description under-triggering is more common than over-triggering — when in doubt, make the description broader
- **Iterate this section**: After each skill creation, append new gotchas here
