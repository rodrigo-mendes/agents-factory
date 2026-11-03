# Validate: composing-github-actions-pipelines (P6 r1, 2026-10-30)

Score: 90.0 (1 HIGH, 1 MEDIUM, 3 LOW). SKILL.md 135 lines. Frontmatter valid. SHAs match F2-F10, F36.

## HIGH
- H1 (A4/cross-skill, blueprints/monorepo-ci-gate.md:54-58): calls `_java-build.yml` with `app-dir: services/api`. Owner skill defines inputs `tool` (required), `java-version`, `package`, `working-directory`; no `app-dir`. Evidence: `uses: ./.github/workflows/_java-build.yml ... with: app-dir: services/api`. The example fails workflow validation. Extends F-012 (catalog-reference.md:23 also says `app-dir`, outputs "artifact name (indicative)" while the owner exports `artifact-name` and `artifact-digest`). Fix: `with: tool: maven, working-directory: services/api, package: jar`; update catalog row.

## MEDIUM
- M1 (rule 11/A4, blueprints/plan-variants.md:21): states `repo:OWNER@OWNER-ID/REPO@REPO-ID:environment:<env>` as fact. F26 gives the immutable form only with `ref:`; the aws skill tags the environment form (unverified, its U1). Fix: add (unverified) or drop the environment example.

## LOW
- L1 (A3): blueprints/unverified-and-risks.md (107 lines) and monorepo-ci-gate.md (125 lines) lack a Contents line.
- L2 (rule 3, SKILL.md:59,62): bullets carry two claims (outputs plus env not propagated; environment string input plus job-level environment).
- L3 (A4, SKILL.md:80): "F36" fact ID is unresolvable at run time (the skill says it never reads the research).

## Checked, fine
Rule 16 model in plan-variants.md matches facts (reviewers = upgrade path). Catalog `_tf-plan.yml`/`_tf-apply.yml` rows match the terraform skill exactly. Verification Loop present. Tag register counts (5/3/5/4) match. 5 evaluation scenarios.
