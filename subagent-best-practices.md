# Subagent Best Practices Guide

> Inspired by: [Detailed Guide to Claude Code SubAgents](https://www.bilibili.com/video/BV1B6YpzFENd/)
>
> Compiled from official documentation, popular GitHub repositories, and community experience

---

## Table of Contents

1. [What Is a Subagent](#1-what-is-a-subagent)
2. [Core Problems: Black Box and Ephemeral](#2-core-problems-black-box-and-ephemeral)
3. [Solution: Result Persistence](#3-solution-result-persistence)
4. [Subagent File Format](#4-subagent-file-format)
5. [Best Practice Design Templates](#5-best-practice-design-templates)
6. [Separating Examples from Skills](#6-separating-examples-from-skills)
7. [Tool Scope Strategy](#7-tool-scope-strategy)
8. [Model Selection Strategy](#8-model-selection-strategy)
9. [Architecture Patterns](#9-architecture-patterns)
10. [Reference Repositories](#10-reference-repositories)
11. [Quick Checklist](#11-quick-checklist)

---

## 1. What Is a Subagent

A Subagent is an **isolated worker** that operates independently from the main conversation. Each subagent:

- Has its own **independent context window** (does not consume the main conversation's context)
- Can use skills and MCP tools
- Is automatically delegated by Claude based on its `description`, or explicitly invoked via `@agent-name`
- Returns a **single message** to the main agent upon completion

**Why subagents were created**: When the main agent researches a codebase, it reads large volumes of files. Stuffing all of that into the main context quickly exhausts the window. Subagents complete their work in an isolated context and return only a summary.

**Supporting evidence**: Chroma's context corruption study tested 18 models and found that performance degrades noticeably as context length increases; the decline is steeper when semantic similarity between the question and context content is low. This explains why cramming unrelated subtask information into the main context degrades quality — subagent context isolation directly addresses this problem. (Source: [Harness Engineering | HumanLayer](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents))

### Anthropic's Official Position: Most Scenarios Don't Need Multi-Agent

> Source: [When to use multi-agent systems (and when not to)](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them) (published 2026-01-23)

Anthropic explicitly states: **"Most teams don't need multi-agent systems."** Improving single-agent prompting often achieves equivalent results. Multi-agent systems typically consume **3-10x more tokens**.

Subagents are only worth using in these three scenarios:

| Scenario | Description | Example |
|----------|-------------|---------|
| **Context pollution** | A subtask brings in large volumes of irrelevant information, degrading main agent quality | Reading many files while researching a codebase |
| **Parallelizable work** | Multiple independent paths can be explored simultaneously, improving **thoroughness** (not speed) | Simultaneously reviewing security, performance, and types |
| **Specialization** | More than 15-20 tools, or conflicting behavioral modes are needed | Empathetic customer support vs. strict code review |

**Key principle: Split by context boundaries, not by roles.** Splitting work into planner → implementer → tester is an **anti-pattern** that creates a "telephone game" — every handoff loses information fidelity. Work should only be split when context can be truly isolated.

---

## 2. Core Problems: Black Box and Ephemeral

### Black Box Problem

| Problem | Description |
|---------|-------------|
| Invisible to user | Results returned by a subagent are **only visible to the main agent**, not to the user |
| No intermediate output | No transparent "thinking" output during execution |
| Hard to debug | No way to know which model the subagent used or which files it read |
| Results vanish | After context compression, subagent return values may be discarded |

### Ephemeral Problem

| Problem | Description |
|---------|-------------|
| No continuous conversation | Each invocation is a **brand new instance** with no memory |
| No follow-up | The main agent cannot ask follow-up questions based on previous results (unless using `SendMessage` to continue) |
| Results not reusable | The next conversation round cannot access the previous subagent's conclusions |

---

## 3. Solution: Result Persistence

Core idea: **Have the subagent write results to the filesystem**, making them accessible to the user, the main agent, and future conversations.

### Option 1: Write to a Conventional Directory (Recommended)

```
project-root/
├── .agents-output/           # subagent output root
│   ├── research/             # research results
│   │   └── 2026-03-23-auth-library-comparison.md
│   ├── review/               # code review results
│   │   └── 2026-03-23-auth-module-review.md
│   └── test/                 # test reports
│       └── 2026-03-23-integration-test-report.md
```

**Advantages**:
- Users can read the files directly
- The main agent can `Read` the results in subsequent conversations
- Git can track change history
- Can be added to `.gitignore` to avoid committing (as needed)

### Option 2: Use the Official `memory` Field

```yaml
---
name: research-agent
memory: project   # results stored in .claude/agent-memory/research-agent/ (the officially recommended default)
---
```

Memory directory mapping:
- `user` → `~/.claude/agent-memory/<agent-name>/` (shared across projects)
- `project` → `.claude/agent-memory/<agent-name>/` (project-level, can be version-controlled, **officially recommended default**)
- `local` → `.claude/agent-memory-local/<agent-name>/` (project-level, not version-controlled)
- Omitted → persistent memory not enabled

**Advantages**: Native support; the subagent automatically loads the first 200 lines of MEMORY.md on next invocation

### Option 3: Hook System Monitoring

```json
// settings.json
{
  "hooks": {
    "SubagentStop": [{
      "type": "command",
      "command": "echo '[SUBAGENT DONE]' && cat .agents-output/latest.md"
    }]
  }
}
```

Uses the `SubagentStop` hook to automatically output results to STDOUT when the subagent finishes.

### Option 4: SendMessage to Continue the Conversation

```
// The main agent can use SendMessage to follow up with a completed subagent
SendMessage(to: 'agent-id', message: 'Please add a security analysis')
```

Each Agent call returns an `agentId` that can be used to restore context and continue the conversation.

---

## 4. Subagent File Format

Place files in `~/.claude/agents/` (global) or `.claude/agents/` (project-level).

```yaml
---
name: agent-name              # required, lowercase with hyphens
description: when to use      # required, Claude uses this for automatic delegation
model: sonnet                 # optional: sonnet / opus / haiku / inherit (omit = inherit)
tools: Read, Grep, Glob       # optional: tool allowlist (omit = inherit all)
disallowedTools: Write, Edit  # optional: tool blocklist
maxTurns: 15                  # optional: maximum iteration count
permissionMode: default       # optional: default / acceptEdits / dontAsk / bypassPermissions / plan
memory: project               # optional: user / project / local (omit = disabled)
skills: my-skill              # optional: injected skill
background: false             # optional: run in background
effort: medium                # optional: reasoning effort level
isolation: worktree           # optional: git worktree isolation
hooks:                        # optional: lifecycle hooks
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate.sh"
mcpServers:                   # optional: MCP servers
  context7:
    type: stdio
    command: npx
    args: ["-y", "@anthropic-ai/context7-mcp"]
---

(Below is the system prompt — the agent's behavioral instructions)
```

### Complete Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier, lowercase letters + hyphens |
| `description` | Yes | Trigger condition description; determines when Claude automatically delegates |
| `model` | No | `sonnet`, `opus`, `haiku`, `inherit`, or a full model ID. **Defaults to `inherit` when omitted** (uses the same model as the main conversation) |
| `tools` | No | Tool allowlist (comma-separated); omit to inherit all |
| `disallowedTools` | No | Tool blocklist |
| `maxTurns` | No | Maximum agentic iteration count |
| `permissionMode` | No | `default` / `acceptEdits` / `dontAsk` / `bypassPermissions` / `plan`. **`bypassPermissions` skips all permission prompts — use with extreme caution** |
| `memory` | No | `user` / `project` / `local`. `user` → `~/.claude/agent-memory/<name>/` (cross-project), `project` → `.claude/agent-memory/<name>/` (version-controllable, officially recommended default), `local` → `.claude/agent-memory-local/<name>/` (not version-controlled). Omit to disable persistent memory |
| `skills` | No | Injected skill name |
| `mcpServers` | No | Scoped MCP servers |
| `hooks` | No | Lifecycle hooks |
| `background` | No | `true` to always run in background |
| `effort` | No | `low` / `medium` / `high` / `max` |
| `isolation` | No | `worktree` for git worktree isolation; the subagent works in an independent repo copy, auto-cleaned when there are no changes |

**Plugin limitation**: Subagents loaded from plugins **do not support** the `hooks`, `mcpServers`, and `permissionMode` fields — these are silently ignored.

---

## 5. Best Practice Design Templates

### Template: Research Agent (with File Output)

````yaml
---
name: researcher
description: >
  Use proactively when the user needs library comparison, technology research,
  or architecture investigation. Writes results to .agents-output/research/.
model: sonnet
tools: Read, Grep, Glob, WebSearch, WebFetch, Write,
       mcp__context7__resolve-library-id, mcp__context7__query-docs
maxTurns: 20
---

# Research Agent

You are an agent focused on technical research.

## Workflow

1. **Understand requirements**: Analyze the research topic and scope
2. **Multi-source collection**: Gather information using WebSearch, Context7, and codebase search
3. **Cross-validation**: Compare consistency across multiple sources
4. **Write report**: Produce a structured research document
5. **Save to file**: Write results to the `.agents-output/research/` directory

## Output Format

Write research results to `.agents-output/research/YYYY-MM-DD-<topic-slug>.md`:

```markdown
# <Research Topic>

> Research date: YYYY-MM-DD
> Scope: <brief description>

## Summary
<3-5 sentences of core findings>

## Detailed Analysis
<structured analysis content>

## Recommendations
<specific, actionable recommendations>

## References
<list of sources used>
```

## Completion Criteria

- [ ] At least 3 independent sources cross-validated
- [ ] Results written to `.agents-output/research/` directory
- [ ] Summary and file path returned to main agent
````

### Template: Code Review Agent (Read-Only)

````yaml
---
name: code-reviewer
description: >
  Use after writing or modifying code. Reviews for quality, security,
  performance, and best practices. Writes review report to .agents-output/review/.
model: sonnet
tools: Read, Grep, Glob, Write
maxTurns: 15
---

# Code Review Agent

You are a strict code reviewer.

## Review Dimensions

1. **Correctness**: Is the logic correct? Are edge cases handled?
2. **Security**: OWASP Top 10 checks
3. **Performance**: Any unnecessary computation or memory waste?
4. **Readability**: Are naming, structure, and comments clear?
5. **Immutability**: Does it follow immutable principles?

## Output Format

Write review results to `.agents-output/review/YYYY-MM-DD-<module-name>-review.md`:

```markdown
# Code Review: <Module Name>

> Review date: YYYY-MM-DD
> Scope: <file list>

## Issue Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |

## CRITICAL Issues
<issues that must be fixed>

## HIGH Issues
<strongly recommended fixes>

## Suggested Improvements
<optional improvement suggestions>
```

## Preventing Early Victory

You **must** complete all review dimensions before declaring the review done.
Do not draw conclusions from reviewing only a subset of files.
Every dimension must have a concrete result (pass or issue found) — none may be skipped.

## Return Content

When returning results to the main agent, include only:
1. Issue summary (count by severity)
2. One-line description of each CRITICAL and HIGH issue
3. File path to the full report
````

### Scenarios Not Suited for Subagents

The following tasks should remain in the **main conversation** — do not delegate them to a subagent:

| Scenario | Reason |
|----------|--------|
| **Planning and architecture design** | Requires back-and-forth communication with the user and real-time course corrections; the subagent's black-box nature creates information asymmetry |
| **Requirements clarification** | The user needs to see intermediate reasoning to judge whether the direction is correct |
| **Controversial technical decisions** | Requires user participation in trade-off discussions; a subagent should not make unilateral decisions |
| **Debugging complex issues** | Debugging is exploratory and requires real-time user feedback and context |

**Decision principle**: If the task's result needs the user to **review, discuss, or modify** before proceeding, don't use a subagent. Subagents are suited for tasks where you "give clear instructions and get back clear results."

Plan Mode (`/plan`) can be used in the main conversation for planning, so the user can fully participate in the discussion.

> **Anthropic's official position**: Splitting by work type (planner → implementer → tester) is an anti-pattern. The original text states this splitting "creates constant coordination overhead," producing a "telephone game" effect — every handoff loses information fidelity, and agents lack the decision-making context from the previous stage. Split by **context boundaries**, not by roles. ([Source](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them), 2026-01-23)

### Best Use Case for Subagents: Verification Agents

Anthropic officially recommends the **Verification Subagent** pattern, because:

- Verification only requires "the artifact + success criteria" — **no full build context needed**
- It is true blackbox testing where context can be fully isolated
- Success criteria are clear and require no back-and-forth discussion

This is precisely why this guide retains the **Research** and **Review** templates — they both fit the "clear input → clear output" characteristic.

#### Early Victory Problem

Anthropic specifically warns: verification agents tend to **run one or two tests and declare success**, skipping comprehensive validation.

**Mitigation strategies** (must be written into the subagent prompt):
- Use mandatory language: "You **must** run the full test suite before declaring pass"
- Specify concrete checks — don't write vague conditions like "confirm it works"
- Require **negative tests** (inputs that should fail)
- List all required checks in the completion criteria

---

## 6. Separating Examples from Skills

Subagent prompts should stay lean. **Code examples and style guides go in skills, not in the subagent**.

### Principle: Subagent Prompts Handle Only Four Things

```
Role definition → Workflow → Output format → Completion criteria
```

Examples and general knowledge bloat the prompt and waste context, and the model already knows how to write code.

### Why Use Skills Instead of Embedding in the Subagent

| Reason | Description |
|--------|-------------|
| **Reusable** | The same skill can be shared across multiple subagents (`skills: coding-style`) |
| **On-demand loading** | Tasks that don't need examples simply don't inject them, saving context |
| **Independent maintenance** | When examples need updating, change one skill file instead of N subagents |

### Skills Directory Structure

```
~/.claude/skills/
├── coding-style.md        # code style examples (immutable patterns, naming conventions, etc.)
├── output-format.md       # output report format examples
└── testing-patterns.md    # test writing examples
```

### Subagent On-Demand References

```yaml
---
name: code-reviewer
tools: Read, Grep, Glob, Write
skills: coding-style          # needs style guide for reviews
---
```

```yaml
---
name: researcher
tools: Read, Grep, Glob, WebSearch, Write
# research agent doesn't need coding-style — don't inject it
---
```

### The One Exception: Output Format Examples

**Output format examples** can stay in the subagent prompt, because they are the agent's own "work spec," not general knowledge:

```markdown
## Output Format

Write to `.agents-output/review/YYYY-MM-DD-<name>.md`:

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
```

This defines "what this agent's output looks like" — it belongs to the agent's own responsibility and is appropriate to keep in the prompt.

### Decision Rules

> For the complete "where does this content type go" decision matrix, see [Skills Best Practices Guide § 11. Skill and Subagent Collaboration](skills-best-practices.md#11-skill-and-subagent-collaboration).
>
> In brief: **Output format** stays in the Subagent prompt (the agent's own work spec); **code style/test patterns** go in Skills (general knowledge, shared across agents); **library documentation** is fetched on-demand via MCP.

---

## 7. Tool Scope Strategy

**Core principle: Principle of Least Privilege**

| Agent Type | Recommended Tools | Description |
|------------|-------------------|-------------|
| Read-only research/review | `Read, Grep, Glob` | Analyze without modifying |
| Research + external data | `Read, Grep, Glob, WebSearch, WebFetch` | Add network access |
| Research + report writing | `Read, Grep, Glob, WebSearch, Write` | Add file writing capability |
| Implementation/fixing | `Read, Write, Edit, Bash, Grep, Glob` | Full development capability |
| Coordination/orchestration | `Read, Glob, Grep, Bash` | No Write/Edit |
| MCP integration | Base tools + `mcp__<server>__*` | Add MCP as needed |

**Important**: Omitting the `tools` field = inheriting all tools. Always list explicitly.

---

## 8. Model Selection Strategy

```
Cost: Haiku <<< Sonnet < Opus

Opus  → Complex reviews, team coordination (for planning and architecture decisions in main conversation)
Sonnet → Primary development, research analysis, code review (researcher, code-reviewer)
Haiku  → High-frequency lightweight operations, quick exploration (explore, lint-checker)
```

**Cost-saving tip**: Set the environment variable `CLAUDE_CODE_SUBAGENT_MODEL` to globally control the subagent model.
Use Opus in the main conversation for complex reasoning; use Sonnet in subagents for focused tasks.

---

## 9. Architecture Patterns

### Pattern 1: Hub-and-Spoke (Recommended)

```
                    ┌─────────────┐
                    │ User Request │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Main Agent  │  ← Opus, handles routing and integration
                    │ (Hub)       │
                    └──┬───┬───┬──┘
                       │   │   │
              ┌────────┘   │   └────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌─────▼─────┐
        │ researcher │ │reviewer│ │  tester   │  ← Sonnet, each with a single responsibility
        │  (Spoke)   │ │(Spoke) │ │  (Spoke)  │
        └─────┬──────┘ └───┬────┘ └─────┬─────┘
              │            │            │
              ▼            ▼            ▼
        .agents-output/ .agents-output/ .agents-output/
        research/       review/         test/
```

**Characteristics**:
- The main agent handles routing decisions and result integration
- Each spoke does one thing only
- All results are written to the unified `.agents-output/` directory

### Pattern 2: Pipeline (Sequential) ⚠️ Use with Caution

> **Warning**: Pipeline is essentially splitting by work type. Anthropic officially states this "creates constant coordination overhead" and is an anti-pattern (see [Section 1](#1-what-is-a-subagent)). Every handoff loses context fidelity: the test agent doesn't know the implementation's design trade-offs, and the reviewer doesn't know the test coverage intent.
>
> **Only consider using when all of the following conditions are met**: each stage's input/output can be fully serialized to files (e.g., spec.md → code → report.md), and each stage does not need to trace back to the previous stage's reasoning. In most cases, Hub-and-Spoke with main conversation coordination is the better choice.

```
PM-spec → Architect → Implementer → Tester → Reviewer
   │          │           │            │          │
   ▼          ▼           ▼            ▼          ▼
 spec.md   adr.md      code        report.md  review.md
```

Chained via hooks; each agent's `SubagentStop` hook suggests the next step.

### Pattern 3: Parallel Workers

```javascript
// Launch multiple subagents simultaneously from the main agent
Agent({ type: "security-reviewer", prompt: "Review auth module" })
Agent({ type: "perf-reviewer", prompt: "Review cache module" })
Agent({ type: "type-checker", prompt: "Review utilities" })
// All three run in parallel, each writing to .agents-output/
```

---

## 10. Reference Repositories

### Official Documentation

- [Create custom subagents](https://code.claude.com/docs/en/sub-agents) — Official complete reference
- [Building multi-agent systems: when and how to use them](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them) — Anthropic's official guide on when to use (and not use) multi-agent, verification agent pattern, Early Victory Problem

### High-Star GitHub Repositories

| Repository | Stars | Highlights |
|------------|-------|------------|
| [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | ~9.6k | Curated collection of 127+ agents, well-categorized |
| [wshobson/agents](https://github.com/wshobson/agents) | — | Plugin architecture, 72 plugins, average 3.4 components |
| [vanzan01/claude-code-sub-agent-collective](https://github.com/vanzan01/claude-code-sub-agent-collective) | — | Hub-and-Spoke pattern, mandatory TDD, research caching |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | — | Comprehensive curation including skills, hooks, and plugins |
| [supatest-ai/awesome-claude-code-sub-agents](https://github.com/supatest-ai/awesome-claude-code-sub-agents) | — | Emphasizes single responsibility and security-first |
| [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) | ~100k | Largest-scale configuration project: 28 agents + 125 skills + 60 commands, covering 10+ languages. Excellent breadth but subagents lack result persistence, and places planning/architecture in subagents (black-box risk) |

### Further Reading

- [Best practices for Claude Code subagents (PubNub)](https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/)
- [Sub-Agent vs. Agent Team (Medium)](https://medium.com/data-science-collective/sub-agent-vs-agent-team-in-claude-code-pick-the-right-pattern-in-60-seconds-e856e5b4e5cc)
- [Claude Code Deep Dive - Subagents in Action (Medium)](https://medium.com/@the.gigi/claude-code-deep-dive-subagents-in-action-703cd8745769)
- [Subagent Parallel vs Sequential Patterns (claudefast)](https://claudefa.st/blog/guide/agents/sub-agent-best-practices)
- [Harness Engineering: leveraging Codex in an agent-first world (OpenAI)](https://openai.com/index/harness-engineering/) — OpenAI's agent engineering methodology, emphasizing infrastructure constraints on agent behavior
- [Skill Issue: Harness Engineering for Coding Agents (HumanLayer)](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents) — Includes Chroma context corruption study and ETH Zurich 138-file experiment data
- [Harness Engineering (Martin Fowler)](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html) — Harness Engineering analysis from a software engineering perspective

---

## 11. Quick Checklist

When designing a new subagent, verify each item:

- [ ] `name` and `description` are clear and specific (description drives automatic delegation)
- [ ] `tools` uses an allowlist, following the principle of least privilege
- [ ] `model` is chosen based on task complexity (don't use Opus for everything)
- [ ] System prompt includes a **clear output format**
- [ ] **Directory and naming conventions** for file output are specified
- [ ] **Completion criteria** (Definition of Done) are defined
- [ ] Return content is concise (summary + file path — don't include the full report)
- [ ] `maxTurns` is set to a reasonable upper limit to prevent runaway execution
