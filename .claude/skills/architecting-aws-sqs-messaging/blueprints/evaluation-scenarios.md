# Evaluation Scenarios — architecting-aws-sqs-messaging

Test cases for `/evaluating-skill-scenarios architecting-aws-sqs-messaging`.
Covers: canonical use, edge cases, and misuse/anti-pattern traps.

---

## Scenario 1 — Canonical: Standard Web Application Async Processing

```json
{
  "skills": ["architecting-aws-sqs-messaging"],
  "query": "Design a serverless async image-processing pipeline: clients upload requests via API Gateway, images are processed by Lambda, results stored in S3. The team uses Python. Provide the architecture and all critical configuration values.",
  "expected_behavior": [
    "Recommends API Gateway AWS Service integration directly to SQS (no Lambda intermediary for ingestion)",
    "Specifies Standard SQS queue (at-least-once delivery acceptable for idempotent image processing)",
    "States visibility timeout = 6 x Lambda function timeout (e.g., Lambda=60s -> VisibilityTimeout=360s)",
    "Specifies DLQ with maxReceiveCount >= 5 and DLQ MessageRetentionPeriod > source queue retention",
    "Enables SSE-SQS (default, zero cost) for encryption at rest",
    "Sets ReceiveMessageWaitTimeSeconds=20 (long polling) at queue level",
    "Enables ReportBatchItemFailures on Lambda ESM configuration",
    "Mentions idempotent consumer design (natural key or DynamoDB conditional write)",
    "Specifies CloudWatch alarm on DLQ ApproximateNumberOfMessagesVisible >= 1",
    "Does NOT recommend claim-check pattern — payload assumed <= 1 MiB after August 2025 limit increase"
  ]
}
```

---

## Scenario 2 — Edge Case: Multi-Tenant SaaS Noisy-Neighbor Prevention

```json
{
  "skills": ["architecting-aws-sqs-messaging"],
  "query": "We have a SaaS platform with hundreds of tenants sharing one SQS Standard queue. Large enterprise tenants send 10,000 messages/hour; small tenants send 10 messages/hour. Small tenants are experiencing 30-minute processing delays. How do we fix this without migrating to FIFO or creating per-tenant queues?",
  "expected_behavior": [
    "Recommends Fair Queues feature (July 2025) — include MessageGroupId = tenantId in all SendMessage calls",
    "Confirms this is a Standard queue feature and requires no consumer-side changes",
    "Explicitly states Fair Queues does NOT provide FIFO ordering or exactly-once guarantees",
    "Notes the feature was released July 2025 and requires verification of regional support",
    "Does NOT recommend migrating to FIFO or creating per-tenant queues to solve this specific problem",
    "Confirms no Lambda ESM reconfiguration is required for Fair Queues to take effect"
  ]
}
```

---

## Scenario 3 — Edge Case: Financial Order Management — FIFO at Scale

```json
{
  "skills": ["architecting-aws-sqs-messaging"],
  "query": "We process financial trade orders that must be executed in strict sequence per order ID. Current volume is 5,000 TPS and growing to 50,000 TPS within 12 months. We need exactly-once processing. Design the SQS architecture.",
  "expected_behavior": [
    "Recommends FIFO queue (not Standard) because strict ordering and exactly-once are required",
    "Recommends enabling high-throughput mode to reach 70,000 TPS (deduplication scope = Message group, throughput limit = Per message group ID)",
    "Specifies MessageGroupId = orderId for strict per-order ordering with high-cardinality distribution",
    "Notes FIFO queue name must end .fifo",
    "Specifies FIFO DLQ (FIFO source requires FIFO DLQ)",
    "Recommends Lambda ESM provisioned mode for sub-minute scale-out at flash-trade-volume peaks",
    "Sets maxReceiveCount >= 5 on DLQ redrive policy",
    "Notes FIFO in-flight limit is 120,000 messages (raised Nov 2024 from 20,000)"
  ]
}
```

---

## Scenario 4 — Misuse Trap: Standard Queue for Order Status Transitions

```json
{
  "skills": ["architecting-aws-sqs-messaging"],
  "query": "We want to track order status transitions (PENDING -> PROCESSING -> SHIPPED -> DELIVERED) using SQS Standard queue. Our consumer reads these messages and updates the database in order. Will this work?",
  "expected_behavior": [
    "Identifies the anti-pattern: Standard queue provides best-effort ordering, not strict ordering",
    "Explicitly warns that under load, messages may arrive out of send order — duplicate delivery is also possible",
    "States this will cause silent data corruption (e.g., SHIPPED processed before PROCESSING, wrong final state)",
    "Recommends FIFO queue with MessageGroupId = orderId for strict per-order sequencing",
    "Recommends idempotent consumer design even for FIFO (edge-case redelivery)",
    "Asks about volume to determine whether standard FIFO or high-throughput FIFO is needed",
    "Does NOT approve using Standard queue for this use case regardless of consumer design"
  ]
}
```

---

## Scenario 5 — Edge Case: Large Payload Strategy

```json
{
  "skills": ["architecting-aws-sqs-messaging"],
  "query": "Our team uses Python and Node.js. We need to pass document processing jobs through SQS. Some documents are 800 KB, others are 3 MB. What is the correct payload strategy?",
  "expected_behavior": [
    "Correctly identifies 1 MiB as the current inline limit (August 2025 increase from 256 KiB)",
    "States 800 KB documents fit inline — no S3 dependency needed post-August 2025",
    "For 3 MB documents: recommends manual claim-check pattern (store payload in S3, include S3 key + bucket in SQS message body)",
    "Explicitly states the SQS Extended Client Library is Java-only — not available for Python or Node.js",
    "Recommends S3 lifecycle policy to clean up unprocessed claim-check objects",
    "Does NOT recommend Extended Client Library for Python/Node.js teams"
  ]
}
```

---

## Scenario 6 — Anti-Pattern Trap: Queue Without DLQ

```json
{
  "skills": ["architecting-aws-sqs-messaging"],
  "query": "We have a high-throughput SQS queue with 1 million messages/day. Our Lambda consumer sometimes fails on malformed messages. The queue depth keeps climbing and ApproximateAgeOfOldestMessage is hours old even at normal load. We have no DLQ. Is this related?",
  "expected_behavior": [
    "Diagnoses the root cause: poison messages cycling indefinitely under visibility timeout windows without a DLQ",
    "Explains that without a DLQ, malformed messages re-enter the queue after each visibility timeout expiry and block or distort throughput",
    "Explains that ApproximateAgeOfOldestMessage distortion is a known symptom of poison-pill accumulation",
    "Recommends immediately adding DLQ with maxReceiveCount >= 5 and redrive policy",
    "Recommends CloudWatch alarm on DLQ ApproximateNumberOfMessagesVisible >= 1 for immediate alerting",
    "Mentions StartMessageMoveTask for redriving messages after the underlying processing bug is fixed",
    "Does NOT suggest increasing visibility timeout as the primary fix"
  ]
}
```
