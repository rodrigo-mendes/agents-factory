---
name: provisioning-aws-sns-v6
description: "SNS Terraform (aws 6.x): topics, FIFO, KMS, topic policies, subscriptions, DLQs. Use when writing HCL for SNS. Not for SQS, Lambda, EventBridge, KMS, CloudWatch alarms."
---

# Provisioning AWS SNS with Terraform — hashicorp/aws 6.x

> Version lock: `-v6` = the **6.x major line**, reference patch 6.69.0/6.70.0, **Terraform ~> 1.16**.
> Research date **2026-10-23**. Claims tagged (unverified) or (medium confidence) were not fully
> confirmed against an official page. Scope: `aws_sns_topic`, `aws_sns_topic_policy`,
> `aws_sns_topic_subscription`, `aws_sns_topic_data_protection_policy`, `aws_sns_sms_preferences`.

## Version Context

| Item | Value | Source (fetched 2026-10-23) |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"` (1.16.6 reference patch) | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | latest 6.70.0; constraint `~> 6.69`; no 7.x released | https://releases.hashicorp.com/terraform-provider-aws/ |
| 6.57.0 | **Withdrawn** — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Region | optional `region` on every SNS resource; change forces replacement; import `id@region` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |
| Identity import | `identity` block needs Terraform >= 1.12 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic.html.markdown |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 is stable since 2026-10-21 and is **not** the target of this skill; re-verify before moving.
- v7 is planned and not released; when it ships, create a new skill (`provisioning-aws-sns-v7`).
- 6.57.0 is withdrawn; a constraint resolving to it must be avoided.

**Version lock:** `-v6` = 6.x major line, Terraform ~> 1.16. A new major is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Topic patterns: [provider block, standard/FIFO topic, KMS key policy, feedback](./blueprints/always-do-topic.md)
- Access and delivery patterns: [topic policy, SQS + DLQ, cross-region, Firehose/HTTPS](./blueprints/always-do-access-delivery.md)
- Never-do access/KMS: [bare account ID, AWS managed key, EventBridge conditions, archive destroy](./blueprints/never-do-access-kms.md)
- Never-do subscriptions: [FIFO endpoints, provider region, unconfirmed subscriptions](./blueprints/never-do-subscriptions.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `required_version = "~> 1.16"` and `version = "~> 6.69"`** in `terraform {}` — latest versions are listed on
  [Terraform releases](https://releases.hashicorp.com/terraform/) and [provider releases](https://releases.hashicorp.com/terraform-provider-aws/);
  `~>` semantics are on the [version constraints page](https://developer.hashicorp.com/terraform/language/expressions/version-constraints).
  See [topic §1](./blueprints/always-do-topic.md#1-terraform-block-and-provider).
- **Name FIFO topics with the `.fifo` suffix and `fifo_topic = true`** ([topic page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic.html.markdown)).
  See [topic §3](./blueprints/always-do-topic.md#3-fifo-topic).
- **Choose FIFO or standard before creating the topic** — AWS says it cannot be converted afterwards
  ([AWS](https://docs.aws.amazon.com/sns/latest/dg/fifo-topic-code-examples.html)). See [topic §3](./blueprints/always-do-topic.md#3-fifo-topic).
- **Set `fifo_throughput_scope` at creation** — AWS recommends it
  ([AWS](https://docs.aws.amazon.com/sns/latest/dg/fifo-high-throughput.html)). See [topic §3](./blueprints/always-do-topic.md#3-fifo-topic).
- **Encrypt topics with `kms_master_key_id`** — Security Hub SNS.1 (severity Medium) is "SNS topics should be encrypted at-rest using AWS KMS"
  ([SNS.1](https://docs.aws.amazon.com/securityhub/latest/userguide/sns-controls.html)). See [topic §2](./blueprints/always-do-topic.md#2-standard-topic-with-a-customer-managed-key).
- **Use a symmetric KMS key** — SNS supports symmetric keys only
  ([AWS](https://docs.aws.amazon.com/sns/latest/dg/sns-key-management.html)).
- **Use a customer managed key when AWS services publish to the topic** and grant the service principal
  `kms:GenerateDataKey*` + `kms:Decrypt` in the key policy; some event sources need an IAM role in the key policy instead
  ([AWS](https://docs.aws.amazon.com/sns/latest/dg/sns-key-management.html)). See [topic §4](./blueprints/always-do-topic.md#4-key-policy-for-aws-service-publishers).
- **Write a bare-account Principal as `arn:aws:iam::<account>:root`** — otherwise AWS converts it and later plans show a diff
  ([policy page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_policy.html.markdown)).
  See [access §6](./blueprints/always-do-access-delivery.md#6-topic-policy).
- **Keep topics non-public (avoid a `*` principal)** — SNS.4 (severity Critical) is "SNS topic access policies should not allow public access"
  ([AWS](https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html),
  [SNS.4](https://docs.aws.amazon.com/securityhub/latest/userguide/sns-controls.html)). See [access §6](./blueprints/always-do-access-delivery.md#6-topic-policy).
- **Enforce TLS with a `Deny` on `SNS:Publish` when `aws:SecureTransport` is `false`**
  ([AWS](https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html)). See [access §6](./blueprints/always-do-access-delivery.md#6-topic-policy).
- **Attach a DLQ with `redrive_policy`** — an SQS queue in the same account and region as the subscription; without a DLQ SNS discards
  the message on a client-side error ([AWS](https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html)).
  See [access §7](./blueprints/always-do-access-delivery.md#7-sqs-subscription-with-a-dlq).
- **Use a FIFO queue as the DLQ of a FIFO topic subscription, a standard queue for a standard topic**
  ([AWS](https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html)).
- **Give an encrypted DLQ a custom KMS key whose policy grants the SNS service principal**
  ([AWS](https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html)). See [access §7](./blueprints/always-do-access-delivery.md#7-sqs-subscription-with-a-dlq).
- **Use a provider in the topic's region for every `aws_sns_topic_subscription`**
  ([subscription page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown)).
  See [access §8](./blueprints/always-do-access-delivery.md#8-cross-region-or-cross-account-subscription).
- **For cross-account same-region SQS, use the SQS queue account's provider**
  ([subscription page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown)).
- **Set `subscription_role_arn` when `protocol = "firehose"`** — required only then
  ([subscription page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown)).
  See [access §9](./blueprints/always-do-access-delivery.md#9-firehose-and-https-subscriptions).
- **Tag topics** — Security Hub SNS.3 (Low) uses a `requiredTagKeys` parameter with no default
  ([SNS.3](https://docs.aws.amazon.com/securityhub/latest/userguide/sns-controls.html)). See [topic §2](./blueprints/always-do-topic.md#2-standard-topic-with-a-customer-managed-key).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Inline `policy` on `aws_sns_topic` vs `aws_sns_topic_policy` (unverified) | Neither provider page has a "do not mix" note; both write the same topic policy, so using both would conflict — an inference. The doc example uses `aws_sns_topic_policy` + `aws_iam_policy_document`. | "Manage the topic policy inline or with `aws_sns_topic_policy`? (Pick one.)" |
| `fifo_throughput_scope = "MessageGroup"` | `MessageGroup` = high-throughput mode; `Topic` = default with more restricted quotas; once `MessageGroup` it cannot be reverted to `Topic` ([AWS](https://docs.aws.amazon.com/sns/latest/dg/fifo-high-throughput.html)). Numeric quotas not read (unverified). | "Is the irreversible high-throughput mode required?" |
| FIFO vs standard topic changes (unverified) | AWS: no FIFO/standard conversion; whether `fifo_topic`/`name` changes force replacement in Terraform is not stated on the provider page. | "Confirm topic type before apply; plan and review any replacement." |
| `archive_policy` (FIFO only) | Retention 1–365 days; extra charges; an active policy blocks topic deletion; encrypted archives need SNS `kms:Decrypt`/`kms:GenerateDataKey` in the key policy ([AWS](https://docs.aws.amazon.com/sns/latest/dg/message-archiving-and-replay-topic-owner.html)). | "Is message archiving worth the cost and delete-time step?" |
| Deactivating an archive with `archive_policy = jsonencode({})` (unverified) | AWS: `{}` disables the policy **and deletes the archive**; how Terraform handles `jsonencode({})` for `archive_policy` is not documented on the provider page. | "Is deleting the archive acceptable? Review the plan before applying." |
| `aws:SourceArn`/`aws:SourceAccount` in the topic policy (unverified) | AWS states confused-deputy conditions explicitly for KMS key policies; use on the topic policy is guidance from a page not fetched. | "Add source conditions to the topic policy for service publishers?" |
| `AuthenticateOnUnsubscribe=true` (medium confidence, absence of evidence) | AWS recommends it on confirmation unless easy unsubscribe is needed ([AWS](https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html)); the subscription page documents no argument for it. | "Is it acceptable that this flag is set outside Terraform?" |
| `maximum_message_size` above 256 KiB | Max 1048576 bytes (default 262144); above 256 KiB at most 100 subscriptions, all SQS, Firehose or Lambda ([topic page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic.html.markdown)). | "Do you need messages above 256 KiB?" |
| Email / HTTP(S) subscriptions | Partially supported by Terraform; unconfirmed ones cannot be removed by Terraform (see Never Do). | "Who confirms the subscription, and is Terraform management acceptable?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Use a bare account ID as a topic-policy Principal — AWS converts it to the root ARN and later plans show a diff. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_policy.html.markdown)) | `arn:aws:iam::<account>:root` |
| Use `alias/aws/sns` for a topic published to by AWS services such as CloudWatch or EventBridge — AWS says to use a customer managed key. ([source](https://docs.aws.amazon.com/sns/latest/dg/sns-key-management.html)) | A customer managed key with the service principal granted in its key policy |
| Add `aws:SourceAccount`/`aws:SourceArn`/`aws:SourceOrgID` conditions to the key policy for EventBridge publishing to an encrypted topic — not supported. ([source](https://docs.aws.amazon.com/sns/latest/dg/sns-key-management.html)) | Grant `events.amazonaws.com` without those conditions |
| Destroy a topic whose `archive_policy` is active — it cannot be deleted. ([source](https://docs.aws.amazon.com/sns/latest/dg/message-archiving-and-replay-topic-owner.html)) | Deactivate the archive policy first, as AWS instructs; see the Ask First row on the archive |
| Subscribe email, SMS, mobile or HTTP(S) endpoints to a FIFO topic. ([topic page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic.html.markdown), [AWS](https://docs.aws.amazon.com/sns/latest/dg/fifo-message-delivery.html)) | SQS (FIFO or standard) endpoints; reach Lambda through an SQS queue ([AWS](https://docs.aws.amazon.com/sns/latest/dg/fifo-message-delivery.html)) |
| Create a subscription with a provider outside the topic's region — creation fails. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown)) | A provider alias in the topic's region |
| Use the topic account's provider for a same-region cross-account SQS subscription — Terraform creates it, keeps no state and recreates it every apply. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown)) | The SQS queue account's provider |
| Expect `terraform destroy` to remove an unconfirmed email/HTTP(S) subscription — it only leaves state and the subscription stays in AWS. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown)) | Confirm it (it can be confirmed outside Terraform), then manage or import it |

## Quick Reference

Sources fetched 2026-10-23.

| Aspect | Value | Source |
|---|---|---|
| Provider version (latest 6.70.0) / constraint | `~> 6.69` | https://releases.hashicorp.com/terraform-provider-aws/ |
| Terraform CLI constraint | `~> 1.16` (1.16.6 reference patch) | https://releases.hashicorp.com/terraform/ |
| `~>` semantics | root modules use `~>` for providers | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| FIFO topic | `fifo_topic = true`, name ends `.fifo`; no email/mobile/SMS/HTTP(S) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic.html.markdown |
| FIFO delivery | SQS FIFO and SQS standard queues | https://docs.aws.amazon.com/sns/latest/dg/fifo-message-delivery.html |
| `fifo_throughput_scope` | `Topic` default; `MessageGroup` high throughput, irreversible | https://docs.aws.amazon.com/sns/latest/dg/fifo-high-throughput.html |
| `kms_master_key_id` | ID of an AWS-managed or customer managed key | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic.html.markdown |
| SNS encryption | symmetric KMS keys only | https://docs.aws.amazon.com/sns/latest/dg/sns-key-management.html |
| Topic `delivery_policy` | wrapped in an `"http"` object | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic.html.markdown |
| Subscription `delivery_policy` | HTTP/HTTPS only; not wrapped in `"http"` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown |
| Subscription protocols | full: sqs, sms, lambda, firehose, application; partial: email, email-json, http, https | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown |
| Firehose | up to five streams per topic for a subscription owner | https://docs.aws.amazon.com/sns/latest/dg/sns-firehose-as-subscriber.html |
| DLQ retries | SQS/Lambda: up to 100,015 attempts over 23 days; SMTP/SMS/mobile push: 50 over 6 hours | https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html |
| Security Hub | SNS.1 Medium (`sns-encrypted-kms`), SNS.3 Low (`tagged-sns-topic`), SNS.4 Critical (`sns-topic-no-public-access`) | https://docs.aws.amazon.com/securityhub/latest/userguide/sns-controls.html |
| `aws_sns_sms_preferences` | cannot be imported | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_sms_preferences.html.markdown |
| Data protection policy | `arn` + `policy` (JSON); import by topic ARN | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_data_protection_policy.html.markdown |

## 5.x → 6.x Migration (SNS)

([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-23):

- The 6.0.0 upgrade guide does not mention any `aws_sns_*` resource, data source or argument — no SNS removals or renames.
- The only 6.0 change touching SNS is the generic `region` argument (Enhanced Region Support).
- CHANGELOG 6.48.0 to 6.70.0 had no SNS entries in the windows read (see coverage limits in
  [unverified-and-risks](./blueprints/unverified-and-risks.md#coverage-limits)).

Upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
— follow it for the general 5.x to 6.x steps; this skill adds no SNS-specific migration step.

## External Resources

All fetched 2026-10-23.

- Topic: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic.html.markdown
- Subscription: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown
- Topic policy: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_policy.html.markdown
- SNS key management: https://docs.aws.amazon.com/sns/latest/dg/sns-key-management.html
- SNS dead-letter queues: https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html
- SNS security best practices: https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html
- Security Hub SNS controls: https://docs.aws.amazon.com/securityhub/latest/userguide/sns-controls.html
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
