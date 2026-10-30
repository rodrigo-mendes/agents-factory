# Never-do patterns with examples

Back to [SKILL.md](../SKILL.md). docker/build-push-action v7.4.0; research date 2026-10-30. Each pattern shows the wrong form and the alternative.

Contents: [N1](#n1-deploy-or-promote-by-latest), [N2](#n2-push-from-pull-request-runs), [N3](#n3-long-lived-registry-credentials), [N4](#n4-unmask-the-ecr-password), [N5](#n5-secrets-as-build-args), [N6](#n6-cache-export-from-read-only-contexts), [N7](#n7-ship-an-image-built-with-load), [N8](#n8-start-on-attest-build-provenance).

## N1. Deploy or promote by `latest`

metadata-action generates `latest` automatically for tag and semver types, and branch and PR tags move on every push, so production may run an image never tested earlier.

```yaml
# ❌ Wrong
image: ghcr.io/acme/app:latest
# ✅ Correct
image: ghcr.io/acme/app@${{ needs.image.outputs.digest }}
```

Sources: https://github.com/docker/metadata-action/blob/v6.2.0/README.md; https://github.com/docker/build-push-action/blob/v7.4.0/README.md

## N2. Push from pull-request runs

Fork and Dependabot pull requests get a read-only token and no secrets; `pull_request_target` workarounds carry a documented risk of cache poisoning and unintended write access.

```yaml
# ❌ Wrong
on: pull_request_target   # checkout of PR head, login, push: true
# ✅ Correct
on: pull_request          # push: false, no login
```

Sources: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows; https://docs.github.com/en/actions/reference/security/secure-use

## N3. Long-lived registry credentials

GitHub recommends `GITHUB_TOKEN` over a personal access token for GHCR; the family uses OIDC for AWS.

```yaml
# ❌ Wrong
password: ${{ secrets.GHCR_PAT }}
# ✅ Correct
password: ${{ secrets.GITHUB_TOKEN }}   # permissions: packages: write on this job
# ECR: configure-aws-credentials (OIDC) + amazon-ecr-login
```

Sources: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry; https://github.com/aws-actions/amazon-ecr-login/blob/v2.1.7/README.md

## N4. Unmask the ECR password

Masked values cannot cross jobs, but unmasked ones are logged when debug logging is on.

```yaml
# ❌ Wrong
- uses: aws-actions/amazon-ecr-login@03f1aad4c6c7ffd436567f42f9384779290529bd # v2.1.7
  with: { mask-password: 'false' }
# ✅ Correct: log in inside the pushing job; pass only the digest between jobs
- uses: aws-actions/amazon-ecr-login@03f1aad4c6c7ffd436567f42f9384779290529bd # v2.1.7
```

Source: https://github.com/aws-actions/amazon-ecr-login/blob/v2.1.7/README.md

## N5. Secrets as build-args

Default provenance contains build argument values, so the secret is exposed in the attestation; rotate anything exposed.

```yaml
# ❌ Wrong
build-args: |
  NPM_TOKEN=${{ secrets.NPM_TOKEN }}
# ✅ Correct
secrets: |
  npm_token=${{ secrets.NPM_TOKEN }}
```

The Dockerfile mount line `RUN --mount=type=secret,id=npm_token` is (medium confidence).
Sources: https://docs.docker.com/build/ci/github-actions/attestations/; https://github.com/docker/build-push-action/blob/v7.4.0/README.md

## N6. Cache export from read-only contexts

Export fails with "failed to reserve cache" when access is read-only, and `ignore-error=true` hides every export error; the default scope also lets images overwrite each other.

```yaml
# ❌ Wrong
cache-to: type=gha,mode=max,ignore-error=true
# ✅ Correct
cache-from: type=gha,scope=my-app
cache-to: ${{ inputs.push && 'type=gha,scope=my-app,mode=max' || '' }}
```

Sources: https://docs.docker.com/build/ci/github-actions/cache/; https://docs.docker.com/build/cache/backends/gha/

## N7. Ship an image built with `load`

The docker exporter and `load: true` add no attestations, and the local image store cannot load images that have them.

```yaml
# ❌ Wrong
load: true   # then docker push
# ✅ Correct
push: true
sbom: true
```

Sources: https://docs.docker.com/build/ci/github-actions/attestations/; https://docs.docker.com/build/metadata/attestations/

## N8. Start on `attest-build-provenance`

Version 4 is a wrapper on `actions/attest`, and new implementations should use `actions/attest`.

```yaml
# ❌ Wrong
- uses: actions/attest-build-provenance@<sha> # v4.2.2
# ✅ Correct (public repositories or Enterprise Cloud only)
- uses: actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6 # v4.2.2
```

Source: https://github.com/actions/attest-build-provenance/blob/v4.2.2/README.md
