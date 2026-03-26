# npm Supply Chain Defense — Claude Code 3-Layer Architecture

A working example of npm supply chain protection using Claude Code's Hook + MCP mechanisms. Automatically intercepts suspicious packages before AI-driven installs.

## Threat Model

AI coding assistants autonomously run `npm install` / `yarn add` / `pnpm add` / `bun add` on behalf of users. This introduces threats that don't exist in manual workflows:

| Threat | Description | Frequency |
|--------|-------------|-----------|
| **Package hallucination** | AI invents a package name that doesn't exist on npm — or worse, matches a typosquat someone registered to intercept this exact scenario | ~1 in 15 AI-assisted additions* |
| **Version hallucination** | Package exists, but AI specifies a version that doesn't — or one with known CVEs | More common than package hallucination* |
| **Malicious install scripts** | `postinstall` / `preinstall` hooks exfiltrate credentials, install backdoors, or download remote payloads | Ongoing supply chain risk |
| **Typosquatting** | `lodash` vs `l0dash` — a single character difference leads to a malicious package | Registry-level threat |
| **Vulnerable pinning** | AI pins to an old version with known prototype pollution, ReDoS, or other CVEs | Common with outdated training data |

\* Frequency estimates from community feedback on [anthropics/claude-code#39421](https://github.com/anthropics/claude-code/issues/39421).

## Architecture

```text
Claude runs: npm install foo
        │
        ▼
┌─ Layer 1: .npmrc ─────────────────┐
│  ignore-scripts=true              │
│  Blocks all preinstall/postinstall│
└───────────────────────────────────┘
        │
        ▼
┌─ Layer 2: PreToolUse Hook ────────┐
│  npm-pkg-check.sh                 │
│  ✓ Safe → one-line output, pass   │
│  🚫 Suspicious → exit 2, block    │
└───────────────────────────────────┘
        │
        ▼
┌─ Layer 3: Semgrep Supply Chain ───┐
│  Scans lockfile for known CVEs    │
│  Detects code-level malice        │
└───────────────────────────────────┘
```

## What Each Layer Defends Against

| Layer | Threat | Mechanism |
|-------|--------|-----------|
| **1** | Malicious `postinstall`/`preinstall` scripts | `.npmrc` globally blocks install scripts |
| **2** | Typosquatting, vulnerable versions, nonexistent packages, unknown CLI flags, version hallucination | Hook queries npm registry + OSV.dev, resolves versions, validates CLI syntax |
| **3** | Known CVEs, malicious code executed at `import` time | Semgrep `semgrep_scan_supply_chain` MCP tool |

## Quick Start

```bash
# 1. Copy .npmrc to your project
cp .npmrc /path/to/your/project/

# 2. Install hook script
mkdir -p ~/.claude/scripts
cp scripts/npm-pkg-check.sh ~/.claude/scripts/
cp scripts/npm-safe-packages.txt ~/.claude/scripts/
chmod +x ~/.claude/scripts/npm-pkg-check.sh

# 3. Add hooks to ~/.claude/settings.json (see settings-snippet.jsonc)

# 4. Enable Semgrep plugin in ~/.claude/settings.json
```

## Files

```text
npm-supply-chain-defense/
├── .npmrc                          # Layer 1: ignore-scripts=true
├── scripts/
│   ├── npm-pkg-check.sh           # Layer 2: pre-install check (Python inside bash)
│   └── npm-safe-packages.txt      # Whitelist for packages needing install scripts
├── tests/
│   └── run-tests.py               # 48 regression tests (37 unit + 11 live)
├── settings-snippet.jsonc          # Hook configuration for settings.json
├── README.md                       # This file (English)
└── README.zh-TW.md                # Traditional Chinese version
```

## Hook Behavior

### Allow (exit 0)

| Scenario | Output |
|----------|--------|
| `git status` (non-npm command) | none |
| `npm install` (bare, from lockfile) | none |
| `npm install esbuild` (whitelisted) | `✓ esbuild (whitelisted)` |
| `npm install lodash` (popular, clean) | `✓ lodash — 125M/week, 3 maintainers` |
| `npm install express@latest` (dist-tag resolved) | `✓ express@5.2.1 — 91M/week, ...` |

### Block (exit 2)

| Scenario | Output |
|----------|--------|
| `npm install zzz-fake-pkg` (not on registry) | `⚠ not found on npm registry` |
| `npm install lodash@4.17.20` (known CVE) | `🚫 BLOCKED (3 known vuln(s): GHSA-...)` |
| `npm install lodash@beta` (version unresolvable) | `🚫 BLOCKED (version not resolved)` |
| `npm install --mystery-flag lodash` (unknown CLI flag) | `🚫 BLOCKED (unrecognized option)` |
| Low downloads + install scripts | `🚫 BLOCKED (low downloads, has install scripts)` |
| Invalid `TOOL_INPUT` JSON | `⚠ blocking as precaution` |
| Registry unreachable (core signal) | `🚫 BLOCKED (registry unreachable)` |

## Design Principles

### Fail-closed

The hook blocks by default when it cannot determine safety. Core signals must succeed for a package to be allowed; supplementary signals degrade gracefully.

| Signal | Type | On failure | Rationale |
|--------|------|------------|-----------|
| Registry metadata | **Core** | **Block** | Can't verify package exists |
| Version resolution | **Core** | **Block** | Can't check the actual version being installed |
| Install scripts check | **Core** | **Block** | Can't determine if scripts are safe |
| OSV vulnerability check | Supplementary | Warning only | CVE database may be temporarily down |
| Download count | Supplementary | Warning only | Stats API is non-critical |

This means: if npm's registry is unreachable, the hook blocks. If OSV.dev is down, the hook warns but allows (since the registry check already passed).

### Per-PM option parsing

The hook validates CLI flags against per-package-manager arity tables (npm, yarn, pnpm, bun). Unknown flags are blocked to prevent parser bypass.

- Known value-taking flags (e.g. `--registry`, `--tag`, `--cwd`) correctly consume their next token
- Boolean flags (e.g. `--fund`, `--save-dev`) do not
- `--flag=value` syntax validates the base flag against the same table
- `--no-xxx` variants of boolean flags are auto-recognized
- npm install verb aliases (`in`, `ins`, `isnt`, `isntall`, etc.) are supported
- Shell operators (`&&`, `||`, `;`, `|`) stop parsing — only the first command is checked

### Version resolution

| Specifier | Resolution method |
|-----------|-------------------|
| `4.17.21` (exact semver) | Used directly |
| `latest`, `beta` (dist-tag) | Looked up from registry `dist-tags` |
| `^4.17.0`, `~2.0` (range) | Resolved via `npm view` with 3s timeout |
| Unresolvable | **Blocked** (fail-closed) |

### Dependency scope detection

The hook detects dependency scope from CLI flags and records it in the structured log:

| Flag | Scope |
|------|-------|
| `--save-dev`, `-D` | `dev` |
| `--save-optional`, `-O` | `optional` |
| `--save-peer` | `peer` |
| `--save-prod`, `-P`, `--save`, `-S` (or no flag) | `prod` |

Scope is logged but does not currently change block policy. This data enables future analysis of dev vs prod failure rates.

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `NPM_PKG_CHECK_SAFE_LIST` | `~/.claude/scripts/npm-safe-packages.txt` | Override whitelist file path |
| `NPM_PKG_CHECK_LOG` | `~/.claude/logs/npm-pkg-check.jsonl` | Override structured log file path |

## Structured Logging

Every check decision is logged as a JSONL entry to `NPM_PKG_CHECK_LOG`:

```json
{
  "ts": "2026-03-26T16:43:55Z",
  "pm": "npm",
  "package": "lodash",
  "spec": "4.17.20",
  "resolved_version": "4.17.20",
  "scope": "prod",
  "decision": "blocked",
  "reason_code": "known_vulnerability",
  "reason_detail": "GHSA-29mw-wpgm-hmr9, GHSA-35jh-r3h4-6jhm, GHSA-xxjr-mmjv-4gpg"
}
```

### Taxonomy

**`decision`** (fixed enum):

| Value | Meaning |
|-------|---------|
| `allow` | Package passed all checks |
| `allow_with_warning` | Allowed but has non-blocking risk signals |
| `blocked` | Install prevented |

**`reason_code`** (fixed enum):

| Value | Meaning |
|-------|---------|
| `clean` | No risks detected |
| `whitelisted` | Package in safe list, skipped checks |
| `has_risks` | Non-blocking risks present |
| `package_not_found` | Package does not exist on registry |
| `version_not_resolved` | Version spec could not be resolved to exact semver |
| `known_vulnerability` | OSV.dev returned CVE/GHSA matches |
| `low_downloads_with_scripts` | Low weekly downloads AND has install scripts |
| `core_signal_unavailable` | Registry or version manifest unreachable |
| `unknown_option` | CLI flag not in arity table |
| `parse_error` | TOOL_INPUT JSON could not be parsed |

**`reason_detail`** (optional free text): vulnerability IDs, error messages, risk descriptions.

This separation allows `GROUP BY reason_code` for analytics without string parsing.

## Running Tests

```bash
# Unit tests only (no network, fully reproducible)
python3 tests/run-tests.py

# Unit + live integration tests (requires network)
python3 tests/run-tests.py --live
```

### Test design

- **Unit tests** (37): Use whitelisted packages (`esbuild`) to isolate parsing logic from network. Verify exit codes, scope detection, log structure, `reason_code` taxonomy, and `decision` taxonomy.
- **Live tests** (11): Hit real npm registry, OSV.dev, and `npm view`. Verify version resolution, vulnerability detection, and real-world package checks.
- **Log validation**: Tests verify every JSONL entry has required fields, `reason_code` is from the fixed taxonomy, `decision` is from the fixed taxonomy, and specific `reason_code` values appear for known test cases. Log validation failure causes the test run to fail (not just warn).
- **Environment isolation**: The test harness overrides `NPM_PKG_CHECK_SAFE_LIST` and `NPM_PKG_CHECK_LOG` via environment variables, so results are independent of the user's home directory.

```text
Result: 37 passed, 0 failed, 11 skipped / 48 total
All 37 executed tests passed. Run with --live for full suite.
```

## Limitations

These three layers cannot defend against:

- **RDD (Remote Dynamic Dependency) attacks** — payload fetched at runtime, invisible to static analysis
- **Zero-day hijacks** — legitimate package compromised before CVE is published
- **Highly obfuscated malicious code** — may evade Semgrep rules
- **Unlisted PM flags** — if a package manager adds new flags, they will be blocked until added to the arity table
- **Post-install import validation** — the hook checks the package itself, not whether the AI's `import` statements match the package's actual exports (complementary CI-level tools like [Open Code Review](https://github.com/opencodereview/cli) address this)

These require runtime defenses (Docker network restrictions, Node.js `--experimental-permission`) at the DevOps/infra level.
