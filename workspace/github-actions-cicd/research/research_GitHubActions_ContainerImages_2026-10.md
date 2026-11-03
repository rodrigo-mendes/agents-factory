# Research: Building and publishing container images from GitHub Actions (docker/build-push-action v7.4.0, setup-buildx v4.4.1, login-action v4.7.0, metadata-action v6.2.0; GHCR, Amazon ECR, OCIR)

> Unit: `publishing-container-images-github-actions`. Source item: "Java image + Next.js container".
> Spec: `researching-technical-frameworks` (default depth = exhaustive, MAX_ITERATIONS = 5).
> Brief: `workspace/github-actions-cicd/execution-1/briefs/P4-research-publishing-container-images-github-actions.md`.
> Every page was read on 2026-10-30. Family facts F1-F24 and family rules 1-16
> (`workspace/github-actions-cicd/_family_facts.md`, `_family_rules.md`) are applied as given.
> This document is provenance for the skill author; the shipped skill must not read it (brief constraint).
>
> Section-order note: the brief requires the file to END with `## Source Bibliography`, so that
> section moves from its template position to the end, after `## Pages read` and `## Facts requested`.
> All 15 template sections are present.
>
> Version note: only `docker/build-push-action` v7.4.0 (F7), `actions/checkout` v7.0.1 (F10),
> `aws-actions/configure-aws-credentials` v6.3.0 (F3) and upload/download-artifact (F23/F24) are in the
> facts file. Every other action tag below was resolved from its GitHub release page and is listed
> under `## Facts requested` (FR1-FR7). Examples use the placeholder `<FRn-sha>` for those until the
> orchestrator adds them to the facts file (rule 4, rule 11). Doc examples show stale majors
> (`actions/checkout@v4`, `docker/login-action@v3`, `docker/build-push-action@v5.0.0` in the
> actions/attest README; `aws-actions/configure-aws-credentials@v4` in the amazon-ecr-login README;
> unlabeled SHAs in the GitHub publish-docker-images tutorial). None of them is used (brief lesson 1).

## Metadata

```yaml
Full_Name: Container image build, publish, attest and digest hand-off from GitHub Actions (GitHub.com hosted runners)
Target_Version: docker/build-push-action v7.4.0 (F7, release "15 Sep")
Companion_Actions (resolved 2026-10-30 from release pages, see Facts requested):
  - docker/setup-buildx-action v4.4.1 ("16 Sep")
  - docker/login-action v4.7.0 ("23 Oct")
  - docker/metadata-action v6.2.0 ("02 Jul")
  - docker/setup-qemu-action v4.4.0 ("15 Sep")
  - aws-actions/amazon-ecr-login v2.1.7 ("19 Aug")
  - actions/attest v4.2.2 ("04 Aug"); actions/attest-build-provenance v4.2.2 ("06 Aug", now a wrapper)
  - oracle-actions/login-ocir v1.3.0 ("18 Jun"; year not shown, old but current latest; F22)
Release_Dates: GitHub release pages show day/month only; years are not shown (2026 inferred by order for the docker/* v4/v6/v7 lines, whose majors all shipped "04/05 Mar")
Support_Status: all listed tags are marked "Latest" on their release pages on 2026-10-30
Primary_Docs:
  - https://github.com/docker/build-push-action/blob/v7.4.0/README.md
  - https://docs.docker.com/build/ci/github-actions/
  - https://github.com/actions/attest/blob/v4.2.2/README.md
  - https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
  - https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html
  - https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm
Integration_Partners: GHCR (GITHUB_TOKEN), Amazon ECR (OIDC via F3 + amazon-ecr-login), OCIR (auth token; login-ocir F22 or docker/login-action), BuildKit attestations, GitHub artifact attestations, gh CLI `attestation verify`, Terraform (digest as input)
Neighbour_Units (by name only, rule 12): building-java-github-actions, building-nextjs-github-actions, federating-github-actions-aws-oidc, federating-github-actions-oci, securing-supply-chain-github-actions, composing-github-actions-pipelines, automating-github-repos-with-actions (github-core: SHA pinning, injection)
Target_Plan: GitHub Team / Pro / Free with PRIVATE repositories (rule 16, G2 DEC-011)
Research_Date: 2026-10-30
Domain_Complexity: Complex (registry credentials, signing/attestation, multi-registry, promotion)
Research_Depth: exhaustive (default)
Max_Iterations: 5
Gap_Loop_Ran: true
Iterations_Used: 3 of 5
Triangulated_Count: 8
Unverified_Count: 8
Irresolvable_Count: 0
Research_Quality_Score: 86%   # ~70 claims, 8 unverified, 7 medium confidence
```

## Executive Summary

The image pipeline on GitHub Actions has four building blocks, all published by Docker:
`docker/setup-buildx-action` creates a BuildKit builder (default driver `docker-container`, needed for
multi-platform builds and cache export); `docker/login-action` authenticates to the registry and logs
out at the end of the job (`logout: true` default); `docker/metadata-action` turns Git context into tags,
OCI labels and annotations; and `docker/build-push-action` v7.4.0 (F7) builds and, only when
`push: true`, pushes, returning `imageid`, `digest` and `metadata` outputs
(https://github.com/docker/build-push-action/blob/v7.4.0/README.md, read 2026-10-30). All four moved to
new majors on 04/05 Mar (build-push v7, setup-buildx v4, login v4, metadata v6, setup-qemu v4) whose
common change is "Node 24 as default runtime (requires Actions Runner v2.327.1 or later)". build-push v7
also removed the deprecated `DOCKER_BUILD_NO_SUMMARY` and `DOCKER_BUILD_EXPORT_RETENTION_DAYS` env vars,
and setup-buildx v4 removed "deprecated inputs/outputs" (release pages, read 2026-10-30). v7.4.0 itself
fixes "Prevent workflow command injection in metadata logs" (#1617), a reason to be on it.

Registry login differs by registry. GHCR uses the job's `GITHUB_TOKEN` with `packages: write`, so no
stored secret is needed on any plan (login-action v4.7.0 README; GitHub Container registry docs). ECR is
keyless: `aws-actions/configure-aws-credentials` (F3) assumes a role through OIDC and
`aws-actions/amazon-ecr-login` v2.1.7 exchanges it for a Docker login, with `mask-password` defaulting to
`true` (amazon-ecr-login v2.1.7 README). OCIR has no OIDC path in the docs read: it needs a username of the
form `<tenancy-namespace>/<username>` and an auth token, either through `docker/login-action` (username +
token) or `oracle-actions/login-ocir` (OCI API key env vars + token) (login-action README; Oracle OCIR
docs; login-ocir v1.3.0 README). On the target plans this matters: environment secrets exist for private
repos only on Pro/Team (and Enterprise), not on Free; deployment branch policies the same; required
reviewers and wait timers only for public repos on Free/Pro/Team
(https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).

Three critical patterns: (1) pull requests build with `push: false` and never log in to a deployable
registry; (2) tag with immutable `sha-<short>` and semver tags from metadata-action, then deploy and promote
by the `digest` output (`repo@sha256:...`), never by `latest` (rule 8); (3) keep BuildKit provenance
(added by default, `mode=min` on private repos, `mode=max` on public) and add `sbom: true`, but note that
GitHub artifact attestations (`actions/attest`, verified with `gh attestation verify`) require GitHub
Enterprise Cloud for private/internal repositories, so on Team/Pro/Free private repos they are an upgrade
path, not a default (actions/attest v4.2.2 README; attest-build-provenance v4.2.2 README).

## Architectural Guardrails

> Confidence legend: High = official page read in full; Triangulated = 2+ independent official
> sources | (medium confidence) = one source, partly read, or inferred | (unverified) = no official
> confirmation found. SHAs: F7 build-push-action, F10 checkout, F3 configure-aws-credentials; FR1-FR7
> placeholders for the rest (see Facts requested).

### ✅ Mandatory Patterns

**A1. Set up Buildx before building; keep the default `docker-container` driver**
> Confidence: High | [✓✓ Triangulated | setup-buildx v4.4.1 README + Docker multi-platform docs]
- Why: "By default, the `docker-container` driver will be used" to build multi-platform images and export cache using a BuildKit container. The docker-container driver "supports multi-platform builds", and attestations are supported "regardless of image store" on that driver.
- Code:
  ```yaml
  # docker/setup-buildx-action v4.4.1 (FR1)
  - uses: docker/setup-buildx-action@<FR1-sha> # v4.4.1
  ```
- Source: https://github.com/docker/setup-buildx-action/blob/v4.4.1/README.md; https://docs.docker.com/build/building/multi-platform/; https://docs.docker.com/build/metadata/attestations/ (all 2026-10-30)

**A2. Generate tags and labels with `docker/metadata-action` and feed both outputs to build-push**
> Confidence: High | [✓✓ Triangulated | metadata-action v6.2.0 README + Docker attestations example]
- Why: outputs `tags`, `labels`, `annotations`, `version`, `json`; the Docker CI examples pass `tags: ${{ steps.meta.outputs.tags }}`. Generated OCI labels include `org.opencontainers.image.source`, `revision`, `created`, `version`. GHCR uses `org.opencontainers.image.source` ("The URL of the repository associated with the package") to connect the package to the repository.
- Code:
  ```yaml
  # docker/metadata-action v6.2.0 (FR3)
  - id: meta
    uses: docker/metadata-action@<FR3-sha> # v6.2.0
    with:
      images: ghcr.io/${{ github.repository }}
      tags: |
        type=sha,format=long
        type=semver,pattern={{version}}
        type=ref,event=branch
        type=ref,event=pr
  ```
- Source: https://github.com/docker/metadata-action/blob/v6.2.0/README.md; https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry (2026-10-30)

**A3. Tag every pushed image with an immutable commit tag (`type=sha`); semver tags on release tags**
> Confidence: High (metadata-action v6.2.0 README)
- Why: `type=sha` outputs "Git short commit (or long if specified) as Docker tag like `sha-860c190`" (prefix `sha-`, format `short` default). `type=semver` needs "a valid semver Git tag on a push tag event". Default tags when `tags` is empty are only `schedule`, `ref,event=branch`, `ref,event=tag`, `ref,event=pr`, which are all moving tags, so the sha entry must be explicit.
- Code: see A2.
- Source: https://github.com/docker/metadata-action/blob/v6.2.0/README.md (2026-10-30)

**A4. Hand the `digest` output to downstream jobs as a job output and deploy `image@digest`**
> Confidence: High | [✓✓ Triangulated | build-push v7.4.0 README + workflow-syntax jobs.<id>.outputs + GHCR pull-by-digest]
- Why: build-push outputs `digest` ("Image digest"); job outputs are defined with `jobs.<job_id>.outputs` and read with `needs.<job_id>.outputs.<name>`; limits "1 MB per job", "50 MB" per run; "Outputs containing secrets are redacted on the runner and not sent" (a digest is not a secret, so it passes). GHCR documents pulling "by the `digest` SHA value" (`ghcr.io/NAMESPACE/IMAGE_NAME@sha256:...`).
- Code:
  ```yaml
  jobs:
    image:
      outputs:
        digest: ${{ steps.push.outputs.digest }}
      steps:
        - id: push
          uses: docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc # v7.4.0
          with:
            push: true
            tags: ${{ steps.meta.outputs.tags }}
    deploy:
      needs: image
      steps:
        - run: echo "IMAGE=ghcr.io/${GITHUB_REPOSITORY}@${DIGEST}"
          env:
            DIGEST: ${{ needs.image.outputs.digest }}
  ```
- Source: https://github.com/docker/build-push-action/blob/v7.4.0/README.md; https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (characters 100000-200000 of 235839 read for outputs); https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/pass-job-outputs (2026-10-30)

**A5. GHCR: log in with `GITHUB_TOKEN` and grant `packages: write` only to the publishing job**
> Confidence: High | [✓✓ Triangulated | login-action v4.7.0 README + GitHub Container registry docs + publish-docker-images tutorial]
- Why: "To authenticate to the GitHub Container Registry, use the GITHUB_TOKEN secret" (login-action). GitHub: if a workflow uses a PAT, "we highly recommend you update your workflow to use the `GITHUB_TOKEN`". The GitHub tutorial grants `contents: read` + `packages: write` (plus attestation permissions when attesting). Data transfer from Actions using `GITHUB_TOKEN` "does not count against the usage", and Container registry storage and bandwidth is "currently free".
- Code:
  ```yaml
  # docker/login-action v4.7.0 (FR2)
  permissions:
    contents: read
    packages: write
  steps:
    - uses: docker/login-action@<FR2-sha> # v4.7.0
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
  ```
- Source: https://github.com/docker/login-action/blob/v4.7.0/README.md; https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry; https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images; https://docs.github.com/en/billing/concepts/product-billing/github-packages (2026-10-30)

**A6. ECR: assume an IAM role by OIDC (F3), then `aws-actions/amazon-ecr-login`; keep `mask-password` at its default `true`**
> Confidence: High | [✓✓ Triangulated | amazon-ecr-login v2.1.7 README + login-action v4.7.0 README (configure-aws-credentials "in combination")]
- Why: the amazon-ecr-login README shows configure-aws-credentials with `role-to-assume` followed by `amazon-ecr-login`; "the default value of the `mask-password` input has changed from `false` to `true`"; "Masked values cannot be passed to separate jobs", and setting it `'false'` "will log your Docker password output if" debug logging is enabled. Output `registry` gives the registry host. Push needs `ecr:GetAuthorizationToken` (Resource `*`) plus `BatchGetImage, BatchCheckLayerAvailability, CompleteLayerUpload, GetDownloadUrlForLayer, InitiateLayerUpload, PutImage, UploadLayerPart`.
- Code:
  ```yaml
  permissions:
    contents: read
    id-token: write          # only on this job (rule 7)
  steps:
    - uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
      with:
        role-to-assume: ${{ vars.ECR_PUSH_ROLE_ARN }}
        aws-region: eu-west-1
    - id: ecr
      uses: aws-actions/amazon-ecr-login@<FR5-sha> # v2.1.7
    # tags: ${{ steps.ecr.outputs.registry }}/my-app:sha-...
  ```
- Source: https://github.com/aws-actions/amazon-ecr-login/blob/v2.1.7/README.md; https://github.com/docker/login-action/blob/v4.7.0/README.md (2026-10-30). Trust-policy `sub` scoping is owned by `federating-github-actions-aws-oidc`.

**A7. Pull requests build without pushing and without registry write credentials**
> Confidence: High | [✓✓ Triangulated | build-push v7.4.0 README (`push` default `false`) + events-that-trigger-workflows (fork PR token read-only, no secrets)]
- Why: `push` "is a shorthand for `--output=type=registry`" with default `false`. In fork PRs "The `GITHUB_TOKEN` has read-only permissions" and "secrets are not passed to the runner"; Dependabot PRs are treated the same. Family rules 7 and 13: no cloud write from PR jobs; any login a PR job needs (e.g. pulling a private base image from ECR) uses a PR-only read role.
- Code:
  ```yaml
  - uses: docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc # v7.4.0
    with:
      context: .
      push: ${{ github.event_name != 'pull_request' }}
      tags: ${{ steps.meta.outputs.tags }}
      labels: ${{ steps.meta.outputs.labels }}
  ```
- Source: https://github.com/docker/build-push-action/blob/v7.4.0/README.md; https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows (2026-10-30)

**A8. Use the GitHub Actions cache backend (`type=gha`) with an explicit `scope` per image**
> Confidence: High | [✓✓ Triangulated | Docker GitHub Actions cache page + gha backend reference]
- Why: `cache-from: type=gha` / `cache-to: type=gha,mode=max` is the documented pattern; `mode` defaults to `min`; `scope` defaults to `buildkit`, and "If you build multiple images, each build will overwrite the cache of the previous" with the default scope. "only GitHub Cache service API v2 is supported. The legacy v1 API has been shut down" (Buildx >= v0.21.0, BuildKit >= v0.20.0). GitHub cache: 10 GB per repository by default, entries unused for 7 days are removed.
- Code:
  ```yaml
  cache-from: type=gha,scope=my-app
  cache-to: type=gha,scope=my-app,mode=max
  ```
- Source: https://docs.docker.com/build/ci/github-actions/cache/; https://docs.docker.com/build/cache/backends/gha/; https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching (2026-10-30)

**A9. Keep BuildKit provenance on and add `sbom: true` on pushed images**
> Confidence: High | [✓✓ Triangulated | Docker GitHub Actions attestations page + Docker build attestations page]
- Why: on GitHub Actions, private repos get "provenance attestations with `mode=min`" automatically, public repos `mode=max`; "SBOM attestations aren't automatically added to the image. To add SBOM attestations, set the `sbom` input ... to true." Attestations "attach to images as a manifest in the image index" and "Pushing the result to a registry with `--push` keeps the attestations"; `load: true` / the docker exporter add none.
- Code:
  ```yaml
  with:
    push: true
    sbom: true
    # provenance: default (mode=min on private repos); see N5 before mode=max
  ```
- Source: https://docs.docker.com/build/ci/github-actions/attestations/; https://docs.docker.com/build/metadata/attestations/ (2026-10-30)

### ⚠️ Conditional Patterns

**C1. Signed artifact attestations (`actions/attest` v4.2.2) and `gh attestation verify`**
- Decision: add a Sigstore-signed GitHub attestation on top of the BuildKit attestations?
- Facts: "To use artifact attestations in private or internal repositories, you must be on a GitHub Enterprise Cloud plan"; public repos: all current plans; GHES not supported (actions/attest v4.2.2 README; attest-build-provenance v4.2.2 README). `actions/attest-build-provenance` v4 "is simply a wrapper on top of `actions/attest`" and "new implementations should use `actions/attest` instead". Permissions: `id-token: write`, `attestations: write`, `artifact-metadata: write` (+ `packages: write` for push-to-registry). Mode: provenance by default, SBOM when `sbom-path` given (JSON, max 16 MB). `subject-name` = image without tag, `subject-digest` = build-push `digest`; `push-to-registry: true` stores it in the registry. Note the GitHub how-to lists only `id-token`, `contents`, `attestations` (+`packages`) and omits `artifact-metadata`, while the README requires it because `create-storage-record` defaults to `true` (medium confidence on which is authoritative; use the README).
- Options: A) Team/Pro/Free private repo: skip; rely on A9 BuildKit attestations, inspected with `docker buildx imagetools inspect <ref> --format '{{json .Provenance}}'` / `'{{json .SBOM}}'` (unsigned, no gh verify). B) Public repo or Enterprise Cloud: add `actions/attest` and verify with `gh attestation verify oci://<image> -R <owner>/<repo>` (default predicate `https://slsa.dev/provenance/v1`; registry login required for `oci://`; `--bundle-from-oci`, `--signer-workflow`, `--source-ref`, `--deny-self-hosted-runners` tighten policy). "Artifact attestations by itself provides SLSA v1.0 Build Level 2"; Level 3 needs the build in a reusable workflow.
- Code (option B only):
  ```yaml
  permissions:
    contents: read
    packages: write
    id-token: write
    attestations: write
    artifact-metadata: write
  steps:
    - uses: actions/attest@<FR6-sha> # v4.2.2
      with:
        subject-name: ghcr.io/${{ github.repository }}
        subject-digest: ${{ steps.push.outputs.digest }}
        push-to-registry: true
  ```
- Source: https://github.com/actions/attest/blob/v4.2.2/README.md; https://github.com/actions/attest-build-provenance/blob/v4.2.2/README.md; https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations; https://docs.github.com/en/actions/concepts/security/artifact-attestations; https://cli.github.com/manual/gh_attestation_verify; https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/ (2026-10-30)

**C2. Multi-architecture images: QEMU on one runner vs native runners per platform**
- Options: A) `docker/setup-qemu-action` v4.4.0 + `platforms: linux/amd64,linux/arm64` in one job; B) one job per platform on native runners (Docker docs map Linux Arm to `ubuntu-24.04-arm` in `docker/github-builder`), merged into one index; C) cross-compilation in a multi-stage Dockerfile.
- Tradeoffs: "Emulation with QEMU can be much slower than native builds ... especially for compute-heavy tasks like compilation and compression"; "Building multiple platforms on the same runner can significantly extend build times". Native runners avoid emulation but need a merge step; availability/pricing of arm64 hosted runners on private repos was not read (unverified). Docker now documents the reusable `docker/github-builder` workflow (`@v1`) for distributed builds; it is not in the facts file (unverified for pinning).
- When: Java (JVM bytecode) images usually only need multi-arch base images, so A is acceptable; Next.js builds with native deps are compile-heavy, prefer B or a single platform (medium confidence, inference).
- Source: https://docs.docker.com/build/building/multi-platform/; https://docs.docker.com/build/ci/github-actions/multi-platform/; https://github.com/docker/setup-qemu-action/releases (2026-10-30)

**C3. Promotion across environments: retag the same digest vs copy to a per-environment registry**
- Options: A) one registry, deploy every environment from `repo@sha256:<digest>`; optionally add an environment tag pointing at the same digest; B) separate registries/accounts per environment and copy the image.
- Facts: `docker buildx imagetools create` "Create[s] a new manifest list based on source manifests", sources "must already exist in the registry where the new manifest is created", and a single index source produces a "carbon copy" (`--prefer-index` default `true`). The page does not say blobs are copied across registries or that the digest is preserved (unverified for cross-registry copy). ECR immutable repositories reject re-pushing an existing tag (`ImageTagAlreadyExistsException`), so environment tags need `IMMUTABLE_WITH_EXCLUSION` filters or no environment tags at all.
- When: A is the default (rule 8, fewest moving parts). B only when account isolation is mandated; then verify digest equality after copy.
- Source: https://docs.docker.com/reference/cli/docker/buildx/imagetools/create/; https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html (2026-10-30)

**C4. OCIR login: `docker/login-action` (username + auth token) vs `oracle-actions/login-ocir` (API key env + auth token)**
- Facts: login-action OCIR: "the username must be placed in format <tenancy>/<username>", "For password create an auth token", registry `<region>.ocir.io`. login-ocir v1.3.0 needs `OCI_CLI_USER`, `OCI_CLI_TENANCY`, `OCI_CLI_FINGERPRINT`, `OCI_CLI_KEY_CONTENT`, `OCI_CLI_REGION` plus input `auth_token`, outputs `ocir_endpoint`, `ocir_username`. Oracle: username `<tenancy-namespace>/<username>` (federated: `<tenancy-namespace>/<domain-name>/<username>`), password = auth token, image path `<registry-domain>/<tenancy-namespace>/<repo-name>:<version>`, registry domain example `ocir.us-ashburn-1.oci.oraclecloud.com`.
- Tradeoffs: login-action stores 2 values (username, token) and does not need the API private key; login-ocir derives endpoint and username but needs the full API key set (same set the OCI deploy job uses under rule 9). login-ocir v1.3.0 was released "18 Jun" with year not shown and only a semver bump + config-dir fix, so it is an old but still latest release (medium confidence on age).
- When: image-only job -> login-action (smaller secret footprint, inference); job that also runs OCI CLI/Terraform with the API key -> login-ocir. OIDC token exchange for OCIR (F20/F21) is not documented for registry login (unverified).
- Source: https://github.com/docker/login-action/blob/v4.7.0/README.md; https://github.com/oracle-actions/login-ocir/blob/v1.3.0/README.md; https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm (2026-10-30)

**C5. Where registry credentials live on the target plan (brief lesson + caller note)**
- Facts (deployments-and-environments page): environment secrets on private repos need "GitHub Pro, GitHub Team, or GitHub Enterprise" (Free: public repos only); environment variables and deployment branches/tags on private repos: Pro/Team (Free: public only); required reviewers, wait timers, admin bypass and custom protection rules: public repos only on Free/Pro/Team. "a job cannot access environment secrets until one of the required reviewers approves it."
- Per registry:
  | Registry | Credential | Team/Pro private | Free private | Public repo / Enterprise |
  |---|---|---|---|---|
  | GHCR | `GITHUB_TOKEN` + `packages: write` | no stored secret | no stored secret | same; required reviewers available as gate |
  | ECR | OIDC role (F3), role ARN is not secret | role trust can be scoped to an environment; environment + deployment branch policy `main` | no environment branch policy: scope trust to the protected branch ref; store role ARN as repository variable or literal (medium confidence; `sub` formats owned by `federating-github-actions-aws-oidc`) | add required reviewers |
  | OCIR | username + auth token (+ API key for login-ocir) | environment secrets in the publishing environment with deployment branch policy (rule 10) | only repository secrets exist: any non-fork workflow run on any branch can read them; mitigate with a push-only OCI user/group limited to the repository compartment and a branch-protected workflow (inference, rule 10 cannot be met; flag to orchestrator) | environment secrets + required reviewers |
- When: Ask the user which plan applies before choosing the OCIR layout; on Free private, recommend GHCR or ECR (no stored secret) or an upgrade to Pro/Team.
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments; https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows (2026-10-30)

**C6. Git context vs path context**
- Facts: Git context is the default; "BuildKit checks out the repository, so `actions/checkout` is not needed" and changes from earlier steps, "including `.dockerignore`", are ignored; set `context` and run `actions/checkout` for path context.
- When: Java/Next.js images that COPY a jar or `.next` output built in an earlier step need path context (`context: .`) after checkout or `download-artifact` (F24).
- Source: https://github.com/docker/build-push-action/blob/v7.4.0/README.md (2026-10-30)

### 🚫 Forbidden Patterns

**N1. Deploying or promoting by `latest` (or any moving tag)**
- Why: metadata-action generates `latest` automatically ("`latest=auto`") for `type=ref,event=tag`, `type=semver`, `type=pep440`, `type=match`; branch/PR tags move with every push. Deploying a moving tag breaks build-once-promote (rule 8).
- ❌ Wrong:
  ```yaml
  image: ghcr.io/acme/app:latest
  ```
- ✅ Correct:
  ```yaml
  image: ghcr.io/acme/app@${{ needs.image.outputs.digest }}
  ```
- Impact: prod may run an image that was never tested in staging; rollbacks are ambiguous.
- Source: https://github.com/docker/metadata-action/blob/v6.2.0/README.md; https://github.com/docker/build-push-action/blob/v7.4.0/README.md (2026-10-30)

**N2. Pushing from pull-request runs or giving them registry write credentials**
- Why: rule 7/13; fork and Dependabot PRs get a read-only token and no secrets anyway, so a push step fails or invites `pull_request_target` workarounds, which GitHub warns "may lead to security vulnerabilities" including "cache poisoning and granting unintended access to write privileges or secrets".
- ❌ Wrong:
  ```yaml
  on: pull_request_target
  # ... checkout PR head, login, push: true
  ```
- ✅ Correct:
  ```yaml
  on: pull_request
  # ... push: false (or push: ${{ github.event_name != 'pull_request' }}), no login
  ```
- Impact: untrusted branch code gains registry write; poisoned images or caches.
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows; https://docs.github.com/en/actions/reference/security/secure-use (2026-10-30)

**N3. Using a personal access token (or long-lived AWS keys) for GHCR / ECR in Actions**
- Why: GitHub "highly recommend[s]" `GITHUB_TOKEN` over a PAT for GHCR workflows; the login-action ECR example with `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` is static keys, while the family uses OIDC (rule 9, F3).
- ❌ Wrong:
  ```yaml
  password: ${{ secrets.GHCR_PAT }}
  # or: username: ${{ vars.AWS_ACCESS_KEY_ID }} / password: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  ```
- ✅ Correct:
  ```yaml
  password: ${{ secrets.GITHUB_TOKEN }}      # GHCR, permissions: packages: write
  # ECR: configure-aws-credentials (OIDC, F3) + amazon-ecr-login (FR5)
  ```
- Impact: long-lived credentials that outlive the job and leak through logs/forks.
- Source: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry; https://github.com/docker/login-action/blob/v4.7.0/README.md; https://github.com/aws-actions/amazon-ecr-login/blob/v2.1.7/README.md (2026-10-30)

**N4. Setting `mask-password: 'false'` on amazon-ecr-login to pass Docker credentials between jobs**
- Why: "Masked values cannot be passed to separate jobs", and unmasked values are logged when debug logging is on.
- ❌ Wrong:
  ```yaml
  - uses: aws-actions/amazon-ecr-login@<FR5-sha> # v2.1.7
    with:
      mask-password: 'false'
  ```
- ✅ Correct:
  ```yaml
  # log in inside the job that pushes; pass only the digest between jobs (A4)
  - uses: aws-actions/amazon-ecr-login@<FR5-sha> # v2.1.7
  ```
- Impact: registry password in logs.
- Source: https://github.com/aws-actions/amazon-ecr-login/blob/v2.1.7/README.md (2026-10-30)

**N5. Passing secrets as `build-args` (they end up in provenance)**
- Why: "the provenance attestations attached to your image by default contains the values of build arguments" so "those secrets are exposed in the provenance attestation"; "rotate any secrets you may have exposed". build-push has `secrets` / `secret-envs` inputs for this.
- ❌ Wrong:
  ```yaml
  build-args: |
    NPM_TOKEN=${{ secrets.NPM_TOKEN }}
  ```
- ✅ Correct:
  ```yaml
  secrets: |
    npm_token=${{ secrets.NPM_TOKEN }}
  # Dockerfile: RUN --mount=type=secret,id=npm_token ...
  ```
- Impact: secret readable by anyone who can pull the image.
- Source: https://docs.docker.com/build/ci/github-actions/attestations/; https://github.com/docker/build-push-action/blob/v7.4.0/README.md (2026-10-30). The Dockerfile `--mount=type=secret` line is (medium confidence): Dockerfile reference not read this run.

**N6. Writing the gha cache from read-only contexts or using one default scope for several images**
- Why: export fails with "failed to reserve cache" when access is read-only; "Workflows with read-only access should keep `cache-from: type=gha` and omit `cache-to`"; `ignore-error=true` "suppresses all cache export errors". Default scope `buildkit` makes each image overwrite the previous one's cache.
- ❌ Wrong:
  ```yaml
  cache-to: type=gha,mode=max,ignore-error=true   # every job, every image, default scope
  ```
- ✅ Correct:
  ```yaml
  cache-from: type=gha,scope=my-app
  cache-to: ${{ github.event_name == 'push' && 'type=gha,scope=my-app,mode=max' || '' }}
  ```
- Impact: silent cache loss or cache poisoning across images.
- Source: https://docs.docker.com/build/ci/github-actions/cache/; https://docs.docker.com/build/cache/backends/gha/ (2026-10-30)

**N7. Using `load: true` (docker exporter) for the image you ship**
- Why: "no attestations are added to the image" for the docker exporter / `load: true`; "the local image store doesn't support loading images with attestations". Use `push: true` for the shipped image; `load` only for local smoke tests.
- ❌ Wrong:
  ```yaml
  load: true
  # then: docker push ...
  ```
- ✅ Correct:
  ```yaml
  push: true
  sbom: true
  ```
- Impact: pushed image carries no provenance/SBOM; digest differs from the attested build.
- Source: https://docs.docker.com/build/ci/github-actions/attestations/; https://docs.docker.com/build/metadata/attestations/ (2026-10-30)

**N8. Starting new work on `actions/attest-build-provenance`**
- Why: "As of version 4, `actions/attest-build-provenance` is simply a wrapper on top of `actions/attest`" and "new implementations should use `actions/attest` instead".
- ❌ Wrong:
  ```yaml
  - uses: actions/attest-build-provenance@<sha> # v4.2.2
  ```
- ✅ Correct:
  ```yaml
  - uses: actions/attest@<FR6-sha> # v4.2.2   (only where C1 option B applies)
  ```
- Impact: extra indirection; diverges from GitHub's current docs.
- Source: https://github.com/actions/attest-build-provenance/blob/v4.2.2/README.md; https://github.com/actions/attest-build-provenance/releases (2026-10-30)

## Migration Guide

| From | To | Change | Source |
|---|---|---|---|
| build-push v6 | v7.0.0 ("05 Mar") | Node 24 default runtime (runner >= v2.327.1); removed `DOCKER_BUILD_NO_SUMMARY` and `DOCKER_BUILD_EXPORT_RETENTION_DAYS` (use `DOCKER_BUILD_SUMMARY=false`, `DOCKER_BUILD_RECORD_RETENTION_DAYS`) | build-push releases; README v7.4.0 |
| build-push v7.3.0 | v7.4.0 ("15 Sep") | "Prevent workflow command injection in metadata logs" (#1617); shared error helper | build-push releases |
| setup-buildx v3 | v4.0.0 ("05 Mar") | Node 24; "Remove deprecated inputs/outputs" (#464); ESM. v4.4.1: "Skip BuildKit image pre-pulls for explicit endpoints" | setup-buildx releases |
| login-action v3 | v4.0.0 ("04 Mar") | Node 24; ESM. v4.7.0 ("23 Oct"): "Preserve explicit ECR settings in `registry-auth`", "Use registry hosts for scoped credentials" | login-action releases |
| metadata-action v5 | v6.0.0 ("05 Mar") | Node 24; "List inputs now preserve `#` inside values while still supporting full-line `#` comments" (check `tags:` lines containing `#`) | metadata-action releases |
| setup-qemu v3 | v4.0.0 ("04 Mar") | Node 24; ESM | setup-qemu releases |
| attest-build-provenance v3 | v4.0.0 ("25 Feb") | becomes wrapper of `actions/attest`; actions/attest v4.0.0 folded provenance and SBOM actions in | attest / attest-build-provenance releases |
| gha cache v1 API | v2 only | "The legacy v1 API has been shut down"; needs Buildx >= v0.21.0, BuildKit >= v0.20.0 | Docker GHA cache page |
| amazon-ecr-login v1 | v2 | `mask-password` default `false` -> `true` | amazon-ecr-login v2.1.7 README |

No breaking change is labeled as such on any release page; the table lists compatibility-affecting
notes. Self-hosted runners older than v2.327.1 cannot run the new majors (all docker/* release notes).

## Implementation Blueprint

Reusable workflow `./.github/workflows/_image-build-push.yml` (rules 5, 6, 15). Representative — adapt to your environment.

```yaml
# _image-build-push.yml — build-push-action v7.4.0 (F7); FRn placeholders until facts file updated
name: _image-build-push
on:
  workflow_call:
    inputs:
      image:        { type: string, required: true }   # e.g. ghcr.io/acme/app (no tag)
      context:      { type: string, default: . }
      file:         { type: string, default: ./Dockerfile }
      platforms:    { type: string, default: linux/amd64 }
      push:         { type: boolean, default: false }
      artifact-name: { type: string, default: '' }     # optional build output from the app job (F24)
    outputs:
      digest:  { value: '${{ jobs.build.outputs.digest }}' }
      version: { value: '${{ jobs.build.outputs.version }}' }
permissions: {}
jobs:
  build:
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      packages: write          # GHCR push; remove for ECR/OCIR-only callers
    outputs:
      digest:  ${{ steps.push.outputs.digest }}
      version: ${{ steps.meta.outputs.version }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - if: inputs.artifact-name != ''
        uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with: { name: '${{ inputs.artifact-name }}', path: build-output }
      - id: meta
        uses: docker/metadata-action@<FR3-sha> # v6.2.0
        with:
          images: ${{ inputs.image }}
          tags: |
            type=sha,format=long
            type=semver,pattern={{version}}
            type=ref,event=pr
      - if: contains(inputs.platforms, ',')
        uses: docker/setup-qemu-action@<FR4-sha> # v4.4.0
      - uses: docker/setup-buildx-action@<FR1-sha> # v4.4.1
      - if: inputs.push
        uses: docker/login-action@<FR2-sha> # v4.7.0
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
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          annotations: ${{ steps.meta.outputs.annotations }}
          sbom: ${{ inputs.push }}
          cache-from: type=gha,scope=${{ inputs.image }}
          cache-to: ${{ inputs.push && format('type=gha,scope={0},mode=max', inputs.image) || '' }}
```

Callers (rule 5): `ci-<app>.yml` on `pull_request` calls it with `push: false`; `cd-<app>.yml` on push
to `main` / release tag calls it with `push: true` and passes `needs.<job>.outputs.digest` to the deploy
job or to Terraform as a variable (`-var image_digest=...`, or `image_uri = "${repo}@${digest}"`).
Notes:
- `cache-to` empty-string expression and the `scope` value containing `/` are (medium confidence): not exercised; scope syntax constraints not documented on the pages read.
- ECR variant: replace the login step with F3 + amazon-ecr-login (A6), add `id-token: write` to this job only, drop `packages: write`.
- OCIR variant: login-action with `registry: <region>.ocir.io`, `username: <tenancy-namespace>/<user>`, `password: ${{ secrets.OCIR_AUTH_TOKEN }}` from an environment secret (C4, C5); reusable workflow declares the secret by name (rule 6).
- For multi-platform builds `digest` is the digest of what was pushed; whether it is the index digest when `platforms` has 2+ entries is (medium confidence, inference from multi-platform docs).

Consumer verification (Representative):
```bash
# BuildKit attestations (all plans)
docker buildx imagetools inspect ghcr.io/acme/app@sha256:<digest> --format '{{json .Provenance}}'
docker buildx imagetools inspect ghcr.io/acme/app@sha256:<digest> --format '{{json .SBOM}}'
# GitHub artifact attestations (public repos or Enterprise Cloud only; requires registry login)
gh attestation verify oci://ghcr.io/acme/app@sha256:<digest> -R acme/app
# Expected: exit 0 and a verified SLSA provenance v1 predicate
```

## Quality Control

- Offline checks for the skill author: `actionlint` on workflows (not researched here; owned by `automating-github-repos-with-actions`), `grep -n "latest" .github/workflows/*.yml` must not find a deploy reference, `grep -n "push: true" ci-*.yml` must return nothing.
- PR run asserts: build succeeds with `push: false`; `DOCKER_BUILD_SUMMARY` default `true` gives a job summary; build record is uploaded as an artifact unless `DOCKER_BUILD_RECORD_UPLOAD=false`; retention via `DOCKER_BUILD_RECORD_RETENTION_DAYS` (build-push v7.4.0 README).
- `call: check` input runs Dockerfile build checks without building (build-push README "Set method for evaluating build", e.g. `check`).
- Vulnerability scanning (Trivy) is owned by `securing-supply-chain-github-actions`.

## Production Readiness

- Limits: GHCR "10 GB size limit for each layer" and "10 minute timeout limit for uploads"; GitHub cache 10 GB per repo, 7-day idle eviction; gha backend "is subject to rate limiting" (Docker gha backend page).
- GHCR packages default to "private" visibility and inherit the linked repository's permissions unless the org disabled inheritance; `GITHUB_TOKEN` gets `admin` on packages published from the workflow's repo.
- Private package quotas (shared with Actions artifacts): Free 500 MB / 1 GB transfer, Pro and Team 2 GB / 10 GB, Enterprise Cloud 50 GB / 100 GB; Container registry storage and bandwidth "currently free" with at least one month's notice before change.
- ECR: enable `IMMUTABLE` (or `IMMUTABLE_WITH_EXCLUSION` with filters) so `sha-` tags cannot be overwritten; "Tag immutability affects all tags" unless exclusion filters are set.
- GHCR and OCIR tag immutability settings were not found in the pages read (unverified).
- Environments on the target plan: see C5 (Free private has no environment secrets, branch policies or reviewers; Pro/Team private have secrets + branch policies, no reviewers).

## Reference Implementations

- docker/build-push-action README examples (v7.4.0) — https://github.com/docker/build-push-action/blob/v7.4.0/README.md
- Docker docs, GitHub Actions: cache, attestations, multi-platform — https://docs.docker.com/build/ci/github-actions/
- GitHub tutorial "Publishing Docker images" (permissions + actions/attest; doc SHAs not used) — https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images
- actions/attest container example — https://github.com/actions/attest/blob/v4.2.2/README.md
- amazon-ecr-login OIDC example — https://github.com/aws-actions/amazon-ecr-login/blob/v2.1.7/README.md
- login-ocir example — https://github.com/oracle-actions/login-ocir/blob/v1.3.0/README.md

## Research Gaps

| ID | Gap | Status | Follow-up |
|---|---|---|---|
| G1 | Full 40-char SHAs for FR1-FR7 taken from release-page commit links; annotated-tag peeling not checked | (medium confidence) | Orchestrator: `git ls-remote https://github.com/<repo> refs/tags/<tag>` (peeled) before adding to facts |
| G2 | Cross-registry copy with `imagetools create` (blob copy, digest preserved) | (unverified) | Read Docker docs on registry-to-registry copy or test; else per-env registries need a separate tool |
| G3 | GHCR and OCIR tag immutability settings | (unverified) | GHCR docs silent; OCIR repository settings page not read |
| G4 | arm64 hosted runner availability/pricing for private repos | (unverified) | Read GitHub-hosted runners reference |
| G5 | OIDC `sub` claim formats and environment scoping on Free private repos (do environments exist without secrets/branch policies?) | (unverified) | Owned by `federating-github-actions-aws-oidc`; deployments-and-environments page has no general plan statement for environments |
| G6 | `digest` output = index digest for multi-platform builds | (medium confidence) | Read buildx metadata file docs |
| G7 | `artifact-metadata: write` required (README) vs omitted (GitHub how-to) | (medium confidence) | Prefer README v4.2.2; only relevant for Enterprise Cloud/public |
| G8 | OCIR registry login through OCI token exchange (F20/F21) | (unverified) | Owned by `federating-github-actions-oci` |

## Research Iteration Changelog

| Iteration | Gap | Resolution | Source |
|---|---|---|---|
| 1 | attest-build-provenance vs attest | Resolved: v4 is a wrapper; use `actions/attest` | attest-build-provenance v4.2.2 README + releases |
| 1 | Artifact attestations on private repos | Resolved: Enterprise Cloud required for private/internal; C1 made conditional | actions/attest v4.2.2 README + attest-build-provenance README |
| 2 | Full SHAs for short release-page commits (attest, ecr-login, login-ocir, setup-qemu) | Resolved from release tag pages (still G1 for peeling) | release tag pages |
| 2 | Job output size and secret redaction | Resolved: 1 MB/job, 50 MB/run, secrets redacted | workflow-syntax (offset 100000) |
| 3 | Registry credentials per plan (caller lesson) | Resolved: C5 table | deployments-and-environments |
| 3 | How to inspect BuildKit attestations without gh | Resolved: `imagetools inspect --format '{{json .Provenance}}'` | imagetools inspect reference |

## Completion Checklist

- [x] Metadata, Executive Summary, three guardrail tiers (9 / 6 / 8)
- [x] Every Never Do has ❌/✅ examples
- [x] Migration guide for build-push v7, setup-buildx v4, login v4, metadata v6, setup-qemu v4, attest v4, gha cache v2
- [x] SHAs in examples only from facts file (F3, F7, F10, F24); others placeholders + Facts requested
- [x] Plan availability (Team/Pro/Free private) checked on docs.github.com; defaults avoid required reviewers
- [x] PR jobs never push and never use deployable credentials (rules 7, 13)
- [x] Pages read table; prompt-injection check done
- [x] Ends with Source Bibliography
- [ ] Commands executed live (not run: research only; marked Representative)

## Agent Operation Notes

- High confidence: build-push inputs/outputs and env vars; setup-buildx default driver; metadata tag types and `latest=auto`; GHCR login with GITHUB_TOKEN, limits, billing; ECR login, mask-password, IAM actions, tag immutability; OCIR username/token format; BuildKit default provenance by repo visibility and SBOM opt-in; artifact attestation plan limits; gh attestation verify flags; environment features by plan; fork PR token/secrets.
- Medium confidence: FR SHAs (peeling), multi-platform digest semantics, workflow expression details in the blueprint, login-ocir age, OCIR on Free private mitigation (inference), Dockerfile secret mount syntax.
- Low / unverified: G2-G5, G8.

## Pages read

| URL | read on | official | prompt-injection-like instructions found |
|---|---|---|---|
| https://github.com/docker/build-push-action/releases | 2026-10-30 (latest 3 + v7.0.0 notes) | yes | no |
| https://github.com/docker/build-push-action/blob/v7.4.0/README.md | 2026-10-30 | yes | no |
| https://github.com/docker/setup-buildx-action/releases | 2026-10-30 (first page) | yes | no |
| https://github.com/docker/setup-buildx-action/blob/v4.4.1/README.md | 2026-10-30 | yes | no |
| https://github.com/docker/login-action/releases | 2026-10-30 (first page) | yes | no |
| https://github.com/docker/login-action/blob/v4.7.0/README.md | 2026-10-30 | yes | no |
| https://github.com/docker/metadata-action/releases | 2026-10-30 (first page) | yes | no |
| https://github.com/docker/metadata-action/blob/v6.2.0/README.md | 2026-10-30 | yes | no |
| https://github.com/docker/setup-qemu-action/releases | 2026-10-30 (first page) | yes | no |
| https://github.com/docker/setup-qemu-action/releases/tag/v4.4.0 | 2026-10-30 | yes | no |
| https://github.com/aws-actions/amazon-ecr-login/releases | 2026-10-30 (first page; notes defer to changelog) | yes | no |
| https://github.com/aws-actions/amazon-ecr-login/releases/tag/v2.1.7 | 2026-10-30 | yes | no |
| https://github.com/aws-actions/amazon-ecr-login/blob/v2.1.7/README.md | 2026-10-30 | yes | no |
| https://github.com/actions/attest/releases | 2026-10-30 (page 1 of 3) | yes | no |
| https://github.com/actions/attest/releases/tag/v4.2.2 | 2026-10-30 | yes | no |
| https://github.com/actions/attest/blob/v4.2.2/README.md | 2026-10-30 | yes | no |
| https://github.com/actions/attest-build-provenance/releases | 2026-10-30 (first page) | yes | no |
| https://github.com/actions/attest-build-provenance/blob/v4.2.2/README.md | 2026-10-30 | yes | no |
| https://github.com/oracle-actions/login-ocir/releases | 2026-10-30 | yes | no |
| https://github.com/oracle-actions/login-ocir/releases/tag/v1.3.0 | 2026-10-30 | yes | no |
| https://github.com/oracle-actions/login-ocir/blob/v1.3.0/README.md | 2026-10-30 | yes | no |
| https://docs.docker.com/build/ci/github-actions/cache/ | 2026-10-30 | yes | no |
| https://docs.docker.com/build/cache/backends/gha/ | 2026-10-30 | yes | no |
| https://docs.docker.com/build/ci/github-actions/attestations/ | 2026-10-30 | yes | no |
| https://docs.docker.com/build/metadata/attestations/ | 2026-10-30 | yes | no |
| https://docs.docker.com/build/ci/github-actions/multi-platform/ | 2026-10-30 | yes | no |
| https://docs.docker.com/build/building/multi-platform/ | 2026-10-30 | yes | no |
| https://docs.docker.com/reference/cli/docker/buildx/imagetools/create/ | 2026-10-30 | yes | no |
| https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/ | 2026-10-30 | yes | no |
| https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/concepts/security/artifact-attestations | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/concepts/security/github_token | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/security/secure-use | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows | 2026-10-30 (pull_request / pull_request_target sections) | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax | 2026-10-30 (characters 0-200000 of 235839) | yes | no |
| https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/pass-job-outputs | 2026-10-30 | yes | no |
| https://docs.github.com/en/billing/concepts/product-billing/github-packages | 2026-10-30 | yes | no |
| https://cli.github.com/manual/gh_attestation_verify | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html | 2026-10-30 | yes | no |
| https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm | 2026-10-30 | yes | no |

## Facts requested

SHAs below come from the commit link on each release (tag) page, read 2026-10-30; confirm peeled
values with `git ls-remote` before adding (G1).

| ID | Repo | Tag | SHA (release page) | Release page URL | Why |
|---|---|---|---|---|---|
| FR1 | docker/setup-buildx-action | v4.4.1 ("16 Sep", Latest) | f87e5991a6d7451dcb8d9637bfbc97413f497069 | https://github.com/docker/setup-buildx-action/releases | A1, blueprint |
| FR2 | docker/login-action | v4.7.0 ("23 Oct", Latest) | 81c6f93d4bc991e510b342a00b419b3bb4efc5c6 | https://github.com/docker/login-action/releases | A5, C4 |
| FR3 | docker/metadata-action | v6.2.0 ("02 Jul", Latest) | dc802804100637a589fabce1cb79ff13a1411302 | https://github.com/docker/metadata-action/releases | A2, A3 |
| FR4 | docker/setup-qemu-action | v4.4.0 ("15 Sep", Latest) | 99012661954931238ded8c8b007157a8430204e1 | https://github.com/docker/setup-qemu-action/releases/tag/v4.4.0 | C2 |
| FR5 | aws-actions/amazon-ecr-login | v2.1.7 ("19 Aug", Latest) | 03f1aad4c6c7ffd436567f42f9384779290529bd | https://github.com/aws-actions/amazon-ecr-login/releases/tag/v2.1.7 | A6, N4 |
| FR6 | actions/attest | v4.2.2 ("04 Aug", Latest, immutable release) | 1e69f48acb82d1966a394da916b4c1698aa569d6 | https://github.com/actions/attest/releases/tag/v4.2.2 | C1 (Enterprise Cloud / public only) |
| FR7 | oracle-actions/login-ocir | v1.3.0 ("18 Jun", Latest; year not shown) | d65011bf8c9300e51a98658388a0fb46d1ed54b1 | https://github.com/oracle-actions/login-ocir/releases/tag/v1.3.0 | C4 (extends F22) |
| (info) | actions/attest-build-provenance | v4.2.2 ("06 Aug") | 4d101475d8b20a2381f78447822ac1eab6504dd8 | https://github.com/actions/attest-build-provenance/releases | Not to be used (N8); listed for completeness |

Also requested: a family decision for OCIR registry secrets on GitHub Free private repos, where
environment secrets do not exist and rule 10 cannot be met (C5).

## Source Bibliography

### Primary Sources (all read 2026-10-30)
- docker/build-push-action releases (v7.4.0 "15 Sep", v7.0.0 "05 Mar") and README v7.4.0 — https://github.com/docker/build-push-action/releases, https://github.com/docker/build-push-action/blob/v7.4.0/README.md
- docker/setup-buildx-action releases and README v4.4.1 — https://github.com/docker/setup-buildx-action/releases, https://github.com/docker/setup-buildx-action/blob/v4.4.1/README.md
- docker/login-action releases and README v4.7.0 — https://github.com/docker/login-action/releases, https://github.com/docker/login-action/blob/v4.7.0/README.md
- docker/metadata-action releases and README v6.2.0 — https://github.com/docker/metadata-action/releases, https://github.com/docker/metadata-action/blob/v6.2.0/README.md
- docker/setup-qemu-action releases (v4.4.0) — https://github.com/docker/setup-qemu-action/releases
- aws-actions/amazon-ecr-login releases and README v2.1.7 — https://github.com/aws-actions/amazon-ecr-login/releases, https://github.com/aws-actions/amazon-ecr-login/blob/v2.1.7/README.md
- actions/attest releases and README v4.2.2 — https://github.com/actions/attest/releases, https://github.com/actions/attest/blob/v4.2.2/README.md
- actions/attest-build-provenance releases and README v4.2.2 — https://github.com/actions/attest-build-provenance/releases, https://github.com/actions/attest-build-provenance/blob/v4.2.2/README.md
- oracle-actions/login-ocir releases and README v1.3.0 — https://github.com/oracle-actions/login-ocir/releases, https://github.com/oracle-actions/login-ocir/blob/v1.3.0/README.md
- Docker docs (no page dates shown): GitHub Actions cache, gha cache backend, GitHub Actions attestations, build attestations, GitHub Actions multi-platform, multi-platform builds, `buildx imagetools create`, `buildx imagetools inspect` — https://docs.docker.com/build/ci/github-actions/cache/, https://docs.docker.com/build/cache/backends/gha/, https://docs.docker.com/build/ci/github-actions/attestations/, https://docs.docker.com/build/metadata/attestations/, https://docs.docker.com/build/ci/github-actions/multi-platform/, https://docs.docker.com/build/building/multi-platform/, https://docs.docker.com/reference/cli/docker/buildx/imagetools/create/, https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/
- GitHub Docs: Container registry; publishing Docker images; using artifact attestations; artifact attestations concept; GITHUB_TOKEN; secure use; deployments and environments; events that trigger workflows; dependency caching; workflow syntax; passing job outputs; GitHub Packages billing — https://docs.github.com/
- GitHub CLI manual: gh attestation verify — https://cli.github.com/manual/gh_attestation_verify
- Amazon ECR: image tag mutability — https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html
- Oracle OCIR: pushing images using the Docker CLI (© 2026) — https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm

### Family facts used
- F3 configure-aws-credentials v6.3.0, F7 build-push-action v7.4.0, F10 checkout v7.0.1, F20/F21 OCI token exchange (referenced as unverified for OCIR), F22 oracle-actions org, F24 download-artifact v8.0.2 — `workspace/github-actions-cicd/_family_facts.md`
