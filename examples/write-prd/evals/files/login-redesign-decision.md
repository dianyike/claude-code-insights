# Login Redesign

- **Date**: 2026-03-28
- **Risk Tier**: Standard
- **Status**: Accepted

## Context

Current login flow has a 40% drop-off rate on mobile. Users complain about too many steps and confusing error messages. We need to simplify the flow while maintaining security standards.

## Decisions

- [x] Use single-page login form instead of multi-step wizard — reduces friction, drop-off data shows step 2 is where we lose users
- [x] Support social login (Google, Apple) alongside email/password — user research shows 60% prefer social login on mobile
- [x] Replace CAPTCHA with invisible risk scoring — CAPTCHA is the #2 complaint after "too many steps"
- [x] Use magic link as primary passwordless option — simpler than TOTP for the target audience

## Boundaries & Constraints

- Must integrate with existing OAuth2 provider (Keycloak)
- Session tokens stored in httpOnly cookies, not localStorage
- Rate limiting: 5 failed attempts → 15 min cooldown
- Social login SDK versions pinned to avoid breaking changes

## Test Strategy

- RED test: login form renders, submits credentials, redirects to dashboard
- Coverage target: 85% for auth module

## Security Considerations

- All auth endpoints behind HTTPS only
- CSRF tokens on all form submissions
- Social login tokens validated server-side, never trusted from client
- Failed login attempts logged for anomaly detection

## Risks & Mitigations

- Social login provider outage → fallback to email/password always available
- Magic link email delivery delay → show "check spam" guidance after 30s, offer resend
- Risk scoring false positives → manual review queue for flagged logins

## Open Questions

- Should we support biometric login (Face ID / fingerprint) in v1 or defer to v2?
- What's the session timeout policy — 24h or 7 days for "remember me"?
