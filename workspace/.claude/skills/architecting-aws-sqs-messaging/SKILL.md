---
name: architecting-aws-sqs-messaging
description: "Designs and implements AWS SQS queue-based messaging architectures for web applications. Use when architecting asynchronous decoupling between application tiers, selecting between Standard/FIFO queue types, configuring DLQ strategies, or integrating SQS with Lambda ESM, SNS fan-out, or API Gateway."
---

## Function

Specialist in AWS SQS messaging architecture for web applications. Covers queue-type selection (Standard, FIFO, FIFO high-throughput), Lambda Event Source Mapping, Dead-Letter Queue lifecycle management, security guardrails, and cloud-native patterns (queue-based load leveling, SNS fan-out, competing consumers).

## Version Context

**Technology**: Amazon Simple Queue Service (SQS)
**Target version**: AWS SQS 2026
**Research date**: 2026-08-30
**Support status**: Active

**Key changes in 2024–2025**:
- **August 2025**: Maximum inline payload raised from 256 KiB to **1 MiB** (Lambda ESM updated simultaneously — claim-check pattern no longer mandatory for most web-app payloads)
- **July 2025**: Standard queues gained **Fair Queues** — include `MessageGroupId` at send time to prevent noisy-neighbor delivery in multi-tenant architectures; no consumer-side changes required
- **2025**: Lambda ESM **Provisioned Mode** — `MinimumPollers` 2–200, `MaximumPollers` 2–10,000; 3x faster scale-up; up to 100,000 concurrent invocations
- **November 2024**: FIFO in-flight limit raised from 20,000 to **120,000 messages**
- FIFO High-Throughput Mode scales to **70,000 TPS** per API action

**Deprecated**: None active. SSE-SQS (AWS-managed key) is the default encryption for all new queues since October 2022.

⚠️ **CRITICAL — Agent Warning**:
This skill targets AWS SQS as of August 2026. Reject patterns referencing the 256 KiB payload limit or 20,000 FIFO in-flight limit — both are outdated. Fair Queues (July 2025) is a Standard queue feature — it does NOT provide FIFO ordering or exactly-once guarantees.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Mandatory patterns, architectural decisions, anti-patterns
- **[Integration Patterns](#integration-patterns)** — SQS with Lambda ESM, SNS, API Gateway, DLQ lifecycle
- **[Verification Loop](#verification-loop)** — AWS CLI checks for queue configuration compliance
- **[Quick Reference](#quick-reference)** — Critical limits and essential commands
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases for agent behavior validation
- **[External Resources](#external-resources)** — Official AWS documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

**P1: Configure DLQ with Redrive Policy and `maxReceiveCount`** — Without a DLQ, poison messages cycle indefinitely under visibility timeout windows, silently degrading throughput and distorting `ApproximateAgeOfOldestMessage`. Set `maxReceiveCount >= 5` for Lambda consumers. Set DLQ `MessageRetentionPeriod` > source queue retention to create an investigation window. FIFO source queue requires a FIFO DLQ. Create CloudWatch alarm: `ApproximateNumberOfMessagesVisible >= 1` on DLQ with no grace period — page on-call immediately.

**P2: Enable SSE-SQS or SSE-KMS** — SSE-SQS is the zero-cost baseline (enabled by default on new queues since October 2022). Upgrade to SSE-KMS when: compliance mandates key audit trails, cross-account Lambda consumers exist, or FIPS 140-2 key management is required. SSE encrypts message body only — never store sensitive data in message attributes.

**P3: Least-Privilege Queue Access Policy — No Wildcard Principal, Enforce TLS** — Never use `"Principal": "*"` in queue resource policies (publicly accessible from any internet principal). Always add an explicit Deny on `aws:SecureTransport: "false"` to enforce HTTPS. Three IAM role classes: Administrators (`sqs:*`), Producers (`sqs:SendMessage`), Consumers (`sqs:ReceiveMessage` + `sqs:DeleteMessage` + `sqs:ChangeMessageVisibility`). For private queues: deploy VPC interface endpoint + `aws:sourceVpce` condition.

**P4: Enable Long Polling (`WaitTimeSeconds = 20`)** — Short polling queries only a random subset of SQS servers, generates high `NumberOfEmptyReceives`, and increases API costs. Set `ReceiveMessageWaitTimeSeconds=20` at queue level. Lambda ESM handles long polling automatically. One polling thread per queue for custom workers; set HTTP client timeout > 20s.

**P5: Set Visibility Timeout >= 6x Lambda Function Timeout** — Formula: `VisibilityTimeout >= 6 x FunctionTimeout`. If using `MaximumBatchingWindowInSeconds`, add that value to the formula. For variable-duration non-Lambda workers, call `ChangeMessageVisibility` as a heartbeat before timeout expires. Maximum visibility timeout: 12 hours.

**P6: Idempotent Consumer Design + Enable `ReportBatchItemFailures`** — Standard queues guarantee at-least-once delivery; even FIFO queues can redeliver in edge cases. Enable `ReportBatchItemFailures` on Lambda ESM. Return correct `batchItemFailures` JSON structure. For FIFO partial batch: stop processing at first failure, return all failed + unprocessed items. Use AWS Powertools Batch Processor for production implementations. Use natural business keys (order ID, transaction ID) or DynamoDB conditional writes as idempotency store.

**P7: CloudWatch Alarms on `ApproximateAgeOfOldestMessage` and DLQ Depth** — Queue depth alone is insufficient to detect consumer lag or poison messages. Alarm: `ApproximateAgeOfOldestMessage > SLA_seconds` on source queue. Alarm: `ApproximateNumberOfMessagesVisible >= 1` on DLQ. For EC2/ECS scaling: alarm on source queue `ApproximateNumberOfMessagesVisible > threshold`. All SQS CloudWatch metrics use `QueueName` as the dimension.

### ⚠️ Ask First

**D1: Standard vs FIFO vs FIFO High-Throughput** — Ask: "Does your business logic require exactly-once processing or strict message ordering per entity, and what is your expected peak TPS?" Standard (unlimited TPS, at-least-once, best-effort order) for high-volume idempotent workloads. FIFO standard (exactly-once, strict order, 3,000 TPS with batching) for financial transactions and order management at moderate volume. FIFO high-throughput (exactly-once, strict order, 70,000 TPS) for high-volume ordered workloads. Standard queue cannot be converted to FIFO after creation.

**D2: SQS vs SNS vs EventBridge vs Kinesis** — Ask: "Does this event need to reach multiple independent consumers simultaneously, does routing require content-based filtering beyond message attributes, and do you need replay capability?" SQS (point-to-point, durable, consumer-pace control). SNS+SQS fan-out (push fan-out + durable per-consumer queues — each consumer fails independently). EventBridge (complex multi-source/target routing, SaaS integration, schema registry). Kinesis (ordered replayable streaming, real-time analytics, event sourcing with replay).

**D3: Lambda ESM vs Long-Polling Worker Fleet** — Ask: "What is the expected maximum processing time per message, do you need GPU or stateful processing, and what is the peak concurrent volume?" Lambda ESM standard (auto-scales to 1,250 concurrent, max 15-min execution). Lambda ESM provisioned (100,000 concurrent, 3x faster scale-up, eliminates cold polling lag). EC2/ECS fleet (unlimited duration, GPU, stateful — requires backlog-per-instance metric scaling + scale-in protection).

**D4: Inline Payload vs Extended Client Library + S3** — Ask: "What languages does your team use, and are any payloads expected to exceed 1 MiB?" Inline (<=1 MiB, zero S3 dependency, simplest). Extended Client Library (Java-only, up to 2 GiB, adds S3 cost and latency). Manual claim-check (any language, payloads > 1 MiB, requires implementation). August 2025 raised the inline limit from 256 KiB to 1 MiB — verify most payloads fit before adding an S3 dependency.

### 🚫 Never Do

| Anti-Pattern | Why Prohibited | Correct Alternative |
|---|---|---|
| No DLQ on any SQS queue | Poison messages cycle indefinitely, silently degrading throughput and distorting queue metrics | Configure `RedrivePolicy` with `maxReceiveCount >= 5`; deploy paired DLQ with CloudWatch alarm on depth >= 1 |
| `"Principal": "*"` in queue resource policy | Makes queue publicly accessible from any internet principal — data exfiltration, message injection, uncontrolled cost | Scope to specific IAM role ARNs; add TLS-enforce Deny condition (`aws:SecureTransport: false`) |
| `VisibilityTimeout < FunctionTimeout` | Message becomes visible before consumer finishes — duplicate processing under normal operation, not just failure scenarios | Set `VisibilityTimeout >= 6 x FunctionTimeout`; use `ChangeMessageVisibility` heartbeat for variable-duration workers |
| Treating Standard queue as exactly-once or strictly ordered | Standard queues guarantee at-least-once delivery with best-effort ordering — silent data corruption in financial and order-management systems | Use FIFO queue with `MessageGroupId`; design all Standard queue consumers to be idempotent |
| Short polling (`WaitTimeSeconds=0`) in production | Queries a random subset of SQS servers, generates high `NumberOfEmptyReceives`, inflates API charges linearly with polling rate | Set `ReceiveMessageWaitTimeSeconds=20` at queue level; Lambda ESM handles this automatically |
| Unencrypted queue containing sensitive data | Messages at rest readable by infrastructure-level access — PCI-DSS, HIPAA, GDPR violation | Enable SSE-SQS (zero additional cost, default for new queues) or SSE-KMS for compliance audit trails |

---

## Integration Patterns

**SQS + Lambda ESM** — Lambda ESM manages all polling, scaling, and partial batch failure. Key config: `BatchSize` (1–10,000), `MaximumBatchingWindowInSeconds`, `FunctionResponseTypes: [ReportBatchItemFailures]`. Standard ESM: 5 initial pollers, +300 concurrent/min, 1,250 max. Provisioned ESM: set `MinimumPollers` + `MaximumPollers` for sub-minute scale-out. ESM visibility timeout must match or be less than queue visibility timeout.

**SQS + SNS Fan-Out** — SNS topic delivers event copy to N SQS queues simultaneously. Each queue has independent DLQ, visibility timeout, and consumer scaling. Consumers must unwrap the SNS envelope (parse the `Message` field from the SNS JSON wrapper delivered to SQS). Use SNS subscription filter policies (message attributes) to limit unnecessary SQS receive charges per queue.

**API Gateway + SQS Direct Integration** — REST API with AWS Service integration type → `sqs:SendMessage`. No Lambda intermediary eliminates cold-start from the ingestion path. Request mapping template uses VTL `application/x-www-form-urlencoded`. Response: HTTP 202 Accepted + SQS MessageId. Use Lambda proxy instead if team lacks VTL expertise.

**DLQ Redrive Lifecycle** — After bug fix: `StartMessageMoveTask` (configurable rate up to 500 msg/s, max 36h task). Monitor: `ListMessageMoveTasks`. Cancel: `CancelMessageMoveTask`. Max 100 concurrent tasks per account. DLQ `MessageRetentionPeriod` must exceed source queue retention to prevent message expiry during investigation.

**Common Problems**:
- **SNS-to-SQS delivery fails** → Add `sqs:SendMessage` permission to SQS resource policy with `ArnLike` condition matching the SNS topic ARN
- **Cross-account Lambda cannot decrypt SSE-KMS queue** → Lambda execution role needs `kms:Decrypt` on the customer-managed KMS key; the default SSE-SQS key cannot grant cross-account access
- **FIFO DLQ type mismatch** → FIFO source queue requires a FIFO DLQ; mismatched types are rejected at redrive policy creation
- **`ApproximateAgeOfOldestMessage` distorted** → Likely a poison-pill loop with no DLQ configured; add DLQ with `maxReceiveCount >= 5`

---

## Verification Loop

The agent MUST execute after each queue configuration or IaC generation:

### 1. DLQ, Visibility Timeout, Retention
```bash
aws sqs get-queue-attributes \
  --queue-url <SOURCE_QUEUE_URL> \
  --attribute-names RedrivePolicy MessageRetentionPeriod VisibilityTimeout
# Expected: RedrivePolicy contains deadLetterTargetArn and maxReceiveCount >= 5
# Expected: VisibilityTimeout >= 6 x Lambda function timeout in seconds
```

### 2. Security Configuration
```bash
aws sqs get-queue-attributes \
  --queue-url <QUEUE_URL> \
  --attribute-names Policy SqsManagedSseEnabled KmsMasterKeyId
# Expected: Policy has no "Principal":"*"; contains Deny on aws:SecureTransport=false
# Expected: SqsManagedSseEnabled=true OR KmsMasterKeyId non-empty
```

### 3. Long Polling
```bash
aws sqs get-queue-attributes \
  --queue-url <QUEUE_URL> \
  --attribute-names ReceiveMessageWaitTimeSeconds
# Expected: 20
```

### 4. Lambda ESM ReportBatchItemFailures
```bash
aws lambda list-event-source-mappings \
  --function-name <FUNCTION_NAME> \
  --query 'EventSourceMappings[].[EventSourceArn,FunctionResponseTypes]'
# Expected: FunctionResponseTypes contains ReportBatchItemFailures
```

**Troubleshooting**:
- `RedrivePolicy` is empty → queue has no DLQ; add `RedrivePolicy` attribute
- `SqsManagedSseEnabled` and `KmsMasterKeyId` both empty → queue is unencrypted; enable SSE-SQS
- `ReceiveMessageWaitTimeSeconds` is `0` → short polling active; set to `20` at queue level
- FIFO redrive policy creation fails → verify DLQ is also FIFO (queue name must end `.fifo`)

---

## Quick Reference

**Essential CLI commands**:
```bash
# Inspect all queue attributes
aws sqs get-queue-attributes --queue-url <URL> --attribute-names All

# Create Standard queue with DLQ, long polling, SSE, correct visibility timeout
aws sqs create-queue --queue-name my-queue \
  --attributes ReceiveMessageWaitTimeSeconds=20,VisibilityTimeout=360,\
MessageRetentionPeriod=345600,SqsManagedSseEnabled=true,\
RedrivePolicy='{"deadLetterTargetArn":"<DLQ_ARN>","maxReceiveCount":"5"}'

# Redrive DLQ back to source queue after bug fix
aws sqs start-message-move-task \
  --source-arn <DLQ_ARN> \
  --destination-arn <SOURCE_QUEUE_ARN>
```

**Critical limits**:

| Resource | Limit | Scope |
|---|---|---|
| Standard queue TPS | Unlimited | Per queue |
| FIFO TPS (standard mode) | 300 (no batch) / 3,000 (with batch) | Per queue |
| FIFO TPS (high-throughput mode) | 70,000 | Per API action |
| FIFO in-flight messages | 120,000 | Per queue |
| Max inline message payload | 1 MiB | Per message (Aug 2025) |
| Visibility timeout max | 12 hours (43,200s) | Per message |
| Message retention max | 14 days | Per queue |
| Delay queue / message timer max | 15 minutes (900s) | Per queue / per message |
| Lambda ESM standard concurrent | 1,250 | Per ESM mapping |
| Lambda ESM provisioned concurrent | 100,000 | Per ESM mapping |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/architecting-aws-sqs-messaging/
├── SKILL.md                              <- This file (guardrails + quick reference)
└── blueprints/
    └── evaluation-scenarios.md           <- 6 test cases for skill-evaluator
```

---

## External Resources

### Official Documentation
- [SQS Developer Guide](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) — Primary reference (2026-08-30)
- [Dead-Letter Queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) — DLQ configuration and redrive lifecycle (2026-08-30)
- [SQS Security Best Practices](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-security-best-practices.html) — Access control and encryption (2026-08-30)
- [High-Throughput FIFO](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html) — 70,000 TPS FIFO mode configuration (2026-08-30)
- [Lambda SQS Error Handling](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html) — ReportBatchItemFailures (2026-08-30)
- [Lambda SQS Scaling](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-scaling.html) — ESM standard and provisioned modes (2026-08-30)
- [API Gateway + SQS Direct Integration](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/integrate-amazon-api-gateway-with-amazon-sqs-to-handle-asynchronous-rest-apis.html) — Request offloading pattern (2026-08-30)
- [Backlog-Per-Instance Scaling](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-using-sqs-queue.html) — EC2 ASG target tracking for SQS (2026-08-30)

### New in 2025
- [Fair Queues (July 2025)](https://aws.amazon.com/about-aws/whats-new/2025/07/amazon-sqs-introduces-fair/) — Multi-tenant delivery fairness for Standard queues (2026-08-30)
- [1 MiB Payload Limit (August 2025)](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib) — Inline payload limit increase (2026-08-30)

### Service Selection
- [Application Integration on AWS — How to Choose](https://docs.aws.amazon.com/decision-guides/latest/application-integration-on-aws-how-to-choose/application-integration-on-aws-how-to-choose.html) — SQS vs SNS vs EventBridge vs Kinesis decision guide (2026-08-30)
