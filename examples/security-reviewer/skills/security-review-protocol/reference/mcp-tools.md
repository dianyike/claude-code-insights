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

## Key Constraints

- **Codex sandbox MUST be `read-only`** — it should analyze, never modify
- **Always send actual code content to Codex**, not just file paths — Codex needs to see the code
- **Save the threadId** from the initial Codex call for potential follow-up
- **Semgrep paths must be absolute** — relative paths will fail
