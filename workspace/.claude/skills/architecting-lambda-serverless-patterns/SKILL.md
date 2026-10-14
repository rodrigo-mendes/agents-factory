---
name: architecting-lambda-serverless-patterns
description: "Architects AWS Lambda serverless solutions with production-grade guardrails covering security, reliability, and performance. Use when designing Lambda functions, selecting invocation models, mitigating cold starts, configuring concurrency controls, or reviewing serverless architecture patterns on AWS (Lambda 2026, research dated 2026-08-28)."
---

## Function

Specialist in AWS Lambda serverless architecture patterns, guardrails, and operational best practices for Lambda 2026 — including Lambda Durable Functions, SnapStart for Python/.NET, Lambda MicroVMs, and scalable network bandwidth introduced in 2026.

## Version Context

**Technology**: AWS Lambda
**Target version**: Lambda 2026 (research date: 2026-08-28; valid through: 2027-08-28)
**Support status**: Active

**Significant 2026 updates**:
- **Lambda Durable Functions (GA December 2025, 30+ regions)**: Native multi-step workflow orchestration for Python 3.13+ and Node.js 22+; suspend up to one year with automatic checkpointing; eliminates Step Functions overhead for code-first workflows
- **Lambda MicroVMs (June 2026)**: VM-level isolation with snapshot-resume for AI sandboxes (ARM64 only; separate quota system; up to 8-hour sessions)
- **SnapStart expanded**: Now supports Python 3.12+ and .NET 8+ in addition to Java 11+
- **Scalable Network Bandwidth (August 2026)**: Non-VPC functions scale from 625 Mbps at 2 GB to 3,000 Mbps at 10,240 MB
- **Self-Managed Code Storage (July 2026)**: Code from customer-owned S3 buckets; managed storage limit increased from 75 GB to 300 GB
- **CloudWatch Application Signals**: No-code ADOT-backed APM with SLOs; no instrumentation code changes required (remove existing X-Ray SDK code first)

**Imminent deprecations** (migrate before these dates):
- `python3.10` — October 31, 2026
- `.NET 8` and `.NET 9` — November 10, 2026
- `Amazon Linux 2` — EOL June 30, 2026 (already past)

**Rejected patterns**: Amazon Linux 2 runtimes, `python3.10` after October 2026, `.NET 8/.NET 9` after November 2026, synchronous Lambda-to-Lambda chains, shared IAM execution roles across functions.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 operational rules
- **[Integration Patterns](#integration-patterns)** — Event-driven, fan-out, saga, CQRS, stream processing
- **[Verification Loop](#verification-loop)** — Post-implementation validation commands
- **[Quick Reference](#quick-reference)** — Critical limits and essential commands
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases for skill validation
- **[External Resources](#external-resources)** — Official dated documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

**1 — One dedicated IAM execution role per function** (Security)
Attach a unique IAM execution role to every Lambda function scoped only to the permissions that function requires. Use IAM Access Analyzer with CloudTrail activity to generate minimum-privilege policies. Baseline managed policy for all functions: `AWSLambdaBasicExecutionRole` (CloudWatch Logs write). Add `AWSLambdaVPCAccessExecutionRole` for VPC-attached functions. Define and manage roles via SAM, CDK, or CloudFormation — never share one role across multiple functions.

**2 — Configure DLQ and on-failure destinations for every async-invoked function** (Reliability)
Lambda retries async invocations twice (function errors) and up to 6 hours (throttles). Without a DLQ or on-failure destination, events that exhaust retries are permanently and silently discarded. Configure `DeadLetterConfig` (SQS standard or SNS standard — not FIFO) AND `DestinationConfig.OnFailure` (SQS, SNS, Lambda, or EventBridge) for every async function. For SQS ESM triggers, configure the DLQ on the SQS source queue — not on the Lambda function.

**3 — Design all functions for idempotency** (Reliability)
Lambda delivers events at-least-once regardless of invocation model. Use Powertools for AWS Lambda Idempotency utility (Python, TypeScript, Java, .NET) backed by DynamoDB for automatic duplicate detection with configurable TTL. Processing the same event multiple times must produce the same outcome with no duplicate side effects.

**4 — Set reserved concurrency on all production functions** (Reliability + Performance)
Default account concurrency is 1,000 concurrent executions per region — shared across all functions. A single high-traffic function without reserved concurrency can throttle every other function in the account. Formula: `reserved_concurrency = avg_rps × avg_duration_seconds × 1.1` (add 10% buffer). Always preserve at least 100 unreserved concurrency for functions without explicit settings. Apply Provisioned Concurrency only to latency-sensitive user-facing API functions — not to async or batch consumers.

**5 — Set timeout and memory from load test data** (Performance Efficiency + Reliability)
Default timeout is 3 seconds; maximum is 900 seconds. Set `timeout = p99_duration + safety_buffer`. For SQS-triggered functions, function timeout must not exceed the SQS Visibility Timeout. Memory drives CPU: 1,792 MB = 1 vCPU; 10,240 MB = 6 vCPUs. Monitor `Max Memory Used` in CloudWatch REPORT log lines. Run Lambda Power Tuning (open-source GitHub tool) for cost-optimal memory sizing.

**6 — Use structured JSON logging with Embedded Metric Format (EMF)** (Operational Excellence)
Use Powertools Logger for automatic JSON formatting (requestId, log level, timestamp, cold start flag). Use Powertools Metrics (EMF-backed) for all custom metrics — never call `cloudwatch:PutMetricData` synchronously inside the handler. Set log level via `LOG_LEVEL` environment variable. Retain CloudWatch log groups at least 90 days for regulated workloads. Configure alarms on error rate and p99 Duration.

**7 — Encrypt sensitive environment variables with a Customer-Managed KMS Key** (Security)
AWS-managed key encryption provides no customer control over key rotation or usage auditing. Use a CMK for environment variables holding sensitive configuration. For access credentials (API keys, database passwords), prefer Secrets Manager or SSM Parameter Store SecureString — fetch at cold-start initialization outside the handler using the AWS Parameters and Secrets Lambda Extension or Powertools parameters utility, not on every invocation. Total environment variable payload limit: 4 KB.

**8 — Attach to customer VPC only when private resource access is required** (Security + Performance)
Lambda already runs inside an AWS-managed VPC invisible to customers. Customer VPC attachment adds Hyperplane ENI provisioning time (minutes for new subnet and security group combinations), a 14-day idle reclaim window, and EC2 API permission requirements. Attaching a function to a public subnet does NOT grant internet access or a public IP. Attach only for private-subnet resources (RDS, ElastiCache, OpenSearch). Reuse the same subnet and security group combination across functions to enable Hyperplane ENI sharing.

---

### ⚠️ Ask First

**A.1 — Lambda vs Fargate vs EC2**
Before recommending Lambda, confirm execution duration, memory ceiling, and traffic pattern. Lambda has a hard 15-minute execution limit and a 10 GB memory ceiling. Fargate supports up to 244 GB memory and persistent connections. EC2 is suited for sustained compute at scale or specialized hardware. For workloads waiting on human approvals or external callbacks, evaluate Lambda Durable Functions first (Python 3.13+ / Node.js 22+, up to one year suspend).

**A.2 — Synchronous vs asynchronous invocation model**
Confirm whether the caller requires an immediate response. Synchronous (API Gateway / ALB) is the only correct choice for user-facing real-time APIs. Async via SQS is preferred for all non-user-facing workloads. Ask about ordering requirements (SQS FIFO vs standard), fan-out (SNS), and content-based routing (EventBridge) before selecting the trigger architecture. Implement `batchItemFailures` (partial batch response) for SQS ESMs to avoid full-batch retries on partial failures.

**A.3 — Single-purpose function vs Lambdalith**
If the target is a migration or prototype, a Lambdalith is acceptable temporarily. Confirm whether this is a target architecture or a migration milestone. For production greenfield, require single-responsibility functions. If a Lambdalith exists in production, recommend strangler fig decomposition. Note: AWS Migration Hub Refactor Spaces is no longer open to new customers (November 7, 2025); AWS Transform is the recommended alternative for strangler fig proxy automation.

**A.4 — Provisioned Concurrency vs On-Demand vs SnapStart**
Ask about p99 latency SLA, runtime, and cost tolerance before recommending a cold-start strategy. Default: on-demand for async workloads. For user-facing endpoints with Java, .NET, or Python: evaluate SnapStart first (sub-second cold starts, no idle billing). Use Provisioned Concurrency when SnapStart is insufficient or the runtime is unsupported (Node.js, Ruby). Provisioned Concurrency and SnapStart are mutually exclusive per function version — choose one strategy.

**A.5 — Orchestration (Step Functions) vs Choreography (EventBridge) vs Lambda Durable Functions**
Confirm workflow complexity, execution duration, and auditability requirements. Step Functions Standard: complex branching, exactly-once execution, compliance audit trails (up to 1 year). Step Functions Express: high-volume short-duration processing (up to 5 minutes, 100,000 executions/sec). EventBridge: loose-coupled choreography across bounded contexts. Lambda Durable Functions: code-first workflows exceeding 15 minutes in Python 3.13+ or Node.js 22+ with a max of 3,000 operations and 100 MB cumulative payload per execution.

---

### 🚫 Never Do

| Anti-Pattern | Risk | Alternative |
|---|---|---|
| **Wildcard IAM permissions** (`"Action": "*"` or `"Resource": "*"`) in execution role | CRITICAL — full account compromise on exploit; privilege escalation | Specific actions scoped to specific ARNs; generate minimum-privilege policy via IAM Access Analyzer + CloudTrail |
| **No DLQ or on-failure destination for async-invoked functions** | HIGH — silent permanent event loss on any failure; no audit trail | Configure both `DeadLetterConfig` (SQS/SNS standard) and `DestinationConfig.OnFailure` on every async function |
| **Hardcoded secrets in source code or plain environment variables** | CRITICAL — exposed in git history, deployment artifacts, and CloudTrail `GetFunction` responses | CMK-encrypted env vars for non-sensitive config; Secrets Manager or SSM SecureString for credentials, fetched at cold-start outside the handler |
| **Recursive Lambda invocations** (function writes to trigger that invokes same function) | CRITICAL — exponential cost escalation and concurrency exhaustion before recursion detection fires at ~16 invocations | Separate functions per logical stage with distinct source and target resources. Emergency stop: set reserved concurrency to `0` |
| **Synchronous Lambda-to-Lambda chains** (`InvocationType: RequestResponse` inside handler) | HIGH — cascading billing, cascading timeouts, hidden coupling | Decouple via SQS (queuing + retry), SNS (fan-out), EventBridge (routing), or Step Functions / Lambda Durable Functions (orchestration) |
| **Long-running monolithic functions in production** (900s timeout, all routes in one function) | MEDIUM — large cold-start penalty, no partial retry on failure, broad IAM blast radius | Decompose into single-responsibility functions coordinated by Step Functions Standard / Express or Lambda Durable Functions |
| **Attaching all functions to VPC regardless of need** | MEDIUM — Hyperplane ENI provisioning delay, 14-day idle reclaim, no security benefit for public-endpoint-only functions | VPC-attach only for private-subnet resources; use VPC Gateway Endpoints (S3, DynamoDB) or Interface Endpoints for private routing without Lambda VPC attachment |
| **Sharing one IAM execution role across multiple functions** | HIGH — blast radius of any single function compromise expands to all services accessible by the shared role | One dedicated execution role per function, defined via SAM/CDK/CloudFormation |

---

## Integration Patterns

**Lambda + API Gateway (Synchronous HTTP)** — HTTP API is ~70% cheaper than REST API with lower latency; use REST API when WAF, caching, usage plans, or custom authorizers are required. API Gateway default throttle (10,000 RPS) does not align with Lambda default concurrency (1,000) — tune both together.

**Lambda + SQS ESM (Async Queue Consumer)** — Configure `BatchSize` and `MaximumBatchingWindowInSeconds` for throughput/latency balance. Return `batchItemFailures` (partial batch response) to avoid retrying successfully processed messages. Configure DLQ on the SQS source queue. SQS ESM Provisioned mode scales 3x faster, up to 100,000 concurrent invocations.

**Lambda + EventBridge (Event-Driven Choreography)** — EventBridge retries up to 185 times over 24 hours with exponential backoff. Content-based pattern-matching rules route events to targets without producer knowledge of consumers. Consumers must be idempotent (at-least-once delivery).

**Lambda + Kinesis / DynamoDB Streams (Ordered Stream Processing)** — One concurrent execution per shard by default; parallelization factor up to 10 for Kinesis Data Streams. Enable `BisectBatchOnFunctionError` to isolate poison-pill records. Set `MaximumRetryAttempts` to prevent indefinitely blocked shards.

**Lambda + Step Functions (Orchestrated Workflows)** — Standard Workflows: exactly-once semantics, audit trail, up to 1-year execution. Express Workflows: high-volume (100,000/sec), up to 5 minutes. Combine patterns: Step Functions orchestrates internal workflow and emits completion events to EventBridge for downstream choreography.

**Lambda + Lambda Durable Functions (Code-First Long-Running Workflows)** — GA December 2025, available in 30+ regions. Python 3.13+ and Node.js 22+ only. Suspend up to one year via Firecracker MicroVM snapshots. Max 3,000 operations and 100 MB cumulative payload per execution; use Step Functions for larger state machines.

---

## Verification Loop

Execute after each implementation or configuration change.

### 1. Deploy

```bash
sam build && sam deploy
# Expected: CREATE_COMPLETE or UPDATE_COMPLETE
# Exit code: 0
```

### 2. Verify Function Configuration

```bash
aws lambda get-function-configuration --function-name <name> \
  --query '[FunctionName,Runtime,Timeout,MemorySize,Role,KMSKeyArn,VpcConfig]'
# Expected: Runtime not deprecated; Timeout proportional to p99; KMSKeyArn non-null for sensitive config
```

### 3. Verify Concurrency and Async Failure Config

```bash
aws lambda get-function-concurrency --function-name <name>
aws lambda get-function-event-invoke-config --function-name <name>
# Expected: ReservedConcurrentExecutions set; DeadLetterConfig.TargetArn and
#           DestinationConfig.OnFailure.Destination both non-null for async functions
```

### 4. Verify IAM Role Isolation

```bash
aws lambda list-functions --query 'Functions[*].[FunctionName,Role]' --output table
# Expected: no two functions share the same Role ARN
```

### 5. Smoke Test

```bash
aws lambda invoke --function-name <name> --payload '{"test": true}' response.json
cat response.json
# Expected: statusCode 200 (or domain success code); no error key in response body
# Exit code: 0
```

**Troubleshooting**:
- Cold start > 1s on Java/Python/.NET → enable SnapStart (requires published version, not `$LATEST`)
- `TooManyRequestsException` → check `ConcurrentExecutions` CloudWatch metric vs reserved concurrency ceiling
- Timeout errors → inspect CloudWatch REPORT logs for p99 Duration vs configured Timeout
- VPC function stuck in `Pending` → check Hyperplane ENI provisioning; verify subnet and security group combination
- `RecursiveInvocationsDropped` CloudWatch metric > 0 → investigate event source for self-referential triggers

---

## Quick Reference

**Essential commands**:
```bash
sam build && sam deploy                                                           # Build and deploy
aws lambda invoke --function-name <name> --payload '{}' out.json                 # Smoke test
aws lambda get-function-configuration --function-name <name>                     # Inspect config
aws lambda put-function-concurrency --function-name <name> \
  --reserved-concurrent-executions 0                                             # Emergency stop (throttle)
aws logs filter-log-events --log-group-name /aws/lambda/<name> \
  --filter-pattern "REPORT"                                                       # Duration + memory stats
aws iam simulate-principal-policy --policy-source-arn <role-arn> \
  --action-names <actions>                                                        # Verify least-privilege
```

**Critical limits**:

| Resource | Limit | Notes |
|---|---|---|
| Execution timeout | 900 seconds (15 min) | Hard limit; use Durable Functions / Step Functions for longer workflows |
| Memory | 128 MB – 10,240 MB | 1,792 MB = 1 vCPU; 10,240 MB = 6 vCPUs |
| Default account concurrency | 1,000 per region | 100 always reserved for unreserved functions; raisable via Service Quotas |
| Burst scaling | +1,000 environments per 10 seconds | Per function |
| Unzipped deployment package | 250 MB | Includes layers; container images exempt |
| Ephemeral storage (/tmp) | 512 MB – 10,240 MB | Not shared between concurrent environments |
| Lambda layers per function | 5 maximum | Counts toward 250 MB unzipped limit |
| Environment variables | 4 KB total payload | Use Secrets Manager for larger config |
| Buffered response payload | 6 MB | Up to 200 MB with response streaming |
| Lambda Durable Functions | 3,000 operations / 100 MB cumulative payload | Python 3.13+ / Node.js 22+ only |
| Network bandwidth (non-VPC) | 625 Mbps at 2 GB → 3,000 Mbps at 10,240 MB | August 2026 update |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/architecting-lambda-serverless-patterns/
├── SKILL.md                          <- This file (guardrails + integration patterns)
└── blueprints/
    └── evaluation-scenarios.md       <- 6 test cases for skill validation
```

---

## External Resources

### Official Documentation (source date: 2026-08-28)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/) — Primary reference
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) — Core recommendations
- [Lambda Execution Role](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html) — IAM and resource-based policies
- [Async Invocation Error Handling](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html) — DLQ and on-failure destinations
- [Lambda Concurrency Configuration](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html) — Reserved and Provisioned Concurrency
- [SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html) — Cold start mitigation (Java 11+, Python 3.12+, .NET 8+)
- [Lambda VPC Configuration](https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html) — Hyperplane ENIs
- [Lambda MicroVMs Guide](https://docs.aws.amazon.com/lambda/latest/dg/lambda-microvms-guide.html) — VM-level isolation (June 2026)
- [Lambda Durable Functions announcement](https://aws.amazon.com/about-aws/whats-new/2025/12/lambda-durable-multi-step-applications-ai-workflows/) — Multi-step orchestration GA (December 2025)
- [Lambda Pricing](https://aws.amazon.com/lambda/pricing/) — Tiered pricing, arm64, Provisioned Concurrency rates
- [CloudWatch Application Signals for Lambda](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-application-signals.html) — No-code APM

### Architecture References
- [Serverless Applications Lens — Well-Architected](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/restful-microservices.html)
- [Lambda vs Fargate Decision Guide](https://docs.aws.amazon.com/decision-guides/latest/fargate-or-lambda/fargate-or-lambda.html)
- [Saga Orchestration Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-orchestration.html)
- [Event-Driven Architecture Concepts](https://docs.aws.amazon.com/lambda/latest/dg/concepts-event-driven-architectures.html)
- [Lambda Recursion Detection](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) — RecursiveInvocationsDropped metric
