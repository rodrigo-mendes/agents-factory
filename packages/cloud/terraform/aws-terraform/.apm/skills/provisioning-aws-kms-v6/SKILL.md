---
name: provisioning-aws-kms-v6
description: "KMS Terraform (aws 6.x): customer managed keys, aliases, key policies, grants, multi-Region and external keys. Use when writing HCL for KMS. Not for IAM roles/policies, Secrets Manager."
---

# Provisioning AWS KMS with Terraform — hashicorp/aws 6.x

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
| 6.0 KMS breaking change | `data "aws_kms_secret"` removed → use `data "aws_kms_secrets"` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown |
| 6.48–6.69 KMS changes | No entries for any `aws_kms_*` resource or data source in this range | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- 1.17.0-rc2 exists; do not target it. Re-verify when starting new work.
- 6.57.0 is permanently withdrawn; any pinned constraint that includes it will fail init.
- v7 is planned; breaking changes documented in the v6 upgrade guide already mention v7 removals.

**Version lock:** this skill locks to the **6.x major line** (suffix `-v6`), reference 6.69.0.
A new major is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Key basics (terraform block, aws_kms_key, aws_kms_alias): [always-do-key-basics](./blueprints/always-do-key-basics.md)
- Key policy and grants (root principal, admin/user separation, aws_kms_grant): [always-do-key-policy](./blueprints/always-do-key-policy.md)
- Never-do policy config (mixing mechanisms, lockout bypass, wildcard IAM): [never-do-policy](./blueprints/never-do-policy.md)
- Never-do usage (asymmetric rotation, alias/aws/, removed resources): [never-do-usage](./blueprints/never-do-usage.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `~> 6.69` (root) or `>= 6.0` (module) and `~> 1.16` for the CLI constraint** in every `terraform {}` block.
  See [key-basics §1](./blueprints/always-do-key-basics.md#1-terraform-block-and-s3-backend).
- **Set `enable_key_rotation = true` on every symmetric `AWS_KMS` key** — required for Security Hub KMS.4;
  only valid for symmetric keys with `AWS_KMS` origin.
  See [key-basics §2](./blueprints/always-do-key-basics.md#2-aws_kms_key).
- **Use `deletion_window_in_days = 30` and `lifecycle { prevent_destroy = true }` for production keys** —
  satisfies KMS.3; destroying the resource schedules deletion after the waiting period.
  See [key-basics §2](./blueprints/always-do-key-basics.md#2-aws_kms_key).
- **Prefix every `aws_kms_alias` with `alias/`; never with `alias/aws/`** — `alias/aws/` is reserved for AWS
  managed keys and causes `InvalidAliasNameException`.
  See [key-basics §3](./blueprints/always-do-key-basics.md#3-aws_kms_alias).
- **Always include the root-account principal in every key policy** — without it, IAM policies that allow access
  are ineffective; if the only named user is deleted, regaining access requires contacting AWS Support.
  See [key-policy §4](./blueprints/always-do-key-policy.md#4-key-policy-and-separation-of-duties).
- **Build key policies with `aws_iam_policy_document`; separate admin and user statements** — admins manage
  keys but have no cryptographic access; grant `CreateGrant` only with `kms:GrantIsForAWSResource = true`.
  See [key-policy §4](./blueprints/always-do-key-policy.md#4-key-policy-and-separation-of-duties).
- **Set policy in `aws_kms_key` OR use `aws_kms_key_policy` — never both** — mixing them causes
  inconsistencies and may overwrite configuration.
  See [never-do-policy §1](./blueprints/never-do-policy.md#1-mixing-policy-mechanisms).
- **List specific key ARNs in IAM `resources` for `kms:Decrypt` / `kms:ReEncryptFrom`** — `"Resource": "*"` on
  decrypt actions fails Security Hub KMS.1 / KMS.2.
  See [never-do-policy §4](./blueprints/never-do-policy.md#4-wildcard-resource-in-iam-decrypt-policies).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Key type | Symmetric (`SYMMETRIC_DEFAULT` / `ENCRYPT_DECRYPT`): auto-rotation supported. Asymmetric RSA/ECC: `SIGN_VERIFY` or `ENCRYPT_DECRYPT`; no auto-rotation. HMAC: `GENERATE_VERIFY_MAC`; no auto-rotation. Affects `customer_master_key_spec`, rotation eligibility, and allowed operations. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown)) | "Is this a symmetric encryption key, an asymmetric signing/encryption key, or an HMAC key?" |
| Policy mechanism | `policy` inline in `aws_kms_key` — simpler, single-module ownership. `aws_kms_key_policy` — separates policy lifecycle from key lifecycle; suits multi-module setups. Never both. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown)) | "Should the key policy be managed inline in aws_kms_key or as a separate aws_kms_key_policy resource?" |
| Multi-Region keys | `multi_region = true` creates a primary key; replicate with `aws_kms_replica_key` per Region. Rotation is enabled only on the primary; new material is used only when all replicas have it. Deletion requires deleting all replicas first. ([source](https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html)) | "Does this key need to be multi-Region? If yes, confirm primary + replica topology and Region ordering." |
| External key material | `aws_kms_external_key` for `EXTERNAL` origin. Key material stored as **plain-text in Terraform state**. No auto-rotation; on-demand rotation only. If material expires or is deleted, the key becomes unusable. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_external_key.html.markdown)) | "Is external key material required? If yes, confirm state security controls and material lifecycle." |
| Rotation period | `rotation_period_in_days` 90–2560; provider has no default (AWS uses 365 days when omitted on enable). Requires `enable_key_rotation = true`. May be constrained by `kms:RotationPeriodInDays` condition key. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown)) | "Should rotation use a custom period (90–2560 days) or the AWS default of 365 days?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Set `policy` in `aws_kms_key` AND use `aws_kms_key_policy` for the same key — "inconsistencies and may overwrite configuration". ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown)) | Choose one mechanism. See [never-do-policy §1](./blueprints/never-do-policy.md#1-mixing-policy-mechanisms) |
| Omit the root-account principal from a key policy — IAM policies become ineffective; if the only named user is deleted, AWS Support is required to regain access. ([source](https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html)) | Always include an "Enable IAM User Permissions" statement with the account root ARN. See [never-do-policy §2](./blueprints/never-do-policy.md#2-omitting-root-account-principal) |
| Start an alias name with `alias/aws/` — reserved for AWS managed keys; causes `InvalidAliasNameException`. ([source](https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateAlias.html)) | `alias/<custom-name>`. See [never-do-usage §2](./blueprints/never-do-usage.md#2-aliasaws-prefix) |
| Set `bypass_policy_lockout_safety_check = true` routinely — prevents future `PutKeyPolicy` calls. ([source](https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateKey.html)) | Leave at default `false`. See [never-do-policy §3](./blueprints/never-do-policy.md#3-bypass-policy-lockout-safety-check) |
| Set `enable_key_rotation = true` on asymmetric or HMAC keys — AWS does not support auto-rotation for these types. ([source](https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html)) | Leave at default `false`; rotate manually via new key + alias retarget. See [never-do-usage §1](./blueprints/never-do-usage.md#1-rotation-on-asymmetric-or-hmac-keys) |
| Use `data "aws_kms_secret"` — removed in hashicorp/aws 6.0. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown)) | `data "aws_kms_secrets"` (plural). See [never-do-usage §3](./blueprints/never-do-usage.md#3-aws_kms_secret-data-source-removed-in-60) |
| Allow `kms:Decrypt` / `kms:ReEncryptFrom` on `"Resource": "*"` in IAM policies — fails KMS.1 / KMS.2. ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/kms-controls.html)) | List specific key ARNs. See [never-do-policy §4](./blueprints/never-do-policy.md#4-wildcard-resource-in-iam-decrypt-policies) |

## Quick Reference

Sources fetched 2026-10-14.

| Aspect | Value | Source |
|---|---|---|
| Provider constraint (root) | `~> 6.69` | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| CLI constraint | `~> 1.16` | https://developer.hashicorp.com/terraform/language/terraform |
| S3 locking | `use_lockfile = true` (`dynamodb_table` deprecated) | https://developer.hashicorp.com/terraform/language/backend/s3 |
| `key_usage` default | `ENCRYPT_DECRYPT` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown |
| `customer_master_key_spec` default | `SYMMETRIC_DEFAULT` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown |
| `deletion_window_in_days` | 7–30; default 30 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown |
| `rotation_period_in_days` | 90–2560; no provider default; AWS uses 365 days on enable | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown |
| Alias name pattern | `alias/[a-zA-Z0-9/_-]+`, 1–256 chars; `alias/aws/` reserved | https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateAlias.html |
| Key policy max size | 32 768 characters | https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateKey.html |
| `bypass_policy_lockout_safety_check` | Default `false`; policy must allow caller a subsequent `PutKeyPolicy` | https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateKey.html |
| KMS.3 — prevent deletion | `prevent_destroy = true` + `deletion_window_in_days = 30` | https://docs.aws.amazon.com/securityhub/latest/userguide/kms-controls.html |
| KMS.4 — rotation | `enable_key_rotation = true` (symmetric AWS_KMS only) | https://docs.aws.amazon.com/securityhub/latest/userguide/kms-controls.html |
| KMS.5 — public access | No `"*"` principal, no untrusted accounts in key policy | https://docs.aws.amazon.com/securityhub/latest/userguide/kms-controls.html |
| Import (key) | `terraform import aws_kms_key.a <key-id>` or identity block (`id@region` cross-region) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown |
| Import (alias) | `terraform import aws_kms_alias.a alias/my-alias` or identity block | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_alias.html.markdown |
| Import (key policy) | `terraform import aws_kms_key_policy.a <key-id>` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key_policy.html.markdown |
| Import (grant) | `terraform import aws_kms_grant.a <key_id>:<grant_id>` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_grant.html.markdown |

## 5.x → 6.x Migration (KMS)

Breaking changes in 6.0.0 that affect KMS work
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-14):

- **`data "aws_kms_secret"`**: removed → replace with `data "aws_kms_secrets"` (plural).
- **`region` attribute added**: every KMS resource and `data.aws_kms_key` now accept optional `region`;
  changing it forces replacement; cross-region imports use `id@region`.
- No breaking changes for `aws_kms_key`, `aws_kms_key_policy`, `aws_kms_alias`, `aws_kms_grant`,
  `aws_kms_replica_key`, `aws_kms_external_key`, or `data.aws_kms_key`.

6.48.0 → 6.69.0 contains no KMS-scope breaking changes.

Upgrade path: move to latest 5.x, get a clean plan, set `~> 6.0`, run `terraform init -upgrade`.

## External Resources

All fetched 2026-10-14.

- Provider releases: https://github.com/hashicorp/terraform-provider-aws/releases
- CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- aws_kms_key resource: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown
- aws_kms_key_policy resource: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key_policy.html.markdown
- aws_kms_alias resource: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_alias.html.markdown
- aws_kms_grant resource: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_grant.html.markdown
- KMS Key Policies Developer Guide: https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html
- KMS Rotate Keys: https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html
- KMS Deleting Keys: https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html
- Security Hub KMS controls: https://docs.aws.amazon.com/securityhub/latest/userguide/kms-controls.html
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
