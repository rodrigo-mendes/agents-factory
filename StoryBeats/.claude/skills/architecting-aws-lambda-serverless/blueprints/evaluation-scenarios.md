# Evaluation Scenarios — architecting-aws-lambda-serverless

**Skill version**: July 2026 service state  
**Purpose**: Validate that the skill activates correctly and guides the agent toward the right decisions.

---

## Scenario 1 — Canonical: Design a serverless REST API backend

```json
{
  "skills": ["architecting-aws-lambda-serverless"],
  "query": "Design a serverless REST API backend on AWS for an order management system. The API must handle up to 500 concurrent users with p99 latency under 200 ms. It needs to store orders in a database, retrieve credentials securely, and emit custom business metrics. The engineering team uses Python.",
  "expected_behavior": [
    "Recommends API Gateway (HTTP API or REST API) as the HTTP front door with AWS WAF for production protection — not a raw Function URL",
    "Specifies arm64 (Graviton) architecture as the default for cost efficiency",
    "Recommends SnapStart on Python 3.12+ for the p99 latency SLO given spiky traffic, with Provisioned Concurrency as an alternative for sustained-low-latency",
    "Specifies Amazon DynamoDB for low-latency persistence and Secrets Manager for runtime credentials",
    "Includes CloudWatch structured JSON logging, X-Ray tracing, and async EMF metrics via Powertools",
    "Recommends Lambda Power Tuning for memory right-sizing — does not guess 128 MB or a round number",
    "Uses IAM execution roles scoped to exact DynamoDB table ARN and specific actions — no wildcards",
    "References the Quick Reference limits table (e.g., payload 6 MB, timeout 900 s) when relevant",
    "Recommends versions + aliases with CodeDeploy canary for safe deployment"
  ]
}
```

**What a passing response looks like**: The agent produces an architecture diagram or structured recommendation covering all mandatory Always-Do patterns, asks the cold-start strategy question (SnapStart vs PC) based on traffic profile, and avoids recommending deprecated runtimes.

**Failure signals**: Agent recommends a Function URL for the public API without flagging WAF absence; hardcodes any credentials; fails to mention idempotency; does not mention right-sizing.

---

## Scenario 2 — Edge case: High-throughput async event pipeline near service limits

```json
{
  "skills": ["architecting-aws-lambda-serverless"],
  "query": "We need to process 50,000 events per minute from an IoT device fleet. Events are published to Kinesis Data Streams. Processing each event involves writing a record to DynamoDB and emitting metrics. Occasionally a malformed event appears and causes the entire batch to fail and retry repeatedly, causing processing delays.",
  "expected_behavior": [
    "Identifies the poison-record problem and recommends enabling ReportBatchItemFailures (partial batch response) on the Kinesis event source mapping",
    "Recommends enabling BisectBatchOnFunctionError to automatically split batches containing poison records",
    "Recommends configuring an on-failure destination (SQS DLQ) on the event source mapping to capture unprocessable records",
    "Warns that default concurrency limit is 1,000/account and recommends requesting a limit increase via AWS Support for high-throughput paths",
    "Recommends monitoring IteratorAge metric — alert if > 30,000 ms (stream falling behind)",
    "Confirms DynamoDB writes must be idempotent (keyed on Kinesis sequence number or message deduplication ID)",
    "Asks whether the function's DynamoDB table provisioning (on-demand vs provisioned) is sufficient for the write throughput",
    "Does NOT recommend chaining Lambda functions to handle overflows — points to Step Functions or Kinesis shard increase instead"
  ]
}
```

**What a passing response looks like**: The agent immediately identifies partial batch response and bisect-on-error as the solution to the poison-record problem, mentions IteratorAge monitoring, and confirms idempotency requirements without prompting. It stays within documented service limits.

**Failure signals**: Agent suggests catching exceptions and continuing without reporting batch item failures (silent drop); fails to mention IteratorAge; recommends Lambda-to-Lambda chaining to handle processing overflow.

---

## Scenario 3 — Anti-pattern trap: "Make Lambda run our 2-hour batch job"

```json
{
  "skills": ["architecting-aws-lambda-serverless"],
  "query": "Our data science team wants to migrate a nightly 2-hour data transformation batch job to Lambda. The job reads 50 GB of CSV files from S3, transforms them, and writes parquet files back to S3. Can we just chunk the data and have Lambda functions call each other in sequence to handle the full dataset?",
  "expected_behavior": [
    "Immediately flags that standard Lambda functions have a hard 15-minute (900 second) timeout — a 2-hour job cannot run in a single Lambda invocation",
    "Explicitly prohibits the Lambda-chaining approach (AP-4) — chaining in code creates a tightly-coupled monolith with no retry visibility and cascading failure risk",
    "Asks clarifying questions: Can the job be decomposed into independent sub-tasks each completing in < 15 min (Step Functions), or is it a long batch that belongs on a different compute service?",
    "Recommends AWS Step Functions Map state for parallel processing of independent chunks with built-in retry/error handling",
    "Recommends AWS Fargate (ECS) or AWS Batch as alternatives for jobs that genuinely cannot be decomposed into < 15-min steps",
    "If Step Functions is chosen, recommends distributing work with a Scatter-Gather pattern (fan-out to parallel Lambda workers, aggregate results) — not sequential chaining",
    "Confirms that any Lambda processing S3 files must use idempotent logic (same file processed twice = same output)",
    "Does NOT suggest workarounds like recursive Lambda self-invocation to bypass the 15-min limit"
  ]
}
```

**What a passing response looks like**: The agent immediately cites the 900-second hard limit, rejects the chaining pattern with an explicit reference to AP-4, asks the decomposability question, and offers Step Functions + parallel Map state or Fargate/Batch as correct alternatives. It does not attempt to engineer around the Lambda timeout limit.

**Failure signals**: Agent accepts the Lambda-chaining approach without objection; suggests using recursive self-invocation or writing intermediate state to S3 to chain invocations beyond 15 min; fails to mention the 900-second hard limit; proceeds without asking whether the job is decomposable.
