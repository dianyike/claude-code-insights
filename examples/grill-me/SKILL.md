---
name: grill-me
description: >
  Interview the user relentlessly about a plan or design until reaching
  shared understanding, resolving each branch of the decision tree.
  Use when user wants to stress-test a plan, get grilled on their design,
  or mentions "grill me".
allowed-tools: Read, Grep, Glob, Write
---

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one.

If a question can be answered by exploring the codebase, explore the codebase instead.

## Interrogation Dimensions

For each design decision, probe these dimensions in order. Skip any that are clearly not applicable.

### 1. Risk Tier Classification

Before diving into details, establish the risk tier first — it determines how strict everything else must be.

- Is this Critical (auth, payments, data migration), Standard (features, APIs), or Exploratory (prototype, spike)?
- If Exploratory: what is the tech-debt remediation date? Open-ended "later" is not acceptable.
- If the user claims Exploratory but the scope touches Critical systems, challenge that classification.

### 2. Boundary & Integration

- Where does external data enter? Are all boundaries schema-validated (no YOLO probing)?
- Are you using strongly-typed SDKs or raw fetch/curl?
- Does this duplicate logic that already exists in a shared utility? Search before creating.

### 3. Testability

- How will this be verified? Define the verification method before discussing implementation.
- For Critical/Standard tier: what does the RED test look like? Can you describe the failing test first?
- Is 80% coverage realistic for this design, or does the architecture make it hard to test?

### 4. Security Surface

- Does this introduce new user input paths? How are they validated?
- Any new secrets, tokens, or credentials? Where are they stored?
- Does this change auth/authorization boundaries?

### 5. Failure Modes

- What happens when the external dependency is down?
- What's the rollback plan?
- For side-effects (deploy, send, delete): is there a confirmation gate, or could automation trigger it accidentally?

## Behavior Rules

- Ask ONE question at a time. Wait for the answer before moving to the next branch.
- If the user's answer reveals a contradiction or gap, stop and surface it immediately — do not silently proceed.
- When a branch is fully resolved, summarize the decision and move to the next.
- After all branches are resolved, produce a final summary and write it to a decision record file (see Output section below).

## Output

When all branches are resolved, write a decision record to `docs/decisions/YYYY-MM-DD-<topic>.md`.

- Use the template at [templates/decision-record.md](templates/decision-record.md)
- If `docs/decisions/` does not exist, create it
- Ask the user to confirm the filename before writing

## Completion Criteria

- [ ] All interrogation dimensions relevant to this design have been probed
- [ ] Each branch resolved with a concrete decision (not "we'll figure it out later")
- [ ] Contradictions and gaps surfaced and addressed
- [ ] Decision record written to `docs/decisions/` and confirmed by user

## Gotchas

- **Iterate this section**: After each grill session, append new gotchas here
