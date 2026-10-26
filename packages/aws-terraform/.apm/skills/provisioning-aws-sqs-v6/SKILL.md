---
name: provisioning-aws-sqs-v6
description: "SQS Terraform (aws 6.x): queues, FIFO, encryption, queue policies, dead-letter queues and redrive. Use when writing HCL for SQS. Not for SNS, KMS, Lambda, EventBridge, S3."
---

# Provisioning AWS SQS with Terraform — hashicorp/aws 6.x

> Version lock: every claim applies to **hashicorp/aws 6.x** (reference patch 6.69.0/6.70.0) + **Terraform ~> 1.16** only.
> Research date **2026-10-23**. Claims tagged (unverified) or (medium confidence) were not fully confirmed
> against an official page. Resources covered: `aws_sqs_queue`, `aws_sqs_queue_policy`,
> `aws_sqs_queue_redrive_policy`, `aws_sqs_queue_redrive_allow_policy`.

## Version Context

| Item | Value | Source (fetched 2026-10-23) |
|---|---|---|
| Terraform CLI | `~> 1.16`; 1.17.0 is stable (2026-10-23) but not the target | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | latest 6.70.0 (2026-10-23); reference 6.69.0/6.70.0; constraint `~> 6.69` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| 6.57.0 | **Withdrawn** from GitHub and Registry — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Region | Optional `region` on all four resources; changing it forces replacement | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |
| Identity import | `identity` block needs Terraform >= 1.12.0 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 became stable on 2026-10-21; this skill still targets `~> 1.16`. Re-verify when starting new work.
- 6.57.0 was withdrawn from GitHub and the Registry; never pin it.
- aws v7 is planned (not released; the upgrade guide lists items "removed in v7.0.0": https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown); it is a new skill.

**Version lock:** `-v6` = the 6.x major line, reference patch 6.69.0/6.70.0, Terraform `~> 1.16`. A new major (v7) is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Queues: [Terraform block, standard queue, encryption, tags, FIFO](./blueprints/always-do-queues.md)
- Policies: [queue policy, SNS producer, encrypted queue with service producers](./blueprints/always-do-policies.md)
- DLQ: [dead-letter queue, redrive, import](./blueprints/always-do-dlq.md)
- Never-do queue config: [FIFO name, throughput, maxReceiveCount, DLQ rules](./blueprints/never-do-queue-config.md)
- Never-do policies/access: [policy Version, public principal, AWS managed key](./blueprints/never-do-policies-access.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `required_version = "~> 1.16"` and `version = "~> 6.69"`** in the root module's `terraform {}` block ([source](https://developer.hashicorp.com/terraform/language/expressions/version-constraints)).
  See [queues §1](./blueprints/always-do-queues.md#1-terraform-block-and-standard-queue).
- **Enable encryption at rest (SSE-SQS or SSE-KMS)** — Security Hub SQS.1 (medium severity) checks that queues are encrypted ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/sqs-controls.html)).
  See [queues §2](./blueprints/always-do-queues.md#2-encryption-and-tags).
- **Tag queues** with `tags` or provider `default_tags` — Security Hub SQS.2 (low severity) checks for the configured `requiredTagKeys` ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/sqs-controls.html)).
  See [queues §2](./blueprints/always-do-queues.md#2-encryption-and-tags).
- **Name FIFO queues with the `.fifo` suffix and set `fifo_queue = true`** ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown)).
  See [queues §3](./blueprints/always-do-queues.md#3-fifo-queue).
- **Set `Version = "2012-10-17"` explicitly in every queue policy** — the provider warns AWS can hang with `timeout while waiting` otherwise ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_policy.html.markdown)).
  See [policies §4](./blueprints/always-do-policies.md#4-queue-policy-with-explicit-version).
- **Prefer `aws_sqs_queue_policy`, `aws_sqs_queue_redrive_policy` and `aws_sqs_queue_redrive_allow_policy` over the inline arguments** — the provider page recommends the dedicated resources ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown)).
  See [policies §4](./blueprints/always-do-policies.md#4-queue-policy-with-explicit-version).
- **Scope an SNS-to-SQS queue policy** with `Principal.Service = sns.amazonaws.com`, `sqs:SendMessage` and an `ArnEquals` `aws:SourceArn` condition ([source](https://docs.aws.amazon.com/sns/latest/dg/subscribe-sqs-queue-to-sns-topic.html)).
  See [policies §5](./blueprints/always-do-policies.md#5-sns-producer-policy).
- **For an SSE-KMS queue that AWS services send to, use a customer managed KMS key** and allow the service principal `kms:Decrypt` and `kms:GenerateDataKey` in its key policy ([source](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-key-management.html)).
  See [policies §6](./blueprints/always-do-policies.md#6-encrypted-queue-with-service-producers).
- **Create the dead-letter queue yourself, in the same account and Region as the source queue** — SQS does not create it ([source](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)).
  See [dlq §7](./blueprints/always-do-dlq.md#7-dead-letter-queue-and-redrive).
- **Use the same queue type for the DLQ as for the source** (FIFO with FIFO, standard with standard) ([source](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-configure-dead-letter-queue.html)).
  See [dlq §7](./blueprints/always-do-dlq.md#7-dead-letter-queue-and-redrive).
- **Give a standard source queue's DLQ longer retention** — standard queues keep the original enqueue timestamp in the DLQ ([source](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)).
  See [dlq §7](./blueprints/always-do-dlq.md#7-dead-letter-queue-and-redrive).
- **Import by queue URL** (all four resources) ([queue](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown), [policy](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_policy.html.markdown), [redrive policy](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_redrive_policy.html.markdown), [redrive allow policy](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_redrive_allow_policy.html.markdown)).
  See [dlq §8](./blueprints/always-do-dlq.md#8-import).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| SSE-SQS vs SSE-KMS | SSE-SQS: `sqs_managed_sse_enabled = true`. SSE-KMS: `kms_master_key_id` (AWS managed `alias/aws/sqs` or custom key). The provider page states no default for `sqs_managed_sse_enabled` (unverified) ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown)). A shorter `kms_data_key_reuse_period_seconds` means more KMS calls and cost ([source](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-key-management.html)). | "SSE-SQS or SSE-KMS (which key)? Do AWS services send to this queue?" |
| Setting both `kms_master_key_id` and `sqs_managed_sse_enabled` | AWS allows one SSE option per queue; the provider page is silent on the combination (medium confidence). ([source](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SetQueueAttributes.html)) | "Which single encryption option should this queue use?" |
| `max_message_size` | Provider page default is 262,144 ([provider page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown)); the AWS API page says 1,048,576 ([AWS API](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SetQueueAttributes.html)). The effective default when omitted may follow AWS, so set it explicitly (medium confidence). | "What maximum message size (1,024–1,048,576 bytes) is needed?" |
| Inline policy arguments vs dedicated resources | The provider recommends the dedicated resources and notes drift is detected only when the inline argument is set. Whether mixing both for one queue conflicts is inferred, not documented (medium confidence). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown)) | "Is this queue's policy managed inline or by a dedicated resource today?" |
| SNS policy with several topics | The SNS page says to use `aws:SourceAccount` if the queue is subscribed to multiple topics, and one statement per topic. ([source](https://docs.aws.amazon.com/sns/latest/dg/subscribe-sqs-queue-to-sns-topic.html)) | "One topic or several? Scope by `aws:SourceArn` or `aws:SourceAccount`?" |
| FIFO high throughput | Needs `deduplication_scope = "messageGroup"` and `fifo_throughput_limit = "perMessageGroupId"`; other combinations give normal throughput ([AWS API](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SetQueueAttributes.html)); use many distinct message group IDs ([FIFO guide](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html)). | "Is high-throughput FIFO required, and how many message groups?" |
| DLQ `maxReceiveCount` and redrive allow policy | Console range 1–1,000; API default 10; `allowAll` (default), `denyAll` or `byQueue` with up to 10 `sourceQueueArns`. ([source](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)) | "How many receives before a message moves to the DLQ, and which queues may use it?" |
| S3 or EventBridge as producer | Exact S3/EventBridge condition keys were not fetched from their own docs (unverified); only the SNS shape is confirmed. | "Which service sends to this queue? Confirm its condition keys in its docs." |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Omit `Version` in a policy attached via `aws_sqs_queue_policy` — AWS can hang with `timeout while waiting`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_policy.html.markdown)) | Set `Version = "2012-10-17"` |
| Allow `Principal` `"*"` in a queue policy without a restricting condition — the AWS best-practices page says to avoid public queues and Security Hub SQS.3 covers policies that allow public access. ([source](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-security-best-practices.html)) | Name specific principals (service principal plus `aws:SourceArn`, or account roles) |
| Rely on the AWS managed key (`alias/aws/sqs`) when `sns`, `s3` or `events` principals must send to an encrypted queue — its key policy cannot be modified. ([source](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-key-management.html)) | Use a customer managed KMS key and grant the service principal in its key policy |
| Write `maxReceiveCount` as a string (`"5"`) in `redrive_policy`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown)) | Use an integer (`5`) |
| Create a FIFO queue whose `name` does not end in `.fifo`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown)) | End the name in `.fifo` with `fifo_queue = true` |
| Set `fifo_throughput_limit = "perMessageGroupId"` without `deduplication_scope = "messageGroup"`. ([source](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SetQueueAttributes.html)) | Set both for high throughput, or neither |
| Pair a FIFO source queue with a standard DLQ, or a standard source with a FIFO DLQ. ([source](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-configure-dead-letter-queue.html)) | Use the same queue type for source and DLQ |
| Point `deadLetterTargetArn` at a queue in another account or Region. ([source](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)) | Create the DLQ in the source queue's account and Region |

## Quick Reference

Sources fetched 2026-10-23.

| Aspect | Value | Source |
|---|---|---|
| Provider constraint (root) | `~> 6.69` | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| `visibility_timeout_seconds` | default 30; range 0–43,200 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown |
| `message_retention_seconds` | default 345,600; range 60–1,209,600 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown |
| `delay_seconds` / `receive_wait_time_seconds` | defaults 0; ranges 0–900 / 0–20 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown |
| `max_message_size` | range 1,024–1,048,576 bytes; docs disagree on default (medium confidence, see Ask First) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown |
| `kms_data_key_reuse_period_seconds` | default 300; range 60–86,400 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown |
| `deduplication_scope` / `fifo_throughput_limit` | defaults `queue` / `perQueue` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown |
| Queue name | 1–80 chars; letters, digits, `_`, `-`; FIFO ends `.fifo` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown |
| Import ID | queue URL; identity attribute `url` (`aws_sqs_queue`) or `queue_url` (other three) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown ; https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_policy.html.markdown ; https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_redrive_policy.html.markdown ; https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_redrive_allow_policy.html.markdown |
| Timeouts | create/update/delete 3 m | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown |
| Security Hub SQS.1 / SQS.2 / SQS.3 | medium severity (encrypted) / low severity (tagged) / critical severity (no public access) | https://docs.aws.amazon.com/securityhub/latest/userguide/sqs-controls.html |
| Redrive allow policy | `allowAll` (default), `denyAll`, `byQueue` up to 10 ARNs | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html |
| `MessageRetentionPeriod` change | can take up to 15 min; reducing it can expire existing messages | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SetQueueAttributes.html |

## 5.x → 6.x Migration (SQS)

([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-23):

- The 6.0.0 upgrade guide has no mention of SQS, `aws_sqs_*` or `aws_sns_topic_subscription`; the only generic change is the optional `region` argument.
- 6.42.0 added `aws_sqs_queue_policy` as a list resource.
- 6.53.0 (2026-07-01) reduced the wait time for queue deletion, fixing a regression from 6.34.0 ([CHANGELOG](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)).
- No other SQS entries were found in 6.48.0–6.70.0 (part of 6.55.0 was not fully visible).

Upgrade path per the guide: move to the latest 5.x, get a clean plan, set `~> 6.0` (this skill uses `~> 6.69`), run `terraform init -upgrade` (upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown).

## External Resources

All fetched 2026-10-23.

- Provider CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- `aws_sqs_queue`: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown
- `aws_sqs_queue_policy`: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_policy.html.markdown
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- SQS dead-letter queues: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html
- SQS key management: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-key-management.html
- Security Hub SQS controls: https://docs.aws.amazon.com/securityhub/latest/userguide/sqs-controls.html
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
