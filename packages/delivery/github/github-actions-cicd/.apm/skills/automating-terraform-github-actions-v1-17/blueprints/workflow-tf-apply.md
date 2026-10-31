# Reusable apply workflow `_tf-apply.yml`

Back to [SKILL.md](../SKILL.md). Terraform 1.17.1; research date 2026-10-30. Consumes the artifact uploaded by [`_tf-plan.yml`](./workflow-tf-plan.md); called only from `cd-infra.yml` ([callers](./workflow-callers.md)).

## Contract

| Item | Value |
|---|---|
| Inputs | `working-directory`, `cloud` (`aws` or `oci`), `environment`, `component`, `plan-artifact-name` |
| Outputs | none |
| Secrets | none passed; the job reads the deploy role variable `AWS_DEPLOY_ROLE_ARN` (or the OCI secrets) of the `<environment>` environment |
| Permissions | contents read, id-token write (this job logs in) |
| Environment | `<environment>`, deployment branch policy `main`; no required reviewers by default |

The approval is the review of the rendered plan in the pull request, on protected `main` with required reviewers, before the merge that starts this run (Pro or Team; https://docs.github.com/en/get-started/learning-about-github/githubs-plans). Required reviewers on the environment are the upgrade path for public repositories or Enterprise. The Free variant has no environments: see [plan variants](./plan-variants.md).

## Workflow

```yaml
name: _tf-apply
on:
  workflow_call:
    inputs:
      working-directory:  { type: string, required: true }
      cloud:              { type: string, required: true }   # aws | oci
      environment:        { type: string, required: true }
      component:          { type: string, required: true }
      plan-artifact-name: { type: string, required: true }
permissions:
  contents: read
env:
  TF_IN_AUTOMATION: "true"
  TF_INPUT: "false"
jobs:
  apply:
    runs-on: ubuntu-latest        # same label as the plan job: same OS and CPU
    timeout-minutes: 60
    environment: ${{ inputs.environment }}
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false   # the local login composite needs the repository on disk
      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with:
          name: ${{ inputs.plan-artifact-name }}
          path: ${{ runner.temp }}
      - env:
          WORKDIR: ${{ inputs.working-directory }}
        run: |
          mkdir -p "$GITHUB_WORKSPACE/$WORKDIR"
          tar -xzf "$RUNNER_TEMP/tfwd.tgz" -C "$GITHUB_WORKSPACE/$WORKDIR"
      - uses: hashicorp/setup-terraform@dfe3c3f87815947d99a8997f908cb6525fc44e9e # v4.0.1
        with:
          terraform_version: "1.17.1"
          terraform_wrapper: false
      # Cloud login (deploy role); the checkout above lets local composites run.
      - name: Cloud login AWS (placeholder, see federating-github-actions-aws-oidc)
        if: inputs.cloud == 'aws'
        run: echo "replace with the AWS login step"
      - name: Cloud login OCI (placeholder, see federating-github-actions-oci)
        if: inputs.cloud == 'oci'
        run: echo "replace with the OCI login step"
      - working-directory: ${{ inputs.working-directory }}
        run: terraform apply -input=false tfplan
```

## Notes

- Apply runs the saved `tfplan` only; there is no `-auto-approve` and no second plan.
- Terraform expects the working directory extracted at the same absolute path, the same OS and CPU, and identical provider plugins. Extracting into `$GITHUB_WORKSPACE/<dir>` is meant to reproduce the plan job's path; that the hosted-runner workspace path is identical across jobs is (unverified), see register U2.
- Official behaviour for a stale saved plan (state changed after the plan) is (unverified), see register U1; the design avoids it by holding one concurrency group over plan and apply and by re-planning on the next merge instead of retrying.
- Plan and apply run in the same workflow run under one concurrency group, so a later run cannot plan between this run's plan and apply.
- Credentials are never passed through `-backend-config`; backend values come from the tfbackend file ([state backends](./state-backends.md)).
- Add a Checkov or Trivy scan of the plan inputs before apply as described in `securing-supply-chain-github-actions`; blast-radius controls (per-component roles, environment split) are in `limiting-blast-radius-github-actions-deploys`.
