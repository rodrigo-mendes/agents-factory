---
name: github-workflows-pr-ci
description: "Guardrails for pull-request CI caller workflows (ci-*.yml): read-only, PR-only cloud role, plan and comment, single ci-gate check. Use when creating or editing a ci- workflow."
paths:
  - "**/.github/workflows/ci-*.{yml,yaml}"
---

# Pull-request CI workflows (ci-*.yml)

A `ci-<app>.yml` caller runs on `pull_request`, builds and plans, and reports. It never changes anything shared. Facts live in the skills below; this rule states what to check.

## Rules

1. Trigger is `pull_request` only. Branch code runs here, so treat it as untrusted.
2. Workflow `permissions` are read-only (`contents: read`); add `pull-requests: write` only on the job that posts the plan comment.
3. Cloud login uses a dedicated PR-only read role or environment (for example `<env>-pr`), never the credentials of a deployable environment.
4. Fork PRs get no secrets and no OIDC; skip or degrade cloud-dependent jobs for forks.
5. Terraform runs plan only, then posts the rendered plan as a PR comment. The human approval is the PR review of that plan.
6. A single `ci-gate` job that `needs` every real job is the only required status check, so path-filtered jobs do not block merges.
7. Call building blocks as `./.github/workflows/_<domain>-<name>.yml` with typed inputs and secrets passed by name.

## Load the skill

- `composing-github-actions-pipelines` for the caller layout and `ci-gate`.
- `automating-terraform-github-actions-v1-17` for the PR plan and comment.
- `federating-github-actions-aws-oidc` / `federating-github-actions-oci` for the PR-only role.
- `building-java-github-actions`, `building-nextjs-github-actions-v16-4` for build jobs.

## Always Do

- Make `ci-gate` run with `if: always()` and fail on any failed or cancelled needed job.
- Keep `id-token: write` on the login job only.
- Cancel superseded runs per PR with a concurrency group.

## Never Do

- Apply, deploy, push images or publish packages from a ci- workflow. Alternative: do it in the `cd-` workflow after merge.
- Use deployable-environment secrets or roles in a PR job. Alternative: the `<env>-pr` read role.
- Mark individual build jobs as required checks. Alternative: require only `ci-gate`.
- Use `pull_request_target` to get secrets for fork PRs. Alternative: no secrets, plan skipped for forks.
