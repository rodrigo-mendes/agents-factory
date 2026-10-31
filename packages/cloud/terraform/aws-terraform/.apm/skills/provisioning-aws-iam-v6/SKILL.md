---
name: provisioning-aws-iam-v6
description: "IAM Terraform (aws 6.x, global): roles, policies, OIDC providers, users, groups, password policy, trust policies. Use when writing HCL for IAM. Not for KMS key policies, Organizations SCPs, Cognito."
---

# Provisioning AWS IAM with Terraform — hashicorp/aws 6.x

> Version lock: every claim applies to **hashicorp/aws 6.x** (reference 6.69.0) + **Terraform ~> 1.16** only.
> Research date **2026-10-14**. Claims tagged (unverified) or (medium confidence) were not fully confirmed
> against an official page.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| Terraform CLI | **1.16.6** — current stable; 1.17.0-rc2 exists, do not target | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | **6.69.0** — current; 6.70.0 "Unreleased" | https://github.com/hashicorp/terraform-provider-aws/releases |
| aws v7 | Not released — v7 planned; upgrade guide lists removals | https://releases.hashicorp.com/terraform-provider-aws/ |
| 6.57.0 | **Withdrawn** from GitHub and Registry — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Provider constraint | `~> 6.69` (root modules); `>= 6.0` (reusable modules) | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| CLI constraint | `~> 1.16` | https://developer.hashicorp.com/terraform/language/terraform |
| `inline_policy` / `managed_policy_arns` | **Deprecated since 5.68.0 / 5.72.0** — still present in 6.x, not removed | https://github.com/hashicorp/terraform-provider-aws/releases/tag/v5.68.0 |
| IAM is a global service | `aws_iam_*` resources are non-region-aware — never set `region =` on them | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |
| `data.aws_region.current.name` | **Deprecated in 6.0** — use `.region` attribute instead | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- 1.17.0-rc2 exists; do not target it. Re-verify when starting new work.
- 6.57.0 is permanently withdrawn; any pinned constraint that includes it will fail init.
- v7 is planned; breaking changes documented in the v6 upgrade guide already mention v7 removals.

**Version lock:** this skill locks to the **6.x major line** (suffix `-v6`), reference 6.69.0.
A new major is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Role and policy patterns: [terraform block, aws_iam_role, policies, exclusive resources](./blueprints/always-do-roles-policies.md)
- Testing and CI: [terraform test with mock_provider, CI sequence](./blueprints/always-do-testing.md)
- OIDC / users / groups / password policy: [OIDC provider, users, groups, access keys, password policy](./blueprints/always-do-oidc-users.md)
- Never-do — roles/policies: [policy_attachment, inline_policy, mixing mechanisms, admin wildcard](./blueprints/never-do-roles-policies.md)
- Never-do — identity/provider: [region on IAM, deprecated data.aws_region, thumbprint, access keys in state](./blueprints/never-do-identity.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `~> 6.69` (root) or `>= 6.0` (module) and `~> 1.16` for the CLI constraint** in every `terraform {}` block.
  See [roles-policies §1](./blueprints/always-do-roles-policies.md#1-terraform-block-and-s3-backend).
- **Use `use_lockfile = true` on the S3 backend** — `dynamodb_table` is deprecated and will be removed.
  See [roles-policies §1](./blueprints/always-do-roles-policies.md#1-terraform-block-and-s3-backend).
- **Never set `region =` on `aws_iam_*` resources** — IAM is a global service, non-region-aware. Using `region` causes an unsupported-argument error.
  See [never-do-identity §1](./blueprints/never-do-identity.md#1-setting-region-on-iam-resources).
- **Use `aws_iam_role_policy` + `aws_iam_role_policies_exclusive` for inline policies** — `inline_policy` on `aws_iam_role` is deprecated (since 5.68.0).
  See [roles-policies §3](./blueprints/always-do-roles-policies.md#3-inline-policies-with-exclusive-management).
- **Use `aws_iam_role_policy_attachment` + `aws_iam_role_policy_attachments_exclusive` for managed policies** — `managed_policy_arns` on `aws_iam_role` is deprecated (since 5.72.0).
  See [roles-policies §4](./blueprints/always-do-roles-policies.md#4-managed-policy-attachments-with-exclusive-management).
- **Use `jsonencode()` or `data.aws_iam_policy_document`** for all policy JSON — both are first-class; pick one per project and stay consistent. Neither is recommended over the other by official docs.
  See [roles-policies §2](./blueprints/always-do-roles-policies.md#2-policy-document-patterns).
- **Include ALL co-managed resource names/ARNs in `*_exclusive` resource lists** — anything not listed is silently removed on apply.
  See [roles-policies §3](./blueprints/always-do-roles-policies.md#3-inline-policies-with-exclusive-management).
- **Scope GitHub OIDC trust with `sub` condition** — IAM rejects any trust policy for the GitHub provider if the `sub` condition is missing, is a wildcard-only value, or is null.
  See [oidc-users §6](./blueprints/always-do-oidc-users.md#6-github-actions-oidc-provider-and-trust-role).
- **Use `.region` attribute from `data.aws_region`**, not `.name` — `.name` is deprecated in 6.0.
  See [never-do-identity §3](./blueprints/never-do-identity.md#3-using-deprecated-dataaws_regioncurrentname).
- **Run `terraform test` with `mock_provider "aws"` and `command = plan`** for CI-safe unit tests.
  See [testing §5](./blueprints/always-do-testing.md#5-terraform-test-and-ci).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Exclusive vs non-exclusive policy management | Exclusive (`*_exclusive` resources): removes any out-of-band inline/managed policy; use when Terraform is the sole manager. Non-exclusive (`aws_iam_role_policy` / `aws_iam_role_policy_attachment`): tolerates out-of-band additions; use for shared roles. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role_policies_exclusive.html.markdown)) | "Should Terraform have exclusive control of this role's inline/managed policies, or will policies be managed outside Terraform?" |
| `aws_iam_policy_attachment` vs role/user/group-scoped attachments | `aws_iam_policy_attachment` creates account-wide exclusive attachments — every holder must be declared in one resource. `aws_iam_role_policy_attachment` is role-scoped and avoids that blast radius. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_policy_attachment.html.markdown)) | "Is this policy shared across roles/users/groups in one account? If yes, use role/user/group-scoped attachment resources instead of aws_iam_policy_attachment." |
| Permissions boundary scope | Boundaries cap effective permissions for a user or role; they do NOT apply to same-account grants to IAM-user ARNs or role-session ARNs in resource-based policies. ([source](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html)) | "Does this role/user need a permissions boundary? Confirm boundary ARN and whether resource-based policy grants to the principal need to be limited." |
| GitHub OIDC `thumbprint_list` | AWS ignores configured thumbprints for GitHub, Auth0, GitLab, Google and S3-hosted JWKS providers — it uses its own trusted root CA library. For other providers, IAM retrieves the thumbprint automatically if the list is omitted. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_openid_connect_provider.html.markdown)) | "Is this OIDC provider GitHub, Auth0, or GitLab? If yes, thumbprint_list may be omitted. For custom providers, supply the thumbprint." |
| IAM user password policy | Destroy behavior is not documented (U5). Expiry changes take effect immediately on existing passwords. ([source](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_passwords_account-policy.html)) | "Should the password policy be managed by Terraform? Confirm that an immediate expiry change on existing passwords is acceptable." |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Set `region =` on any `aws_iam_*` resource — IAM is a global service; the argument is unsupported. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown)) | Omit `region` on all `aws_iam_*` resources |
| Use `id@region` import IDs for IAM resources — region-scoped import IDs are only for regional resources. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown)) | Import IAM resources by name or ARN only (no `@region` suffix) |
| Use `inline_policy` or `managed_policy_arns` on `aws_iam_role` — deprecated since 5.68.0 / 5.72.0; incompatible with the separate attachment resources, causing "resource cycling and/or errors". ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role.html.markdown)) | `aws_iam_role_policy` + `aws_iam_role_policies_exclusive`; `aws_iam_role_policy_attachment` + `aws_iam_role_policy_attachments_exclusive` |
| Mix `aws_iam_policy_attachment` with `aws_iam_role_policy_attachment` on the same role — causes permanent diff. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role_policy_attachment.html.markdown)) | Use only one attachment mechanism per role |
| Use `aws_iam_policy_attachment` when the policy is shared across multiple roles/users/groups managed by separate resources — it revokes the policy from every holder not listed. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_policy_attachment.html.markdown)) | Use `aws_iam_role_policy_attachment`, `aws_iam_user_policy_attachment`, or `aws_iam_group_policy_attachment` |
| Use `"*"` action on `"*"` resource in a customer managed policy — violates Security Hub IAM.1 (admin-access check). ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/iam-controls.html)) | Scope actions and resources to least privilege |
| Omit the `sub` condition from a GitHub OIDC trust policy, or use only a wildcard — IAM rejects the create/update. ([source](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html)) | Always include a non-wildcard `token.actions.githubusercontent.com:sub` condition |
| Use `data.aws_region.current.name` in ARN interpolation — `.name` is deprecated in 6.0. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown)) | `data.aws_region.current.region` |
| Store long-term access keys for human users or for workloads that can use roles — violates IAM best practices. ([source](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)) | Use IAM roles with temporary credentials; `aws_iam_access_key` secret is written to state in plaintext |
| S3 backend with `dynamodb_table` — deprecated, will be removed. ([source](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` for native S3 locking |
| Pin `version = "6.57.0"` — withdrawn from GitHub and the Registry. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` or any non-withdrawn patch |

## Quick Reference

Sources fetched 2026-10-14.

| Aspect | Value | Source |
|---|---|---|
| Provider constraint (root) | `~> 6.69` | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| CLI constraint | `~> 1.16` | https://developer.hashicorp.com/terraform/language/terraform |
| S3 locking | `use_lockfile = true` (`dynamodb_table` deprecated) | https://developer.hashicorp.com/terraform/language/backend/s3 |
| IAM is global | Never set `region =` on `aws_iam_*`; never use `@region` import IDs | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |
| `inline_policy` deprecated since | 5.68.0 — still present in 6.x, not removed | https://github.com/hashicorp/terraform-provider-aws/releases/tag/v5.68.0 |
| `managed_policy_arns` deprecated since | 5.72.0 — still present in 6.x, not removed | https://github.com/hashicorp/terraform-provider-aws/releases/tag/v5.72.0 |
| Policy JSON | `jsonencode()` or `data.aws_iam_policy_document` — both equal, neither preferred | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role.html.markdown |
| `data.aws_region` | Use `.region`, not `.name` (`.name` deprecated 6.0) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown |
| GitHub OIDC `thumbprint_list` | Optional for GitHub — AWS uses own CA library | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_openid_connect_provider.html.markdown |
| GitHub OIDC `sub` condition | Required, non-wildcard — IAM rejects if missing or wildcard-only | https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html |
| `aws_iam_access_key` state | `secret` written to state in plaintext | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_access_key.html.markdown |
| Security Hub IAM.1 | No `Action *` on `Resource *` in customer managed policies | https://docs.aws.amazon.com/securityhub/latest/userguide/iam-controls.html |
| Security Hub IAM.2 | Attach policies to groups/roles, not users | https://docs.aws.amazon.com/securityhub/latest/userguide/iam-controls.html |
| Security Hub IAM.15 | Password minimum length ≥ 14 | https://docs.aws.amazon.com/securityhub/latest/userguide/iam-controls.html |
| `terraform test` CI | `init -backend=false`, `validate -json`, `plan -detailed-exitcode -input=false -out=tfplan` | https://developer.hashicorp.com/terraform/cli/commands/plan |

## 5.x → 6.x Migration (IAM)

Breaking changes in 6.0.0 that affect IAM work
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-14):

- **`data.aws_region`**: `name` attribute deprecated → use `.region`.
- **`aws_redshift_service_account`**: removed — use a service principal name in IAM policies instead.
- **No breaking changes** for `aws_iam_role`, `aws_iam_policy`, `aws_iam_user`, `aws_iam_group`, `aws_iam_openid_connect_provider`, or the `*_exclusive` resources.
- `inline_policy` and `managed_policy_arns` remain deprecated (since 5.68.0 / 5.72.0) — not newly deprecated in 6.x, not removed.

Upgrade path: move to latest 5.x, get a clean plan, set `~> 6.0`, run `terraform init -upgrade`.

## External Resources

All fetched 2026-10-14.

- Provider releases: https://github.com/hashicorp/terraform-provider-aws/releases
- CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- Enhanced region support (global services): https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
- IAM best practices: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- IAM OIDC providers: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html
- GitHub OIDC trust: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html
- Permissions boundaries: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html
- Password policy (AWS): https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_passwords_account-policy.html
- Security Hub IAM controls: https://docs.aws.amazon.com/securityhub/latest/userguide/iam-controls.html
- Terraform S3 backend: https://developer.hashicorp.com/terraform/language/backend/s3
- Terraform test: https://developer.hashicorp.com/terraform/language/tests
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
