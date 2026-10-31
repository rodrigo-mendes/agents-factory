# Never-do patterns with examples

Back to [SKILL.md](../SKILL.md). GitHub.com docs as of 2026-10-30. Each pattern shows the wrong form and the alternative.

Contents: [N1](#n1-reusable-workflow-in-a-subfolder) | [N2](#n2-secrets-inherit-to-a-block) | [N3](#n3-caller-env-or-github_env-across-the-call) | [N4](#n4-environment-on-the-calling-job) | [N5](#n5-secrets-context-in-a-composite-action) | [N6](#n6-run-step-without-shell) | [N7](#n7-required-check-from-a-path-filtered-workflow) | [N8](#n8-raising-permissions-in-the-called-workflow) | [N9](#n9-paths-and-paths-ignore-together) | [N10](#n10-credentials-in-cache-paths)

## N1. Reusable workflow in a subfolder

Subdirectories of the workflows folder are not supported; the call fails.

```yaml
# ❌ Wrong
uses: ./.github/workflows/node/build.yml
# ✅ Correct
uses: ./.github/workflows/_node-build.yml
```

Source: https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows

## N2. `secrets: inherit` to a block

It passes every caller secret, only one level deep, and hides which secrets a block needs; nested blocks silently get empty values.

```yaml
# ❌ Wrong
build:
  uses: ./.github/workflows/_deploy-vercel.yml
  secrets: inherit
# ✅ Correct
build:
  uses: ./.github/workflows/_deploy-vercel.yml
  secrets:
    VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
```

Source: https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows

## N3. Caller `env` or `GITHUB_ENV` across the call

Caller workflow-level `env` is not propagated, and `GITHUB_ENV` cannot pass values to caller steps.

```yaml
# ❌ Wrong
env:
  APP_DIR: apps/web
jobs:
  build:
    uses: ./.github/workflows/_node-build.yml   # expects env.APP_DIR
# ✅ Correct
jobs:
  build:
    uses: ./.github/workflows/_node-build.yml
    with:
      app-dir: apps/web
      mode: static
```

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations

## N4. `environment:` on the calling job

"The job that calls the reusable workflow can't use the `environment` keyword." Teams then fall back to repository secrets, which the family forbids for deploy credentials.

```yaml
# ❌ Wrong
deploy:
  uses: ./.github/workflows/_deploy-s3-cf.yml
  environment: prod
# ✅ Correct
deploy:
  uses: ./.github/workflows/_deploy-s3-cf.yml
  with:
    environment: prod
    artifact-name: ${{ needs.build.outputs.artifact-name }}
```

Source: https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows

## N5. Secrets context in a composite action

The `secrets` context is not available for composite actions.

```yaml
# ❌ Wrong (in action.yml)
env:
  NODE_AUTH_TOKEN: ${{ secrets.NPM_READ_TOKEN }}
# ✅ Correct (action.yml declares inputs.npm-token; the caller passes it)
env:
  NODE_AUTH_TOKEN: ${{ inputs.npm-token }}
```

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/contexts

## N6. Run step without shell

`shell` is required when `run` is set; the metadata is invalid and every caller fails.

```yaml
# ❌ Wrong
- run: npm ci
# ✅ Correct
- run: npm ci
  shell: bash
```

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax

## N7. Required check from a path-filtered workflow

A workflow skipped by a path filter leaves its check Pending and the pull request cannot merge. Full pattern: [monorepo with a ci-gate](./monorepo-ci-gate.md).

```yaml
# ❌ Wrong: "ci-web / build" required in branch protection
on:
  pull_request:
    paths: ["apps/web/**"]
# ✅ Correct: no path filter; only "ci-gate" is required
on:
  pull_request:
jobs:
  ci-gate:
    if: always()
    needs: [changes, web]
```

Source: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks

## N8. Raising permissions in the called workflow

The called workflow can only downgrade what the caller passes; elevation fails with 403.

```yaml
# ❌ Wrong: caller has contents: read, _x.yml asks for write
permissions:
  contents: write
# ✅ Correct: grant on the calling job
publish:
  uses: ./.github/workflows/_x.yml
  permissions:
    contents: write
```

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations

## N9. `paths` and `paths-ignore` together

You cannot use both filters for the same event. Wrong: `paths: ["apps/**"]` plus `paths-ignore: ["apps/**/*.md"]`. Correct: `paths: ["apps/**", "!apps/**/*.md"]`.

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

## N10. Credentials in cache paths

Anyone with read access can open a pull request and read cache contents. Wrong: `path` lists `~/.npmrc` that contains a token. Correct: `path: ~/.npm`, with the token arriving at run time through an input and never cached.

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching
