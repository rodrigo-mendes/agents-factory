# Test round 1 - publishing-container-images-github-actions

Method: answers simulated in the evaluator's own context from SKILL.md plus its blueprints (no agent spawned, DEC-014). Judged against the scenarios in blueprints/evaluation-scenarios.md. Date 2026-10-30. All 10 SHAs in the skill match F2-F10/F28-F34 (checked).

Verdict: 5/5 scenarios PASS, 2 findings.

| # | Scenario | Verdict | Evidence |
|---|---|---|---|
| 1 | GHCR on merge, digest output | PASS | workflow-image-publish.md header has typed inputs + outputs `digest`,`image-ref`; ci-image `push: false`, cd-image `push: true`; GHCR job `permissions: { contents: read, packages: write }` at job level; `type=sha,format=long`; `sbom: ${{ inputs.push }}`; deploy reads `needs.image.outputs.image-ref`; Verification Loop has SHA grep, `latest` grep, `push: true` in ci-*. |
| 2 | Multi-arch ECR, Team | PASS | ECR job: configure-aws-credentials then amazon-ecr-login, `id-token: write` on the ECR job only, `prod-publish` environment in caller, QEMU step `if: contains(inputs.platforms, ',')`, Ask First row on QEMU vs native + arm64 availability "unverified", `mask-password` default, ECR immutability in notes. Index-digest question is (medium confidence) only in the GHCR notes, not repeated in the ECR job (minor). |
| 3 | Deploy by latest | PASS | Never Do row 1 "Deploy or promote by latest ... -> repo@sha256:<digest>"; rule 8; digest job-output limits stated. |
| 4 | PR push + gh attestation on private Team | PASS | Never Do row 2 (incl. pull_request_target); attestations-and-verification.md "Signed GitHub artifact attestations need a public repository or GitHub Enterprise Cloud ... Team ... not available; keep the BuildKit default"; `imagetools inspect --format '{{json .Provenance}}'`; `actions/attest` as upgrade path, attest-build-provenance rejected. |
| 5 | OCIR on Free private | PASS | Ask First row "GitHub plan"; registry-credentials.md Free variant "repository secrets are readable by any non-fork workflow run on any branch"; "Recommend GHCR or ECR ... or an upgrade"; OCIR job uses docker/login-action, "OIDC login for OCIR is (unverified)". |

## Findings

### P-1 (medium) ECR/OCIR job takes a deployable environment and id-token on PR builds
`_image-publish.yml` ECR job always declares `environment: ${{ inputs.environment }}` and `permissions: { contents: read, id-token: write }`, even when `push: false`. A ci-image caller using `registry: ecr` therefore must grant `id-token: write` (design note: "caller may have to grant the union") and, if the caller copies the cd value `prod-publish`, binds a PR run to a deployable environment. Breaks family rules 7 and 13 and the OIDC skill Never Do "Give a PR job environment: prod". The only guard is a prose line in the ECR notes; no ci example for ecr/ocir exists.
Skill text responsible: workflow-image-publish-ecr-ocir.md `ecr:` job header; workflow-callers.md has only a GHCR ci-image. Fix: add `if`/split job (login job vs build job) or document "ci callers pass `environment: ''` and the ECR job gets id-token only when push"; add an ECR ci example.

### P-2 (low-medium) Direct configure-aws-credentials without allowed-account-ids / session name
ECR job calls the action directly with only `role-to-assume` and `aws-region`. The OIDC skill Always Do says "Set allowed-account-ids when calling the action directly" and prefers the `./.github/actions/cloud/login-aws` composite. No mention of either in this skill. Same pattern in nextjs and blast-radius skills (see their reports).

### P-3 (low) Verification Loop raw text
Rows 1-2 are written with `\|` inside backticks (needed for the Markdown table). An agent copying the raw file may run `grep -nE ':latest\|@latest'`, where `\|` is a literal pipe in ERE, so the check never matches. Suggest moving the loop to a code block.

## Known/tracked, not re-reported
F-012 catalog drift: catalog says `_image-publish.yml` inputs "registry and image name (indicative)" and output "image digest"; actual outputs are `digest` and `image-ref` (no worse than described).
