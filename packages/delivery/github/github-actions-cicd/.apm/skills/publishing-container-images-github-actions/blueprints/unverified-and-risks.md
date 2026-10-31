# Unverified and risks register

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Tags are plain parentheses: (unverified) and (medium confidence).

Contents: [Version-lifetime risk](#version-lifetime-risk), [Unverified](#unverified-8), [Irresolvable](#irresolvable-0), [Medium confidence](#medium-confidence-8), [Coverage limits](#coverage-limits-5), [Tag to register mapping](#tag-to-register-mapping), [Source Bibliography](#source-bibliography).

## Version-lifetime risk

As of 2026-10-30.

- The Docker actions moved to new majors in March (build-push v7, setup-buildx v4, login v4, metadata v6, setup-qemu v4); all need Actions Runner v2.327.1 or later because of the Node 24 default. Self-hosted runners older than that cannot run them. Source: https://github.com/docker/build-push-action/releases
- Release pages show day and month only; the year of each tag is inferred by order, not read. Re-resolve every SHA with `git ls-remote` before bumping. Source: https://github.com/docker/login-action/releases
- `oracle-actions/login-ocir` v1.3.0 declares `node20`, and runners removed Node20 on 2026-09-23; the changelog does not say what happens to such actions (F38). This skill uses `docker/login-action` for OCIR for that reason. Source: https://github.blog/changelog/2026-09-23-deprecation-of-node-20-on-github-actions-runners/
- The `type=gha` cache supports only the v2 cache API (Buildx 0.21.0 or later, BuildKit 0.20.0 or later); the v1 API is shut down. Source: https://docs.docker.com/build/cache/backends/gha/
- GHCR storage and bandwidth are "currently free" with at least one month's notice before a change; private quotas are shared with Actions artifacts. Source: https://docs.github.com/en/billing/concepts/product-billing/github-packages
- Artifact attestations on private repositories need GitHub Enterprise Cloud; a plan change on GitHub's side alters the upgrade path. Source: https://github.com/actions/attest/blob/v4.2.2/README.md

## Unverified (8)

| ID | Claim | Impact | Workaround |
|---|---|---|---|
| U1 | Whether job-level permissions of skipped jobs in a called workflow count when the caller's permissions are validated | startup failure when the caller grants less than the union | keep only the job of the registry in use |
| U2 | A job-level `environment` set to an empty string is accepted | Free private callers may fail at parse time | split the job or omit the key in the copy for Free |
| U3 | `docker buildx imagetools create` copies blobs between registries and preserves the digest | promotion to a second registry may change the digest | deploy from one registry; compare digests after any copy |
| U4 | GHCR and OCIR tag immutability settings | `sha-` tags could be overwritten | deploy by digest, which cannot be overwritten |
| U5 | Availability and pricing of arm64 hosted runners for private repositories; pinning of `docker/github-builder` | native multi-arch design unclear | QEMU on one runner, or single platform |
| U6 | OIDC `sub` formats and environment scoping on Free private repositories | trust policy for the Free variant | owned by `federating-github-actions-aws-oidc` |
| U7 | OIDC or token-exchange login to OCIR (F20 and F21 cover OCI API calls only) | static auth token stays | owned by `federating-github-actions-oci` |
| U8 | metadata-action lowercases an `images` value that has capitals | GHCR rejects uppercase names | pass `image-name` in lowercase |

## Irresolvable (0)

None.

## Medium confidence (8)

| ID | Claim | Why moderate | Check |
|---|---|---|---|
| M1 | A `scope` containing `/` and an empty-string `cache-to` expression work as written | scope syntax not documented on the pages read | run the workflow once with `push: true` |
| M2 | `digest` is the index digest when `platforms` has 2 or more entries | inferred from the multi-platform docs | `docker buildx imagetools inspect` after the first push |
| M3 | `artifact-metadata: write` is required (README) although the GitHub how-to omits it | two official pages disagree | follow the README; relevant only on public or Enterprise Cloud |
| M4 | `login-ocir` v1.3.0 is an old release that is still the latest | the year is not shown on the release page | check the releases page before use |
| M5 | A push-only OCI user plus a branch-protected workflow mitigates repository secrets on Free private | inference, family rule 10 cannot be met | ask the user to accept the risk |
| M6 | Java images suit QEMU multi-arch; Next.js images with native dependencies prefer native runners or one platform | inference from the QEMU slowdown statement | time a build on both |
| M7 | On Free private, the ECR role ARN may sit in a repository variable or a literal | scoping on Free was not read in full | ask the user |
| M8 | Dockerfile `RUN --mount=type=secret,id=...` syntax | Dockerfile reference not read | read the Dockerfile reference before use |

## Coverage limits (5)

| ID | Limit |
|---|---|
| L1 | The workflow-syntax page was read for characters 0-200000 of 235839 |
| L2 | Docker documentation pages carry no publication date |
| L3 | GitHub doc examples show stale action majors (checkout v4, login v3, attest README using build-push v5); only the facts-file pins are used |
| L4 | The caller's GitHub plan is unknown; the skill asks first |
| L5 | `docker/github-builder`, `oracle-actions/login-ocir` runtime behavior on current runners and attestation verification on a live Team repository were not run |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | workflow-image-publish.md design notes (skipped jobs) | U1 |
| (unverified) | workflow-callers.md OCIR and ECR variants (empty environment) | U2 |
| (unverified) | attestations-and-verification.md promotion (cross-registry copy); unverified (prose form) in SKILL.md Ask First (promotion) | U3 |
| (unverified) | attestations-and-verification.md promotion (immutability); unverified (prose form) in SKILL.md Ask First (tag immutability) | U4 |
| unverified (prose form) | SKILL.md Ask First (multi-arch) | U5 |
| (unverified) | registry-credentials.md Free private variant | U6 |
| (unverified) | workflow-image-publish-ecr-ocir.md OCIR job; registry-credentials.md OCIR credentials | U7 |
| (unverified) | workflow-image-publish.md design notes (lowercase) | U8 |
| (medium confidence) | workflow-image-publish.md notes (cache scope) | M1 |
| (medium confidence) | workflow-image-publish.md notes (digest) | M2 |
| (medium confidence) | attestations-and-verification.md upgrade path | M3 |
| medium confidence (prose form) | SKILL.md Ask First (OCIR login) | M4 |
| (medium confidence) | registry-credentials.md Free private variant (OCIR mitigation) | M5 |
| medium confidence (prose form) | SKILL.md Ask First (multi-arch) | M6 |
| (medium confidence) | registry-credentials.md Free private variant (ECR) | M7 |
| (medium confidence) | attestations-and-verification.md secrets; never-do-patterns.md N5 | M8 |

## Source Bibliography

All fetched 2026-10-30. Docker documentation pages carry no date.

**github.com (actions and releases)**
- https://github.com/docker/build-push-action/blob/v7.4.0/README.md
- https://github.com/docker/setup-buildx-action/blob/v4.4.1/README.md
- https://github.com/docker/login-action/blob/v4.7.0/README.md
- https://github.com/docker/metadata-action/blob/v6.2.0/README.md
- https://github.com/docker/setup-qemu-action/releases/tag/v4.4.0
- https://github.com/aws-actions/amazon-ecr-login/blob/v2.1.7/README.md
- https://github.com/actions/attest/blob/v4.2.2/README.md
- https://github.com/actions/attest-build-provenance/blob/v4.2.2/README.md
- https://github.com/oracle-actions/login-ocir/blob/v1.3.0/README.md
- SHA verification: `git ls-remote https://github.com/<owner>/<repo> refs/tags/<tag>`

**docs.docker.com**
- https://docs.docker.com/build/ci/github-actions/cache/
- https://docs.docker.com/build/cache/backends/gha/
- https://docs.docker.com/build/ci/github-actions/attestations/
- https://docs.docker.com/build/metadata/attestations/
- https://docs.docker.com/build/ci/github-actions/multi-platform/
- https://docs.docker.com/build/building/multi-platform/
- https://docs.docker.com/reference/cli/docker/buildx/imagetools/create/
- https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/

**docs.github.com and GitHub**
- https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
- https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images
- https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations
- https://docs.github.com/en/actions/reference/security/secure-use
- https://docs.github.com/en/actions/reference/security/oidc
- https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/pass-job-outputs
- https://docs.github.com/en/billing/concepts/product-billing/github-packages
- https://docs.github.com/en/get-started/learning-about-github/githubs-plans
- https://github.blog/changelog/2026-09-23-deprecation-of-node-20-on-github-actions-runners/
- https://cli.github.com/manual/gh_attestation_verify

**Cloud vendors**
- https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html
- https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm
