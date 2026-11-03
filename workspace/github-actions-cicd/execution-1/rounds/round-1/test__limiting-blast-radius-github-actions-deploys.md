# Test round 1 - limiting-blast-radius-github-actions-deploys

Method: simulated in the evaluator's own context from SKILL.md plus blueprints (no agent spawned, DEC-014). 2026-10-30. SHAs match F3, F10, F23, F24. Rule 16 plan model reads consistently with the other four skills (Pro/Team default: ruleset + main-only environments + PR review; Free: no environments, `ref:refs/heads/main` trust, weaker, stated).

Verdict: 5/5 scenarios PASS, 4 findings.

| # | Scenario | Verdict | Evidence |
|---|---|---|---|
| 1 | Dev/stage/prod on Team, canary | PASS | approval-models.md ruleset JSON (`required_approving_review_count: 1`, `dismiss_stale_reviews_on_push`, `require_last_push_approval`, required check `plan`, `bypass_actors: []`, `enforcement: active`); environments `custom_branch_policies: true` + policy `main`; isolation-matrix.md roles `<app>-<env>-deploy` trust `environment:<env>` and `<app>-dev-pr-read` trust `environment:dev-pr`; `cd-orders` calls `_promote/_smoke-test/_rollback`; "Verify artifact hash" in every promote; concurrency `cancel-in-progress: false`, `timeout-minutes: 30`, `environment: {name, url}`; canary `"0.10"`; release delegated to `deploying-aws-lambda`. |
| 2 | Solo maintainer, Pro | PASS | "require_last_push_approval ... the only collaborator cannot give"; options in order (second collaborator, 0 approvals + required check, manual dispatch); "Bypass lists are not available on user-owned repositories". The matrix/env/hash rows are not restated in that section (implicit, acceptable). |
| 3 | Rebuild for prod | PASS | Never Do row 2 "Rebuild for each environment -> Build once, verify hash or digest, promote"; Verification Loop check 3 greps for build commands in `_promote/_rollback`. Offered alternatives (runtime config or a new merge) appear only in the scenario text, not in a blueprint: the answer must supply them from judgement (minor). |
| 4 | Required reviewers on private Team | PASS | Never Do row 1; Version Context "Free, Pro and Team: public repositories only"; approval-models.md Default + Upgrade path "Only for a public repository or GitHub Enterprise ... Never the default design". |
| 5 | ECS CANARY auto rollback | PASS | progressive-delivery.md "whether alarms also cover BLUE_GREEN, LINEAR and CANARY is (unverified)"; Ask First row; rolling update with alarms/circuit breaker shown; manual redeploy of previous task definition. |

## Findings

### B-1 (medium) Three different names for the required check
Ruleset in approval-models.md requires `plan`; isolation-matrix.md "Supply chain" row says required check `ci-gate`; the supply-chain skill uses `gate`; composing uses `ci-gate`. A generated ruleset would require a check that may not exist (merge permanently blocked or silently unguarded). Also `plan` assumes a plan job exists in every `ci-<app>.yml`, which is not true for a Lambda-only pipeline (the text says "plan or diff job"). Skill text: approval-models.md lines 15, 38, 60; isolation-matrix.md row Supply chain. Fix: one family name (`ci-gate`) and a sentence that the ruleset requires the aggregate job only.

### B-2 (low-medium) Script injection pattern in `_smoke-test.yml`
`if bash "${{ inputs.check_script }}"; then ...` interpolates an input straight into `run:` while sibling values go through `env:`. Family rule: inputs reach shells only via env (github-core). Fix: `env: CHECK_SCRIPT` and `bash "$CHECK_SCRIPT"`.

### B-3 (medium) Direct login with variable `AWS_ROLE_ARN`, no allowed-account-ids; id-token on whole job
`_promote.yml`/`_rollback.yml` call configure-aws-credentials directly (OIDC skill: set allowed-account-ids / use the login-aws composite) and grant `id-token: write` on the whole promote job (release adapter, hash check, deploy all hold the token). The agent's Never Do says "id-token: write outside the login job" and overrides skills (agent precedence 1), so the agent may refuse this skill's own blueprint, or split it differently each run. Align the skill and the agent wording ("the job that logs in").

### B-4 (low) Catalog contradicts the smoke-test contract (worse than F-012)
composing catalog row `_smoke-test.yml`: output "pass/fail via job result". The real `_smoke-test.yml` always exits 0 and reports output `passed`; the cd caller branches on `needs.smoke-prod.outputs.passed`. A caller written from the catalog (`if: success()`) would never roll back. Likewise catalog `_promote.yml` outputs "none" vs `deployed_ref`, `previous_ref`; and `_build-orders.yml` in the cd example is referenced but defined nowhere (a contract with `zip_sha256` output is never given). Also a failure of `complete-prod` after a passed smoke has no rollback path (rollback-prod only reacts to smoke failure).

## Known/tracked, not re-reported
F-012 names; F-010 required-reviewers model: now correct here (no private-repo reviewer promise).
