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

After findings are confirmed (confidence >= 50%), enter the fix-verify loop to remediate and validate fixes.

### 4.0 Mode Boundary

**Sections 1-3 and Section 4 operate under fundamentally different structural guarantees.**

- **Sections 1-3** (diagnostic): dual-source cross-validation with weighted scoring. Both Semgrep and Codex contribute findings independently, and the 60/40 weights govern classification.
- **Section 4** (remediation): each round must have exactly **one strategy source**. Usually that source is Codex; if 4.1 matches a canonical fix pattern, the source becomes the canonical pattern instead. In either case, Semgrep's role narrows to **violation oracle** — it can confirm "this rule still fires" or "this rule stopped firing," but it cannot confirm that the root cause is resolved or that the fix direction is correct.

The 60/40 diagnostic weights do NOT apply here. The constraints below exist to compensate for this single-proposer asymmetry — they are not bureaucracy.

### 4.1 Known Fix Gate

Before asking Codex for a fix strategy, check if the finding matches a canonical fix pattern:

| CWE Category | Canonical Fix | Do NOT |
|---|---|---|
| SQL Injection (CWE-89) | Parameterized queries / prepared statements | String escaping, concat-based sanitization |
| XSS (CWE-79) | Contextual output encoding / safe sink APIs | Manual regex stripping |
| Hardcoded Secret (CWE-798) | Remove + rotate + env var / secret manager | Obfuscation, base64 encoding |
| Path Traversal (CWE-22) | Allowlist + resolve-then-check canonical path | Blacklist patterns like `../` |

**If match found**:
1. Apply the canonical fix
2. Still write the prediction block (see 4.2 Constraint 2) — the strategy source changes from Codex to canonical pattern, but the verification contract is identical
3. Open a read-only Codex session (`mcp__codex__codex`) with the code + applied canonical fix for thread continuity — this ensures `codex-reply` is available for 4.3 verification
4. Skip to 4.3

**If no match** → proceed to 4.2.

Rationale: For well-understood vulnerability classes, letting the model "be creative" only increases drift probability. The prediction block is not "for Codex" — it's the falsifiable target that makes verification meaningful.

### 4.2 Request Fix from Codex

For same-thread refinement, use `codex-reply` with the existing threadId to request a fix. If 4.4 requires a fresh strategy reset, open a new read-only `mcp__codex__codex` session using the fresh fix-strategy template in [reference/mcp-tools.md](reference/mcp-tools.md). Two hard constraints apply either way:

**Constraint 1 — Single Root-Cause Hypothesis**

Each round targets exactly ONE root-cause cluster. A single root cause may manifest across multiple call sites — fixing them together in one round is correct.

What's prohibited: mixing unrelated fix directions in one round (e.g., fixing SQL injection AND XSS simultaneously). This isolates cause-effect so that Semgrep evidence is interpretable.

**Constraint 2 — Prediction Block** (MANDATORY before applying any fix)

Before applying the fix, write down the following prediction. This applies to BOTH the canonical path (4.1) and the Codex path (4.2):

```
prediction:
  root_cause_hypothesis: "<what you believe is the underlying cause>"
  minimal_change_scope: "<which files:lines will be modified>"
  expected_rules_to_clear: ["<semgrep-rule-id-1>", ...]
  expected_grep_patterns_to_disappear: ["<pattern>", ...]
  possible_new_findings: ["<rule-id or 'none'>"]
  disconfirming_evidence: "<what result would prove this hypothesis WRONG>"
  rollback_trigger: "<specific condition that means revert immediately>"
```

If the prediction cannot be stated concretely, the fix is too vague to apply. Stop and refine the hypothesis first.

For MCP prompt templates, see [reference/mcp-tools.md](reference/mcp-tools.md).

### 4.3 Apply and Re-verify

After applying the fix:

1. **Run Semgrep** on modified files — record the actual output
2. **Compare actual output against prediction block point-by-point:**
   - Did `expected_rules_to_clear` actually clear? (Y/N per rule)
   - Did `expected_grep_patterns_to_disappear` actually disappear? (Y/N per pattern)
   - Did any findings appear in `possible_new_findings`? Expected or unexpected?
   - Did the `disconfirming_evidence` condition trigger?
3. **Call Codex verify** (using the verify prompt from [reference/mcp-tools.md](reference/mcp-tools.md)) — Codex must compare against the prediction block, not just re-review the code
4. **Classify the round outcome:**
   - **Prediction confirmed**: all expected rules cleared, no unexpected findings → finding resolved
   - **Prediction partially confirmed**: some rules cleared, others persist → record as hypothesis refinement evidence, proceed to next round. **Constraint**: partially confirmed only permits same root-cause family refinement. It does NOT permit switching to a new remediation direction in the same thread without recording the original hypothesis as failed or superseded
   - **Prediction falsified**: disconfirming evidence triggered, or zero predictions matched → this is a hypothesis failure, not an implementation bug

Key framing: Semgrep checks "does the violation pattern still match?" — NOT "is the code now secure."

### 4.4 Iteration Protocol

Cap at 3 rounds. Each round escalates the strategy diversity requirement:

- **Round 1 fails**: Stay on same Codex threadId. Inject into the prompt: the failed prediction block, actual Semgrep output, and the specific mismatch. Ask Codex to **revise its root-cause hypothesis**, not just tweak the fix
- **Round 2 fails**: MANDATORY strategy switch:
  - Abandon the current threadId — start a **fresh Codex session**
  - New prompt MUST include: both failed hypotheses, their predictions, actual outputs, and the explicit instruction: "propose a fundamentally different approach — the previous two attempts targeted [X] and both failed because [Y]"
  - Purpose: break narrative inertia from accumulated thread context
- **Round 3 fails**: Stop all automated repair. Escalate to human with a structured bundle:
  - All 3 hypotheses with prediction blocks
  - All 3 actual Semgrep outputs
  - All 3 prediction-vs-actual comparisons
  - Agent's assessment of why convergence failed

### 4.5 Rollback Rules

NOT a blanket "any new finding → revert." Apply tiered judgment:

| Condition | Action | Reason |
|---|---|---|
| New HIGH/CRITICAL finding not in `possible_new_findings` | Immediate rollback | Unacceptable regression |
| Original rule still fires AND zero predictions matched | Rollback | Hypothesis was entirely wrong, no value in keeping the change |
| Rule transferred (old cleared, new appeared at same severity) | Mark as hypothesis failure, keep change, investigate in next round | May be progress toward correct direction |
| Low-severity secondary signal appeared | Note in ledger, continue | Semgrep is not a truth oracle; minor noise is expected |

### 4.6 Hypothesis Ledger

Each round's hypothesis, prediction, actual output, and decision MUST be persisted — not just held in transient context.

**Location**: Append as `## Fix-Verify Hypothesis Log` as the final section of the security report, after `## Supply Chain`.

**Format per round**:

```markdown
### Round N — [CONFIRMED | PARTIALLY CONFIRMED | FALSIFIED | ROLLBACK]
- **Hypothesis**: ...
- **Prediction**: [paste prediction block]
- **Actual Semgrep output**: [rule IDs fired / cleared]
- **Prediction match**: [point-by-point comparison]
- **Decision**: [applied / rolled back / escalated]
- **Evidence carried forward**: [what the next round should know]
```

Purpose: prevent the agent from repeating the same class of mistake, and give the human reviewer a diagnostic trail if escalation occurs.

### 4.7 Common Fix Pitfalls

| Pitfall | Example | Prevention |
|---------|---------|------------|
| Fix introduces new vuln | Escaping SQL by string concat instead of parameterized query | Semgrep re-scan catches pattern |
| Fix is cosmetic only | Renaming a variable but not fixing the logic | Codex re-verify catches intent mismatch |
| bare `except:` catches SystemExit | `sys.exit()` inside `try/except:` block | Check that except clauses use `except Exception:` not `except:` |
| Fix for wrong version | Checking latest when user specified `@^1.0.0` | Always resolve to exact version before checking |
| Partial fix | Fixed one call site but same pattern exists elsewhere | Grep for the pattern project-wide after fixing |
| Hypothesis drift | Round 1 targets SQL injection, Round 2 silently shifts to input validation | Prediction block comparison catches scope change |

## 5. Gotchas

- Semgrep `semgrep_scan` requires **absolute paths** — relative paths silently return no results
- Codex may hallucinate line numbers — always verify with Read before citing
- Semgrep supply chain scan reads lockfiles from CWD — make sure CWD is project root
- Codex `read-only` sandbox prevents it from running verification scripts — you must do that yourself
- If Codex returns a threadId, save it. For same-thread refinement and conflict follow-up, use `codex-reply` with that threadId. Exception: when 4.4 requires a strategy reset, start a fresh session and save the new threadId
- Semgrep findings JSON structure may vary between local scan and platform findings — normalize before comparing
- Never declare "all issues fixed" after applying Codex's suggestions without re-running both Codex verify AND Semgrep re-scan — Codex can confirm fixes that are actually incomplete
- When Codex says "no new issues", still run Semgrep — Codex misses structural issues like bare `except:` catching `SystemExit`, `pipefail` interactions, and shell quoting edge cases
- Codex is strong at finding logic-level issues (fail-open, parser bypass, state machine gaps) but weak at shell/bash edge cases (SIGPIPE, IFS, `grep | head` under pipefail) — Semgrep is better for the latter
- After each fix round, explicitly list what was claimed fixed vs what was actually verified — prevents "fixed" claims from compounding without evidence
- **Iterate this section**: After each real review, append new gotchas here — false positive patterns you encountered, specific Codex hallucination tendencies (e.g., inventing middleware that doesn't exist), or Semgrep rules that consistently misfire on your codebase. This list should grow with use, not stay static
