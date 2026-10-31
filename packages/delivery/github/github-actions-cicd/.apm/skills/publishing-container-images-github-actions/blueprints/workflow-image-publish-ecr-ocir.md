# Reusable workflow `_image-publish.yml` (ECR and OCIR jobs)

Back to [SKILL.md](../SKILL.md). Continuation of [header and GHCR job](./workflow-image-publish.md): append both jobs under `jobs:` in `./.github/workflows/_image-publish.yml`. Research date 2026-10-30. Credential placement per plan: [registry credentials](./registry-credentials.md).

Contents: [ECR job](#ecr-job), [OCIR job](#ocir-job), [OCIR login alternative](#ocir-login-alternative).

## ECR job

Keyless: OIDC role (F3), then `amazon-ecr-login` (F32). The role trust policy (`sub` format, F26) belongs to `federating-github-actions-aws-oidc`.

```yaml
  ecr:
    if: inputs.registry == 'ecr' && inputs.push
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    environment: ${{ inputs.environment }}
    permissions: { contents: read, id-token: write }
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
      - uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
        with:
          role-to-assume: ${{ vars.ECR_PUSH_ROLE_ARN }}
          aws-region: ${{ inputs.aws-region }}
      - id: ecr
        uses: aws-actions/amazon-ecr-login@03f1aad4c6c7ffd436567f42f9384779290529bd # v2.1.7
      - id: meta
        uses: docker/metadata-action@dc802804100637a589fabce1cb79ff13a1411302 # v6.2.0
        with:
          images: ${{ format('{0}/{1}', steps.ecr.outputs.registry, inputs.image-name) }}
          tags: |
            type=sha,format=long
            type=semver,pattern={{version}}
      - if: contains(inputs.platforms, ',')
        uses: docker/setup-qemu-action@99012661954931238ded8c8b007157a8430204e1 # v4.4.0
      - uses: docker/setup-buildx-action@f87e5991a6d7451dcb8d9637bfbc97413f497069 # v4.4.1
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
          cache-from: type=gha,scope=${{ inputs.image-name }}
          cache-to: ${{ inputs.push && format('type=gha,scope={0},mode=max', inputs.image-name) || '' }}
      - id: ref
        if: inputs.push
        run: echo "ref=${REGISTRY}/${IMAGE}@${DIGEST}" >> "$GITHUB_OUTPUT"
        env:
          REGISTRY: ${{ steps.ecr.outputs.registry }}
          IMAGE: ${{ inputs.image-name }}
          DIGEST: ${{ steps.push.outputs.digest }}
```

- `mask-password` stays at its default `true`; a masked password cannot cross jobs, so log in inside the pushing job.
- The role ARN is the environment variable `ECR_PUSH_ROLE_ARN`, read inside the job; the job runs only when `push` is true, so a pull request never binds the environment or requests an OIDC token.
- A pull request that must pull a private base image from ECR needs its own read-role job with a separate environment, added to your copy (family rule 13).
- Turn on ECR tag immutability for the repository so `sha-` tags cannot be overwritten.

Sources: https://github.com/aws-actions/amazon-ecr-login/blob/v2.1.7/README.md; https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html (read 2026-10-30)

## OCIR job

An OIDC login for OCIR is (unverified): no page read documents it. Username `<tenancy-namespace>/<user>` and an auth token come in as secrets. `image-name` is the repository path after the host, for example `<tenancy-namespace>/app`.

```yaml
  ocir:
    if: inputs.registry == 'ocir' && inputs.push
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    environment: ${{ inputs.environment }}
    permissions: { contents: read }
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
          images: ${{ inputs.ocir-host }}/${{ inputs.image-name }}
          tags: |
            type=sha,format=long
            type=semver,pattern={{version}}
      - uses: docker/setup-buildx-action@f87e5991a6d7451dcb8d9637bfbc97413f497069 # v4.4.1
      - uses: docker/login-action@81c6f93d4bc991e510b342a00b419b3bb4efc5c6 # v4.7.0
        with:
          registry: ${{ inputs.ocir-host }}
          username: ${{ secrets.OCIR_USERNAME }}
          password: ${{ secrets.OCIR_AUTH_TOKEN }}
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
      - id: ref
        if: inputs.push
        run: echo "ref=${HOST}/${IMAGE}@${DIGEST}" >> "$GITHUB_OUTPUT"
        env:
          HOST: ${{ inputs.ocir-host }}
          IMAGE: ${{ inputs.image-name }}
          DIGEST: ${{ steps.push.outputs.digest }}
```

For multi-platform OCIR builds add the QEMU step from the GHCR job. Both secrets are environment secrets of `environment`, read inside this job; the caller passes nothing (no `secrets:` block, no `inherit`). The job runs only for `push: true`.

Sources: https://github.com/docker/login-action/blob/v4.7.0/README.md; https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm (read 2026-10-30)

## OCIR login alternative

`oracle-actions/login-ocir` v1.3.0 (F34, `oracle-actions/login-ocir@d65011bf8c9300e51a98658388a0fb46d1ed54b1`) derives the endpoint and username but needs the whole OCI API key set (`OCI_CLI_USER`, `OCI_CLI_TENANCY`, `OCI_CLI_FINGERPRINT`, `OCI_CLI_KEY_CONTENT`, `OCI_CLI_REGION`) plus `auth_token`. It declares `node20`, and runners removed Node20 on 2026-09-23; the changelog does not say what happens to such actions (F38). Prefer the `docker/login-action` step above; use login-ocir only when the same job already holds the API key.

Sources: https://github.com/oracle-actions/login-ocir/blob/v1.3.0/README.md; https://github.blog/changelog/2026-09-23-deprecation-of-node-20-on-github-actions-runners/ (read 2026-10-30)
