# Research — AWS SQS with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `sqs`, P4 fan-out, single researcher, no sub-agents).
> Registry pages render JS-only (F12); upstream raw markdown in `hashicorp/terraform-provider-aws` (`main`) is the source for resource docs.
> Coverage reference only (not a source): `workspace/terraform/research_AWS_SQS_aws-v6.x.md` (6.47.0, Terraform 1.7 — EOL). Claims found wrong are listed in §8.
> SQS is a **regional** service: every in-scope resource accepts optional `region` (F5); none is in the F14 global list.

## 1. Version Context

| Item | Value | Source (fetched 2026-10-23) |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"` (F1); 1.17.0 stable but not the target (F2) | `_family_facts_v6.md` F1, F2 |
| hashicorp/aws | latest 6.70.0 (CHANGELOG header "6.70.0 (October 21, 2026)"); 6.71.0 Unreleased; constraint `~> 6.69` (F3) | [2], F3 |
| Withdrawn | 6.57.0 — never pin (F4) | F4 |
| Region | Optional `region` on all four SQS resources; changing it forces replacement; import `id@region` (F5) | [1][3][4][5], F5 |
| Identity import | `identity` block needs Terraform ≥ 1.12.0 (F11) — satisfied by 1.16 | [1], F11 |

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

## 2. Provider 6.x changes for SQS

- **6.0.0 upgrade guide (F13):** contains **no** mention of SQS, `aws_sqs_*` or `aws_sns_topic_subscription` — no breaking changes for this unit beyond the generic `region` addition (F5). [6]
- **CHANGELOG 6.48.0 → 6.70.0** (in-scope resources) [2]:
  - 6.53.0 (2026-07-01) bug fix: `resource/aws_sqs_queue` reduces wait time for queue deletion, fixing a regression from v6.34.0 (#48722).
  - No other SQS entries found in 6.48.0–6.54.0 or 6.56.0–6.70.0; 6.71.0 (Unreleased) has none.
  - Pre-window context: 6.42.0 added `aws_sqs_queue_policy` as a **list resource** (#47489).
  - Coverage limit: part of 6.55.0 straddled two fetch chunks (see L1).

## 3. `aws_sqs_queue` [1]

All arguments optional. Defaults/ranges as documented on the provider page:

| Argument | Default | Range / notes |
|---|---|---|
| `name` | generated if omitted | 1–80 chars, ASCII letters, digits, `_`, `-`; **FIFO names must end in `.fifo`**; conflicts with `name_prefix` |
| `name_prefix` | — | conflicts with `name` |
| `fifo_queue` | `false` (standard) | — |
| `content_based_deduplication` | — | FIFO only |
| `deduplication_scope` | `queue` | `messageGroup` \| `queue` |
| `fifo_throughput_limit` | `perQueue` | `perQueue` \| `perMessageGroupId` |
| `visibility_timeout_seconds` | 30 | 0–43,200 |
| `message_retention_seconds` | 345,600 (4 d) | 60–1,209,600 (14 d) |
| `delay_seconds` | 0 | 0–900 |
| `receive_wait_time_seconds` | 0 (short polling) | 0–20 |
| `max_message_size` | 262,144 (provider doc) | 1,024–1,048,576 bytes — see M1 (AWS API default is now 1 MiB) |
| `kms_master_key_id` | — | AWS-managed (`alias/aws/sqs`) or custom KMS key |
| `kms_data_key_reuse_period_seconds` | 300 | 60–86,400 |
| `sqs_managed_sse_enabled` | not stated on page | SSE-SQS; drift detected only when set in config (U1) |
| `policy`, `redrive_policy`, `redrive_allow_policy` | — | JSON; drift detected only when set in config; page **recommends the dedicated resources** instead |
| `tags` | — | `default_tags` matching keys overridden; `tags_all` exported |
| `region` | provider region | F5 |

Documented notes / warnings [1]:
- **WARNING:** AWS can hang indefinitely (`timeout while waiting`) when creating/updating a queue with an associated `aws_sqs_queue_policy` whose `Version` is not explicitly `"2012-10-17"`.
- `redrive_policy`: `maxReceiveCount` must be an **integer** (`5`), not a string (`"5"`).
- No statement that `fifo_queue` forces replacement, nor that `sqs_managed_sse_enabled` conflicts with `kms_master_key_id` (see M2, U2).
- Examples on the page: basic queue with inline `redrive_policy` (`maxReceiveCount` 4); FIFO (`.fifo` + `content_based_deduplication`); high-throughput FIFO (`deduplication_scope = "messageGroup"`, `fifo_throughput_limit = "perMessageGroupId"`); DLQ with separate `aws_sqs_queue_redrive_allow_policy` (`byQueue`); SSE-SQS (`sqs_managed_sse_enabled = true`); SSE-KMS (`kms_master_key_id = "alias/aws/sqs"`, reuse 300).

Attributes: `arn`, `id` (= queue URL), `url` (= `id`), `tags_all`. Timeouts: create/update/delete 3 m.
**Import ID:** the queue URL (e.g. `https://queue.amazonaws.com/80398EXAMPLE/MyQueue`); identity attribute `url` (required, Terraform ≥ 1.12); `import { id = "<url>" }` (≥ 1.5); CLI `terraform import aws_sqs_queue.x <url>`. [1]

Service-side constraints (AWS API) [7]:
- `perMessageGroupId` is allowed only when `DeduplicationScope = messageGroup`. High throughput = both set; other combinations give normal throughput.
- `ContentBasedDeduplication` uses a SHA-256 hash of the body (not attributes); an explicit `MessageDeduplicationId` overrides it; without either, send fails.
- `MessageRetentionPeriod` changes can take up to 15 min and reducing it can expire existing messages.
- Only **one** SSE option per queue (SSE-KMS or SSE-SQS) → do not set both `kms_master_key_id` and `sqs_managed_sse_enabled = true` (M2).
- FIFO high throughput: per partition up to 3,000 msg/s with batching or 300 msg/s per operation; use many distinct message group IDs. [8]

## 4. `aws_sqs_queue_policy` [3]

- Required: `queue_url`, `policy` (JSON). Optional: `region`. No exported attributes.
- WARNING: set policy `Version = "2012-10-17"` explicitly or AWS may hang.
- Examples: SNS→SQS (`sqs:SendMessage`, `ArnEquals aws:SourceArn` = topic ARN) via `aws_iam_policy_document`; S3→SQS via `jsonencode` with explicit `Version`.
- **Import ID:** queue URL; identity `queue_url` (required). Since 6.42.0 also a list resource [2].
- Do not mix with inline `aws_sqs_queue.policy`: the queue page recommends this resource instead of the inline argument [1]; the permanent-diff consequence of mixing is inferred (M3).

## 5. `aws_sqs_queue_redrive_policy` [4] and `aws_sqs_queue_redrive_allow_policy` [5]

- `aws_sqs_queue_redrive_policy`: required `queue_url` (source queue), `redrive_policy` JSON with `deadLetterTargetArn` and `maxReceiveCount`; optional `region`. No NOTE/WARNING blocks. Import: queue URL; identity `queue_url`.
- `aws_sqs_queue_redrive_allow_policy`: required `queue_url` (the DLQ), `redrive_allow_policy` JSON; optional `region`. No exported attributes. Import: queue URL (e.g. `https://queue.amazonaws.com/123456789012/myqueue`); identity `queue_url`.
- Inline vs separate: same "recommend the dedicated resource" guidance as §4 [1]; managing the same attribute from both is inferred to conflict (M3).

## 6. Dead-letter queue pattern (AWS) [9][10][7]

- DLQ must be in the **same account and Region** as the source; SQS does not create it automatically. [9][10]
- **Type must match:** FIFO source → FIFO DLQ; standard → standard. [10][7]
- `maxReceiveCount`: console range 1–1,000 [10]; API default 10 [7]; set high enough for retries [9]. Standard queues with `maxReceiveCount > 3`: messages received ≥ 3 times without deletion move to the back of the queue. [9]
- Retention: standard queues keep the **original enqueue timestamp** in the DLQ → best practice: DLQ retention **longer** than source. FIFO resets the timestamp on move. [9]
- Redrive allow policy: `allowAll` (default, same account/Region), `denyAll`, `byQueue` with up to **10** `sourceQueueArns`. [9][7]
- Don't use a DLQ with FIFO if exact order must never break. [9]
- Encryption is not changed by the move (encrypted stays encrypted; unencrypted stays unencrypted). DLQ consumers need `kms:Decrypt` on the source queue's key too. [11][12]

## 7. Producer integrations — queue policy and KMS conditions

- **SNS → SQS** [13]: queue policy `Principal.Service = sns.amazonaws.com`, `Action sqs:SendMessage`, `Condition ArnEquals aws:SourceArn = <topic ARN>`; use `aws:SourceAccount` if subscribed to multiple topics; one statement per topic. Same-account owner subscriptions auto-confirm; cross-account needs confirmation. `raw_message_delivery` is **not** documented on the SQS pages fetched → out of scope here (L2).
- **S3 → SQS**: provider `aws_sqs_queue_policy` example uses an S3 principal with explicit `Version` [3]; exact S3 condition keys not re-fetched from S3 docs (U3).
- **EventBridge → SQS**: `events.amazonaws.com` is listed as an event source for encrypted queues [12]; queue-policy example not fetched from EventBridge docs (U3).
- **Encrypted queues + AWS service producers** [12]: create a **customer managed** KMS key and allow the service principal (`sns`, `s3`, `events`.amazonaws.com) `kms:Decrypt` + `kms:GenerateDataKey` in the key policy; the AWS managed key policy can't be modified. Use `aws:SourceArn`/`aws:SourceAccount` in key policies for confused-deputy protection.
- Producers need `kms:Decrypt` + `kms:GenerateDataKey`; consumers `kms:Decrypt`. [12]
- Queue encrypted with the AWS managed key cannot invoke a Lambda in another account; all SSE requests need HTTPS + SigV4. [11]

## 8. AWS guidance — Security Hub and best practices

Security Hub CSPM SQS controls [14]:

| ID | Title | Severity | Config rule | Terraform lever |
|---|---|---|---|---|
| SQS.1 | Queues should be encrypted at rest (SSE-SQS or SSE-KMS) | Medium | `sqs-queue-encrypted` | `sqs_managed_sse_enabled = true` or `kms_master_key_id` |
| SQS.2 | Queues should be tagged (`requiredTagKeys`, up to 6; no default) | Low | `tagged-sqs-queue` | `tags` / provider `default_tags` |
| SQS.3 | Access policies should not allow public access | Critical | `sqs-queue-no-public-access` | `aws_sqs_queue_policy` without `*` principal; fixed-value conditions only (wildcards/variables in conditions are not evaluated as PASSED) |

Security best practices [15]: no public queues (avoid `Principal` `""` / `*`); least privilege (admin / producer / consumer roles); IAM roles for apps; SSE; enforce TLS with `aws:SecureTransport` in the queue policy; consider VPC endpoints and endpoint/VPC conditions in queue policies.

Other: SSE encrypts message body only — not queue metadata, message metadata or metrics; backlogged messages are not encrypted retroactively [11]. Shorter data-key reuse = more KMS calls/cost [12].

### Legacy-file claims found wrong or unsupported
1. "inline `policy` attribute is deprecated" — **wrong**: the provider only recommends `aws_sqs_queue_policy`; no deprecation [1].
2. `max_message_size = 262144  # 256 KiB (default maximum)` — **wrong**: max is 1,048,576 bytes [1][7].
3. "`sqs_managed_sse_enabled` defaults to true in v6.x … improvement over v5.x" — **unsupported**: provider page states no default; no 6.0 upgrade-guide entry [1][6] (U1).
4. "setting both causes a provider error" — **unsupported** on the provider page; AWS says only one SSE option per queue (M2).
5. `required_version = ">= 1.7"`, `version = "~> 6.0"`, S3 backend `dynamodb_table` — outdated (F1, F3, F7).
6. "Never use `aws:SourceArn` without scoping to your account" — overstated: AWS documents `aws:SourceArn` **or** `aws:SourceAccount` [13].
7. FIFO "70,000 msg/s" figures — not confirmed on the fetched high-throughput page (U4).

## 9. Unverified / medium-confidence items and coverage limits

- **U1** `sqs_managed_sse_enabled` default value in provider 6.x / whether new queues get SSE-SQS by default (unverified).
- **U2** Whether changing `fifo_queue` forces replacement in the provider (not documented; AWS has no FIFO attribute in SetQueueAttributes valid set beyond read — inference only) (unverified).
- **U3** Exact S3 and EventBridge queue-policy condition examples from S3/EventBridge docs (unverified; SNS confirmed).
- **U4** Absolute FIFO high-throughput regional quotas (msg/s) (unverified; per-partition figures confirmed [8]).
- **M1** `max_message_size` default: provider doc says 262,144, AWS API says 1,048,576 — the effective default when omitted may follow AWS (medium confidence); set it explicitly.
- **M2** Don't set `kms_master_key_id` together with `sqs_managed_sse_enabled = true` — from AWS "only one SSE option per queue" [7]; provider behaviour undocumented (medium confidence).
- **M3** "Do not mix" inline `policy`/`redrive_policy`/`redrive_allow_policy` with their dedicated resources — derived from the provider recommendation and drift note [1], not an explicit "do not mix" sentence (medium confidence).
- **L1** CHANGELOG fetched in 100k-char chunks; the tail of 6.55.0 straddled a chunk boundary and was not fully visible.
- **L2** `aws_sns_topic_subscription` (incl. `raw_message_delivery`) not covered — not on SQS pages (belongs to SNS unit).
- **L3** Data sources `aws_sqs_queue` / `aws_sqs_queues` not researched (out of scope).

## 10. Security note

No prompt-injection or instruction-like text aimed at AI agents was seen in any fetched page.

## Source Bibliography

All accessed 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_policy.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_redrive_policy.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_redrive_allow_policy.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
7. https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SetQueueAttributes.html
8. https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html
9. https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html
10. https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-configure-dead-letter-queue.html
11. https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-server-side-encryption.html
12. https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-key-management.html
13. https://docs.aws.amazon.com/sns/latest/dg/subscribe-sqs-queue-to-sns-topic.html
14. https://docs.aws.amazon.com/securityhub/latest/userguide/sqs-controls.html
15. https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-security-best-practices.html
16. `c:\agents\agents-factory\workspace\aws-terraform\_family_facts_v6.md` (F1–F5, F7, F11–F13)
