# Callers: ci-web, cd-web-s3, cd-web-vercel

Back to [SKILL.md](../SKILL.md). Next.js 16.4.x; research date 2026-10-30. Commands are representative, adapt to your environment. Reusable workflows: [build](./workflow-node-build.md), [S3 and CloudFront](./workflow-deploy-s3-cf.md), [Vercel](./workflow-deploy-vercel.md).

## `ci-web.yml` (pull_request, never deploys)

No secrets, no `id-token`, no cloud login: branch code runs during install and build. A pull request that needs a cloud read would use a PR-only read role, not a deployable environment; this pipeline needs none. Mode `vercel` runs checks only, so the same caller fits every target.

```yaml
name: ci-web
on: pull_request
permissions:
  contents: read
concurrency: { group: "ci-web-${{ github.ref }}", cancel-in-progress: true }
jobs:
  build:
    uses: ./.github/workflows/_node-build.yml
    with:
      mode: static            # static | standalone | vercel, matching next.config output
      retention-days: 3
```

Monorepos with path filters leave a required check Pending when the workflow is skipped; use job-level change detection and one always-running gate job as the only required check (medium confidence).

## `cd-web-s3.yml` (push to main, build once, promote the same artifact)

`NEXT_PUBLIC_*` values stay environment-agnostic in the artifact, so staging and prod receive byte-identical files; per-environment values come from a config file the client fetches per environment.

```yaml
name: cd-web-s3
on:
  push:
    branches: [main]
permissions:
  contents: read
concurrency: { group: cd-web-s3, cancel-in-progress: false }
jobs:
  build:
    uses: ./.github/workflows/_node-build.yml
    with:
      mode: static
      retention-days: 30
  deploy-staging:
    needs: build
    uses: ./.github/workflows/_deploy-s3-cf.yml
    permissions: { contents: read, id-token: write }
    with:
      environment: staging
      artifact-name: ${{ needs.build.outputs.artifact-name }}
      artifact-digest: ${{ needs.build.outputs.artifact-digest }}
  deploy-prod:
    needs: [build, deploy-staging]
    uses: ./.github/workflows/_deploy-s3-cf.yml
    permissions: { contents: read, id-token: write }
    with:
      environment: prod
      artifact-name: ${{ needs.build.outputs.artifact-name }}
      artifact-digest: ${{ needs.build.outputs.artifact-digest }}
```

Pro/Team: both environments carry a deployment branch rule `main`, and the human approval is the pull-request review before merge to protected `main`. Free private: skip `environments`, inline the deploy jobs without the `environment` line, trust `ref:refs/heads/main` in the role, and separate staging and prod by role or account. Calling a reusable workflow needs the caller job to grant the permissions the called job uses.

## `cd-web-vercel.yml` (push to main)

```yaml
name: cd-web-vercel
on:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  checks:
    uses: ./.github/workflows/_node-build.yml
    with:
      mode: vercel
  deploy:
    needs: checks
    uses: ./.github/workflows/_deploy-vercel.yml
    with:
      environment: prod                                    # omit on Free Option B
      vercel-cli-version: ${{ vars.VERCEL_CLI_VERSION }}   # pinned by the team, no default
    secrets:                                               # Free Option B only; Pro/Team: see the Vercel blueprint
      VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
      VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
      VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
```

Free Option A has no `cd-web-vercel.yml`: Vercel's Git integration deploys, and `ci-web.yml` with mode `vercel` runs the checks. The deploy path runs only on `push` to `main`, never on `pull_request`.

## Container caller

A standalone caller builds once with mode `standalone` and passes the artifact to the image workflow of `publishing-container-images-github-actions`; see [standalone container](./standalone-container.md).
