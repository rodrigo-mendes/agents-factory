# Always-do patterns with code

Back to [SKILL.md](../SKILL.md). docker/build-push-action v7.4.0; research date 2026-10-30. Full workflows: [GHCR job](./workflow-image-publish.md), [ECR and OCIR jobs](./workflow-image-publish-ecr-ocir.md), [callers](./workflow-callers.md).

Contents: [Buildx and metadata](#buildx-and-metadata), [Pull requests](#pull-requests), [Digest hand-off](#digest-hand-off), [Registry login](#registry-login), [Attestations](#attestations), [Cache](#cache).

## Buildx and metadata

Keep the default `docker-container` driver; it supports multi-platform builds and attestations.

```yaml
- uses: docker/setup-buildx-action@f87e5991a6d7451dcb8d9637bfbc97413f497069 # v4.4.1
- id: meta
  uses: docker/metadata-action@dc802804100637a589fabce1cb79ff13a1411302 # v6.2.0
  with:
    images: ghcr.io/${{ inputs.image-name }}
    tags: |
      type=sha,format=long
      type=semver,pattern={{version}}
```

Default tags when `tags` is empty are only moving tags (schedule, branch, tag, PR), so the `type=sha` line must be explicit.
Sources: https://github.com/docker/setup-buildx-action/blob/v4.4.1/README.md; https://github.com/docker/metadata-action/blob/v6.2.0/README.md

## Pull requests

```yaml
- uses: docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc # v7.4.0
  with:
    push: ${{ inputs.push }}   # the ci caller passes false; no login step runs
```

`push` is shorthand for `--output=type=registry` and defaults to `false`. In fork pull requests the token is read-only and secrets are not passed.
Sources: https://github.com/docker/build-push-action/blob/v7.4.0/README.md; https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows

## Digest hand-off

```yaml
outputs:
  digest: ${{ steps.push.outputs.digest }}
# downstream job
env:
  IMAGE_REF: ghcr.io/acme/app@${{ needs.image.outputs.digest }}
```

Job outputs are read with `needs.<job_id>.outputs.<name>`; limits are 1 MB per job and 50 MB per run. GHCR documents pulling by the digest SHA value.
Sources: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/pass-job-outputs; https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry

## Registry login

```yaml
# GHCR: job permissions { contents: read, packages: write }
- uses: docker/login-action@81c6f93d4bc991e510b342a00b419b3bb4efc5c6 # v4.7.0
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

```yaml
# ECR: job permissions { contents: read, id-token: write }
- uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
  with: { role-to-assume: "${{ vars.ECR_PUSH_ROLE_ARN }}", aws-region: "${{ inputs.aws-region }}" }
- id: ecr
  uses: aws-actions/amazon-ecr-login@03f1aad4c6c7ffd436567f42f9384779290529bd # v2.1.7
```

`mask-password` defaults to `true`; leave it. Push to ECR needs `ecr:GetAuthorizationToken` plus the layer and image actions listed in the action README.
Sources: https://github.com/docker/login-action/blob/v4.7.0/README.md; https://github.com/aws-actions/amazon-ecr-login/blob/v2.1.7/README.md

## Attestations

```yaml
with:
  push: true
  sbom: true
```

```bash
docker buildx imagetools inspect ghcr.io/acme/app@sha256:<digest> --format '{{json .SBOM}}'
```

Details and the upgrade path: [attestations and verification](./attestations-and-verification.md).
Sources: https://docs.docker.com/build/ci/github-actions/attestations/; https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/

## Cache

```yaml
cache-from: type=gha,scope=my-app
cache-to: ${{ inputs.push && 'type=gha,scope=my-app,mode=max' || '' }}
```

The default scope is `buildkit`, so several images overwrite each other's cache unless each sets a scope. Read-only workflows keep `cache-from` and omit `cache-to`.
Sources: https://docs.docker.com/build/ci/github-actions/cache/; https://docs.docker.com/build/cache/backends/gha/
