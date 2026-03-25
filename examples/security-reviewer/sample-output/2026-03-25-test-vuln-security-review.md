# Security Review: test-vuln.js staged commit

> Review date: 2026-03-25
> Scope: `test-vuln.js` (staged, new file)
> Protocol: Dual-verification (Semgrep baseline + Codex cross-validation)
> Semgrep version: 1.155.0
> Codex thread: 019d2302-7a98-7522-ab29-9b055d2e8253

## Executive Summary

| Source | Findings | Agreement Rate |
|--------|----------|---------------|
| Semgrep Baseline | 3 issues (2 built-in XSS rules + 2 custom rules) | - |
| Codex Analysis | 4 issues | 75% overlap (3/4 match Semgrep) |
| Cross-validated | 4 confirmed | - |

**Verdict: CRITICAL**

Three distinct vulnerability classes were confirmed by both Semgrep and Codex. A fourth finding (missing authorization) was Codex-only but subsequently verified with a custom Semgrep rule. No false positives were found. The parameterized query on lines 10-11 was correctly identified as safe by both sources.

---

## Confirmed Findings (Both Sources Agree)

### [HIGH] Hardcoded Credential

- **File**: `test-vuln.js:2`
- **Confidence**: 90% (base 80% both-agree + 5% CWE reference + 5% exploit scenario)
- **Description**: A plaintext password is hardcoded directly in source code. Anyone with access to the repository, build artifacts, or deployment history can recover the credential.
- **Evidence**: `const password = "super_secret_123";`
- **Trigger**: Attacker reads source code, git history, or a leaked artifact. The credential can then be replayed against any authentication endpoint where it is valid.
- **Impact**: Full compromise of the account/service associated with the credential. Because it is in source control, the exposure window extends back to the first commit that included this line.
- **Fix**:
  1. Remove the hardcoded string immediately.
  2. Load the value from environment variable: `const password = process.env.APP_PASSWORD;`
  3. Validate presence at startup: `if (!process.env.APP_PASSWORD) throw new Error("Missing APP_PASSWORD");`
  4. Rotate the exposed credential — treat `super_secret_123` as compromised.
- **Semgrep rule**: custom `hardcoded-password` (ERROR)
- **CWE**: CWE-798 Use of Hard-coded Credentials

---

### [HIGH] SQL Injection via String Concatenation

- **File**: `test-vuln.js:3`
- **Confidence**: 90% (base 80% both-agree + 5% CWE reference + 5% exploit scenario)
- **Description**: A SQL query is built by concatenating an unvalidated variable directly into the query string.
- **Evidence**: `const query = "SELECT * FROM users WHERE id = " + userId;`
- **Trigger**: If `userId` is attacker-controlled (e.g., from a query parameter or request body), payloads such as `0 OR 1=1 --` alter query logic, potentially extracting all rows or enabling further exploitation.
- **Impact**: Data exfiltration, data modification, authentication bypass, or full database compromise depending on database permissions.
- **Fix**:
  ```javascript
  // WRONG (current)
  const query = "SELECT * FROM users WHERE id = " + userId;

  // CORRECT — parameterized query (already demonstrated in the same file on line 10)
  const safeQuery = db.prepare("SELECT * FROM users WHERE id = ?");
  safeQuery.run(userId);
  ```
  Additionally, validate `userId` as an integer before using it.
- **Semgrep rule**: custom `sql-injection-string-concat` (ERROR)
- **CWE**: CWE-89 Improper Neutralization of Special Elements used in an SQL Command

---

### [HIGH] Reflected Cross-Site Scripting (XSS)

- **File**: `test-vuln.js:6`
- **Confidence**: 90% (base 80% both-agree + 5% CWE reference + 5% exploit scenario)
- **Description**: Unsanitized user input from `req.query.name` is concatenated directly into HTML and sent to the browser via `res.send`.
- **Evidence**: `res.send('<h1>' + req.query.name + '</h1>');`
- **Trigger**: A request to `/admin?name=<script>alert(document.cookie)</script>` injects arbitrary JavaScript into the victim's browser. The payload executes in the context of the origin serving the page.
- **Impact**: Session hijacking, credential theft, CSRF token exfiltration, page defacement, or redirection to phishing sites.
- **Fix**:
  ```javascript
  // Option 1: Use a template engine that auto-escapes (EJS, Handlebars, etc.)
  res.render('admin', { name: req.query.name });

  // Option 2: HTML-encode manually before embedding
  const he = require('he');
  res.send('<h1>' + he.encode(req.query.name) + '</h1>');

  // Option 3: Content Security Policy as defense-in-depth
  res.setHeader('Content-Security-Policy', "default-src 'self'");
  ```
- **Semgrep rules**: `javascript.express.security.injection.raw-html-format.raw-html-format` (WARNING, CWE-79), `javascript.express.security.audit.xss.direct-response-write.direct-response-write` (WARNING, CWE-79)
- **OWASP**: A03:2021 Injection, A05:2025 Injection
- **CWE**: CWE-79 Improper Neutralization of Input During Web Page Generation

---

## Codex-Only Findings (Verified)

### [MEDIUM] Missing Authorization on Admin Route

- **File**: `test-vuln.js:5`
- **Confidence**: 75% (base 40% Codex-only + 15% deep verification confirmed + 5% exploit scenario; Semgrep confirmed via custom rule post-hoc)
- **Description**: The `/admin` route has no visible authentication or authorization middleware. Any unauthenticated user can directly request this endpoint.
- **Evidence**: `app.get('/admin', (req, res) => {`
- **Verification method**: Grep confirmed no auth-related keywords (middleware, auth, requireAuth, isAuthenticated, passport, jwt, session) exist anywhere in the file. Custom Semgrep rule `express-admin-route-no-auth` confirmed the pattern.
- **Trigger**: Direct HTTP GET to `/admin` with no credentials bypasses access control entirely.
- **Impact**: Unauthorized access to administrative functionality. Combined with the XSS vulnerability on line 6, an attacker can both access the page and exploit users visiting it.
- **Fix**:
  ```javascript
  // Add auth middleware before the handler
  app.get('/admin', requireAuth, requireRole('admin'), (req, res) => {
    res.send('<h1>' + he.encode(req.query.name) + '</h1>');
  });
  ```
- **Codex reasoning**: Sound — the endpoint name implies privileged access and no access control is visible in scope.
- **Note**: Semgrep has no built-in rule for this pattern; detection required a custom rule authored during conflict resolution.

---

## Conflicts Resolved

| Finding | Semgrep Says | Codex Says | Verdict | Reason |
|---------|-------------|------------|---------|--------|
| XSS Line 6 | WARNING (2 rules, CWE-79) | HIGH | HIGH | Higher severity preserved (conservative); Codex reasoning sound |
| Missing Auth Line 5 | Not detected (no built-in rule) | MEDIUM | MEDIUM (verified) | Custom rule confirmed; Codex correct |

---

## Unresolved (Escalated to Human)

None. All findings were resolvable within the dual-verification protocol.

---

## Negative Checks (Confirmed NOT Vulnerable)

| Pattern | Location | Verdict | Reason |
|---------|----------|---------|--------|
| Parameterized query | Lines 10-11 | SAFE | `db.prepare()` with `?` placeholder binds userId as a parameter; no string concatenation |
| Insecure direct object reference | Whole file | NOT PRESENT | No direct object lookup tied to missing access control beyond the admin route |
| Error handling leaking data | Whole file | NOT PRESENT | No error handling code in this file |
| Supply chain vulnerabilities | project root | NOT PRESENT | `semgrep_scan_supply_chain` found 0 issues; no lockfile changes in this commit |

---

## Supply Chain

Supply chain scan returned 0 results. No dependency changes in the staged commit. No action required.

---

## Finding Summary

| # | Severity | Type | Line | Sources | Confidence |
|---|----------|------|------|---------|------------|
| 1 | HIGH | Hardcoded Credential | 2 | Semgrep + Codex | 90% |
| 2 | HIGH | SQL Injection | 3 | Semgrep + Codex | 90% |
| 3 | HIGH | Reflected XSS | 6 | Semgrep + Codex | 90% |
| 4 | MEDIUM | Missing Authorization | 5 | Codex (verified) | 75% |

**Total: 4 findings — 3 HIGH, 1 MEDIUM. All confirmed. No false positives. COMMIT BLOCKED.**

---

## Required Actions Before Commit

1. Remove `const password = "super_secret_123"` — replace with environment variable and rotate the credential.
2. Replace string-concatenated SQL query with parameterized query (pattern already in the same file, lines 10-11).
3. HTML-escape `req.query.name` before embedding in `res.send` response.
4. Add authentication and role-based authorization middleware to the `/admin` route.

Per the project security policy (`security.md`): CRITICAL/HIGH issues must be resolved before continuing.
