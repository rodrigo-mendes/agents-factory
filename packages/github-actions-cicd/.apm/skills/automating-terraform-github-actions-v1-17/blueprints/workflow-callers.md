# Callers: ci-infra and cd-infra

Back to [SKILL.md](../SKILL.md). Terraform 1.17.1; research date 2026-10-30. Thin callers over [`_tf-plan.yml`](./workflow-tf-plan.md) and [`_tf-apply.yml`](./workflow-tf-apply.md). Naming: `ci-` pull_request, `cd-` merge, `ops-` schedule (see [drift caller](./workflow-drift.md)). Free-plan variant: [plan variants](./plan-variants.md).

## Contents

- [ci-infra.yml](#ci-infrayml-pull-request-never-applies)
- [cd-infra.yml](#cd-infrayml-merge-saved-plan-apply-after-pr-review)

Repository layout (state per environment and component):

```text
infra/network/  main.tf  backend.tf  .terraform.lock.hcl  tests/plan_only.tftest.hcl
infra/env/prod/network.s3.tfbackend     # non-secret: bucket, key, region
infra/env/prod/app-oci.tfbackend        # oci backend: bucket, namespace, region, key
.github/workflows/  ci-infra.yml  cd-infra.yml  ops-drift.yml  _tf-plan.yml  _tf-apply.yml
```

## ci-infra.yml: pull request, never applies

```yaml
name: ci-infra
on:
  pull_request:            # no paths filter: ci-gate is the required check
permissions:
  contents: read
concurrency:
  group: ci-infra-${{ github.ref }}
  cancel-in-progress: true        # safe here: this workflow never applies
jobs:
  changes:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    outputs:
      infra: ${{ steps.diff.outputs.infra }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with: { fetch-depth: 0, persist-credentials: false }
      - id: diff
        env:
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
        run: |
          n=$(git diff --name-only "$BASE_SHA" HEAD -- infra | wc -l)
          echo "infra=$([ "$n" -gt 0 ] && echo true || echo false)" >> "$GITHUB_OUTPUT"
  network:
    needs: changes
    if: needs.changes.outputs.infra == 'true'
    permissions:
      contents: read
      id-token: write             # the plan job logs in (read-only role)
      pull-requests: write        # the comment job
    uses: ./.github/workflows/_tf-plan.yml
    with:
      working-directory: infra/network
      cloud: aws
      environment: prod           # preview runs under prod-pr
      component: network
      backend-config: ../env/prod/network.s3.tfbackend
      preview: true
  ci-gate:                        # the only required status check
    if: always()
    needs: [changes, network]
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - env:
          RESULTS: ${{ join(needs.*.result, ' ') }}
        run: |
          case " $RESULTS " in *" failure "*|*" cancelled "*) exit 1;; esac
```

A workflow-level `paths` filter on a required workflow leaves the check pending when no path matches; job-level detection plus `ci-gate` avoids it (pattern owned by `composing-github-actions-pipelines`). PRs from forks get no secrets, so cloud plans only work for same-repository branches; for fork-heavy repositories drop the cloud login and run fmt, validate and mocked tests only (Ask First in [SKILL.md](../SKILL.md)). The path to `backend-config` is relative to `working-directory`.

## cd-infra.yml: merge, saved plan, apply after PR review

```yaml
name: cd-infra
on:
  push:
    branches: [main]
    paths: ["infra/**"]
permissions:
  contents: read
concurrency:
  group: terraform-prod-network   # environment + component; covers plan and apply
  cancel-in-progress: false
jobs:
  plan:
    permissions:
      contents: read
      id-token: write
    uses: ./.github/workflows/_tf-plan.yml
    with:
      working-directory: infra/network
      cloud: aws
      environment: prod           # merge plan runs under prod: deploy role, takes the lock
      component: network
      backend-config: ../env/prod/network.s3.tfbackend
  apply:
    needs: plan
    if: needs.plan.outputs.has-changes == 'true'
    permissions:
      contents: read
      id-token: write
    uses: ./.github/workflows/_tf-apply.yml
    with:
      working-directory: infra/network
      cloud: aws
      environment: prod
      component: network
      plan-artifact-name: ${{ needs.plan.outputs.plan-artifact-name }}
```

- The human approval happened in the pull request: the reviewers read the rendered preview plan on protected `main` before merging.
- Workflow-level concurrency in the caller covers both jobs, so no other run for the same environment and component plans between this run's plan and apply (design placement, medium confidence, see register M1).
- Use one caller or one job pair per component, each with its own group name; for OCI set `cloud: oci` and an `oci` backend file ([state backends](./state-backends.md)).
- The fresh plan on the merge commit is the plan that gets applied; the PR plan was only a preview.
