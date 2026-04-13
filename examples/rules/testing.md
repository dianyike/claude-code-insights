# Testing Requirements

These apply to production code. For documentation, config, and exploratory work, scope testing to what's relevant.

## Coverage Target: Aim for 80% where it is a meaningful measure

Test types to consider based on the change:
- **Unit Tests** — Individual functions, utilities, components
- **Integration Tests** — API endpoints, database operations
- **E2E Tests** — Critical user flows (framework chosen per language)

Use the test types that match the scope of your change — not every change needs all three, and coverage should not drive unnecessary test scaffolding.

## Test-Driven Development

When building new features or fixing bugs with clear expected behavior, follow this workflow:
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
