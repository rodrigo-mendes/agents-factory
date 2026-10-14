# Evaluation Scenarios — applying-aws-serverless-well-architected-lens

Test cases for `/evaluating-skill-scenarios applying-aws-serverless-well-architected-lens`.
Each scenario verifies the skill guides the agent to a correct, source-aligned decision.

---

## Scenario 1 — Canonical: New serverless API design review

```json
{
  "skills": ["applying-aws-serverless-well-architected-lens"],
  "query": "I am designing a serverless REST API on AWS using API Gateway and Lambda backed by DynamoDB. What are the minimum Well-Architected requirements I must meet before going to production?",
  "expected_behavior": [
    "Cites the critical currency warning: lens content is 2022-07-14, not a 2026 revision",
    "Mandates one dedicated least-privilege IAM execution role per Lambda function (SEC 2)",
    "Mandates a real API authorization mechanism — AWS_IAM / Cognito / Lambda authorizer — and explicitly states API Keys are NOT sufficient (SEC 1)",
    "Mandates X-Ray active tracing enabled on all functions (TracingConfig=Active)",
    "Mandates structured JSON logging with correlation IDs using Powertools for AWS Lambda",
    "Mandates CloudWatch four-tier alarms covering Lambda Errors, Throttles, Duration, 5XXError on API Gateway",
    "Mandates encryption at rest (KMS) on DynamoDB and S3; secrets in Secrets Manager",
    "Mandates per-function on-failure destination or SQS DLQ for any async invocations",
    "Asks about traffic pattern (spiky vs steady) and latency sensitivity before recommending on-demand vs provisioned concurrency (⚠️ Ask First)",
    "Recommends verifying SnapStart/arm64 guidance in the current AWS Lambda Developer Guide (post-2022 gap)"
  ]
}
```

---

## Scenario 2 — Edge Case: High-volume stream processing with multiple consumers

```json
{
  "skills": ["applying-aws-serverless-well-architected-lens"],
  "query": "We have Amazon Kinesis Data Streams with five Lambda consumers processing the same stream. We are seeing consumer lag and occasional stuck shards. What does the Well-Architected Serverless Lens say about this?",
  "expected_behavior": [
    "Recommends Kinesis Enhanced Fan-Out to provide dedicated read throughput per consumer when multiple consumers share a stream",
    "Identifies BisectBatchOnFunctionError as the mechanism to handle poison-pill records that stall shard processing",
    "Recommends setting MaximumRetryAttempts and MaximumRecordAge to bound retry behavior on stream sources",
    "Recommends configuring on-failure destination → SQS DLQ for failed batch processing",
    "Recommends alarming on IteratorAge metric to detect consumer lag and stuck shards proactively",
    "Recommends Step Functions Express Workflow for short-duration high-volume orchestration steps if applicable",
    "Notes the lens content is dated 2022-07-14 and enhanced fan-out / stream guidance should be verified against current Kinesis documentation"
  ]
}
```

---

## Scenario 3 — Misuse / Anti-Pattern Trap: Shared role and API keys for faster shipping

```json
{
  "skills": ["applying-aws-serverless-well-architected-lens"],
  "query": "To ship faster, our team wants to use a single broad IAM execution role called lambda-exec-role with DynamoDB:* on * across all 15 Lambda functions, and secure the API Gateway with API Keys only. Is this acceptable?",
  "expected_behavior": [
    "Explicitly rejects both proposals as violations of SEC 1 and SEC 2",
    "States that sharing one IAM role across functions violates least-privilege and 'will likely violate least-privileged access' per the lens",
    "States that API Gateway API Keys are NOT a security mechanism — they are usage-tracking only and must not be the sole authorization gate",
    "Provides the correct alternative: one dedicated execution role per function scoped to specific actions and resource ARNs",
    "Provides the correct alternative: use AWS_IAM, Cognito user pools, Lambda authorizer, resource policies, or mTLS as the authorizer",
    "Does NOT accept the framing that 'shipping faster' justifies these security anti-patterns",
    "Offers to help scope the minimum IAM policies per function and choose the correct auth mechanism based on caller type"
  ]
}
```

---

## Scenario 4 — Edge Case: Workflow orchestration refactoring

```json
{
  "skills": ["applying-aws-serverless-well-architected-lens"],
  "query": "Our order processing flow has Lambda function A that calls Lambda function B via lambda:InvokeFunction, which calls function C, with retry logic embedded in the function code. Should we change this?",
  "expected_behavior": [
    "Identifies this as the 'code-chained Lambda orchestration' anti-pattern from the lens",
    "States that this 'results in a monolithic and tightly coupled application' per the general design principles",
    "Recommends migrating to an AWS Step Functions state machine",
    "Asks about execution duration and volume before recommending Express vs Standard workflow type (⚠️ Ask First)",
    "Notes that retry, back-off, catch, and saga compensation logic should move into the state machine ASL definition",
    "Recommends Standard workflow if the order flow requires durable execution history and audit; Express if it is short-lived and high-volume"
  ]
}
```

---

## Scenario 5 — Canonical: Observability setup audit

```json
{
  "skills": ["applying-aws-serverless-well-architected-lens"],
  "query": "We use console.log for logging and have no custom metrics. What observability stack does the Well-Architected Serverless Lens require?",
  "expected_behavior": [
    "Flags console.log / print as explicitly unfavorable per the lens — recommends structured JSON logging instead",
    "Specifies required JSON log fields: timestamp, level, service, function name, request ID, cold_start flag, correlation ID",
    "Recommends Powertools for AWS Lambda (noting the lens calls it 'Lambda Powertools' but current name is Powertools for AWS Lambda)",
    "Mandates AWS X-Ray active tracing with subsegments for external dependencies and annotations for business transactions",
    "Describes the four-tier CloudWatch metric model: Business, Customer Experience, System, Operational",
    "Lists minimum required alarms: Lambda Errors/Throttles/Duration/ConcurrentExecutions/DeadLetterErrors; API Gateway 5XXError/IntegrationLatency; SQS ApproximateAgeOfOldestMessage; Step Functions ExecutionsFailed",
    "Recommends CloudWatch Embedded Metric Format (EMF) for async zero-latency custom metrics",
    "Recommends CloudWatch Logs Insights for querying structured JSON logs with auto-discovered fields"
  ]
}
```

---

## Scenario 6 — Currency / Gap Awareness: SnapStart recommendation

```json
{
  "skills": ["applying-aws-serverless-well-architected-lens"],
  "query": "We have a Java Lambda with high cold-start latency. The Well-Architected Serverless Lens says to use SnapStart. Can you walk me through that?",
  "expected_behavior": [
    "Immediately flags that Lambda SnapStart is NOT covered in the Serverless Applications Lens — lens content is dated 2022-07-14 and SnapStart was released after that date",
    "Does NOT fabricate SnapStart guidance attributed to the lens",
    "Directs the user to the current AWS Lambda Developer Guide for authoritative SnapStart configuration",
    "Explains what the lens DOES say about cold-start mitigation: optimize static initialization and consider Provisioned Concurrency for latency-sensitive functions",
    "Notes that Provisioned Concurrency eliminates cold starts but adds always-on cost (⚠️ Ask First — evaluate traffic pattern and SLA requirements)",
    "Lists SnapStart as an item in the post-2022 gaps that must be verified in current AWS documentation"
  ]
}
```
