# Evaluation Scenarios — queuing-with-amazon-sqs

> 3 test scenarios to verify skill correctness. Each scenario specifies the skill invoked,
> the representative query, and the expected behaviors an evaluator should check.

---

## Scenario 1 — Canonical: Standard SQS Queue with Long Polling, DLQ, and Lambda Consumer

```json
{
  "skills": ["queuing-with-amazon-sqs"],
  "query": "Set up a Standard SQS queue for an order-processing microservice. The queue should use long polling, have a dead-letter queue, and be consumed by a Lambda function. Include the Lambda function code and the queue configuration.",
  "expected_behavior": [
    "Creates both a source queue and a separate DLQ in the same Region and same account",
    "Sets ReceiveMessageWaitTimeSeconds=20 (long polling) on the source queue",
    "Attaches a redrive policy with maxReceiveCount=5 (or similar; not 1) pointing to the DLQ ARN",
    "Sets DLQ MessageRetentionPeriod strictly longer than the source queue (e.g., 14 days vs 4 days)",
    "Sets VisibilityTimeout to match or exceed expected processing time",
    "Provides a Lambda handler that returns batchItemFailures for partial batch failures (ReportBatchItemFailures pattern)",
    "Does NOT call ReceiveMessage or DeleteMessage manually — defers to Lambda ESM",
    "Makes the Lambda handler idempotent (idempotency key on the business operation)",
    "Does not assume exactly-once delivery without an idempotency guard"
  ]
}
```

**Evaluator checks**:
- `WaitTimeSeconds` is 20, not 0
- `maxReceiveCount` is between 3 and 10; not 1
- DLQ retention > source queue retention
- Lambda code returns `{"batchItemFailures": [...]}` on partial failure
- Lambda code includes an idempotency guard on the business side effect

---

## Scenario 2 — Edge Case: FIFO Queue for Payment Order Processing with High-Throughput Mode

```json
{
  "skills": ["queuing-with-amazon-sqs"],
  "query": "We process payment events for an e-commerce platform. Events must be processed in strict order per customer, exactly once, with no duplicates. Expected peak load is 2,000 payment events per second across 500 active customer sessions simultaneously. Design the SQS configuration.",
  "expected_behavior": [
    "Chooses FIFO queue (not Standard) — strict order and exactly-once are correctness requirements",
    "Uses MessageGroupId keyed on customer ID (e.g., customer-{customerId}) to ensure per-customer FIFO ordering",
    "Uses MessageDeduplicationId or enables content-based deduplication on the queue",
    "Identifies that 2,000 TPS across 500 distinct MessageGroupIds exceeds default FIFO per-partition 300 TPS and recommends enabling high-throughput FIFO mode",
    "Does NOT attach a DLQ and then suggest ignoring ordering — notes that DLQ with FIFO breaks ordering, presents the alternatives (retry-in-place or redesign)",
    "Queue name ends in .fifo",
    "Does not recommend Standard queue with idempotency as a substitute when exactly-once is a stated correctness requirement"
  ]
}
```

**Evaluator checks**:
- FIFO queue selected, not Standard
- `MessageGroupId` = per-customer identifier
- High-throughput FIFO mode mentioned for 2,000 TPS requirement
- DLQ trade-off for FIFO is explicitly discussed (ordering breakage risk)
- Queue name has `.fifo` suffix

---

## Scenario 3 — Misuse/Anti-Pattern Trap: Consumer Using Short Polling Without DLQ

```json
{
  "skills": ["queuing-with-amazon-sqs"],
  "query": "Our consumer polls SQS every second with WaitTimeSeconds=0 in a tight loop. Messages sometimes fail but we have no DLQ — we just let them retry forever. Visibility timeout is set to 30 seconds but some jobs take 10 minutes. Is this setup OK?",
  "expected_behavior": [
    "Identifies WaitTimeSeconds=0 as Anti-pattern 1 (short polling) and prescribes WaitTimeSeconds=20",
    "Identifies the missing DLQ as a gap — poison messages will cycle forever; prescribes adding a redrive policy with maxReceiveCount 3–10",
    "Identifies visibility timeout=30s for 10-minute jobs as Anti-pattern 3 — message reappears mid-processing causing duplicate work; prescribes extending the timeout and/or using a ChangeMessageVisibility heartbeat",
    "Does NOT validate or agree that the setup is acceptable",
    "Does NOT propose maxReceiveCount=1 as the fix for the DLQ",
    "Provides corrected configuration or code showing: WaitTimeSeconds=20, VisibilityTimeout>=600, redrive policy with maxReceiveCount>=3"
  ]
}
```

**Evaluator checks**:
- All three issues are flagged (short polling, no DLQ, wrong visibility timeout)
- Agent does not affirm the broken setup
- Corrected config includes `WaitTimeSeconds=20`
- Corrected visibility timeout is ≥ 600 seconds (or uses heartbeat pattern)
- Redrive policy `maxReceiveCount` is ≥ 3 (not 1)
- DLQ retention is set longer than source queue retention
