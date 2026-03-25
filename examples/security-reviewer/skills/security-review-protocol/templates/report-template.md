# Security Review: <scope description>

> Review date: YYYY-MM-DD
> Scope: <list of reviewed files>
> Protocol: Dual-verification (Semgrep baseline + Codex cross-validation)

## Executive Summary

| Source | Findings | Agreement Rate |
|--------|----------|---------------|
| Semgrep Baseline | N issues | - |
| Codex Analysis | N issues | X% overlap |
| Cross-validated | N confirmed | - |

Verdict: SECURE / WARNING / CRITICAL

## Confirmed Findings (Both Sources Agree)

### [SEVERITY] Finding Title
- **File**: `path/to/file:line`
- **Confidence**: X% (source: both)
- **Description**: What the vulnerability is
- **Trigger**: How it can be exploited
- **Impact**: What damage it could cause
- **Fix**: Concrete remediation code or steps
- **Evidence**: Semgrep rule ID + Codex reasoning

## Baseline-Only Findings (Semgrep Only)

(Same format, confidence typically 60-80%)

## Codex-Only Findings (Verified)

(Same format, confidence varies by verification result)

## Conflicts Resolved

| Finding | Semgrep Says | Codex Says | Verdict | Reason |
|---------|-------------|------------|---------|--------|
| ... | ... | ... | ... | ... |

## Unresolved (Escalated to Human)

Items where deep verification could not reach a conclusion.
Flag these for manual review.

## Supply Chain

(If applicable: dependency vulnerability findings)
