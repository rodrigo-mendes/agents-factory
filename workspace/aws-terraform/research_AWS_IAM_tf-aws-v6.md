# Research — AWS IAM with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-14**. Status: **COMPLETE** (unit `iam`, P4 fan-out, single researcher, no sub-agents).
> Registry pages render JS-only (F12); the upstream raw markdown in `hashicorp/terraform-provider-aws`
> (`main`) is the authoritative source for resource docs. Shared facts are cited by ID from
> `workspace/aws-terraform/_family_facts_v6.md` (F1–F13) and were not re-researched.
> Coverage checklist only (not a source): `workspace/terraform/research_AWS_IAM_aws-v6.x.md` (6.47.0, Terraform 1.7, EOL).

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | 1.16.6 latest stable; target `required_version = "~> 1.16"`; 1.17.0-rc2 pre-release, do not target | F1, F2 |
| hashicorp/aws | 6.69.0 latest; target `version = "~> 6.69"`; no 7.x | F3 |
| Withdrawn | 6.57.0, never pin | F4 |
| Constraint style | root modules `~>`; reusable modules `>=` minimum only | F6 |
| Identity import | `identity` block requires Terraform >= 1.12.0, satisfied by 1.16 | F11 |
| **IAM and `region`** | **IAM is a global service. `aws_iam_*` resources are listed as "non-region-aware", so they do NOT take the per-resource `region` argument that F5 describes.** The guide also lists `aws_rolesanywhere_*`, `aws_caller_identity` and the policy-document data sources as non-region-aware | [10] (2026-10-14) |
| Exclusive resources origin | `aws_iam_role_policies_exclusive` was added in **5.68.0** (#39203), and `inline_policy` was deprecated in the same release. `aws_iam_role_policy_attachments_exclusive` was added in **5.72.0** (#39718), and `managed_policy_arns` was deprecated in the same release. Neither is new in 6.x | [6], [7] (2026-10-14) |

Recommended root-module block (F1/F3/F6):

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

> **Scope note on F5:** F5 says every resource accepts `region`. The enhanced-region-support guide
> makes an exception for global services, IAM included [10]. IAM skills must not emit `region =` on
> `aws_iam_*` resources and must not use `id@region` import IDs for them. F5 itself is still correct for regional services.

## 2. Provider 6.x changes for IAM

**6.0.0 upgrade guide (F13)** [5] (2026-10-14):
- The guide lists **no** `aws_iam_*` resources or data sources, and does not mention `inline_policy` or `managed_policy_arns`. Both arguments are **still deprecated, not removed**, in 6.x (confirmed on the current `iam_role` page [11]).
- Adjacent IAM authoring impact: the `aws_region` data source's `name` attribute "has been deprecated. Use `region` instead." Policies that build ARNs from `data.aws_region.current.name` should use `.region` instead [5].
- `aws_redshift_service_account` was removed. The guide notes "AWS recommends that a service principal name should be used instead of an AWS account ID in any relevant IAM policy" [5].

**CHANGELOG 6.48.0 → 6.69.0, IAM scope** [8] (2026-10-14). No BREAKING entries:
- 6.53.0: `aws_iam_user` handles `InvalidAction` in partitions where access-key cleanup is unsupported (#48473).
- 6.54.0: `aws_iam_policy_attachment` gains resource identity support (#48639). Only part of 6.54.0 was visible (see L1).
- 6.58.0: `aws_iam_user` retries destroy on conflicts and ignores non-errors during destroy (#49260).
- 6.61.0: new list resource `aws_iam_instance_profile` (#49576).
- 6.65.0: new list resources `aws_iam_group` (#49994) and `aws_iam_user_policy` (#49993). Both gain resource identity.
- 6.66.0: new list resource `aws_iam_openid_connect_provider` (#50024). The NOTE says it is "best-effort", is hard to test, and asks for community testing.
- No IAM entries in 6.48–6.52, 6.55–6.57.1, 6.59–6.60, 6.62–6.64, 6.67–6.69.

## 3. Roles and role policies

Source for each: `https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/<name>.html.markdown` (2026-10-14).

### aws_iam_role [11]
- **Required:** `assume_role_policy`. Build it with `jsonencode()` or `data.aws_iam_policy_document`. An `aws_iam_policy` resource cannot be used here.
- **Optional:**
  - `description`
  - `force_detach_policies`, default `false`
  - `max_session_duration`, 1 to 12 hours, default 1 hour
  - `name` or `name_prefix`. Both **force new**, and they conflict with each other. If neither is set, Terraform assigns a random name.
  - `path`. The page states no default (U1).
  - `permissions_boundary` (policy ARN)
  - `tags`. Tags override provider `default_tags` on matching keys.
- **`inline_policy`: DEPRECATED.** Use `aws_iam_role_policy` instead, plus `aws_iam_role_policies_exclusive` if you want exclusive management. An empty `inline_policy {}` removes out-of-band inline policies.
- **`managed_policy_arns`: DEPRECATED.** Use `aws_iam_role_policy_attachment` instead, plus `aws_iam_role_policy_attachments_exclusive` for exclusivity. `managed_policy_arns = []` detaches all managed policies.
- **NOTE (do not mix):** `inline_policy` and `managed_policy_arns` give the role exclusive control of that policy type. They are incompatible with `aws_iam_policy_attachment`, `aws_iam_role_policy_attachment` and `aws_iam_role_policy`. Mixing them causes "resource cycling and/or errors".
- **NOTE (rename):** If you use `aws_iam_policy_attachment` and change the role's `name` or `path`, set `force_detach_policies = true` and apply it first. Otherwise you get `DeleteConflict`. `aws_iam_role_policy_attachment` has no such requirement.
- **Import:** by role `name`. Identity import takes `name` (required) and `account_id` (optional). No timeouts section.

### aws_iam_role_policy (inline) [12]
- **Required:** `role` (role name) and `policy` (JSON).
- **Optional:** `name` or `name_prefix` (conflict). If neither is set, Terraform assigns a random name.
- **NOTE:** "incompatible with using the aws_iam_role resource inline_policy argument". Using both causes a permanent difference.
- **Import:** `role_name:role_policy_name`. Identity import takes `role` + `name` (required) and `account_id` (optional).

### aws_iam_role_policy_attachment [13]
- **Required:** `role` and `policy_arn`.
- **NOTE:** Never combine with `aws_iam_policy_attachment`, or with `aws_iam_role.managed_policy_arns` on the same role. Either causes a permanent difference.
- **Import:** `<role>/<policy_arn>`, e.g. `test-role/arn:aws:iam::xxxxxxxxxxxx:policy/test-policy`. Identity import takes `role` + `policy_arn` (required) and `account_id` (optional).

### aws_iam_role_policies_exclusive [14]
- **Required:** `role_name` and `policy_names` (inline policy names).
- **Apply:** removes any inline policy on the role that is not listed, "including removal of inline policies which are not explicitly configured". `policy_names = []` removes all inline policies.
- **Destroy:** stops reconciliation. The policies stay on the role.
- **WARNING:** Include the names of any co-managed `aws_iam_role_policy` resources in `policy_names`, or there will be persistent drift.
- Reconciliation happens only at `apply`. It does not stop out-of-band additions in between.
- **Import:** by role name.

### aws_iam_role_policy_attachments_exclusive [15]
- **Required:** `role_name` and `policy_arns`.
- **Apply:** detaches unlisted managed policies. `policy_arns = []` detaches all of them.
- **Destroy:** does not detach the configured policies.
- **WARNING:** Include the ARNs of co-managed `aws_iam_role_policy_attachment` resources, or they will drift.
- **Import:** by role name.

### aws_iam_instance_profile [16]
- **Required:** none. `role` is optional.
- `name` or `name_prefix`: force new, and they conflict.
- `path` defaults to `/`. The page does not list it as force-new.
- **NOTE:** `name` must be unique regardless of `path` or `role`. Reusing a name gives `EntityAlreadyExists`.
- **Import:** by `name`. Identity import takes `name` and optionally `account_id`.

### aws_iam_service_linked_role [17]
- **Required:** `aws_service_name` (e.g. `elasticbeanstalk.amazonaws.com`). Forces new.
- **Optional:** `custom_suffix` (forces new; not supported by every service), `description` (in-place update), `tags`.
- **Import:** by role ARN, e.g. `arn:aws:iam::123456789012:role/aws-service-role/elasticbeanstalk.amazonaws.com/AWSServiceRoleForElasticBeanstalk`. Identity import takes `arn`.

## 4. Managed policies and policy documents

### aws_iam_policy [18]
- **Required:** `policy` (JSON).
- **Optional:**
  - `name` or `name_prefix`: force new
  - `description`: **forces new**
  - `path`: default `"/"`
  - `delay_after_policy_creation_in_ms`: no default stated
  - `tags`
- **Exports:** `arn` (also the `id`), `policy_id`, `attachment_count`, `tags_all`.
- **NOTE:** Use `jsonencode()` or `aws_iam_policy_document`.
- **Import:** by policy ARN. Identity import takes `arn`.

### aws_iam_policy_attachment (avoid) [19]
- **WARNING:** It creates "**exclusive** attachments" across the whole account. Every user, role and group that holds the policy must be declared in one resource. Any other holder, including holders set through other Terraform resources, has the policy revoked.
- Conflicts with `aws_iam_{role,user,group}_policy_attachment` (permanent diff) and with `aws_iam_role.managed_policy_arns`.
- Reference `policy_arn` from the policy resource. Building the ARN as a string can cause `DeleteConflict` or `NoSuchEntity` errors.
- Import is not documented on the page (U2). The 6.54.0 CHANGELOG adds resource identity [8].

### data.aws_iam_policy_document vs jsonencode [20]
- Generates the JSON policy document. Exports `json` and `minified_json`.
- Using it is optional: "It is also valid to use literal JSON strings", or `file()`.
- The data-source page does **not** rank it against `jsonencode()`. The resource pages (`iam_role`, `iam_role_policy`, `iam_policy`) recommend **either** `jsonencode()` **or** this data source, to avoid JSON formatting and whitespace issues [11][12][18]. Treat both as first-class choices.
- **Arguments:**
  - `version`: default `2012-10-17` (`2008-10-17` also valid)
  - `policy_id`
  - `statement` blocks
  - `source_policy_documents`: merged; their `sid`s must be unique
  - `override_policy_documents`: a statement with a matching `sid` replaces the earlier one. "Statements without a `sid` cannot be overridden."
- **Statement block:**
  - `sid`
  - `effect`: default `Allow`
  - `actions` / `not_actions`
  - `resources` / `not_resources`: the two conflict
  - `principals` / `not_principals`: `type`, `identifiers`
  - `condition`: `test`, `variable`, `values`. Multiple conditions are ANDed.
- **Interpolation:** write AWS policy variables as `&{aws:username}`, not `${…}`.
- It is a non-region-aware data source [10].

## 5. Users, groups, access keys, OIDC, password policy

### aws_iam_user [21]
- **Required:** `name`. Allowed characters are alphanumerics and `=,.@-_`. Names are case-insensitive.
- `path`: default `/`.
- `permissions_boundary`: optional.
- **`force_destroy`** (default `false`):
  - With it set, destroy also deletes non-Terraform-managed access keys, login profiles and MFA devices.
  - Without it, destroy fails if such items exist.
  - It takes effect only after an apply has stored it in state. It does nothing if set in the same run that replaces or destroys the user.
- **NOTE:** With `aws_iam_policy_attachment`, changing `name` or `path` needs `force_destroy = true` applied first.
- **Import:** by `name`. Identity import takes `name` and optionally `account_id`.

### aws_iam_group [22]
- **Required:** `name` (case-insensitive, so "ADMINS" conflicts with "admins").
- `path`: default `/`.
- **NOTE:** Manage membership either entirely in Terraform or entirely in the console.
- **Import:** by name. Identity import takes `name` and optionally `account_id`.
- **`aws_iam_group_membership`** [23]:
  - WARNING: "Multiple aws_iam_group_membership resources with the same group name will produce inconsistent behavior!"
  - Use `aws_iam_user_group_membership` for non-exclusive membership.

### Exclusive resources for users and groups [24][25][26][27]
- `aws_iam_user_policies_exclusive` (`user_name`, `policy_names`) and `aws_iam_group_policies_exclusive` (`group_name`, `policy_names`) manage inline policies.
- `aws_iam_user_policy_attachments_exclusive` (`user_name`, `policy_arns`) and `aws_iam_group_policy_attachments_exclusive` (`group_name`, `policy_arns`) manage managed-policy attachments.
- They behave like the role versions:
  - unlisted items are removed on apply
  - `[]` removes everything
  - destroy leaves the policies in place
  - co-managed resources must be listed, or there will be drift
- Import is by user or group name.

### aws_iam_access_key (guidance) [28]
- **Required:** `user`. **Optional:** `pgp_key`, `status` (default `Active`; `Active` or `Inactive`).
- **`secret` is written to the state file in plaintext.** `ses_smtp_password_v4` is derived from the secret. How it is stored is not stated, so treat it the same way (M1).
- Setting `pgp_key` (raw key or `keybase:<user>`) fills `encrypted_secret` instead. The doc notes this prevents using the secret in automation.
- On import, `secret`, `encrypted_secret`, `key_fingerprint`, `pgp_key` and the SES passwords are unavailable ("cannot be read from the IAM API").
- **AWS guidance** [31]: prefer temporary credentials. Use long-term access keys only when roles are impossible (e.g. some third-party clients). Rotate keys when needed, and use "access last used" information to remove keys safely.

### aws_iam_openid_connect_provider (GitHub Actions OIDC) [29][32][33]
- **Required:** `url` (the `iss` claim) and `client_id_list` (audiences; use `sts.amazonaws.com` for GitHub).
- **`thumbprint_list` is OPTIONAL.**
  - For **GitHub**, Auth0, GitLab, Google and S3-hosted JWKS providers, AWS uses its own trusted root CA library. Configured thumbprints are kept but not used.
  - If `thumbprint_list` is omitted for other providers, IAM retrieves the top intermediate CA thumbprint automatically.
  - If you set `thumbprint_list` and later remove it, the original list is kept.
- **AWS limits** [32]:
  - Each OIDC provider URL must be unique in the account.
  - 1–5 thumbprints and 1–100 audiences per provider.
  - The OIDC IdP must be in the same account as the role that trusts it.
  - AWS falls back to thumbprint verification only if it cannot retrieve the TLS certificate or if TLS v1.3 is required.
- **Import:** by provider ARN. Identity import takes `arn`. Whether `url` forces new is not stated (U3).
- **GitHub trust policy** [33]:
  - Principal: `Federated = <oidc provider ARN>`. Action: `sts:AssumeRoleWithWebIdentity`.
  - Condition: `StringEquals` `token.actions.githubusercontent.com:aud = sts.amazonaws.com`.
  - Condition: `token.actions.githubusercontent.com:sub` scoped to org/repo/branch, e.g. `repo:Org/Repo:ref:refs/heads/main` with `StringEquals`, or `repo:Org/Repo:*` with `StringLike`.
  - **IAM rejects any create or update of a trust policy for the GitHub provider when the `sub` key is missing, or when its value is only a wildcard or null.**
  - AWS recommends limiting `sub` to specific repositories or branches, and adding protection rules to GitHub environments.
  - The HCP Terraform provider (`app.terraform.io`, audience `aws.workload.identity`) likewise requires an `app.terraform.io:sub` condition. Without it, IAM and STS deny the request.

### aws_iam_account_password_policy [30][34]
- All arguments are optional:
  - `allow_users_to_change_password`
  - `hard_expiry`
  - `max_password_age`
  - `minimum_password_length`
  - `password_reuse_prevention`
  - `require_lowercase_characters`, `require_numbers`, `require_symbols`, `require_uppercase_characters`
- The provider page states no defaults or ranges (U4).
- Read-only `expire_passwords` is `true` when `max_password_age > 0`.
- **NOTE:** "There is only a single policy allowed per AWS account". The resource overwrites any existing policy. What happens on destroy is not stated (U5).
- **Import ID:** literal `iam-account-password-policy`.
- **AWS ranges** [34]:
  - minimum length 6–128
  - expiry 1–1,095 days; expiry applies **immediately** to existing passwords
  - reuse prevention 1–24
- **AWS default policy:** minimum 8 characters, 3 of 4 character types, passwords never expire.
- The policy does not apply to the root user or to access keys. There is no lockout option, so pair it with MFA.

## 6. Permissions boundaries [35]
- A boundary is a managed policy (AWS or customer managed) that sets the **maximum** permissions for an IAM **user or role**. "It limits the user's permissions but does not provide permissions on its own."
- In Terraform, set it with `permissions_boundary` on `aws_iam_role` or `aws_iam_user` [11][21].
- **Evaluation:**
  - Effective permissions = identity-based policy ∩ boundary. An explicit deny in any policy type wins.
  - With SCPs or session policies, the result is the intersection of all of them.
- **Resource-based policies:**
  - Grants to an **IAM role ARN** are limited by an implicit deny in the boundary.
  - Same-account grants to an **IAM user ARN**, or to a **role-session ARN**, are **not** limited by it.
- **Important:** Do not use `NotPrincipal` + `Deny` in resource policies for principals that have a boundary. It always denies them. Use `ArnNotEquals` with `aws:PrincipalArn` instead.
- **Delegation pattern:**
  - Allow `iam:CreateUser`, `iam:PutUserPermissionsBoundary`, etc. only with the condition `StringEquals iam:PermissionsBoundary = <boundary ARN>`.
  - Deny edits to the boundary policies (`CreatePolicyVersion`, `DeletePolicy`, `SetDefaultPolicyVersion`).
  - Deny `iam:DeleteUserPermissionsBoundary`.
  - The AWS example uses users; the role equivalents (`iam:CreateRole`, `iam:PutRolePermissionsBoundary`) follow the same logic but were not shown on this page (M2).
- AWS best-practice framing: "Use permissions boundaries to delegate permissions management within an account" [31].

## 7. AWS guidance — IAM best practices [31]
Headings, in order:
1. Human users federate through an IdP with temporary credentials. IAM Identity Center is recommended, and account access manager can assign existing roles.
2. Workloads use temporary credentials from IAM roles. Outside AWS, use Roles Anywhere, `AssumeRoleWithSAML`, `AssumeRoleWithWebIdentity` or IoT mTLS.
3. Require MFA, phishing-resistant (passkeys or security keys) where possible.
4. Update access keys when long-term credentials are unavoidable.
5. Protect root user credentials.
6. Apply least privilege.
7. Start with AWS managed policies, then move to customer managed least-privilege policies.
8. Generate policies from CloudTrail activity with IAM Access Analyzer.
9. Regularly remove unused users, roles, permissions, policies and credentials, using last accessed information.
10. Use policy conditions (e.g. TLS-only).
11. Verify public and cross-account access with Access Analyzer.
12. Validate policies with Access Analyzer (100+ checks).
13. Set multi-account guardrails with SCPs and RCPs. These grant nothing on their own.
14. Use permissions boundaries for delegation.

## 8. Security Hub CSPM — IAM controls [36]
| ID | Title (short) | Severity | Config rule / parameters |
|---|---|---|---|
| IAM.1 | No customer managed policy with `"*"` admin (`Action *` on `Resource *`) | High | `iam-policy-no-statements-with-admin-access`; `excludePermissionBoundaryPolicy: true`; checks customer managed policies only |
| IAM.2 | IAM users should not have IAM policies attached | Low | `iam-user-no-policies-check` |
| IAM.3 | Access keys rotated ≤ 90 days | Medium | `access-keys-rotated`; `maxAccessKeyAge 90` |
| IAM.4 | No root user access key | Critical | `iam-root-access-key-check` |
| IAM.5 | MFA for users with a console password | Medium | `mfa-enabled-for-iam-console-access` |
| IAM.6 | Hardware MFA for root | Critical | `root-account-hardware-mfa-enabled` |
| IAM.7 | Strong password policy | Medium | `iam-password-policy`; defaults: upper/lower/symbol/number `true`, `MinimumPasswordLength 8` (custom 8–128); `PasswordReusePrevention` (12–24) and `MaxPasswordAge` (1–90) have no default |
| IAM.8 | Unused user credentials removed | Medium | `iam-user-unused-credentials-check`; `maxCredentialUsageAge 90` |
| IAM.9 | MFA for root | Critical | `root-account-mfa-enabled` |
| IAM.10 | Strong password policy (CIS v1.2 variant: length ≥ 7, reuse 4, max age 90) | Medium | `iam-password-policy` |
| IAM.11–IAM.14 | Require uppercase / lowercase / symbol / number | Medium | `iam-password-policy` |
| IAM.15 | Minimum length ≥ 14 | Medium | `iam-password-policy` |
| IAM.16 | Prevent password reuse | Low | `iam-password-policy` |
| IAM.17 | Passwords expire ≤ 90 days | Low | `iam-password-policy` |
| IAM.18 | Support role exists (`AWSSupportAccess` attached) | Low | `iam-policy-in-use` |
| IAM.19 | MFA for all IAM users | Medium | `iam-user-mfa-enabled` |
| IAM.20 | Avoid use of root user | Low | `use-of-root-account-test` (custom) |
| IAM.21 | Customer managed policies: no service wildcard actions (`s3:*`) | Low | `iam-policy-no-statements-with-full-access`; `excludePermissionBoundaryPolicy True` |
| IAM.22 | User credentials unused 45 days removed | Medium | `iam-user-unused-credentials-check` |
| IAM.23 / IAM.24 / IAM.25 | Access Analyzer analyzers / roles / users tagged | Low | tag parameters |
| IAM.26 | Expired IAM-managed SSL/TLS certificates removed | Medium | — |
| IAM.27 | No `AWSCloudShellFullAccess` attached | Medium | — |
| IAM.28 | Access Analyzer external access analyzer enabled | High | `iam-external-access-analyzer-enabled` |

Terraform implications:
- IAM.1 and IAM.21: no `"*"` actions in `aws_iam_policy`. Boundary policies are excluded from these checks.
- IAM.2: attach policies to groups or roles, not users.
- IAM.7 and IAM.15–17: the "CIS-safe" settings are `minimum_password_length >= 14`, all four `require_*` set to `true`, `password_reuse_prevention` 12–24 and `max_password_age <= 90`. The combination is derived from the controls above (M3).
- IAM.24 and IAM.25: tag roles and users.

## 9. Unverified / medium-confidence items and coverage limits
- U1 `aws_iam_role` `path` default not stated on the provider page. AWS default `/` is assumed but was not verified for roles.
- U2 `aws_iam_policy_attachment` import not documented. Resource identity was added in 6.54.0.
- U3 Whether `aws_iam_openid_connect_provider.url` forces new is not stated.
- U4 `aws_iam_account_password_policy` defaults and ranges are not on the provider page. Use the AWS ranges in §5.
- U5 Behaviour of `aws_iam_account_password_policy` on destroy (revert to the AWS default?) is not stated.
- U6 Release year of 5.68.0 and 5.72.0: the GitHub pages show "19 September" and "15 October" without a year. 2024 is inferred from a linked 5.71.0 date.
- M1 `ses_smtp_password_v4` state storage is inferred to be plaintext like `secret`.
- M2 The role-delegation boundary actions are extrapolated from the AWS user example.
- M3 The "CIS-safe" password-policy combination is derived from the Security Hub controls, not from a single statement.
- M4 Verbatim wording: WebFetch paraphrases, though the substance was confirmed on the raw markdown.
- L1 CHANGELOG [8] was read in two chunks. 6.54.0 straddled the boundary and was only partly visible.
- L2 Raw `main` docs may run slightly ahead of 6.69.0 (registry pages not readable, F12).
- L3 Not covered: `aws_iam_saml_provider`, `aws_iam_virtual_mfa_device`, `aws_iam_user_login_profile`, `aws_iam_signing_certificate`, `aws_iam_organizations_features`, `aws_iam_outbound_web_identity_federation`, `aws_iam_principal_policy_simulation`, Access Analyzer resources and IRSA/EKS Pod Identity.

**Legacy-file claims found wrong** (`workspace/terraform/research_AWS_IAM_aws-v6.x.md`):
1. Wrong: the `*_exclusive` resources are listed as "New_V6_Resources" and `inline_policy`/`managed_policy_arns` as "deprecated in v6.x". In fact they were added, and the arguments deprecated, in **5.68.0 and 5.72.0**. The arguments remain deprecated, not removed, in 6.x [6][7][11].
2. Wrong: the GitHub OIDC pattern hard-codes `thumbprint_list` and calls it "current". In fact `thumbprint_list` is optional and AWS ignores thumbprints for GitHub [29][32].
3. Wrong: it uses `data.aws_region.current.name` in ARNs. `name` is deprecated in 6.0, so use `.region` [5].
4. Wrong: the S3 backend uses `dynamodb_table`. That argument is deprecated, so use `use_lockfile = true` (F7).
5. Unsupported: "`aws_iam_policy_document` … integrates with `terraform validate`" and is "(recommended)" over `jsonencode`. No official page states either. The provider pages present the two as equal options [11][20].
6. Unsupported: `create_before_destroy` "prevents downtime during rename" on a role with a fixed `name`. Not documented. Because `name` forces new and role names are unique, this likely fails with a name conflict (unverified).
7. Wrong: the GitHub OIDC trust example uses `StringLike` for `sub` with an exact ref. That is valid, but AWS's exact-match example uses `StringEquals`. Note that IAM rejects a wildcard-only `sub` [33].

## 10. Security note
- No prompt-injection or instruction-like text aimed at AI agents was found in the fetched pages. The `iam_role` page was explicitly checked, and the saved Security Hub page was grepped for `system-reminder`, "ignore previous" and "assistant", with no matches.
- Search-engine snippets from non-official sites (w3cub, awsfundamentals, pulumi, upbound) appeared in results. They were not used as sources.

## Source Bibliography

All fetched 2026-10-14.

1. `c:\agents\agents-factory\workspace\aws-terraform\_family_facts_v6.md` (F1–F13, shared facts)
2. https://releases.hashicorp.com/terraform/ (via F1/F2)
3. https://github.com/hashicorp/terraform-provider-aws/releases (via F3)
4. https://developer.hashicorp.com/terraform/language/backend/s3 (via F7)
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
6. https://github.com/hashicorp/terraform-provider-aws/releases/tag/v5.68.0
7. https://github.com/hashicorp/terraform-provider-aws/releases/tag/v5.72.0
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/release/5.x/CHANGELOG.md (partially read; truncated)
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role.html.markdown
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role_policy.html.markdown
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role_policy_attachment.html.markdown
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role_policies_exclusive.html.markdown
15. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role_policy_attachments_exclusive.html.markdown
16. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_instance_profile.html.markdown
17. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_service_linked_role.html.markdown
18. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_policy.html.markdown
19. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_policy_attachment.html.markdown
20. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/iam_policy_document.html.markdown
21. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_user.html.markdown
22. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_group.html.markdown
23. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_group_membership.html.markdown
24. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_user_policies_exclusive.html.markdown
25. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_group_policies_exclusive.html.markdown
26. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_user_policy_attachments_exclusive.html.markdown
27. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_group_policy_attachments_exclusive.html.markdown
28. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_access_key.html.markdown
29. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_openid_connect_provider.html.markdown
30. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_account_password_policy.html.markdown
31. https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
32. https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html
33. https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html
34. https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_passwords_account-policy.html
35. https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html
36. https://docs.aws.amazon.com/securityhub/latest/userguide/iam-controls.html
