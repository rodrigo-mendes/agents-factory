---
name: provisioning-aws-dynamodb-v6
description: "DynamoDB Terraform (aws 6.x): tables, indexes, PITR, encryption, autoscaling, global tables. Use when writing HCL for DynamoDB. Not for KMS, IAM, Lambda, CloudWatch."
---

# Provisioning AWS DynamoDB with Terraform — hashicorp/aws 6.x

> Version lock: `-v6` = the **6.x major line**; reference patch 6.69.0/6.70.0 + **Terraform ~> 1.16**.
> Research date **2026-10-23**. Claims tagged (unverified) or (medium confidence) were not fully
> confirmed against an official page. Sibling skills: provisioning-aws-kms-v6 (keys),
> provisioning-aws-iam-v6 (roles, policies), provisioning-aws-lambda-v6, provisioning-aws-cloudwatch-v6.

## Version Context

| Item | Value | Source (fetched 2026-10-23) |
|---|---|---|
| Terraform CLI | `~> 1.16` (1.16.6); 1.17.0 is stable since 2026-10-21 but not the target | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | latest 6.70.0 (2026-10-23) | https://releases.hashicorp.com/terraform-provider-aws/ |
| Provider constraint | root modules `~>` (this skill: `~> 6.69`, allows 6.70.x); reusable modules `>=` minimum only | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| 6.57.0 | **Withdrawn** from GitHub and Registry — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Region | Regional resources accept optional `region` (DynamoDB is regional); changing it forces replacement | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |
| State locking | `use_lockfile = true`; `dynamodb_table` is deprecated | https://developer.hashicorp.com/terraform/language/backend/s3 |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 became stable on 2026-10-21 (not the target); re-verify before moving.
- 6.57.0 is permanently withdrawn; v7 is planned and would be a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Foundation: [terraform block, backend, table, data protection, throughput](./blueprints/always-do-foundation.md)
- Indexes and capacity: [GSI/LSI, auto scaling](./blueprints/always-do-indexes-capacity.md)
- Replication and satellites: [global tables v2, policy, Kinesis, tests](./blueprints/always-do-replication-satellites.md)
- Never-do table and indexes: [attributes, GSI mixing, warm throughput, key ARN](./blueprints/never-do-table-indexes.md)
- Never-do replication and provider: [replicas, table items, backend, version](./blueprints/never-do-replication-provider.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Constrain the provider with `~>` in root modules (this skill uses `~> 6.69`); reusable modules set only `>=`.**
  See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-s3-backend). Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints
- **Set `required_version = "~> 1.16"`** (Terraform 1.16.6 is the target).
  See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-s3-backend). Source: https://releases.hashicorp.com/terraform/
- **Use `use_lockfile = true` on the S3 backend** — `dynamodb_table` locking is deprecated.
  See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-s3-backend). Source: https://developer.hashicorp.com/terraform/language/backend/s3
- **Set `billing_mode` explicitly** — the default is `PROVISIONED`.
  See [foundation §2](./blueprints/always-do-foundation.md#2-table-keys-billing-and-data-protection). Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown
- **Define `attribute` blocks only for table, LSI and GSI key attributes.**
  See [foundation §2](./blueprints/always-do-foundation.md#2-table-keys-billing-and-data-protection). Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown
- **Pass `kms_key_arn` only for a customer managed key** (keys other than `alias/aws/dynamodb`).
  See [foundation §2](./blueprints/always-do-foundation.md#2-table-keys-billing-and-data-protection). Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown
- **Use `key_schema` blocks on inline `global_secondary_index`** — `hash_key`/`range_key` are marked deprecated on the table page.
  See [indexes §3](./blueprints/always-do-indexes-capacity.md#3-secondary-indexes). Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown
- **Add `lifecycle { ignore_changes = [read_capacity, write_capacity] }` when an App Auto Scaling policy is attached to the table.**
  See [indexes §4](./blueprints/always-do-indexes-capacity.md#4-auto-scaling-for-provisioned-tables). Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown
- **Set `policy_type = "TargetTrackingScaling"` on DynamoDB scaling policies** — the default is `StepScaling`.
  See [indexes §4](./blueprints/always-do-indexes-capacity.md#4-auto-scaling-for-provisioned-tables). Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/appautoscaling_policy.html.markdown
- **Use `replica` blocks of `aws_dynamodb_table` for Global Tables V2** — the V1 resource page names them for V2; keep one replica mechanism per table.
  See [replication §6](./blueprints/always-do-replication-satellites.md#6-global-tables-v2-replicas). Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_global_table.html.markdown
- **Use provider >= 6.57.1 when tuning `warm_throughput`** — lowering it no longer replaces the table.
  See [foundation §5](./blueprints/always-do-foundation.md#5-on-demand-and-warm-throughput). Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- **Run `terraform test` with `mock_provider "aws"` and `command = plan`.**
  See [replication §8](./blueprints/always-do-replication-satellites.md#8-terraform-test). Source: https://developer.hashicorp.com/terraform/language/tests/mocking

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Billing mode | `PAY_PER_REQUEST`, or `PROVISIONED` with App Auto Scaling target and policy. Security Hub DynamoDB.1 is "Tables should automatically scale capacity with demand" (Config rule `dynamodb-autoscaling-enabled`). ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/dynamodb-controls.html)) | "On-demand billing, or provisioned capacity with auto scaling?" |
| Deletion protection and PITR | `deletion_protection_enabled` defaults to `false` (Security Hub DynamoDB.6 checks it); `point_in_time_recovery` is off when the block is absent (DynamoDB.2 checks it), provider `recovery_period_in_days` defaults to 35. ([table page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown), [controls](https://docs.aws.amazon.com/securityhub/latest/userguide/dynamodb-controls.html)). AWS states a 1-35 day period, restores always create a new table, and decreasing the period drops older restore points. ([source](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery_Howitworks.html)) | "Enable deletion protection and PITR? Which recovery period?" |
| Encryption key | AWS owned (default, free), AWS managed, or customer managed (KMS charges); switchable at any time. ([source](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/EncryptionAtRest.html)) The Security Hub controls DynamoDB.1, .2, .4, .5 and .6 do not mention a customer managed key; DynamoDB.3 and .7 concern DAX (medium confidence, absence of evidence). ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/dynamodb-controls.html)) | "Which key type? A customer managed key is created in provisioning-aws-kms-v6." |
| Separate global index resource | `aws_dynamodb_global_secondary_index` gives finer GSI lifecycle control but cannot be mixed with inline blocks; the table page calls it "experimental" while the resource page shows no warning (medium confidence). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_global_secondary_index.html.markdown)) | "Inline GSI blocks, or the separate resource?" |
| Global table shape | `replica` blocks: `consistency_mode` `EVENTUAL` (default) or `STRONG`; `global_table_witness` only with exactly one `STRONG` replica; `kms_key_arn` change recreates the replica. `aws_dynamodb_global_table` manages V1 (2017.11.29); its page says to use `replica` for V2 and warns of "many restrictions". ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_global_table.html.markdown)) | "Which regions and consistency mode? Is a V1 table involved?" |
| Backup coverage | Security Hub DynamoDB.4 expects the table in a backup plan (AWS Backup); the on-demand backup resource was not researched. ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/dynamodb-controls.html)) | "Should the table be added to an AWS Backup plan?" |
| Settings the docs leave open | Write-capacity autoscaling metric name (unverified); Kinesis `approximate_creation_date_time_precision` default (unverified); contributor insights `mode` values (unverified); TTL deletion timing (unverified). | "Confirm against current docs before use — which value do you want?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Add `attribute` blocks for non-key attributes — "infinite plan loop". ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown)) | Define attributes only for table, LSI and GSI keys |
| Mix inline `global_secondary_index` blocks with `aws_dynamodb_global_secondary_index` — "conflicts, perpetual differences, and Global Secondary Indexes being overwritten". ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_global_secondary_index.html.markdown)) | One mechanism per table |
| Use inline GSI `hash_key`/`range_key` — marked deprecated on the table page. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown)) | `key_schema` blocks |
| Set both `warm_throughput` values explicitly to 12000/4000 — causes reported diffs. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown)) | Omit the block |
| Set `kms_key_arn` to the `alias/aws/dynamodb` key — the argument is for other keys. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown)) | Omit `kms_key_arn` for the AWS managed key, or pass a customer managed key ARN |
| Mix `replica` blocks with `aws_dynamodb_table_replica`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown)) | One mechanism; with the replica resource set `ignore_changes = [replica]` on the table |
| Manage large amounts of data with `aws_dynamodb_table_item`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table_item.html.markdown)) | Keep the resource to a few seed items |
| S3 backend with `dynamodb_table` — deprecated. ([source](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` |
| Pin `version = "6.57.0"` — withdrawn. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` or any non-withdrawn patch |

## Quick Reference

Sources fetched 2026-10-23.

| Aspect | Value | Source |
|---|---|---|
| Provider constraint (root) | `~>` style; this skill uses `~> 6.69` (a choice) | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| S3 locking | `use_lockfile = true` | https://developer.hashicorp.com/terraform/language/backend/s3 |
| Billing mode | `PROVISIONED` (default) or `PAY_PER_REQUEST` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown |
| PITR (provider) | `recovery_period_in_days` default 35 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown |
| PITR (AWS) | recovery period 1–35 days; restore creates a new table | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery_Howitworks.html |
| Default encryption | AWS owned key; `enabled = true` alone = AWS managed `alias/aws/dynamodb` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown |
| Warm throughput | minimum and default 12000 read / 4000 write | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown |
| Separate GSI resource args | `table_name`, `index_name`, `key_schema`, `projection`, `provisioned_throughput` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_global_secondary_index.html.markdown |
| Auto scaling target | `service_namespace = "dynamodb"`; `resource_id = "table/<name>"` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/appautoscaling_target.html.markdown |
| Auto scaling policy | `policy_type` defaults to `StepScaling`; set `TargetTrackingScaling` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/appautoscaling_policy.html.markdown |
| Resource policy | 20 KB limit including whitespace | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_resource_policy.html.markdown |
| Table export | PITR must be enabled | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table_export.html.markdown |
| Security Hub controls | DynamoDB.1 autoscale, .2 PITR, .4 backup plan, .5 tags, .6 deletion protection | https://docs.aws.amazon.com/securityhub/latest/userguide/dynamodb-controls.html |
| Table timeouts | create 30m, update 60m, delete 10m; import ID = table name | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown |

## 5.x → 6.x Migration (DynamoDB)

The 6.0.0 upgrade guide has no item mentioning DynamoDB or Application Auto Scaling, so no
`aws_dynamodb_*` or `aws_appautoscaling_*` argument was removed or renamed there
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-23).
Changes found in 6.x ([CHANGELOG](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md), 2026-10-23):

- **GSI `hash_key`/`range_key`**: deprecated on the table page in favor of `key_schema`.
- **6.52.0**: `aws_dynamodb_table_item` gains list resource, Resource Identity and import support.
- **6.57.1**: lowering `warm_throughput` no longer replaces the table.
- **6.67.0**: eventual-consistency fix for `list-resource/aws_dynamodb_table_replica` on replace.
- **`recovery_period_in_days`**: the version that introduced it is (unverified); do not call it new.
- **State locking**: replace S3 backend `dynamodb_table` with `use_lockfile = true`.

Upgrade path: get a clean plan on the latest 5.x, set `~> 6.69`, run `terraform init -upgrade`.

## External Resources

All fetched 2026-10-23.

- Provider releases: https://releases.hashicorp.com/terraform-provider-aws/
- CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- Security Hub DynamoDB controls: https://docs.aws.amazon.com/securityhub/latest/userguide/dynamodb-controls.html
- DynamoDB encryption at rest: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/EncryptionAtRest.html
- DynamoDB PITR: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery_Howitworks.html
- Terraform S3 backend: https://developer.hashicorp.com/terraform/language/backend/s3
- Terraform test: https://developer.hashicorp.com/terraform/language/tests
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
