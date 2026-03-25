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

## 4. Gotchas

- Semgrep `semgrep_scan` requires **absolute paths** — relative paths silently return no results
- Codex may hallucinate line numbers — always verify with Read before citing
- Semgrep supply chain scan reads lockfiles from CWD — make sure CWD is project root
- Codex `read-only` sandbox prevents it from running verification scripts — you must do that yourself
- If Codex returns a threadId, save it. If conflict resolution needs follow-up, use `codex-reply` with that threadId instead of starting a new session (preserves context, saves tokens)
- Semgrep findings JSON structure may vary between local scan and platform findings — normalize before comparing
- **Iterate this section**: After each real review, append new gotchas here — false positive patterns you encountered, specific Codex hallucination tendencies (e.g., inventing middleware that doesn't exist), or Semgrep rules that consistently misfire on your codebase. This list should grow with use, not stay static
