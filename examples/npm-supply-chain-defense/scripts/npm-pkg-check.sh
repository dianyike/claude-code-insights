#!/usr/bin/env bash
# npm-pkg-check.sh — Pre-install safety check for npm packages
# Called by Claude Code PreToolUse hook before npm install / bun add / yarn add
#
# Design: fail-closed. If parsing fails, python3 is unavailable,
# network is down for core signals, or a version can't be resolved,
# the script blocks (exit 2).
#
# Exit 0 = allow install to proceed
# Exit 2 = block

# Require python3 upfront
if ! command -v python3 &>/dev/null; then
  echo "⚠️ npm-pkg-check: python3 required but not found — blocking as precaution"
  exit 2
fi

# Python controls all logic AND the exit code directly.
# No bash grep on output — exit code is authoritative.
exec python3 << 'PYEOF'
import json, os, re, shlex, subprocess, sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError

# ── Config ──────────────────────────────────────────────────────────
MIN_WEEKLY_DOWNLOADS = 100
MAX_AGE_DAYS_FOR_NEW_WARNING = 7
SAFE_PACKAGES_FILE = os.environ.get(
    "NPM_PKG_CHECK_SAFE_LIST",
    os.path.expanduser("~/.claude/scripts/npm-safe-packages.txt"),
)
LOG_FILE = os.environ.get(
    "NPM_PKG_CHECK_LOG",
    os.path.expanduser("~/.claude/logs/npm-pkg-check.jsonl"),
)
HTTP_TIMEOUT = 5
NPM_VIEW_TIMEOUT = 3
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?$")

PACKAGE_MANAGERS = {"npm", "yarn", "bun", "pnpm"}
SHELL_OPERATORS = {"&&", "||", ";", "|", "&"}

# Per-PM install verb aliases (from each PM's --help / docs)
INSTALL_VERBS = {
    "npm": {"install", "i", "in", "ins", "inst", "insta", "instal",
            "isnt", "isnta", "isntal", "isntall", "add"},
    "yarn": {"install", "add"},
    "pnpm": {"install", "add", "i"},
    "bun": {"install", "add", "i"},
}

# ── Per-PM option arity tables ──────────────────────────────────────
# 0 = boolean flag (no value), 1 = takes next token as value
# Unknown flags → fail-closed (block).
OPTION_ARITY = {
    "npm": {
        "--registry": 1, "--userconfig": 1, "--globalconfig": 1,
        "--prefix": 1, "--cache": 1, "--loglevel": 1, "--otp": 1,
        "--workspace": 1, "-w": 1, "--workspaces": 0,
        "--include-workspace-root": 0,
        "--verbose": 0, "--quiet": 0, "--silent": 0,
        "--global": 0, "-g": 0, "--json": 0, "--long": 0,
        "--timing": 0, "--color": 0, "--no-color": 0,
        "--unicode": 0, "--no-unicode": 0,
        "--save": 0, "-S": 0, "--save-dev": 0, "-D": 0,
        "--save-optional": 0, "-O": 0, "--save-exact": 0, "-E": 0,
        "--save-peer": 0, "--save-prod": 0, "-P": 0, "--no-save": 0,
        "--save-bundle": 0, "-B": 0,
        "--tag": 1, "-t": 1,
        "--dry-run": 0, "--force": 0, "-f": 0,
        "--legacy-peer-deps": 0, "--strict-peer-deps": 0,
        "--legacy-bundling": 0, "--global-style": 0,
        "--prefer-dedupe": 0, "--no-bin-links": 0,
        "--no-optional": 0, "--ignore-scripts": 0,
        "--no-audit": 0, "--no-fund": 0, "--fund": 0, "--audit": 0,
        "--package-lock-only": 0, "--no-package-lock": 0,
        "--foreground-scripts": 0, "--install-strategy": 1,
        "--omit": 1, "--include": 1, "--install-links": 0,
        "--cpu": 1, "--os": 1, "--libc": 1,
    },
    "yarn": {
        "--cwd": 1, "--mutex": 1, "--registry": 1,
        "--modules-folder": 1, "--cache-folder": 1,
        "--dev": 0, "-D": 0, "--peer": 0, "-P": 0,
        "--optional": 0, "-O": 0, "--exact": 0, "-E": 0,
        "--tilde": 0, "-T": 0, "--ignore-scripts": 0,
        "--no-lockfile": 0, "--frozen-lockfile": 0,
        "--pure-lockfile": 0, "--check-files": 0,
        "--silent": 0, "--verbose": 0, "--json": 0,
        "--force": 0, "--flat": 0, "--production": 0,
        "--non-interactive": 0, "--ignore-engines": 0,
        "--ignore-platform": 0, "--ignore-optional": 0,
        "--offline": 0, "--prefer-offline": 0,
        "--audit": 0, "--no-bin-links": 0,
        "--network-timeout": 1, "--network-concurrency": 1,
    },
    "pnpm": {
        "--dir": 1, "-C": 1, "--filter": 1, "--registry": 1,
        "--workspace": 1, "-w": 0, "--recursive": 0, "-r": 0,
        "--save-dev": 0, "-D": 0, "--save-optional": 0, "-O": 0,
        "--save-exact": 0, "-E": 0, "--save-peer": 0, "--save-prod": 0,
        "--global": 0, "-g": 0, "--no-optional": 0,
        "--ignore-scripts": 0, "--force": 0,
        "--loglevel": 1, "--silent": 0, "--reporter": 1,
        "--prefer-offline": 0, "--offline": 0,
        "--store-dir": 1, "--global-dir": 1, "--virtual-store-dir": 1,
        "--save-catalog": 0, "--allow-build": 0,
        "--workspace-root": 0, "--frozen-lockfile": 0,
        "--strict-peer-dependencies": 0, "--no-lockfile": 0,
        "--shamefully-hoist": 0, "--no-hoist": 0,
    },
    "bun": {
        "--cwd": 1, "--registry": 1,
        "--dev": 0, "-d": 0, "--optional": 0,
        "--exact": 0, "-E": 0, "--global": 0, "-g": 0,
        "--force": 0, "--no-save": 0, "--dry-run": 0,
        "--verbose": 0, "--silent": 0, "--no-progress": 0,
        "--backend": 1, "--no-cache": 0, "--frozen-lockfile": 0,
        "--production": 0, "--trust": 0,
    },
}

# ── Per-PM scope detection flags ────────────────────────────────────
# Maps flags to dependency scope. Checked after install verb.
SCOPE_FLAGS = {
    "npm": {
        "--save-dev": "dev", "-D": "dev",
        "--save-optional": "optional", "-O": "optional",
        "--save-peer": "peer",
        "--save-prod": "prod", "-P": "prod", "--save": "prod", "-S": "prod",
    },
    "yarn": {
        "--dev": "dev", "-D": "dev",
        "--peer": "peer", "-P": "peer",
        "--optional": "optional", "-O": "optional",
    },
    "pnpm": {
        "--save-dev": "dev", "-D": "dev",
        "--save-optional": "optional", "-O": "optional",
        "--save-peer": "peer",
        "--save-prod": "prod",
    },
    "bun": {
        "--dev": "dev", "-d": "dev",
        "--optional": "optional",
    },
}

# ── Helpers ─────────────────────────────────────────────────────────
def http_get_json(url):
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            return json.loads(resp.read())
    except Exception:
        return None

def http_post_json(url, payload):
    try:
        data = json.dumps(payload).encode()
        req = Request(url, data=data, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            return json.loads(resp.read())
    except Exception:
        return None

def load_safe_list():
    try:
        with open(SAFE_PACKAGES_FILE) as f:
            return {line.strip() for line in f if line.strip() and not line.startswith("#")}
    except FileNotFoundError:
        return set()

def shell_tokenize(command):
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        return list(lexer)
    except ValueError:
        return command.split()

def get_abbreviated_metadata(pkg):
    try:
        req = Request(
            f"https://registry.npmjs.org/{pkg}",
            headers={"Accept": "application/vnd.npm.install-v1+json"},
        )
        with urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            return json.loads(resp.read())
    except URLError as e:
        if hasattr(e, "code") and e.code == 404:
            return {"error": "Not found"}
        return None
    except Exception:
        return None

def resolve_option(pm, flag, arity_table):
    if flag == "--":
        return 0, True
    if "=" in flag:
        base = flag.split("=", 1)[0]
        table = arity_table.get(pm, {})
        if base in table:
            return 0, True
        if base.startswith("--no-"):
            pos = "--" + base[5:]
            if pos in table and table[pos] == 0:
                return 0, True
        return 0, False
    table = arity_table.get(pm, {})
    if flag in table:
        return table[flag], True
    if flag.startswith("--no-"):
        base = "--" + flag[5:]
        if base in table and table[base] == 0:
            return 0, True
    return 0, False

def extract_packages(words):
    """
    State machine parser. Returns (packages, pm, scope) or ("__BLOCK__:reason", None, None).
    packages: list of (name, version_spec)
    pm: detected package manager
    scope: "prod" | "dev" | "optional" | "peer" (from flags, default "prod")
    """
    packages = []
    state = "find_pm"
    current_pm = None
    skip_next = False
    end_of_options = False
    detected_scope = "prod"  # default

    for word in words:
        if skip_next:
            skip_next = False
            continue

        if word in SHELL_OPERATORS:
            break

        if state == "find_pm":
            if word in PACKAGE_MANAGERS:
                current_pm = word
                state = "find_verb"
            continue

        if state == "find_verb":
            if word == "--":
                end_of_options = True
                continue
            if word.startswith("-") and not end_of_options:
                arity, known = resolve_option(current_pm, word, OPTION_ARITY)
                if not known:
                    return f"__BLOCK__:unrecognized option '{word}' for {current_pm}", None, None
                if arity == 1:
                    skip_next = True
                continue
            if word in INSTALL_VERBS.get(current_pm, set()):
                state = "packages"
                end_of_options = False
                continue
            else:
                break

        if state == "packages":
            if word == "--":
                end_of_options = True
                continue
            if word.startswith("-") and not end_of_options:
                # Check scope flags before option validation
                scope_table = SCOPE_FLAGS.get(current_pm, {})
                base_flag = word.split("=", 1)[0] if "=" in word else word
                if base_flag in scope_table:
                    detected_scope = scope_table[base_flag]

                arity, known = resolve_option(current_pm, word, OPTION_ARITY)
                if not known:
                    return f"__BLOCK__:unrecognized option '{word}' for {current_pm}", None, None
                if arity == 1:
                    skip_next = True
                continue

            skip_prefixes = ("git:", "git+", "git@", "http:", "https:", "file:", "./", "../", "/", "npm:")
            if any(word.startswith(p) for p in skip_prefixes):
                continue
            if word.endswith(".tgz") or word.endswith(".tar.gz"):
                continue
            if "npm:" in word:
                continue
            if "/" in word and not word.startswith("@"):
                continue

            if word.startswith("@") and "/" in word:
                parts = word.split("/", 1)
                scope_part = parts[0]
                rest = parts[1]
                if "@" in rest:
                    at_idx = rest.index("@")
                    name = scope_part + "/" + rest[:at_idx]
                    version = rest[at_idx + 1:]
                else:
                    name = word
                    version = ""
            else:
                if "@" in word:
                    at_idx = word.index("@")
                    name = word[:at_idx]
                    version = word[at_idx + 1:]
                else:
                    name = word
                    version = ""

            if re.match(r"^(@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*$", name):
                packages.append((name, version))

    return packages, current_pm, detected_scope

def resolve_version(pkg, spec, abbrev):
    if not spec:
        latest = (abbrev or {}).get("dist-tags", {}).get("latest")
        return latest, True, None
    if SEMVER_RE.fullmatch(spec):
        return spec, True, None
    tags = (abbrev or {}).get("dist-tags", {})
    if spec in tags:
        return tags[spec], True, None
    try:
        cp = subprocess.run(
            ["npm", "view", f"{pkg}@{spec}", "version", "--json"],
            capture_output=True, text=True, timeout=NPM_VIEW_TIMEOUT, check=False,
        )
    except FileNotFoundError:
        return None, False, "npm not available"
    except subprocess.TimeoutExpired:
        return None, False, "npm view timed out"
    if cp.returncode != 0 or not cp.stdout.strip():
        return None, False, f"unable to resolve '{spec}'"
    try:
        out = json.loads(cp.stdout)
        version = out[-1] if isinstance(out, list) else out
    except json.JSONDecodeError:
        version = cp.stdout.strip()
    if isinstance(version, str) and SEMVER_RE.fullmatch(version):
        return version, True, None
    return None, False, f"resolved value '{version}' is not exact semver"

def check_install_scripts(pkg, version):
    data = http_get_json(f"https://registry.npmjs.org/{pkg}/{version}")
    if data is None:
        return None
    scripts = data.get("scripts", {})
    return any(k in scripts for k in ("preinstall", "install", "postinstall"))

def check_vulns(pkg, version):
    if not version or not SEMVER_RE.fullmatch(version):
        return 0, []
    payload = {"package": {"name": pkg, "ecosystem": "npm"}, "version": version}
    data = http_post_json("https://api.osv.dev/v1/query", payload)
    if not data:
        return 0, []
    vulns = data.get("vulns", [])
    ids = [v.get("id", "unknown") for v in vulns[:3]]
    return len(vulns), ids

def get_downloads(pkg):
    data = http_get_json(f"https://api.npmjs.org/downloads/point/last-week/{pkg}")
    if not data:
        return 0
    return data.get("downloads", 0)

# ── Structured logging ──────────────────────────────────────────────
def write_log(entry):
    """Append a JSONL entry to the log file. Never block on failure."""
    try:
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # logging must never block the hook

def make_log_entry(pm, pkg, spec, resolved_version, dep_scope, decision, reason_code, reason_detail=None):
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pm": pm,
        "package": pkg,
        "spec": spec or None,
        "resolved_version": resolved_version,
        "scope": dep_scope,
        "decision": decision,
        "reason_code": reason_code,
    }
    if reason_detail:
        entry["reason_detail"] = reason_detail
    return entry

# ── Main ────────────────────────────────────────────────────────────
tool_input = os.environ.get("TOOL_INPUT", "")
if not tool_input:
    sys.exit(0)

try:
    data = json.loads(tool_input)
except (json.JSONDecodeError, TypeError):
    print("⚠️ npm-pkg-check: failed to parse TOOL_INPUT — blocking as precaution")
    write_log(make_log_entry(None, None, None, None, None, "blocked", "parse_error", "invalid_tool_input_json"))
    sys.exit(2)

command = data.get("command", "")
if not command:
    sys.exit(0)

words = shell_tokenize(command)
result = extract_packages(words)

# extract_packages returns a tuple of 3; string on parse failure
if isinstance(result[0], str) and result[0].startswith("__BLOCK__:"):
    reason = result[0].split(":", 1)[1]
    print(f"🚫 BLOCKED — command parse error: {reason}")
    write_log(make_log_entry(None, None, None, None, None, "blocked", "unknown_option", reason))
    sys.exit(2)

packages, detected_pm, dep_scope = result
if not packages:
    sys.exit(0)

safe_list = load_safe_list()
blocked = False

for pkg, spec in packages:
    if pkg in safe_list:
        print(f"✓ {pkg} (whitelisted)")
        write_log(make_log_entry(detected_pm, pkg, spec, None, dep_scope, "allow", "whitelisted", None))
        continue

    # ── Core signal: registry metadata (fail-closed) ──
    abbrev = get_abbreviated_metadata(pkg)
    if abbrev is None:
        print(f"🚫 {pkg} — BLOCKED (registry unreachable — core signal unavailable)")
        write_log(make_log_entry(detected_pm, pkg, spec, None, dep_scope, "blocked", "core_signal_unavailable", "registry_metadata"))
        blocked = True
        continue

    if "error" in abbrev:
        print(f"⚠️ {pkg} — not found on npm registry")
        write_log(make_log_entry(detected_pm, pkg, spec, None, dep_scope, "blocked", "package_not_found", None))
        blocked = True
        continue

    # ── Core signal: version resolution (fail-closed) ──
    check_version, resolved_ok, resolve_err = resolve_version(pkg, spec, abbrev)
    if not resolved_ok or not check_version:
        reason = resolve_err or "unknown"
        print(f"🚫 {pkg}@{spec} — BLOCKED (version not resolved: {reason})")
        write_log(make_log_entry(detected_pm, pkg, spec, None, dep_scope, "blocked", "version_not_resolved", reason))
        blocked = True
        continue

    # ── Core signal: install scripts (fail-closed on network error) ──
    has_scripts_result = check_install_scripts(pkg, check_version)
    if has_scripts_result is None:
        print(f"🚫 {pkg}@{check_version} — BLOCKED (cannot fetch version manifest — core signal unavailable)")
        write_log(make_log_entry(detected_pm, pkg, spec, check_version, dep_scope, "blocked", "core_signal_unavailable", "version_manifest"))
        blocked = True
        continue
    has_scripts = has_scripts_result

    # ── Supplementary signals (fail-open) ──
    downloads = get_downloads(pkg)
    vuln_count, vuln_ids = check_vulns(pkg, check_version)
    has_vuln = vuln_count > 0

    age_days = None
    modified = abbrev.get("modified", "")
    if modified:
        try:
            mod_dt = datetime.fromisoformat(modified.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - mod_dt).days
        except Exception:
            pass

    maintainers = len(abbrev.get("maintainers", []))

    # ── Risk assessment ──
    risks = []
    if has_vuln:
        risks.append(f"{vuln_count} known vuln(s): {', '.join(vuln_ids)}")
    if downloads < MIN_WEEKLY_DOWNLOADS:
        risks.append(f"low downloads: {downloads}/week")
    if has_scripts:
        risks.append("has install scripts")
    if age_days is not None and age_days < MAX_AGE_DAYS_FOR_NEW_WARNING:
        risks.append(f"published {age_days}d ago")

    # ── Decision + Output ──
    version_display = f"@{check_version}" if spec else ""
    if not risks:
        print(f"✓ {pkg}{version_display} — {downloads}/week, {maintainers} maintainers")
        write_log(make_log_entry(detected_pm, pkg, spec, check_version, dep_scope, "allow", "clean", None))
    else:
        risk_str = ", ".join(risks)
        if has_vuln:
            print(f"🚫 {pkg}@{check_version} — BLOCKED ({risk_str})")
            write_log(make_log_entry(detected_pm, pkg, spec, check_version, dep_scope, "blocked", "known_vulnerability", ", ".join(vuln_ids)))
            blocked = True
        elif downloads < MIN_WEEKLY_DOWNLOADS and has_scripts:
            print(f"🚫 {pkg} — BLOCKED ({risk_str})")
            write_log(make_log_entry(detected_pm, pkg, spec, check_version, dep_scope, "blocked", "low_downloads_with_scripts", None))
            blocked = True
        else:
            print(f"⚠️ {pkg}{version_display} — ({risk_str}) — {downloads}/week, {maintainers} maintainers")
            write_log(make_log_entry(detected_pm, pkg, spec, check_version, dep_scope, "allow_with_warning", "has_risks", risk_str))

if blocked:
    print()
    print("--- BLOCKED: One or more packages failed safety check. ---")
    print(f"To override, add the package name to: {SAFE_PACKAGES_FILE}")

sys.exit(2 if blocked else 0)
PYEOF
