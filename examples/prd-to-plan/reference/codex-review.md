# Codex Review Patterns for PRD-to-Plan

Reference prompt patterns for using Codex as an **optional review pass** on a phase breakdown.

This is adapted from the Codex review style used in the security-reviewer example, but scoped to implementation planning rather than security auditing.

If you are using Codex MCP directly, call `mcp__codex__codex` with one of the prompts below.

The `[INSERT ... HERE]` placeholders are working slots for the planning agent or skill runner to fill automatically during execution. They are not meant for the end user to paste manually in normal skill usage.

## When to Use

Use this only after you already have a first-pass phase breakdown.

Good fits:

- Complex features with several integration boundaries
- High-risk work (auth, billing, migrations, multi-team changes)
- Plans with 4+ phases where merge/split mistakes are easy to make
- PRDs that still contain open questions or ambiguous priorities

Avoid for:

- Tiny features where review cost exceeds risk
- Exploratory spikes where the plan is intentionally provisional

## Review Prompt: Phase-Quality Audit

Use when you want Codex to challenge the current phase draft.

```text
You are reviewing an implementation plan derived from a PRD.

Your job is to critique the phase breakdown, not to rewrite the plan from scratch.

For each finding, provide:
1. Finding type: coverage gap / sequencing issue / horizontal slice / over-detailed plan / merge-split issue
2. Exact phase(s) affected
3. Why this is a problem
4. The minimal correction

If you find no issues in a category, explicitly say so.

Review checklist:
- Each phase must be a demoable vertical slice
- Every PRD user story must map to at least one phase
- Earlier phases should establish only the minimum durable decisions needed by later phases
- The plan should not leak brittle implementation details like file names or low-level function design
- Merge/split advice should preserve tracer-bullet sequencing

PRD:
---
[INSERT PRD HERE]
---

Current phase breakdown:
---
[INSERT PHASE BREAKDOWN HERE]
---
```

## Review Prompt: Coverage and Sequencing Check

Use when you specifically want Codex to verify user-story mapping and order of execution.

```text
Review this implementation plan for two things only:

1. Coverage: which PRD user stories are missing, duplicated, or deferred too late?
2. Sequencing: which phases depend on decisions or infrastructure that have not been established yet?

Return:
- Coverage findings
- Sequencing findings
- Whether any phase should be merged or split
- A short revised phase order if needed

PRD user stories:
---
[INSERT USER STORIES HERE]
---

Current phases:
---
[INSERT PHASES HERE]
---
```

## Review Prompt: Keep the Plan High-Level

Use when the phase draft is drifting into implementation detail.

```text
Review this plan for implementation-detail leakage.

Flag any phase content that is too low-level for a planning document, such as:
- specific file paths
- function names
- class names
- library-specific remediation steps
- low-level API call sequences

For each flagged item:
1. Quote the problematic detail briefly
2. Explain why it is too implementation-specific
3. Suggest a higher-level rewrite that preserves planning intent

Plan:
---
[INSERT PLAN HERE]
---
```

## Usage Notes

- Keep the review bounded. Ask Codex to critique the current draft, not to generate a brand-new plan unless the draft is unsalvageable.
- Treat Codex findings as adversarial feedback, not automatic truth. The planning agent still decides what to incorporate.
- Surface unresolved review disagreements to the user instead of silently picking one side.
- When using Codex MCP directly, send the completed prompt via `mcp__codex__codex`; if you need a follow-up on the same review, continue in the same thread.
