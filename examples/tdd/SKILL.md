---
name: tdd
description: >
  Test-driven development with red-green-refactor loop. Use when user wants
  to build features or fix bugs using TDD, mentions "red-green-refactor",
  wants integration tests, or asks for test-first development.
---

# Test-Driven Development

Tests verify behavior through public interfaces, not implementation details. Always use vertical slices (one test -> one implementation -> repeat), never horizontal slices.

## Additional resources

- For TDD philosophy and anti-patterns, see [reference/philosophy.md](reference/philosophy.md)
- For good/bad test examples, see [examples/tests.md](examples/tests.md)
- For mocking guidelines, see [examples/mocking.md](examples/mocking.md)
- For deep module design, see [reference/deep-modules.md](reference/deep-modules.md)
- For interface testability, see [reference/interface-design.md](reference/interface-design.md)
- For refactor candidates, see [reference/refactoring.md](reference/refactoring.md)

## Workflow

### 1. Planning

- [ ] Identify what interface changes are needed
- [ ] Identify which behaviors to test (prioritize)
- [ ] Design interfaces for testability (accept deps, return results, small surface)
- [ ] List the behaviors to test (not implementation steps)

### 2. Tracer Bullet

Write ONE test that confirms ONE thing about the system:

```
RED:   Write test for first behavior -> test fails
GREEN: Write minimal code to pass -> test passes
```

### 3. Incremental Loop

For each remaining behavior:

```
RED:   Write next test -> fails
GREEN: Minimal code to pass -> passes
```

- One test at a time
- Only enough code to pass current test
- Don't anticipate future tests

### 4. Refactor

After all tests pass:

- [ ] Extract duplication
- [ ] Deepen modules (move complexity behind simple interfaces)
- [ ] Run tests after each refactor step

**Never refactor while RED.** Get to GREEN first.

## Checklist Per Cycle

- [ ] Test describes behavior, not implementation
- [ ] Test uses public interface only
- [ ] Test would survive internal refactor
- [ ] Code is minimal for this test
- [ ] No speculative features added

## Gotchas

- **Iterate this section**: After each TDD session, append new gotchas here
