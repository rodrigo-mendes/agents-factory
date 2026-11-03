# Validate: limiting-blast-radius-github-actions-deploys (P6 round 1, validator B, 2026-10-30)

Score: 88.5 (0 HIGH, 4 MEDIUM, 3 LOW). SKILL.md 141 lines, frontmatter valid, three tiers, Version Context, Verification Loop (rule 14), 5 scenarios, pins match facts (F10, F23, F24, F3, F26); rule 16 plan model reads consistently in SKILL.md, approval-models.md and isolation-matrix.md (PR review default, required reviewers = upgrade path, Free weaker and explicit).

Base path: packages/github-actions-cicd/.apm/skills/limiting-blast-radius-github-actions-deploys/

## MEDIUM
- M1 (D4/A5): `blueprints/workflow-smoke-rollback.md:128` states "A failed smoke test reaches `rollback-prod`, then the run is red so no later environment starts". Trace of the shown caller: `_smoke-test` always exits 0 (`:47`), `complete-prod` is skipped (`:115`), `rollback-prod` succeeds (`:120-125`), so the workflow concludes green after an automatic prod rollback; later environments are only skipped because they `needs` skipped jobs. Evidence: "The job always exits 0 and reports `passed`". Fix hint: add a final job `needs: [rollback-prod]` that fails when `smoke-prod.outputs.passed != 'true'`, and correct the sentence.
- M2 (security rule 5/7, publishing design note "inputs reach shell only through env"): `blueprints/workflow-smoke-rollback.md:43` runs `bash "${{ inputs.check_script }}"`; the input is interpolated inside `run:`. Pass it through `env:` (`CHECK_SCRIPT`) and call `bash "$CHECK_SCRIPT"`; also validate it is a repo path.
- M3 (SKILL.md:89 Never "Rebuild for each environment"; Verification Loop check 3, SKILL.md:124): `blueprints/always-do-patterns.md:97-105` runs `vercel build --prod` in the deploy stage and the loop forbids `vercel build` in `_promote.yml`, yet the Vercel target cannot use the zip hash step (`reusable-workflows.md:66-68`, `dist/function.zip`). The Vercel path either rebuilds per environment or has no hash check; the skill does not say which exception applies. Fix hint: document Vercel as the one target where build output is environment-bound (nextjs M-pattern) and define the hash/identity that is promoted (deployment URL promote of a staged build, as in `never-do-patterns.md` N6).
- M4 (cross-skill contract names, family consistency): (a) required status check is `plan` in `approval-models.md:15,38` and `evaluation-scenarios.md:10`, `ci-gate` in `isolation-matrix.md:17` and in composing, README and rule github-workflows-pr-ci, and `gate` in securing-supply-chain; the ruleset JSON you ship requires a check that the family PR callers never produce for non-Terraform apps. (b) role variable is `vars.AWS_ROLE_ARN` (`reusable-workflows.md:72`, `workflow-smoke-rollback.md:79`) but `vars.AWS_DEPLOY_ROLE_ARN` in federating-github-actions-aws-oidc and nextjs. Fix hint: use `ci-gate` everywhere (and say `plan` is a job under it for Terraform) and `AWS_DEPLOY_ROLE_ARN`.

## LOW
- L1 (A3): `blueprints/unverified-and-risks.md` is 129 lines with no contents list.
- L2: `_smoke-test.yml` declares `environment` input (`workflow-smoke-rollback.md:20`) that is never used.
- L3 (D4): evidence of reuse of the same concurrency group across canary/complete is only medium confidence (M10) and not exercised by a verification step.

Checked and clean: counts (8/11/5) match tables; plan availability table matches F25/F39; ruleset JSON uses `bypass_actors: []`, `active`.
