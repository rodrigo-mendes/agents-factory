# Validate: automating-terraform-github-actions-v1-17 (P6 r1, 2026-10-30)

Score (new + worse-than-described only): 86.0 (1 HIGH, 3 MEDIUM, 1 LOW). Known F-001..F-011 all still present, listed below. SKILL.md 119 lines. SHAs and 1.17.1 match F1, F2, F10, F23, F24.

## HIGH
- H1 (rule 16, worse than F-010): the skill never mentions protected `main` or PR review (grep "protected|PR review" = 0 hits in the skill). The whole approval model is required reviewers: SKILL.md:3 ("behind environment reviewers"), :46, :59 (Always Do), blueprints/workflow-tf-apply.md:11,13, always-do-patterns.md:7,98-104, workflow-callers.md:47 ("reviewed apply"), evaluation-scenarios.md:12,36. Its own Ask First (SKILL.md:79) and scenario 5 say reviewers do not work on Pro/Team private, the DEFAULT plan. The default flow therefore has no gate. Fix: default gate = PR review on protected `main` + environment branch policy `main`; reviewers as upgrade path; add Free variant pointer to composing plan-variants.md.

## MEDIUM
- M1 (cross-skill): merge-time plan runs `-lock=true` (blueprints/workflow-tf-plan.md:78) under `<env>-plan` "read credentials" (:11,13). S3 `use_lockfile` needs Put/Delete (state-backends.md:32); OCI skill flags that a read-only user cannot write the lock (federating-github-actions-oci policies-and-rotation.md:44). Terraform skill is silent. Fix: state the plan role needs lock-write on the state bucket, or lock-free plan; align with oci U7.
- M2 (rule 13, worse than F-002): `<env>-plan` environment/role is used for PR plans (workflow-tf-plan.md:42), merge plans and drift (workflow-callers.md:104). The aws skill defines only `gha-<app>-<env>-deploy` and `-pr-read` with `environment:<env>-pr`; the oci skill `oci-pr`. No sibling defines `<env>-plan`. Fix: use `<env>-pr` for PR and a documented role for merge plan/drift.
- M3 (cross-skill, workflow-callers.md:22-23): `ci-infra.yml` uses `on.pull_request.paths`; composing N7 forbids requiring such a workflow and the skill has no `ci-gate`. Fix: warn it is informational only or link the gate pattern.

## LOW
- L1 (rule 3, SKILL.md:52): "Pass -input=false and set TF_IN_AUTOMATION" is two claims.

## Known, still present (not re-scored)
F-001 no Verification Loop (Quick Navigation lines 30-42, rule 14); F-002 PR creds (see M2); F-003 no Contents in always-do-patterns (153 lines), never-do-patterns (136), workflow-callers (147), workflow-tf-plan (133), unverified-and-risks (127); F-004 tag notation; F-005 citations (SKILL.md:51 retention cites plan command); F-006 `cloud` input unused (login is a placeholder, plan.md:63); F-007 ops-drift has no concurrency group; F-008 artifact name `tfplan-env-comp-${GITHUB_SHA}` collides on re-run attempt (immutable artifacts); F-009 `<repo-workflows-dir>` at workflow-callers.md:15,35,65,78 (rule 15); F-011 as above.
