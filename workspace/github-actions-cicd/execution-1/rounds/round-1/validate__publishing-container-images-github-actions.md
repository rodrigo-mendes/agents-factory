# Validate: publishing-container-images-github-actions (P6 round 1, validator B, 2026-10-30)

Score: 90.0 (1 HIGH, 1 MEDIUM, 3 LOW). SKILL.md 133 lines, frontmatter valid (name = folder, description third person with "Use when", <1536 chars), three tiers present, Version Context, Verification Loop (rule 14), 5 evaluation scenarios, all pins match _family_facts.md (F2-F10, F28-F34).

Base path: packages/github-actions-cicd/.apm/skills/publishing-container-images-github-actions/

## HIGH
- H1 (D4/B5, family rule 6, composing SKILL.md:58): `blueprints/workflow-callers.md:16-17` ci-image.yml calls the reusable with `permissions: { contents: read }`, while the GHCR job in `blueprints/workflow-image-publish.md:52` declares `permissions: { contents: read, packages: write }`. Evidence: "uses: ./.github/workflows/_image-publish.yml / permissions: { contents: read }" vs "permissions: { contents: read, packages: write }". Composing says "the called workflow can only keep or reduce" the caller's permissions, so the PR example (the canonical Scenario 1) fails at startup even with `push: false`. The note at callers:26 only covers the union of all three jobs and says trimming unused jobs fixes it; trimming does not fix it for the GHCR job itself. Fix hint: give ci-image `packages: write` (read-only token on forks anyway) or split a PR-only no-login job without `packages: write`; state it in design notes.

## MEDIUM
- M1 (rule 10, composing Never Do SKILL.md:90): `blueprints/workflow-callers.md:74` reads `${{ vars.ECR_PUSH_ROLE_ARN }}` and `:83-84` reads `${{ secrets.OCIR_USERNAME }}` / `OCIR_AUTH_TOKEN` in the caller job's `with:`/`secrets:`, but `blueprints/registry-credentials.md:21-22` says these live as environment variable/secrets of `<env>-publish`. A caller job that uses a reusable workflow cannot declare `environment:` (composing forbids it), so environment-scoped values do not resolve in the caller; the default design silently receives empty values. Fix hint: have the called job read them from its own environment (declare required secrets, document the U8-style uncertainty in the register) or state that these must be repository/organization-level for this call shape (and flag the rule-10 weakening).

## LOW
- L1 (A3): `blueprints/unverified-and-risks.md` is 121 lines with no contents list.
- L2 (rule 1, D6): `SKILL.md:91` Never row "Use a PAT for GHCR or long-lived AWS keys for ECR" cites only the GHCR container-registry page; it supports the PAT half, not the AWS-keys half. Cite the ECR/OIDC source or split the row.
- L3 (composing Always Do SKILL.md:64, pr-ci rule): no `timeout-minutes` on the ghcr/ecr/ocir jobs (`workflow-image-publish.md:49`, `workflow-image-publish-ecr-ocir.md:12,74`) and no PR concurrency group on `ci-image.yml` (`workflow-callers.md:11-21`).

Checked and clean: SHAs/versions vs facts; plan model (rule 16) reads the same as siblings in registry-credentials.md; register counts (8/8/5) match tables; no secrets: inherit; no `<repo-workflows-dir>`.
