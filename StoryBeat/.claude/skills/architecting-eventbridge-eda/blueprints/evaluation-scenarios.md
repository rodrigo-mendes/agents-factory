# Evaluation Scenarios — architecting-eventbridge-eda

5 test cases covering canonical use, edge cases, anti-pattern traps, and architectural decision points.

---

## Scenario 1: Canonical — Reliable fan-out to multiple consumers

```json
{
  "skills": ["architecting-eventbridge-eda"],
  "query": "Design an EventBridge setup to route order events from our e-commerce service to three consumers: a Lambda that updates inventory, a Step Functions workflow for fraud detection, and an SQS queue for analytics. Make it production-ready.",
  "expected_behavior": [
    "Recommends a custom event bus (not the default bus) for the orders domain to isolate the bounded context",
    "Configures a single rule with three targets (Lambda, Step Functions, SQS) — all within the 5-target limit",
    "Attaches a standard SQS DLQ (not FIFO) to every target",
    "Sets MaximumRetryAttempts and MaximumEventAgeInSeconds explicitly per target SLA",
    "Notes Lambda and Step Functions targets are invoked ASYNCHRONOUSLY",
    "Recommends idempotent consumers with DynamoDB conditional writes for deduplication",
    "Recommends alarming on InvocationsFailedToBeSentToDlq and InvocationsSentToDlq"
  ]
}
```

---

## Scenario 2: Edge Case — Cross-account forwarding under compliance constraints

```json
{
  "skills": ["architecting-eventbridge-eda"],
  "query": "We have a central audit account (Account C) that must receive events from services in Account A and Account B. Account B currently forwards events it received from Account A on to Account C. Payloads may contain PII. How should we design this for 2026 AWS best practices?",
  "expected_behavior": [
    "Identifies the third-hop anti-pattern: A -> B -> C is silently rejected by EventBridge with THIRD_ACCOUNT_HOP_DETECTED",
    "Recommends Account A publish directly to Account C (single hop) instead of chaining through B",
    "Recommends CMK encryption on the central bus with correct KMS key policy (events.amazonaws.com principal, encryption context scoped to bus ARN)",
    "Attaches a DLQ on the CMK bus for encryption/decryption failures",
    "Recommends interface VPC endpoints (PrivateLink) for PII payload transit",
    "Notes Schema Discovery is unavailable on CMK buses — recommends explicit schema management",
    "Pins explicit account IDs (not *) in every consuming rule's account field"
  ]
}
```

---

## Scenario 3: Anti-Pattern Trap — FIFO DLQ and third-hop chain

```json
{
  "skills": ["architecting-eventbridge-eda"],
  "query": "We want ordered delivery for our payment events so we are using a FIFO SQS queue as the DLQ on our EventBridge rule. Our hub bus in Account B also forwards all partner events received from Account A to Account C for central logging. Please implement this.",
  "expected_behavior": [
    "Refuses to configure a FIFO queue as the DLQ — explains EventBridge does not support FIFO DLQs",
    "Offers standard SQS DLQ as the correct alternative and suggests encoding ordering metadata in the consumer",
    "Refuses to implement the A->B->C forwarding chain",
    "Explains THIRD_ACCOUNT_HOP_DETECTED silent failure mode with DLQ error code reference",
    "Proposes Account A publishing directly to both Account B and Account C as single hops",
    "Does not implement the original request as-specified"
  ]
}
```

---

## Scenario 4: Decision Point — Choreography vs orchestration for a multi-step saga

```json
{
  "skills": ["architecting-eventbridge-eda"],
  "query": "We have an order transaction spanning 5 services: order creation, inventory reservation, payment processing, shipping assignment, and notification dispatch. If inventory fails, we need to cancel the order and refund any payment. Should we use EventBridge choreography or Step Functions orchestration?",
  "expected_behavior": [
    "Does not choose for the user without presenting trade-offs",
    "Presents the choreography vs orchestration comparison table",
    "Notes 5 participants and complex compensation (cancel + refund) favor orchestration",
    "Explains choreography risk: scattered compensation logic and weaker end-to-end observability",
    "Recommends Step Functions orchestration for this scenario while documenting the trade-offs explicitly",
    "Notes EventBridge can still serve as the entry-point trigger for the Step Functions execution",
    "Asks or confirms whether teams want centralized timeout/retry control before finalizing"
  ]
}
```

---

## Scenario 5: Edge Case — Large payload and Pipes enrichment ceiling

```json
{
  "skills": ["architecting-eventbridge-eda"],
  "query": "We need to pipe DynamoDB Stream records (which can reach 900 KB) through EventBridge Pipes to a Lambda target. The Lambda also needs to fetch additional metadata from our internal API, which takes around 4 minutes. What are the risks and how should we handle this?",
  "expected_behavior": [
    "Flags the critical risk: the Pipes total execution ceiling is 5 minutes (not adjustable); a 4-minute enrichment plus Lambda invocation likely exceeds this",
    "Recommends the claim-check pattern via Amazon S3 for large payloads to avoid the 1 MB PutEvents limit",
    "Suggests moving the 4-minute metadata fetch into an async post-processing step or caching the reference data to reduce enrichment latency",
    "Notes only Step Functions Express (not Standard) is supported as synchronous Pipes enrichment",
    "Notes that returning empty body from enrichment suppresses the target — this is not an error but intentional filter behavior",
    "Confirms DynamoDB Streams source in Pipes preserves shard ordering end-to-end",
    "Mentions enrichment response cap is 6 MB — 900 KB records are within range but claim-check is still recommended for PII or payload growth"
  ]
}
```
