# Reusable workflows and contracts: _promote.yml

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Fixed names: `_promote.yml`, `_smoke-test.yml`, `_rollback.yml` (family rule 5; reusable workflows must sit directly in the workflows folder, no subfolders). The other two are in [smoke and rollback](./workflow-smoke-rollback.md). The skill ships no workflow files; these are contracts to generate.

## Contents

- Contract table
- Target adapters
- _promote.yml

## Contract table

| Workflow | Inputs (typed) | Outputs | Secrets (by name) | Permissions |
|---|---|---|---|---|
| `_promote.yml` | `environment` string, `app` string, `target` string (`lambda`, `ecs`, `cloudfront`, `vercel`, `terraform`), `phase` string (`canary` or `complete`), `canary_weight` string, `artifact_name` string, `artifact_sha256` string | `deployed_ref`, `previous_ref` | `VERCEL_TOKEN` (optional, only for `vercel`) | `contents: read`; `id-token: write` on the login job only |
| `_smoke-test.yml` | `base_url` string, `expected_ref` string, `check_script` string, `attempts` string | `passed` (`true` or `false`) | none | `contents: read` |
| `_rollback.yml` | `environment` string, `app` string, `target` string, `previous_ref` string, `reason` string | `rolled_back_to` | `VERCEL_TOKEN` (optional) | `contents: read`; `id-token: write` on the login job only |

Rules for all three (family rules 6 and 7): no `secrets: inherit`, caller-level `env` is not passed down, results travel through outputs. A workflow reads its role ARN and region from `vars` inside its own job that declares `environment: ${{ inputs.environment }}`. That environment values resolve in the called job and not in the caller is (medium confidence).

## Target adapters

Each target has two composite actions the caller never edits: `./.github/actions/<target>/release` (publish and shift to `canary_weight`, or complete) and `./.github/actions/<target>/revert`. Release steps for Lambda belong to `deploying-aws-lambda`; the adapters only add the weight and rollback logic described in [progressive delivery](./progressive-delivery.md). Inputs of an adapter: `ref`, `weight`, `phase`.

## _promote.yml

```yaml
# Representative; adapt to your environment (pins per _family_facts.md)
name: _promote
on:
  workflow_call:
    inputs:
      environment: { type: string, required: true }
      app: { type: string, required: true }
      target: { type: string, required: true }
      phase: { type: string, required: true }          # canary | complete
      canary_weight: { type: string, required: true }  # "0" = all at once
      artifact_name: { type: string, required: true }
      artifact_sha256: { type: string, required: true }
    secrets:
      VERCEL_TOKEN: { required: false }
    outputs:
      deployed_ref: { value: "${{ jobs.promote.outputs.deployed_ref }}" }
      previous_ref: { value: "${{ jobs.promote.outputs.previous_ref }}" }
permissions:
  contents: read
jobs:
  promote:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    environment:
      name: ${{ inputs.environment }}
      url: ${{ vars.APP_URL }}
    concurrency:
      group: deploy-${{ inputs.app }}-${{ inputs.environment }}
      cancel-in-progress: false
    permissions:
      contents: read
      id-token: write            # this is the job that logs in (family rules 7 and 18)
    outputs:
      deployed_ref: ${{ steps.release.outputs.ref }}
      previous_ref: ${{ steps.release.outputs.previous_ref }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with: { persist-credentials: false }   # the local login composite needs the workspace
      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with: { name: "${{ inputs.artifact_name }}", path: dist }
      - name: Verify artifact hash
        run: echo "${EXPECTED_SHA256}  dist/function.zip" | sha256sum -c -
        env:
          EXPECTED_SHA256: ${{ inputs.artifact_sha256 }}
      - uses: ./.github/actions/cloud/login-aws   # owned by federating-github-actions-aws-oidc
        with:
          role-arn: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
          region: ${{ vars.AWS_REGION }}
      - id: release
        uses: ./.github/actions/lambda/release   # one adapter per target; swap per inputs.target
        with: { ref: "${{ inputs.artifact_sha256 }}", weight: "${{ inputs.canary_weight }}", phase: "${{ inputs.phase }}" }
```

Notes:
- Credentials do not cross jobs, so the login job also runs the release adapter. Download and hash check come before the login step; the token is requested only when the login composite runs, and the calling job must grant `id-token: write` for the called job to hold it. Splitting the release away from the login job is not possible.
- For `target: vercel` the artifact is the prebuilt output archive made in the build stage (see [always-do patterns](./always-do-patterns.md), Vercel); the same digest identifies it and the adapter verifies that archive instead of `dist/function.zip`.
- The same concurrency group in the sequential `canary` and `complete` calls does not deadlock because the jobs run one after another through `needs`; a group spanning sequential jobs of one run is (medium confidence).
- The hash step fits zip artifacts; for images pass the digest as `artifact_sha256` and skip the download (the adapter deploys `repo@sha256:<digest>`).
- That `gh` and `aws` are preinstalled on `ubuntu-latest` is (medium confidence); install them explicitly if a run fails with command not found.
- Pass `canary_weight: "0"` for `dev` so it releases all at once.
- Do not add a build step here; the Verification Loop in SKILL.md fails the pipeline if one appears.
