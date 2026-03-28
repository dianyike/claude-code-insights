# PRD: Login Redesign

- **Date**: 2026-03-28
- **Author**: Product Team
- **Status**: Approved
- **Decision Records**: `docs/decisions/login-redesign-decision.md`

## Problem Statement

Mobile users drop out of the current login flow at a high rate because the experience is slow, multi-step, and unclear when errors occur. This creates lost conversions and repeated support burden for users who should be able to regain access quickly.

## Goals & Non-Goals

### Goals

- Reduce mobile login drop-off from 40% to below 15%
- Let returning users complete login through the fastest acceptable path for their situation
- Preserve current security expectations while removing unnecessary user-facing friction

### Non-Goals

- Redesigning account registration
- Replacing the current identity provider
- Building an admin console for authentication management
- Shipping biometric login in v1

## User Stories

### P0 (Must Have)

- As a mobile user, I want to log in from a single screen, so that I can finish authentication without getting lost in multiple steps.
- As a returning user, I want to use Google or Apple sign-in, so that I can log in with minimal typing.
- As a returning user, I want to request a magic link, so that I can log in without remembering my password.
- As a user who makes a mistake, I want clear error messages, so that I know exactly what to fix.

### P1 (Should Have)

- As a user, I want a fallback path when a social provider is unavailable, so that I am not blocked from accessing my account.
- As a user on a weak network, I want resend guidance for magic links, so that I am not stuck waiting without feedback.
- As a user, I want risk checks to happen with less friction than CAPTCHA, so that normal logins feel fast.

### P2 (Nice to Have)

- As a returning user, I want a remember-me option, so that I do not have to log in every session.

## Functional Requirements

### Login experience

- FR-1: Provide a single-screen login entry point for mobile users.
- FR-2: Support email/password, Google sign-in, Apple sign-in, and magic link from the same entry point.
- FR-3: Show clear, actionable error states for invalid credentials, expired links, and temporary lockouts.

### Social login

- FR-4: Integrate Google sign-in through the existing identity provider boundary.
- FR-5: Integrate Apple sign-in through the existing identity provider boundary.
- FR-6: If a social provider is unavailable, present a fallback path to email/password login.

### Magic link

- FR-7: Let users request a magic link to a registered email address.
- FR-8: Let users understand whether to retry, resend, or check spam if the email is delayed.

### Security and abuse controls

- FR-9: Replace visible CAPTCHA with lower-friction risk scoring.
- FR-10: Rate-limit repeated failed attempts and communicate lockout state to the user.

## Non-Functional Requirements

- **Performance**: Login entry should feel responsive on mobile and avoid unnecessary page transitions.
- **Security**: The solution must preserve current server-side token validation and current authentication trust boundaries.
- **Scalability**: The design must support increased social-login adoption without introducing a separate auth stack.
- **Observability**: The team must be able to track login success, drop-off, provider failure, and lockout events.

## Technical Constraints

- Existing identity provider remains the system of record
- Current auth boundaries and token validation model remain in place
- Rate limiting is required for repeated failures
- The login redesign must fit into the existing mobile web product

## Success Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Mobile login drop-off | 40% | < 15% | Funnel analytics |
| Social login adoption | 0% | > 40% | Login method mix |
| Login support complaints | High | Lower than current baseline | Support categorization |

## Open Questions

- Should remember-me remain P2 or be deferred entirely?
- Which risk scoring provider will back the lower-friction abuse checks?
- What should the magic-link expiration window be?

## References

- `docs/decisions/login-redesign-decision.md`
