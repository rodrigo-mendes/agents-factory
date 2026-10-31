# Always-do patterns with code

Back to [SKILL.md](../SKILL.md). Terraform 1.17.1; research date 2026-10-30. Full workflows: [plan](./workflow-tf-plan.md), [apply](./workflow-tf-apply.md), [callers](./workflow-callers.md). Backend blocks: [state backends](./state-backends.md).

## Contents

[Saved plan](#saved-plan-only) · [Retention](#plan-artifact-retention) · [Automation env](#automation-environment) · [Pinned CLI](#pinned-cli) · [Exit codes](#exit-codes) · [S3 backend](#s3-backend-locking-and-versioning) · [OCI backend](#oci-native-backend) · [State keys](#one-state-key-per-environment-and-component) · [Approval gate](#approval-gate-on-apply) · [Concurrency](#concurrency-without-cancellation) · [Lock file](#lock-file-for-the-runner-platform) · [Drift](#drift-signal) · [Plan rendering](#plan-rendering) · [Plan-only tests](#plan-only-tests-on-pull-requests)

## Saved plan only

Terraform treats passing the plan file as the approval; the human approval is the pull request review of the rendered plan before merge (see [plan variants](./plan-variants.md)).

```bash
# Terraform 1.17.1
terraform plan  -input=false -out=tfplan
terraform apply -input=false tfplan
```

Source: https://developer.hashicorp.com/terraform/cli/commands/apply

## Plan artifact retention

```yaml
- uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
  with:
    name: tfplan-${{ inputs.environment }}-${{ inputs.component }}-${{ github.sha }}-${{ github.run_attempt }}
    path: ${{ runner.temp }}/tfwd.tgz
    retention-days: 1
```

Anyone with repository read access can download artifacts, so keep the lifetime short.
Source: https://developer.hashicorp.com/terraform/cli/commands/plan

## Automation environment

```yaml
env:
  TF_IN_AUTOMATION: "true"
  TF_INPUT: "false"
```

`TF_INPUT=false` acts as `-input=false`; `TF_IN_AUTOMATION` stops Terraform suggesting next commands.
Source: https://developer.hashicorp.com/terraform/cli/config/environment-variables

## Pinned CLI

```yaml
- uses: hashicorp/setup-terraform@dfe3c3f87815947d99a8997f908cb6525fc44e9e # v4.0.1
  with:
    terraform_version: "1.17.1"
    terraform_wrapper: false
```

Without `terraform_version` the action defaults to `latest`. The wrapper is switched off so plain exit codes and stdout reach the shell (wrapper behaviour with `-detailed-exitcode` is (unverified), see register).
Source: https://github.com/hashicorp/setup-terraform

## Exit codes

GitHub's default bash runs with `-e`, so a bare exit code 2 fails the step. Capture it first.

```bash
set +e
terraform plan -input=false -detailed-exitcode -out=tfplan
rc=$?
set -e
if [ "$rc" -eq 1 ]; then exit 1; fi
echo "has-changes=$([ "$rc" -eq 2 ] && echo true || echo false)" >> "$GITHUB_OUTPUT"
```

Source: https://developer.hashicorp.com/terraform/cli/commands/plan

## S3 backend locking and versioning

```hcl
# Terraform 1.17 - backend.tf (partial config; bucket, key, region via -backend-config file)
terraform {
  backend "s3" {
    use_lockfile = true
    encrypt      = true
  }
}
```

The lock file needs `s3:GetObject`, `s3:PutObject` and `s3:DeleteObject`; enable bucket versioning for recovery. Details: [state backends](./state-backends.md).
Source: https://developer.hashicorp.com/terraform/language/backend/s3

## OCI native backend

Use `backend "oci"` with `auth = "APIKey"` by default; the full block is in [state backends](./state-backends.md).
Source: https://developer.hashicorp.com/terraform/language/backend/oci

## One state key per environment and component

```text
env/prod/network.s3.tfbackend   key = "network/prod/terraform.tfstate"
env/prod/app.s3.tfbackend       key = "app/prod/terraform.tfstate"
env/dev/network.s3.tfbackend    key = "network/dev/terraform.tfstate"
```

Family decision: small states keep lock contention and blast radius small.

## Approval gate on apply

Default (Pro/Team private): protected `main` with required PR reviewers; the apply job uses environment `<env>` (branch policy `main`) with no required reviewers.

```yaml
apply:
  needs: plan
  environment: prod        # deploy role; branch policy main; the PR review was the approval
```

Source: https://docs.github.com/en/get-started/learning-about-github/githubs-plans ; variants and upgrade path: [plan variants](./plan-variants.md)

## Concurrency without cancellation

```yaml
concurrency:
  group: terraform-prod-network
  cancel-in-progress: false
```

Source: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency

## Lock file for the runner platform

```bash
terraform providers lock -platform=linux_amd64 -platform=darwin_arm64 -platform=windows_amd64
```

Commit the result so plan and apply runners select identical providers.
Source: https://developer.hashicorp.com/terraform/language/files/dependency-lock

## Drift signal

```bash
terraform plan -input=false -refresh-only -detailed-exitcode -no-color > drift.txt
```

Never use `-minimal-refresh` or `-refresh=false` for drift; they ignore external changes to resources with no planned change.
Source: https://developer.hashicorp.com/terraform/cli/commands/plan

## Plan rendering

```bash
terraform show -no-color tfplan > plan.txt     # text, for comments and summaries
# terraform show -json prints sensitive values in plain text: never post it
```

Source: https://developer.hashicorp.com/terraform/cli/commands/show

## Plan-only tests on pull requests

```bash
terraform test -filter=tests/plan_only.tftest.hcl
```

`run` blocks default to `command = apply` and create real infrastructure; plan-only files declare `command = plan`.
Source: https://developer.hashicorp.com/terraform/language/tests
