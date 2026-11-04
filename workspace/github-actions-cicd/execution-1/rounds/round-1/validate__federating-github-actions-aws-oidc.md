# Validate: federating-github-actions-aws-oidc (P6 r1, 2026-10-30)

Score: 90.0 (1 HIGH, 1 MEDIUM, 3 LOW). SKILL.md 130 lines. F3 SHA e1253824... correct everywhere; checkout F10 correct. Verification Loop, 3 tiers, 5 scenarios, register counts (9/0/4/5) all correct. Rule 13/16 model consistent with oci and composing.

## HIGH
- H1 (B3/cross-skill, blueprints/login-composite-action.md:38): the composite hard-codes `role-duration-seconds: 900` and exposes no input for it (notes :43 list only three inputs). Credentials die after 15 minutes. Terraform apply jobs allow 60 minutes (terraform `_tf-apply` timeout 60) and the terraform skill's login placeholder points at this composite; Java/Lambda releases can exceed 15 minutes too. SKILL.md:57 only says "between 900 and the role's maximum". Fix: add a `duration-seconds` input (default 3600 unless chained), justify the constant, and say the role max session must cover the job.

## MEDIUM
- M1 (rule 11): "created on or after 2026-07-15" at SKILL.md:21,53 and unverified-and-risks.md:10; F26 says "created after 2026-07-15" (composing, oci and java say "after"). Fix: align to F26.

## LOW
- L1 (A4, SKILL.md:87; login-composite-action.md:3): "F3" fact ID and "(F3 pin)" are unresolvable at run time.
- L2 (rule 11, always-do-patterns.md:19): "AWS CLI v2.39.2 reference" has no source and is not in the facts file.
- L3: `actions/checkout` without `persist-credentials: false` (always-do-patterns.md:64, never-do-patterns.md:52, login-composite-action.md:64); composing examples set it.

## Note for terraform
This skill defines roles `-deploy` and `-pr-read` and environment `<env>-pr` only; the terraform skill's `<env>-plan` has no counterpart (see terraform M2).
