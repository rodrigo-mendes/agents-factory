# Test P6 r2 - limiting-blast-radius-github-actions-deploys (S1)

Own-context simulation, 2026-10-30. S1 PASS. Score 100.

| r1 finding | Status | Evidence |
|---|---|---|
| B-1 MEDIUM check names | FIXED | approval-models.md:15,38,60 and isolation-matrix.md:17 all `ci-gate`; evaluation-scenarios.md:10 |
| B-2 LOW-MED injection in smoke test | FIXED | workflow-smoke-rollback.md:42-45 `CHECK_SCRIPT` via env, path allow-list `./scripts/*.sh` |
| B-3 MEDIUM direct login / id-token | FIXED | reusable-workflows.md:72-74 and workflow-smoke-rollback.md:82-83 use `./.github/actions/cloud/login-aws` with `vars.AWS_DEPLOY_ROLE_ARN`; :59 id-token on the job that logs in, :82 explains why release runs in that job |
| B-4 LOW catalog/contract | FIXED | catalog-reference.md:28-30 `deployed_ref`/`previous_ref`, `passed`; workflow-smoke-rollback.md:125-127 rollback also on failed `complete-prod`; `_build-orders` replaced by `_java-build.yml` (:99) |

New findings: none.
