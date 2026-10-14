---
name: applying-aws-serverless-well-architected-lens
description: "Applies the AWS Well-Architected Serverless Applications Lens (2022-07-14 content) to production serverless workloads on Lambda, API Gateway, Step Functions, DynamoDB, SQS/SNS/EventBridge, and Cognito. Use when designing, reviewing, or auditing serverless architectures on AWS for pillar alignment, least-privilege IAM, API authorization, idempotency, DLQ, saga orchestration, structured logging, X-Ray tracing, and CloudWatch metrics. Supplement with current AWS Lambda Developer Guide for post-2022 capabilities (SnapStart, arm64/Graviton2, response streaming)."
---

> **CRITICAL CURRENCY WARNING**: The Serverless Applications Lens content is dated **2022-07-14**. The "2026" in the PDF title is a copyright boilerplate artifact only — no content revision occurred. Per the 12-month currency rule, all patterns carry the flag `> ⚠️ Source dated 2022-07`. Post-2022 capabilities (Lambda SnapStart, arm64/Graviton2, response streaming, recursion detection) are absent — verify independently. See [Post-2022 Gaps](./blueprints/post-2022-gaps.md).

## Function

Specialist in the AWS Well-Architected Framework — Serverless Applications Lens for production serverless workloads. Encodes six Well-Architected pillars narrowed to serverless-specific guidance: eight mandatory patterns, three architectural decisions, and five anti-patterns.

## Version Context

**Technology/Framework**: AWS Well-Architected Framework — Serverless Applications Lens
**Content date**: 2022-07-14 (HTML publication date, verified 2026-08-27)
**PDF copyright**: 2026 (auto-updated copyright — NOT a content revision date)
**Support status**: Active (no newer substantive revision published as of 2026-08-27)

**Pillars covered (serverless-specific)**:
- Operational Excellence — OPS 1: metrics/alerts, structured logging, distributed tracing
- Security — SEC 1/2/3: IAM least-privilege, API authorization, data protection
- Reliability — failure management: idempotency, DLQ, saga orchestration
- Performance Efficiency — PER 1: memory tuning, provisioned concurrency, capacity mode
- Cost Optimization — COST 1: 1-ms billing, performance-cost alignment
- Sustainability — deferred to base Well-Architected Framework (not substantively expanded)

**Post-2022 capabilities absent from this lens** (verify independently):
`Lambda SnapStart` · `arm64/Graviton2` · `Response Streaming` · `Recursion Detection` · `Lambda Destinations full guidance`

⚠️ **CRITICAL — Agent Warning**:
This skill targets the **2022-07-14 content revision** of the Serverless Applications Lens.
Reject any claim of "2026 Serverless Lens updated content" — that revision does not exist.
Supplement with the current AWS Lambda Developer Guide for post-2022 features.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 summaries (this file)
- **[Always-Do Patterns](./blueprints/always-do-patterns.md)** — 8 mandatory patterns with full detail
- **[Ask-First Decisions](./blueprints/ask-first-decisions.md)** — 3 decision matrices with tradeoff tables
- **[Never-Do Anti-Patterns](./blueprints/never-do-patterns.md)** — 5 anti-patterns with ❌/✅ examples
- **[Post-2022 Gaps](./blueprints/post-2022-gaps.md)** — Capabilities absent from the 2022 content
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Test scenarios for this skill
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands
- **[Quick Reference](#quick-reference)** — Critical metrics and limits at a glance
- **[External Resources](#external-resources)** — Official AWS documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For full patterns with config examples, see [Always-Do Patterns](./blueprints/always-do-patterns.md).

**1. One least-privilege IAM role per Lambda function** (SEC 2)
Sharing a role across functions violates least-privilege and "will likely violate least-privileged access." Assign each function a dedicated execution role scoped to only the specific actions and resources it needs. Use tag-based access control for API-level granularity.

**2. Enforce a real API authorization mechanism — never API keys alone** (SEC 1)
API Gateway API Keys are usage-tracking only, not a security gate. Use: `AWS_IAM` for AWS callers, `Cognito user pools` for end users/social IdP, `Lambda authorizer` for custom/external IdP, `resource policies` for account/IP/VPC isolation, `mTLS` for IoT/app-to-app. Layer AWS WAF managed rule groups (SQLi/XSS) in front.

**3. Orchestrate with Step Functions state machines, not chained Lambda code** (OPS/Reliability)
Direct `lambda.invoke` chains produce monolithic, tightly coupled applications. Use AWS Step Functions: Standard for durable/audited long-running workflows, Express for short high-volume. Move retry, back-off, catch, and saga rollback logic into the state machine definition.

**4. Design idempotent operations and attach a DLQ to every async function** (Reliability)
Events can be delivered more than once. Make all operations idempotent. For each async function: set `Destination on Failure` → SQS DLQ. For stream sources: set `MaximumRetryAttempts`, `MaximumRecordAge`, `BisectBatchOnFunctionError`. Inspect `UnprocessedItems` (BatchWriteItem) and `FailedRecordCount` (PutRecords) in batch responses.

**5. Emit structured JSON logs with correlation IDs** (OPS)
Avoid `print`/`console.log`. Emit JSON with: timestamp, level, service, function name, request ID, `cold_start` flag, and correlation ID. Use Powertools for AWS Lambda. Propagate correlation IDs to downstream services; sample DEBUG logs at scale.

**6. Enable AWS X-Ray active tracing on all Lambda functions** (OPS)
Set `TracingConfig=Active` on every function. Add X-Ray subsegments for external dependencies. Add annotations (indexed key-value pairs) for business transactions to enable trace filtering. Tune socket read/write timeouts to fail fast.

**7. Instrument CloudWatch four-tier metrics with tiered alarms** (OPS 1)
Four tiers: Business, Customer Experience, System, Operational. Alarm on: Lambda `Duration`, `Errors`, `Throttles`, `ConcurrentExecutions`, `DeadLetterErrors`, `ProvisionedConcurrencySpilloverInvocations`; streams `IteratorAge`; API Gateway `IntegrationLatency`, `Latency`, `5XXError`; SQS `ApproximateAgeOfOldestMessage`; DynamoDB throttle metrics; Step Functions `ExecutionsFailed`/`ExecutionThrottled`; EventBridge `FailedInvocations`/`ThrottledRules`.

**8. Encrypt sensitive data before logs/URLs/persistence; validate all input** (SEC 3)
URL path/query strings can leak into CloudWatch Logs unencrypted — never send PII in query strings. Encrypt at rest (KMS) on all stores (DynamoDB, S3, OpenSearch). Use API Gateway JSON-schema request validation plus deep app-level validation. Store secrets in Secrets Manager with rotation and audited access. Sign Lambda code with AWS Signer.

### ⚠️ Ask First

For full decision matrices, see [Ask-First Decisions](./blueprints/ask-first-decisions.md).

**Decision 1 — Lambda concurrency provisioning model per function**
- On-demand: spiky/unpredictable traffic, zero idle cost
- Provisioned Concurrency: latency-sensitive steady user-facing APIs, eliminates cold starts, adds always-on cost
- Reserved Concurrency: blast-radius isolation or throttle protection for critical/noisy functions, caps max throughput

Ask: Is the function latency-sensitive with steady traffic? Does it need isolation from the account-level throttle pool?

**Decision 2 — Step Functions workflow type**
- Express (Sync/Async): short-duration high-volume, at-least-once, cheaper per transition
- Standard: long-running durable audited workflows, exactly-once, higher per-transition cost

Ask: What is the expected execution duration, volume, and durability/audit requirement?

**Decision 3 — API Gateway endpoint type and DynamoDB capacity mode**
- Edge-optimized endpoint: geographically dispersed global consumers
- Regional endpoint: regional consumers or same-Region AWS-internal callers
- DynamoDB on-demand: unpredictable/spiky traffic, zero capacity planning
- DynamoDB provisioned: predictable consistent traffic, lower cost at high sustained utilization

Ask: Is traffic predictable (→ provisioned/regional) or bursty/global (→ on-demand/edge)?

### 🚫 Never Do

For full anti-patterns with ❌ Wrong / ✅ Correct code examples, see [Never-Do Anti-Patterns](./blueprints/never-do-patterns.md).

**1. Shared IAM role across multiple Lambda functions** — Violates SEC 2; enables lateral privilege escalation across functions; compliance violation. Use one dedicated least-privilege role per function.

**2. API Gateway API Keys as the sole authorization gate** — Not a security mechanism; keys are usage-tracking only; unauthorized callers get API access. Use AWS_IAM / Cognito / Lambda authorizer / resource policy / mTLS instead.

**3. Chaining Lambda functions via `lambda.invoke` in code** — Creates monolithic tightly coupled apps; hides failures; complicates retries and observability. Replace with Step Functions state machines.

**4. Async processing without DLQ or unchecked partial-batch failures** — Causes silent data loss and blocked Kinesis/DynamoDB stream shards. Attach on-failure destination → SQS DLQ; inspect `UnprocessedItems`/`FailedRecordCount`.

**5. Sensitive data in URL paths/query strings or unencrypted in storage** — URL query strings leak into CloudWatch Logs; unencrypted stores expose data on breach. Use POST body for PII; encrypt at rest with KMS; use Secrets Manager for credentials.

---

## Integration Patterns

For full examples, see [Always-Do Patterns](./blueprints/always-do-patterns.md).

**RESTful Microservice (standard path)**:
`AWS WAF` + `API Gateway` (real authorizer, throttling) → `Lambda` (dedicated least-privilege role, structured JSON logging, X-Ray active) → `DynamoDB` (encrypted at rest, KMS); CloudWatch four-tier alarms; async failures → SQS DLQ.

**Web Application**:
`CloudFront` + `S3` (static hosting) → `Cognito user pools` (auth tokens) → `API Gateway` → `Lambda` → `DynamoDB`; AWS Amplify for SPA atomic deploys and custom domains.

**High-Volume Stream Processing**:
`Kinesis` (enhanced fan-out per consumer) → `Lambda` (bisect-batch, max-retry, max-record-age, on-failure → SQS DLQ); alarm on `IteratorAge`; `Step Functions Express` for short orchestration steps.

**Multi-Step Transaction / Saga**:
`Step Functions Standard` (state machine: retry, catch, saga compensation branch, DLQ step) → `Lambda` functions (stateless, idempotent, dedicated roles) → `DynamoDB` (conditional writes for idempotency).

**Common problems**:
- **Throttled function starves downstream** → Set Reserved Concurrency; use SQS as buffer to absorb burst.
- **Cold start spikes user-facing latency** → Optimize static initialization; evaluate Provisioned Concurrency (⚠️ Ask First — adds standing cost).
- **Kinesis shard stuck on poison pill** → Enable `BisectBatchOnFunctionError` + `MaximumRetryAttempts` + `MaximumRecordAge` + on-failure DLQ.

---

## Verification Loop

Execute after each architecture decision or IaC code generation:

### 1. IAM — One Dedicated Role per Function

```bash
# List all function execution roles
aws lambda list-functions \
  --query 'Functions[*].[FunctionName,Role]' --output table

# Detect shared roles (any role ARN appearing more than once = violation)
aws lambda list-functions --query 'Functions[*].Role' \
  --output text | tr '\t' '\n' | sort | uniq -d
# Expected: no output
```

### 2. Async Functions — DLQ / On-Failure Destination

```bash
# Check async invocation config per function
aws lambda get-function-event-invoke-config \
  --function-name <FUNCTION_NAME>
# Expected: DestinationConfig.OnFailure.Destination set; MaximumRetryAttempts configured

# Check event source mapping DLQ (for SQS/Kinesis/DDB Streams triggers)
aws lambda list-event-source-mappings \
  --query 'EventSourceMappings[*].[FunctionArn,DestinationConfig,BisectBatchOnFunctionError]' \
  --output table
```

### 3. X-Ray Active Tracing — All Functions

```bash
aws lambda list-functions \
  --query 'Functions[*].[FunctionName,TracingConfig.Mode]' --output table
# Expected: every function shows Mode = Active
```

### 4. API Authorization — No API-Key-Only Methods

```bash
# List REST API resources and method auth types
aws apigateway get-resources --rest-api-id <API_ID> \
  --query 'items[*].resourceMethods' --output json
# Expected: no method has authorizationType=NONE without a resource policy;
# apiKeyRequired: true must accompany a real authorizer, not substitute for one
```

### 5. Encryption at Rest

```bash
# DynamoDB
aws dynamodb describe-table --table-name <TABLE_NAME> \
  --query 'Table.SSEDescription'
# Expected: Status=ENABLED, SSEType=KMS

# S3
aws s3api get-bucket-encryption --bucket <BUCKET_NAME>
# Expected: SSEAlgorithm=aws:kms
```

**Troubleshooting**:
- Shared roles found → Create per-function roles; scope policies to minimum required actions and resource ARNs.
- Missing DLQ → `aws lambda put-function-event-invoke-config --destination-config '{"OnFailure":{"Destination":"<SQS_ARN>"}}'`
- `TracingConfig=PassThrough` → `aws lambda update-function-configuration --tracing-config Mode=Active --function-name <NAME>`
- DynamoDB SSEDescription absent → Enable server-side encryption (KMS) in table definition.

---

## Quick Reference

**Critical CloudWatch alarms per service** (lens OPS 1, content date 2022-07-14):

| Service | Metric | Alert Condition |
|---------|--------|-----------------|
| Lambda | Errors | > 0 sustained |
| Lambda | Throttles | > function threshold |
| Lambda | Duration | approaching configured timeout |
| Lambda | ConcurrentExecutions | approaching reserved/account limit |
| Lambda | DeadLetterErrors | > 0 |
| Lambda | ProvisionedConcurrencySpilloverInvocations | > 0 |
| Kinesis / DDB Streams | IteratorAge | increasing or stalled |
| API Gateway | 5XXError | > 0 sustained |
| API Gateway | IntegrationLatency | exceeds SLA |
| SQS | ApproximateAgeOfOldestMessage | exceeds threshold |
| Step Functions | ExecutionsFailed / ExecutionThrottled | > 0 |
| EventBridge | FailedInvocations / ThrottledRules | > 0 |

**Lambda concurrency limits (AWS regional defaults)**:

| Resource | Default | Notes |
|----------|---------|-------|
| Concurrent executions (account) | 1,000 per region | Soft limit; request increase via Support |
| Reserved concurrency | Per-function cap | Protects AND limits that function |
| Provisioned concurrency | Per-function, pre-warmed | Always-on cost even at zero traffic |

**Post-2022 features — verify separately** (not in this lens):
`SnapStart (Java/Python/.NET)` · `arm64/Graviton2 compute` · `Response Streaming` · `Recursion Detection`

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/applying-aws-serverless-well-architected-lens/
├── SKILL.md                              <- This file (summaries + guardrails)
└── blueprints/
    ├── always-do-patterns.md             <- 8 mandatory patterns with full config detail
    ├── ask-first-decisions.md            <- 3 decision matrices with tradeoff tables
    ├── never-do-patterns.md              <- 5 anti-patterns with ❌ Wrong / ✅ Correct
    ├── post-2022-gaps.md                 <- Capabilities absent from 2022 lens content
    └── evaluation-scenarios.md           <- Test scenarios for this skill
```

---

## External Resources

> ⚠️ All Serverless Lens sources dated **2022-07-14**, accessed **2026-08-27**. Verify currency before production decisions.

### Serverless Lens (Official AWS — 2022-07-14 content)
- [Welcome / publication date](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html)
- [General Design Principles](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html)
- [Identity & Access Management (SEC 1/2)](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html)
- [Data Protection (SEC 3)](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/data-protection.html)
- [Failure Management (DLQ, idempotency, saga)](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html)
- [Operate — Metrics and Alerts (OPS 1)](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-metrics-and-alerts.html)
- [Structured Logging](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-logging.html)
- [Distributed Tracing (X-Ray)](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-distributed-tracing.html)
- [Selection / Performance Efficiency (PER 1)](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/selection.html)
- [Cost-Effective Resources (COST 1)](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/cost-effective-resources.html)
- [Reference Scenarios](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/scenarios.html)

### Post-2022 Supplements (verify for current capabilities)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html) — SnapStart, arm64/Graviton2, response streaming, recursion detection
- [Powertools for AWS Lambda](https://docs.powertools.aws.dev/lambda/) — Structured logging, metrics, tracing (current product name)
