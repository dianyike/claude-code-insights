# Testing Requirements

These apply to production code. For documentation, config, and exploratory work, scope testing to what's relevant. When the user hasn't explicitly requested tests, apply the risk tier from `pragmatism.md` — Critical changes warrant proactive test coverage, Standard changes should flag the gap to the user, Exploratory work can defer.

## Coverage Is a Diagnostic, Not a Target

Ask: "If this code breaks in production, would the existing tests catch it?" If no, add the missing test — regardless of current coverage percentage. If yes, don't write a test just to move a number.

Test types to consider based on the change:
- **Unit Tests** — Individual functions, utilities, components
- **Integration Tests** — API endpoints, database operations
- **E2E Tests** — Critical user flows (framework chosen per language)

Use the test types that match the scope of your change — not every change needs all three, and coverage should not drive unnecessary test scaffolding.

Why: A coverage number can be gamed by testing trivial paths. The "would tests catch a real break" question directly targets the purpose of testing.

## Test-Driven Development

When building new features or fixing bugs with clear expected behavior, follow this workflow. Skip TDD for exploratory work where the behavior is still being discovered — write tests after the design stabilizes.

1. Write the test first (RED — it should fail)
2. Write minimal implementation (GREEN — it should pass)
3. Refactor (IMPROVE)

## Test Real Logic, Not Hardcoded Answers

Tests should verify the implementation's actual behavior, not mirror hardcoded expected values. If you can swap the implementation for a no-op and tests still pass, the tests are broken.

Why: Hardcoded test expectations create false confidence. They pass today but miss real regressions.

```
# Good: tests the parsing logic
assert parse_config('{"port": 3000}').port == 3000

# Bad: hardcoded expected output copied from implementation
assert result == '{"port":3000,"host":"localhost","debug":false}'
```

## Troubleshooting Test Failures

1. Check test isolation
2. Verify mocks are correct
3. Fix the implementation, not the tests (unless the tests are wrong)
