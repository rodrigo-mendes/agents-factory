# _smoke-test.yml, _rollback.yml and the cd caller

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Contracts: [reusable workflows](./reusable-workflows.md).

## Contents

- _smoke-test.yml
- _rollback.yml
- cd caller
- Rollback triggers

## _smoke-test.yml

```yaml
# Representative; adapt to your environment
name: _smoke-test
on:
  workflow_call:
    inputs:
      base_url: { type: string, required: true }
      expected_ref: { type: string, required: true }
      check_script: { type: string, required: true }   # repo path under ./scripts/, read-only HTTP checks
      attempts: { type: string, required: true }
    outputs:
      passed: { value: "${{ jobs.smoke.outputs.passed }}" }
permissions:
  contents: read
jobs:
  smoke:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    outputs:
      passed: ${{ steps.run.outputs.passed }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with: { persist-credentials: false }
      - id: run
        env:
          BASE_URL: ${{ inputs.base_url }}
          EXPECTED_REF: ${{ inputs.expected_ref }}
          ATTEMPTS: ${{ inputs.attempts }}
          CHECK_SCRIPT: ${{ inputs.check_script }}
        run: |
          case "$CHECK_SCRIPT" in ./scripts/*.sh) ;; *) echo "passed=false" >> "$GITHUB_OUTPUT"; exit 0 ;; esac
          if bash "$CHECK_SCRIPT"; then echo "passed=true" >> "$GITHUB_OUTPUT"
          else echo "passed=false" >> "$GITHUB_OUTPUT"; fi
```

The job always exits 0 and reports `passed`, so the caller decides rollback. It has no cloud login and no environment: it sends read-only HTTP requests to the canary URL. The script path reaches the shell only through `env`, and anything outside `./scripts/` counts as a failed check. Checks that need cloud signals (Lambda `x-amz-executed-version`, ECS alarms) run inside the promote adapter.

## _rollback.yml

```yaml
# Representative; adapt to your environment
name: _rollback
on:
  workflow_call:
    inputs:
      environment: { type: string, required: true }
      app: { type: string, required: true }
      target: { type: string, required: true }
      previous_ref: { type: string, required: true }
      reason: { type: string, required: true }
    secrets:
      VERCEL_TOKEN: { required: false }
    outputs:
      rolled_back_to: { value: "${{ jobs.rollback.outputs.rolled_back_to }}" }
permissions:
  contents: read
jobs:
  rollback:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    environment: { name: "${{ inputs.environment }}", url: "${{ vars.APP_URL }}" }
    concurrency: { group: "deploy-${{ inputs.app }}-${{ inputs.environment }}", cancel-in-progress: false }
    permissions: { contents: read, id-token: write }   # the job that logs in (family rule 18)
    outputs:
      rolled_back_to: ${{ steps.revert.outputs.ref }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with: { persist-credentials: false }
      - uses: ./.github/actions/cloud/login-aws     # owned by federating-github-actions-aws-oidc
        with: { role-arn: "${{ vars.AWS_DEPLOY_ROLE_ARN }}", region: "${{ vars.AWS_REGION }}" }
      - id: revert
        uses: ./.github/actions/lambda/revert    # repoints alias, task set, origin path or Vercel alias
        with: { ref: "${{ inputs.previous_ref }}" }
```

Rollback repoints to an artifact that was already verified; it never rebuilds.

## cd caller

```yaml
# Representative; adapt to your environment. cd-orders.yml, push to main
on: { push: { branches: [main] } }
permissions: { contents: read }
jobs:
  build:   # build once (building-java-github-actions); outputs artifact-name and artifact-digest
    uses: ./.github/workflows/_java-build.yml
    with: { tool: maven, package: zip, working-directory: services/orders }
  deploy-dev:
    needs: build
    uses: ./.github/workflows/_promote.yml
    permissions: { contents: read, id-token: write }   # a caller grants what the called login job needs
    with: { environment: dev, app: orders, target: lambda, phase: complete, canary_weight: "0",
            artifact_name: "${{ needs.build.outputs.artifact-name }}", artifact_sha256: "${{ needs.build.outputs.artifact-digest }}" }
  canary-prod:
    needs: [build, deploy-dev]   # stage omitted here for brevity; repeat the pattern
    uses: ./.github/workflows/_promote.yml
    permissions: { contents: read, id-token: write }
    with: { environment: prod, app: orders, target: lambda, phase: canary, canary_weight: "0.10",
            artifact_name: "${{ needs.build.outputs.artifact-name }}", artifact_sha256: "${{ needs.build.outputs.artifact-digest }}" }
  smoke-prod:
    needs: canary-prod
    uses: ./.github/workflows/_smoke-test.yml
    with: { base_url: "https://orders.example.com", expected_ref: "${{ needs.canary-prod.outputs.deployed_ref }}",
            check_script: ./scripts/smoke.sh, attempts: "5" }
  complete-prod:
    needs: [build, canary-prod, smoke-prod]
    if: needs.smoke-prod.outputs.passed == 'true'
    uses: ./.github/workflows/_promote.yml
    permissions: { contents: read, id-token: write }
    with: { environment: prod, app: orders, target: lambda, phase: complete, canary_weight: "0",
            artifact_name: "${{ needs.build.outputs.artifact-name }}", artifact_sha256: "${{ needs.build.outputs.artifact-digest }}" }
  rollback-prod:   # smoke failed, or the completing step failed after a passed smoke
    needs: [canary-prod, smoke-prod, complete-prod]
    if: always() && needs.canary-prod.result == 'success' && (needs.smoke-prod.outputs.passed != 'true' || needs.complete-prod.result == 'failure')
    uses: ./.github/workflows/_rollback.yml
    permissions: { contents: read, id-token: write }
    with: { environment: prod, app: orders, target: lambda, previous_ref: "${{ needs.canary-prod.outputs.previous_ref }}", reason: prod-not-completed }
  prod-result:     # final job: the run is red unless prod completed with no rollback
    needs: [complete-prod, rollback-prod]
    if: always()
    runs-on: ubuntu-latest
    timeout-minutes: 5
    permissions: {}
    steps:
      - env: { COMPLETE: "${{ needs.complete-prod.result }}", ROLLBACK: "${{ needs.rollback-prod.result }}" }
        run: |
          if [ "$COMPLETE" != "success" ] || [ "$ROLLBACK" != "skipped" ]; then echo "prod not completed (rollback: $ROLLBACK)"; exit 1; fi
```

After an automatic rollback `rollback-prod` succeeds but `prod-result` fails, so the run ends red and any later environment (which `needs: prod-result`) never starts. A manual rollback uses the same workflow from `ops-rollback-<app>.yml` on `workflow_dispatch`, with `previous_ref` chosen from the deployments API.

## Rollback triggers

Per-target mechanism and automatic coverage: [progressive delivery](./progressive-delivery.md).

If the promote job itself fails mid-shift (before smoke runs), the release adapter must run its revert step under `if: failure()` and then fail the job, so the environment is not left half-shifted. A runner that dies cannot run that step; use CodeDeploy (Lambda) or ECS alarms when rollback must not depend on the runner.
