# Claude Code Skills Best Practices Guide

> Inspired by: [From Development, Evaluation to Safe Usage — Building Skills: Deep Read of "Equipping Agents for the Real World with Agent Skills" Part 3](https://www.bilibili.com/video/BV1ZmCLBmExv/)
>
> Compiled from Anthropic's official documentation, popular GitHub repositories, community experience, and [Lessons from Building Claude Code: How We Use Skills](https://www.linkedin.com/pulse/lessons-from-building-claude-code-how-we-use-skills-thariq-shihipar-iclmc)

---

## Table of Contents

1. [What Is a Skill](#1-what-is-a-skill)
2. [Core Architecture: Progressive Loading](#2-core-architecture-progressive-loading)
3. [SKILL.md File Format](#3-skillmd-file-format)
4. [Content Writing Principles](#4-content-writing-principles)
5. [Frontmatter Field Reference](#5-frontmatter-field-reference)
6. [Skill Types and Invocation Control](#6-skill-types-and-invocation-control)
7. [Directory Structure and Storage Locations](#7-directory-structure-and-storage-locations)
8. [Advanced Patterns](#8-advanced-patterns)
9. [Skill vs Subagent vs CLAUDE.md Decision Matrix](#9-skill-vs-subagent-vs-claudemd-decision-matrix)
10. [Best Practice Design Templates](#10-best-practice-design-templates)
11. [Skill and Subagent Collaboration](#11-skill-and-subagent-collaboration)
12. [Security Guidelines](#12-security-guidelines)
13. [Iteration Methodology](#13-iteration-methodology)
14. [Common Troubleshooting](#14-common-troubleshooting)
15. [References](#15-references)
16. [Quick Checklist](#16-quick-checklist)

---

## 1. What Is a Skill

A Skill is a structured folder composed of **instructions, scripts, and resources** that Claude can dynamically discover and load to improve performance on specific tasks.

> Source: [Extend Claude with skills](https://code.claude.com/docs/en/skills)

### Core Definition

- Each Skill uses a `SKILL.md` file as its entry point, with optional scripts and reference materials
- Claude automatically decides whether to load a Skill based on its `description`, or the user can manually trigger it via `/skill-name`
- Follows the [Agent Skills](https://agentskills.io) open standard for cross-tool compatibility

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Discoverable** | Claude scans all skill `name` + `description` fields to automatically determine whether to trigger |
| **Actionable** | Not just knowledge — can execute scripts, call tools, and produce files |
| **Reusable** | The same skill can be shared across projects (`~/.claude/skills/`) or across an organization (enterprise) |
| **Hooks Support** | Can register dynamic hooks within the skill lifecycle |
| **Flexible Configuration** | Tool allowlists, model selection, effort level, subagent isolation |
| **Directory Structure** | Leverage subdirectories for templates, examples, scripts, and reference docs |

### Goal of Skills

**Encapsulate portable, reusable process knowledge.** The `name` and `description` are always loaded into context (for discovery); full instructions are only loaded when triggered (saving context). Skills can both read and execute scripts.

### Custom Commands Have Merged into Skills

`.claude/commands/deploy.md` and `.claude/skills/deploy/SKILL.md` both create `/deploy` with identical behavior. Existing commands continue to work, but skills offer additional features: subdirectory support for attachments, frontmatter-controlled triggering, and automatic loading by Claude.

---

## 2. Core Architecture: Progressive Loading

Skills use a **three-layer progressive disclosure** approach to maximize context efficiency:

```
Layer 1: YAML metadata (~100 tokens)
  ↓ Claude scans all skill name + description fields to assess relevance
Layer 2: SKILL.md body (<5k tokens recommended)
  ↓ Full instructions loaded only when the skill is triggered
Layer 3: Appendix files (unlimited)
  ↓ Loaded only when explicitly referenced in SKILL.md
```

### Why This Matters

- **Layer 1 is always in context**: All skill descriptions occupy roughly 2% of the context window (fallback cap of 16,000 characters)
- **Layer 2 loads on demand**: Unneeded skills don't waste context
- **Layer 3 loads lazily**: Large API docs and example sets don't need to load every time

### Context Budget

The total size of skill descriptions is dynamically capped at 2% of the context window, with a fallback of 16,000 characters. When exceeded, some skills are excluded. Check with `/context`, or override with the `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable.

---

## 3. SKILL.md File Format

Every Skill must have a `SKILL.md` file consisting of two parts:

```yaml
---
# ===== YAML Frontmatter =====
name: my-skill                    # Display name, lowercase + digits + hyphens (max 64 chars)
description: >                    # Claude uses this to decide whether to trigger (max 1024 chars)
  Reviews Python code for bugs and readability issues.
  Use when user asks to review, check, or audit code.
---

# ===== Markdown Body: Skill Instructions =====

## Workflow

1. Step one
2. Step two

## Output format

...
```

### Two Content Types

**Reference Content**: Provides knowledge that Claude integrates into its current work. Suitable for inline execution.

```yaml
---
name: api-conventions
description: API design patterns for this codebase
---

When writing API endpoints:
- Use RESTful naming conventions
- Return consistent error formats
- Include request validation
```

**Task Content**: Gives Claude specific step-by-step instructions. Typically paired with `disable-model-invocation: true` for manual triggering only.

```yaml
---
name: deploy
description: Deploy the application to production
context: fork
disable-model-invocation: true
---

Deploy the application:
1. Run the test suite
2. Build the application
3. Push to the deployment target
```

---

## 4. Content Writing Principles

> Source: [Lessons from Building Claude Code: How We Use Skills](https://www.linkedin.com/pulse/lessons-from-building-claude-code-how-we-use-skills-thariq-shihipar-iclmc) (Thariq Shihipar, Anthropic)

### 4.1 The Description Is for the Model, Not for Humans

When Claude starts a session, it scans all skill `description` fields to determine whether a request matches any skill. Therefore, descriptions should specify **when to trigger**, not provide a feature summary.

```yaml
# ❌ Bad — reads like a product brochure
description: A tool for monitoring pull requests

# ✅ Good — specifies trigger conditions and words users would say
description: >
  Trigger when user says babysit, watch CI, monitor PRs,
  or check pipeline status.
```

### 4.2 Don't State the Obvious

Claude already has extensive general programming knowledge. A Skill should not rehash textbook material — it should supply what Claude **doesn't already know**:

| Include | Don't Include |
|---------|---------------|
| Your team's specific conventions and preferences | Language syntax and standard library usage |
| Project-specific context and history | Generic design pattern tutorials |
| External system connection and auth workflows | Framework basics |
| Pitfalls encountered and workarounds | Content already covered in official docs |

### 4.3 Build a Gotchas Section

The **highest-signal content** in any Skill is often not the tutorial — it's the Gotchas (pitfall log). Only your team's real-world issues count as unique knowledge.

```markdown
## Gotchas

- `api/v2/users` returns `created_at` in UTC, but `updated_at` in local timezone (issue filed, won't be fixed short-term)
- Test environment rate limit is 10 req/s, not the 100 stated in docs — batch tests must add delay
- Deploy script silently skips migration on macOS — must add `--force-migrate` flag
```

**Iteration tip**: Keep the Gotchas section updated over time. Whenever Claude hits an unexpected failure while executing a Skill, add the failure pattern to Gotchas.

### 4.4 Constrain the Goal, Not the Path

Avoid over-constraining Claude's execution steps. Specify **what to achieve**, not a fixed sequence of operations:

```markdown
# ❌ Over-constrained — limits flexibility
1. Run `npm test`
2. Run `npm run lint`
3. Run `npm run build`
4. Deploy

# ✅ Goal-constrained — Claude adapts the order as needed
Ensure the code passes all tests and lint checks, then build and deploy.
Adapt the order based on the current state (e.g., skip build if only docs changed).
```

---

## 5. Frontmatter Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Recommended (technically optional) | Display name; defaults to directory name if omitted. Lowercase letters, digits, hyphens (max 64 chars). Listed as required metadata in the official Help Center |
| `description` | Recommended (technically optional) | What the skill does and when to use it. Claude uses this to decide whether to trigger. Falls back to the first paragraph of the body if omitted (max 1024 chars). Listed as required metadata in the official Help Center |
| `argument-hint` | No | Hint displayed during autocomplete. e.g., `[issue-number]`, `[filename] [format]` |
| `disable-model-invocation` | No | Set to `true` to prevent Claude from auto-triggering; only manual `/name` invocation allowed. Default `false` |
| `user-invocable` | No | Set to `false` to hide from the `/` menu; only Claude can trigger it. Default `true` |
| `allowed-tools` | No | Tool allowlist available to Claude during skill execution (e.g., `Read, Grep, Glob`) |
| `model` | No | Model to use during skill execution |
| `effort` | No | Reasoning effort: `low` / `medium` / `high` / `max` (`max` is Opus 4.6 only) |
| `context` | No | Set to `fork` to execute in an isolated subagent context |
| `agent` | No | When `context: fork` is set, specifies which subagent type to use (e.g., `Explore`, `Plan`, custom agent) |
| `hooks` | No | Hooks configuration for the skill lifecycle |

> **The following fields are NOT natively supported by Claude Code** — Claude Code's frontmatter parser does not process these fields, and writing them has no effect. Listed here for reference only.

| Field | Source | Description |
|-------|--------|-------------|
| `mode` | Third-party source analysis | Setting to `true` classifies the skill as a Mode Command. Not listed in the official frontmatter reference; behavior may change across versions |
| `version` | [Agent Skills](https://agentskills.io) open standard | Version tracking metadata, e.g., `"1.0.0"` |
| `compatibility` | [Agent Skills](https://agentskills.io) open standard | Declares required tools and dependencies |
| `license` | [Agent Skills](https://agentskills.io) open standard | License declaration (e.g., `MIT`) for shareable skills |

### String Substitution Variables

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed when invoking the skill |
| `$ARGUMENTS[N]` / `$N` | Access the Nth argument by position (0-based) |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_SKILL_DIR}` | Absolute path to the directory containing the skill's `SKILL.md` |

---

## 6. Skill Types and Invocation Control

### Invocation Mode Matrix

| Frontmatter Setting | User Can Trigger | Claude Can Trigger | Context Loading Behavior |
|---------------------|------------------|--------------------|--------------------------|
| (default) | Yes | Yes | description always in context; full content loaded on trigger |
| `disable-model-invocation: true` | Yes | No | description **not in** context; loaded when user triggers |
| `user-invocable: false` | No | Yes | description always in context; loaded when Claude triggers |

### When to Use Which

| Type | Setting | Use Case |
|------|---------|----------|
| **Bidirectional** | Default | General-purpose tools, code explanation, formatting |
| **User-only** | `disable-model-invocation: true` | Side-effecting operations: deploy, commit, send message |
| **Claude-only** | `user-invocable: false` | Background knowledge: legacy-system-context, coding-style |

### Key Principle

> **Skills with side effects must set `disable-model-invocation: true`.** You don't want Claude to auto-deploy just because the code looks ready.

---

## 7. Directory Structure and Storage Locations

### Skill Directory Structure

```
my-skill/
├── SKILL.md              # Main instructions (required) — keep under 500 lines
├── reference.md          # Detailed API docs (loaded on demand)
├── examples.md           # Usage examples (loaded on demand)
├── templates/
│   └── output-template.md  # Output template
└── scripts/
    └── helper.py         # Executable script
```

Reference attachments in `SKILL.md` so Claude knows when to load them:

```markdown
## Additional resources

- For complete API details, see [reference.md](reference.md)
- For usage examples, see [examples.md](examples.md)
```

### Storage Locations and Priority

| Location | Path | Scope |
|----------|------|-------|
| Enterprise | Deployed via managed settings | All users in the organization |
| Personal | `~/.claude/skills/<skill-name>/SKILL.md` | All projects for the individual |
| Project | `.claude/skills/<skill-name>/SKILL.md` | This project only |
| Plugin | `<plugin>/skills/<skill-name>/SKILL.md` | Wherever the plugin is enabled |

**Priority**: Enterprise > Personal > Project. Same-name skills at higher priority override lower priority. Plugin skills use a `plugin-name:skill-name` namespace and don't conflict.

### Monorepo Support

When working in a subdirectory, Claude automatically discovers nested `.claude/skills/` directories. For example, when editing files in `packages/frontend/`, it also loads `packages/frontend/.claude/skills/`.

### --add-dir Additional Directories

`.claude/skills/` directories within paths added via `--add-dir` are automatically loaded, with live change detection supported.

---

## 8. Advanced Patterns

### 8.1 Dynamic Context Injection

The `` !`<command>` `` syntax executes a shell command before the skill reaches Claude, replacing the placeholder with the output:

```yaml
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: Explore
allowed-tools: Bash(gh *)
---

## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
- Changed files: !`gh pr diff --name-only`

## Your task
Summarize this pull request...
```

Execution order:
1. Each `` !`<command>` `` runs immediately (Claude hasn't seen anything yet)
2. Output replaces the placeholders in the skill
3. Claude receives the fully rendered prompt

### 8.2 Subagent Isolated Execution

`context: fork` runs the skill in an isolated subagent context:

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---

Research $ARGUMENTS thoroughly:

1. Find relevant files using Glob and Grep
2. Read and analyze the code
3. Summarize findings with specific file references
```

**Note**: `context: fork` is only appropriate for skills with explicit task instructions. If a skill contains only guidelines (e.g., "use these API conventions") without a concrete task, the subagent receives the guidelines but has no actionable prompt and returns meaninglessly.

### 8.3 Bundled Scripts and Visual Output

**Core principle**: Encapsulate stable capabilities into scripts and helper functions, and let Claude handle **composition** rather than reinventing the wheel. Don't make Claude write boilerplate from scratch every time — give it code, not documentation.

Skills can bundle and execute scripts in any language, producing interactive HTML and other visual output:

````yaml
---
name: codebase-visualizer
description: Generate an interactive tree visualization of your codebase
allowed-tools: Bash(python *)
---

# Codebase Visualizer

Run the visualization script:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/visualize.py .
```
````

This pattern works for: dependency graphs, test coverage reports, API documentation, database schema visualizations, and more.

### 8.4 Extended Thinking

Include the word "ultrathink" in the skill content to enable extended thinking.

### 8.5 Config State Management (Stateful Skills)

> Source: [Lessons from Building Claude Code](https://www.linkedin.com/pulse/lessons-from-building-claude-code-how-we-use-skills-thariq-shihipar-iclmc)

Skills are stateless on every run. Use `config.json` to store user preferences, turning a Skill from a **stateless tool** into a **stateful assistant**:

```yaml
---
name: deploy
description: Deploy application. Trigger on deploy, ship, release.
disable-model-invocation: true
allowed-tools: Read, Write, Bash(npm *), Bash(git *)
---

# Deploy

## Setup (first run only)

Check if `${CLAUDE_SKILL_DIR}/config.json` exists.
If not, ask the user for:
- Default deploy target (staging / production)
- Notification channel (Slack webhook URL)
- Whether to run migrations automatically

Save answers to `${CLAUDE_SKILL_DIR}/config.json`.

## Subsequent runs

Read `${CLAUDE_SKILL_DIR}/config.json` and use saved preferences.
```

### 8.6 Log Memory (Incremental Reports Across Runs)

> Source: [Lessons from Building Claude Code](https://www.linkedin.com/pulse/lessons-from-building-claude-code-how-we-use-skills-thariq-shihipar-iclmc)

Skills don't remember what they did last time. The solution: have the Skill write a log, read it on the next run, and report only **incremental changes**:

```yaml
---
name: babysit-prs
description: >
  Monitor open PRs and report status changes.
  Trigger on babysit, watch PRs, check pipeline.
allowed-tools: Read, Write, Bash(gh *)
---

# PR Babysitter

## Workflow

1. Read the log at `${CLAUDE_SKILL_DIR}/data/run-log.jsonl`
   (if it exists — first run will have no log)
2. Fetch current PR statuses: `gh pr list --json number,title,statusCheckRollup`
3. Compare with last log entry — identify what CHANGED since last run
4. Report only the deltas (new failures, newly passing, new PRs)
5. Append current state to `${CLAUDE_SKILL_DIR}/data/run-log.jsonl`
```

**Key point**: Use JSONL format for logs (one JSON object per line) for easy appending and parsing. Each record should include a timestamp and a full state snapshot.

### 8.7 On-Demand Hooks (Session-Level Guardrails)

> Source: [Lessons from Building Claude Code](https://www.linkedin.com/pulse/lessons-from-building-claude-code-how-we-use-skills-thariq-shihipar-iclmc)

Some safety rules are too strict to keep on permanently. Use a Skill to dynamically register a Hook that expires automatically when the session ends:

```yaml
---
name: careful
description: >
  Enable extra safety checks for the current session.
  Trigger on careful, safe mode, paranoid mode.
disable-model-invocation: true
hooks:
  PreToolUse:
    - matcher: Bash
      command: |
        # Block dangerous commands in careful mode
        echo "$TOOL_INPUT" | grep -qE '(rm -rf|drop table|force push|--no-verify)' \
          && echo "BLOCKED: dangerous command detected in careful mode" \
          && exit 1
        exit 0
---

# Careful Mode Enabled

Extra safety hooks are now active for this session:

- `rm -rf` commands are blocked
- `drop table` SQL is blocked
- `git push --force` is blocked
- `--no-verify` flag is blocked

To disable, end the session or start a new one.
```

**Design philosophy**: This isn't about permanently limiting capabilities — it's about temporarily elevating the safety level during high-risk operations. The Hook expires automatically when the session ends, without affecting everyday workflows.

---

## 9. Skill vs Subagent vs CLAUDE.md Decision Matrix

| Factor | Skill | Subagent | CLAUDE.md |
|--------|-------|----------|-----------|
| **Persistence** | Folder, auto-loaded | Fork context, isolated execution | Always loaded |
| **Context Cost** | Progressive (on-demand) | Independent context window | Always occupies context |
| **Reusability** | Three tiers: Project / Personal / Enterprise | Project-level | Project-level |
| **Automation** | Supports auto-triggering | Delegated by the main agent | Passively loaded |
| **Best For** | Repeatable processes/workflows | Tasks requiring context isolation | Global rules and conventions |

### When to Use What

| Scenario | Choice | Reason |
|----------|--------|--------|
| You keep typing the same prompt repeatedly | **Skill** | Encapsulate as a reusable, triggerable command |
| Claude must always follow a rule | **CLAUDE.md** | Loaded into every conversation |
| A subtask would bring in too much irrelevant information | **Subagent** | Context isolation — only returns a summary |
| Need to execute scripts and produce files | **Skill** | Supports bundled scripts and `allowed-tools` |
| Background knowledge, but not needed every time | **Skill** (`user-invocable: false`) | Loaded on demand without wasting context |
| A planning task requiring back-and-forth | **Main conversation + Plan Mode** | Requires real-time user involvement |

---

## 10. Best Practice Design Templates

### Template 1: Reference Skill (Background Knowledge)

````yaml
---
name: coding-style
description: >
  Immutable coding patterns, naming conventions, and file organization rules.
  Use when writing or reviewing code in this project.
user-invocable: false
---

# Coding Style Guide

## Immutability (CRITICAL)

ALWAYS create new objects, NEVER mutate existing ones:

```
WRONG:  modify(original, field, value) -> changes original in-place
CORRECT: update(original, field, value) -> returns new copy with change
```

## File Organization

- High cohesion, low coupling
- 200-400 lines typical, 800 max
- Organize by feature/domain, not by type

## Additional resources

- For complete patterns, see [reference.md](reference.md)
````

### Template 2: Task Skill (User-Triggered Only)

```yaml
---
name: deploy
description: Deploy the application to staging or production environment
disable-model-invocation: true
context: fork
allowed-tools: Bash(npm *), Bash(git *), Read, Grep
argument-hint: [environment]
---

# Deploy Application

Deploy to $ARGUMENTS environment.

## Pre-flight checks

1. Run the full test suite: `npm test`
2. Verify no uncommitted changes: `git status`
3. Confirm current branch is `main`

## Deploy steps

1. Build the application: `npm run build`
2. Run deployment script: `npm run deploy:$0`
3. Verify deployment health check

## Post-deploy

1. Run smoke tests against deployed environment
2. Report deployment status with version and timestamp

## Failure handling

If any step fails, STOP immediately and report:
- Which step failed
- The error output
- Suggested remediation
```

### Template 3: Research Skill (Forked Execution)

```yaml
---
name: deep-research
description: >
  Research a library, framework, or technical topic thoroughly.
  Use when comparing technologies, investigating architecture, or
  answering "what should we use for X?" questions.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, WebSearch, WebFetch
---

# Deep Research

Research $ARGUMENTS thoroughly.

## Workflow

1. **Define scope**: Clarify what exactly needs to be researched
2. **Multi-source collection**: Search web, read docs, explore codebase
3. **Cross-validate**: Compare findings across at least 3 independent sources
4. **Synthesize**: Produce structured findings with specific references

## Output format

Return a structured summary:

### Key findings
- 3-5 bullet points of core discoveries

### Detailed analysis
- Comparison table if multiple options
- Pros/cons with concrete evidence

### Recommendation
- Specific, actionable recommendation with rationale

### Sources
- List all sources consulted
```

### Template 4: Workflow Skill (With Scripts and Templates)

```yaml
---
name: create-component
description: >
  Scaffold a new React component with tests, stories, and types.
  Use when user asks to create, scaffold, or generate a component.
allowed-tools: Read, Write, Bash(npm *)
argument-hint: [ComponentName]
---

# Create Component

Scaffold a new React component named `$0`.

## Steps

1. Read the template files in this skill directory:
   - [templates/component.tsx.md](templates/component.tsx.md)
   - [templates/component.test.tsx.md](templates/component.test.tsx.md)

2. Create the component directory: `src/components/$0/`

3. Generate files using the templates, replacing `{{ComponentName}}` with `$0`

4. Run type check: `npm run typecheck`

5. Run the new test: `npm test -- --testPathPattern=$0`

## Completion criteria

- [ ] Component file created and exports correctly
- [ ] Test file created and passes
- [ ] TypeScript compiles without errors
```

### Template 5: PR Review Skill (Dynamic Injection)

```yaml
---
name: review-pr
description: >
  Review the current pull request for quality, security, and best practices.
  Use when asked to review, check, or audit a PR.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, Bash(gh *)
---

# Pull Request Review

## Context (auto-injected)

- PR description: !`gh pr view --json title,body --jq '.title + "\n" + .body'`
- Changed files: !`gh pr diff --name-only`
- Diff stats: !`gh pr diff --stat`

## Review dimensions

You MUST review ALL of the following dimensions:

1. **Correctness**: Logic errors, edge cases, off-by-one errors
2. **Security**: OWASP Top 10 checks, input validation, secret exposure
3. **Performance**: Unnecessary computation, N+1 queries, memory leaks
4. **Readability**: Naming, structure, comments, complexity
5. **Testing**: Are changes covered by tests? Are edge cases tested?

## Output format

### Summary

| Dimension | Status | Issues |
|-----------|--------|--------|
| Correctness | PASS/FAIL | count |
| Security | PASS/FAIL | count |
| Performance | PASS/FAIL | count |
| Readability | PASS/FAIL | count |
| Testing | PASS/FAIL | count |

### Critical issues (must fix)
...

### Suggestions (nice to have)
...

## Anti-early-victory

You MUST complete ALL review dimensions before returning results.
Do NOT review only part of the diff and declare "looks good."
Each dimension must have a concrete finding (pass or issue found).
```

---

## 11. Skill and Subagent Collaboration

Skills and Subagents are complementary systems that can be integrated bidirectionally:

### Direction 1: Skill → Subagent (`context: fork`)

The skill content becomes the subagent's task prompt, with the `agent` field determining the execution environment:

```yaml
# SKILL.md
---
name: my-task
context: fork
agent: Explore      # Uses the Explore agent's model, tools, and permissions
---

(This content becomes the task the subagent receives)
```

### Direction 2: Subagent → Skill (`skills` field)

The subagent definition uses the `skills` field to preload a skill as reference knowledge:

```yaml
# .claude/agents/code-reviewer.md
---
name: code-reviewer
tools: Read, Grep, Glob, Write
skills: coding-style           # Preloads the full content of the coding-style skill
---

(Subagent's system prompt)
```

### Integration Summary

| Direction | System Prompt | Task | Additional Loading |
|-----------|--------------|------|--------------------|
| Skill + `context: fork` | From agent type | SKILL.md content | CLAUDE.md |
| Subagent + `skills` | Subagent's markdown body | Claude's delegation message | Preloaded skills + CLAUDE.md |

> **WARNING**: `context: fork` is only appropriate for skills with **explicit task instructions**. If a skill only contains guidelines (e.g., "use these API conventions") without a concrete task, the subagent receives the guidelines but has no actionable prompt and returns meaninglessly. When using `context: fork` in "Direction 1", the SKILL.md body **must contain an executable task description** — reference knowledge alone is not enough.

### Division of Responsibilities

| Content Type | Where to Put It | Reason |
|-------------|-----------------|--------|
| Output format examples | Skill or Subagent prompt | The agent's own work specification |
| Code style/conventions | Skill (`user-invocable: false`) | Shared knowledge used by multiple agents |
| Library usage examples | MCP (e.g., Context7) | Fetches the latest docs in real time |
| Repeatable workflows | Skill (task content) | Encapsulated as a triggerable command |
| Heavy tasks needing context isolation | Subagent | Independent context window |

---

## 12. Security Guidelines

Skills can run scripts and access the file system — security awareness must scale accordingly.

### Three Security Red Lines

| Red Line | Description |
|----------|-------------|
| **Only install from trusted sources** | Do not execute skill packages or scripts of unknown origin |
| **Inspect before use** | Carefully read all files in a skill, especially scripts, dependencies, and external connections |
| **Understand the execution logic** | Distinguish what code will run, what the inputs/outputs are, and avoid accidental execution |

### Security Configuration

| Measure | Description |
|---------|-------------|
| `allowed-tools` | Restrict the tools available to Claude, preventing unauthorized API calls or file operations |
| `disable-model-invocation: true` | Side-effecting skills must be manually triggered |
| `context: fork` | Subagent isolation prevents side effects from polluting the main conversation |
| Permission rules | Use `Skill(deploy *)` deny rules to block specific skills |

### Threat Awareness

The community has tracked hundreds of malicious skill patterns (e.g., Unicode injection, hidden instructions, auto-execute patterns). Related statistics can be found in community security threat databases such as [FlorianBruniaux/claude-code-ultimate-guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide). **These figures are unofficial community statistics and have not been verified by Anthropic.** **Security is not about limiting capability — it's about protecting trust.** The openness of Skills enables Claude to truly "get things done," but it also means a larger attack surface.

---

## 13. Iteration Methodology

### Step 1: Start with Evaluation (Problem-Driven)

1. Have Claude execute real tasks first and **record failure points and friction points**
2. Each Skill should address a specific gap — don't build "just in case" skills
3. Validate in small steps and expand incrementally

### Step 2: Design for Scale (Layered Structure)

1. Put the main workflow in `SKILL.md` (<500 lines)
2. Split details into attachments like `reference/`, `templates/`, `examples/`
3. Follow progressive loading: metadata (~100 tokens) → body (<5k) → appendix (unlimited)

### Step 3: Name and Describe from Claude's Perspective

1. `name` + `description` determine whether Claude triggers — precision matters
2. **Write trigger conditions in the description, not a feature summary** (see Section 4.1)
3. Include keywords users are likely to say; start with verbs
4. Monitor actual usage: track mistriggers and missed triggers as iteration input
5. Use a `PreToolUse` hook to log skill trigger frequency and identify under-triggered skills

### Step 4: Iterate Together with Claude

1. **On success**: Have Claude summarize "what worked" and write it back into the Skill
2. **On failure**: Guide it to reflect on the gap, then add the findings to the SOP
3. Build a **human-AI co-creation feedback loop**

---

## 14. Common Troubleshooting

| Problem | Root Cause | Solution |
|---------|-----------|----------|
| Skill doesn't trigger | Description is vague or keywords don't match | Rewrite the description to include words users naturally say. Use `/skill-name` to confirm the skill exists |
| Wrong Skill triggers | Multiple skills have overlapping descriptions | Increase the distinctiveness of each skill's description |
| Skill triggers too often | Description is too broad | Add `disable-model-invocation: true`, or narrow the description |
| Claude can't see certain Skills | Total skill count exceeds the context budget | Check with `/context`, remove unneeded skills, or increase `SLASH_COMMAND_TOOL_CHAR_BUDGET` |
| Attachments not loaded | SKILL.md doesn't reference the file | Explicitly link to attachments with markdown links in SKILL.md |
| Changes don't take effect | Edited the skill in the wrong location | Verify the path and priority (Enterprise > Personal > Project) |
| `context: fork` produces no output | Skill contains only guidelines, no task | `context: fork` requires explicit task instructions — reference knowledge alone is not enough |

---

## 15. References

### Official Documentation

- [Extend Claude with skills](https://code.claude.com/docs/en/skills) — Official complete reference
- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — Official writing guide
- [How to create custom Skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills) — Help Center tutorial
- [Agent Skills open standard](https://agentskills.io) — Cross-tool compatibility standard

### Official Team Articles

- [Lessons from Building Claude Code: How We Use Skills](https://www.linkedin.com/pulse/lessons-from-building-claude-code-how-we-use-skills-thariq-shihipar-iclmc) (Thariq Shihipar, Anthropic) — 9 battle-tested best practices covering the content layer, structure layer, and advanced techniques. Primary source for Sections 4 and 8.5-8.7 of this guide
- [A complete guide to building skills for Claude](https://claude.com/blog/complete-guide-to-building-skills-for-claude) — Official comprehensive building guide

### High-Star GitHub Repositories

| Repository | Highlights |
|------------|-----------|
| [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) | Curated Claude Skills collection with clear categorization |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | 680+ agent skills including official team and community contributions |
| [rohitg00/awesome-claude-code-toolkit](https://github.com/rohitg00/awesome-claude-code-toolkit) | Comprehensive toolkit with 135 agents + 35 skills + 42 commands |
| [FlorianBruniaux/claude-code-ultimate-guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide) | 14 production-grade skill templates with security threat database |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | Comprehensive curation including skills, hooks, and plugins |
| [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | Community-curated Skills collection |
| [mattpocock/skills](https://github.com/mattpocock/skills) | 17 high-quality Skills — grill-me (design tree interrogation), tdd (vertical slice TDD), write-a-prd / prd-to-plan (requirements to implementation plan), and more. Design patterns worth studying |

### Further Reading

- [Claude Skills Explained (AnalyticsVidhya)](https://www.analyticsvidhya.com/blog/2026/03/claude-skills-custom-skills-on-claude-code/) — In-depth architecture analysis
- [Essential Claude Code Skills and Commands](https://batsov.com/articles/2026/03/11/essential-claude-code-skills-and-commands/) — Practical tips
- [10 Must-Have Skills for Claude (Medium)](https://medium.com/@unicodeveloper/10-must-have-skills-for-claude-and-any-coding-agent-in-2026-b5451b013051) — Community recommendations
- [Skill Issue: Harness Engineering for Coding Agents (HumanLayer)](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents) — Skills as progressive disclosure in practice, with context corruption research data
- [Harness Engineering: leveraging Codex in an agent-first world (OpenAI)](https://openai.com/index/harness-engineering/) — OpenAI's agent engineering methodology

---

## 16. Quick Checklist

When designing a new Skill, verify each item:

**Content Layer**
- [ ] `description` specifies **trigger conditions**, not a feature summary (Section 4.1)
- [ ] Does not repeat general knowledge Claude already has — only adds project-specific context (Section 4.2)
- [ ] Includes a **Gotchas** section documenting pitfalls the team has encountered (Section 4.3)
- [ ] Constrains the **goal**, not the step sequence (Section 4.4)

**Structure Layer**
- [ ] `SKILL.md` stays under 500 lines; detailed references go in attachments
- [ ] Attachments use **relative paths** and their purpose is documented in SKILL.md
- [ ] User preferences stored in `config.json` when needed (Section 8.5)

**Triggering and Security**
- [ ] Side-effecting skills set `disable-model-invocation: true`
- [ ] Background knowledge skills set `user-invocable: false`
- [ ] Long-running tasks needing isolation use `context: fork`
- [ ] `allowed-tools` restricts available tools following least privilege

**Acceptance**
- [ ] Includes clear **completion criteria** (Definition of Done)
- [ ] Tested with real scenarios for both triggering and execution
- [ ] No hardcoded secrets or sensitive data
