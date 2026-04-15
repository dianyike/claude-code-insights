---
name: write-prd
description: >
  Write a structured PRD from design decisions, rough ideas, or conversation context.
  Use when user wants to write a PRD, create requirements, document a feature spec,
  or bridge design decisions into a product requirements document. Bridges the gap
  between design exploration (grill-me) and implementation planning (prd-to-plan).
allowed-tools: Read, Write, Grep, Glob
---

# Write PRD

Turn design decisions, rough ideas, or conversation context into a structured PRD that prd-to-plan can consume directly.

## Workflow

### 1. Gather context

Check what's already available before asking the user to repeat themselves:

- Look for decision records in `docs/decisions/` — these are grill-me outputs
- Check if the user pasted or referenced any existing design notes
- Scan conversation history for requirements already discussed

If context is thin, interview the user (see [Interview Guide](#interview-guide)).

### 2. Interview Guide

Fill gaps the existing context doesn't cover. Ask **exactly one blocking question per turn** — do not batch multiple questions into a single response. This matters because batching overwhelms the user and produces shallow answers; one focused question gets a thoughtful response.

**Must answer before drafting** (block on these, ask in order):
1. Who is the target user and what's their pain?
2. What does "done" look like? (the success state, not the feature list)
3. What is explicitly out of scope? (non-goals prevent scope creep)

**Ask if not inferrable from context** (one per turn):
- What are the priority tiers — what's P0 vs P1 vs nice-to-have?
- Are there hard technical constraints (existing APIs, schema contracts, third-party limits)?
- What are the non-functional requirements (performance, security, compliance)?
- How will success be measured?

Stop interviewing once you have enough to draft. Don't exhaust the user — you can mark gaps as Open Questions in the PRD.

### 3. Draft the PRD

Use the template at [templates/prd.md](templates/prd.md). Key principles:

- **User stories are the spine** — prd-to-plan maps phases to user stories, so every requirement must trace back to at least one story. If a requirement has no user story, either write one or question whether it belongs.
- **Non-goals are as important as goals** — they prevent scope creep during prd-to-plan and tdd phases. Be specific: "not building admin dashboard" is better than "keeping it simple."
- **Prioritize ruthlessly** — P0/P1/P2 tiers. If everything is P0, nothing is. Push the user to make hard choices.
- **Link decision records** — if grill-me decision records exist, reference them in the References section so context isn't lost.
- **Stay at product and system-contract level** — PRDs describe *what* the system promises, not *how* it's built. Do not include implementation mechanisms such as cookie types (`httpOnly`), SDK pinning strategies, function names, or file paths. Those belong in the implementation plan, not the PRD.
- **Traceability** — every functional requirement must trace back to a user story or a decision in the decision record. If you can't trace it, either write a user story for it or remove the requirement.

### 4. Review with user

Present the draft and explicitly ask:

- Are the non-goals correct? (most common source of later scope disputes)
- Do the P0 user stories capture the minimum viable feature?
- Any missing technical constraints?

Iterate until the user approves.

### 5. Write the PRD file

Create `docs/prds/` if it doesn't exist. Write to `docs/prds/YYYY-MM-DD-<feature-name>.md`.

- Ask the user to confirm the filename before writing
- If decision records from grill-me exist, add them to the References section

### 6. Delegated / Eval Mode

If this skill is being executed by a subagent, eval harness, or any caller that provides an explicit output path or workspace, distinguish between **draft artifacts** and the **canonical PRD file**:

- **Draft artifacts**: Write the PRD draft and any handoff notes to the caller-provided output location
- **Canonical PRD file**: Only write `docs/prds/YYYY-MM-DD-<feature-name>.md` after explicit user confirmation of the filename in the current conversation
- **No silent promotion**: Do not treat a draft written to an eval workspace as the canonical PRD
- **Handoff clarity**: If canonical write is blocked on confirmation, say so explicitly and include the proposed filename/path

When operating in delegated/eval mode:

- Prefer saving `prd-draft.md` plus a short `process-log.md` or handoff note
- Preserve unresolved questions so the parent agent can continue the user conversation
- If the caller gives both an output directory and a confirmed canonical path, write both: the draft artifact for evaluation and the canonical PRD for the repo

## Completion Criteria

- [ ] Problem statement clearly articulates user pain (not solution)
- [ ] Every functional requirement traces to a user story
- [ ] Non-goals section is non-empty and specific
- [ ] User stories have priority tiers (P0/P1/P2)
- [ ] User approved the final PRD
- [ ] PRD file written to `docs/prds/` with confirmed filename
- [ ] In delegated/eval mode, draft artifacts were written to the caller-provided output path and canonical write was deferred unless explicitly confirmed

## Gotchas

- **Do not batch questions**: The interview step says "one question per turn" for a reason. Batching 3 questions into one message produces shallow answers — the user skims and gives one-line replies. One focused question gets a thoughtful response. This was confirmed in eval iteration 1 where the skill sent 3 questions at once despite the instruction.
- **Do not leak implementation details into PRDs**: Technical constraints like "httpOnly cookies", "SDK versions pinned", or specific API endpoint paths are implementation-level concerns. A PRD should say "session tokens must not be accessible to client-side scripts" (system contract), not "use httpOnly cookies" (implementation). This regression was caught in eval iteration 1 — the with-skill output was *more* implementation-heavy than the without-skill baseline.
- **Iterate this section**: After each PRD session, append new gotchas here
