---
name: prd-to-plan
description: >
  Turn a PRD into a multi-phase implementation plan using tracer-bullet
  vertical slices, saved as a local Markdown file in ./plans/. Use when
  user wants to break down a PRD, create an implementation plan, plan
  phases from a PRD, or mentions "tracer bullets".
allowed-tools: Read, Write, Grep, Glob
---

# PRD to Plan

Break a PRD into a phased implementation plan using vertical slices (tracer bullets). Output is a Markdown file in `docs/plans/`.

## Process

### 1. Confirm the PRD is in context

The PRD should already be in the conversation. If it isn't, ask the user to paste it or point you to the file.

### 2. Explore the codebase

If you have not already explored the codebase, do so to understand the current architecture, existing patterns, and integration layers.

### 3. Identify durable architectural decisions

Before slicing, identify high-level decisions that are unlikely to change throughout implementation:

- Route structures / URL patterns
- Database schema shape
- Key data models
- Authentication / authorization approach
- Third-party service boundaries

These go in the plan header so every phase can reference them.

### 4. Draft vertical slices

Break the PRD into **tracer bullet** phases. Each phase is a thin vertical slice that cuts through ALL integration layers end-to-end, NOT a horizontal slice of one layer.

- Each slice delivers a narrow but COMPLETE path through every layer (schema, API, UI, tests)
- A completed slice is demoable or verifiable on its own
- Prefer many thin slices over few thick ones
- Do NOT include specific file names, function names, or implementation details that are likely to change as later phases are built
- DO include durable decisions: route paths, schema shapes, data model names

### 5a. Optional Codex review

For complex, high-risk, or multi-phase plans, run an **optional review pass** before presenting the breakdown to the user. This is a review step, not a replacement for the planning skill.

Use this when any of the following are true:

- The feature touches auth, payments, migrations, or external integrations
- The PRD still has important open questions or architectural uncertainty
- The phase breakdown is large enough that merge/split mistakes are likely
- Multiple engineers will implement the plan and phase boundaries need to be defensible

Review focus:

- Is each phase a true vertical slice rather than a horizontal layer split?
- Are all PRD user stories covered by at least one phase?
- Are there hidden sequencing or dependency mistakes between phases?
- Did the plan leak too much implementation detail?
- Should any phases be merged or split further?

If Codex or another review agent is available, use the prompt patterns in [reference/codex-review.md](reference/codex-review.md). If the review finds material issues, revise the draft before showing it to the user.

### 5b. Quiz the user

Present the proposed breakdown as a numbered list. For each phase show:

- **Title**: short descriptive name
- **User stories covered**: which user stories from the PRD this addresses

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Should any phases be merged or split further?

Iterate until the user approves the breakdown.

### 6. Write the plan file

Create `./plans/` if it doesn't exist. Write the plan as a Markdown file named after the feature (e.g. `./plans/user-onboarding.md`).

- Use the template at [templates/plan.md](templates/plan.md)
- Ask the user to confirm the filename before writing

## Completion Criteria

- [ ] All PRD user stories mapped to at least one phase
- [ ] Each phase is a vertical slice (touches all layers end-to-end)
- [ ] User approved the phase breakdown
- [ ] Plan file written to `./plans/` with confirmed filename
- [ ] If an optional review pass was used, material findings were either incorporated or surfaced to the user

## Gotchas

- **Codex review is a review pass, not the main planner**: The plan should still be authored locally, then challenged. If you outsource the whole planning step to the reviewer, you lose control of the phase structure and the review becomes less meaningful.
- **Iterate this section**: After each planning session, append new gotchas here
