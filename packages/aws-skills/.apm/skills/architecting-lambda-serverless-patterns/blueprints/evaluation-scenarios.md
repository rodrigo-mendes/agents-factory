# Evaluation Scenarios — architecting-lambda-serverless-patterns

Test cases for use with `/evaluating-skill-scenarios architecting-lambda-serverless-patterns`.

---

## Scenario 1 — Canonical: Design a Serverless REST API

```json
{
  "skills": ["architecting-lambda-serverless-patterns"],
  "query": "Design a serverless REST API on AWS for an e-commerce order service. The API must handle up to 500 requests/second at peak with sub-200ms p99 latency. Team uses Python 3.12.",
  "expected_behavior": [
    "Recommends API Gateway (HTTP API for cost efficiency, or REST API if WAF/usage plans are needed) fronting Lambda",
    "Recommends SnapStart for Python 3.12+ to mitigate cold starts for latency-sensitive endpoints",
    "Specifies one dedicated IAM execution role per Lambda function scoped to minimum required permissions",
    "Sets reserved concurrency: 500 RPS × average duration; adds 10% buffer",
    "Recommends Powertools Logger (structured JSON) and Powertools Metrics (EMF) for observability",
    "Recommends DynamoDB for order state (single-digit ms reads, on-demand capacity)",
    "Notes that API Gateway default throttle (10,000 RPS) must be tuned alongside Lambda reserved concurrency",
    "Does NOT recommend python3.10 (imminent deprecation October 31, 2026)"
  ]
}
```

---

## Scenario 2 — Canonical: Async Event Pipeline with S3 Trigger

```json
{
  "skills": ["architecting-lambda-serverless-patterns"],
  "query": "A Lambda function is triggered by S3 PutObject events to process uploaded CSV files and write results to DynamoDB. How should failure handling be configured?",
  "expected_behavior": [
    "Identifies this as an asynchronous push-based trigger (not an ESM) — S3 invokes Lambda directly",
    "Recommends configuring DeadLetterConfig (SQS standard queue) AND DestinationConfig.OnFailure on the Lambda function",
    "Clarifies that the DLQ goes on the Lambda function (not an SQS source queue) because the trigger is S3, not SQS ESM",
    "Recommends idempotent function design because Lambda delivers at-least-once",
    "Recommends Powertools Idempotency utility backed by DynamoDB for duplicate detection",
    "Sets function timeout based on p99 processing duration from load tests, not the default 3 seconds",
    "Recommends structured JSON logging with Powertools Logger including cold start flag and requestId"
  ]
}
```

---

## Scenario 3 — Edge Case: Cold-Start-Sensitive API with Sub-100ms p99 SLA

```json
{
  "skills": ["architecting-lambda-serverless-patterns"],
  "query": "A financial transaction API built on Java 17 Lambda requires strict sub-100ms p99 latency including cold starts. What is the correct cold-start mitigation strategy?",
  "expected_behavior": [
    "Presents the SnapStart vs Provisioned Concurrency decision (A.4 Ask First)",
    "Recommends evaluating SnapStart first for Java 17 (supported since Java 11+) as it achieves sub-second cold starts without continuous idle billing",
    "Notes that SnapStart requires a published function version (not $LATEST) and cannot be combined with Provisioned Concurrency",
    "If SnapStart sub-second is insufficient for sub-100ms SLA, recommends Provisioned Concurrency with Application Auto Scaling at 70% LambdaProvisionedConcurrencyUtilization target",
    "Notes that Provisioned Concurrency incurs continuous billing even when environments process no requests",
    "Notes that SnapStart requires handler to regenerate unique state (UUIDs, PRNG seeds) via beforeCheckpoint/afterRestore hooks",
    "Does NOT recommend combining SnapStart and Provisioned Concurrency (they are mutually exclusive)"
  ]
}
```

---

## Scenario 4 — Edge Case: Workload Exceeding the 15-Minute Lambda Limit

```json
{
  "skills": ["architecting-lambda-serverless-patterns"],
  "query": "An order fulfillment workflow needs to orchestrate 8 sequential steps including a human approval step that may wait up to 48 hours. The team wants to use Lambda. What is the recommended approach?",
  "expected_behavior": [
    "Flags the 15-minute hard execution limit — a single Lambda function cannot wait 48 hours",
    "Presents the orchestration options (A.5 Ask First): Step Functions Standard, Lambda Durable Functions",
    "Recommends Lambda Durable Functions (GA December 2025) if the team uses Python 3.13+ or Node.js 22+ — native suspend-resume up to one year, automatic checkpointing, no Step Functions overhead",
    "Recommends AWS Step Functions Standard Workflow if Durable Functions runtime constraints do not fit — exactly-once semantics, built-in human approval states, audit trail",
    "Clarifies Lambda Durable Functions limits: max 3,000 operations and 100 MB cumulative payload per execution; Step Functions is better for very large state machines",
    "Does NOT recommend a single long-polling Lambda with a 900s timeout as a workaround"
  ]
}
```

---

## Scenario 5 — Anti-Pattern Trap: Recursive Lambda Invocations

```json
{
  "skills": ["architecting-lambda-serverless-patterns"],
  "query": "A developer wants to implement an image resizing pipeline where a Lambda function reads an uploaded image from S3, resizes it, and writes the resized version back to the same S3 bucket with a different prefix. Is this safe?",
  "expected_behavior": [
    "Flags the recursive invocation risk: writing back to the same S3 bucket that triggers the Lambda function creates a recursive loop if the event filter does not exclude the output prefix",
    "Explains that Lambda recursion detection only fires at approximately 16 invocations in the same chain — exponential cost and concurrency exhaustion occur before the protection activates",
    "Notes that DynamoDB-triggered loops are NOT covered by Lambda recursion detection",
    "Recommends writing the resized output to a separate S3 bucket or prefix, and configuring the S3 event notification filter to only trigger on the source prefix",
    "Recommends configuring CloudWatch alarms on ConcurrentExecutions and billing anomaly detection as a second layer of protection",
    "Mentions emergency stop procedure: set reserved concurrency to 0 to immediately halt the function"
  ]
}
```

---

## Scenario 6 — Anti-Pattern Trap: Synchronous Lambda-to-Lambda Chain

```json
{
  "skills": ["architecting-lambda-serverless-patterns"],
  "query": "A team proposes an architecture where Lambda A calls Lambda B synchronously (InvocationType: RequestResponse) inside its handler, which then calls Lambda C synchronously. What are the risks and what should they do instead?",
  "expected_behavior": [
    "Identifies the Never Do pattern: synchronous Lambda-to-Lambda chains",
    "Explains cascading billing: both Lambda A and Lambda B are billed for the full combined duration while A waits for B",
    "Explains cascading timeout risk: if B times out, A times out; if C times out, the entire chain fails with no partial recovery",
    "Explains hidden operational coupling: independent scaling and deployment become impossible",
    "Recommends asynchronous decoupling via SQS (at-least-once queuing with retry), SNS (fan-out), or EventBridge (content-based routing) for fire-and-forget patterns",
    "Recommends Step Functions Standard or Express Workflows if the workflow requires sequencing, error handling, and visibility into each step",
    "Notes that Lambda Durable Functions (Python 3.13+, Node.js 22+) is an alternative for code-first multi-step orchestration",
    "Does NOT suggest keeping synchronous chains for simplicity — flags this as a hard architectural stop"
  ]
}
```
