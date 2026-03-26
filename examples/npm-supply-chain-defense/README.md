# npm Supply Chain Defense — Claude Code 3-Layer Architecture

A working example of npm supply chain protection using Claude Code's Hook + MCP mechanisms. Automatically intercepts suspicious packages before AI-driven installs.

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
| **2** | Typosquatting, vulnerable versions, nonexistent packages, unknown CLI flags | Hook queries npm registry + OSV.dev, resolves versions, validates CLI syntax |
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
│   └── run-tests.py               # 42 regression tests (31 unit + 11 live)
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

Core signals block on failure. Supplementary signals degrade gracefully.

| Signal | Type | On failure |
|--------|------|------------|
| Registry metadata | Core | **Block** |
| Version resolution | Core | **Block** |
| Install scripts check | Core | **Block** |
| OSV vulnerability check | Supplementary | Warning only |
| Download count | Supplementary | Warning only |

### Per-PM option parsing

The hook validates CLI flags against per-package-manager arity tables (npm, yarn, pnpm, bun). Unknown flags are blocked to prevent parser bypass.

Known value-taking flags (e.g. `--registry`, `--tag`, `--cwd`) correctly consume their next token. Boolean flags (e.g. `--fund`, `--save-dev`) do not. `--flag=value` syntax is validated against the same table.

### Version resolution

| Specifier | Resolution method |
|-----------|-------------------|
| `4.17.21` (exact semver) | Used directly |
| `latest`, `beta` (dist-tag) | Looked up from registry `dist-tags` |
| `^4.17.0`, `~2.0` (range) | Resolved via `npm view` with 3s timeout |
| Unresolvable | **Blocked** |

### Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `NPM_PKG_CHECK_SAFE_LIST` | `~/.claude/scripts/npm-safe-packages.txt` | Override whitelist path |

## Running Tests

```bash
# Unit tests only (no network, fully reproducible)
python3 tests/run-tests.py

# Unit + live integration tests (requires network)
python3 tests/run-tests.py --live
```

Unit tests use whitelisted packages to isolate parsing logic from network. The test harness overrides `NPM_PKG_CHECK_SAFE_LIST` to point at the repo's whitelist file, so results are independent of the user's home directory.

```text
Result: 31 passed, 0 failed, 11 skipped / 42 total
All 31 executed tests passed. Run with --live for full suite.
```

## Limitations

These three layers cannot defend against:

- **RDD (Remote Dynamic Dependency) attacks** — payload fetched at runtime, invisible to static analysis
- **Zero-day hijacks** — legitimate package compromised before CVE is published
- **Highly obfuscated malicious code** — may evade Semgrep rules
- **Unlisted PM flags** — if a package manager adds new flags, they will be blocked until added to the arity table

These require runtime defenses (Docker network restrictions, Node.js `--experimental-permission`) at the DevOps/infra level.
