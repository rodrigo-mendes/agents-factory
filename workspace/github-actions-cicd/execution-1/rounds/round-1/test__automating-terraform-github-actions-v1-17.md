# Test P6 r1 - automating-terraform-github-actions-v1-17

Evaluator: skill-evaluator (own-context simulation, no sub-agents). Date 2026-10-30. Source read: packages/github-actions-cicd/.apm/skills/automating-terraform-github-actions-v1-17/ (SKILL.md + all blueprints).

Verdict on the file's own scenarios: S2, S3, S4 PASS; S1 and S5 PASS only against a stale scenario text that encodes the superseded approval model (see T-1). Pilot findings F-001..F-011 still present as described, except where noted below. New findings T-1..T-5.

## S1 Canonical AWS S3 pipeline - PASS on criteria (criteria themselves conflict with rule 16)
- must: reusable plan/apply, typed inputs and outputs `plan-artifact-name`, `has-changes`, callers ci/cd/ops-drift, no inherit: PASS (workflow-tf-plan.md Contract, workflow-callers.md).
- must: ci-infra runs fmt, validate, plan-only tests, preview plan, comment with `terraform show -no-color`, never applies: PASS (`terraform test -filter=tests/plan_only.tftest.hcl`, `gh pr comment`).
- must: cd-infra plans on merge commit, `retention-days: 1`, applies `tfplan` in same run "in a job whose environment has required reviewers": PASS textually (workflow-tf-apply.md Environment row). Under rule 16 / F25 that gate does not exist on a Team private repo (see T-1).
- must: caller concurrency `terraform-prod-network`, `cancel-in-progress: false`; `use_lockfile = true`, tfbackend with per-component key, versioning: PASS.
- must: setup-terraform SHA dfe3c3f8... + "1.17.1", upload v7.0.2 / download v8.0.2 SHAs, login placeholder naming `federating-github-actions-aws-oidc`: PASS.
- must_not: no -auto-approve, no dynamodb-only, no default retention, no tags, no apply in ci: OK.

## S2 OCI native backend - PASS
- `backend "oci"`, Terraform 1.12.0+, S3-compatible route deprecated, `init -migrate-state` with "exact procedure ... not on the pages read (unverified)" (state-backends.md). `cloud: oci`, API key default, token exchange as medium-confidence option (Ask First). No credentials in `-backend-config` (Never Do row 5, N5). must_not OK.
- Note: the answer cannot name the environment of the OCI credentials consistently, see T-2.

## S3 apply on pull_request - PASS
- Declines via Never Do row 6, N6, SKILL.md "ci-infra.yml (pull_request, never applies)"; offers preview comment, plan-only tests, merge-time apply; sandbox dispatch workflow is not text-backed but not required by must_not. `id-token: write` is job-level in ci-infra (OK).

## S4 PR artifact / -auto-approve - PASS
- Refuses -auto-approve (N1: "The approver approves something that is never shown"). Trap section: needs `github-token` and `run-id`, merge commit differs from PR head, stale plan official behaviour (unverified, U1/I1). Default fresh plan on merge commit; Ask First row asks whether reviewers must approve the PR plan itself. Retention 1 day. must_not OK.

## S5 Required reviewers on private Team - PASS on criteria, dead end in practice
- States "On GitHub Free, Pro or Team they work only in public repositories", Ask First "Which GitHub plan owns this private repository?" and `<environment>-plan` vs `<environment>` separation (Contract table). Does not promise the gate. OK.
- But the skill supplies no alternative: no plan-variants blueprint, no statement that the gate becomes PR review on protected main (rule 16 DEFAULT), no Free variant. The answer must stop at a question, or fall back on the unused `environment: prod # required reviewers` snippet in always-do-patterns.md.

## Findings
- T-1 (HIGH; same family as tracked F-010 but worse): the whole skill is still built on required reviewers as the apply gate (SKILL.md Always Do bullet 10 "Reference an environment with required reviewers on the apply job"; always-do-patterns.md "Saved plan only ... the human approval is the environment review" and "Environment gate on apply: required reviewers configured on this environment"; `_tf-apply.yml` Contract "released only after a required reviewer approves"; evaluation-scenarios S1). Rule 16 / F25 / F39 say this does not work on private Pro/Team. SKILL.md contradicts itself: its own Ask First row says reviewers work only in public repos. No Free/Pro variant exists. The evaluation scenarios S1 and S5 also test the old model, so a response that follows rule 16 (approval = PR review of the rendered plan on protected main) would be judged wrong against S1 ("environment has required reviewers"). Fix direction: plan-variants blueprint like the three siblings, rewrite the Always Do bullet, scenarios S1/S5.
- T-2 (MEDIUM, cross-skill contract): the plan job uses `environment: ${{ inputs.environment }}-plan` for both PR preview and merge plan. aws-oidc defines roles/environments `<env>` and `<env>-pr` (trust `environment:<env>-pr`); oci defines `oci-pr`, `oci-dev`, `oci-prod`; composing plan-variants says `<env>-pr`. No sibling defines `<env>-plan`, so the AWS role trust and OCI environment names do not exist for the plan job. Rule 13 names the PR environment `<env>-pr`. Rule 16 also sets deployment branch policy `main` on environments, which would reject a PR-branch job that targets `prod-plan` (aws-oidc flags this as unverified).
- T-3 (MEDIUM): merge-time plan runs `-lock=true` with the read-only `<env>-plan` credentials (workflow-tf-plan.md; `LOCK="-lock=true"` unless preview). The same skill states the S3 lock file needs `s3:PutObject` and `s3:DeleteObject`, and federating-github-actions-oci says "A read-only user cannot write the lock object ... belongs to the Terraform skill". Neither sibling defines a plan role that can lock, so the cd-infra plan job fails to lock on both clouds, or the user silently uses the deploy credentials.
- T-4 (MEDIUM): `_tf-apply.yml` has no checkout; it downloads the tarball and extracts it. The login composites (`./.github/actions/cloud/login-aws`, `login-oci`) are local actions that need the repo on disk (aws-oidc login-composite-action.md Notes: "the calling job checks out the repository first"). Replacing the "Cloud login (placeholder)" step with the composite fails in the apply job. Fix: add a checkout before the login or state it in the placeholder comment.
- T-5 (LOW, tracked F-011, same as described): `uses: ./<repo-workflows-dir>/_tf-plan.yml` in workflow-callers.md still violates rule 15; the explanatory note exists. The `cloud` input is still unused by any step except the placeholder comment (F-006 as described). No Verification Loop section (rule 14 / F-001 as described). Blueprints without Contents list (F-003 as described).
- Fact checks: setup-terraform dfe3c3f8... (F2), checkout (F10), upload (F23), download (F24), Terraform 1.17.1 (F1) all match. No action pinned by tag.
