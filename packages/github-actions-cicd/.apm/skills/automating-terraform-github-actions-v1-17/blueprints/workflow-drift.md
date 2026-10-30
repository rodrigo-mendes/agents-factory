# Caller ops-drift.yml: schedule, opens an issue, never applies

Back to [SKILL.md](../SKILL.md). Terraform 1.17.1; research date 2026-10-30. Sibling callers `ci-infra.yml` and `cd-infra.yml`: [callers](./workflow-callers.md). Naming: `ops-` schedule or dispatch.

```yaml
name: ops-drift
on:
  schedule: [{ cron: "17 5 * * *" }]
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: terraform-prod-network   # same group as cd-infra: never plans during an apply
  cancel-in-progress: false
jobs:
  drift:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    environment: prod-pr          # read-only role
    permissions:
      contents: read
      issues: write
      id-token: write
    defaults:
      run:
        working-directory: infra/network
    env:
      TF_IN_AUTOMATION: "true"
      TF_INPUT: "false"
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: hashicorp/setup-terraform@dfe3c3f87815947d99a8997f908cb6525fc44e9e # v4.0.1
        with:
          terraform_version: "1.17.1"
          terraform_wrapper: false
      # Read-only cloud login: federating-github-actions-aws-oidc or federating-github-actions-oci
      - name: Cloud login (placeholder)
        run: echo "replace with the read-only login step"
      - run: terraform init -input=false -backend-config=../env/prod/network.s3.tfbackend
      - id: drift
        run: |
          set +e
          terraform plan -input=false -lock=false -refresh-only -detailed-exitcode -no-color > drift.txt
          rc=$?
          set -e
          if [ "$rc" -eq 1 ]; then exit 1; fi
          echo "exitcode=$rc" >> "$GITHUB_OUTPUT"
      - if: steps.drift.outputs.exitcode == '2'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          LABEL: drift-prod-network
        run: |
          gh label create "$LABEL" --repo "$GITHUB_REPOSITORY" 2>/dev/null || true
          open=$(gh issue list --repo "$GITHUB_REPOSITORY" --label "$LABEL" --state open --json number --jq 'length')
          if [ "$open" -eq 0 ]; then
            head -c 60000 drift.txt > body.txt
            gh issue create --repo "$GITHUB_REPOSITORY" --label "$LABEL" --title "Drift: prod/network" --body-file body.txt
          fi
```

## Notes

- No apply step exists in this workflow, by design; the fix goes through a PR.
- The drift job shares the `terraform-prod-network` group with `cd-infra.yml`, so it never plans while an apply runs, and `cancel-in-progress: false` keeps a queued run instead of cancelling it.
- A run opens an issue only when none is open under the label, so a drift that stays open does not create a daily duplicate.
- Scheduled workflows run on the latest default-branch commit, can be delayed under load, and in public repositories are disabled after 60 days without repository activity (https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).
- Schedule plus issue is a composition of documented parts (medium confidence, see register M2). Whether a `-refresh-only` plan takes the state lock is (unverified), see register U3.
