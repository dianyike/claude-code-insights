# Golden Rules

Enforceable constraints — apply with pragmatism (see `pragmatism.md` for risk-tier scoping).

## 1. Prefer Shared Tool Libraries

Centralize critical logic when adding new code — search the existing codebase before creating any new utility. If a shared utility exists, use it; if it's missing functionality, extend it.

This rule governs new code. When fixing existing code, duplication you notice in passing is not a trigger to refactor — defer to Rule #3. Extending an existing utility is only in scope if the extension itself falls within what the user asked for. If the extension would exceed the user's request, defer to Rule #3 and inline the logic instead.

Search depth should scale with change size. A one-line fix does not warrant a repo-wide audit; reach for shared logic that the task already touches, and stop there.

Why: Duplicated logic across agents/skills/modules drifts out of sync and creates subtle bugs.

**Violation signal**: Two or more files containing functionally identical code.

## 2. Validated External Access

Route all external data access through schema validation or strongly-typed SDKs. Prefer typed SDK clients over raw HTTP calls. Fail fast on unexpected response shapes.

Why: Unvalidated hand-crafted payloads to external APIs are a top source of runtime surprises and security issues.

**Violation signal**: Raw `fetch`/`curl` to external services without schema validation on both request and response.

## 3. Only Do What's Asked

Implement exactly what was requested. A bug fix is a bug fix — skip the surrounding cleanup, extra configurability, and speculative abstractions. Three similar lines are better than a premature helper.

Why: Overengineering is the #1 trap with capable models. Extra files, extra abstractions, and "while I'm here" improvements create review burden and unintended side effects.

```
# Good
User: "Fix the null check in parseConfig"
→ Fix the null check. Done.

# Bad
User: "Fix the null check in parseConfig"
→ Fix the null check + refactor the module + add JSDoc + create a utility

# Borderline — how to decide
User: "Add a retry to the API call in fetchUser"
→ Add the retry. Don't also add circuit breaker, timeout config,
  or retry-count parameter "while you're there."
→ If the retry without a timeout creates a real issue (security/correctness),
  flag it to the user — don't silently skip it, but don't silently add it either.
```

## 4. Give Context With Instructions

When writing prompts, instructions, or rules — explain *why*, not just *what*. Use 3-5 examples when you need precise format control.

Why: Rules without rationale get pattern-matched and misapplied in adjacent cases; examples only improve format reliability when they resolve a specific ambiguity, otherwise they bias the model toward superficial imitation.
