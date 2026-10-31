# Reusable workflow `_image-publish.yml` (header and GHCR job)

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. The file is `./.github/workflows/_image-publish.yml` (name fixed; workflows cannot sit in subfolders). The ECR and OCIR jobs go under the same `jobs:` key: [ECR and OCIR jobs](./workflow-image-publish-ecr-ocir.md). Callers: [callers](./workflow-callers.md).

Contents: [Design notes](#design-notes), [Header](#header), [Build job (PR)](#build-job-pr-push-false), [GHCR job](#ghcr-job).

## Design notes

- One publishing job per registry (`ghcr`, `ecr`, `ocir`), each gated by `inputs.push`, so that `id-token: write` exists only on the ECR job and `packages: write` only on the GHCR job (family rule 7). A separate `build` job (contents: read only, no login, no environment) serves every `push: false` run. Keep only the jobs for the registry you use: a called job that asks for more permissions than the caller grants is rejected, and whether skipped jobs count is (unverified).
- Secrets and the ECR role ARN are read inside the called job from its `environment` (`secrets.*`, `vars.ECR_PUSH_ROLE_ARN`); the workflow declares no secrets (family rule 18).
- Every job sets `timeout-minutes`.
- Every action is pinned by full SHA from the family facts (F3, F7, F10, F28-F32, F34); SHA pinning and injection rules: `automating-github-repos-with-actions`.
- Inputs reach shell steps only through `env:`, never inline in `run:`.
- `push: false` runs no login step and no cache export. A guard step fails any push attempt on a `pull_request` run.
- Pass `image-name` in lowercase; whether metadata-action lowercases it is (unverified).
- Outputs of the skipped jobs are empty strings, so the workflow outputs coalesce them with `||`.

## Header

```yaml
# ./.github/workflows/_image-publish.yml
name: _image-publish
on:
  workflow_call:
    inputs:
      context:      { type: string,  default: . }
      file:         { type: string,  default: ./Dockerfile }
      registry:     { type: string,  required: true }   # ghcr | ecr | ocir
      image-name:   { type: string,  required: true }   # lowercase, no host, no tag
      platforms:    { type: string,  default: linux/amd64 }
      push:         { type: boolean, default: false }
      environment:  { type: string,  default: '' }      # ecr, ocir push only; empty on Free private
      aws-region:   { type: string,  default: '' }      # ecr only
      ocir-host:    { type: string,  default: '' }      # ocir only, e.g. eu-frankfurt-1.ocir.io
      artifact-name: { type: string, default: '' }      # optional: built artifact (jar, .next) downloaded into context
    outputs:
      digest:    { value: '${{ jobs.ghcr.outputs.digest || jobs.ecr.outputs.digest || jobs.ocir.outputs.digest }}' }
      image-ref: { value: '${{ jobs.ghcr.outputs.image-ref || jobs.ecr.outputs.image-ref || jobs.ocir.outputs.image-ref }}' }
permissions: {}
jobs:
```

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (read 2026-10-30)

## Build job (PR, push false)

```yaml
  build:
    if: '!inputs.push'
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    permissions: { contents: read }
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - if: inputs.artifact-name != ''
        uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with:
          name: ${{ inputs.artifact-name }}
          path: ${{ inputs.context }}
      - if: contains(inputs.platforms, ',')
        uses: docker/setup-qemu-action@99012661954931238ded8c8b007157a8430204e1 # v4.4.0
      - uses: docker/setup-buildx-action@f87e5991a6d7451dcb8d9637bfbc97413f497069 # v4.4.1
      - uses: docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc # v7.4.0
        with:
          context: ${{ inputs.context }}
          file: ${{ inputs.file }}
          platforms: ${{ inputs.platforms }}
          push: false
          cache-from: type=gha,scope=${{ inputs.image-name }}
```

The build job pulls public base images only. It needs no registry, no environment and no `id-token`, so the ci-image caller grants `contents: read` alone. The same `download-artifact` step sits in every publishing job.

## GHCR job

```yaml
  ghcr:
    if: inputs.registry == 'ghcr' && inputs.push
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    permissions: { contents: read, packages: write }
    outputs:
      digest:    ${{ steps.push.outputs.digest }}
      image-ref: ${{ steps.ref.outputs.ref }}
    steps:
      - if: inputs.push && github.event_name == 'pull_request'
        run: echo "::error::push is not allowed on pull_request" && exit 1
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - if: inputs.artifact-name != ''
        uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with: { name: "${{ inputs.artifact-name }}", path: "${{ inputs.context }}" }
      - id: meta
        uses: docker/metadata-action@dc802804100637a589fabce1cb79ff13a1411302 # v6.2.0
        with:
          images: ghcr.io/${{ inputs.image-name }}
          tags: |
            type=sha,format=long
            type=semver,pattern={{version}}
            type=ref,event=pr
      - if: contains(inputs.platforms, ',')
        uses: docker/setup-qemu-action@99012661954931238ded8c8b007157a8430204e1 # v4.4.0
      - uses: docker/setup-buildx-action@f87e5991a6d7451dcb8d9637bfbc97413f497069 # v4.4.1
      - if: inputs.push
        uses: docker/login-action@81c6f93d4bc991e510b342a00b419b3bb4efc5c6 # v4.7.0
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - id: push
        uses: docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc # v7.4.0
        with:
          context: ${{ inputs.context }}
          file: ${{ inputs.file }}
          platforms: ${{ inputs.platforms }}
          push: ${{ inputs.push }}
          sbom: ${{ inputs.push }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          annotations: ${{ steps.meta.outputs.annotations }}
          cache-from: type=gha,scope=${{ inputs.image-name }}
          cache-to: ${{ inputs.push && format('type=gha,scope={0},mode=max', inputs.image-name) || '' }}
      - id: ref
        if: inputs.push
        run: echo "ref=${IMAGE}@${DIGEST}" >> "$GITHUB_OUTPUT"
        env:
          IMAGE: ghcr.io/${{ inputs.image-name }}
          DIGEST: ${{ steps.push.outputs.digest }}
```

Notes:
- The `cache-to` empty-string expression and a `scope` value containing `/` are (medium confidence): the pages read do not constrain scope syntax.
- With 2 or more platforms, whether `digest` is the index digest is (medium confidence); confirm with `docker buildx imagetools inspect` after the first push.
- `context: .` after checkout is path context; the default git context needs no checkout and ignores earlier steps.
- A build output from an earlier job (jar, `.next`) is handed over with the `artifact-name` input; the caller uploads it first and the download lands inside `context`.

Sources: https://github.com/docker/build-push-action/blob/v7.4.0/README.md; https://github.com/docker/metadata-action/blob/v6.2.0/README.md; https://docs.docker.com/build/ci/github-actions/cache/ (read 2026-10-30)
