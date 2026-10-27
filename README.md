# AppSec DevSecOps Pipeline

[![security-pipeline](https://github.com/Uppula4070/appsec-devsecops-pipeline/actions/workflows/security.yml/badge.svg)](https://github.com/Uppula4070/appsec-devsecops-pipeline/actions/workflows/security.yml)

A GitHub Actions pipeline that puts **SAST, dependency scanning, secrets scanning and DAST** in front of every pull request, and **blocks the merge** when a scan finds something. The target is a small Flask notes API.

> **Lab only.** Everything here runs on a demo app I wrote for this project. No employer code, data or findings.

## How it works

```
 Pull request opened
        │
        ├── Unit tests ─────────────── pytest (includes an SQL-injection regression test)
        ├── SAST ───────────────────── Semgrep: python, flask, owasp-top-ten, secrets rules
        ├── Dependency scan (SCA) ──── pip-audit against the OSV / PyPI advisory databases
        ├── Secrets scan ───────────── Gitleaks over the full git history
        └── DAST ───────────────────── app started in CI, OWASP ZAP baseline scan against it
                    │
        any job fails ──► merge blocked (branch protection)
        all jobs pass ──► merge allowed
```

Semgrep results are also uploaded as SARIF, so they show up in the repo's **Security → Code scanning** tab. Dependabot opens weekly PRs for outdated Python packages and GitHub Actions.

## See it catch real bugs

[Pull request #9](https://github.com/Uppula4070/appsec-devsecops-pipeline/pull/9) (branch `vulnerable-demo-v2`) adds three deliberate flaws, and shows the pipeline failing and the merge blocked:

| Flaw added | Caught by |
|---|---|
| SQL built with an f-string from user input (`/notes/unsafe?q=`) | Semgrep (SAST) |
| Hardcoded API key in the source | Gitleaks and Semgrep secrets rules |
| `requests==2.19.1`, which has known CVEs | pip-audit (SCA) |

The `main` branch shows the fixes: parameterized queries, no secrets in code, current dependencies, and strict security headers.

## What it found in its own first run

The very first run on `main` failed 3 of 5 checks, all real issues, and each was fixed rather than suppressed:

| Scanner | Finding | Fix |
|---|---|---|
| pip-audit | `flask 3.1.2` affected by PYSEC-2026-2151 (missing `Vary: Cookie`, cache leak) | Upgraded to `flask 3.1.3` |
| Semgrep | 11 GitHub Actions referenced by mutable tags (`@v4`), a supply-chain risk | Pinned every action to a full commit SHA |
| Semgrep | Dependabot had no cooldown, so it would adopt a brand-new (possibly compromised) release immediately | Added a 7-day cooldown |
| ZAP | `Server` header leaked `Werkzeug/x Python/x` | Served the app with Waitress instead of the dev server; header is now `notes-api` |
| ZAP | CSP missing directives that don't fall back to `default-src` | Added `form-action 'none'` and `base-uri 'none'` |

## Design choices

- **Fail closed.** Every scanner runs with the option that makes it fail the job, rather than only reporting.
- **Tuned, not silenced.** The one ZAP rule ignored (`.zap/rules.tsv`) is informational for a JSON API, and the reason is written next to it.
- **Fixes are tested.** `tests/test_app.py` sends a classic `' OR '1'='1` payload so an injection bug can't quietly come back.
- **Least privilege.** The workflow's default token is read-only; only the SAST job gets `security-events: write` to upload results.
- **Pinned supply chain.** Third-party actions are pinned to commit SHAs, and Dependabot proposes updates after a cooldown.

## Run it locally

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements-dev.txt
python -m pytest -q
python -m app.app               # http://127.0.0.1:5000/notes?q=welcome
```

## Repo layout

```
app/app.py                     Flask notes API (the scan target)
tests/test_app.py              Unit and security regression tests
.github/workflows/security.yml The security pipeline
.github/dependabot.yml         Automated dependency updates
.zap/rules.tsv                 ZAP rule tuning, with reasons
```
