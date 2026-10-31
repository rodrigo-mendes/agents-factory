---
name: provisioning-aws-organizations-v6
description: "Organizations Terraform (aws 6.x, global): org, OUs, accounts, SCPs, attachments, delegated admins. Use when writing HCL for an AWS org. Not for IAM, CloudTrail org trails, KMS."
---

# Provisioning AWS Organizations with Terraform — hashicorp/aws 6.x

> Version lock: every claim applies to **hashicorp/aws 6.x** (reference 6.70.0) + **Terraform ~> 1.16** only.
> `-v6` = 6.x major line; v7 = new skill. Research date **2026-10-23**. Claims tagged (unverified) or
> (medium confidence) were not fully confirmed against an official page.
> **Organizations is a global service: no `region` argument, no `@region` import ID.**

## Version Context

| Item | Value | Source (fetched 2026-10-23) |
|---|---|---|
| Terraform CLI | `~> 1.16` (1.16.6); 1.17.0 is stable since 2026-10-21 but not the target | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | **6.70.0** latest (CHANGELOG dates it 2026-10-21); constraint `~> 6.69`; no 7.x | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| 6.57.0 | **Withdrawn** — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Region | Global: `aws_organizations_*` resources do not accept `region` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |
| Hosting | Hosted in `us-east-1`; Service Quotas lookups must use `us-east-1` | https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html |
| Identity import | `identity` blocks need Terraform >= 1.12.0 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc.html.markdown |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 is stable since 2026-10-21 (this skill still targets `~> 1.16`); re-verify before moving the constraint.
- hashicorp/aws 6.70.0 is latest; 6.57.0 is withdrawn; v7 is planned and would be a new skill.

**Version lock:** `-v6` = 6.x major line, reference patch 6.70.0, Terraform `~> 1.16`. A new major is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Foundation: [terraform block, organization, OUs, accounts](./blueprints/always-do-foundation.md)
- Policies: [SCP, attachments, delegated admin, resource policy, test](./blueprints/always-do-policies.md)
- Never-do organization: [region, FullAWSAccess, SCP limits, role_name, skip_destroy](./blueprints/never-do-organization.md)
- Never-do provider: [status, dynamodb_table, withdrawn version](./blueprints/never-do-provider.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `~> 6.69` (root) and `~> 1.16` in every root `terraform {}` block** — https://developer.hashicorp.com/terraform/language/expressions/version-constraints
  See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-provider).
- **Use `use_lockfile = true` on the S3 backend** — `dynamodb_table` is deprecated: https://developer.hashicorp.com/terraform/language/backend/s3
  See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-provider).
- **Authenticate the provider into the management account**, because account management must be done from the organization's root account: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_account.html.markdown
  See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-provider).
- **Keep `feature_set = "ALL"` (the default)** — `aws_service_access_principals` and `enabled_policy_types` require it: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_organization.html.markdown
  See [foundation §2](./blueprints/always-do-foundation.md#2-organization).
- **Use `roots[0].id` as the top-level `parent_id`** for OUs and accounts: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_organization.html.markdown
  See [foundation §3](./blueprints/always-do-foundation.md#3-organizational-units).
- **Keep OU nesting within 5 levels under the root** — AWS quota: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html
  See [foundation §3](./blueprints/always-do-foundation.md#3-organizational-units).
- **Set `parent_id` explicitly on `aws_organizations_account`** — a configured value is needed for drift detection: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_account.html.markdown
  See [foundation §4](./blueprints/always-do-foundation.md#4-accounts).
- **Add `lifecycle { ignore_changes = [role_name] }` when `role_name` is set** — Organizations cannot read it back: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_account.html.markdown
  See [foundation §4](./blueprints/always-do-foundation.md#4-accounts).
- **Use the deny-list model for SCPs** (keep `FullAWSAccess`, add `Deny` statements) as the low-friction default: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_evaluation.html
  See [policies §5](./blueprints/always-do-policies.md#5-deny-list-scp-and-attachment).
- **Test SCPs on an OU first** before attaching to the root — AWS strongly recommends it: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html
  See [policies §5](./blueprints/always-do-policies.md#5-deny-list-scp-and-attachment).
- **Attach a root-level SCP denying `organizations:LeaveOrganization` and `account:CloseAccount`**: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html
  See [policies §5](./blueprints/always-do-policies.md#5-deny-list-scp-and-attachment).
- **Enable `SECURITYHUB_POLICY` or `INSPECTOR_POLICY` only with the matching service principal** in `aws_service_access_principals`: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_organization.html.markdown
  See [policies §6](./blueprints/always-do-policies.md#6-policy-types-and-non-scp-policies).
- **Read `state`, not the deprecated `status`**, on organization and account attributes: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_organization.html.markdown
  See [foundation §4](./blueprints/always-do-foundation.md#4-accounts).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| `CONSOLIDATED_BILLING` → `ALL` | Needs approval from member accounts that joined by invitation, then finalization by the owner in the AWS Console; until then Terraform shows a perpetual diff and the API keeps reporting `CONSOLIDATED_BILLING`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_organization.html.markdown)) | "Are all invited accounts ready to approve, and will the owner finalize in the Console?" |
| `close_on_deletion = true` | By default deleting the resource only removes the account from the organization; this setting closes it. Closure quotas are enforced and can return `CLOSE_ACCOUNT_QUOTA_EXCEEDED`, then you close it manually. This is not supported for GovCloud accounts. With `create_govcloud`, the GovCloud account (`govcloud_id`) can only be managed by importing it with this resource. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_account.html.markdown)) | "Should destroying this resource close the AWS account?" |
| Changing `iam_user_access_to_billing` | Changing it forces account recreation. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_account.html.markdown)) | "Is recreating the account acceptable?" |
| Allow-list SCPs | Replacing `FullAWSAccess` blocks new services until explicitly allowed; an explicit `Allow` must exist at every level from root to account. ([source](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_evaluation.html)) | "Deny list (default) or allow list?" |
| Attaching an SCP to the root | Affects every member account; AWS recommends thorough testing first. ([source](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)) | "Has this SCP been tested on an OU?" |
| Disabling a policy type (`enabled_policy_types`) | Disabling the SCP type detaches all SCPs and the attachments are not recoverable; re-enabling restores only `FullAWSAccess`. ([source](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)) | "Confirm every SCP attachment can be lost and recreated." |
| Provider identity: management account or delegated administrator | Account management must be done from the organization's root account ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_account.html.markdown)); using a delegated administrator instead, where AWS allows it, is an inference (medium confidence). | "Does this provider authenticate into the management account or a delegated administrator?" |
| Root SCP denying Leave/Close | Organizations created in the console after 2026-07-10 get it automatically; those created with the CLI, SDKs, CloudFormation or before that date must attach it manually ([source](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html)). That Terraform-created organizations need it too is an inference (medium confidence). | "Was this organization created in the console after 2026-07-10?" |
| `return_organization_only = true` | Avoids API throttling, but only `arn`, `feature_set`, `master_account_arn`, `master_account_email` and `master_account_id` are populated, so `roots[0].id` is unavailable. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_organization.html.markdown)) | "Do you need roots or accounts attributes?" |
| `prevent_destroy` on foundational accounts | Standard Terraform lifecycle usage; the resource page does not prescribe it (medium confidence). | "Should foundational accounts be protected with `prevent_destroy`?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Set `region` or an `@region` import ID on `aws_organizations_*` — Organizations is global. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown)) | Omit `region`; import with the plain ID (`o-…`, `ou-…`, `p-…`, account ID) |
| Remove `FullAWSAccess` without modifying or replacing it — "all AWS actions from member accounts will fail". ([source](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)) | Keep it attached and add `Deny` statements |
| Apply 5120 chars / 5 attached policies to SCPs — those are RCP limits. ([source](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html)) | SCP limits: 10,240 chars, 10 attached per root/OU/account |
| Expect SCPs to restrict the management account — "SCPs don't affect users or roles in the management account". ([source](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)) | Restrict the management account by access control and use it only for tasks that require it |
| Set `role_name` without `ignore_changes` — perpetual diff after import. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_account.html.markdown)) | `lifecycle { ignore_changes = [role_name] }` |
| Rely on `skip_destroy = true` on `aws_organizations_policy` to protect the last attached SCP — destroy only removes it from state without deleting it. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_policy.html.markdown)) | Use it to keep a policy that must stay attached; AWS requires at least one attached SCP (minimum 1; the last SCP cannot be removed) |
| Read the deprecated `status` attribute on `aws_organizations_account` or the organization. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_account.html.markdown)) | Use `state` |
| S3 backend with `dynamodb_table` — deprecated. ([source](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` |
| Pin `version = "6.57.0"` — withdrawn. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` |

## Quick Reference

Sources fetched 2026-10-23.

| Aspect | Value | Source |
|---|---|---|
| Provider / CLI constraint | `~> 6.69` / `~> 1.16` | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| Region | None: global resources, no `@region` import | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |
| Org feature set | `ALL` (default) or `CONSOLIDATED_BILLING` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_organization.html.markdown |
| Policy default type | `SERVICE_CONTROL_POLICY` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_policy.html.markdown |
| Import IDs | org `o-…`; OU `ou-…`; account ID (or `<id>_<ALLOW\|DENY>`); policy `p-…`; attachment `<target_id>:<policy_id>`; delegated admin `<account_id>/<service_principal>`; resource policy `rp-…` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_policy_attachment.html.markdown (attachment); other IDs on each resource page listed in the bibliography |
| Account timeouts | create/update/delete 10 min each | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_account.html.markdown |
| SCP size / attached | 10,240 chars / 10 per root, OU or account (min 1) | https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html |
| RCP size / attached | 5,120 chars / 5 (`RCPFullAWSAccess` counts) | https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html |
| Accounts / OUs / depth | 10 default (adjustable) / 2000 / 5 levels | https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html |
| Concurrent creations | 5 accounts; closures 3 concurrent | https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html |
| Account closure quota | 20% of members or 250, whichever higher, max 1,000 per 30 days | https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html |
| Policy API throttling | Create/Attach/Detach/UpdatePolicy 2 rps; Enable/DisablePolicyType and EnableAWSServiceAccess 1 rps | https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html |
| Resource policy limit | 40,000 chars | https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html |
| Security Hub Account.2 | Accounts should be part of an organization; High; rule `account-part-of-organizations` | https://docs.aws.amazon.com/securityhub/latest/userguide/account-controls.html |
| Security Hub Account.1 | Security contact information provided; moderate severity | https://docs.aws.amazon.com/securityhub/latest/userguide/account-controls.html |
| Security Hub org controls page | Fetch returned no controls (unverified: absence of evidence) | https://docs.aws.amazon.com/securityhub/latest/userguide/organizations-controls.html |

## 5.x → 6.x Migration (Organizations)

- None found in the 6.0.0 upgrade guide for any `aws_organizations_*` resource or data source (medium confidence, absence of evidence)
  ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-23).
- None found in the CHANGELOG from 6.48.0 to 6.70.0 for `aws_organizations_*` or Organizations policy types (medium confidence, absence of evidence)
  ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md), 2026-10-23).
- `status` on organization and account attributes is deprecated: use `state`.
- Legacy material written for Terraform 1.7 / aws 6.47.0 is superseded: use `~> 1.16`, `~> 6.69`, `use_lockfile`.
- Which 6.x release added each newer policy type was not traced (see L3 in the register).

## External Resources

All fetched 2026-10-23.

- Provider CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- Enhanced region support: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
- Organizations quotas: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html
- SCPs: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html
- Management account best practices: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html
- Security Hub account controls: https://docs.aws.amazon.com/securityhub/latest/userguide/account-controls.html
- Terraform S3 backend: https://developer.hashicorp.com/terraform/language/backend/s3
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
