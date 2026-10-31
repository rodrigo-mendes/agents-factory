# Always-do patterns with code

Back to [SKILL.md](../SKILL.md). GitHub.com docs as of 2026-10-30. Pins come from the family facts (checkout v7.0.1, upload-artifact v7.0.2, download-artifact v8.0.2, setup-node v7.1.0).

Contents: [A1 layout](#a1-layout-and-naming) | [A2 reusable workflow contract](#a2-reusable-workflow-contract) | [A3 caller wiring](#a3-caller-wiring-and-permissions) | [A4 environment as input](#a4-environment-as-an-input) | [A5 timeouts and concurrency](#a5-timeouts-and-concurrency)

## A1. Layout and naming

Reusable workflows sit flat in the workflows folder; subdirectories are not supported. The `_` prefix is a family decision that separates blocks from triggerable callers (https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows).

```text
.github/
  workflows/
    ci-web.yml               # caller, on: pull_request
    cd-web.yml               # caller, on: push to main
    ops-nightly.yml          # caller, on: schedule / workflow_dispatch
    _node-build.yml          # reusable, on: workflow_call
  actions/
    node/setup/action.yml    # composite action
    repo/changes/action.yml  # composite action
```

## A2. Reusable workflow contract

Input `type` must be `boolean`, `number` or `string`; without a `default`, booleans are `false`, numbers `0`, strings `""`. Outputs map a job output. `required: true` on a secret only checks that the caller passes it, not that it has a value (https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).

The interface below is the one `building-nextjs-github-actions-v16-4` defines for `_node-build.yml`; the owner skill holds the full steps. Secrets are declared by name under `workflow_call.secrets` (see `_deploy-vercel.yml` in the [catalog](./catalog-reference.md)).

```yaml
# ./.github/workflows/_node-build.yml (interface and job skeleton)
name: _node-build
on:
  workflow_call:
    inputs:
      app-dir:         { type: string, default: ".", description: "Folder holding package.json" }
      mode:            { type: string, required: true, description: "static | standalone | vercel" }
      node-version:    { type: string, default: "24" }
      package-manager: { type: string, default: "npm" }
    outputs:
      artifact-name:
        description: Name of the uploaded build artifact (empty in mode vercel)
        value: ${{ jobs.build.outputs.artifact-name }}
      artifact-digest:
        description: Digest reported by upload-artifact (empty in mode vercel)
        value: ${{ jobs.build.outputs.artifact-digest }}
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    outputs:
      artifact-name: ${{ steps.meta.outputs.name }}
      artifact-digest: ${{ steps.upload.outputs.artifact-digest }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      # install, lint, test, build, upload (id: upload) and the meta step: owner skill
```

Node lines (26, 24, 22) and the build steps belong to `building-nextjs-github-actions-v16-4`. The setup composite of this skill is in [composite actions](./composite-actions.md).

## A3. Caller wiring and permissions

The caller's workflow-level `env` is not propagated and the called workflow's env is not visible to the caller; results travel through outputs only. With no `permissions` on the calling job, the called workflow gets the default token permissions, and it can only reduce what it receives (https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations).

```yaml
# ./.github/workflows/cd-web.yml (excerpt)
concurrency:
  group: deploy-web-prod
  cancel-in-progress: false
jobs:
  build:
    uses: ./.github/workflows/_node-build.yml
    permissions:
      contents: read
    with:
      app-dir: apps/web
      mode: vercel
  deploy:
    needs: build
    uses: ./.github/workflows/_deploy-vercel.yml
    permissions:
      contents: read
    with:
      environment: prod
      vercel-cli-version: <pinned-version>
    secrets:
      VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
      VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
      VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
  verify:
    needs: [build, deploy]
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - run: echo "deployed ${DEPLOY_URL}, artifact ${ARTIFACT}"
        env:
          DEPLOY_URL: ${{ needs.deploy.outputs.deployment-url }}
          ARTIFACT: ${{ needs.build.outputs.artifact-name }}
```

`<pinned-version>` is a placeholder: the owner skill requires a pinned Vercel CLI version and gives no default. The jobs inside each block carry their own `timeout-minutes`.

A matrix job can call a reusable workflow; the caller output is the one set by the last successful matrix leg that sets a value (https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows). Chains go up to 10 levels; `secrets: inherit` reaches only the directly called workflow, so deeper levels need explicit pass-through.

## A4. Environment as an input

The job that calls a reusable workflow cannot use `environment:`. The deploying job inside the called workflow reads it from a string input, so environment secrets are available there (https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows). Plan availability of environments: [plan variants](./plan-variants.md).

```yaml
# ./.github/workflows/_deploy-s3-cf.yml (excerpt; interface per building-nextjs-github-actions-v16-4)
on:
  workflow_call:
    inputs:
      environment:     { type: string, required: true }
      artifact-name:   { type: string, required: true }
      artifact-digest: { type: string, default: "" }
permissions:
  contents: read
jobs:
  deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    environment: ${{ inputs.environment }}
    concurrency:
      group: deploy-s3-${{ inputs.environment }}
      cancel-in-progress: false
    permissions:
      contents: read
      id-token: write            # this job only
    steps:
      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with:
          name: ${{ inputs.artifact-name }}
      - uses: ./.github/actions/cloud/login-aws
        with:
          role-arn: ${{ vars.AWS_DEPLOY_ROLE_ARN }}   # variable of the <env> environment
          region: ${{ vars.AWS_REGION }}
      # sync, origin switch, invalidation: owner skill
```

The PR-side role `AWS_PR_ROLE_ARN` lives in the `<env>-pr` environment and is read the same way, inside the called job. An environment secret that the caller does not supply is said to resolve to an empty string unless declared `required: true` (medium confidence).

## A5. Timeouts and concurrency

- Job `timeout-minutes` defaults to 360; a hung job otherwise burns up to six hours of private-repository minutes. The value 5 to 30 is a family choice.
- PR CI: `group: ${{ github.workflow }}-${{ github.head_ref || github.run_id }}` with `cancel-in-progress: true`. `github.head_ref` is defined only on `pull_request`, so the fallback is `github.run_id`. In a called workflow `github.workflow` is the caller's workflow name.
- Every caller has a `concurrency` group: PR callers as above, deploy callers per app and environment (`deploy-<app>-<env>`).
- Deploy: one group per environment with `cancel-in-progress: false` (medium confidence, design inference). `queue: max` keeps up to 100 pending runs and is invalid with `cancel-in-progress: true`.

Sources: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency ; https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
