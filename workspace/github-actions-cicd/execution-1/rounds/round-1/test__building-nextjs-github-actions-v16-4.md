# Test round 1 - building-nextjs-github-actions-v16-4

Method: simulated in the evaluator's own context from SKILL.md plus blueprints (no agent spawned, DEC-014). 2026-10-30. SHAs (setup-node 949feb, cache 55cc83, pnpm ea17c6, upload cf430e, download 900082, configure-aws e12538, checkout 3d3c42) and versions (Next 16.4.3, Node 26/24/22) match F3, F6, F10, F14, F15, F23, F24, F36, F37.

Verdict: 5/5 scenarios PASS, 4 findings.

| # | Scenario | Verdict | Evidence |
|---|---|---|---|
| 1 | Static export to S3+CF on Team | PASS | `_node-build.yml` inputs `app-dir, mode, node-version, package-manager` and outputs `artifact-name, artifact-digest`; composite `./.github/actions/build/setup-node-build`; lint `${PM} run lint` (eslint .), `next typegen && tsc --noEmit`; `.next/cache` key; `NEXT_TELEMETRY_DISABLED: "1"`; cd-web-s3 builds once, staging then prod same artifact; `releases/${GITHUB_SHA}/`, origin switch, `/*` invalidation, rollback workflow (medium confidence flagged); `id-token: write` job-level only; Plan variants table "approval is the PR review before merge to protected main", `repo:ORG/REPO:environment:prod` and the post-2026-07-15 immutable sub note. |
| 2 | pnpm on Node 26 | PASS | Always Do "Use pnpm/action-setup instead of Corepack on Node 26"; composite orders pnpm/action-setup before setup-node with `cache: pnpm`; `--frozen-lockfile` "(unverified)"; never-do-patterns.md line 83 offers Node 24 if Corepack required. |
| 3 | Vercel token in PR job | PASS | Never Do rows 4-6; workflow-deploy-vercel.md "no Vercel token is ever exposed to pull-request code", `git.deploymentEnabled { "main": false }`; ci-web mode `vercel`; Actions preview only with preview-only credential (scoping unverified). |
| 4 | Rebuild with NEXT_PUBLIC per env | PASS | Never Do row 2, always-do-patterns.md line 59 "`publicRuntimeConfig` is removed in 16", `await connection()`, config file for static export; row 3 refuses secrets in NEXT_PUBLIC/build args. |
| 5 | Vercel on Free private | PASS | Ask First rows "GitHub plan and privacy" and "Vercel on Free" (F1/F2) and "Vercel CLI version" (no pin, required input, no default); Plan variants table states "every user with write access can read the secret"; caller on `push` to `main` only. |

## Findings

### N-1 (medium) Free F2 Vercel path keeps `environment:` on the reusable job
`_deploy-vercel.yml` hard-codes `environment: ${{ inputs.environment }}` and cd-web-vercel.yml passes `environment: prod`. For F2 (Free private, repository secrets) the blueprint says only "declared secrets cover the Free variant", whereas the S3 blueprint says "inline the deploy job in the caller and drop the environment line" and the blast-radius skill says "Do not reference environment: in Free private workflows; the behaviour is (unverified)". So the default F2 output may reference an environment that cannot exist on Free private. Skill text: workflow-deploy-vercel.md Plan variants + Notes; workflow-callers.md `cd-web-vercel.yml`. Fix: make `environment` optional (`default ''`) and state the Free variant.

### N-2 (medium) AWS login called directly, no allowed-account-ids / session name, name drift
`_deploy-s3-cf.yml` and `ops-web-rollback.yml` call `aws-actions/configure-aws-credentials` directly with `role-to-assume: ${{ vars.AWS_DEPLOY_ROLE_ARN }}`. OIDC skill Always Do: "Set allowed-account-ids when calling the action directly" and shape "composite `./.github/actions/cloud/login-aws`". Variable names also differ across the family: `AWS_DEPLOY_ROLE_ARN` (this skill), `AWS_ROLE_ARN` (blast-radius, router scenario 1), `ECR_PUSH_ROLE_ARN` (images). Not catastrophic, but a pipeline combining skills ends with three names for one concept.

### N-3 (low) Inline expression in `run:` against the family injection rule
`_deploy-s3-cf.yml`: `run: echo "artifact ${{ inputs.artifact-name }} digest ${{ inputs.artifact-digest }}" >> "$GITHUB_STEP_SUMMARY"`. The images skill states "Inputs reach shell steps only through env:". Inputs come from a trusted caller, but the example is the pattern the github-core skill forbids.

### N-4 (low) Unpinned runner label and cross-contract
`runs-on: ubuntu-latest` throughout (images uses `ubuntu-24.04`). The composing catalog lists `_node-build.yml` with secret `NPM_READ_TOKEN` marked "confirmed", while the real workflow declares "No secrets" and outputs `artifact-name` and `artifact-digest`: tracked as F-012 but the "confirmed" label makes it worse than a name drift. A caller written from the catalog passes a secret the workflow does not declare (workflow_call error).

## Known/tracked, not re-reported
F-012 (names), pilot F-001..F-011 on the terraform skill: no recurrence found here (no `<repo-workflows-dir>`, PR jobs hold no credentials, tags are plain parentheses).
