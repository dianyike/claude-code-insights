# Pragmatism (Risk-Based Flexibility)

Meta-rule that governs how strictly other rules are enforced. Without this layer, rules are either fully obeyed (too slow) or fully ignored (too sloppy).

## Risk Tiers

| Tier | Scope | Rule Enforcement |
|------|-------|-----------------|
| **Critical** | Core business logic, payment flows, auth/identity, data migrations | Apply rules at maximum strictness. Any exception should be explicit and justified. |
| **Standard** | Product features, API endpoints, shared libraries | Full enforcement with documented exceptions allowed |
| **Exploratory** | Prototypes, internal tools, one-off scripts, spikes | Testing and coverage requirements may be relaxed, but tag as tech debt |

## Exception Protocol

When skipping a rule, leave a `<!-- TECH-DEBT: rule=<rule>, reason=<why>, due=<YYYY-MM-DD> -->` comment at the deviation site so it's visible and traceable.

Why: Deviations without records are invisible — they look like mistakes instead of intentional trade-offs.
