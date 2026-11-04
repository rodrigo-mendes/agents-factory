# Test P6 r1 - federating-github-actions-aws-oidc

Evaluator: skill-evaluator (own-context simulation, no sub-agents). Date 2026-10-30. Source read: packages/github-actions-cicd/.apm/skills/federating-github-actions-aws-oidc/ (SKILL.md + all blueprints except unverified-and-risks.md).

Verdict: 5 PASS, 0 FAIL. Two cross-skill defects (A-1, A-2).

## S1 Deploy role per environment on Team - PASS
- Asks/confirms plan and age: Ask First "GitHub plan"; trust-policies-by-plan.md "Ask the plan first".
- Provider audience `sts.amazonaws.com`, no thumbprint (Always Do bullets 1-2); roles `gha-<app>-<env>-deploy` / `-pr-read`, `StringEquals` on aud and sub, PR role `environment:<env>-pr` (trust table).
- Environment with branch policy `main`; approval "is the PR review before merge", not required reviewers (trust-policies-by-plan.md "Plan model": "Required reviewers ... are public-repository or Enterprise features (upgrade path only)"). Matches rule 16.
- Composite `./.github/actions/cloud/login-aws`, job-level `id-token: write`, SHA e1253824... # v6.3.0, HCL delegated to `provisioning-aws-iam-v6`: PASS (always-do-patterns.md "Job-level id-token"; SKILL.md Scope).
- must_not: no tag, no single role, no workflow-level id-token, no required-reviewer promise, no HCL copied: OK.

## S2 Repo created after 2026-07-15 - PASS
- Immutable sub vs legacy side by side (trust-policies-by-plan.md "Legacy and immutable sub formats"), environment string "(unverified)", "Read the real sub from a decoded test token". Troubleshooting table lists job shape, custom template, wrong provider account (login-composite-action.md). Wildcard not suggested; thumbprint not suggested.

## S3 Long-lived access keys - PASS (one expected bullet not skill-backed)
- Declines: Never Do row 3 / N3 ("A leaked key stays valid until rotated"; README recommends temporary credentials). Shortest keyless path = provider + one role + composite, all present. The "ask what blocks OIDC" step is not in the skill text; harmless.

## S4 StringLike repo:ORG/* and PR on prod - PASS
- N1 and Never Do row 1: shared issuer, IAM rejects wildcard-only value; "wildcard is acceptable only on a read-only role, and then only per repository". Never Do row 2 / N2: PR job on `<env>-pr` or no environment; `:pull_request` form in trust page. `aud` is pinned in every sample. OK.

## S5 Free private - PASS
- Free: no environments; roles trust `ref:refs/heads/main`, PR role `:pull_request`; caveat "dev and prod cannot be separated by `sub` alone", separate by account or repository, "accepted risk, never silent"; sub-template route with "(unverified)" availability on Free. must_not OK.

## Findings
- A-1 (MEDIUM, cross-skill): the login composite hard-codes `role-duration-seconds: 900` and exposes no duration input (login-composite-action.md; the Notes list only `allowed-account-ids`, `role-chaining`, `mask-aws-account-id` as reasons to call the action directly). The Terraform apply job has `timeout-minutes: 60` and a CD deploy can run longer than 15 minutes; the session expires mid-apply. Fix: add a `duration-seconds` input or name duration among the reasons to bypass the composite.
- A-2 (MEDIUM, cross-skill): environment/role naming. This skill and composing plan-variants use `<env>` and `<env>-pr`. automating-terraform-github-actions-v1-17 uses `<env>-plan` for the plan job (read credentials, also used on merge, with `-lock=true`). There is no role for it here: only `deploy` and `pr-read`; the pr-read role has no S3 lock-object rights, so a merge-time plan with `use_lockfile = true` cannot lock. Define a `plan` role (or state that merge plan uses the deploy role) in the trust table.
- A-3 (LOW): the composite requires a prior checkout (Notes). The Terraform `_tf-apply.yml` job has none; see the terraform report T-4.
- A-4 (LOW): N2 sample uses environment `prod-pr` with deployment branch policy `main` on `prod`; behaviour of branch policy for `pull_request` events on `prod-pr` is flagged (unverified). Acceptable, noted.
- Fact checks: configure-aws-credentials v6.3.0 SHA e1253824... (F3), checkout (F10) match; immutable sub text matches F26; Verification Loop present (rule 14). Rule 16 text identical in meaning to composing, oci, java.
