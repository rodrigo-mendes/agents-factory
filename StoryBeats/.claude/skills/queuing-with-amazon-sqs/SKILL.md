---
name: queuing-with-amazon-sqs
description: "Designs and implements asynchronous messaging architectures with Amazon SQS (Standard and FIFO queues). Use when building producer-consumer decoupling, event-driven pipelines, Lambda-consumed queues, or fanout patterns on AWS."
---

## Function
Specialist in async decoupling and event-driven design with Amazon SQS (current GA, pinned 2026-07).

## Version Context

**Technology**: Amazon Simple Queue Service (Amazon SQS)
**Target Edition**: Current GA — SQS is a continuously updated managed service with no semantic version
**Pinned to**: 2026-07-31 (re-verify after 2027-07-31; quotas and limits evolve)
**Support status**: Active

**Breaking change (2025-08-04)**: Maximum message payload raised from **256 KiB to 1 MiB (1,048,576 bytes)** across all commercial Regions and AWS GovCloud (US), for Standard and FIFO queues.
Source: [1 MiB payload announcement](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib)

⚠️ **Version Lock**: Reject any SQS pattern that still assumes a 256 KiB message ceiling — that limit is stale as of 2025-08-04.

## Quick Navigation

- **[Always-Do Patterns](./blueprints/always-do-patterns.md)** — 8 mandatory patterns with code examples
- **[Ask-First Decisions](./blueprints/ask-first-decisions.md)** — 5 architectural decisions with trade-off matrices
- **[Never-Do Patterns](./blueprints/never-do-patterns.md)** — 10 anti-patterns with correct alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — SQS ↔ Lambda, SNS, S3 Extended Client
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 test scenarios: canonical, FIFO edge, misuse trap
- **[Verification Loop](#verification-loop)** — CLI smoke test and CloudWatch health check
- **[Quick Reference](#quick-reference)** — Critical limits table and essential commands

---

## Blueprints & Guardrails

### ✅ Always Do

For full code examples see [Always-Do Patterns](./blueprints/always-do-patterns.md).

- **Long polling (WaitTimeSeconds = 20)** — Set on every consumer or at queue level (`ReceiveMessageWaitTimeSeconds = 20`). Queries all servers, eliminates empty responses, lowers cost. Never leave default short polling in a busy consumer loop.
- **Dead-letter queue with redrive policy** — Create a DLQ (same account, Region, and queue type), attach `{"deadLetterTargetArn": "...", "maxReceiveCount": 5}`. Isolates poison messages for debugging without cycling through the main queue.
- **DLQ retention longer than source queue** — Standard queues carry the original enqueue timestamp when moved to the DLQ; a short DLQ retention silently expires messages before inspection. Use DLQ ≥ 14 days when source is 4 days.
- **Visibility timeout matches processing time (heartbeat)** — Set timeout to max expected processing time; extend with `ChangeMessageVisibility` as a heartbeat. Hard cap is 12 hours from first receipt and is NOT reset by extension.
- **DeleteMessage after every successful processing** — SQS never auto-removes on receipt; missing this causes reprocessing and pushes toward the ~120,000 Standard in-flight limit. Use `DeleteMessageBatch`; with Lambda use `ReportBatchItemFailures`.
- **Idempotent consumers (design for at-least-once)** — Standard queues guarantee at-least-once; Lambda SQS event sources explicitly warn of duplicate delivery. Key all writes on a business idempotency key so replays are no-ops.
- **Batch API calls (up to 10 messages)** — Use `SendMessageBatch`, `DeleteMessageBatch`, and `MaxNumberOfMessages = 10`. Cuts API call count; for FIFO multiplies per-partition throughput from ~300/s toward ~3,000/s.
- **Server-side encryption for sensitive queues** — Enable SQS-managed SSE (baseline) or SSE-KMS with a customer-managed key for regulated data; pair with IAM and queue policy for least-privilege access control.

### ⚠️ Ask First

For decision matrices with examples see [Ask-First Decisions](./blueprints/ask-first-decisions.md).

- **Standard vs FIFO queue** — Ask: "Is strict ordering or exactly-once processing a correctness requirement, or can the consumer be idempotent? What peak TPS is needed?" Standard gives nearly unlimited throughput; FIFO gives exactly-once + strict order at ≤300 TPS (3,000/s batched) per partition.
- **Fan-out: SNS→SQS vs single queue** — SQS delivers to one consumer; SNS fans out to many subscribers each with their own durable SQS queue. Ask: "Does exactly one worker fleet consume this event, or must independent services each receive their own copy?"
- **Payloads > 1 MiB** — Inline max is 1,048,576 bytes. Above that: Extended Client Library (S3 pointer, up to 2 GB, sync clients only) or split into smaller messages. Ask: "What is the realistic max payload and can the app accept the sync-only Extended Client constraint?"
- **Lambda ESM: on-demand vs provisioned pollers** — On-demand starts at 5 concurrent invokes, scales to 1,250 max. Provisioned scales 3x faster, up to 20,000 concurrent, costs more. Ask: "Is there a strict low-latency SLA with spiky traffic that justifies provisioned polling costs?"
- **DLQ maxReceiveCount and retention period** — Coupled correctness decisions: `maxReceiveCount` too low creates a poison-message hair trigger; too high slows failure isolation. Retention must exceed source queue's. Confirm both with the architect before deploying.

### 🚫 Never Do

For wrong/correct code side-by-side see [Never-Do Patterns](./blueprints/never-do-patterns.md).

- **Short polling in a busy consumer loop** — Tight loop with `WaitTimeSeconds = 0` causes empty responses, inflated bills, and false-empty responses (sampled subset misses existing messages). Use `WaitTimeSeconds = 20`.
- **Assuming exactly-once on a Standard queue** — At-least-once with best-effort ordering; duplicates are normal. Make consumers idempotent or switch to FIFO when exactly-once is a correctness requirement.
- **Visibility timeout shorter than processing time** — Message reappears mid-processing; a second consumer picks it up. Concurrent duplicate work and data corruption result.
- **Expecting to extend beyond the 12-hour hard cap** — `ChangeMessageVisibility` extensions do NOT reset the 12-hour ceiling from first receipt. Use Step Functions or task decomposition for longer workflows.
- **Forgetting DeleteMessage / ignoring in-flight limit** — Undeleted messages reappear after the visibility timeout; Standard queue in-flight limit is ~120,000 (returns `OverLimit`). Monitor `ApproximateNumberOfMessagesNotVisible`.
- **maxReceiveCount = 1** — A single transient failure sends the message to the DLQ, defeating SQS's built-in retry resilience. Use ≥ 5 to absorb transient errors.
- **DLQ on a FIFO queue when ordering is a correctness requirement** — Moving a failed message to the DLQ breaks the strict ordering context. Per AWS guidance: do not use a DLQ with FIFO when reordering changes meaning.
- **DLQ retention equal to or shorter than source queue retention** — Standard queues carry the original enqueue timestamp on DLQ move; equal/short DLQ retention silently expires messages before inspection.
- **Payloads > 1 MiB inline (or still capping at 256 KiB)** — Inline max is 1,048,576 bytes (raised 2025-08-04); the old 256 KiB cap is stale. For larger payloads use the Extended Client Library.
- **DLQ or Lambda consumer in a different Region than the source queue** — Cross-Region DLQ is invalid; Lambda SQS event source must be in the same Region as the queue. Cross-account Lambda ESM is allowed; cross-Region is not.

---

## Integration Patterns

For full code examples see [Integration Patterns](./blueprints/integration-patterns.md).

- **SQS ↔ Lambda (Event Source Mapping)** — Lambda polls the queue on your behalf; use `ReportBatchItemFailures` to retry only failed items; match Lambda timeout to queue visibility timeout; Lambda and queue must be in the same Region.
- **SQS ↔ SNS (Fan-out)** — SNS topic with multiple SQS queue subscriptions; each queue gets a durable copy; SQS buffers if a subscriber is offline; use FIFO SNS → FIFO SQS for ordered fanout.
- **SQS ↔ S3 (Extended Client)** — Payload > 1 MiB: store body in S3, keep a reference pointer in the SQS message; requires Amazon SQS Extended Client Library (Java/Python); sync clients only; up to 2 GB.

**Common problems**:
- **Lambda ESM does not scale fast enough** → Enable provisioned pollers or configure `MaximumConcurrency`
- **Messages repeatedly fail and clog the queue** → Confirm DLQ is configured and `maxReceiveCount` is set; verify consumer throws on error rather than swallowing it
- **FIFO throughput bottleneck** → Increase the number of distinct `MessageGroupId` values or enable high-throughput FIFO mode

---

## Verification Loop

Run after provisioning or modifying any SQS resource.

### 1. Validate IaC (Terraform example)
```bash
terraform validate && terraform plan -out=tfplan
# Expected: 0 errors; plan shows queue + DLQ with correct attributes
# Exit code: 0
```

### 2. CLI smoke test (AWS CLI v2)
```bash
QUEUE_URL=$(aws sqs get-queue-url --queue-name my-queue --query QueueUrl --output text)

aws sqs send-message --queue-url "$QUEUE_URL" --message-body '{"test":true}'
RECEIPT=$(aws sqs receive-message --queue-url "$QUEUE_URL" \
  --wait-time-seconds 5 --query 'Messages[0].ReceiptHandle' --output text)
# Expected: non-empty ReceiptHandle

aws sqs delete-message --queue-url "$QUEUE_URL" --receipt-handle "$RECEIPT"
# Exit code: 0
```

### 3. CloudWatch health check
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS --metric-name ApproximateNumberOfMessagesNotVisible \
  --dimensions Name=QueueName,Value=my-queue \
  --start-time $(date -u -d '1 hour ago' +%FT%TZ) \
  --end-time $(date -u +%FT%TZ) \
  --period 300 --statistics Maximum
# Expected: MaxValue near 0 (no stuck in-flight messages)
```

**Troubleshooting**:
- `AWS.SimpleQueueService.NonExistentQueue` → queue not created or wrong Region specified
- `OverLimit` on ReceiveMessage → ~120,000 in-flight limit reached; increase deletion rate or request a quota increase
- `InvalidParameterValue` on `WaitTimeSeconds` > 20 → hard max is 20 seconds

---

## Quick Reference

**Essential commands (AWS CLI v2)**:
```bash
# Create DLQ then main queue with long polling and redrive policy
aws sqs create-queue --queue-name my-dlq
aws sqs create-queue --queue-name my-queue \
  --attributes '{"RedrivePolicy":"{\"deadLetterTargetArn\":\"<DLQ_ARN>\",\"maxReceiveCount\":\"5\"}",
                 "ReceiveMessageWaitTimeSeconds":"20","VisibilityTimeout":"120"}'

# Batch send (up to 10 messages)
aws sqs send-message-batch --queue-url <URL> --entries file://batch.json

# Receive with long polling and max batch
aws sqs receive-message --queue-url <URL> --max-number-of-messages 10 --wait-time-seconds 20

# Delete message after processing
aws sqs delete-message --queue-url <URL> --receipt-handle <Handle>
```

**Critical limits (pinned 2026-07-31)**:

| Resource | Limit | Note |
|---|---|---|
| Message size | max **1 MiB** (1,048,576 bytes) | Raised from 256 KiB on 2025-08-04 |
| Retention | 60 s – **14 days** (default 4 days) | DLQ retention must exceed source |
| Visibility timeout | 0 – **12 hours** (default 30 s) | Hard cap, NOT reset by extension |
| Long-poll wait | max **20 seconds** | Per request or queue attribute |
| Batch size | max **10 messages** | Send / receive / delete |
| In-flight (Standard) | ~**120,000** | `OverLimit` error beyond this |
| Delay | 0 – **15 minutes** | Per queue or per message timer |
| FIFO throughput | **300 TPS** / **3,000/s** batched | Per partition; higher with high-throughput mode |

---

## External Resources

### Official Documentation
- [What is Amazon SQS?](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) — Primary reference (accessed 2026-07-31)
- [Amazon SQS message quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html) — Authoritative limits (accessed 2026-07-31)
- [Visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) — 12-hour cap, heartbeat, in-flight (accessed 2026-07-31)
- [Short and long polling](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html) (accessed 2026-07-31)
- [Using dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) (accessed 2026-07-31)
- [High throughput for FIFO queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html) (accessed 2026-07-31)
- [SQS delay queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-delay-queues.html) (accessed 2026-07-31)
- [Using Lambda with Amazon SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html) (accessed 2026-07-31)
- [Configuring scaling for SQS event source mappings](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-scaling.html) (accessed 2026-07-31)

### Breaking Change
- [1 MiB payload announcement](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib) — Published 2025-08-04; accessed 2026-07-31

### Research Base
- [research_cloud_AWS_SQS_2026-07.md](../../../StoryBeats/docs/research_cloud_AWS_SQS_2026-07.md) — Source research file; confidence: High; all claims source-dated 2026-07-31
