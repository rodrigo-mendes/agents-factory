---
name: provisioning-aws-cloudwatch-v6
description: "CloudWatch Terraform (aws 6.x): log groups, metric and subscription filters, alarms, dashboards. Use when writing HCL for CloudWatch. Not for X-Ray tracing, CloudTrail, VPC flow logs."
---

# Provisioning AWS CloudWatch with Terraform — hashicorp/aws 6.x

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
| New in 6.64.0 | `warm_up_configuration` block on `aws_cloudwatch_metric_alarm` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| New in 6.69.0 | `evaluation_window` (wall-clock windows) on `aws_cloudwatch_metric_alarm` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- 1.17.0-rc2 exists; do not target it. Re-verify when starting new work.
- 6.57.0 is permanently withdrawn; any pinned constraint that includes it fails init.
- v7 is planned; breaking changes documented in the v6 upgrade guide already.
- CloudWatch Evidently (`aws_evidently_*`) is deprecated; AWS ended support on 2025-10-17.

**Version lock:** this skill locks to the **6.x major line** (suffix `-v6`), reference 6.69.0.
A new major is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Foundation patterns: [terraform block + log group](./blueprints/always-do-foundation.md)
- Alarm patterns: [metric alarm, composite alarm, CIS filters](./blueprints/always-do-alarms.md)
- Security patterns: [subscription filter, data protection, terraform test](./blueprints/always-do-security.md)
- Never-do logs: [log class misuse, immutable fields, deletion protection](./blueprints/never-do-logs.md)
- Never-do alarms: [missing child actions, heredoc whitespace, param conflicts](./blueprints/never-do-alarms.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `~> 6.69` (root) or `>= 6.0` (module) and `~> 1.16` for the CLI constraint** in every `terraform {}` block.
  See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-s3-backend).
- **Use `use_lockfile = true` on the S3 backend** — `dynamodb_table` is deprecated and will be removed.
  See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-s3-backend).
- **Always set `retention_in_days`** on `aws_cloudwatch_log_group` — the default is indefinite retention.
  See [foundation §2](./blueprints/always-do-foundation.md#2-log-group-with-retention-and-deletion-protection).
- **Set `deletion_protection_enabled = false` explicitly** when the group must be deletable — removing
  the argument is not enough; AWS rejects deletion of a protected group with `ValidationException`.
  See [foundation §2](./blueprints/always-do-foundation.md#2-log-group-with-retention-and-deletion-protection).
- **Add `alarm_actions` to every `aws_cloudwatch_metric_alarm`** — Security Hub CloudWatch.15 (High)
  evaluates metric alarms independently; a parent composite alarm does not satisfy it.
  See [alarms §3](./blueprints/always-do-alarms.md#3-metric-alarm-with-required-actions).
- **Keep `actions_enabled = true`** on every alarm — Security Hub CloudWatch.17 (High) checks this field.
  See [alarms §3](./blueprints/always-do-alarms.md#3-metric-alarm-with-required-actions).
- **Wrap `alarm_rule` in `trimspace()`** on `aws_cloudwatch_composite_alarm` — the TF docs forbid
  leading or trailing whitespace; heredocs keep a trailing newline.
  See [alarms §4](./blueprints/always-do-alarms.md#4-composite-alarm-with-trimspace).
- **Prevent subscription filter recursion** — never subscribe a log group that is part of its own
  delivery pipeline (Lambda, Step Functions, Fargate, VPC flow logs).
  See [security §6](./blueprints/always-do-security.md#6-subscription-filter-with-recursion-guard).
- **Use `aws:SourceArn` and `aws:SourceAccount` conditions** in Kinesis/Firehose trust policies for
  subscription filters — confused deputy mitigation.
  See [security §6](./blueprints/always-do-security.md#6-subscription-filter-with-recursion-guard).
- **Run `terraform test` with `mock_provider "aws"` and `command = plan`** for CI-safe unit tests.
  See [security §8](./blueprints/always-do-security.md#8-terraform-test-and-ci).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Log group encryption | Default: server-side AES-256-GCM (no cost, no config). KMS: set `kms_key_id` with a symmetric key; key policy must grant `logs.<region>.amazonaws.com` actions `kms:Encrypt`, `kms:Decrypt`, `kms:ReEncrypt*`, `kms:GenerateDataKey*`, `kms:Describe*`. AWS recommends a separate key per group. ([source](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/encrypt-log-data-kms.html)) | "Should this log group use KMS encryption? If yes, confirm a symmetric key exists and its policy grants the CloudWatch Logs service principal." |
| Log group class | `STANDARD` (all features). `INFREQUENT_ACCESS` (lower ingestion cost, no metric filters/subscription filters/Live Tail/anomaly detection). `DELIVERY` (Lambda logs to S3/Firehose only, 2-day forced retention, no Insights). Class is immutable after creation (M1). ([source](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch_Logs_Log_Classes.html)) | "What log class is needed? Confirm IA workloads do not need filters, and DELIVERY is only for Lambda S3/Firehose." |
| Missing-data treatment | `missing` (default): INSUFFICIENT_DATA only when entire eval range lacks data. `breaching`: continuously-reporting metrics (rollback alarms). `notBreaching`: error-only metrics (DynamoDB ThrottledRequests). ([source](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/alarms-and-missing-data.html)) | "How should missing data be treated? Confirm whether the metric reports continuously or only on error." |
| Subscription filter destination | Lambda: omit `role_arn`, grant via `aws_lambda_permission`. Kinesis: provide `role_arn`. Firehose: AWS-documented but TF page names only Kinesis/Lambda (M2). ([source](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions.html)) | "What is the subscription filter destination? Confirm whether a `role_arn` is required." |
| Composite alarm lifecycle | Destroying a child alarm while a composite depends on it will fail; two-stage updates or `depends_on` may be needed. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_composite_alarm.html.markdown)) | "Will child alarms be destroyed or renamed while this composite alarm exists? If yes, plan a two-stage update." |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Leave `alarm_actions = []` on child metric alarms thinking a composite covers CloudWatch.15. ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/cloudwatch-controls.html)) | Add `alarm_actions` to every `aws_cloudwatch_metric_alarm`. See [never-do-alarms §1](./blueprints/never-do-alarms.md#1-child-alarm-with-empty-actions) |
| Use a heredoc for `alarm_rule` — keeps a trailing newline, violating the no-whitespace requirement. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_composite_alarm.html.markdown)) | `trimspace()` or a one-line string. See [never-do-alarms §2](./blueprints/never-do-alarms.md#2-heredoc-alarm_rule) |
| Set both `statistic` and `extended_statistic` on one alarm — the TF NOTE forbids it. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_metric_alarm.html.markdown)) | Use one or the other. See [never-do-alarms §3](./blueprints/never-do-alarms.md#3-statistic-and-extended_statistic-together) |
| Set top-level `metric_name`/`namespace`/`period`/`statistic` together with `metric_query` blocks. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_metric_alarm.html.markdown)) | Put all metric params inside `metric_query` blocks. See [never-do-alarms §4](./blueprints/never-do-alarms.md#4-metric_query-with-top-level-metric-params) |
| Use `log_group_class = "INFREQUENT_ACCESS"` on groups needing metric or subscription filters. ([source](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch_Logs_Log_Classes.html)) | `STANDARD` class for groups requiring filters. See [never-do-logs §2](./blueprints/never-do-logs.md#2-infrequent_access-with-filters) |
| Use `log_group_class = "DELIVERY"` for non-Lambda workloads. AWS limits it to Lambda logs to S3/Firehose. ([source](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch_Logs_Log_Classes.html)) | `STANDARD` or `INFREQUENT_ACCESS`. See [never-do-logs §1](./blueprints/never-do-logs.md#1-delivery-class-misuse) |
| Set `default_value` and `dimensions` together in `metric_transformation` — they conflict. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_metric_filter.html.markdown)) | Use one or the other per transformation. |
| Pin `version = "6.57.0"` — withdrawn from GitHub and the Registry. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` or any non-withdrawn patch. |
| S3 backend with `dynamodb_table` — deprecated. ([source](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` for native S3 locking. |

## Quick Reference

Sources fetched 2026-10-14.

| Aspect | Value | Source |
|---|---|---|
| Provider constraint (root) | `~> 6.69` | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| CLI constraint | `~> 1.16` | https://developer.hashicorp.com/terraform/language/terraform |
| S3 locking | `use_lockfile = true` (`dynamodb_table` deprecated) | https://developer.hashicorp.com/terraform/language/backend/s3 |
| Log group default encryption | Server-side AES-256-GCM — **not** a KMS CMK | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/encrypt-log-data-kms.html |
| Log group default retention | Indefinite — always set `retention_in_days` | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html |
| Valid `retention_in_days` values | 0, 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_group.html.markdown |
| `DELIVERY` class restriction | Lambda logs to S3/Firehose only; 2-day retention forced; no Insights | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch_Logs_Log_Classes.html |
| `INFREQUENT_ACCESS` limits | No metric filters, subscription filters, Live Tail, anomaly detection | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch_Logs_Log_Classes.html |
| Log class immutability | Cannot change after creation — (medium confidence) TF page is silent on ForceNew (M1) | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch_Logs_Log_Classes.html |
| `treat_missing_data` default | `missing` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_metric_alarm.html.markdown |
| CloudWatch.15 (High) | Metric alarms must have `alarm_actions`; composites do not satisfy this for children | https://docs.aws.amazon.com/securityhub/latest/userguide/cloudwatch-controls.html |
| CloudWatch.16 (Medium) | `retention_in_days >= 365`; `0` (never-expire) is also COMPLIANT | https://docs.aws.amazon.com/config/latest/developerguide/cw-loggroup-retention-period-check.html |
| CloudWatch.17 (High) | `actions_enabled = true` on metric alarms | https://docs.aws.amazon.com/securityhub/latest/userguide/cloudwatch-controls.html |
| Composite `actions_enabled` | Changing it forces a new resource | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_composite_alarm.html.markdown |
| Subscription filter limit | Up to 5 per log group; 1 account-level per region | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions.html |
| `terraform test` CI | `init -backend=false`, `validate -json`, `plan -detailed-exitcode -input=false -out=tfplan` | https://developer.hashicorp.com/terraform/cli/commands/plan |

## 5.x → 6.x Migration (CloudWatch)

Breaking changes in 6.0.0 affecting CloudWatch
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-14):

- **No breaking changes** for `aws_cloudwatch_log_*`, `aws_cloudwatch_metric_alarm`,
  `aws_cloudwatch_composite_alarm` or `aws_cloudwatch_dashboard`.
- **CloudWatch Evidently** (`aws_evidently_*`): deprecated in provider; AWS ended support 2025-10-17.

Notable non-breaking enhancements between 6.48.0 and 6.69.0:
- 6.64.0: `warm_up_configuration` on `aws_cloudwatch_metric_alarm`.
- 6.69.0: `evaluation_window` (wall-clock windows) on `aws_cloudwatch_metric_alarm`.
- 6.56.0: `@source.log` as valid `emit_system_fields` on subscription filters.

Upgrade path: move to latest 5.x, get a clean plan, set `~> 6.0`, run `terraform init -upgrade`.

## External Resources

All fetched 2026-10-14.

- Provider releases: https://github.com/hashicorp/terraform-provider-aws/releases
- CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- CloudWatch Logs encryption: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/encrypt-log-data-kms.html
- CloudWatch Logs classes: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch_Logs_Log_Classes.html
- CloudWatch alarms and missing data: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/alarms-and-missing-data.html
- Security Hub CloudWatch controls: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudwatch-controls.html
- Subscription filter recursion prevention: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions-recursion-prevention.html
- Subscription filter confused deputy: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions-confused-deputy.html
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
