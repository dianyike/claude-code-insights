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

# ── Test cases ──────────────────────────────────────────────────────
# (description, TOOL_INPUT_value, expected_exit, category)
# category: "unit" = pure parsing logic, no network
#           "live" = requires network (registry, OSV, npm view)

TESTS = [
    # ── Unit: Parsing & fail-closed ──
    ("invalid JSON → BLOCK",
     "not-json", 2, "unit"),
    ("empty TOOL_INPUT → pass",
     "", 0, "unit"),
    ("bare npm install → pass",
     '{"command": "npm install"}', 0, "unit"),
    ("non-npm: git status → pass",
     '{"command": "git status"}', 0, "unit"),
    ("non-npm: pip install → pass",
     '{"command": "pip install requests"}', 0, "unit"),
    ("non-npm: ls -la → pass",
     '{"command": "ls -la"}', 0, "unit"),

    # ── Unit: Shell operators ──
    # These still need network to check the extracted package, but we can test
    # parse-level behavior with packages that will be checked against whitelist.
    # We add "esbuild" (whitelisted) to isolate parsing from network.
    ("npm install esbuild&&npm test → only esbuild (whitelisted)",
     '{"command": "npm install esbuild&&npm test"}', 0, "unit"),
    ("npm install esbuild;npm test → only esbuild",
     '{"command": "npm install esbuild;npm test"}', 0, "unit"),
    ("npm install esbuild | grep x → only esbuild",
     '{"command": "npm install esbuild | grep x"}', 0, "unit"),

    # ── Unit: PM flags before verb (whitelisted pkg to avoid network) ──
    ("npm --registry https://... install esbuild",
     '{"command": "npm --registry https://registry.npmjs.org install esbuild"}', 0, "unit"),
    ("npm --registry=https://... install esbuild",
     '{"command": "npm --registry=https://custom install esbuild"}', 0, "unit"),
    ("npm --loglevel silent install esbuild",
     '{"command": "npm --loglevel silent install esbuild"}', 0, "unit"),
    ("yarn --cwd /tmp add esbuild",
     '{"command": "yarn --cwd /tmp add esbuild"}', 0, "unit"),
    ("pnpm --dir /tmp add esbuild",
     '{"command": "pnpm --dir /tmp add esbuild"}', 0, "unit"),

    # ── Unit: Post-verb flags (whitelisted pkg) ──
    ("npm install --tag beta esbuild",
     '{"command": "npm install --tag beta esbuild"}', 0, "unit"),
    ("npm install --fund esbuild (boolean, no value)",
     '{"command": "npm install --fund esbuild"}', 0, "unit"),
    ("npm install --loglevel silent esbuild",
     '{"command": "npm install --loglevel silent esbuild"}', 0, "unit"),
    ("npm install --save-prod esbuild",
     '{"command": "npm install --save-prod esbuild"}', 0, "unit"),
    ("npm install --no-fund esbuild (--no-xxx variant)",
     '{"command": "npm install --no-fund esbuild"}', 0, "unit"),
    ("pnpm add --prefer-offline esbuild",
     '{"command": "pnpm add --prefer-offline esbuild"}', 0, "unit"),
    ("pnpm add --store-dir /tmp esbuild",
     '{"command": "pnpm add --store-dir /tmp esbuild"}', 0, "unit"),

    # ── Unit: Unknown flags → BLOCK ──
    ("npm --unknown-flag install esbuild → BLOCK",
     '{"command": "npm --unknown-flag install esbuild"}', 2, "unit"),
    ("npm install --unknown-flag esbuild → BLOCK",
     '{"command": "npm install --unknown-flag esbuild"}', 2, "unit"),
    ("npm install --mystery=1 esbuild → BLOCK",
     '{"command": "npm install --mystery=1 esbuild"}', 2, "unit"),

    # ── Unit: npm install verb aliases (whitelisted pkg) ──
    ("npm in esbuild",
     '{"command": "npm in esbuild"}', 0, "unit"),
    ("npm ins esbuild",
     '{"command": "npm ins esbuild"}', 0, "unit"),
    ("npm isntall esbuild",
     '{"command": "npm isntall esbuild"}', 0, "unit"),

    # ── Unit: Non-registry specifiers → skip (no packages to check) ──
    ("npm alias → skip",
     '{"command": "npm install myalias@npm:react@18"}', 0, "unit"),
    ("SCP git URL → skip",
     '{"command": "npm install git@github.com:user/repo.git"}', 0, "unit"),
    ("github shorthand → skip",
     '{"command": "npm install user/repo"}', 0, "unit"),

    # ── Unit: Whitelist ──
    ("whitelisted package → pass",
     '{"command": "npm install esbuild"}', 0, "unit"),

    # ── Live: Version resolution (requires network + npm) ──
    ("lodash@^4.17.0 → resolve to exact",
     '{"command": "npm install lodash@^4.17.0"}', 0, "live"),
    ("express@latest → resolve dist-tag",
     '{"command": "npm install express@latest"}', 0, "live"),
    ("lodash@beta → BLOCK (no beta tag)",
     '{"command": "npm install lodash@beta"}', 2, "live"),

    # ── Live: Vulnerability detection ──
    ("lodash@4.17.20 → BLOCK (known CVE)",
     '{"command": "npm install lodash@4.17.20"}', 2, "live"),
    ("express latest → pass (clean)",
     '{"command": "npm install express"}', 0, "live"),

    # ── Live: Registry errors ──
    ("non-existent package → BLOCK",
     '{"command": "npm install zzz-fake-999"}', 2, "live"),

    # ── Live: Shell operators with real packages ──
    ("npm install lodash&&npm test → only lodash",
     '{"command": "npm install lodash&&npm test"}', 0, "live"),
    ("npm install lodash;npm test → only lodash",
     '{"command": "npm install lodash;npm test"}', 0, "live"),

    # ── Live: PM flags with real packages ──
    ("npm --registry https://... install lodash",
     '{"command": "npm --registry https://registry.npmjs.org install lodash"}', 0, "live"),
    ("npm install --tag beta lodash",
     '{"command": "npm install --tag beta lodash"}', 0, "live"),
    ("pnpm add --prefer-offline lodash",
     '{"command": "pnpm add --prefer-offline lodash"}', 0, "live"),
]


def run_test(description, tool_input, expected_exit):
    env = {**os.environ, "TOOL_INPUT": tool_input, "NPM_PKG_CHECK_SAFE_LIST": SAFE_LIST}
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

    for i, (desc, inp, expected, category) in enumerate(TESTS, 1):
        if category == "live" and not LIVE:
            skipped += 1
            print(f"  ⊘ #{i} {desc} (skipped: live)")
            continue

        status, msg = run_test(desc, inp, expected)
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
