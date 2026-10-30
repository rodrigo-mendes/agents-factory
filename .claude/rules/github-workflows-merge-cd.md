---
name: github-workflows-merge-cd
description: "Guardrails for merge and release CD caller workflows (cd-*.yml): plan variants and approval model, environments, concurrency, saved-plan apply, promotion by digest, smoke test and rollback. Use when creating or editing a cd- workflow."
paths:
  - "**/.github/workflows/cd-*.{yml,yaml}"
---

# Merge and release CD workflows (cd-*.yml)

A `cd-<app>.yml` caller runs on merge or release and is the only place that applies or deploys. Facts live in the skills below.

## Rules

1. Ask the user's GitHub plan before generating CD. Default is Pro/Team private repos; the Free private variant is weaker and must be stated, never applied silently. Variants: `composing-github-actions-pipelines` (plan-variants).
2. Default model: environments with secrets and variables, deployment branch policy `main`, protected `main` with required PR reviewers. The approval is the PR review of the rendered plan before merge; cloud roles trust `environment:<env>`.
3. Free variant: no environments or protected branches; OIDC roles trusting `ref:refs/heads/main`, dev/prod split by account, role or repo, accepted risk written down. A static secret (OCIR, Vercel) is a repository secret with least privilege and an explicit warning.
4. Concurrency group per app and environment with `cancel-in-progress: false`, so a running deploy is never cancelled.
5. Apply only the saved plan produced earlier in the same run; never re-plan at apply.
6. Build once and promote the same image digest or zip hash through environments; never rebuild for prod.
7. For prod deploys, call `_smoke-test` and `_rollback` (`limiting-blast-radius-github-actions-deploys`).
8. Environment-scoped secrets for anything that can deploy, except the documented Free private variant (rule 3).

## Load the skill

- `limiting-blast-radius-github-actions-deploys` for approvals by plan, promotion, smoke test, rollback.
- `automating-terraform-github-actions-v1-17` for saved-plan apply.
- `publishing-container-images-github-actions` for digest outputs.
- `composing-github-actions-pipelines` for plan variants and block layout.

## Always Do

- Pass the digest or hash as a job output into the deploy job.
- Keep `id-token: write` only on the login job of each deploy.
- Name the plan variant in a comment at the top of the workflow.

## Ask First

- Free private variant, or any prod deploy without a reviewed plan.

## Never Do

- Run `terraform apply` without a saved plan file. Alternative: `apply` the artifact from the plan job.
- Cancel an in-progress deploy. Alternative: queue with `cancel-in-progress: false`.
- Rebuild the artifact per environment. Alternative: promote the same digest or hash.
- Use repository-scoped secrets for deploy credentials where environments exist (exception: the documented Free private variant, with its warning). Alternative: environment secrets.
- Deploy prod without calling `_smoke-test` and `_rollback`. Alternative: add those blocks to the prod deploy.
