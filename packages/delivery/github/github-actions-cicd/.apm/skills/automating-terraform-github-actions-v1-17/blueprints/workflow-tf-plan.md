# Reusable plan workflow `_tf-plan.yml`

Back to [SKILL.md](../SKILL.md). Terraform 1.17.1; research date 2026-10-30. Called by [ci-infra and cd-infra](./workflow-callers.md); the plan it uploads is consumed by [`_tf-apply.yml`](./workflow-tf-apply.md). `workflow_call` mechanics: see `composing-github-actions-pipelines`. File name starts with `_` and sits in the workflows folder root (subfolders are not supported; https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows).

## Contents

- [Contract](#contract)
- [Workflow](#workflow)
- [Notes](#notes)

## Contract

| Item | Value |
|---|---|
| Inputs | `working-directory`, `cloud` (`aws` or `oci`), `environment`, `component`, `backend-config` (non-secret tfbackend path), `preview` (boolean, true on pull requests) |
| Outputs | `plan-artifact-name`, `has-changes` (`true` when exit code 2) |
| Secrets | none passed; the job reads the variables and secrets of its own environment |
| Permissions | `plan` job: contents read, id-token write; `comment` job: pull-requests write only |
| Environments | preview run: `<environment>-pr` (read-only role, `-lock=false`); merge run: `<environment>` (deploy role, so the plan can take the state lock) |

The AWS role ARN is `vars.AWS_PR_ROLE_ARN` in `<environment>-pr` and `vars.AWS_DEPLOY_ROLE_ARN` in `<environment>`, read inside this job, never in the caller. The Free variant has no environments: see [plan variants](./plan-variants.md).

## Workflow

```yaml
name: _tf-plan
on:
  workflow_call:
    inputs:
      working-directory: { type: string, required: true }
      cloud:             { type: string, required: true }    # aws | oci
      environment:       { type: string, required: true }
      component:         { type: string, required: true }
      backend-config:    { type: string, required: true }
      preview:           { type: boolean, default: false }
    outputs:
      plan-artifact-name:
        value: ${{ jobs.plan.outputs.artifact-name }}
      has-changes:
        value: ${{ jobs.plan.outputs.has-changes }}
permissions:
  contents: read
env:
  TF_IN_AUTOMATION: "true"
  TF_INPUT: "false"
jobs:
  plan:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    environment: ${{ inputs.preview && format('{0}-pr', inputs.environment) || inputs.environment }}
    permissions:
      contents: read
      id-token: write            # only this job logs in
    outputs:
      artifact-name: ${{ steps.plan.outputs.artifact-name }}
      has-changes: ${{ steps.plan.outputs.has-changes }}
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: hashicorp/setup-terraform@dfe3c3f87815947d99a8997f908cb6525fc44e9e # v4.0.1
        with:
          terraform_version: "1.17.1"
          terraform_wrapper: false
      # Cloud login, one step per cloud, taught by the neighbour skills.
      - name: Cloud login AWS (placeholder, see federating-github-actions-aws-oidc)
        if: inputs.cloud == 'aws'
        run: echo "replace with the AWS login step"
      - name: Cloud login OCI (placeholder, see federating-github-actions-oci)
        if: inputs.cloud == 'oci'
        run: echo "replace with the OCI login step"
      - run: terraform fmt -check -recursive
      - env:
          BACKEND_CONFIG: ${{ inputs.backend-config }}
        run: terraform init -input=false -backend-config="$BACKEND_CONFIG"
      - run: terraform validate
      - if: inputs.preview
        run: terraform test -filter=tests/plan_only.tftest.hcl
      - id: plan
        env:
          PREVIEW: ${{ inputs.preview }}
          TF_ENV: ${{ inputs.environment }}
          TF_COMPONENT: ${{ inputs.component }}
          RUN_ATTEMPT: ${{ github.run_attempt }}
        run: |
          LOCK="-lock=true"
          if [ "$PREVIEW" = "true" ]; then LOCK="-lock=false"; fi
          set +e
          terraform plan -input=false "$LOCK" -detailed-exitcode -out=tfplan
          rc=$?
          set -e
          if [ "$rc" -eq 1 ]; then exit 1; fi
          echo "has-changes=$([ "$rc" -eq 2 ] && echo true || echo false)" >> "$GITHUB_OUTPUT"
          echo "artifact-name=tfplan-${TF_ENV}-${TF_COMPONENT}-${GITHUB_SHA}-${RUN_ATTEMPT}" >> "$GITHUB_OUTPUT"
          terraform show -no-color tfplan > "$RUNNER_TEMP/plan.txt"
          {
            echo '### Terraform plan (preview, not the applied plan)'
            echo '```'; head -c 60000 "$RUNNER_TEMP/plan.txt"; echo; echo '```'
          } > "$RUNNER_TEMP/comment.md"
          cat "$RUNNER_TEMP/comment.md" >> "$GITHUB_STEP_SUMMARY"
      - if: steps.plan.outputs.has-changes == 'true' && !inputs.preview
        run: tar -czf "$RUNNER_TEMP/tfwd.tgz" .
      - if: steps.plan.outputs.has-changes == 'true' && !inputs.preview
        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with:
          name: ${{ steps.plan.outputs.artifact-name }}
          path: ${{ runner.temp }}/tfwd.tgz
          retention-days: 1
      - if: steps.plan.outputs.has-changes == 'true' && inputs.preview
        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with:
          name: ${{ steps.plan.outputs.artifact-name }}-comment
          path: ${{ runner.temp }}/comment.md
          retention-days: 1
  comment:
    needs: plan
    if: inputs.preview && needs.plan.outputs.has-changes == 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 5
    permissions:
      pull-requests: write
    steps:
      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with:
          name: ${{ needs.plan.outputs.artifact-name }}-comment
      - env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
        run: gh pr comment "$PR_NUMBER" --repo "$GITHUB_REPOSITORY" --body-file comment.md
```

## Notes

- The PR run never uploads `tfplan`; it is never applied. Only the merge run uploads the whole working directory, including `.terraform`, which HashiCorp says to archive for a cross-machine apply. Whether that is the right content is an Ask First (medium confidence, see register M8).
- The merge-time plan runs under `<environment>` with the deploy role because it takes the state lock; a read-only role cannot write the S3 lock file (needs `s3:PutObject` and `s3:DeleteObject`, see [state backends](./state-backends.md)).
- The artifact name ends in the run attempt so a re-run of the same commit does not reuse a name; that artifact names must be unique within a run is (unverified), see register U10.
- `-lock=false` on the preview is the read-only choice (medium confidence, see register M4); HashiCorp calls it dangerous when others run commands on the same workspace, so the comment is labelled preview.
- Whether a refresh or plan writes any object, so that "never writes to cloud" holds strictly, is (unverified), see register U3.
- A plan comment is capped at 65535 characters; the script truncates at 60000 bytes and always writes the job summary (limit 1 MiB per step).
- `terraform_wrapper: false` avoids the wrapper altering stdout; its effect on `-detailed-exitcode` was not read (unverified), see register U6.
- The `plan_only.tftest.hcl` mock syntax is (unverified), see register U7.
- Never print `terraform show -json` into logs or comments; use `-no-color` text.
