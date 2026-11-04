# Research — AWS SNS with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `sns`, P4 fan-out, flat — no sub-agents).
> Researched directly by `framework-researcher` with WebFetch against official sources only.
> Registry pages render JS-only (F12); upstream raw markdown in `hashicorp/terraform-provider-aws` (`main`) is the source for resource docs.
> Coverage reference only (not a source): `workspace/terraform/research_AWS_SNS_aws-v6.x.md` (6.47.0, Terraform 1.7 — EOL). Claims of it found wrong are listed in §8.
> SNS is a **regional** service: every in-scope resource documents optional `region` (F5; not in F14).

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"` (1.16.6 reference patch); 1.17.0 stable but not the target | F1, F2 |
| hashicorp/aws | latest 6.70.0; constraint `version = "~> 6.69"`; no 7.x | F3 |
| Withdrawn | 6.57.0 — never pin | F4 |
| Region | Optional `region` on all SNS resources; change forces replacement; import `id@region` | F5; [1][2][3][4][5] |
| Identity import | `identity = { arn = ... }` needs Terraform ≥ 1.12 (satisfied by 1.16) | F11; [1][2][3][4] |

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

## 2. Provider 6.x changes for SNS

- **6.0.0 upgrade guide (F13)**: no mention of any `aws_sns_*` resource, data source or argument → no SNS breaking changes, removals or renames [6] (2026-10-23).
- The only 6.0 change affecting SNS is the generic Enhanced Region Support `region` argument (F5).
- **CHANGELOG 6.48.0 → 6.70.0** [7]: **no SNS entries** found. 6.56.0–6.70.0 and 6.48.0–6.54.0 fully read; 6.55.0 read in two partial windows with no SNS hit (see L1). 6.71.0 "Unreleased" is empty.

## 3. `aws_sns_topic` [1]

Arguments (all optional):
- `name` — random if omitted; conflicts with `name_prefix`. **FIFO names must end in `.fifo`**.
- `name_prefix` — conflicts with `name`.
- `display_name`.
- `policy` — full IAM policy JSON (inline topic policy).
- `delivery_policy` — SNS delivery retry policy JSON (on the topic it is wrapped in an `"http"` object; on subscriptions it is not [2]).
- Feedback: `application_`, `http_`, `lambda_`, `sqs_`, `firehose_` × `success_feedback_role_arn`, `failure_feedback_role_arn`, `success_feedback_sample_rate` (0–100). Roles let SNS write delivery status to CloudWatch Logs; a failure role logs all failed deliveries.
- `kms_master_key_id` — ID of an AWS-managed or customer-managed key (example uses `alias/aws/sns`).
- `maximum_message_size` — 1024–1048576 bytes, default 262144. Above 256 KiB the topic may have at most 100 subscriptions, all SQS, Firehose or Lambda.
- `signature_version` — `1` (SHA1) or `2` (SHA256).
- `tracing_config` — `PassThrough` or `Active`.
- `fifo_topic` — bool, default `false`. FIFO topics cannot deliver to email, mobile, SMS or HTTP(S).
- `fifo_throughput_scope` — `Topic` or `MessageGroup`.
- `archive_policy` — message archiving for FIFO topics (JSON).
- `content_based_deduplication` — enables content-based dedup for FIFO topics.
- `tags` (provider `default_tags` with matching keys are overridden).

Attributes: `id` = `arn` (topic ARN), `beginning_archive_time`, `owner`, `tags_all`.
Import: topic ARN, e.g. `arn:aws:sns:us-west-2:123456789012:my-topic` (identity `arn`, `id`, or CLI).
The provider page has **no NOTE/WARNING callouts** [1] (2026-10-23).

AWS-side semantics (docs.aws.amazon.com):
- After you create a FIFO topic you **can't convert it** to standard (or the other way) [8]. Forces-new in Terraform is not stated on [1] (U1).
- FIFO topics deliver to **both SQS FIFO and SQS standard queues**. Standard queues give best-effort ordering and at-least-once delivery. Customer-managed endpoints (email, mobile, SMS, HTTP(S)) cannot subscribe and return errors. To reach Lambda, go through an SQS queue [9].
- `FifoThroughputScope`: the default is `Topic` (topic-level dedup, more restricted quotas). `MessageGroup` enables high throughput, and **once set to `MessageGroup` it cannot be reverted to `Topic`**. AWS recommends setting it at creation. Numeric quotas are on the SNS quotas page, not read here (U2) [10].
- Archive policy: available **only for application-to-application FIFO topics**. Retention is 1–365 days, set as `{"MessageRetentionPeriod":"30"}`; `{}` disables it and deletes the archive. **A topic with an active archive policy cannot be deleted**, so deactivate it first. Additional charges apply. Encrypted archives need SNS `kms:Decrypt`/`kms:GenerateDataKey` in the key policy [11].
- Encryption: SNS supports **symmetric KMS keys only** [12].

## 4. `aws_sns_topic_policy` [3]

- Required: `arn` (topic ARN), `policy` (full IAM policy JSON). Optional: `region`. Attribute: `owner`.
- NOTE: if a Principal is a bare account ID, AWS converts it to the root ARN and later plans show a diff, so use `arn:aws:iam::123456789012:root`.
- Example condition: `StringEquals` on `AWS:SourceOwner` with principal `AWS: *` (the doc example). Under SNS.4, a `*` principal with fixed-value conditions can pass; wildcard or variable conditions are not evaluated [13].
- Import: topic ARN.
- **Inline `policy` on `aws_sns_topic` vs `aws_sns_topic_policy`**: neither page [1][3] has a "do not mix" note. Both write the same topic `Policy` attribute, so managing it in both places would conflict. That conclusion is an inference (M1). Recommendation: pick one; `aws_sns_topic_policy` + `aws_iam_policy_document` is the pattern used in the doc example.
- Confused deputy: for AWS-service publishers, add `aws:SourceArn` / `aws:SourceAccount` conditions. AWS states this explicitly for **KMS key policies** used with service event sources [12]. Applying it to the topic policy itself is guidance from the IAM confused-deputy page, which was not fetched here (M2).

## 5. `aws_sns_topic_subscription` [2]

Required: `topic_arn`, `protocol`, `endpoint`; `subscription_role_arn` is **required only when `protocol = "firehose"`** (IAM role used to publish to the Firehose stream).

Protocols:
- **Fully supported**: `sqs`, `sms`, `lambda`, `firehose`, `application`. For `application` the endpoint is a mobile device endpoint ARN; for `sms` it is a phone number.
- **Partially supported**: `email`, `email-json`, `http`, `https`.

Optional args:
- `confirmation_timeout_in_minutes` — HTTP/HTTPS only, default `1`.
- `delivery_policy` — HTTP/HTTPS only; not wrapped in `"http"`.
- `endpoint_auto_confirms` — default `false` (e.g. PagerDuty).
- `filter_policy` — JSON.
- `filter_policy_scope` — default MessageAttributes; alternative MessageBody.
- `raw_message_delivery` — default `false`.
- `redrive_policy` — JSON DLQ.
- `replay_policy` — JSON archived-message replay.

Confirmation behaviour, as the docs state it [2]:
- An **unconfirmed** partially supported subscription **cannot be removed by Terraform**. Destroy removes it from state only, and it stays in AWS. `pending_confirmation` shows the status.
- "You cannot unsubscribe to a subscription that is pending confirmation." Confirmation can happen outside Terraform, such as through the email link.
- A subscription imported after confirmation can be deleted by Terraform. Deleting a topic deletes its subscriptions.

Cross-region/account [2]:
- The subscription must use a provider in the **topic's region**, or creation fails.
- Cross-account, same region: use the **SQS queue account's** provider. Otherwise Terraform creates the subscription, keeps no state and recreates it on every apply.
- Cross-account and cross-region: queue account, topic region.

Attributes: `arn`, `id`, `confirmation_was_authenticated`, `owner_id`, `pending_confirmation`.
Import: subscription ARN `arn:aws:sns:<region>:<account>:<topic>:<uuid>`.

DLQ rules (AWS) [14]:
- The DLQ is an SQS queue in the **same account and region as the subscription**. FIFO topic subscriptions use FIFO queues; standard topic subscriptions use standard queues.
- An **encrypted** SQS DLQ needs a **custom KMS key** whose policy grants the SNS service principal access.
- Without a DLQ, a client-side error, or a server-side error after retries run out, makes SNS **discard** the message.
- Retries: SQS/Lambda endpoints get up to 100,015 attempts over 23 days; SMTP/SMS/mobile push get 50 over 6 hours.
- Set DLQ retention to 14 days. Alarm on `ApproximateNumberOfMessagesVisible`, not `NumberOfMessagesSent`.

Firehose: a subscription owner can subscribe up to **five** Firehose streams per topic [15]. Required role permissions are not detailed on that page (U3).

## 6. `aws_sns_topic_data_protection_policy` [4] and `aws_sns_sms_preferences` [5]

- Data protection: required `arn` (topic ARN) and `policy` (JSON); optional `region`; no extra attributes. Import by topic ARN (identity `arn`, `id`, CLI).
- SMS preferences (brief): all arguments optional: `monthly_spend_limit`, `delivery_status_iam_role_arn`, `delivery_status_success_sampling_rate` (0–100), `default_sender_id`, `default_sms_type` (`Promotional`|`Transactional`), `usage_report_s3_bucket`, `region`. **Cannot be imported.**

## 7. AWS guidance

### KMS CMK requirement for AWS-service publishers [12]
To let AWS event sources publish to encrypted topics:
1. **Use a customer managed key**.
2. Grant the service principal `kms:GenerateDataKey*` + `kms:Decrypt` in the key policy.
3. Add `aws:SourceAccount` / `aws:SourceArn` conditions.

Listed principals:
- CloudWatch `cloudwatch.amazonaws.com`
- CloudWatch Events `events.amazonaws.com`
- S3 `s3.amazonaws.com`
- CodeCommit, DMS, Directory Service, DynamoDB, Inspector, Redshift
- RDS `events.rds.amazonaws.com`
- Glacier, SES, Snowball Edge, SSM Incident Manager (`ssm-incidents`, `ssm-contacts`)

Some event sources need an **IAM role** in the key policy instead of the service principal: EC2 Auto Scaling, Elastic Transcoder, CodePipeline, AWS Config, Elastic Beanstalk, IoT, EC2 Image Builder.

**Important:** `aws:SourceAccount`/`aws:SourceArn`/`aws:SourceOrgID` in the KMS policy are **not supported for EventBridge → encrypted topics**.

Publishers need `kms:GenerateDataKey*` + `kms:Decrypt` on the key. The AWS managed key cannot satisfy this requirement because its policy can't be edited. That last point is an inference; the page says only "use a customer managed key" (M3).

### Security best practices [16]
Preventive:
- Topics not public (avoid `*` principal).
- Least privilege (admin / publisher / subscriber).
- IAM roles, not stored credentials.
- SSE with KMS.
- Enforce TLS with a `Deny` on `SNS:Publish` when `aws:SecureTransport = false`.
- VPC endpoints plus topic policies.
- No subscriptions to raw-IP http endpoints; use domain names.
- `AuthenticateOnUnsubscribe=true` on confirmation unless easy unsubscribe is needed. This flag cannot be set by the Terraform resource args (inference, M4).

### Security Hub CSPM controls [13]

| ID | Title | Severity | Config rule |
|---|---|---|---|
| SNS.1 | SNS topics should be encrypted at-rest using AWS KMS | Medium | `sns-encrypted-kms` |
| SNS.3 | SNS topics should be tagged (`requiredTagKeys` param, no default) | Low | `tagged-sns-topic` |
| SNS.4 | SNS topic access policies should not allow public access | Critical | `sns-topic-no-public-access` |

**SNS.2 is not listed** on the current page [13]; its status (retired?) was not confirmed (U4). SNS.1 passes with any KMS key, AWS-managed or CMK, according to the control description ("keys managed in AWS KMS").

## 8. Unverified / medium-confidence / limits / legacy errors

- **U1** Whether `fifo_topic` / `name` changes force replacement in Terraform (AWS says no conversion is possible [8]).
- **U2** Numeric FIFO/standard throughput quotas (quotas page not fetched).
- **U3** Firehose `subscription_role_arn` required permissions.
- **U4** SNS.2 status.
- **M1** Inline `policy` vs `aws_sns_topic_policy` conflict (inferred; no doc note).
- **M2** `aws:SourceArn`/`aws:SourceAccount` in the topic policy (documented here only for KMS policies).
- **M3** AWS-managed key unusable for service publishers (inferred from "use a customer managed key").
- **M4** `AuthenticateOnUnsubscribe` not expressible in TF args.
- **L1** CHANGELOG 6.55.0 read only in partial windows.
- **L2** `aws_sns_platform_application` and the `data.aws_sns_topic` data source are out of scope.
- **L3** Filter-policy syntax pages were not fetched.

Legacy-file claims found **wrong** (workspace/terraform/research_AWS_SNS_aws-v6.x.md):
1. "FIFO subscribers **must** be SQS FIFO queues": wrong. SQS standard queues are also supported [9][8].
2. `fifo_throughput_scope = "Topic"` = 3,000 msg/s and `MessageGroup` = 300 msg/s: inverted or unsupported. `MessageGroup` is the **high-throughput** mode, `Topic` is the default with more restricted quotas, and `MessageGroup` is irreversible [10].
3. "Cross-region not supported for SNS → SQS": contradicted. The provider doc describes cross-region subscriptions, which need a provider in the topic region [2].
4. "`alias/aws/sns` … does NOT require explicit key policy entries" for CloudWatch/EventBridge publishers: misleading. AWS requires a **customer managed key** for AWS-service event sources [12].
5. Legacy constraints (`>= 1.7`, `~> 6.0`, `dynamodb_table` locking) are superseded by F1/F3/F7.
6. Unverified legacy claims (not confirmed on pages read): "SNS feedback role must use `AmazonSNSRole` exactly — custom policies will not work"; "raw_message_delivery NOT supported for Lambda"; "~30,000 msg/s standard".

## 9. Security note
None. No instruction-like or prompt-injection text was observed in any fetched page.

## Source Bibliography
All accessed 2026-10-23.
1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_policy.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_data_protection_policy.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_sms_preferences.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
8. https://docs.aws.amazon.com/sns/latest/dg/fifo-topic-code-examples.html
9. https://docs.aws.amazon.com/sns/latest/dg/fifo-message-delivery.html
10. https://docs.aws.amazon.com/sns/latest/dg/fifo-high-throughput.html
11. https://docs.aws.amazon.com/sns/latest/dg/message-archiving-and-replay-topic-owner.html
12. https://docs.aws.amazon.com/sns/latest/dg/sns-key-management.html
13. https://docs.aws.amazon.com/securityhub/latest/userguide/sns-controls.html
14. https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html
15. https://docs.aws.amazon.com/sns/latest/dg/sns-firehose-as-subscriber.html
16. https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html
