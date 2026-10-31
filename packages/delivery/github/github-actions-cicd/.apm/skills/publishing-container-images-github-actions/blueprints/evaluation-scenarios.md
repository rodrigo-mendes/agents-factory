# Evaluation scenarios

Back to [SKILL.md](../SKILL.md). Each scenario lists the prompt, expected behaviour and fail signals. Judge against docker/build-push-action v7.4.0 on GitHub.com Actions as of 2026-10-30.

## Scenario 1: Canonical, GHCR on merge with digest output

**Prompt:** "Build our Dockerfile on every PR and publish to GHCR when we merge to main. The deploy job needs the exact image."

**Expected:**
- Reusable `./.github/workflows/_image-publish.yml` with typed inputs (`context`, `file`, `registry`, `image-name`, `platforms`, `push`) and outputs `digest` and `image-ref`; thin callers `ci-image.yml` (pull_request, `push: false`) and `cd-image.yml` (push to main, `push: true`).
- GHCR login with `secrets.GITHUB_TOKEN`, `packages: write` only on the publishing job, tags with `type=sha,format=long`, `sbom: true`, default provenance.
- The deploy job reads `needs.image.outputs.image-ref` (`repo@sha256:...`); no `latest`.
- Every action pinned by the full SHA from the family facts; no `secrets: inherit`.
- Verification Loop commands offered (SHA grep, no `latest`, no `push: true` in ci callers).

**Fail signals:** version tags instead of SHAs; login step in the pull-request path; deploy by tag; `packages: write` at workflow level.

## Scenario 2: Edge, multi-arch image to ECR

**Prompt:** "Publish a linux/amd64 and linux/arm64 image to ECR. We are on a Team plan, private repo, no static AWS keys."

**Expected:**
- OIDC role through `configure-aws-credentials` then `amazon-ecr-login`, `id-token: write` only on the ECR job, environment `<env>-publish` with the role trust scoped to that environment (format owned by `federating-github-actions-aws-oidc`).
- QEMU step only when `platforms` has a comma; asks whether QEMU or native runners suit the build (compute-heavy builds are slow under emulation) and flags arm64 runner availability as unverified.
- `mask-password` left at the default; ECR tag immutability recommended; whether `digest` is the index digest stated as medium confidence with the `imagetools inspect` check.
- Digest, not a tag, handed to the deploy job.

**Fail signals:** `AWS_ACCESS_KEY_ID` secrets; `mask-password: 'false'`; environment tags on an immutable repository without exclusion filters; claims about arm64 pricing.

## Scenario 3: Rejection, deploy by `latest`

**Prompt:** "Our deploy job should just pull ghcr.io/acme/app:latest, that is simpler than passing digests around."

**Expected:**
- Declines: `latest` and branch tags move on every push, so production can run an image that was never tested; promotion is by digest (family rule 8).
- Shows the one-line alternative: `ghcr.io/acme/app@${{ needs.image.outputs.digest }}`, with the digest as a job output (limits 1 MB per job).
- Offers a human-readable tag only as an extra label next to the digest, never as the deploy reference.

**Fail signals:** keeps `:latest` in a deploy or Terraform variable; rebuilds the image for production.

## Scenario 4: Trap, push from pull_request and gh attestation on a private Team repo

**Prompt:** "Make the PR workflow push a preview image to GHCR, and add `gh attestation verify` to our release checklist. The repo is private on the Team plan."

**Expected:**
- Declines pushing from a pull_request job: no registry write credentials on PR runs, and `pull_request_target` is not a workaround; offers `push: false` builds and a preview only after merge or from a dispatched workflow on a protected branch.
- States that artifact attestations on private repositories need GitHub Enterprise Cloud (F33), so `gh attestation verify` will not work here; offers the BuildKit provenance and SBOM inspected with `docker buildx imagetools inspect --format '{{json .Provenance}}'`, noting they are unsigned.
- Mentions `actions/attest` as the upgrade path for public repositories or Enterprise Cloud, not `attest-build-provenance`.

**Fail signals:** adds `push: true` or a registry login to `ci-image.yml`; promises a verified signature on the Team private repository; adds `attestations: write` without the plan check.

## Scenario 5: Ask First, OCIR on a Free private repository

**Prompt:** "Publish to OCIR from GitHub Actions. We are on GitHub Free, private repo."

**Expected:**
- Asks which plan applies before choosing the layout; explains that environment secrets and protected branches do not exist on Free private repositories.
- Recommends GHCR or ECR (no stored static secret) or an upgrade; if the user insists, uses a least-privilege repository secret with an explicit warning that any non-fork run on any branch can read it.
- Uses `docker/login-action` with `<tenancy-namespace>/<user>` and an auth token; does not claim an OIDC login for OCIR.

**Fail signals:** silently stores the token as a repository secret; says an environment gate will protect it; claims federation works for registry login.
