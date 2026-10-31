---
name: provisioning-aws-eventbridge-v6
description: "EventBridge Terraform (aws 6.x): buses, rules, targets, archives, API destinations, Scheduler, pipes. Use when writing HCL for EventBridge. Not for Lambda, SQS, SNS, Step Functions, IAM."
---

# Provisioning AWS EventBridge with Terraform — hashicorp/aws 6.x

> Version lock: every claim applies to **hashicorp/aws 6.x** (reference patch 6.69.0 / 6.70.0) + **Terraform ~> 1.16** only.
> `-v6` = the 6.x major line. Each source carries its own read date (2026-10-22 or 2026-10-23).
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page.
> EventBridge was formerly known as CloudWatch Events; the resource prefix stays `aws_cloudwatch_event_*`
> ([page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_rule.html.markdown)).

## Version Context

| Item | Value | Source (read date) |
|---|---|---|
| Terraform CLI | this skill targets `~> 1.16` (1.16.6 released 2026-10-14) | https://releases.hashicorp.com/terraform/ (2026-10-23) |
| Terraform 1.17.0 | stable since 2026-10-21; not this skill's target | https://releases.hashicorp.com/terraform/ (2026-10-23); https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md (2026-10-23) |
| hashicorp/aws | latest 6.70.0; this skill targets `~> 6.69`; no 7.x released | https://releases.hashicorp.com/terraform-provider-aws/ (2026-10-23) |
| 6.57.0 | Withdrawn from GitHub and the Registry — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md (2026-10-23) |
| Provider constraint | `~>` in root modules; a minimum (`>=`) only in reusable modules | https://developer.hashicorp.com/terraform/language/expressions/version-constraints (2026-10-23) |
| Region | In-scope resources document an optional `region` (default: provider Region); changing it forces replacement | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown (2026-10-23) |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 is stable since 2026-10-21 ([releases](https://releases.hashicorp.com/terraform/), read 2026-10-23); this skill still targets `~> 1.16`.
- 6.57.0 is withdrawn from GitHub and the Registry; never pin it.
- The [upgrade guide](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown) (read 2026-10-23) says `s3_us_east_1_regional_endpoint` "will be removed in `v7.0.0`"; no 7.x release exists. A v7 = a new skill.

**Version lock:** this skill locks to the **6.x major line** (suffix `-v6`), reference patch 6.69.0/6.70.0,
Terraform ~> 1.16. A new major is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Foundation patterns: [Terraform block, bus, bus policy, archive](./blueprints/always-do-foundation.md)
- Rules and targets: [rule, target, retry, DLQ, input transformer, Lambda permission](./blueprints/always-do-rules-targets.md)
- Scheduler and integrations: [connection, API destination, schedule, pipe](./blueprints/always-do-scheduler-integrations.md)
- Never-do bus and rules: [policy vs permission, schedules, `is_enabled`](./blueprints/never-do-bus-and-rules.md)
- Never-do targets: [Logs role, input, DLQ, permissions, `role_arn`](./blueprints/never-do-targets.md)
- Never-do scheduler and versions: [schedule role, backend, withdrawn version](./blueprints/never-do-scheduler-and-versions.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `~>` constraints in the root module** — [version constraints](https://developer.hashicorp.com/terraform/language/expressions/version-constraints). See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-s3-backend).
- **Pin `required_version = "~> 1.16"`** — this skill's target, not a page claim ([releases](https://releases.hashicorp.com/terraform/)). See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-s3-backend).
- **Pin `version = "~> 6.69"`** — this skill's target, not a page claim ([releases](https://releases.hashicorp.com/terraform-provider-aws/)). See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-s3-backend).
- **Use `use_lockfile = true` on the S3 backend** — [S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3). See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-s3-backend).
- **Set `state` on `aws_cloudwatch_event_rule`** — `is_enabled` is deprecated in its favor ([rule page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_rule.html.markdown)). See [rules §3](./blueprints/always-do-rules-targets.md#3-rule).
- **Set `event_pattern` or `schedule_expression` on every rule** — at least one is required ([rule page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_rule.html.markdown)). See [rules §3](./blueprints/always-do-rules-targets.md#3-rule).
- **Filter event patterns on `source` and `detail-type`** ([AWS best practices](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-patterns-best-practices.html)). See [rules §3](./blueprints/always-do-rules-targets.md#3-rule).
- **Set the target's `event_bus_name` to the rule's bus** ([target page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_target.html.markdown)). See [rules §4](./blueprints/always-do-rules-targets.md#4-target-with-retry-dlq-and-input-transformer).
- **Write `input_template` as valid JSON, escaped for both JSON and Terraform** ([target page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_target.html.markdown)). See [rules §4](./blueprints/always-do-rules-targets.md#4-target-with-retry-dlq-and-input-transformer).
- **Use a standard SQS queue in the rule's Region as the DLQ** ([DLQ page](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html)). See [rules §4](./blueprints/always-do-rules-targets.md#4-target-with-retry-dlq-and-input-transformer).
- **Grant the DLQ queue policy yourself** — the console does it automatically, but not when you create the target through the API ([DLQ page](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html)). See [rules §4](./blueprints/always-do-rules-targets.md#4-target-with-retry-dlq-and-input-transformer).
- **Give a Lambda target a permission path: a resource-based policy (`aws_lambda_permission`, principal `events.amazonaws.com`) or a `role_arn` with an execution role** ([AWS page](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html)). See [rules §4](./blueprints/always-do-rules-targets.md#4-target-with-retry-dlq-and-input-transformer).
- **Prefer EventBridge Scheduler for schedules** — AWS calls scheduled rules a legacy feature and recommends Scheduler ([AWS page](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html)). See [scheduler §6](./blueprints/always-do-scheduler-integrations.md#6-scheduler-schedule-and-group).
- **Tag event buses** — Security Hub control EventBridge.2 checks it ([controls](https://docs.aws.amazon.com/securityhub/latest/userguide/eventbridge-controls.html)). See [foundation §2](./blueprints/always-do-foundation.md#2-bus-bus-policy-and-archive).
- **Consider a resource-based policy on custom buses** — Security Hub control EventBridge.3 checks for one ([controls](https://docs.aws.amazon.com/securityhub/latest/userguide/eventbridge-controls.html)). See [foundation §2](./blueprints/always-do-foundation.md#2-bus-bus-policy-and-archive).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Scheduled rule vs Scheduler | AWS recommends Scheduler; scheduled rules use UTC+0 only with a minimum precision of one minute and exist only on the default bus ([AWS page](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html)). | "Should this schedule use `aws_scheduler_schedule` (recommended) or a scheduled rule?" |
| Cross-account access on a bus | Bus policy and `aws_cloudwatch_event_permission` are mutually incompatible; the permission resource takes `principal = "*"` only with an `aws:PrincipalOrgID` condition ([permission page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_permission.html.markdown)). | "Policy document or permission resources for this bus? Which accounts or organization?" |
| Targets per rule | AWS allows up to 5 targets per rule and recommends duplicating the rule instead ([AWS page](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rules-best-practices.html)). | "One target per rule (recommended) or several?" |
| Archive retention | Omit `retention_days` for indefinite retention (unverified). | "How many days must archived events be kept, or indefinitely?" |
| Connection authentication | The connection page has internal inconsistencies about `connectivity_parameters` placement (unverified). | "Which authorization type? Verify argument layout against the current page before applying." |
| Events from AWS services on a custom bus | Whether AWS service events reach a non-default bus is not confirmed (unverified). | "Which bus will the source publish to? Confirm in the source service's docs." |
| Target ID scope | The import format `bus/rule/target_id` suggests an ID identifies one target per rule per bus (medium confidence). | "Confirm target IDs are unique per rule." |
| SNS and Lambda resource policies | The `source_arn` on `aws_lambda_permission` mapped to the rule ARN (medium confidence); the AWS SNS sample has no `aws:SourceArn` condition, adding one is (medium confidence). | "Restrict the resource policy to the rule ARN?" |
| Global endpoints | EventBridge.4 asks for event replication on global endpoints; the endpoint resource was not read (unverified). | "Are global endpoints in scope? Read the endpoint resource page first." |
| Rule-target retry limits | Numeric limits are not on the provider page; Scheduler documents 60–86400 s and 0–185 attempts (unverified for rule targets). | "Which retry limits are required for rule targets?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Manage one bus with both `aws_cloudwatch_event_bus_policy` and `aws_cloudwatch_event_permission` — the policy resource "is incompatible with the EventBridge permission resource and will overwrite permissions". ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_bus_policy.html.markdown)) | Pick one of the two resources per bus |
| Set `schedule_expression` on a rule whose `event_bus_name` is not the default bus — it works only on the default bus. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_rule.html.markdown)) | Keep scheduled rules on the default bus, or use `aws_scheduler_schedule` |
| Use `is_enabled` on a rule — deprecated, conflicts with `state`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_rule.html.markdown)) | `state = "ENABLED"` or `"DISABLED"` |
| Set `role_arn` on a CloudWatch Logs target — Logs targets use resource-based policies. ([source](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html)) | Omit `role_arn`; grant `events.amazonaws.com` and `delivery.logs.amazonaws.com` `logs:CreateLogStream` and `logs:PutLogEvents` through a resource-based policy |
| Combine `input`, `input_path` and `input_transformer` on one target — they are mutually exclusive. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_target.html.markdown)) | Use exactly one of the three |
| Use a FIFO queue or a queue in another Region as a DLQ. ([source](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html)) | A standard SQS queue in the same Region as the rule |
| Target a Lambda function or SNS topic with no permission path — neither a resource-based policy nor a `role_arn` with an execution role. ([provider page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_target.html.markdown), [AWS page](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html)) | Grant a resource-based policy (`aws_lambda_permission` / `aws_sns_topic_policy`) or set `role_arn` with an execution role |
| Omit `role_arn` on a target that is an `ecs_target`, EC2 instance, Kinesis stream, Step Functions state machine, or an event bus in another account or Region. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_target.html.markdown)) | Set `role_arn` on those targets |
| Omit `role_arn` in the `target` block of `aws_scheduler_schedule` — it is required. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/scheduler_schedule.html.markdown)) | Set `target { role_arn = … }` |
| Use `dynamodb_table` in the S3 backend — deprecated. ([source](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` |
| Pin `version = "6.57.0"` — withdrawn from GitHub and the Registry. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` |

## Quick Reference

| Aspect | Value | Source (read date) |
|---|---|---|
| Rule trigger | at least one of `schedule_expression` or `event_pattern` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_rule.html.markdown (2026-10-23) |
| Rule `state` | `ENABLED` (default), `DISABLED`, `ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS` (not combinable with `schedule_expression`) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_rule.html.markdown (2026-10-23) |
| `event_pattern` size | page: 2048 characters by default, 4096 through a service-quota request | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_rule.html.markdown (2026-10-23) |
| Default retry | 24 hours and up to 185 attempts, then the event is dropped | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html (2026-10-23) |
| Errors sent straight to the DLQ | missing permissions, target no longer exists, invalid address / DNS failure | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html (2026-10-23) |
| Scheduler retry | `maximum_event_age_in_seconds` 60–86400 (default 86400); `maximum_retry_attempts` 0–185 (default 185) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/scheduler_schedule.html.markdown (2026-10-23) |
| Scheduler time zone | `schedule_expression_timezone` defaults to `UTC` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/scheduler_schedule.html.markdown (2026-10-23) |
| Scheduler `group_name` | default `default`; forces new resource | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/scheduler_schedule.html.markdown (2026-10-23) |
| API destination rate | `invocation_rate_limit_per_second` default 300 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_api_destination.html.markdown (2026-10-23) |
| Archive retention | omit `retention_days` to archive indefinitely | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_archive.html.markdown (2026-10-23) |
| Pipes resource policies | Pipes does not support resource-based policies | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html (2026-10-23) |
| Security Hub controls | EventBridge.2 (tagged buses), EventBridge.3 (custom bus policy), EventBridge.4 (global endpoint replication) | https://docs.aws.amazon.com/securityhub/latest/userguide/eventbridge-controls.html (2026-10-23) |
| Resource identity | 6.54.0 added it to seven `aws_cloudwatch_event_*` resources and made `aws_scheduler_schedule` a list resource | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md (2026-10-23) |
| Identity import | `identity` blocks need Terraform ≥ 1.12.0 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc.html.markdown (2026-10-23) |

## 5.x → 6.x Migration (EventBridge)

([upgrade guide](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), read 2026-10-23):

- No item for `aws_cloudwatch_event_*`, `aws_scheduler_*` or `aws_pipes_pipe`.
- `is_enabled` on `aws_cloudwatch_event_rule` is deprecated, not removed; use `state` ([rule page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_rule.html.markdown)).
- [CHANGELOG](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md) 6.54.0 (2026-07-08): resource identity for `aws_cloudwatch_event_api_destination`, `_archive`, `_bus`, `_bus_policy`, `_connection`, `_endpoint`, `_permission`; `aws_scheduler_schedule` gains identity and becomes a list resource.
- CHANGELOG 6.66.0 (2026-09-21): `aws_pipes_pipe` no longer sends an unset `server_root_ca_certificate` as an empty string (it had made `UpdatePipe` fail).
- No breaking changes were found in the CHANGELOG ranges read (6.48.0–6.70.0) for the scoped resources (absence of evidence, not a guarantee).

Upgrade path: the [upgrade guide](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown) says: "Before upgrading to version `6.0.0`, first upgrade to the latest available `5.x` version of the provider"; confirm a plan completes "without errors or unexpected changes"; update version constraints "to allow the `6.x` series"; run `terraform init -upgrade` "to download the new version". This skill uses `~> 6.69`.

## External Resources

Read dates in parentheses.

- Version 6 upgrade guide (2026-10-23): https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- CHANGELOG (2026-10-23): https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- Rule (2026-10-23): https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_rule.html.markdown
- Target (2026-10-23): https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_target.html.markdown
- Scheduler schedule (2026-10-23): https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/scheduler_schedule.html.markdown
- AWS — resource-based policies (2026-10-23): https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html
- AWS — DLQ (2026-10-23): https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html
- AWS — retry policy (2026-10-23): https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html
- Security Hub EventBridge controls (2026-10-23): https://docs.aws.amazon.com/securityhub/latest/userguide/eventbridge-controls.html
- Terraform S3 backend (2026-10-23): https://developer.hashicorp.com/terraform/language/backend/s3
- Related skills: provisioning-aws-lambda-v6, provisioning-aws-sqs-v6, provisioning-aws-sns-v6, provisioning-aws-step-functions-v6, provisioning-aws-cloudwatch-v6, provisioning-aws-iam-v6
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
