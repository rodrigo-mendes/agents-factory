---
name: publishing-container-images-github-actions
description: "Builds and publishes container images from GitHub Actions to GHCR, Amazon ECR or OCIR: reusable _image-publish.yml, PR builds without push, digest hand-off, BuildKit provenance and SBOM. Use when writing or reviewing image build and push workflows. Not for Azure DevOps."
---

# Container images on GitHub Actions (GHCR, ECR, OCIR)

> Version lock: every claim applies to **docker/build-push-action v7.4.0** with setup-buildx v4.4.1, login-action v4.7.0 and metadata-action v6.2.0 on GitHub.com hosted runners. Research date **2026-10-30**.
> Claims tagged unverified or medium confidence were not fully confirmed against an official page; each tag maps to the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: the image build, publish, attest and digest hand-off only. How `workflow_call` works belongs to `composing-github-actions-pipelines`; cloud login trust belongs to `federating-github-actions-aws-oidc` and `federating-github-actions-oci`; image scanning belongs to `securing-supply-chain-github-actions`; SHA pinning and injection-safe scripting belong to `automating-github-repos-with-actions`.
> Provenance: the dated research file for this unit under the factory workspace; this skill never reads it at run time.

## Version Context

| Item | Value | Source (fetched 2026-10-30) |
|---|---|---|
| `docker/build-push-action` | v7.4.0 = `c3c9e263c25d99ce0380d002d59b67737d91b0dc` | https://github.com/docker/build-push-action/releases |
| `docker/setup-buildx-action` | v4.4.1 = `f87e5991a6d7451dcb8d9637bfbc97413f497069` | https://github.com/docker/setup-buildx-action/releases |
| `docker/login-action` | v4.7.0 = `81c6f93d4bc991e510b342a00b419b3bb4efc5c6` | https://github.com/docker/login-action/releases |
| `docker/metadata-action` | v6.2.0 = `dc802804100637a589fabce1cb79ff13a1411302` | https://github.com/docker/metadata-action/releases |
| `docker/setup-qemu-action` | v4.4.0 = `99012661954931238ded8c8b007157a8430204e1` | https://github.com/docker/setup-qemu-action/releases/tag/v4.4.0 |
| `aws-actions/amazon-ecr-login` | v2.1.7 = `03f1aad4c6c7ffd436567f42f9384779290529bd` | https://github.com/aws-actions/amazon-ecr-login/releases/tag/v2.1.7 |
| `aws-actions/configure-aws-credentials` | v6.3.0 = `e1253824e5c10ff9df46874f81ed3ec929e19cfd` | https://github.com/aws-actions/configure-aws-credentials/releases |
| `actions/attest` (upgrade path) | v4.2.2 = `1e69f48acb82d1966a394da916b4c1698aa569d6` | https://github.com/actions/attest/releases/tag/v4.2.2 |
| `oracle-actions/login-ocir` (option) | v1.3.0 = `d65011bf8c9300e51a98658388a0fb46d1ed54b1` | https://github.com/oracle-actions/login-ocir/releases/tag/v1.3.0 |
| `actions/checkout` | v7.0.1 = `3d3c42e5aac5ba805825da76410c181273ba90b1` | https://github.com/actions/checkout/releases |

**Version-lifetime risk** (as of 2026-10-30; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- The Docker actions need Actions Runner v2.327.1 or later (Node 24 default); older self-hosted runners cannot run them.
- `login-ocir` declares `node20`, which runners removed on 2026-09-23; this skill logs in to OCIR with `docker/login-action`.
- Release pages show no year; re-resolve SHAs with `git ls-remote` before every bump.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Reusable workflow: header and GHCR job](./blueprints/workflow-image-publish.md)
- [Reusable workflow: ECR and OCIR jobs](./blueprints/workflow-image-publish-ecr-ocir.md)
- [Callers: ci-image, cd-image, digest hand-off](./blueprints/workflow-callers.md)
- [Registry credentials per GitHub plan](./blueprints/registry-credentials.md)
- [Attestations, promotion and verification](./blueprints/attestations-and-verification.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [Verification Loop](#verification-loop)
- [External Resources](#external-resources)

## Blueprints & Guardrails

Shape: the reusable `_image-publish.yml` (inputs `context`, `file`, `registry` ghcr|ecr|ocir, `image-name`, `platforms`, `push`, optional `artifact-name`; outputs `digest`, `image-ref`) holds the build logic; PR runs (`push: false`) use a login-free `build` job, publishing jobs run only for `push: true`; callers `ci-image.yml` (pull_request, `push: false`) and `cd-image.yml` (merge, `push: true`) wire it. Cross-references by name only: `building-java-github-actions`, `building-nextjs-github-actions-v16-4`, `automating-terraform-github-actions-v1-17`, `limiting-blast-radius-github-actions-deploys`.

### ✅ Always Do

- **Run `docker/setup-buildx-action` before the build and keep the default `docker-container` driver**; it supports multi-platform builds and attestations ([setup-buildx README](https://github.com/docker/setup-buildx-action/blob/v4.4.1/README.md)).
- **Build pull requests with `push: false`**; `push` defaults to `false` ([build-push README](https://github.com/docker/build-push-action/blob/v7.4.0/README.md)).
- **Run no registry login in pull-request jobs of a deployable registry** (family decision; fork pull requests also get no secrets per [events reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)).
- **Tag every pushed image with `type=sha,format=long`**; default metadata tags are all moving tags ([metadata README](https://github.com/docker/metadata-action/blob/v6.2.0/README.md)).
- **Expose the `digest` output as a job output and deploy `repo@sha256:...`** ([pass job outputs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/pass-job-outputs)).
- **Authenticate to GHCR with `secrets.GITHUB_TOKEN`** ([login-action README](https://github.com/docker/login-action/blob/v4.7.0/README.md)).
- **Grant `packages: write` at job level, on the publishing job only** (family decision; permission scopes per [container registry docs](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)).
- **Log in to ECR with an OIDC role then `amazon-ecr-login`** ([amazon-ecr-login README](https://github.com/aws-actions/amazon-ecr-login/blob/v2.1.7/README.md)).
- **Keep `mask-password` at its default `true`** ([amazon-ecr-login README](https://github.com/aws-actions/amazon-ecr-login/blob/v2.1.7/README.md)).
- **Keep the default BuildKit provenance** (`mode=min` on private repositories) ([GitHub Actions attestations](https://docs.docker.com/build/ci/github-actions/attestations/)).
- **Set `sbom: true` on pushed images**; SBOMs are not added automatically ([GitHub Actions attestations](https://docs.docker.com/build/ci/github-actions/attestations/)).
- **Inspect attestations with `docker buildx imagetools inspect --format`** ([imagetools inspect](https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/)).
- **Pass build secrets through the `secrets` input**, because provenance records build arguments ([GitHub Actions attestations](https://docs.docker.com/build/ci/github-actions/attestations/)).
- **Set a `scope` per image on the `type=gha` cache** ([GitHub Actions cache](https://docs.docker.com/build/ci/github-actions/cache/)).

Code for each rule: [always-do patterns](./blueprints/always-do-patterns.md).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| GitHub plan | Pro or Team private (default: environments, branch policy, PR review) vs Free private (weaker: repository secrets, no branch policy) | "Which GitHub plan owns this private repository?" |
| Registry | GHCR or ECR (no stored static secret) vs OCIR (auth token, static) | "Which registry, and is OCIR required?" |
| OCIR login | `docker/login-action` (2 secrets, default) vs `login-ocir` (needs API key set; old release, medium confidence) | "Does this job already hold the OCI API key?" |
| Multi-arch | QEMU on one runner vs native runners vs single platform; recommendation per language is medium confidence; arm64 runner availability is unverified | "Which platforms are needed, and is build time critical?" |
| Promotion | One registry, same digest everywhere (default) vs copy to per-environment registries; digest preservation on copy is unverified | "Is account isolation mandated for registries?" |
| Attestations | BuildKit default (all plans, unsigned) vs `actions/attest` (public or Enterprise Cloud only) | "Is the repository public or on Enterprise Cloud?" |
| Tag immutability | ECR immutable tags (recommended) vs mutable; GHCR and OCIR settings are unverified | "May the repository be set to immutable tags?" |
| Build input | Git context (default, ignores earlier steps) vs path context after checkout or artifact download | "Does the image copy a jar or `.next` output from an earlier job?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Deploy or promote by `latest` or any moving tag ([metadata README](https://github.com/docker/metadata-action/blob/v6.2.0/README.md)) | Deploy `repo@sha256:<digest>` |
| Push or log in to a deployable registry from a `pull_request` run, or use `pull_request_target` to do it ([events reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)) | `push: false`, no login |
| Use a PAT for GHCR ([container registry docs](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)) or long-lived AWS keys for ECR ([OIDC reference](https://docs.github.com/en/actions/reference/security/oidc)) | `GITHUB_TOKEN`; OIDC role plus `amazon-ecr-login` |
| Set `mask-password: 'false'` on `amazon-ecr-login` ([README](https://github.com/aws-actions/amazon-ecr-login/blob/v2.1.7/README.md)) | Log in inside the pushing job, pass only the digest |
| Pass secrets as `build-args` ([attestations](https://docs.docker.com/build/ci/github-actions/attestations/)) | `secrets:` input with a Dockerfile secret mount |
| Write the gha cache from read-only runs or share the default scope ([cache](https://docs.docker.com/build/ci/github-actions/cache/)) | `cache-from` only, `scope` per image |
| Ship an image built with `load: true` ([attestations](https://docs.docker.com/build/metadata/attestations/)) | `push: true` with `sbom: true` |
| Start new work on `actions/attest-build-provenance` ([README](https://github.com/actions/attest-build-provenance/blob/v4.2.2/README.md)) | `actions/attest`, where the plan allows |

Examples with alternatives: [never-do patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Default provenance | `mode=min` private, `mode=max` public repositories; SBOM needs `sbom: true` | https://docs.docker.com/build/ci/github-actions/attestations/ |
| Job output limits | 1 MB per job, 50 MB per workflow run | https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax |
| GHCR limits | 10 GB per layer, 10 minute upload timeout | https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry |
| gha cache | 10 GB per repository, v2 API only | https://docs.docker.com/build/cache/backends/gha/ |
| OCIR username | `<tenancy-namespace>/<user>` plus auth token | https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm |
| Artifact attestations | private repositories need Enterprise Cloud | https://github.com/actions/attest/blob/v4.2.2/README.md |
| Reusable workflow location | the workflows folder, no subfolders | https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows |

## Verification Loop

Offline checks on the generated files (run from the repository root).

| Command | Expected |
|---|---|
| `grep -nE 'uses: [^ ]+@' .github/workflows/_image-publish.yml \| grep -vE '@[0-9a-f]{40}'` | no output (every action pinned by full SHA) |
| `grep -n -e ':latest' -e '@latest' .github/workflows/*.yml` | no output |
| `grep -n 'push: true' .github/workflows/ci-*.yml` | no output |
| `grep -n 'secrets: inherit' .github/workflows/*.yml` | no output |
| `actionlint .github/workflows/_image-publish.yml` | exit 0 (tool owned by `automating-github-repos-with-actions`; skip if not installed) |

After the first real push (needs registry access): `docker buildx imagetools inspect <image-ref>` prints the manifest for the digest in the `digest` output, with attestation manifests when `sbom` is on.

## External Resources

All fetched 2026-10-30.

- [docker/build-push-action README v7.4.0](https://github.com/docker/build-push-action/blob/v7.4.0/README.md)
- [Docker: GitHub Actions attestations](https://docs.docker.com/build/ci/github-actions/attestations/)
- [GitHub: Working with the Container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
