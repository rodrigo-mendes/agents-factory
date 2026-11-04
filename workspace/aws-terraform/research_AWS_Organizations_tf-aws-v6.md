# Research — AWS Organizations with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `organizations`, flat fan-out, single researcher, no sub-agents).
> Resource docs come from the upstream raw markdown in `hashicorp/terraform-provider-aws` (`main`), because Registry pages are JS-only (F12).
> Coverage checklist only, never a source: `workspace/terraform/research_AWS_Organization_aws-v6.x.md` (6.47.0, Terraform 1.7, EOL). Its errors are listed in §9.
> All URLs below were read on 2026-10-23 unless a family fact (F#) is cited.

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"` (1.16.6). 1.17.0 is stable but not the target | F1, F2 |
| hashicorp/aws | latest 6.70.0 (CHANGELOG dates it 2026-10-21); constraint `~> 6.69`; no 7.x | F3; [B3] |
| Withdrawn | 6.57.0, never pin it | F4 |
| Region | **Organizations is GLOBAL.** The enhanced-region guide lists the line `* Organizations (`aws_organizations_*`)` verbatim among services whose resources do not accept `region`. None of the 7 in-scope resource pages, nor the `aws_organizations_policies_for_target` data source page, documents a `region` argument. Import IDs carry no `@region` | F14; [B1], [B4]–[B11] |
| Service hosting | "AWS Organizations is a global service that is physically hosted in the US East (N. Virginia) Region (`us-east-1`)". Service Quotas lookups must use `us-east-1` | [B13] |
| Identity import | `identity` blocks need Terraform ≥ 1.12.0. Every in-scope resource page documents an identity schema | F11; [B4]–[B10] |

Related global resources from other services (not `aws_organizations_*`) that the guide also lists as global: `aws_cloudtrail_organization_delegated_admin_account`, `aws_vpc_ipam_organization_admin_account` [B1]. The guide also has a table row for `aws_servicecatalog_organizations_access`. That resource belongs to Service Catalog and is out of scope here.

Recommended block (root module): `required_version = "~> 1.16"`, `aws = { source = "hashicorp/aws", version = "~> 6.69" }`. S3 backend should use `use_lockfile = true`, not `dynamodb_table` (F6, F7).

## 2. Provider 6.x changes for Organizations

- **6.0.0 upgrade guide (F13):** no entries for any `aws_organizations_*` resource or data source. The only organization-related section there is `aws_guardduty_organization_configuration`, which is out of scope [B2].
- **CHANGELOG 6.48.0 (2026-06-03) → 6.70.0 (2026-10-21):** **no entries** mention any `aws_organizations_*` resource or data source, or any Organizations policy type. I read the whole range, in two contiguous chunks covering offsets 0–200000. The only nearby entries are for other services' organization-scoped resources: GuardDuty org configuration feature (6.56.0, 6.70.0), Observability Admin `*_for_organization` (6.48.0, 6.61.0–6.63.0), Detective org configuration identity (6.51.0), Config org managed rule fix (6.54.0) [B3].
- So the current resource surface (§3–§8) is the one to use. Policy types documented today: `AISERVICES_OPT_OUT_POLICY`, `BACKUP_POLICY`, `BEDROCK_POLICY`, `CHATBOT_POLICY`, `DECLARATIVE_POLICY_EC2`, `INSPECTOR_POLICY`, `RESOURCE_CONTROL_POLICY`, `S3_POLICY`, `SECURITYHUB_POLICY`, `SERVICE_CONTROL_POLICY`, `TAG_POLICY`, `UPGRADE_ROLLOUT_POLICY` [B4], [B6]. I did not establish which 6.x release added each type (L3).

## 3. `aws_organizations_organization` [B4]

All arguments are optional:
- `feature_set`: `ALL` (**default**) or `CONSOLIDATED_BILLING`.
- `aws_service_access_principals`: list of service principals (`<svc>.amazonaws.com`). **Requires `feature_set = "ALL"`.**
- `enabled_policy_types`: policy types enabled on the root. **Requires `feature_set = "ALL"`.** Allowed values are the 12 listed in §2. Dependencies: `INSPECTOR_POLICY` needs `inspector2.amazonaws.com` in `aws_service_access_principals`, and `SECURITYHUB_POLICY` needs `securityhub.amazonaws.com`.
- `return_organization_only` (default `false`): when `true`, only `arn`, `feature_set`, `master_account_arn`, `master_account_email` and `master_account_id` are populated. Use it to avoid API throttling.

Documented warnings:
- Moving `CONSOLIDATED_BILLING` → `ALL` requires approval from member accounts that joined **by invitation**, then finalization by the owner in the AWS Console. Until then Terraform shows a **perpetual diff** and the API keeps reporting `CONSOLIDATED_BILLING`.
- AWS recommends enabling service integrations through each service's own console or commands, because some services do not support enablement through this endpoint.

Attributes:
- `id`, `arn`, `master_account_arn|email|id|name`.
- `roots[]`: `arn`, `id`, `name`, `policy_types[] {name, status}`. Use `roots[0].id` as the top-level `parent_id`.
- `accounts[]` (includes the management account) and `non_master_accounts[]`: `arn`, `email`, `id`, `joined_method`, `joined_timestamp`, `name`, `state`, `status`. `status` is **deprecated**, use `state`.

Import: organization ID (`o-1234567`). Identity schema: `id` (required), `account_id` (optional). No timeouts documented.

AWS side: SCPs are "available only in an organization that has all features enabled" [B12].

**Management account / provider requirement:** the account page says "Account management must be done from the organization's root account" [B5]. AWS lists the APIs callable only from the management account [B15]. For the provider this means the `aws` provider (credentials or `assume_role`) must authenticate into the management account, or into a delegated administrator where AWS allows it (see §8). A `region` setting has no effect on these resources (F14).

## 4. `aws_organizations_organizational_unit` [B7]

- Required: `name`, `parent_id` (the root or another OU).
- Optional: `tags`. Keys that match provider `default_tags` override them.
- Attributes: `accounts[]` (direct child accounts only, no child OUs; fields `arn`, `email`, `id`, `name`), `arn`, `id`, `tags_all`.
- Import: `ou-1234567`. Identity: `id`, plus optional `account_id`.
- The page does not say whether changing `parent_id` forces replacement (U1). No NOTE blocks.
- AWS quotas: 2000 OUs, nesting at most **5 levels** under the root [B13].

## 5. `aws_organizations_account` [B5]

- Required: `email` (must not already belong to another AWS account), `name`.
- Optional:
  - `parent_id`: defaults to the root. The docs say a configured value is needed for drift detection.
  - `role_name`: IAM role pre-created with admin permissions that trusts the management account.
  - `close_on_deletion`: default is not to close. Not supported for GovCloud.
  - `create_govcloud`: exposes `govcloud_id`. The GovCloud account can only be managed by importing it.
  - `iam_user_access_to_billing`: `ALLOW`/`DENY`. The API defaults to `ALLOW` when unset. **Changing it forces account recreation.**
  - `tags`.
- **`role_name` perpetual diff:** Organizations has no API to read `role_name` back, so a set value always diffs after import. The docs show this workaround:
  ```hcl
  lifecycle { ignore_changes = [role_name] }
  ```
- **Deletion behavior:**
  - By default destroy only **removes** the account from the organization.
  - `close_on_deletion = true` closes the account. Closure quotas can return `CLOSE_ACCOUNT_QUOTA_EXCEEDED`, in which case you must close the account manually.
  - AWS also requires that a created account exists ≥ 4 days before it can be removed [B13].
- Attributes: `arn`, `govcloud_id`, `id`, `joined_method`, `joined_timestamp`, `state`, `status` (**deprecated**, use `state`), `tags_all`.
- Timeouts: `create`, `update` and `delete` each default to 10 min.
- Import: account ID, or `<account_id>_<ALLOW|DENY>` when `iam_user_access_to_billing` is set. Identity: `id`, plus optional `account_id`.
- Recommendation (inference, medium confidence M1): add `prevent_destroy` for foundational accounts. This is standard Terraform lifecycle usage; the resource page does not prescribe it.

## 6. `aws_organizations_policy` [B6] and `aws_organizations_policy_attachment` [B8]

Policy:
- Required: `content`, `name`.
- Optional: `description`, `type` (default **`SERVICE_CONTROL_POLICY`**; 12 values listed in §2), `skip_destroy`, `tags`.
- `content` syntax depends on the policy type. For SCP/RCP use `jsonencode(...)` or `data.aws_iam_policy_document.x.json`. Tag, backup and other management policies use their own `@@assign` syntax, so build them with `jsonencode`, not the IAM document data source (M2: an inference from the per-type syntax links).
- `skip_destroy = true`: destroy removes the policy from state only and does not delete it. Documented purpose: keeping policies that must stay attached to satisfy AWS's minimum of one attached policy.
- Attributes: `id`, `arn`, `tags_all`. No NOTE blocks.
- Import: `p-12345678`. Identity: `id`, plus optional `account_id`.

Policy attachment:
- Required: `policy_id`, `target_id` (root, OU or account ID). Optional: `skip_destroy`. The docs say: "If set to `true`, destroy will **not** detach the policy".
- Import: `<target_id>:<policy_id>`, for example `123456789012:p-12345678`. Identity: `policy_id` and `target_id`, plus optional `account_id`.

## 7. `aws_organizations_delegated_administrator` [B9], `aws_organizations_resource_policy` [B10], data source [B11]

- **delegated_administrator:**
  - Required: `account_id` (member account), `service_principal`.
  - Attributes: `id`, `arn`, `delegation_enabled_date`, `email`, `joined_method`, `joined_timestamp`, `name`, `status`.
  - Import: `<account_id>/<service_principal>` (slash-separated). Identity: `delegated_account_id` and `service_principal`, plus optional `account_id`.
- **resource_policy:**
  - Required: `content` (JSON in the delegation policy syntax). Optional: `tags`.
  - Attributes: `arn`, `id`, `tags_all`.
  - Import: `rp-12345678`. AWS limit: 40,000 characters for the resource-based delegation policy [B13].
- **data `aws_organizations_policies_for_target` (brief):**
  - Required: `target_id` (`r-…`, 12-digit account, `ou-…`) and `filter`.
  - The page lists only 7 filter values: `AISERVICES_OPT_OUT_POLICY`, `BACKUP_POLICY`, `CHATBOT_POLICY`, `DECLARATIVE_POLICY_EC2`, `RESOURCE_CONTROL_POLICY`, `SERVICE_CONTROL_POLICY`, `TAG_POLICY`. This is narrower than the resource's 12 types (U2).
  - Output: `ids`.

## 8. AWS guidance — SCPs, best practices, quotas, Security Hub

SCP semantics [B12], [B14]:
- SCPs **grant no permissions**. They set the maximum available permissions for IAM users and roles in **member** accounts, including the member root user.
- "SCPs don't affect users or roles in the management account". SCPs **do** apply to member accounts that are delegated administrators.
- SCPs do not affect service-linked roles or resource-based policies directly.
- `FullAWSAccess` is attached by AWS "to every root, OU and account when it's created". "You should not remove the FullAWSAccess policy unless you modify or replace it … otherwise all AWS actions from member accounts will fail."
- Disabling the SCP type detaches all SCPs, and the attachments are not recoverable. Re-enabling restores only `FullAWSAccess`.
- **Deny list vs allow list:**
  - Allow: an explicit `Allow` must exist at **every** level from the root to the account.
  - Deny: a `Deny` at any level in the path applies to everything below it.
  - Deny list (keep `FullAWSAccess` and add `Deny` statements) is the low-friction default.
  - Allow list (replace `FullAWSAccess`) blocks new services until they are explicitly allowed. AWS warns that "Relying solely on allow statements … can lead to unintended access".
- **Testing:** AWS "strongly recommends that you don't attach SCPs to the root … without thoroughly testing". Test in an OU first and use IAM service-last-accessed data.

Management account best practices [B15]:
- Limit and review who has access.
- Use the account only for tasks that require it, and deploy no workloads there.
- Attach a root-level SCP that denies `organizations:LeaveOrganization` and `account:CloseAccount`. Organizations created **in the console after July 10, 2026** get this automatically. Organizations created with the CLI, SDKs, CloudFormation (and therefore Terraform, M3) or before that date must attach it manually.
- Delegate services to member accounts.

Quotas [B13] (defaults):

| Quota | Value |
|---|---|
| Accounts per org | 10 by default, adjustable (up to 50,000) |
| Roots / OUs / OU depth | 1 / 2000 / 5 levels |
| Max document size | SCP **10,240** chars; RCP 5120; declarative, backup, tag, chat apps and Security Hub 10,000; AI opt-out 2500 |
| Policies per org | SCP 10,000; RCP 2000; most others 1000 |
| Directly attached per root/OU/account | SCP **10** (minimum 1; the last SCP cannot be removed); RCP 5 (`RCPFullAWSAccess` auto-attached, cannot be detached, counts toward the 5); declarative, backup, tag, Security Hub 10; chat apps and AI opt-out 5 |
| Concurrent account creations | 5 |
| Account closures per 30 days | 20% of members or 250, whichever is higher, max 1,000 (not adjustable); 3 concurrent |
| Tags per root/OU/account | 50 |
| Throttling | CreatePolicy, AttachPolicy, DetachPolicy and UpdatePolicy: 2 rps (burst 3); Enable/DisablePolicyType and EnableAWSServiceAccess: 1 rps (burst 2) |

Security Hub:
- `https://docs.aws.amazon.com/securityhub/latest/userguide/organizations-controls.html` returned no controls, so there is **no Organizations control category** (U3, medium confidence).
- Related control: **[Account.2] AWS accounts should be part of an AWS Organizations organization**. Severity **High**, Config rule `account-part-of-organizations`, periodic [B16].
- Also **[Account.1]** security contact information provided, Medium [B16].
- ServiceCatalog.1 (portfolios shared within the organization only) appeared only in search results and was not read (U4).

## 9. Legacy-file claims found wrong or outdated

| # | Legacy claim | Finding |
|---|---|---|
| W1 | "Maximum SCP size is 5120 characters per policy, max 5 SCPs per entity" (also a 5120 validation in the module) | **Wrong.** SCP 10,240 chars, 10 per entity. 5120/5 are the **RCP** limits [B13] |
| W2 | Account closure "cannot close more than 10% of accounts in the past 30 days" | **Wrong.** 20% or 250, max 1,000 [B13] |
| W3 | S3 backend with `dynamodb_table` locking "mandatory" | **Outdated.** Deprecated, use `use_lockfile` (F7) |
| W4 | `aws_organizations_policy.skip_destroy` "prevents the last attached SCP from being removed" | **Imprecise.** It only skips deletion on destroy (state removal) [B6] |
| W5 | `CONSOLIDATED_BILLING`→`ALL` "requires all member accounts to accept" | **Imprecise.** Only accounts that joined by invitation [B4] |
| W6 | Gap: "`aws_organizations_resource_policy` full argument surface" not documented | **Resolved.** `content` + `tags` [B10] |
| W7 | Terraform ≥ 1.7 / `~> 6.0` / `terraform import` CLI | **Superseded** by F1/F3. Identity import needs ≥ 1.12 (F11) |
| W8 | "Terraform does not infer cross-resource ordering for Organizations resources — depends_on is often required" | **Unsupported** by any read source. References create implicit dependencies (U5) |

## 10. Unverified / medium-confidence / limits

- U1: whether changing `aws_organizations_organizational_unit.parent_id` forces replacement (not stated on the page).
- U2: why `policies_for_target.filter` lists fewer types than the resource (docs lag vs real validation).
- U3: absence of a Security Hub `organizations-controls` page (the fetch returned only a title).
- U4: ServiceCatalog.1 severity and details not read.
- U5: legacy `depends_on` claim (W8).
- U6: legacy claim that RCPs and declarative policies **do** apply to the management account (RCP page not read).
- M1: `prevent_destroy` on foundational accounts (Terraform-generic inference).
- M2: build non-IAM policy types with `jsonencode` rather than `aws_iam_policy_document` (inference from the per-type syntax).
- M3: Terraform-created organizations do not get the automatic Leave/Close SCP. Inference: Terraform calls the API, which is not the console path.
- L1: AWS service-specific docs for tag, backup and declarative policy syntax were not fetched.
- L2: the root access management / centralized root credentials feature was not researched.
- L3: the 6.x release that introduced each newer policy type is outside the 6.48→6.70 range and was not traced.
- L4: legacy integration sections (CloudTrail, Config, SSO, S3) are out of scope for this unit.

## 11. Security note

No prompt-injection or instruction-like text was observed in any fetched page.

## Source Bibliography

All accessed 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_organization.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_account.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_policy.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_organizational_unit.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_policy_attachment.html.markdown
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_delegated_administrator.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_resource_policy.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/organizations_policies_for_target.html.markdown
12. https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html
13. https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html
14. https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_evaluation.html
15. https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html
16. https://docs.aws.amazon.com/securityhub/latest/userguide/account-controls.html
17. https://docs.aws.amazon.com/securityhub/latest/userguide/organizations-controls.html (fetched; no control content returned)
