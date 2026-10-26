# Unverified Claims and Risks — hashicorp/aws 6.x SQS

Research date 2026-10-23. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x is the current stable major** as of 2026-10-23 (latest 6.70.0, 2026-10-21; reference
  6.69.0/6.70.0). Re-verify when starting new work. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- **Terraform 1.17.0 is stable since 2026-10-21.** It is not the target of this skill (`~> 1.16`, 1.16.6 released
  2026-10-14); re-verify before moving. Source: https://releases.hashicorp.com/terraform/
- **6.57.0 was withdrawn** from GitHub and the Registry — never pin it.
- **aws v7 is planned** (not released; the upgrade guide lists items "removed in v7.0.0": https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown). When it ships, create a new skill `provisioning-aws-sqs-v7`.
- Resource docs were read from the upstream `main` branch, which may run slightly ahead of the reference patch.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | `sqs_managed_sse_enabled` default value in provider 6.x, and whether new queues get SSE-SQS by default — not stated on the provider page | (unverified) — set the encryption option explicitly |
| U2 | Whether changing `fifo_queue` forces replacement — not documented | (unverified) — not stated anywhere in this skill |
| U3 | Exact S3 and EventBridge queue-policy condition examples from their own docs (SNS is confirmed) | (unverified) — take the condition keys from the S3 / EventBridge docs |
| U4 | Absolute FIFO high-throughput regional quotas (messages/s); only per-partition figures were confirmed | (unverified) — not stated anywhere in this skill |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | `max_message_size` default: provider page says 262,144, AWS API page says 1,048,576 | (medium confidence) — set it explicitly |
| M2 | Do not set `kms_master_key_id` together with `sqs_managed_sse_enabled = true` — from AWS "one SSE option per queue"; provider behaviour undocumented | (medium confidence) — ask which single option |
| M3 | Do not mix inline `policy`/`redrive_policy`/`redrive_allow_policy` with the dedicated resources — derived from the provider recommendation and drift note, not an explicit sentence | (medium confidence) — ask how the queue is managed today |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | CHANGELOG fetched in chunks; the tail of 6.55.0 straddled a chunk boundary and was not fully visible |
| L2 | `aws_sns_topic_subscription` (including `raw_message_delivery`) not covered — belongs to `provisioning-aws-sns-v6` |
| L3 | Data sources `aws_sqs_queue` / `aws_sqs_queues` not researched |

## Tag to Register Mapping

U2 and U4 are registered only (they are not used as tags anywhere in the skill); L1–L3 are coverage notes.

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence) | SKILL.md Quick Reference — `max_message_size` row | M1 |
| (medium confidence) | always-do-queues.md §1 Terraform Block and Standard Queue — `max_message_size` comment | M1 |
| (medium confidence) | evaluation-scenarios.md Scenario 3 — `must_pass` criterion on the combined encryption options | M2 |
| (unverified) | evaluation-scenarios.md Scenario 5 — `must_pass` criterion on S3/EventBridge condition keys | U3 |
| (unverified) | SKILL.md Blueprints & Guardrails, Ask First — "SSE-SQS vs SSE-KMS" row (default of `sqs_managed_sse_enabled`) | U1 |
| (unverified) | SKILL.md Blueprints & Guardrails, Ask First — "S3 or EventBridge as producer" row | U3 |
| (medium confidence) | SKILL.md Blueprints & Guardrails, Ask First — "Setting both `kms_master_key_id` and `sqs_managed_sse_enabled`" row | M2 |
| (medium confidence) | SKILL.md Blueprints & Guardrails, Ask First — "`max_message_size`" row | M1 |
| (medium confidence) | SKILL.md Blueprints & Guardrails, Ask First — "Inline policy arguments vs dedicated resources" row | M3 |

## Source Bibliography

All accessed 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown — arguments, defaults, warnings, import
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — 6.42.0, 6.53.0, 6.57.0 withdrawn, 6.70.0
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_policy.html.markdown — Version warning, examples, import
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_redrive_policy.html.markdown — redrive policy resource
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_redrive_allow_policy.html.markdown — redrive allow policy resource
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — no SQS entries
7. https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SetQueueAttributes.html — attribute constraints
8. https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html — FIFO high throughput
9. https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html — DLQ behaviour
10. https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-configure-dead-letter-queue.html — DLQ configuration
11. https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-server-side-encryption.html — SSE
12. https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-key-management.html — KMS keys and producers
13. https://docs.aws.amazon.com/sns/latest/dg/subscribe-sqs-queue-to-sns-topic.html — SNS to SQS policy
14. https://docs.aws.amazon.com/securityhub/latest/userguide/sqs-controls.html — SQS.1, SQS.2, SQS.3
15. https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-security-best-practices.html — security best practices
16. https://releases.hashicorp.com/terraform/ — Terraform 1.16.x and 1.17.0
17. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown — `region` argument
