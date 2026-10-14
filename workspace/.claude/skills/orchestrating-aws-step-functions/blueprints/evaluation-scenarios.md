# Evaluation Scenarios — orchestrating-aws-step-functions

Minimum 3 scenarios: canonical use, edge case, and misuse/anti-pattern trap.
For evaluation via `/evaluating-skill-scenarios orchestrating-aws-step-functions`.

---

## Scenario 1 — Canonical: Order Processing Orchestration

```json
{
  "skills": ["orchestrating-aws-step-functions"],
  "query": "Design a Step Functions workflow for order processing. The workflow must: (1) validate and persist the order to DynamoDB, (2) call a payment API (async — external payment provider), (3) on payment approval send an order confirmation email via SES, (4) on payment failure trigger a compensation state. Include error handling, observability, and IAM considerations.",
  "expected_behavior": [
    "Selects Standard Workflow (not Express) — exactly-once payment semantics required, .waitForTaskToken needed for async payment callback",
    "Uses direct SDK integration arn:aws:states:::aws-sdk:dynamodb:putItem for order persistence (no Lambda-as-glue)",
    "Implements .waitForTaskToken for the async payment step — task token passed to payment provider; HeartbeatSeconds declared",
    "Every Task state includes Retry with JitterStrategy:FULL and Catch routing to CompensationState",
    "Every Task state declares TimeoutSeconds",
    "Recommends JSONata query language at state machine level for new state machine",
    "Specifies LoggingConfiguration.Level:ALL with /aws/vendedlogs/states/{name} log group prefix",
    "Enables TracingConfiguration.Enabled:true for X-Ray",
    "Describes least-privilege IAM execution role scoped to specific DynamoDB table, SES, and SQS ARNs with confused-deputy condition"
  ]
}
```

**Pass criteria**: Response includes all 9 expected behaviors. Fail if response uses Lambda for DynamoDB write, omits Retry/Catch on any Task, omits TimeoutSeconds, or recommends Express for this use case.

---

## Scenario 2 — Edge Case: 25,000-Event History Breach

```json
{
  "skills": ["orchestrating-aws-step-functions"],
  "query": "We have a Standard Workflow that uses an Inline Map to process S3 records. The dataset grows to 3,000 items and each iteration generates approximately 10 events. The workflow started failing mid-processing after recent dataset growth. What is the root cause and how do we fix it?",
  "expected_behavior": [
    "Correctly identifies the 25,000-event history limit as the root cause: 3,000 items × 10 events = 30,000 events — execution fails unconditionally at event 25,000",
    "Explains that execution failure at the limit is unconditional — all partial results are permanently lost with no recovery via Redrive",
    "Prescribes switching Map state from INLINE mode to DISTRIBUTED mode",
    "Explains that each Distributed Map child execution has its own independent 25,000-event budget",
    "Recommends ResultWriter to S3 to avoid 256 KiB output limit on aggregated results",
    "Notes that Distributed Map is Standard Workflow only (not available in Express)",
    "Optionally mentions ItemBatcher for grouping items per child execution to reduce child execution count",
    "Recommends CloudWatch alarm at 20,000 parent events via GetExecutionHistory for early warning"
  ]
}
```

**Pass criteria**: Root cause is correctly identified as 25,000-event limit; Distributed Map is prescribed as the solution; ResultWriter to S3 mentioned. Fail if response suggests Redrive as a solution (it cannot recover mid-Map failures) or recommends Express (Express does not support Distributed Map).

---

## Scenario 3 — Misuse / Anti-Pattern Trap: Step Functions as High-Frequency Event Queue

```json
{
  "skills": ["orchestrating-aws-step-functions"],
  "query": "We want to use Step Functions Standard Workflow to process IoT sensor readings arriving at 5,000 events per second. Each execution would run a small 3-state workflow: validate reading → store to DynamoDB → publish alert to SNS. Total daily volume: 430 million events. The team wants a polling loop using Wait states to handle any retry logic. Design this architecture.",
  "expected_behavior": [
    "Refuses to proceed with Standard Workflow for 5,000 events/sec — clearly states Standard cap is 2,000 exec/sec (ExecutionThrottled beyond) and per-transition pricing is prohibitive at this volume",
    "Flags the Wait-state polling loop as an anti-pattern — generates 6+ events per poll interval, accelerating toward 25,000-event history ceiling",
    "Does NOT design the requested Standard Workflow architecture — redirects to correct alternatives",
    "Recommends SQS + Lambda with event source mapping for durable at-least-once processing at this throughput",
    "OR recommends Express Workflow (Asynchronous) at 100,000 exec/sec for idempotent processing with CloudWatch Logs mandatory",
    "Explains the cost implication: Standard at 5,000/sec with 3 transitions = 15,000 transitions/sec × $0.000025 = $32,400/day vs Express pricing",
    "States that Step Functions is not a substitute for SQS, Kinesis, or EventBridge for raw event throughput at queue scale"
  ]
}
```

**Pass criteria**: Response refuses the Standard Workflow + Wait-state polling design; clearly identifies both the throughput cap and the polling-loop anti-pattern; redirects to SQS ESM or Express. Fail if response designs the requested architecture, attempts to work around the 2,000/sec cap without flagging it as a design error, or accepts the polling-loop pattern.

---

## Scenario 4 — Supplemental: JSONata Migration Decision

```json
{
  "skills": ["orchestrating-aws-step-functions"],
  "query": "We have two situations: (A) building a brand-new order validation workflow from scratch, (B) migrating an existing 40-state payment workflow from JSONPath to JSONata. How should we approach query language selection in each case?",
  "expected_behavior": [
    "For (A): recommends JSONata at state machine level (QueryLanguage:JSONata) — AWS recommendation for all new state machines; two fields instead of five",
    "For (B): recommends incremental migration using per-state QueryLanguage override, not a full rewrite",
    "Explains the Assign/Output parallelism gotcha: values assigned in Assign are not available in the same state's Output expression",
    "Notes that $eval is unsupported in Step Functions JSONata — use $parse instead",
    "Warns about the 1-second JSONata expression timeout for complex transforms",
    "For (B): notes there is no pricing difference between JSONata and JSONPath"
  ]
}
```

**Pass criteria**: Differentiates net-new (JSONata) from migration (incremental per-state override); includes the Assign/Output parallelism gotcha. Fail if response recommends a full JSONata rewrite for the 40-state existing workflow without flagging migration risk, or misses the expression timeout limit.
