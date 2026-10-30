---
name: automating-terraform-github-actions-v1-17
description: "Builds Terraform 1.17 CI/CD on GitHub Actions for AWS and OCI: reusable plan and apply workflows, PR plan preview, saved-plan apply after PR review on protected main, S3 or oci state locking, drift issues. Use when writing or reviewing Terraform pipelines. Not for Azure DevOps."
---

# Terraform 1.17 on GitHub Actions (AWS and OCI)

> Version lock: every claim applies to **Terraform 1.17.x (pin 1.17.1)** driven from GitHub.com Actions. Research date **2026-10-30**.
> Claims tagged unverified or medium confidence were not fully confirmed against an official page; each tag maps to the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: the Terraform pieces only. How `workflow_call` works belongs to `composing-github-actions-pipelines`; cloud login belongs to `federating-github-actions-aws-oidc` and `federating-github-actions-oci`; SHA pinning and injection-safe scripting belong to `automating-github-repos-with-actions`.
> Provenance: the dated research file for this unit under the factory workspace; this skill never reads it at run time.

## Version Context

| Item | Value | Source (fetched 2026-10-30) |
|---|---|---|
| Terraform CLI | 1.17.1 (2026-10-28); minor line 1.17 started 1.17.0 on 2026-10-21; no breaking changes listed | https://developer.hashicorp.com/terraform/language/upgrade-guides |
| `hashicorp/setup-terraform` | v4.0.1 = `dfe3c3f87815947d99a8997f908cb6525fc44e9e` | https://github.com/hashicorp/setup-terraform/releases |
| `actions/checkout` | v7.0.1 = `3d3c42e5aac5ba805825da76410c181273ba90b1` | https://github.com/actions/checkout/releases |
| `actions/upload-artifact` | v7.0.2 = `cf430e030ddbb5b0abf93d22962f4752f3646cd9` | https://github.com/actions/upload-artifact/releases |
| `actions/download-artifact` | v8.0.2 = `9000827ccba6bdab643e8b6fd33ac0654aef8333` | https://github.com/actions/download-artifact/releases |
| S3 backend locking | `use_lockfile = true`; DynamoDB locking deprecated | https://developer.hashicorp.com/terraform/language/backend/s3 |
| OCI native backend | `oci` backend, Terraform v1.12.0 or later; S3-compatible route deprecated by Oracle | https://docs.oracle.com/en-us/iaas/Content/dev/terraform/object-storage-state.htm |

**Version-lifetime risk** (as of 2026-10-30; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Terraform 1.17.0 is a fresh minor line; re-check the changelog before bumping the pin.
- S3 `dynamodb_table` "will be removed in a future minor version"; the `oci` backend replaces the S3-compatible OCI route.
- Pinned action SHAs go stale; re-resolve them with `git ls-remote` before every bump.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Reusable plan workflow](./blueprints/workflow-tf-plan.md)
- [Reusable apply workflow](./blueprints/workflow-tf-apply.md)
- [Callers: ci-infra, cd-infra](./blueprints/workflow-callers.md)
- [Drift caller: ops-drift](./blueprints/workflow-drift.md)
- [Plan variants: Pro/Team default, Free, upgrade path](./blueprints/plan-variants.md)
- [State backends: S3 and oci](./blueprints/state-backends.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [Verification Loop](#verification-loop)
- [External Resources](#external-resources)

## Blueprints & Guardrails

Shape: reusable `_tf-plan.yml` and `_tf-apply.yml` hold the Terraform logic; thin callers `ci-infra.yml` (pull_request, never applies), `cd-infra.yml` (merge, fresh saved plan, apply in the same run) and `ops-drift.yml` (schedule, never applies) wire them. Default gate (Pro/Team private): protected `main` with required PR reviewers; environments `<env>` (deploy role) and `<env>-pr` (PR read-only role); the required check is `ci-gate`. Free and upgrade variants: [plan variants](./blueprints/plan-variants.md). Cross-references by name only: `managing-terraform-cicd` (Azure DevOps sibling), `terraform-standards`, `limiting-blast-radius-github-actions-deploys`, `securing-supply-chain-github-actions` (Checkov scanning).

### ✅ Always Do

- **Apply only a saved plan file** from `plan -out` in the same run ([apply command](https://developer.hashicorp.com/terraform/cli/commands/apply)).
- **Upload plan artifacts with `retention-days: 1`**; plan files hold sensitive values in cleartext ([plan command](https://developer.hashicorp.com/terraform/cli/commands/plan)).
- **Pass `-input=false`** (or set `TF_INPUT=false`) so no step waits for a prompt ([environment variables](https://developer.hashicorp.com/terraform/cli/config/environment-variables)).
- **Set `TF_IN_AUTOMATION: "true"`** in the workflow env ([environment variables](https://developer.hashicorp.com/terraform/cli/config/environment-variables)).
- **Pin `terraform_version: "1.17.1"` in `setup-terraform`**; the default is `latest` ([README](https://github.com/hashicorp/setup-terraform)).
- **Read `-detailed-exitcode` explicitly**: 0 no changes, 1 error, 2 changes ([plan command](https://developer.hashicorp.com/terraform/cli/commands/plan)).
- **Set `use_lockfile = true` on the S3 backend**; it defaults to `false` ([S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3)).
- **Enable bucket versioning on the state bucket** for state recovery ([S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3)).
- **Use the native `oci` backend on OCI** with Terraform 1.12.0 or later ([Oracle state page](https://docs.oracle.com/en-us/iaas/Content/dev/terraform/object-storage-state.htm)).
- **Keep one state key per environment and component** (family decision; `key` argument in the [S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3)).
- **Make the approval the PR review of the rendered plan**, on protected `main` with required PR reviewers (Pro or Team private; [GitHub plans](https://docs.github.com/en/get-started/learning-about-github/githubs-plans)).
- **Run the apply job in environment `<env>`** with deployment branch policy `main` ([deployments reference](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)).
- **Run the merge-time plan in `<env>`** so the deploy role can write the S3 lock file ([S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3)).
- **Run the PR plan in `<env>-pr`** with a read-only role and `-lock=false` (medium confidence, see register M4).
- **Set `cancel-in-progress: false` on the apply concurrency group** ([control concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)).
- **Commit `.terraform.lock.hcl`** ([dependency lock file](https://developer.hashicorp.com/terraform/language/files/dependency-lock)).
- **Detect drift with `plan -refresh-only -detailed-exitcode`** ([plan command](https://developer.hashicorp.com/terraform/cli/commands/plan)).
- **Render plans for comments with `terraform show -no-color`**, not `-json` ([show command](https://developer.hashicorp.com/terraform/cli/commands/show)).
- **Run only `command = plan` test files on pull requests** with `-filter` ([tests language](https://developer.hashicorp.com/terraform/language/tests)).

Code for each rule: [always-do patterns](./blueprints/always-do-patterns.md).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Which plan is applied | Fresh plan on the merge commit, applied in the same run (default, medium confidence) vs the PR's plan artifact (needs `github-token` and `run-id`; merge-queue safety (unverified)) | "Must reviewers approve the PR plan itself, or is the fresh merge-time plan acceptable after the PR review?" |
| PR plan and state access | Read-only role with `-lock=false` (medium confidence) vs no cloud plan on PRs (fmt, validate, mocked tests only) | "Should PRs read cloud state? Fork PRs get no secrets." |
| Plan artifact content | Whole working directory incl. `.terraform` (default, medium confidence) vs `tfplan` only plus re-init (equivalence (unverified)) | "May the artifact hold provider binaries and backend config?" |
| Concurrency placement | Workflow-level group in the caller covers plan and apply (medium confidence) vs job-level | "One group per environment and component, at workflow level?" |
| Drift scope | `-refresh-only` (external change only) vs normal plan (also unapplied config) vs both (composition, medium confidence) | "Should unapplied merged config count as drift?" |
| OCI credentials | API key in environment secrets (default) vs `SecurityToken` token exchange (medium confidence) | "API key or token exchange for the oci backend and provider?" |
| Test scope | Plan and mock only on PRs vs apply-mode tests in a dispatched sandbox workflow; `mock_provider` syntax (unverified) | "Which `.tftest.hcl` files are plan or mock only?" |
| GitHub plan | Pro/Team private: PR review on protected `main` is the gate (default). Free private: no environments and no protected branches, weaker variant. Required reviewers on environments need a public repository or Enterprise | "Which GitHub plan owns this private repository, and are the Free-variant risks acceptable?" |
| PR output | Comment (65535 characters max) vs job summary (1 MiB per step) vs both | "Is a PR comment wanted? The summary is always written." |
| Lock migration | Add `use_lockfile` beside `dynamodb_table`, then drop it; whether `-reconfigure` is needed (unverified) | "Is there existing DynamoDB state locking to migrate?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| `terraform apply -auto-approve` in the merge workflow ([tutorial](https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform)) | `terraform apply -input=false tfplan` from the same run |
| Upload plan artifacts with the default 90-day retention ([Actions settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)) | `retention-days: 1` |
| Rely on DynamoDB-only or no locking on S3 ([S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` |
| Start new OCI stacks on the S3-compatible endpoint ([Oracle state page](https://docs.oracle.com/en-us/iaas/Content/dev/terraform/object-storage-state.htm)) | `backend "oci"` |
| Put secrets in `-backend-config` or the backend block; they land in `.terraform` and plan files ([S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3)) | Non-secret keys only; credentials from the login step's environment |
| Apply, or run apply-mode `terraform test`, from a pull_request workflow ([test command](https://developer.hashicorp.com/terraform/cli/commands/test)) | Plan-only test files; apply only in `cd-infra.yml` |
| Apply from the drift workflow ([plan command](https://developer.hashicorp.com/terraform/cli/commands/plan)) | Open an issue; fix through a PR |
| `cancel-in-progress: true` on an apply group ([control concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)) | `cancel-in-progress: false` |
| Promise an environment reviewer gate on a private Free, Pro or Team repository ([deployments reference](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)) | PR review on protected `main` (Pro/Team) or the Free variant in [plan variants](./blueprints/plan-variants.md) |
| Log in from a PR plan with the deploy role of `<env>` (roles: `federating-github-actions-aws-oidc`) | The read-only role of `<env>-pr` |
| Share one plugin cache directory across concurrent `init` runs ([CLI config](https://developer.hashicorp.com/terraform/cli/config/config-file)) | Per-job `TF_PLUGIN_CACHE_DIR` under `runner.temp` |

Examples with alternatives: [never-do patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Plan exit codes | 0 no changes, 1 error, 2 changes present | https://developer.hashicorp.com/terraform/cli/commands/plan |
| Artifact default retention | 90 days; set `retention-days` | https://docs.github.com/en/actions/tutorials/store-and-share-data |
| Required reviewers | up to six; one approval suffices; self-review can be blocked | https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments |
| `queue: max` | up to 100 pending; not with `cancel-in-progress: true` | https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency |
| Job summary | 1 MiB per step, 20 per job | https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands |
| Scheduled workflows | latest commit on default branch; shortest interval 5 minutes | https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows |
| `oci` backend minimum | Terraform v1.12.0 | https://docs.oracle.com/en-us/iaas/Content/dev/terraform/object-storage-state.htm |
| Reusable workflow location | the workflows folder, no subfolders | https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows |

## Verification Loop

Run offline from the repository root after generating the workflows; no cloud access needed.

1. `terraform -chdir=infra/network init -backend=false -input=false && terraform -chdir=infra/network validate` expects `Success! The configuration is valid.`
2. `terraform fmt -check -recursive infra` expects exit code 0 and no output.
3. `grep -rn "auto-approve" .github/workflows` expects no match.
4. `grep -rEn "uses: [^./][^@]*@v[0-9]" .github/workflows` expects no match (no action pinned by tag).
5. `grep -rLn "timeout-minutes" .github/workflows/_tf-*.yml` expects no file listed.
6. `grep -rn "retention-days" .github/workflows/_tf-plan.yml` expects `retention-days: 1` on both uploads.

If any check fails, fix the named file and rerun all six.

## External Resources

All fetched 2026-10-30.

- [Running Terraform in automation](https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform)
- [Terraform plan command](https://developer.hashicorp.com/terraform/cli/commands/plan)
- [Control deployments (GitHub)](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
