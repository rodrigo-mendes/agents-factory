# Validate r2: publishing-container-images-github-actions (validator B, 2026-10-30)

Score: 99.5 (0 HIGH, 0 MEDIUM, 1 LOW). Base: packages/github-actions-cicd/.apm/skills/publishing-container-images-github-actions/

## Round-1 findings
- H1 FIXED (residual LOW below): push:false now routes to a `build` job (contents: read, no login, no environment) - workflow-image-publish.md:9,51-52; caller ci-image has `permissions: { contents: read }` and says no `packages: write` (workflow-callers.md:20,27).
- M1 FIXED: environment passed as string input (`workflow-callers.md:81,94`); jobs set `environment: ${{ inputs.environment }}` and read `vars.ECR_PUSH_ROLE_ARN` / `secrets.OCIR_*` inside (`workflow-image-publish-ecr-ocir.md:16,30,81,104-105`).
- L1 FIXED: Contents line at unverified-and-risks.md:5.
- L2 FIXED: SKILL.md:91 cites GHCR docs and OIDC reference.
- L3 FIXED: timeout-minutes 30 on every job (workflow-image-publish.md:51,80; ecr-ocir.md:15,80); ci-image concurrency (workflow-callers.md:14-16).

## ECR_PUSH_ROLE_ARN / `<env>-publish`
Acceptable third role (push-only, separated from deploy; least privilege), not a defect in the skill. It is a documentation gap family-wide: see package report N2.

## New findings
- N1 LOW (workflow-callers.md:20 vs workflow-image-publish.md:81): the reusable file still contains the ghcr job asking `packages: write` while ci-image grants only contents: read; whether skipped jobs count is stated (unverified) at workflow-image-publish.md:9. Hint: verify once, or grant `packages: write` in ci-image if rejected.
