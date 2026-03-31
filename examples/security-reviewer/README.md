# Security Reviewer — Dual-Verification Subagent Example

A working example of a security-focused subagent that cross-validates findings between Semgrep (static analysis) and Codex (LLM second opinion) via MCP, producing confidence-scored security reports with a convergence-hardened Fix-Verify Loop.

## Architecture

```
You → Claude Code (Main Agent)
       │
       ├─ /security:review [--base] [--scope] [--background]
       │       ↓
       │   security-reviewer (Subagent, Sonnet, READ-ONLY)
       │       ↓
       │   ═══════════════════════════════════════════════
       │     READ-ONLY boundary (review never crosses)
       │   ═══════════════════════════════════════════════
       │       ↓
       │   ┌─────────────────────────────┐
       │   │ Step 1: Semgrep Baseline     │  semgrep_scan + semgrep_findings
       │   │ Independent judgment first   │  + supply chain + manual Grep
       │   └──────────┬──────────────────┘
       │              ↓
       │   ┌─────────────────────────────┐
       │   │ Step 2: Codex Second Opinion │  mcp__codex__codex (read-only)
       │   │ MCP tool call               │  mcp__codex__codex-reply (follow-up)
       │   └──────────┬──────────────────┘
       │              ↓
       │   ┌─────────────────────────────┐
       │   │ Step 3: Cross-Validation     │  security-review-protocol skill
       │   │ Confidence scoring           │  Semgrep 60% / Codex 40% weight
       │   │ Conflict → conservative      │  False negative > false positive
       │   └──────────┬──────────────────┘
       │              ↓
       │   Report → .agents-output/security/
       │   Return → verdict + counts + suggested /security:fix command
       │
       ├─ /security:fix <report> [--finding] [--deep]
       │       ↓
       │   ═══════════════════════════════════════════════
       │     WRITE boundary (explicit user opt-in only)
       │   ═══════════════════════════════════════════════
       │       ↓
       │   Runs in MAIN CONVERSATION (not a subagent)
       │       ↓
       │   ┌─────────────────────────────┐
       │   │ Step 4: Fix-Verify Loop      │  Convergence-hardened:
       │   │ Known Fix Gate → Codex fix   │  - Falsifiable prediction block
       │   │ Prediction → Semgrep verify  │  - User confirmation per fix
       │   │ Hypothesis ledger            │  - Fresh-session strategy reset
       │   └──────────┬──────────────────┘  - Tiered rollback rules
       │              ↓
       │   Modified files + hypothesis ledger appended to report
       │
       └─ /security:status / result / cancel   ← job management
```

## File Structure

```
.claude/
├── agents/
│   └── security-reviewer.md              # Subagent: read-only audit (Steps 1-3)
└── skills/
    ├── security-review/
    │   └── SKILL.md                       # /security:review command (target resolution)
    ├── security-fix/
    │   └── SKILL.md                       # /security:fix command (main-conversation remediation)
    └── security-review-protocol/
        ├── SKILL.md                       # Core logic: cross-validation + scoring + fix-verify
        ├── reference/
        │   └── mcp-tools.md               # MCP tool call patterns (on-demand)
        └── templates/
            └── report-template.md         # Report structure (on-demand)
```

## Prerequisites

- **Semgrep MCP plugin**: `semgrep-plugin` configured in Claude Code
- **Codex MCP server**: `codex` configured in Claude Code
- Both must appear in `/tools` output

## How to Use

### 1. Copy files into your project

```bash
# Copy the subagent
cp agents/security-reviewer.md YOUR_PROJECT/.claude/agents/

# Copy the skill (entire directory)
cp -r skills/security-review-protocol YOUR_PROJECT/.claude/skills/
```

### 2. Trigger a security review

Use the slash command:

```
/security:review                         # Auto-detect scope
/security:review --base develop          # Diff against develop branch
/security:review --scope staged          # Only staged changes
/security:review src/auth/               # Filter to specific path
/security:review --background            # Run in background
```

Or say any of these to Claude Code (trigger words):

- "security check"
- "audit code"
- "scan for vulnerabilities"
- "is this safe"
- "check for secrets"
- "before merge security scan"

Or explicitly: `@security-reviewer`

### 3. Read the report

Reports are written to `.agents-output/security/YYYY-MM-DD-<scope>-security-review.md`.

### 4. Fix findings (opt-in)

```
/security:fix .agents-output/security/2026-03-31-auth-security-review.md
/security:fix .agents-output/security/2026-03-31-auth-security-review.md --finding F-003
/security:fix .agents-output/security/2026-03-31-auth-security-review.md --dry-run
```

This runs in the main conversation (not a subagent) so you can confirm each fix before it's applied.

## Design Principles

### Review/Fix Boundary

| Action | Entry point | Write permission | Execution context |
|--------|------------|-----------------|-------------------|
| **Review** | `/security:review` | Read-only | Subagent (isolated context) |
| **Fix** | `/security:fix` | Write (opt-in) | Main conversation (user-visible) |
| **Gate** | Stop hook | Read-only | Subagent |

Why `/security:fix` runs in the main conversation instead of a subagent:
- Fix-verify requires user confirmation before each code change
- Prediction blocks must be visible to the user (not hidden in a black box)
- The fix needs full context from the review (findings, Codex threadId)
- Splitting reviewer → fixer by role is a subagent anti-pattern (telephone game)

### Content Layering (No Duplication)

| Layer | Contains | Does NOT contain |
|-------|----------|-----------------|
| Subagent prompt | Role, workflow steps, output location, completion checklist | Business logic, scoring formulas, MCP parameters |
| /security:review skill | Command interface, target resolution | Business logic, MCP parameters |
| /security:fix skill | Fix command interface, confirmation flow | Scoring formulas, MCP parameters |
| security-review-protocol SKILL.md | Cross-validation logic, conflict resolution, confidence scoring, Fix-Verify Loop (prediction blocks, iteration protocol, rollback rules, hypothesis ledger) | MCP call examples, report template |
| reference/ | MCP tool call patterns and parameters | Business logic |
| templates/ | Report markdown structure | Analysis logic |

Each piece of information lives in exactly one place. The subagent references the protocol skill; the command skills define the user-facing interface.

### Trust-but-Verify Protocol

The core insight: **run your own analysis first, then get a second opinion, then cross-reference.**

| Scenario | Handling |
|----------|---------|
| Both agree | High confidence (80%+), report directly |
| Semgrep found, Codex missed | Report — tool findings are reproducible (60%) |
| Codex found, Semgrep missed | Verify with Grep/AST first, then report (40%+) |
| Conflict | Deep verification, lean conservative |

### Conservative Principle

When Semgrep and Codex disagree, prefer false positives over false negatives. A false alarm wastes time; a missed vulnerability causes damage.

## Sample Output

See [sample-output/2026-03-25-test-vuln-security-review.md](sample-output/2026-03-25-test-vuln-security-review.md) for a real report generated from a test file containing intentional vulnerabilities (hardcoded secret, SQL injection, XSS).

Key observations from the sample:
- 3 HIGH findings confirmed by both sources (90% confidence each)
- 1 MEDIUM finding discovered by Codex only, then verified via custom Semgrep rule (75% confidence)
- Parameterized query correctly identified as SAFE (negative check)
- XSS severity conflict resolved conservatively (Semgrep WARNING → Codex HIGH → kept HIGH)

## Customization

### Adjust confidence weights

Edit `SKILL.md` section 3.2 to change the Semgrep/Codex weight ratio (default 60/40).

### Add project-specific patterns

Add custom Semgrep rules to the manual pattern check in `security-reviewer.md` Step 1.5.

### Change the Codex prompt strategy

Edit `reference/mcp-tools.md` Codex section to adjust what the Codex prompt asks for.

### Extend the Known Fix Gate

Add rows to the canonical fix pattern table in `SKILL.md` section 4.1 for vulnerability classes common in your codebase (e.g., SSRF, deserialization).

### Adjust rollback sensitivity

Edit the tiered rollback table in `SKILL.md` section 4.5. For stricter environments, promote "rule transferred" from "keep change" to "rollback."

### Change the iteration cap

The default is 3 rounds before human escalation (`SKILL.md` section 4.4). Reduce to 2 for faster feedback loops, or increase if your fix patterns require more exploration.
