# Evaluation Scenarios — orchestrating-aws-step-functions

3 scenarios to verify the skill activates correctly and produces accurate guidance. Derived from the research Scenario Coverage section.

---

## Scenario 1 — Canonical: Mixed-idempotency microservice orchestration

```json
{
  "skills": ["orchestrating-aws-step-functions"],
  "query": "Design a Step Functions state machine to orchestrate an order pipeline: charge a credit card (non-idempotent), update inventory in DynamoDB (idempotent), and send a confirmation email via SES (idempotent, high volume). Include error handling and logging.",
  "expected_behavior": [
    "Uses a STANDARD parent state machine for the payment step (non-idempotent, exactly-once guarantee required)",
    "Adds an explicit Retry block on the Lambda invoke for the payment step covering Lambda.ServiceException, Lambda.AWSLambdaException, Lambda.SdkClientException, Lambda.ClientExecutionTimeoutException with MaxAttempts 6 and BackoffRate 2",
    "Sets TimeoutSeconds on every Task state",
    "Enables CloudWatch Logs with /aws/vendedlogs/states/ prefix",
    "Recommends nesting an Express child state machine for the SES email sends (idempotent, high-volume)",
    "Scopes the IAM execution role to exact ARNs (specific Lambda ARN, DynamoDB table ARN, SES ARN) — no wildcards",
    "Asks whether inventory updates could exceed 256 KiB before choosing payload strategy"
  ]
}
```

**Pass criteria**: Agent proposes Standard workflow type, identifies the payment step as the driver for that choice, includes Retry block with correct error codes, and raises the payload-size question before finalizing architecture.

---

## Scenario 2 — Edge: Large-scale S3 data pipeline near quota boundaries

```json
{
  "skills": ["orchestrating-aws-step-functions"],
  "query": "We need to process 5 million CSV rows from S3, apply a transform to each row using Lambda, and write results back to S3. We want up to 2,000 parallel workers. Estimated per-item history events: 8. What Step Functions pattern should we use and what limits do we need to respect?",
  "expected_behavior": [
    "Identifies that 5M rows x 8 events = 40M events — far exceeds the 25,000-event Standard execution limit; rules out Inline Map and single Standard execution",
    "Recommends Distributed Map (Mode: DISTRIBUTED) with ExecutionType: EXPRESS for child workflows (idempotent transform)",
    "Notes that MaxConcurrency 2,000 is within the 10,000 Distributed Map limit but asks about downstream Lambda concurrency limits",
    "Recommends ItemBatcher to amortize per-child-execution overhead (e.g. MaxItemsPerBatch: 50)",
    "Sets ToleratedFailurePercentage / ToleratedFailureCount before deployment",
    "Uses ItemReader with ReaderConfig InputType: CSV and ResultWriter to S3",
    "Notes Standard-only constraint for Distributed Map",
    "Flags that each child Express execution must still complete in ≤5 minutes"
  ]
}
```

**Pass criteria**: Agent correctly identifies the 25,000-event quota as the primary driver, recommends Distributed Map with Express children, raises the 5-minute Express limit for per-item processing, and sets failure thresholds.

---

## Scenario 3 — Misuse/anti-pattern trap: Payment processing on Express "for speed and cost"

```json
{
  "skills": ["orchestrating-aws-step-functions"],
  "query": "Our payment processing workflow finishes in under 2 minutes and we process 50,000 transactions per hour. A colleague suggests using Express async workflows to save cost. Should we proceed?",
  "expected_behavior": [
    "Refuses / flags the proposal without qualification — does not proceed with Express async for payment processing",
    "Explains that Express async provides at-least-once semantics: the payment step may execute more than once, causing duplicate charges",
    "Asks: 'Is every step idempotent?' — payment steps are explicitly non-idempotent by definition",
    "Recommends Standard workflow for the payment step to get exactly-once guarantee",
    "Optionally: explains that Express children can be nested for idempotent post-payment steps (notifications, audit log writes) to capture the cost benefit without sacrificing correctness",
    "Does not recommend any workaround that keeps the payment step on Express async",
    "May note that Standard per-transition billing at 50k/hour needs cost modelling before comparing to Express"
  ]
}
```

**Pass criteria**: Agent refuses the anti-pattern without ambiguity, correctly identifies at-least-once as the disqualifying factor, and proposes the Standard-parent + Express-child nesting pattern as the correct cost-optimization strategy.
