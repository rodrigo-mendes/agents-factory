# Validate r2: securing-supply-chain-github-actions (validator B, 2026-10-30)

Score: 97.0 (0 HIGH, 1 MEDIUM, 1 LOW). Base: packages/github-actions-cicd/.apm/skills/securing-supply-chain-github-actions/

## Round-1 findings
- M1 FIXED: licensed jobs moved to `_code-security.yml` (workflow-licensed-jobs.md:3,20); deploy gate `scan-image` keeps `contents: read` (workflow-callers.md:70-71); PR caller grants the write scopes only on `code-security` (workflow-callers.md:26-35).
- M2 FIXED: `ci-gate` (workflow-callers.md:36).
- L1 FIXED: SARIF text now says Trivy image results only (workflow-licensed-jobs.md:98).
- L2 FIXED: timeout-minutes on scan 20, codeql 60, dependency-review 15, ci-gate 5.
- L3 FIXED: Contents line present.
- L4 PARTIAL (LOW, still open): concurrency added (workflow-callers.md:16-18), but `code-security` still grants `pull-requests: write` while github-workflows-pr-ci.instructions.md:14 allows it only on the plan-comment job. Hint: extend the rule to "the job that posts a PR comment".

## New findings
- N1 MEDIUM (workflow-licensed-jobs.md:96-104 vs workflow-security-scan.md:43): the optional SARIF upload step is added to the `scan` job of `_security-scan.yml`, whose permissions are `contents: read`; `upload-sarif` needs `security-events: write`, and the callers deliberately no longer grant it there. With CODE_SECURITY_ENABLED true the step fails (and `(success() || failure())` makes the job red). Hint: move the upload into `_code-security.yml` as a job with `security-events: write`, or document a job-level `security-events: write` plus caller grant.
