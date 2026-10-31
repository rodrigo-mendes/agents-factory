# Callers: ci, cd and JDK matrix

Back to [SKILL.md](../SKILL.md). Names: `ci-<app>.yml` for pull requests, `cd-<app>.yml` for merges; structure of `workflow_call` belongs to `composing-github-actions-pipelines`. Research date 2026-10-30.

## ci-orders.yml (pull_request, never publishes)

```yaml
# ./.github/workflows/ci-orders.yml
name: ci-orders
on:
  pull_request:
    paths: ['services/orders/**']
permissions:
  contents: read
concurrency:
  group: ci-orders-${{ github.ref }}
  cancel-in-progress: true   # a newer push supersedes the older PR run
jobs:
  build:
    strategy:
      fail-fast: false
      matrix:
        java: ['17', '21', '25']
    permissions:
      contents: read
    uses: ./.github/workflows/_java-build.yml
    with:
      tool: maven
      java-version: ${{ matrix.java }}
      package: jar
      working-directory: services/orders
```

- No `secrets:` block, no `id-token`, no `packages: write`: PR code runs here.
- A path filter leaves a required status check Pending when the workflow is skipped; use one always-running gate job as the required check (the gate design is owned by `composing-github-actions-pipelines`).
- Each leg uploads reports and a JAR with the JDK in the name, so artifact names never collide (https://github.com/actions/upload-artifact/blob/v7.0.2/README.md).

## cd-orders.yml (merge to main, builds the deployable once)

```yaml
# ./.github/workflows/cd-orders.yml
name: cd-orders
on:
  push:
    branches: [main]
    paths: ['services/orders/**']
permissions:
  contents: read
concurrency:
  group: cd-orders
  cancel-in-progress: false   # never cancel a build that may be releasing
jobs:
  build:
    permissions:
      contents: read
    uses: ./.github/workflows/_java-build.yml
    with:
      tool: maven
      java-version: '21'          # the Lambda runtime: java21
      package: zip
      working-directory: services/orders
  # release: needs: build
  #   pass needs.build.outputs.artifact-name and needs.build.outputs.artifact-digest to the
  #   release workflow of deploying-aws-lambda (zip) or publishing-container-images-github-actions (image)
```

- Only one JDK builds the deployable; tests for 17 and 25 already ran in `ci-orders.yml`.
- The release job (owned by the neighbour skills) holds the cloud login and the environment; this file stays credential-free.

## Plans and approval

| Variant | CI build | Release gate |
|---|---|---|
| Default: GitHub Pro or Team, private repo | no credentials needed | environment with deployment branch policy `main`; protected `main` with required PR reviewers; approval is the PR review before merge |
| Weaker: GitHub Free, private repo | no credentials needed | no environments and no protected branches; cloud roles trust `ref:refs/heads/main`; any unavoidable static secret is a least-privilege repository secret with a warning |

Required reviewers, wait timers and artifact attestations are an upgrade path for public repositories or Enterprise only. OIDC subject for repositories created after 2026-07-15 uses the immutable format `repo:OWNER@OWNER-ID/REPO@REPO-ID:...`; that matters to the neighbour login skills, not to this build.

## Library publishing (Ask First, cd-* only)

- `GITHUB_TOKEN` to GitHub Packages: `permissions: contents: read, packages: write`, distribution repository `id` `github`, no stored secret.
- Another registry: `server-id` plus `server-username-env-var` and `server-password-env-var` in setup-java, values read from an environment secret; on GitHub Free private repositories environment secrets are not available, so the secret becomes a repository secret (a documented exception to environment-scoped secrets).
- With Maven 3.10, `mvn-server-repository-origins` scopes a credential to named origins.
- `mvn deploy` re-runs the lifecycle; for a promoted artifact prefer a release job that publishes the downloaded file.

Sources: https://docs.github.com/en/actions/tutorials/publish-packages/publish-java-packages-with-maven, https://github.com/actions/setup-java/blob/v6.1.0/docs/advanced-usage.md.
