# Pragmatism (Risk-Based Flexibility)

Meta-rule that governs how strictly other rules are enforced. Without this layer, rules are either fully obeyed (too slow) or fully ignored (too sloppy).

## Risk Tiers

| Tier | Scope | Rule Enforcement |
|------|-------|-----------------|
| **Critical** | Core business logic, payment flows, auth/identity, data migrations | Apply rules at maximum strictness. Any exception should be explicit and justified. |
| **Standard** | Product features, API endpoints, shared libraries | Full enforcement with documented exceptions allowed |
| **Exploratory** | Prototypes, internal tools, one-off scripts, spikes | Testing and coverage requirements may be relaxed, but tag as tech debt |

## Rule Priority (when rules conflict)

When two rules point in different directions, resolve by this order:

1. **Security & Safety** — non-negotiable baseline, never relaxed regardless of tier or user request
2. **User intent** — the user's explicitly stated goal and scope defines the playing field
3. **Correctness** — no bugs *within the scope the user defined*. This is not a license to handle every edge case the user didn't ask about
4. **Code quality** — readability, patterns, naming, style
5. **Coverage / metrics** — informational, not a target

When choosing a lower-priority rule over a higher one, leave a reason at the decision site. This uses the same audit trail as the Exception Protocol below — both are cases of "deviation from the default needs a record."

Why: Without explicit priority, AI agents systematically default to the most conservative rule (typically security or correctness), which produces over-engineering — the exact failure mode Golden Rule #3 exists to prevent.

### Worked Examples

While fixing a bug in an internal function, you notice the boundary layer lacks input validation. Apply priorities: is it a security issue? If yes, #1 wins — fix it. If it's just code quality, #2 (user intent) beats #4 (code quality) — leave it, optionally flag to the user.

User says: "I know this edge case won't happen in our setup, skip it." Apply priorities: #2 (user intent) beats #3 (correctness) — don't handle the edge case. Exception: if the "edge case" is actually a security hole, #1 overrides — flag it, don't silently skip.

## Exception Protocol

When skipping a rule, leave a `<!-- TECH-DEBT: rule=<rule>, reason=<why> -->` comment at the deviation site so it's visible and traceable.

When modifying a file that contains TECH-DEBT comments, surface them to the user and ask whether to address them now. This amortizes tracking cost into the read-before-write workflow instead of requiring a separate sweep ritual.

Why: Deviations without records are invisible — they look like mistakes instead of intentional trade-offs. Periodic grep rituals get forgotten; surfacing debt when you're already touching the file is zero-marginal-cost.
