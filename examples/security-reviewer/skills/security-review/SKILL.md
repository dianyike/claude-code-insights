---
name: security-review
description: >
  Run a read-only dual-verification security audit (Semgrep + Codex cross-validation).
  Use when: user says "security review", "audit code", "scan for vulnerabilities",
  "is this safe", "check for secrets", "before merge security scan", or invokes /security:review.
  Produces a confidence-scored report; never modifies source code.
  For remediation, see /security:fix.
disable-model-invocation: true
argument-hint: "[--base <branch>] [--scope staged|working-tree] [--background] [path...]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(git *)
  - Agent
---

# /security:review — Read-Only Security Audit

Run the `security-reviewer` subagent to produce a dual-verification security report. This command is **always read-only** — it will never modify source code files.

## Command Syntax

```
/security:review [options] [path...]
  --base <branch>              # Diff against a base branch (merge-base)
  --scope staged|working-tree  # Explicit change scope
  --background                 # Run in background, return job ID
  --wait                       # Run in foreground (default)
```

## Target Resolution

Determine the review scope before invoking the subagent:

### Priority Order

1. If `--base <branch>` is specified → **branch diff mode**
   - Run: `git merge-base HEAD <branch>` → `git diff --name-only <merge-base>..HEAD`
2. If `--scope` is specified → **explicit scope mode**
   - `staged`: `git diff --staged --name-only`
   - `working-tree`: `git diff --name-only` + `git ls-files --others --exclude-standard`
3. If neither specified and working tree is dirty → **auto: working-tree**
4. If neither specified and working tree is clean → **auto: branch diff against default branch**

### Path Filtering

If `[path...]` arguments are provided, filter the resolved file list to only include files whose paths start with any of the given prefixes.

### Handoff to Subagent

Pass the resolved scope to the `security-reviewer` subagent:

```
Review scope:
- Mode: <branch-diff|staged|working-tree>
- Base: <branch> (if applicable)
- Files: <resolved file list>
- Path filters: <prefixes> (if applicable)
```

## Background Execution

When `--background` is specified:

1. Launch the `security-reviewer` subagent with `run_in_background: true`
2. Return immediately with: "Security review started. Use `/security:status` to check progress."
3. When the subagent completes, the notification will include the verdict and report path.

When `--wait` (default):

1. Launch the `security-reviewer` subagent in foreground
2. Display the verdict and report path when complete

## Related Commands

- `/security:fix <report>` — Opt-in remediation based on a review report (requires explicit user action)

### Job Management (Phase 1 — not yet implemented)

The following commands are planned but not yet available as separate skills. Until implemented, use natural language (e.g., "check the security scan status") and the main agent will handle it via the Agent tool's built-in background notification.

- `/security:status [job-id]` — Check background job progress. Without ID, list all active jobs
- `/security:result <job-id>` — Retrieve completed job verdict and report path
- `/security:cancel <job-id>` — Mark a running job as CANCELLED (subagent may still complete in background)

**Expected behavior** (for future implementation):
- Job state is persisted at `.agents-output/security/jobs/<job-id>.json`
- States: QUEUED → RUNNING → COMPLETED / FAILED / CANCELLED
- On session restart, any RUNNING job is marked STALE (detected by checking `status == RUNNING` with `created_at` older than the current session start)

## Completion Criteria

- [ ] Target resolution produced a concrete file list (or "no changes found" if empty)
- [ ] `security-reviewer` subagent invoked with resolved scope
- [ ] Verdict and report path displayed to user
- [ ] If `--background`: job ID returned immediately, no blocking
- [ ] No source code files modified

## Gotchas

- `--base` and `--scope` are mutually exclusive in practice — if both specified, `--base` wins (priority order). Don't warn the user; just follow priority
- When working tree is clean AND no default branch is detectable (e.g., fresh repo with only one commit), auto mode falls through to an empty file list. Surface this clearly instead of running Semgrep on zero files
- `--background` relies on Claude Code's `run_in_background` for the Agent tool — the subagent cannot be cancelled mid-execution; `/security:cancel` only marks the job as CANCELLED and stops waiting for results
- Path filters are prefix-matched, not glob-matched. `src/auth` matches `src/auth/login.ts` and `src/auth-utils/helper.ts`. If users expect glob semantics, clarify
- **Iterate this section**: After each real usage, append new gotchas here

## What This Command Does NOT Do

- Does not modify source code (read-only)
- Does not enter the Fix-Verify Loop (Section 4 of the protocol)
- Does not auto-remediate findings
- Does not require Write or Edit tool permissions
