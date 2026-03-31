---
name: security-fix
description: >
  Fix vulnerabilities identified by /security:review using the Fix-Verify Loop.
  Use when: user says "fix security findings", "remediate vulnerabilities",
  or invokes /security:fix with a report path.
  Requires an existing security review report as input.
  Modifies source code — explicit opt-in only.
disable-model-invocation: true
argument-hint: "<report> [--finding <id>] [--deep] [--dry-run] [--yes]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(git *)
  - Write
  - Edit
  - mcp__plugin_semgrep-plugin_semgrep__semgrep_scan
  - mcp__plugin_semgrep-plugin_semgrep__semgrep_scan_with_custom_rule
  - mcp__plugin_semgrep-plugin_semgrep__get_abstract_syntax_tree
  - mcp__codex__codex
  - mcp__codex__codex-reply
---

# /security:fix — Opt-In Security Remediation

Fix vulnerabilities identified in a `/security:review` report using the convergence-hardened Fix-Verify Loop (Section 4 of `security-review-protocol`).

This command **modifies source code** — it is never auto-triggered.

## Why This Runs in Main Conversation (Not a Subagent)

Fix-verify requires:
- **User confirmation** before each fix (prediction block approval)
- **Visible intermediate state** (prediction vs actual comparison)
- **Full review context** (findings, Codex threadId, code patterns from the report)

Delegating to a subagent would create a "telephone game" (handoff loses context fidelity) and hide the confirmation flow in a black box. Per our subagent best practices: split by context boundaries, not by roles.

## Command Syntax

```
/security:fix <report> [options]
  <report>                     # Required: path to a security review report
  --finding <id>               # Fix only a specific finding (e.g., F-003).
                               # Note: if this finding shares a root-cause cluster
                               # with other findings, only this finding is fixed —
                               # sibling findings are skipped. The root cause may
                               # remain partially addressed.
  --deep                       # Enable round 3 of fix-verify (default: 2 rounds)
  --dry-run                    # Show fix plan without modifying files
  --yes                        # Skip per-fix confirmation prompts
```

## Typical Workflow

```
1. /security:review                    # Read-only audit → produces report
2. (User reviews report)
3. /security:fix .agents-output/security/2026-03-31-auth-security-review.md
   # Or target a specific finding:
   /security:fix .agents-output/security/2026-03-31-auth-security-review.md --finding F-003
```

## Execution

### 1. Parse Report

1. Read the security review report at `<report>` path
2. Extract confirmed findings (confidence >= 50%) in normalized format
3. If `--finding <id>` specified, filter to that finding only
4. If no fixable findings exist, report "Nothing to fix" and exit
5. Extract the Codex threadId from the report (if available) for session continuity

### 2. Triage

Group findings by root-cause cluster. A single root cause may manifest across multiple call sites. Order clusters by severity (CRITICAL first, then HIGH, then MEDIUM).

### 3. Fix-Verify Loop (Per Cluster)

For each root-cause cluster, execute Section 4 of the `security-review-protocol` skill (4.1 through 4.7). The protocol defines the full logic — do not deviate from it.

**Additional constraint for this command**: Before applying each fix (after writing the prediction block per 4.2), display the prediction summary and wait for user confirmation. Skip this gate only if `--yes` was passed. The protocol itself does not enforce this gate — it's a command-level safety layer because `/security:fix` runs in the main conversation where user interaction is possible.

### 4. Record Results

Append the `## Fix-Verify Hypothesis Log` to the original security review report per Section 4.6 of the protocol.

## Dry-Run Mode

When `--dry-run` is specified:

1. Parse report and triage findings as normal
2. For each cluster, identify the fix strategy (canonical or Codex-proposed)
3. Write the prediction block
4. Display the plan: which files would be modified, what changes would be made
5. Do NOT apply any changes or modify any files

## User Confirmation Flow

By default, before each fix is applied:

1. Display the prediction block summary (root cause, files to modify, expected outcome)
2. Wait for user approval
3. If denied, skip this finding and move to the next

With `--yes`, skip confirmation prompts (use for trusted canonical fixes).

## Round Caps

| Mode | Max Rounds | When to Use |
|------|-----------|-------------|
| Default | 2 | Covers ~90% of issues, low hypothesis drift risk |
| `--deep` | 3 | CRITICAL findings, Round 3 uses fresh Codex session |

## Related Commands

- `/security:review` — Run the read-only audit that produces the report this command consumes
- `/security:status` — Check background review job status

## Completion Criteria

- [ ] Report parsed and fixable findings extracted
- [ ] Each root-cause cluster processed through protocol Section 4
- [ ] User confirmed (or `--yes` skipped) every applied fix
- [ ] Semgrep re-scan passed after each fix (per Section 4.3)
- [ ] Hypothesis Ledger appended to original report
- [ ] Final summary: N fixed / N total, files modified, escalations

## Gotchas

- The report path must point to an existing `.agents-output/security/*.md` file — the skill parses its structured format (Executive Summary, findings sections). Arbitrary markdown files will fail silently or extract zero findings
- If the original review's Codex threadId is not in the report, fix-verify starts a fresh Codex session. This means Round 1 loses the context continuity advantage — consider re-running `/security:review` first if the report is old
- `--dry-run` still calls Codex to get fix proposals (read-only) — it costs tokens even though no files are modified. The savings are only in skipping the apply+verify cycle
- `--yes` bypasses the user confirmation gate entirely. Only safe for well-understood canonical fixes (CWE-89, CWE-79, etc.). For Codex-proposed fixes, always let the user review the prediction block
- When `--finding <id>` targets a finding that shares a root-cause cluster with other findings, only the specified finding is fixed — sibling findings in the same cluster are skipped. This may leave the root cause partially addressed
- Protocol Section 4 has its own gotchas (absolute paths, Codex hallucination, threadId management) — refer to `security-review-protocol` Section 5
- **Iterate this section**: After each real usage, append new gotchas here

## What This Command Does NOT Do

- Does not re-run the full security audit (use `/security:review` for that)
- Does not auto-trigger from gates or hooks
- Does not fix findings below 50% confidence (those are escalated to human)
- Does not delegate to a subagent (runs in main conversation for user visibility)
