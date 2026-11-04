# Validate r2: federating-github-actions-aws-oidc (2026-10-30). Score 97.5

H1 FIXED: login-composite-action.md:30-47 input `role-duration-seconds` default 3600, justified; chained cap noted.
M1 FIXED: "created after 2026-07-15" at SKILL.md:21,53.
L1 FIXED (no "F3" ids). L2 FIXED (no v2.39 reference). L3 FIXED: persist-credentials false at login-composite-action.md:71, never-do:54, always-do:66.

NEW
- MEDIUM (rule 17 / cross-skill): the skill defines `-deploy` and `-pr-read` roles and `<env>-pr` only. The images skill uses `vars.ECR_PUSH_ROLE_ARN` in `<env>-publish` (registry-credentials.md:21; always-do-patterns.md:63) and trusts `environment:<env>-publish` "per F26 in this skill", but this skill has no `-publish` role, trust row or trust-policies-by-plan.md entry. Fix: add the publish role (push-only ECR policy, trust `environment:<env>-publish`) here.
