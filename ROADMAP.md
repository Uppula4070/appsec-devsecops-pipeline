# Roadmap

Small, self-contained improvements, each one pull request.
Size: 🟢 under an hour · 🟡 an evening · 🔴 a weekend.

> `main` is protected: every change goes through a pull request and merges only when all five checks pass.
> `git checkout -b my-change` → commit → `git push -u origin my-change` → open the PR on GitHub → merge when green.

## Pipeline

- [ ] 🟢 Generate an SBOM (CycloneDX) for the Python dependencies and upload it as a build artifact
- [ ] 🟢 Upload pip-audit results as SARIF so they appear in the Security tab next to Semgrep
- [ ] 🟡 Add a `Dockerfile` that runs the app with Waitress as a non-root user, and a Trivy job that scans the image
- [ ] 🟡 Add `CODEOWNERS` so changes to `.github/workflows/` need your review
- [ ] 🔴 Run ZAP against the app with an authenticated session, not just anonymous pages

## Application

- [ ] 🟢 Add per-client rate limiting to `/notes` (open finding F-04 in the pentest-report-toolkit sample report), with a test that expects HTTP 429
- [ ] 🟡 Add a second demo pull request with a cross-site scripting flaw in a new HTML endpoint, caught by Semgrep

## Docs

- [ ] 🟢 Add a short "How to reproduce locally" section showing how to run Semgrep and pip-audit on your own machine
