# Never-do patterns with examples

Back to [SKILL.md](../SKILL.md). Terraform 1.17.1; research date 2026-10-30. Each pattern shows the wrong form and the alternative.

## Contents

[N1 auto-approve](#n1-apply-with--auto-approve) · [N2 retention](#n2-plan-artifacts-with-default-retention) · [N3 locking](#n3-dynamodb-only-or-no-locking-on-s3) · [N4 OCI S3 route](#n4-new-oci-stacks-on-the-s3-compatible-endpoint) · [N5 backend secrets](#n5-secrets-in--backend-config) · [N6 PR apply](#n6-apply-or-apply-mode-tests-on-pull_request) · [N7 drift apply](#n7-apply-from-the-drift-workflow) · [N8 cancel](#n8-cancel-in-progress-true-on-apply) · [N9 plugin cache](#n9-one-plugin-cache-across-concurrent-init-runs) · [Trap](#trap-apply-a-plan-from-another-run)

## N1. Apply with `-auto-approve`

The approver approves something that is never shown; a commit landing between review and apply is applied silently. HashiCorp: use automatic approval only with non-critical infrastructure.

```yaml
# ❌ Wrong
- run: terraform apply -auto-approve -input=false
# ✅ Correct
- run: terraform apply -input=false tfplan   # tfplan from the plan job of this run
```

Source: https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform

## N2. Plan artifacts with default retention

Plan files hold sensitive values in cleartext; artifacts default to 90 days and are readable by anyone with repository read access.

```yaml
# ❌ Wrong
- uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
  with: { name: plan, path: tfplan }
# ✅ Correct
- uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
  with:
    name: tfplan-${{ inputs.environment }}-${{ inputs.component }}-${{ github.sha }}-${{ github.run_attempt }}
    path: ${{ runner.temp }}/tfwd.tgz
    retention-days: 1
```

Source: https://developer.hashicorp.com/terraform/cli/commands/plan

## N3. DynamoDB-only or no locking on S3

`use_lockfile` defaults to `false`, and DynamoDB locking is deprecated and will be removed in a future minor version. Without a lock, concurrent applies can corrupt state.

```hcl
# ❌ Wrong
backend "s3" { dynamodb_table = "tf-locks" }
# ✅ Correct
backend "s3" { use_lockfile = true }   # during migration both may be set at once
```

Source: https://developer.hashicorp.com/terraform/language/backend/s3

## N4. New OCI stacks on the S3-compatible endpoint

Oracle marks that route deprecated and HashiCorp tests the `s3` backend only against Amazon S3.

```hcl
# ❌ Wrong
backend "s3" {
  endpoints      = { s3 = "https://<namespace>.compat.objectstorage.<region>.oraclecloud.com" }
  use_path_style = true
}
# ✅ Correct
backend "oci" { bucket = "acme-tfstate-prod"  namespace = "acmetenancyns"  region = "eu-frankfurt-1"  key = "app/prod/terraform.tfstate" }
```

Source: https://docs.oracle.com/en-us/iaas/Content/dev/terraform/object-storage-state.htm

## N5. Secrets in `-backend-config`

Values passed this way land in the `.terraform` directory and in plan files, which then travel inside the artifact.

```bash
# ❌ Wrong
terraform init -backend-config="secret_key=${{ secrets.S3_SECRET }}"
# ✅ Correct: non-secret values only; credentials come from the login step's environment
terraform init -input=false -backend-config=env/prod/network.s3.tfbackend
```

Source: https://developer.hashicorp.com/terraform/language/backend/s3

## N6. Apply or apply-mode tests on pull_request

`terraform test` creates real infrastructure by default; a PR branch must never change a shared account.

```yaml
# ❌ Wrong
on: pull_request
steps: [ { run: terraform test } ]        # run blocks default to command = apply
# ✅ Correct
on: pull_request
steps: [ { run: terraform test -filter=tests/plan_only.tftest.hcl } ]
```

Source: https://developer.hashicorp.com/terraform/cli/commands/test

## N7. Apply from the drift workflow

Drift may be an intentional emergency change; a scheduled apply silently reverts it. The fix goes through a PR.

```yaml
# ❌ Wrong
on: { schedule: [ { cron: "17 5 * * *" } ] }
# ... terraform apply -auto-approve -refresh-only
# ✅ Correct: exit code 2 opens an issue; no apply step exists in ops-drift.yml
```

Source: https://developer.hashicorp.com/terraform/cli/commands/plan

## N8. `cancel-in-progress: true` on apply

It cancels any running job or workflow in the same group. An interrupted apply can leave the state lock behind and resources half-created (partial state is (medium confidence), see register).

```yaml
# ❌ Wrong
concurrency: { group: terraform-prod-network, cancel-in-progress: true }
# ✅ Correct
concurrency: { group: terraform-prod-network, cancel-in-progress: false }
```

Source: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency

## N9. One plugin cache across concurrent init runs

The plugin cache directory is not guaranteed to be concurrency safe; `init` behaviour with several parallel calls is undefined.

```yaml
# ❌ Wrong
strategy: { matrix: { component: [network, app, data] } }
env: { TF_PLUGIN_CACHE_DIR: /shared/self-hosted/cache }
# ✅ Correct: one directory per job, created first
env: { TF_PLUGIN_CACHE_DIR: "${{ runner.temp }}/tf-plugin-cache" }
```

Source: https://developer.hashicorp.com/terraform/cli/config/config-file

## Trap: apply a plan from another run

Not a blanket ban, but never the default: a cross-run download needs `github-token` and `run-id`, the merge commit differs from the PR head, and the saved plan can be stale (official stale-plan behaviour is (unverified), see register). Plan again on the merge commit and apply that file in the same run; see the Ask First table in [SKILL.md](../SKILL.md).
