# Callers: ci-image, cd-image and digest hand-off

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Reusable workflow: [header and GHCR job](./workflow-image-publish.md), [ECR and OCIR jobs](./workflow-image-publish-ecr-ocir.md). Credential placement: [registry credentials](./registry-credentials.md).

Naming follows the family: `ci-<app>.yml` on pull_request, `cd-<app>.yml` on merge or release (rule 5).

## ci-image.yml (pull request, never pushes)

```yaml
# ./.github/workflows/ci-image.yml
name: ci-image
on: pull_request
permissions: {}
concurrency:
  group: ci-image-${{ github.ref }}
  cancel-in-progress: true
jobs:
  image:
    uses: ./.github/workflows/_image-publish.yml
    permissions: { contents: read }
    with:
      registry: ghcr
      image-name: acme/app
      push: false
```

- `push: false` routes to the `build` job of the reusable workflow: no login, no environment, no cache export, no `packages: write`; the build only proves the Dockerfile works.
- For a built artifact (Java jar, Next.js standalone) upload it in an earlier job and pass `artifact-name: <name>`; it is downloaded into `context` before the build.
- Never trigger this on `pull_request_target`; branch code would run with a write-capable token and secrets.
- If you keep all three registry jobs in the workflow, the caller may have to grant the union of their permissions; trim the unused jobs instead (see design notes).

Sources: https://github.com/docker/build-push-action/blob/v7.4.0/README.md; https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows (read 2026-10-30)

## cd-image.yml (merge to main, publishes and hands off the digest)

```yaml
# ./.github/workflows/cd-image.yml
name: cd-image
on:
  push:
    branches: [main]
permissions: {}
concurrency:
  group: cd-image-main
  cancel-in-progress: false
jobs:
  image:
    uses: ./.github/workflows/_image-publish.yml
    permissions: { contents: read, packages: write }
    with:
      registry: ghcr
      image-name: acme/app
      push: true
  deploy:
    needs: image
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    permissions: { contents: read }
    steps:
      - run: echo "Deploying ${IMAGE_REF}"
        env:
          IMAGE_REF: ${{ needs.image.outputs.image-ref }}
```

- `needs.image.outputs.image-ref` is `ghcr.io/acme/app@sha256:...`; every environment is deployed from that reference.
- Job outputs are limited to 1 MB per job and 50 MB per workflow run; a digest fits easily.
- Never rebuild for production: promote the same digest (family rule 8).

Source: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/pass-job-outputs (read 2026-10-30)

## ECR and OCIR variants of the publish call

```yaml
  image:  # ECR: Pro/Team private (default)
    uses: ./.github/workflows/_image-publish.yml
    permissions: { contents: read, id-token: write }
    with:
      registry: ecr
      image-name: acme/app
      push: true
      environment: prod-publish   # holds variable ECR_PUSH_ROLE_ARN, read inside the job
      aws-region: eu-west-1
```

```yaml
  image:  # OCIR: OCIR_USERNAME and OCIR_AUTH_TOKEN are secrets of the environment
    uses: ./.github/workflows/_image-publish.yml
    permissions: { contents: read }
    with:
      registry: ocir
      image-name: <tenancy-namespace>/app
      ocir-host: eu-frankfurt-1.ocir.io
      push: true
      environment: prod-publish
```

These variants are the `cd-image` caller (`push: true`); the PR caller never sets `environment`. On GitHub Free private repositories leave `environment` empty; whether an empty value is accepted is (unverified). See [registry credentials](./registry-credentials.md#free-private-variant) for the weaker layout.

## Feeding the digest to infrastructure

The deploy job passes `image-ref` to the infrastructure step as a variable, for example a Terraform `-var image_uri="${IMAGE_REF}"` set through `env:`. Provisioning, plan and apply belong to `automating-terraform-github-actions-v1-17`; Lambda or Functions deployment belongs to `deploying-aws-lambda` and the OCI skills. Do not copy their content here.

## Consumer check after publish

```bash
docker buildx imagetools inspect ghcr.io/acme/app@sha256:<digest>
# Expected: the manifest (or index) for exactly that digest, with attestation manifests when sbom is on
```

Source: https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/ (read 2026-10-30)
