# MCP Tool Call Reference

Reference for Semgrep and Codex MCP tool call patterns used in the dual-verification security review.

## Semgrep Tools

### semgrep_scan — Scan files with default rules

```
Tool: mcp__plugin_semgrep-plugin_semgrep__semgrep_scan
Parameters:
  code_files:
    - { path: "/absolute/path/to/file1.ts" }
    - { path: "/absolute/path/to/file2.py" }

Returns: JSON array of findings, each with:
  - check_id (rule that matched)
  - path (file path)
  - start/end (line numbers)
  - extra.message (description)
  - extra.severity (INFO/WARNING/ERROR)
  - extra.metadata (references, CWE IDs)
```

### semgrep_scan_with_custom_rule — Scan with custom YAML rule

```
Tool: mcp__plugin_semgrep-plugin_semgrep__semgrep_scan_with_custom_rule
Parameters:
  code_files:
    - { path: "file.ts", content: "<actual file content>" }
  rule: |
    rules:
      - id: hardcoded-secret
        pattern: $KEY = "..."
        message: Potential hardcoded secret
        severity: ERROR
        languages: [typescript, javascript]
```

### semgrep_findings — Fetch historical findings from platform

```
Tool: mcp__plugin_semgrep-plugin_semgrep__semgrep_findings
Parameters:
  repos: ["owner/repo-name"]
  severities: ["SEVERITY_CRITICAL", "SEVERITY_HIGH"]
  limit: 20
  status: "ISSUE_TAB_OPEN"
```

### semgrep_scan_supply_chain — Dependency vulnerability scan

```
Tool: mcp__plugin_semgrep-plugin_semgrep__semgrep_scan_supply_chain
Parameters: (none — scans workspace lockfiles automatically)
```

## Codex Tools

### codex — Start a security review session

```
Tool: mcp__codex__codex
Parameters:
  prompt: |
    You are performing a security audit. Analyze the following code for vulnerabilities.

    For each finding, provide:
    1. Vulnerability type (e.g., SQL injection, XSS, SSRF)
    2. Exact location (file:line)
    3. Triggering condition (how an attacker would exploit this)
    4. Impact (what damage could be done)
    5. Concrete fix (code snippet)

    If you find NO vulnerabilities in a section, explicitly state what you checked and why it's safe.

    Code to review:
    ---
    [INSERT CODE CONTENT HERE]
    ---
  cwd: "/path/to/project"
  sandbox: "read-only"
```

### codex-reply — Drill deeper on conflicts

```
Tool: mcp__codex__codex-reply
Parameters:
  threadId: "<threadId from initial codex call>"
  prompt: |
    Our static analysis tool (Semgrep) flagged the following that you did not mention:

    - [Finding description, file:line, rule ID]

    Please analyze specifically:
    1. Is this a true positive or false positive?
    2. If true positive, why did you miss it?
    3. If false positive, explain why it's safe.

    Also, you flagged the following that Semgrep did NOT flag:

    - [Codex-only finding description]

    Please provide the specific code pattern that makes this vulnerable,
    so we can verify with a targeted grep.
```

### codex-reply — Request concrete fixes

```
Tool: mcp__codex__codex-reply
Parameters:
  threadId: "<threadId from initial codex call>"
  prompt: |
    We are fixing ONE root-cause cluster at a time. This round targets:

    Root-cause hypothesis: [describe the underlying cause]
    Findings in this cluster: [list findings with file:line]

    For your proposed fix, provide:
    1. The exact code change (before → after)
    2. Why this fix addresses the root cause
    3. Any edge cases the fix might miss
    4. Whether the fix could introduce new issues

    IMPORTANT — return this prediction block EXACTLY:
    prediction:
      root_cause_hypothesis: "<what you believe is the underlying cause>"
      minimal_change_scope: "<which files:lines will be modified>"
      expected_rules_to_clear: ["<semgrep-rule-id-1>", ...]
      expected_grep_patterns_to_disappear: ["<pattern>", ...]
      possible_new_findings: ["<rule-id or 'none'>"]
      disconfirming_evidence: "<what result would prove this hypothesis WRONG>"
      rollback_trigger: "<specific condition that means revert immediately>"

    [For round 2+ ONLY, append:]
    Previous failed approaches:
    - Round N: [hypothesis], predicted [X], actual result was [Y]
    - Round N: [hypothesis], predicted [X], actual result was [Y]
    Do NOT propose a variation of these failed approaches.
    Propose a fundamentally different remediation strategy.
```

### codex — Start fresh fix strategy session

For Round 2+ strategy resets (SKILL.md 4.4), start a new thread instead of using `codex-reply`. This breaks narrative inertia while preserving the same prediction contract.

```
Tool: mcp__codex__codex
Parameters:
  prompt: |
    We are resetting the remediation strategy because previous rounds failed.
    Propose a fundamentally different fix strategy for this ONE root-cause cluster.

    Current target cluster:
    - Root-cause hypothesis under investigation: [describe cluster]
    - Findings in this cluster: [list findings with file:line]

    Previous failed approaches:
    - Round 1: hypothesis [X], prediction [Y], actual result [Z]
    - Round 2: hypothesis [X], prediction [Y], actual result [Z]

    For your proposed fix, provide:
    1. The exact code change (before → after)
    2. Why this fix addresses the root cause
    3. Any edge cases the fix might miss
    4. Whether the fix could introduce new issues

    Return this prediction block EXACTLY:
    prediction:
      root_cause_hypothesis: "<what you believe is the underlying cause>"
      minimal_change_scope: "<which files:lines will be modified>"
      expected_rules_to_clear: ["<semgrep-rule-id-1>", ...]
      expected_grep_patterns_to_disappear: ["<pattern>", ...]
      possible_new_findings: ["<rule-id or 'none'>"]
      disconfirming_evidence: "<what result would prove this hypothesis WRONG>"
      rollback_trigger: "<specific condition that means revert immediately>"

    Current code:
    ---
    [INSERT CURRENT CODE CONTENT HERE]
    ---
  cwd: "/path/to/project"
  sandbox: "read-only"
```

### codex — Open canonical fix verification session

For findings that matched a Known Fix Gate (SKILL.md 4.1) and were fixed via canonical pattern without a prior Codex session. Opens a new thread so `codex-reply` is available for verification.

```
Tool: mcp__codex__codex
Parameters:
  prompt: |
    A canonical fix has been applied for a known vulnerability pattern.
    Please review the CURRENT version of the code below.

    Vulnerability type: [CWE category]
    Canonical fix applied: [description of what was changed]
    Files modified: [list]

    Code after fix:
    ---
    [INSERT CURRENT CODE CONTENT HERE]
    ---

    Your role: verify the fix is correctly applied. Do NOT suggest
    alternative approaches — the canonical pattern is the standard.
    Focus on: completeness, edge cases, and whether any call sites
    were missed.
  cwd: "/path/to/project"
  sandbox: "read-only"
```

### codex-reply — Verify fixes against prediction

```
Tool: mcp__codex__codex-reply
Parameters:
  threadId: "<threadId from fix request or canonical verification session>"
  prompt: |
    Fixes have been applied. Here is the prediction we made BEFORE
    applying them, and the ACTUAL Semgrep results after applying them.

    PREDICTION (written before fix):
    - Root-cause hypothesis: [hypothesis]
    - Minimal change scope: [files:lines changed]
    - Expected rules to clear: [list]
    - Expected grep patterns to disappear: [list]
    - Possible new findings: [list or 'none']
    - Disconfirming evidence: [what would prove hypothesis wrong]
    - Rollback trigger: [what condition requires immediate revert]

    ACTUAL Semgrep output after fix:
    - Rules that cleared: [list]
    - Rules that still fire: [list]
    - New rules that appeared: [list]

    Current code after fix:
    ---
    [INSERT CURRENT CODE CONTENT HERE]
    ---

    Compare prediction vs actual point-by-point:
    1. Which predictions matched?
    2. Which predictions did NOT match? Why?
    3. Classify this round: is the mismatch a "strategy error"
       (wrong root cause) or "implementation incomplete"
       (right direction, partial fix)?
    4. Did the rollback trigger fire? If yes, explain why.
    5. Any NEW security issues introduced by the fix?

    Do NOT re-review the code from scratch. Focus on the
    prediction-vs-actual comparison.
```

## Key Constraints

- **Codex sandbox MUST be `read-only`** — it should analyze, never modify
- **Always send actual code content to Codex**, not just file paths — Codex needs to see the code
- **Save the threadId** from the active Codex session for potential follow-up
- **Semgrep paths must be absolute** — relative paths will fail
- **Prediction block is mandatory** — no fix should be applied without a written, falsifiable prediction (see SKILL.md 4.2)
- **Canonical fix path still needs a Codex session** — open one via `codex` (not `codex-reply`) before verification
