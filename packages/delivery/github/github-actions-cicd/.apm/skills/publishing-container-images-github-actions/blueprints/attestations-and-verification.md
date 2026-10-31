# Attestations, digest promotion and verification

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Workflow: [header and GHCR job](./workflow-image-publish.md).

Contents: [Default: BuildKit attestations](#default-buildkit-attestations), [Inspect without gh](#inspect-without-gh), [Upgrade path: artifact attestations](#upgrade-path-artifact-attestations), [Promotion by digest](#promotion-by-digest), [Secrets and provenance](#secrets-and-provenance).

## Default: BuildKit attestations

- On GitHub Actions, private repositories get provenance with `mode=min` automatically, public repositories `mode=max`.
- SBOM is not added automatically: set `sbom: true` on the build step (the workflow does it when `push` is true).
- Attestations attach to the pushed image as manifests in the image index and survive a push; `load: true` and the docker exporter add none, so never ship an image built that way.
- BuildKit attestations are unsigned; they cannot be checked with `gh attestation verify`.

```yaml
- id: push
  uses: docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc # v7.4.0
  with:
    push: true
    sbom: true
    # provenance: leave the default (mode=min on private repositories)
```

Sources: https://docs.docker.com/build/ci/github-actions/attestations/; https://docs.docker.com/build/metadata/attestations/ (read 2026-10-30)

## Inspect without gh

```bash
docker buildx imagetools inspect ghcr.io/acme/app@sha256:<digest> --format '{{json .Provenance}}'
docker buildx imagetools inspect ghcr.io/acme/app@sha256:<digest> --format '{{json .SBOM}}'
# Expected: a JSON document for each; null means the attestation was not attached
```

Source: https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/ (read 2026-10-30)

## Upgrade path: artifact attestations

Signed GitHub artifact attestations need a public repository or GitHub Enterprise Cloud for private and internal repositories (F33). On Team, Pro or Free private repositories they are not available; keep the BuildKit default.

`actions/attest` v4.2.2 (F33) replaces `actions/attest-build-provenance`, which is now a wrapper. Add it after the build step, with the permissions on that job only:

```yaml
# permissions: contents: read, packages: write, id-token: write, attestations: write, artifact-metadata: write
- uses: actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6 # v4.2.2
  with:
    subject-name: ghcr.io/acme/app
    subject-digest: ${{ steps.push.outputs.digest }}
    push-to-registry: true
```

```bash
gh attestation verify oci://ghcr.io/acme/app@sha256:<digest> -R acme/app
# Expected: exit 0 and a verified SLSA provenance v1 predicate; needs a registry login for oci://
```

- The README lists `artifact-metadata: write`; the GitHub how-to omits it. Which is authoritative is (medium confidence); follow the README.
- Artifact attestations alone give SLSA v1.0 Build Level 2; Level 3 needs the build in a reusable workflow.

Sources: https://github.com/actions/attest/blob/v4.2.2/README.md; https://github.com/actions/attest-build-provenance/blob/v4.2.2/README.md; https://cli.github.com/manual/gh_attestation_verify (read 2026-10-30)

## Promotion by digest

- Tag every pushed image with `type=sha,format=long`; semver tags come only from a semver Git tag.
- Deploy and promote `repo@sha256:<digest>`; never a moving tag. `latest` is generated automatically for tag and semver types, and branch and PR tags move on every push.
- One registry, the same digest in every environment, is the default (family rule 8). Copying to a per-environment registry with `docker buildx imagetools create` requires the sources to exist in the target registry, and blob copy plus digest preservation across registries are (unverified); verify digest equality after any copy.
- ECR immutable repositories reject re-pushing an existing tag with `ImageTagAlreadyExistsException`; environment tags need exclusion filters or no environment tags at all.
- GHCR and OCIR tag immutability settings are (unverified): the pages read do not describe them.

Sources: https://github.com/docker/metadata-action/blob/v6.2.0/README.md; https://docs.docker.com/reference/cli/docker/buildx/imagetools/create/; https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html (read 2026-10-30)

## Secrets and provenance

Build arguments are written into the default provenance attestation, so a secret passed as `build-args` is readable by anyone who can pull the image. Use the `secrets` input and a Dockerfile secret mount.

```yaml
secrets: |
  npm_token=${{ secrets.NPM_TOKEN }}
# Dockerfile: RUN --mount=type=secret,id=npm_token ...
```

Rotate any secret that was ever passed as a build argument. The Dockerfile mount syntax was not read from the Dockerfile reference and is (medium confidence).

Sources: https://docs.docker.com/build/ci/github-actions/attestations/; https://github.com/docker/build-push-action/blob/v7.4.0/README.md (read 2026-10-30)
