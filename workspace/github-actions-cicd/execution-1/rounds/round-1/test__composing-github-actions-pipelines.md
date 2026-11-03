# Test P6 r1 - composing-github-actions-pipelines

Evaluator: skill-evaluator (own-context simulation, no sub-agents). Date 2026-10-30. Source read: packages/github-actions-cicd/.apm/skills/composing-github-actions-pipelines/ (SKILL.md + all blueprints).

Verdict: 4 PASS, 1 PASS with a defect (S1), 0 FAIL. Cross-skill defect D-1 is high severity.

## S1 Canonical monorepo ci-gate - PASS on criteria, defect D-1 in the produced code
- must: blocks `_node-build.yml` / `_java-build.yml` flat, composite `repo/changes`, caller `ci-monorepo.yml` with no path filter: PASS (monorepo-ci-gate.md "Caller ci-monorepo.yml", `on: pull_request` only).
- must: `changes` job, `if:` per app, `if: always()` ci-gate accepting success|skipped, only gate required: PASS (`case "$r" in success|skipped) ;;`).
- must: typed inputs, outputs, named secrets, permissions on calling jobs, timeout-minutes on every job, concurrency `cancel-in-progress: true`: PASS (A2, A3, A5).
- must: facts SHAs with tag comments, PR does not deploy: PASS (checkout 3d3c42e5... # v7.0.1).
- must_not: none violated (no path filters, no inherit, no tags).
- D-1 (see Findings): the produced `api:` job calls `_java-build.yml` with `app-dir: services/api`, which the owner skill does not define.

## S2 Central blocks repo pinned by SHA - PASS
- Default stays same-repo, central is an option, "Ask: Must blocks be shared across repositories?" (central-blocks-repo.md, SKILL.md Ask First).
- `my-org/ci-blocks/.github/workflows/_node-build.yml@<40-hex>`, "The commit SHA ... is the safest", versioning guidance 1-4 (new tag, `_node-build-2.yml`).
- Access setting and outside-collaborator log visibility; "equivalent setting for a personal account ... was not found (unverified)".
- Named secrets kept ("keep named secrets"). Dependabot for composites is tagged medium/unverified, not claimed as fact. must_not clean.

## S3 secrets: inherit across repositories - PASS (one expected bullet is not skill-backed)
- Declines: SKILL.md Never Do row 2; central-blocks-repo.md "works only within the same organization or enterprise and still only for the directly called workflow"; N2 "hides which secrets a block needs".
- Offers named secrets under `secrets:` plus the block's declared `secrets:` section (N2 correct form, A2).
- Gap: expected "short script or table to list the secrets once" has no supporting text in the skill; the model must improvise it. Not a must_not violation.

## S4 environment: on calling job + required path-filtered workflow - PASS
- Rejects `environment:` on the calling job (Never Do row 4, N4, A4) and moves it to a string input.
- Rejects required path-filtered workflow (Never Do row 7, N7, monorepo-ci-gate.md "Why": check stays Pending).
- Asks the plan (Ask First "GitHub plan"); plan-variants.md table: Free private has no environments, "Required reviewers on environments ... no | no (public repositories or Enterprise)". Matches rule 16. must_not clean.

## S5 composite vs reusable - PASS
- Ask First row "Does this block need its own runner, a secret, an environment or several jobs?"; composite recommended for repeated steps (composite-actions.md table).
- Token passed as `npm-token` input, `NODE_AUTH_TOKEN: ${{ inputs.npm-token }}`, `shell: bash` on every run step; N5 and N6 forbid `secrets.` and missing shell; "no INPUT_ variables" stated. must_not clean.

## Findings
- D-1 (HIGH, extends tracked F-012, worse than described): F-012 describes catalog names out of sync, but the executable example is broken. monorepo-ci-gate.md `api:` calls `_java-build.yml` with `app-dir: services/api`. The owner skill (building-java-github-actions/blueprints/workflow-java-build.md) defines inputs `tool` (required), `java-version`, `package`, `working-directory`, and no `app-dir`. GitHub rejects an undefined input and the required `tool` is missing, so the generated ci-monorepo.yml fails at parse time. catalog-reference.md row `_java-build.yml` ("`app-dir` (indicative)", output "artifact name (indicative)") repeats it; real outputs are `artifact-name`, `artifact-digest`. The `_node-build.yml` row lists `node-version` and secret `NPM_READ_TOKEN` but the owner (building-nextjs-github-actions-v16-4 workflow-node-build.md) defines `app-dir, mode, node-version, package-manager`; no NPM_READ_TOKEN secret seen in the grep of that skill. Fix direction: change the example call to the owner's real inputs (`tool: maven`, `working-directory: services/api`) or add a clearly marked placeholder block.
- D-2 (LOW): the own `_node-build.yml` example in always-do-patterns.md A2 uploads `<app-dir>/dist`, while the owner builds `out` or `.next/standalone`; two different `_node-build.yml` definitions exist in the family. Same root cause as D-1.
- D-3 (LOW): no text for the "list secrets once" offer in S3.
- Rule checks: facts pins match (F10, F6, F23, F24, F36). Rule 15 real paths used. Rule 16 plan model reads the same as aws-oidc, oci, java. Rule 14 Verification Loop present. No `<repo-workflows-dir>` placeholder.
