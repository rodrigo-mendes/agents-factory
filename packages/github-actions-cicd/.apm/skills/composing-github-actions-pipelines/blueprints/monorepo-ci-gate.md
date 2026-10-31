# Monorepo with a ci-gate

Back to [SKILL.md](../SKILL.md). GitHub.com docs as of 2026-10-30. The pending behaviour is documented; the combined design (job-level detection plus `ci-gate`) is composed from official pieces (medium confidence).

Contents: [Why](#why) | [Caller ci-monorepo.yml](#caller-ci-monorepoyml) | [Composite changes](#composite-githubactionsrepochangesactionyml) | [Options](#options) | [Check names](#check-names)

## Why

- A workflow skipped by path filtering, branch filtering or a commit message leaves its checks Pending; a pull request that requires them is blocked. GitHub advises avoiding required workflows that can be skipped.
- A job skipped by `if` reports Success. A job whose dependency failed or was skipped is itself skipped and may not block merging, so a required aggregate job needs `always()` with `needs`.
- Path filter facts: `paths` and `paths-ignore` cannot be mixed; a diff over 3,000 files may skip; tags are not evaluated.

Sources: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks ; https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

## Caller `ci-monorepo.yml`

Pull-request jobs never deploy and use no credentials of a deployable environment. Branch protection (Pro/Team) or nothing (Free, see [plan variants](./plan-variants.md)): require only `ci-gate`.

```yaml
# ./.github/workflows/ci-monorepo.yml
name: ci-monorepo
on:
  pull_request:
permissions:
  contents: read
concurrency:
  group: ${{ github.workflow }}-${{ github.head_ref || github.run_id }}
  cancel-in-progress: true
jobs:
  changes:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    outputs:
      web: ${{ steps.diff.outputs.web }}
      api: ${{ steps.diff.outputs.api }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 0
          persist-credentials: false
      - id: diff
        uses: ./.github/actions/repo/changes
        with:
          base-sha: ${{ github.event.pull_request.base.sha }}
  web:
    needs: changes
    if: needs.changes.outputs.web == 'true'
    uses: ./.github/workflows/_node-build.yml
    permissions:
      contents: read
    with:
      app-dir: apps/web
      mode: vercel
  api:
    needs: changes
    if: needs.changes.outputs.api == 'true'
    uses: ./.github/workflows/_java-build.yml
    permissions:
      contents: read
    with:
      tool: maven
      working-directory: services/api
      package: jar
  ci-gate:
    if: always()
    needs: [changes, web, api]
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Fail if any needed job failed or was cancelled
        env:
          R_CHANGES: ${{ needs.changes.result }}
          R_WEB: ${{ needs.web.result }}
          R_API: ${{ needs.api.result }}
        run: |
          for r in "$R_CHANGES" "$R_WEB" "$R_API"; do
            case "$r" in
              success|skipped) ;;
              *) echo "a required job ended with: $r"; exit 1 ;;
            esac
          done
```

The `fetch-depth` input of checkout was not confirmed on a page read for this unit (unverified). The inputs of `_node-build.yml` (`mode: vercel` runs checks only, no artifact) and `_java-build.yml` are the ones the owner skills define (`building-nextjs-github-actions-v16-4`, `building-java-github-actions`); see the [catalog](./catalog-reference.md).

## Composite `./.github/actions/repo/changes/action.yml`

```yaml
name: repo-changes
description: Emit true/false per app area from the PR diff
inputs:
  base-sha:
    description: Base commit of the pull request
    required: true
outputs:
  web:
    description: apps/web changed
    value: ${{ steps.calc.outputs.web }}
  api:
    description: services/api changed
    value: ${{ steps.calc.outputs.api }}
runs:
  using: composite
  steps:
    - id: calc
      shell: bash
      env:
        BASE_SHA: ${{ inputs.base-sha }}
      run: |
        files="$(git diff --name-only "$BASE_SHA"...HEAD)"
        has() { grep -Eq "$1" <<<"$files" && echo true || echo false; }
        shared="$(has '^(\.github/|package-lock\.json$)')"
        web="$(has '^apps/web/')"; api="$(has '^services/api/')"
        [ "$shared" = true ] && web=true && api=true
        { echo "web=$web"; echo "api=$api"; } >> "$GITHUB_OUTPUT"
```

The three-dot `git diff` mirrors how GitHub evaluates PR path filters. A change under `.github/` re-runs everything because blocks are local.

## Options

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Path filters per caller | Simple, no runs for untouched apps | Cannot be required checks | Checks are informational |
| Job-level detection plus `ci-gate` (default) | One required check that always reports | A small always-on job; a script to maintain | Merge-gating monorepo CI |

## Check names

The status-check context of a job inside a called workflow is reported by community sources as `<caller job> / <called job>`, which no official page confirms. `ci-gate` is a plain job, so the design does not depend on it. Read the exact name from a pull request's checks list before writing any ruleset by hand.
