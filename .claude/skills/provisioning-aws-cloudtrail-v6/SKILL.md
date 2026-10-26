---
name: provisioning-aws-cloudtrail-v6
description: "CloudTrail Terraform (aws 6.x): trails, log bucket and KMS policies, event data stores, delegated admin. Use when writing HCL for CloudTrail. Not for S3, KMS, CloudWatch, Organizations."
---

# Provisioning AWS CloudTrail with Terraform — hashicorp/aws 6.x

> Version lock: every claim applies to **hashicorp/aws 6.x** (reference patch 6.69.0/6.70.0) +
> **Terraform ~> 1.16** only. Research date **2026-10-23**. Claims tagged (unverified) or
> (medium confidence) were not fully confirmed against an official page.

## Version Context

| Item | Value | Source (fetched 2026-10-23) |
|---|---|---|
| Terraform CLI | `~> 1.16`; 1.17.0 is stable but not the target | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | latest 6.70.0; constraint `~> 6.69`; no 7.x released | https://releases.hashicorp.com/terraform-provider-aws/ |
| 6.57.0 | **Withdrawn** from GitHub and the Registry — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Region model | `aws_cloudtrail` and `aws_cloudtrail_event_data_store` accept optional `region` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown |
| Global exception | `aws_cloudtrail_organization_delegated_admin_account` has no `region` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |
| CloudTrail Lake | closed to new customers since 2026-05-31; existing customers continue | https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake.html |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 became stable on 2026-10-21; this skill still targets `~> 1.16`. Re-verify when starting new work.
- 6.57.0 is permanently withdrawn; a constraint that resolves to it fails init.
- v7 is not released; when it ships, write a new skill (`provisioning-aws-cloudtrail-v7`).

**Version lock:** `-v6` = the 6.x major line, reference patch 6.69.0/6.70.0, Terraform `~> 1.16`.
A new major is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Trail patterns: [Terraform block, log bucket and policy, trail](./blueprints/always-do-trail.md)
- KMS/Lake patterns: [key policy, event data store, delegated admin, tests](./blueprints/always-do-kms-lake.md)
- Never-do trail: [selectors, `:*`, encryption, bucket policy, channel](./blueprints/never-do-trail.md)
- Never-do provider/migration: [`.name`, `suspend`, global `region`, backend, 6.57.0, Lake key](./blueprints/never-do-provider-migration.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Set `kms_key_id` on every trail** — Security Hub CloudTrail.2 fails when `KmsKeyId` is undefined: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html.
  See [trail §3](./blueprints/always-do-trail.md#3-the-trail).
- **Set `is_multi_region_trail = true`** — Security Hub CloudTrail.1 needs a multi-Region trail: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html.
  See [trail §3](./blueprints/always-do-trail.md#3-the-trail).
- **Set `enable_log_file_validation = true`** — it defaults to `false`: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown.
  See [trail §3](./blueprints/always-do-trail.md#3-the-trail).
- **End `cloud_watch_logs_group_arn` with `:*`** — the argument must include the log stream wildcard: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown.
  See [trail §3](./blueprints/always-do-trail.md#3-the-trail).
- **Add `depends_on = [aws_s3_bucket_policy.…]` on the trail** — the bucket policy must exist before the trail: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown.
  See [trail §3](./blueprints/always-do-trail.md#3-the-trail).
- **Add `aws:SourceArn` (the trail ARN) to the bucket policy statements** — AWS lists it as a security best practice: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html.
  See [trail §2](./blueprints/always-do-trail.md#2-log-bucket-hardening-and-bucket-policy).
- **Keep the bucket policy prefix equal to `s3_key_prefix`** — a mismatch gives "There is a problem with the bucket policy": https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html.
  See [trail §2](./blueprints/always-do-trail.md#2-log-bucket-hardening-and-bucket-policy).
- **Enable all four S3 Block Public Access settings on the log bucket** — Security Hub CloudTrail.6 (Critical) checks them: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html.
  See [trail §2](./blueprints/always-do-trail.md#2-log-bucket-hardening-and-bucket-policy).
- **Enable S3 server access logging on the log bucket** — Security Hub CloudTrail.7: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html.
  See [trail §2](./blueprints/always-do-trail.md#2-log-bucket-hardening-and-bucket-policy).
- **Give the key policy encrypt, decrypt and describe sections** — trails need all three: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-kms-key-policy-for-cloudtrail.html.
  See [kms-lake §4](./blueprints/always-do-kms-lake.md#4-kms-key-policy-for-the-trail).
- **Tag the trail** — Security Hub CloudTrail.9 checks `requiredTagKeys`: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html.
  See [trail §3](./blueprints/always-do-trail.md#3-the-trail).
- **Create an organization trail only in the management account** — `is_organization_trail` is creatable only there: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown.
  See [trail §2](./blueprints/always-do-trail.md#2-log-bucket-hardening-and-bucket-policy).
- **Set `kms_key_id` on the event data store at creation** — AWS says the key cannot be removed or changed afterwards: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake.html.
  See [kms-lake §5](./blueprints/always-do-kms-lake.md#5-event-data-store-cloudtrail-lake).
- **Add the event data store key-policy conditions after the store exists** — they use the store ID in `aws:SourceArn`: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-kms-key-policy-for-cloudtrail.html.
  See [kms-lake §5](./blueprints/always-do-kms-lake.md#5-event-data-store-cloudtrail-lake).
- **Use `data.aws_region.current.region`** — `name` was deprecated in 6.0: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown.
  See [trail §1](./blueprints/always-do-trail.md#1-terraform-block-and-region).
- **Use `use_lockfile = true` on the S3 backend** — `dynamodb_table` is deprecated: https://developer.hashicorp.com/terraform/language/backend/s3.
  See [trail §1](./blueprints/always-do-trail.md#1-terraform-block-and-region).
- **Omit `region` on the organization delegated admin account** — it is global: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown.
  See [kms-lake §6](./blueprints/always-do-kms-lake.md#6-organization-delegated-administrator-global).
- **Run `terraform test` with `mock_provider "aws"` and `command = plan`** for CI-safe tests: https://developer.hashicorp.com/terraform/language/tests.
  See [kms-lake §7](./blueprints/always-do-kms-lake.md#7-terraform-test-and-ci).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Selector type for data events | `event_selector` (S3 object, Lambda function, DynamoDB table data resources) or `advanced_event_selector` (`field_selector` fields); the two conflict. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown)) | "Which selector type should this trail use, and which data events are needed?" |
| Account trail vs organization trail | Organization trail: `is_organization_trail = true`, management account only, extra `AWSLogs/<o-organizationID>/*` bucket statement. ([source](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html)) | "Is this an organization trail created from the management account?" |
| Use CloudTrail Lake | Closed to new customers since 2026-05-31; only onboarded accounts can use `aws_cloudtrail_event_data_store`. ([source](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake.html)) | "Is this account already onboarded to CloudTrail Lake?" |
| Event data store retention and billing | `retention_period` 2555 days on the provider page (medium confidence); `billing_mode` `EXTENDABLE_RETENTION_PRICING` or `FIXED_RETENTION_PRICING`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_event_data_store.html.markdown)) | "What retention period and billing mode does the store need?" |
| Event data store termination protection | `termination_protection_enabled` defaults to `true`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_event_data_store.html.markdown)) | "Should termination protection stay on?" |
| Insights | `insight_selector` takes `ApiCallRateInsight` or `ApiErrorRateInsight`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown)) | "Which Insights types should be enabled?" |
| SNS topic in another region | `sns_topic_name` must be the ARN if the topic is in a different region. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown)) | "Is the SNS topic in the trail's region?" |
| Default log encryption | Two AWS pages disagree on the default (medium confidence); always set `kms_key_id`. ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html)) | "Which KMS key ARN should encrypt the trail?" |
| Channel integration | `aws_cloudtrail_channel` has no provider doc page (404) (unverified); do not write HCL. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_channel.html.markdown)) | "How does this integrate with CloudTrail Lake channels?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Set `event_selector` and `advanced_event_selector` on one trail — they conflict. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown)) | Use only one selector type |
| Write `cloud_watch_logs_group_arn` without `:*`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown)) | `"${aws_cloudwatch_log_group.x.arn}:*"` |
| Write a bucket policy prefix that differs from `s3_key_prefix` — gives "There is a problem with the bucket policy". ([source](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html)) | Use the same prefix in both |
| Use a Requester Pays bucket for trail logs. ([source](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html)) | A dedicated, non-Requester-Pays bucket |
| Set `region` on `aws_cloudtrail_organization_delegated_admin_account`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown)) | Omit `region`; import by account ID only |
| Use `data.aws_region.current.name` in ARNs — deprecated in 6.0. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown)) | `.region` |
| Set `suspend = 0` or `1` on an event data store. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown)) | `""`, `true` or `false` |
| Plan to remove or change the event data store KMS key after association. ([source](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake.html)) | Choose the key at creation |
| S3 backend with `dynamodb_table` — deprecated. ([source](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` |
| Pin `version = "6.57.0"` — withdrawn. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` |

## Quick Reference

Sources fetched 2026-10-23.

| Aspect | Value | Source |
|---|---|---|
| Provider constraint (root) | `~> 6.69` | https://releases.hashicorp.com/terraform-provider-aws/ |
| CLI constraint | `~> 1.16` | https://releases.hashicorp.com/terraform/ |
| Trail required args | `name`, `s3_bucket_name` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown |
| Trail defaults | `is_multi_region_trail` false; `include_global_service_events` true; `enable_log_file_validation` false; `enable_logging` true; `is_organization_trail` false | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown |
| Trail ARN import | `arn:aws:cloudtrail:<region>:<account>:trail/<name>` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown |
| Event data store defaults | `retention_period` 2555 (medium confidence); `termination_protection_enabled` true; `multi_region_enabled` true; `organization_enabled` false | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_event_data_store.html.markdown |
| Event data store import | `arn:aws:cloudtrail:<region>:<account>:eventdatastore/<id>`; timeouts 5m | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_event_data_store.html.markdown |
| Delegated admin | required `account_id`; global, no `region` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_organization_delegated_admin_account.html.markdown |
| Bucket policy principal | `cloudtrail.amazonaws.com`: `s3:GetBucketAcl` + `s3:PutObject` (`bucket-owner-full-control`) | https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html |
| Security Hub CT.1 / CT.2 / CT.4 / CT.5 | multi-Region trail / encryption / log validation / CloudWatch Logs | https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html |
| Security Hub CT.6 / CT.7 / CT.9 / CT.10 | bucket not public / access logging / tags / store CMK | https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html |
| Identity import | `identity { arn }` needs Terraform >= 1.12.0 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown |

## 5.x → 6.x Migration (CloudTrail)

Changes in 6.0.0 that affect CloudTrail work
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-23):

- **`aws_cloudtrail_event_data_store`**: appears only in the Nullable Boolean Validation Update table for `suspend` — use `""`, `true` or `false`.
- **`data.aws_region`**: `name` deprecated → `.region`.
- No upgrade-guide entry for `aws_cloudtrail`, `aws_cloudtrail_organization_delegated_admin_account` or `data.aws_cloudtrail_service_account`.
- Changelog 6.48.0 → 6.70.0: no CloudTrail entries found (medium confidence).

## External Resources

All fetched 2026-10-23.

- Trail docs: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown
- Event data store docs: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_event_data_store.html.markdown
- Delegated admin docs: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_organization_delegated_admin_account.html.markdown
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- AWS CloudTrail — S3 bucket policy: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html
- AWS CloudTrail — KMS key policy: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-kms-key-policy-for-cloudtrail.html
- AWS CloudTrail — security best practices: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html
- Security Hub CloudTrail controls: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
