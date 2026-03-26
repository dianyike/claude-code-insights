---
name: security-review-protocol
description: >
  Load when performing dual-source security review, cross-validating
  Semgrep findings with Codex, or resolving conflicting vulnerability assessments.
  Trigger on: security audit, scan vulnerabilities, cross-validate findings,
  conflict resolution, confidence scoring.
user-invocable: false
---

# Security Review Protocol

Core business logic for the dual-verification security review workflow: cross-validation, conflict resolution, and confidence scoring.

## Additional resources

- For MCP tool call patterns and parameters, see [reference/mcp-tools.md](reference/mcp-tools.md)
- For report output template, see [templates/report-template.md](templates/report-template.md)

## 1. Cross-Validation Logic

### 1.1 Finding Normalization

Before comparing, normalize findings from both sources into a common format:

```
{
  id: "<unique-id>",
  source: "semgrep" | "codex",
  type: "<vulnerability-type>",     // e.g., "sql-injection", "xss", "hardcoded-secret"
  file: "<file-path>",
  line: <line-number>,
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
  description: "<what the issue is>",
  evidence: "<specific code or pattern that triggered this>",
  trigger: "<how it can be exploited>",
  fix: "<remediation suggestion>"
}
```

### 1.2 Matching Algorithm

Two findings from different sources are considered **matching** when:

1. **Same file** (exact path match)
2. **Overlapping location** (line numbers within 5 lines of each other)
3. **Same vulnerability category** (e.g., both are injection-related, both are auth-related)

If criteria 1+3 match but lines differ by >5, flag as **partial match** — may be the same root cause manifesting at different points.

### 1.3 Classification

| Semgrep Found | Codex Found | Classification | Action |
|:---:|:---:|---|---|
| Yes | Yes | **Confirmed** | Report with high confidence |
| Yes | No | **Baseline-only** | Report — tool findings are reproducible |
| No | Yes | **Codex-only** | Verify with targeted Grep/AST before reporting |
| No | No | (not applicable) | — |

## 2. Conflict Resolution Protocol

### 2.1 Divergence Types

**Type A: Codex says safe, Semgrep says vulnerable (most dangerous)**

Conservative stance: treat as vulnerable until proven otherwise.

Resolution steps:
1. Read the flagged code and its surrounding context (50 lines)
2. Check if there are sanitization functions upstream
3. Run a targeted custom Semgrep rule for the specific pattern
4. If still ambiguous → report as finding with note "Codex disagrees — needs human review"

**Type B: Codex says vulnerable, Semgrep says nothing (potential false positive)**

Moderate stance: verify before reporting.

Resolution steps:
1. Use Grep to find the exact pattern Codex described
2. Use `get_abstract_syntax_tree` to verify the code structure
3. If Codex's reasoning is sound and code confirms → report as finding
4. If pattern not found or reasoning flawed → discard with note

**Type C: Both found it but disagree on severity or fix**

Resolution steps:
1. Prefer Semgrep's CWE/severity mapping (based on established rule databases)
2. Evaluate Codex's reasoning for severity — may have project-specific context
3. Report with the higher severity (conservative) and note the disagreement

### 2.2 Deep Verification Techniques

When conflicts arise, use these targeted verification methods:

| Technique | Tool | When to Use |
|-----------|------|-------------|
| Targeted grep | Grep | Verify specific code patterns exist |
| AST analysis | `get_abstract_syntax_tree` | Verify code structure matches vulnerability pattern |
| Custom Semgrep rule | `semgrep_scan_with_custom_rule` | Test a specific hypothesis about a vulnerability |
| Upstream trace | Read + Grep | Check if input is sanitized before reaching the flagged point |
| Codex follow-up | `codex-reply` | Ask Codex to explain or defend its finding with evidence |

## 3. Confidence Score Calculation

### 3.1 Base Weights

| Source | Weight | Rationale |
|--------|--------|-----------|
| Semgrep finding | 60% | Deterministic, reproducible, based on established rules |
| Codex finding | 40% | Reasoning-based, can catch logic flaws that rules miss |

### 3.2 Score Formula

```
confidence = base_score + modifiers

Where:
  base_score:
    - Both agree:        max(60, 40) + 20 = 80%
    - Semgrep only:      60%
    - Codex only:        40%

  modifiers:
    - Deep verification confirms:           +15%
    - Semgrep rule has CWE reference:       +5%
    - Codex provided exploit scenario:      +5%
    - Historical finding exists (platform): +10%
    - Conflict unresolved:                  cap at 50%

  cap: 95% (never claim absolute certainty)
```

### 3.3 Escalation Threshold

- Confidence >= 70%: Report as confirmed finding
- Confidence 50-69%: Report with "needs verification" flag
- Confidence < 50%: Escalate to human review, do not auto-report as confirmed

## 4. Fix-Verify Loop

After findings are confirmed (confidence >= 50%), use Codex to get fix suggestions and verify them.

### 4.1 Request Fix from Codex

Use `codex-reply` with the existing threadId to request concrete fixes:

```
Tool: mcp__codex__codex-reply
Parameters:
  threadId: "<saved threadId>"
  prompt: |
    Based on the findings from your review, provide concrete fixes for each confirmed issue.

    For each fix:
    1. The exact code change (before → after)
    2. Why this fix addresses the root cause
    3. Any edge cases the fix might miss
    4. Whether the fix could introduce new issues

    Confirmed findings:
    - [list findings with file:line]
```

### 4.2 Apply and Re-verify

After applying fixes:

1. Run Semgrep again on the modified files — confirm the original findings are gone
2. Run Semgrep on the modified files — check for NEW findings introduced by the fix
3. Use `codex-reply` to verify the fix is correct and complete:

```
Tool: mcp__codex__codex-reply
Parameters:
  threadId: "<saved threadId>"
  prompt: |
    I applied fixes based on your suggestions. Please review the CURRENT version
    of the code and verify:

    1. Are all previously reported issues properly fixed?
    2. Are there any NEW issues introduced by the fixes?
    3. Any remaining edge cases or security concerns?

    Be specific about line numbers and whether each original finding is resolved
    or still present.
```

### 4.3 Iteration Protocol

- If Codex finds remaining issues in the re-verify step, repeat 4.1-4.2
- Cap at 3 iterations — if issues persist after 3 rounds, escalate to human review
- Each iteration MUST re-run Semgrep (not just Codex) to avoid regression
- Never declare "all fixed" based solely on Codex's claim — Semgrep must also confirm

### 4.4 Common Fix Pitfalls

| Pitfall | Example | Prevention |
|---------|---------|------------|
| Fix introduces new vuln | Escaping SQL by string concat instead of parameterized query | Semgrep re-scan catches pattern |
| Fix is cosmetic only | Renaming a variable but not fixing the logic | Codex re-verify catches intent mismatch |
| bare `except:` catches SystemExit | `sys.exit()` inside `try/except:` block | Check that except clauses use `except Exception:` not `except:` |
| Fix for wrong version | Checking latest when user specified `@^1.0.0` | Always resolve to exact version before checking |
| Partial fix | Fixed one call site but same pattern exists elsewhere | Grep for the pattern project-wide after fixing |

## 5. Gotchas

- Semgrep `semgrep_scan` requires **absolute paths** — relative paths silently return no results
- Codex may hallucinate line numbers — always verify with Read before citing
- Semgrep supply chain scan reads lockfiles from CWD — make sure CWD is project root
- Codex `read-only` sandbox prevents it from running verification scripts — you must do that yourself
- If Codex returns a threadId, save it. If conflict resolution needs follow-up, use `codex-reply` with that threadId instead of starting a new session (preserves context, saves tokens)
- Semgrep findings JSON structure may vary between local scan and platform findings — normalize before comparing
- Never declare "all issues fixed" after applying Codex's suggestions without re-running both Codex verify AND Semgrep re-scan — Codex can confirm fixes that are actually incomplete
- When Codex says "no new issues", still run Semgrep — Codex misses structural issues like bare `except:` catching `SystemExit`, `pipefail` interactions, and shell quoting edge cases
- Codex is strong at finding logic-level issues (fail-open, parser bypass, state machine gaps) but weak at shell/bash edge cases (SIGPIPE, IFS, `grep | head` under pipefail) — Semgrep is better for the latter
- After each fix round, explicitly list what was claimed fixed vs what was actually verified — prevents "fixed" claims from compounding without evidence
- **Iterate this section**: After each real review, append new gotchas here — false positive patterns you encountered, specific Codex hallucination tendencies (e.g., inventing middleware that doesn't exist), or Semgrep rules that consistently misfire on your codebase. This list should grow with use, not stay static
