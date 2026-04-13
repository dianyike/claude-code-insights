# Workflow Rules

## Language Rules

- Write **rule files**, **subagents**, **MCP configs**, **claude.md**, and **skills** in **English**
- Reply to the user in **Traditional Chinese (zh-TW)**
- All frontend-facing text uses **Traditional Chinese (zh-TW)**

## Critical Thinking

Analyze intent and logic before implementing. When requirements contain contradictions or ambiguity, surface them immediately with:
1. What the conflict is
2. Why it matters
3. Suggested alternatives

Why: Silently guessing through unclear requirements creates rework. Catching issues early saves everyone time.

## Read Before You Write

Read the relevant code before proposing changes. When referencing functions, files, or APIs — verify they exist first.

Why: Claude is capable enough to sound confident about code that was renamed or removed. Grounding in the actual codebase prevents hallucinated suggestions.

```
# Good
Read the file → understand the structure → edit with confidence

# Bad
Assume the function signature → write code that doesn't compile
```

## Concise Responses

Lead with the answer or action. Skip environment explanations, definitions, and background context the user already knows.

## When Commands Fail

Read the error → analyze root cause → fix. Follow the diagnostic chain.

**Rule of Three**: if a retry fails twice, stop and perform root-cause analysis before the next attempt. Blind retries waste tokens and often make things worse.

## Think Before Act

For multi-file or non-trivial changes, outline your plan in 3 bullet points before editing. Skip this for single-line fixes or obvious changes.

## Verification First

Run the smallest relevant verification (test, build, lint, or manual check) before reporting "Done." For pure documentation or analysis tasks, a re-read of the output is sufficient.

## Clean Up After Yourself

Remove temporary files, debug logs, and scratch code when the task is complete. Add a "clean up temp files after task" step to your plan when generating intermediate artifacts.

Why: Leftover temp files accumulate and confuse future sessions.

## Git for State Awareness

Use `git status` and `git diff` to stay aware of what has changed. Only create commits when the user requests them.

Why: Git is more reliable than session memory for tracking state, but unsolicited commits create noise and side effects.

