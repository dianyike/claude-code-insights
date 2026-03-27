---
name: skill-name
description: >
  Brief description of capability.
  Use when [specific trigger keywords users would say].
# --- Invocation control (uncomment ONE that applies) ---
# disable-model-invocation: true   # Has side effects — user-only trigger
# user-invocable: false             # Background knowledge — Claude-only trigger
# --- Subagent isolation (uncomment if needed) ---
# context: fork
# agent: Explore
# --- Tool restrictions (set for task skills) ---
# allowed-tools: Read, Grep, Glob
# --- Optional ---
# argument-hint: [argument-name]
# model: sonnet
# effort: medium
---

# Skill Name

## Goal

[What this skill achieves — constrain the objective, not the step sequence]

## Workflow

[High-level steps. Use goal-oriented language, not rigid commands.
Let Claude adapt order based on context. Explain *why* each step matters.]

1. ...
2. ...
3. ...

## Output format

[Define what the output looks like — file path, structure, format]

## Completion criteria

- [ ] [Specific, verifiable condition 1]
- [ ] [Specific, verifiable condition 2]
- [ ] [Specific, verifiable condition 3]

## Additional resources

- For detailed reference, see [reference/details.md](reference/details.md)

## Validation (optional)

[For skills with objectively verifiable outputs, define how to test them.
Not all skills need this — subjective or reference-only skills can skip it.]

- Test prompt 1: "[realistic user request]" — expect [outcome]
- Test prompt 2: "[edge case request]" — expect [outcome]

## Gotchas

- **Iterate this section**: After each use, append new gotchas discovered during execution
