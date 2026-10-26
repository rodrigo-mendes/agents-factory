---
name: provisioning-aws-s3-v6
description: "S3 Terraform (aws 6.x): buckets, ownership, BPA, SSE, TLS policy, versioning, lifecycle, access logging, objects. Use when writing HCL for S3. Not for KMS keys, CloudFront distributions."
---

# Provisioning AWS S3 with Terraform — hashicorp/aws 6.x

> Version lock: every claim applies to **hashicorp/aws 6.x** (reference 6.69.0) + **Terraform ~> 1.16** only.
> Research date **2026-10-14**. Claims tagged (unverified) or (medium confidence) were not fully confirmed
> against an official page.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| Terraform CLI | **1.16.6** — current stable; 1.17.0-rc2 exists, do not target | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | **6.69.0** — current; v7 planned but not released | https://github.com/hashicorp/terraform-provider-aws/releases |
| Withdrawn | 6.57.0 — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Provider constraint | `~> 6.69` (root modules); `>= 6.0` (reusable modules) | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| CLI constraint | `~> 1.16` | https://developer.hashicorp.com/terraform/language/terraform |
| 6.0 S3 breaking | `bucket_region` attribute replaces `region` for reading a bucket's home region | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown |
| `bucket_namespace` | Added 6.37.0; `account-regional` enforces account-scoped naming | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| `expected_bucket_owner` | Deprecated on satellite resources (dropped from identity in 6.31.0); forces new | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| SSE-C | Blocked since April 2026 for all new general-purpose buckets (and existing without SSE-C objects, except Bahrain/UAE) | https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-s3-c-encryption-setting-faq.html |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- 1.17.0-rc2 exists; do not target it. Re-verify when starting new work.
- 6.57.0 was withdrawn from GitHub and the Registry; never pin it.
- v7 is planned; the v6 upgrade guide marks `s3_us_east_1_regional_endpoint` as "will be removed in v7.0.0".
- Inline `aws_s3_bucket` arguments (e.g. `versioning`, `server_side_encryption_configuration`) are deprecated but were **not removed in 6.0** — removal is planned for a future major version.

**Version lock:** this skill locks to the **6.x major line** (suffix `-v6`), reference 6.69.0.
A new major is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Foundation patterns: [terraform block, bucket, ownership, BPA](./blueprints/always-do-bucket-foundation.md)
- Security patterns: [SSE, TLS policy, access logging](./blueprints/always-do-security-encryption.md)
- Lifecycle / versioning patterns: [versioning timing, lifecycle filter, multipart abort](./blueprints/always-do-lifecycle-versioning.md)
- Object / testing patterns: [s3_object source_hash, terraform test, CI](./blueprints/always-do-objects-testing.md)
- Never-do resource conflicts: [inline mixing, multi-resource, etag+KMS, mfa_delete+lifecycle](./blueprints/never-do-resource-conflicts.md)
- Never-do ownership/ACL: [log-delivery-write ACL, expected_bucket_owner](./blueprints/never-do-ownership-acl.md)
- Never-do provider/migration: [bucket_region, account PAB region, aws_region name, backend lock, withdrawn version](./blueprints/never-do-provider-migration.md)
- Never-do naming/endpoints: [account-regional naming, legacy us-east-1 endpoint](./blueprints/never-do-naming-endpoints.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `~> 6.69` (root) or `>= 6.0` (module) and `~> 1.16` for the CLI constraint** in every `terraform {}` block.
  See [foundation §1](./blueprints/always-do-bucket-foundation.md#1-terraform-block-and-s3-backend).
- **Use `use_lockfile = true` on the S3 backend** — `dynamodb_table` is deprecated.
  See [foundation §1](./blueprints/always-do-bucket-foundation.md#1-terraform-block-and-s3-backend).
- **Use standalone satellite resources, not deprecated inline arguments** (`versioning`, `server_side_encryption_configuration`, `acl`, etc.) — mixing an inline block with its standalone resource causes Terraform to treat it as drift.
  See [foundation §2](./blueprints/always-do-bucket-foundation.md#2-bucket-resource-and-ownership-controls).
- **Set `object_ownership = "BucketOwnerEnforced"` via `aws_s3_bucket_ownership_controls`** — the default for new buckets; disables ACLs entirely. Use `aws_s3_bucket_policy` for access control.
  See [foundation §2](./blueprints/always-do-bucket-foundation.md#2-bucket-resource-and-ownership-controls).
- **Set all four BPA booleans explicitly on `aws_s3_bucket_public_access_block`** — all default `false`; omitting any one leaves a gap.
  See [foundation §3](./blueprints/always-do-bucket-foundation.md#3-bucket-level-public-access-block).
- **Manage `aws_s3_account_public_access_block` once per account; never set `region` on it** — the resource is global; multiple resources per account cause perpetual diff; account-level settings apply to all Regions.
  See [foundation §4](./blueprints/always-do-bucket-foundation.md#4-account-level-public-access-block).
- **Configure default encryption with `aws_s3_bucket_server_side_encryption_configuration`** (`AES256`, `aws:kms` or `aws:kms:dsse`; never the inline block); keep SSE-C blocked (blocked by AWS since April 2026).
  See [security §5](./blueprints/always-do-security-encryption.md#5-sse-configuration).
- **Enforce TLS via bucket policy `Deny` on `aws:SecureTransport = false`** (S3.5).
  See [security §6](./blueprints/always-do-security-encryption.md#6-tls-enforcement-via-bucket-policy).
- **Use bucket policy to grant `logging.s3.amazonaws.com s3:PutObject`** for access logging targets — ACL `log-delivery-write` is incompatible with `BucketOwnerEnforced`. Target bucket must be same-Region and must not have a default Object Lock retention.
  See [security §7](./blueprints/always-do-security-encryption.md#7-access-logging).
- **Use `filter {}` (not deprecated rule-level `prefix`) in every lifecycle rule** — omitting `filter` applies the rule to all objects.
  See [lifecycle §8](./blueprints/always-do-lifecycle-versioning.md#8-lifecycle-configuration).
- **Add `depends_on = [aws_s3_bucket_versioning.x]` for resources needing a `version_id`** — AWS recommends ~15 min after first enabling before writing critical objects.
  See [lifecycle §9](./blueprints/always-do-lifecycle-versioning.md#9-versioning).
- **Use `source_hash = filemd5(...)` instead of `etag` for KMS-encrypted objects** — `etag` is not MD5 for KMS or multipart > 16 MB.
  See [objects §10](./blueprints/always-do-objects-testing.md#10-aws_s3_object).
- **Run `terraform test` with `mock_provider "aws"` and `command = plan`** for CI-safe unit tests.
  See [testing §11](./blueprints/always-do-objects-testing.md#11-terraform-test-and-ci).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| SSE algorithm | SSE-S3 (`AES256`) vs SSE-KMS (`aws:kms`; without key ID uses `aws/s3`) vs DSSE-KMS (`aws:kms:dsse`). Security Hub S3.17 passes only SSE-KMS/DSSE-KMS; SSE-S3 fails it. `bucket_key_enabled` turns on S3 Bucket Keys for SSE-KMS; its cost effect is (unverified). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_server_side_encryption_configuration.html.markdown)) | "What SSE level is required: SSE-S3, SSE-KMS, or DSSE-KMS?" |
| Versioning | Enables indefinite object version growth — combine with noncurrent expiration lifecycle rules (S3.10/S3.14). Once enabled, cannot be disabled (only suspended). Object Lock makes it permanently irreversible. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_versioning.html.markdown)) | "Is versioning needed? If yes, confirm noncurrent-version lifecycle rules are in scope." |
| Replication | Versioning must be enabled on source and destination first; `priority` (unique) is required for multiple destinations; `existing_object_replication` needs AWS Support activation (medium confidence). No HCL pattern in this skill. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_replication_configuration.html.markdown)) | "Is replication needed? If yes, confirm source and destination versioning and IAM role scope." |
| Object Lock | `default_retention` takes `mode` = `COMPLIANCE` or `GOVERNANCE` and exactly one of `days`/`years`; the behavioral difference between modes is (unverified). Enabling Object Lock turns on versioning; neither can be turned off afterwards. For an existing bucket enable versioning first. No HCL pattern in this skill. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_object_lock_configuration.html.markdown)) | "Is Object Lock required? If yes, which mode and retention period?" |
| Bucket namespace | `global` (default, first-claim): any account can take the name once released. `account-regional`: name is locked to your account but must follow `<prefix>-<account-id>-<region>-an` format; not available in me-south-1 (Bahrain) and me-central-1 (UAE). ([source](https://docs.aws.amazon.com/AmazonS3/latest/userguide/gpbucketnamespaces.html)) | "Should the bucket use account-regional namespace? If yes, confirm the naming format is used." |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Mix a deprecated inline block (e.g. `versioning {}`, `server_side_encryption_configuration {}`) with its standalone satellite resource on the same bucket — Terraform treats it as drift. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket.html.markdown)) | Use only the standalone satellite resource; remove the inline block entirely |
| Have more than one `aws_s3_bucket_policy` / `aws_s3_bucket_lifecycle_configuration` / `aws_s3_bucket_notification` / `aws_s3_bucket_cors_configuration` per bucket — policy and notification `Put*` APIs replace the whole config (last apply wins); duplicate lifecycle/CORS configs give a perpetual diff. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_policy.html.markdown)) | One resource per bucket; for independent notification consumers use EventBridge |
| Use `etag = filemd5(...)` for KMS-encrypted objects or multipart uploads > 16 MB — etag is not MD5 in those cases. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_object.html.markdown)) | `source_hash = filemd5(...)` (state-only, correct for KMS) |
| Combine `mfa_delete = "Enabled"` with lifecycle rules — AWS explicitly states MFA delete cannot be used with a lifecycle configuration. ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/s3-controls.html)) | Choose one: MFA delete or lifecycle — not both |
| Use `acl = "log-delivery-write"` on the logging target when `BucketOwnerEnforced` is set — incompatible. ([source](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html)) | Grant `logging.s3.amazonaws.com s3:PutObject` via bucket policy |
| Use `expected_bucket_owner` on satellite resources — deprecated, forces replacement. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | Remove `expected_bucket_owner` from the configuration |
| Use `bucket_namespace = "account-regional"` with an arbitrary bucket name — account-regional names must end with `-<account-id>-<region>-an`. ([source](https://docs.aws.amazon.com/AmazonS3/latest/userguide/gpbucketnamespaces.html)) | `bucket = "${var.prefix}-${data.aws_caller_identity.current.account_id}-${data.aws_region.current.region}-an"` |
| Read bucket's home region via the `.region` attribute — in 6.0 this became Enhanced Region Support targeting. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown)) | Use `.bucket_region` attribute |
| Set `s3_us_east_1_regional_endpoint = "legacy"` in provider config — deprecated in 6.0, removed in v7. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown)) | Remove it or set `"regional"` |
| Set `region` on `aws_s3_account_public_access_block` or import with `id@region` — this resource is global, not regional. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown)) | Omit `region`; import with `<account_id>` only |
| Use `data.aws_region.current.name` — `name` is deprecated in 6.0. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown)) | `data.aws_region.current.region` |
| Pin `version = "6.57.0"` — withdrawn. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` or any non-withdrawn patch |

## Quick Reference

Sources fetched 2026-10-14.

| Aspect | Value | Source |
|---|---|---|
| Provider constraint (root) | `~> 6.69` | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| CLI constraint | `~> 1.16` | https://developer.hashicorp.com/terraform/language/terraform |
| S3 locking | `use_lockfile = true` (`dynamodb_table` deprecated) | https://developer.hashicorp.com/terraform/language/backend/s3 |
| `bucket_region` | Bucket home region attribute (6.0 change; `region` is now Enhanced Region Support) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown |
| Ownership default | `BucketOwnerEnforced` for new buckets (ACLs disabled) | https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html |
| PAB defaults | All four booleans default `false`; set all explicitly | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_public_access_block.html.markdown |
| Account PAB | One `aws_s3_account_public_access_block` per account; global resource — never set `region` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_account_public_access_block.html.markdown |
| `data.aws_region` | Use `.region` attribute (not deprecated `.name`) for the region name | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown |
| SSE-C | Blocked since April 2026 for new buckets and existing without SSE-C objects (except Bahrain/UAE) | https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-s3-c-encryption-setting-faq.html |
| Bucket Key | `bucket_key_enabled` = S3 Bucket Keys for SSE-KMS; cost effect (unverified) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_server_side_encryption_configuration.html.markdown |
| TLS enforce | `Deny aws:SecureTransport = false` bucket policy (S3.5) | https://docs.aws.amazon.com/securityhub/latest/userguide/s3-controls.html |
| Lifecycle filter | `filter {}` (all objects); exactly one child for prefix/tag/size; `and` to combine | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_lifecycle_configuration.html.markdown |
| `transition_default_minimum_object_size` | `all_storage_classes_128K` default — objects < 128 KB do not transition | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_lifecycle_configuration.html.markdown |
| Versioning timing | AWS recommends ~15 min after first enable before writing critical objects | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_versioning.html.markdown |
| `source_hash` | State-only; use `filemd5()` for KMS or multipart; `etag` is not MD5 in those cases | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_object.html.markdown |
| `bucket_regional_domain_name` | Use for CloudFront origins (not deprecated `bucket_domain_name`) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket.html.markdown |
| `terraform test` CI | `init -backend=false`, `validate -json`, `plan -detailed-exitcode -input=false -out=tfplan` | https://developer.hashicorp.com/terraform/cli/commands/plan |

## 5.x → 6.x Migration (S3)

Breaking changes in 6.0.0 that affect S3 work
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-14):

- **`aws_s3_bucket` (resource and data source)**: `bucket_region` attribute added and should be used instead of `region` to read the bucket's home region. `region` now means Enhanced Region Support (cross-region targeting). Any HCL reading `.region` for the bucket's location must switch to `.bucket_region`.
- **Provider config**: `s3_us_east_1_regional_endpoint = "legacy"` deprecated; remove it or set `"regional"`. Will be removed in v7.
- **Inline arguments not removed**: deprecated inline args (`versioning`, `acl`, `server_side_encryption_configuration`, etc.) were **not removed** in 6.0 — they remain deprecated for a future major version. Do not use them; use satellite resources.

Upgrade path: move to latest 5.x, get a clean plan, set `~> 6.0`, run `terraform init -upgrade`, fix S3 items, plan again.
6.48.0 → 6.69.0 contains no S3-scope breaking changes.

## External Resources

All fetched 2026-10-14.

- Provider releases: https://github.com/hashicorp/terraform-provider-aws/releases
- CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- aws_s3_bucket resource doc: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket.html.markdown
- S3 security best practices: https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html
- S3 Block Public Access: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html
- S3 Bucket Namespaces (account-regional): https://docs.aws.amazon.com/AmazonS3/latest/userguide/gpbucketnamespaces.html
- Security Hub S3 controls: https://docs.aws.amazon.com/securityhub/latest/userguide/s3-controls.html
- SSE-C deprecation FAQ: https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-s3-c-encryption-setting-faq.html
- Terraform S3 backend: https://developer.hashicorp.com/terraform/language/backend/s3
- Terraform test: https://developer.hashicorp.com/terraform/language/tests
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
