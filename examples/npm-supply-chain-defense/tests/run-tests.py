#!/usr/bin/env python3
"""
Regression tests for npm-pkg-check.sh

Usage:
  python3 tests/run-tests.py           # unit tests only (no network, always reproducible)
  python3 tests/run-tests.py --live    # unit + live network integration tests

Script path is resolved relative to this file, not from ~/.claude/.
"""
import json, os, subprocess, sys
from pathlib import Path

# Resolve all paths relative to this file — no dependency on user HOME
_EXAMPLE_DIR = Path(__file__).resolve().parent.parent
SCRIPT = str(_EXAMPLE_DIR / "scripts" / "npm-pkg-check.sh")
SAFE_LIST = str(_EXAMPLE_DIR / "scripts" / "npm-safe-packages.txt")
LIVE = "--live" in sys.argv

import tempfile
_TMPDIR = tempfile.mkdtemp()
LOG_FILE = os.path.join(_TMPDIR, "npm-pkg-check.jsonl")
ALT_SAFE_LIST = os.path.join(_TMPDIR, "alt-safe-packages.txt")
with open(ALT_SAFE_LIST, "w") as f:
    f.write("lodash\n")

# ── Test cases ──────────────────────────────────────────────────────
# (description, TOOL_INPUT_value, expected_exit, category, extra_env)
# category: "unit" = pure parsing logic, no network
#           "live" = requires network (registry, OSV, npm view)

TESTS = [
    # ── Unit: Parsing & fail-closed ──
    ("invalid JSON → BLOCK",
     "not-json", 2, "unit", {}),
    ("empty TOOL_INPUT → pass",
     "", 0, "unit", {}),
    ("bare npm install → pass",
     '{"command": "npm install"}', 0, "unit", {}),
    ("non-npm: git status → pass",
     '{"command": "git status"}', 0, "unit", {}),
    ("non-npm: pip install → pass",
     '{"command": "pip install requests"}', 0, "unit", {}),
    ("non-npm: ls -la → pass",
     '{"command": "ls -la"}', 0, "unit", {}),

    # ── Unit: Shell operators ──
    # These still need network to check the extracted package, but we can test
    # parse-level behavior with packages that will be checked against whitelist.
    # We add "esbuild" (whitelisted) to isolate parsing from network.
    ("npm install esbuild&&npm test → only esbuild (whitelisted)",
     '{"command": "npm install esbuild&&npm test"}', 0, "unit", {}),
    ("npm install esbuild;npm test → only esbuild",
     '{"command": "npm install esbuild;npm test"}', 0, "unit", {}),
    ("npm install esbuild | grep x → only esbuild",
     '{"command": "npm install esbuild | grep x"}', 0, "unit", {}),

    # ── Unit: PM flags before verb (whitelisted pkg to avoid network) ──
    ("npm --registry https://... install esbuild",
     '{"command": "npm --registry https://registry.npmjs.org install esbuild"}', 0, "unit", {}),
    ("npm --registry=https://... install esbuild",
     '{"command": "npm --registry=https://custom install esbuild"}', 0, "unit", {}),
    ("npm --loglevel silent install esbuild",
     '{"command": "npm --loglevel silent install esbuild"}', 0, "unit", {}),
    ("yarn --cwd /tmp add esbuild",
     '{"command": "yarn --cwd /tmp add esbuild"}', 0, "unit", {}),
    ("pnpm --dir /tmp add esbuild",
     '{"command": "pnpm --dir /tmp add esbuild"}', 0, "unit", {}),

    # ── Unit: Post-verb flags (whitelisted pkg) ──
    ("npm install --tag beta esbuild",
     '{"command": "npm install --tag beta esbuild"}', 0, "unit", {}),
    ("npm install --fund esbuild (boolean, no value)",
     '{"command": "npm install --fund esbuild"}', 0, "unit", {}),
    ("npm install --loglevel silent esbuild",
     '{"command": "npm install --loglevel silent esbuild"}', 0, "unit", {}),
    ("npm install --save-prod esbuild",
     '{"command": "npm install --save-prod esbuild"}', 0, "unit", {}),
    ("npm install --no-fund esbuild (--no-xxx variant)",
     '{"command": "npm install --no-fund esbuild"}', 0, "unit", {}),
    ("pnpm add --prefer-offline esbuild",
     '{"command": "pnpm add --prefer-offline esbuild"}', 0, "unit", {}),
    ("pnpm add --store-dir /tmp esbuild",
     '{"command": "pnpm add --store-dir /tmp esbuild"}', 0, "unit", {}),

    # ── Unit: Unknown flags → BLOCK ──
    ("npm --unknown-flag install esbuild → BLOCK",
     '{"command": "npm --unknown-flag install esbuild"}', 2, "unit", {}),
    ("npm install --unknown-flag esbuild → BLOCK",
     '{"command": "npm install --unknown-flag esbuild"}', 2, "unit", {}),
    ("npm install --mystery=1 esbuild → BLOCK",
     '{"command": "npm install --mystery=1 esbuild"}', 2, "unit", {}),

    # ── Unit: npm install verb aliases (whitelisted pkg) ──
    ("npm in esbuild",
     '{"command": "npm in esbuild"}', 0, "unit", {}),
    ("npm ins esbuild",
     '{"command": "npm ins esbuild"}', 0, "unit", {}),
    ("npm isntall esbuild",
     '{"command": "npm isntall esbuild"}', 0, "unit", {}),

    # ── Unit: Non-registry specifiers → BLOCK ──
    ("npm alias → BLOCK",
     '{"command": "npm install myalias@npm:react@18"}', 2, "unit", {}),
    ("SCP git URL → BLOCK",
     '{"command": "npm install git@github.com:user/repo.git"}', 2, "unit", {}),
    ("github shorthand → BLOCK",
     '{"command": "npm install user/repo"}', 2, "unit", {}),
    ("git+ URL → BLOCK",
     '{"command": "npm install git+https://github.com/user/repo.git"}', 2, "unit", {}),
    ("tarball URL → BLOCK",
     '{"command": "npm install https://example.com/pkg.tgz"}', 2, "unit", {}),
    ("local tarball → BLOCK",
     '{"command": "npm install ./my-pkg-1.0.0.tgz"}', 2, "unit", {}),
    ("file: specifier → BLOCK",
     '{"command": "npm install file:../local-pkg"}', 2, "unit", {}),

    # ── Unit: Whitelist ──
    ("whitelisted package → pass",
     '{"command": "npm install esbuild"}', 0, "unit", {}),

    # ── Unit: Allowlist-only mode ──
    ("allowlist-only: whitelisted package → pass",
     '{"command": "npm install esbuild"}', 0, "unit", {"NPM_PKG_CHECK_MODE": "allowlist-only"}),
    ("allowlist-only: unlisted package → BLOCK",
     '{"command": "npm install lodash"}', 2, "unit", {"NPM_PKG_CHECK_MODE": "allowlist-only"}),

    # ── Unit: Global installs → BLOCK ──
    ("npm install -g esbuild → BLOCK",
     '{"command": "npm install -g esbuild"}', 2, "unit", {}),
    ("npm -g install esbuild → BLOCK",
     '{"command": "npm -g install esbuild"}', 2, "unit", {}),
    ("pnpm add -g esbuild → BLOCK",
     '{"command": "pnpm add -g esbuild"}', 2, "unit", {}),

    # ── Live: Version resolution (requires network + npm) ──
    ("lodash@^4.17.0 → resolve to exact",
     '{"command": "npm install lodash@^4.17.0"}', 0, "live", {}),
    ("express@latest → resolve dist-tag",
     '{"command": "npm install express@latest"}', 0, "live", {}),
    ("lodash@beta → BLOCK (no beta tag)",
     '{"command": "npm install lodash@beta"}', 2, "live", {}),

    # ── Live: Vulnerability detection ──
    ("lodash@4.17.20 → BLOCK (known CVE)",
     '{"command": "npm install lodash@4.17.20"}', 2, "live", {}),
    ("whitelisted lodash@4.17.20 → still BLOCK",
     '{"command": "npm install lodash@4.17.20"}', 2, "live", {"NPM_PKG_CHECK_SAFE_LIST": ALT_SAFE_LIST}),
    ("express latest → pass (clean)",
     '{"command": "npm install express"}', 0, "live", {}),

    # ── Live: Registry errors ──
    ("non-existent package → BLOCK",
     '{"command": "npm install zzz-fake-999"}', 2, "live", {}),

    # ── Live: Shell operators with real packages ──
    ("npm install lodash&&npm test → only lodash",
     '{"command": "npm install lodash&&npm test"}', 0, "live", {}),
    ("npm install lodash;npm test → only lodash",
     '{"command": "npm install lodash;npm test"}', 0, "live", {}),

    # ── Live: PM flags with real packages ──
    ("npm --registry https://... install lodash",
     '{"command": "npm --registry https://registry.npmjs.org install lodash"}', 0, "live", {}),
    ("npm install --tag beta lodash",
     '{"command": "npm install --tag beta lodash"}', 0, "live", {}),
    ("pnpm add --prefer-offline lodash",
     '{"command": "pnpm add --prefer-offline lodash"}', 0, "live", {}),

    # ── Unit: Scope detection (whitelisted pkg, no network) ──
    ("npm install --save-dev esbuild → scope=dev",
     '{"command": "npm install --save-dev esbuild"}', 0, "unit", {}),
    ("npm install -D esbuild → scope=dev",
     '{"command": "npm install -D esbuild"}', 0, "unit", {}),
    ("npm install --save-optional esbuild → scope=optional",
     '{"command": "npm install --save-optional esbuild"}', 0, "unit", {}),
    ("npm install --save-peer esbuild → scope=peer",
     '{"command": "npm install --save-peer esbuild"}', 0, "unit", {}),
    ("yarn add --dev esbuild → scope=dev",
     '{"command": "yarn add --dev esbuild"}', 0, "unit", {}),
    ("npm install esbuild → scope=prod (default)",
     '{"command": "npm install esbuild"}', 0, "unit", {}),
]


def run_test(description, tool_input, expected_exit, extra_env):
    env = {
        **os.environ,
        "TOOL_INPUT": tool_input,
        "NPM_PKG_CHECK_SAFE_LIST": SAFE_LIST,
        "NPM_PKG_CHECK_LOG": LOG_FILE,
        **extra_env,
    }
    try:
        cp = subprocess.run(
            ["bash", SCRIPT],
            env=env, capture_output=True, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        return "FAIL", f"{description} — timed out"

    if cp.returncode == expected_exit:
        return "PASS", description
    else:
        stdout_preview = cp.stdout.strip()[:120] if cp.stdout.strip() else "(no output)"
        return "FAIL", f"{description} — expected exit {expected_exit}, got {cp.returncode}\n    {stdout_preview}"


def main():
    if not os.path.isfile(SCRIPT):
        print(f"ERROR: script not found at {SCRIPT}")
        print("Make sure you run this from the repo root or the tests/ directory.")
        sys.exit(1)

    print(f"Script: {SCRIPT}")
    print(f"Mode:   {'unit + live' if LIVE else 'unit only'}")
    print()

    passed = failed = skipped = 0
    failures = []

    for i, (desc, inp, expected, category, extra_env) in enumerate(TESTS, 1):
        if category == "live" and not LIVE:
            skipped += 1
            print(f"  ⊘ #{i} {desc} (skipped: live)")
            continue

        status, msg = run_test(desc, inp, expected, extra_env)
        if status == "PASS":
            passed += 1
            print(f"  ✓ #{i} {desc}")
        else:
            failed += 1
            failures.append(f"  ✗ #{i} {msg}")
            print(f"  ✗ #{i} {msg}")

    print(f"\n{'='*60}")
    total_run = passed + failed
    print(f"Result: {passed} passed, {failed} failed, {skipped} skipped / {len(TESTS)} total")

    # ── Verify structured log ──
    # Valid taxonomies — any value outside these sets is a test failure
    VALID_REASON_CODES = {
        "whitelisted", "clean", "has_risks",
        "package_not_found", "version_not_resolved", "known_vulnerability",
        "low_downloads_with_scripts", "core_signal_unavailable",
        "unknown_option", "parse_error", "global_install", "not_in_allowlist",
        "non_registry_specifier",
    }
    VALID_DECISIONS = {"allow", "allow_with_warning", "blocked"}

    log_ok = True
    log_entries = []
    if os.path.isfile(LOG_FILE):
        with open(LOG_FILE) as f:
            log_lines = [line.strip() for line in f if line.strip()]
        print(f"\nLog entries: {len(log_lines)} written to {LOG_FILE}")

        required_fields = {"ts", "pm", "package", "scope", "decision", "reason_code"}
        for i, line in enumerate(log_lines):
            try:
                entry = json.loads(line)
                log_entries.append(entry)
                missing = required_fields - set(entry.keys())
                if missing:
                    print(f"  ✗ Log entry #{i+1} missing fields: {missing}")
                    log_ok = False
                # Verify reason_code is from taxonomy
                rc = entry.get("reason_code")
                if rc not in VALID_REASON_CODES:
                    print(f"  ✗ Log entry #{i+1} has invalid reason_code: '{rc}'")
                    log_ok = False
                # Verify decision is from taxonomy
                dec = entry.get("decision")
                if dec not in VALID_DECISIONS:
                    print(f"  ✗ Log entry #{i+1} has invalid decision: '{dec}'")
                    log_ok = False
            except json.JSONDecodeError:
                print(f"  ✗ Log entry #{i+1} is not valid JSON")
                log_ok = False

        # Verify scope detection in log
        scope_checks = {"dev": False, "optional": False, "peer": False, "prod": False}
        for entry in log_entries:
            s = entry.get("scope")
            if s in scope_checks:
                scope_checks[s] = True
        for scope_name, found in scope_checks.items():
            if not found and not skipped:
                print(f"  ⚠ No log entry with scope={scope_name} (may be in skipped live tests)")

        # Verify specific reason_codes appear for known test cases
        reason_codes_found = {e.get("reason_code") for e in log_entries}
        # parse_error should appear (from test #1: invalid JSON)
        if "parse_error" not in reason_codes_found:
            print("  ✗ Expected reason_code='parse_error' from invalid JSON test — not found")
            log_ok = False
        # whitelisted should appear (from esbuild tests)
        if "whitelisted" not in reason_codes_found:
            print("  ✗ Expected reason_code='whitelisted' from esbuild tests — not found")
            log_ok = False
        # unknown_option should appear (from unknown flag tests)
        if "unknown_option" not in reason_codes_found:
            print("  ✗ Expected reason_code='unknown_option' from unknown flag tests — not found")
            log_ok = False
        # global_install should appear (from npm install -g test)
        if "global_install" not in reason_codes_found:
            print("  ✗ Expected reason_code='global_install' from global install tests — not found")
            log_ok = False
        # not_in_allowlist should appear (from allowlist-only test)
        if "not_in_allowlist" not in reason_codes_found:
            print("  ✗ Expected reason_code='not_in_allowlist' from allowlist-only test — not found")
            log_ok = False
        # non_registry_specifier should appear (from git/tarball/alias tests)
        if "non_registry_specifier" not in reason_codes_found:
            print("  ✗ Expected reason_code='non_registry_specifier' from non-registry specifier tests — not found")
            log_ok = False

        if log_ok:
            print("  ✓ All log entries have valid structure, reason_codes, and decisions")
        else:
            failed += 1
            failures.append("  ✗ Log validation failed — see details above")
    else:
        print(f"\n✗ No log file generated at {LOG_FILE}")
        failed += 1
        failures.append("  ✗ No log file generated")

    # ── Cleanup ──
    import shutil
    shutil.rmtree(_TMPDIR, ignore_errors=True)

    print(f"\n{'='*60}")
    total_run = passed + failed
    print(f"Result: {passed} passed, {failed} failed, {skipped} skipped / {len(TESTS)} total")

    if failures:
        print("\nFailures:")
        for f in failures:
            print(f)
        sys.exit(1)
    else:
        if skipped:
            print(f"\nAll {total_run} executed tests passed. Run with --live for full suite.")
        else:
            print("\nAll tests passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
