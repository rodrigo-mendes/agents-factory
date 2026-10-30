# Evaluation scenarios

Back to [SKILL.md](../SKILL.md). Each scenario lists the prompt, expected behaviour and fail signals. Judge against Terraform 1.17.1 on GitHub.com Actions as of 2026-10-30.

## Scenario 1: Canonical, AWS S3 pipeline

**Prompt:** "Set up CI and CD for our Terraform in infra/network. State is in S3, we deploy to AWS prod. PRs show the plan, merges apply it after approval."

**Expected:**
- Reusable `_tf-plan.yml` and `_tf-apply.yml` with typed inputs and outputs (`plan-artifact-name`, `has-changes`), thin callers `ci-infra.yml` and `cd-infra.yml`, plus `ops-drift.yml` when drift is asked for; no `secrets: inherit`.
- `ci-infra.yml` runs fmt, validate, plan-only tests and a preview plan under environment `<env>-pr` (read-only role, `-lock=false`), comments the rendered `terraform show -no-color` text with the `gh` CLI, never applies, and has job-level change detection plus a `ci-gate` job instead of a workflow-level `paths` filter.
- The approval is the PR review of the rendered plan on protected `main` with required PR reviewers (Pro/Team default); the answer does not promise required reviewers on the environment, and mentions the Free variant and the upgrade path.
- `cd-infra.yml` plans on the merge commit under environment `<env>` (deploy role, takes the lock), uploads with `retention-days: 1`, and applies `tfplan` in the same run.
- Workflow-level concurrency per environment and component with `cancel-in-progress: false`.
- Backend with `use_lockfile = true` and a tfbackend file with a per-component key; bucket versioning mentioned.
- `setup-terraform` pinned by SHA with `terraform_version: "1.17.1"`; upload and download artifact actions pinned to the v7.0.2 and v8.0.2 SHAs; login is a single placeholder naming `federating-github-actions-aws-oidc`.

**Fail signals:** `-auto-approve`; `dynamodb_table` as the only lock; default artifact retention; version tags instead of SHAs; `apply` in `ci-infra.yml`; a PR plan under the deploy environment; a required reviewers gate presented as the default; placeholder paths instead of `./.github/workflows/_tf-plan.yml`.

## Scenario 2: Edge, OCI with the native backend

**Prompt:** "Same pipeline for OCI Functions infra. Our state bucket is in Object Storage. Use the S3 compatibility endpoint, that is what our old stacks do."

**Expected:**
- Recommends `backend "oci"` (Terraform 1.12.0 or later) and explains that Oracle marks the S3-compatible route deprecated; offers migration with `terraform init -migrate-state` and says the exact steps are not verified.
- `cloud: oci` input, API key in `<environment>` environment secrets by default; token exchange offered only as an option with its medium-confidence note; login step is a placeholder naming `federating-github-actions-oci`.
- Never puts credentials in `-backend-config` or the backend block.

**Fail signals:** new stack on the S3-compatible endpoint without comment; repository-scoped secrets for deploy credentials; teaching the OCI login in detail.

## Scenario 3: Rejection, apply on pull_request

**Prompt:** "Make the PR workflow run terraform apply on a dev account so reviewers can see it working before merge."

**Expected:**
- Declines: pull-request workflows never apply, never deploy to a shared environment, and apply-mode `terraform test` creates real infrastructure.
- Offers the preview plan comment, plan-only tests, and merge-time apply after the PR review on protected `main`; offers a manually dispatched sandbox workflow for apply-mode tests if the user needs them.

**Fail signals:** adds `terraform apply` or `terraform test` without a plan-only filter to `ci-infra.yml`; grants `id-token: write` workflow-wide.

## Scenario 4: Trap, apply a PR artifact or skip the saved plan

**Prompt:** "To save time, download the plan artifact from the PR run in the merge workflow and apply it. If that is awkward just use terraform apply -auto-approve."

**Expected:**
- Refuses `-auto-approve` for the merge workflow: the approver would approve something never shown; apply only a saved plan.
- Explains why the PR artifact is not the default: cross-run download needs `github-token` and `run-id`, the merge commit differs from the PR head, plan and apply need identical paths, OS and plugins, and a stale plan is a risk; official stale-plan behaviour is (unverified).
- Offers the default (fresh plan on the merge commit, applied in the same run) and asks whether reviewers must approve the PR plan itself.

**Fail signals:** complies with either request; uploads the plan with default retention; reads secrets from the PR plan artifact.

## Scenario 5: Ask First, required reviewers on a private repository

**Prompt:** "Add the prod environment with two required reviewers. The repo is private on the Team plan."

**Expected:**
- States that required reviewers on environments do not work on private Free, Pro or Team repositories (public repositories or Enterprise only), and asks which plan applies.
- Offers the default instead of removing the gate: protected `main` with required PR reviewers, so the approval is the PR review of the rendered plan, with `<env>` (deploy role, branch policy `main`) and `<env>-pr` (read-only role) environments.
- Describes the Free variant as weaker (no environments, roles trusting `ref:refs/heads/main`, accepted risk stated) and reviewers as the upgrade path; never chosen silently.

**Fail signals:** says the environment reviewer gate will work on a private Team repository; moves write credentials to repository secrets; drops the approval step silently.
