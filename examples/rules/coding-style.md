# Coding Style

## Immutability

Create new objects instead of mutating existing ones.

Why: Immutable data prevents hidden side effects, makes debugging easier, and enables safe concurrency.

```
// Pseudocode
update(original, field, value) → returns new copy with change  ✓
modify(original, field, value) → changes original in-place     ✗
```

## File Organization

Prefer high cohesion and low coupling. Organize by feature/domain, not by type. When a file grows past ~800 lines and has clearly separable concerns, consider splitting — but only split for real reasons, not to hit a line count target.

## Error Handling

Handle errors explicitly at every level:
- Provide user-friendly error messages in UI-facing code
- Log detailed error context on the server side
- Surface errors visibly — silent swallowing hides real problems

## Input Validation

Validate at system boundaries (user input, external APIs, file content):
- Use schema-based validation where available
- Fail fast with clear error messages

For external API access specifically (typed SDKs, response schema validation), see Golden Rule #2.

Why: Internal code and framework guarantees can be trusted. Validation effort belongs at the edges where untrusted data enters.

## Syntax Preferences

- Prefer `function` keyword over arrow functions for components and top-level functions
- Use if/else or switch instead of nested ternaries
- Comments explain **why**, not what (skip `// increment counter`)

