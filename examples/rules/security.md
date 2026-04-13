# Security Guidelines

Security rules keep stronger enforcement language — the cost of a miss is high.

## Pre-Commit Security Checks

When committing code that handles user input, auth, or external data, verify the relevant items:
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All user inputs validated
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized HTML)
- [ ] CSRF protection enabled
- [ ] Authentication/authorization verified
- [ ] Rate limiting on all endpoints
- [ ] Error messages don't leak sensitive data

## Secret Management

- Store secrets in environment variables or a secret manager — never in source code
- Validate that required secrets are present at startup
- Rotate any secrets that may have been exposed

## Safety Boundaries for Destructive Operations

Confirm with the user before executing operations that are hard to reverse: deleting files/branches, force-push, sending messages to external services, modifying shared infrastructure.

Why: Claude is capable enough to execute multi-step destructive actions autonomously. Explicit confirmation prevents costly mistakes.

## Security Response Protocol

When a security issue is found:
1. Stop current work immediately
2. Assess severity and impact scope
3. Fix critical issues before continuing
4. Rotate any exposed secrets
5. Review the codebase for similar issues

> **Tip**: If you have a dedicated security scanning agent or tool (e.g., Semgrep, CodeQL), integrate it into step 2 for automated assessment.
