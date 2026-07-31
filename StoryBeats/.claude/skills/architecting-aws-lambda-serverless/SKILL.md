---
name: architecting-aws-lambda-serverless
description: "Architects event-driven serverless workloads on AWS Lambda following Well-Architected Serverless Lens principles. Use when designing, reviewing, or implementing Lambda-based API backends, async event pipelines, or stream processors on AWS."
---

## Function

Specialist in AWS Lambda serverless architecture patterns — security, reliability, performance, and cost — aligned to the AWS Well-Architected Serverless Applications Lens and the Lambda Developer Guide (July 2026 service state).

## Version Context

**Technology**: AWS Lambda  
**Target State**: July 2026 service state (Lambda Developer Guide — continuously updated)  
**Research Date**: 2026-07-31  
**Currency Threshold**: Review after 2027-07-31 — cloud service limits and runtimes evolve rapidly

**Critical — AL2 EOL June 30, 2026**: AL2-based runtimes are deprecated. Migrate all functions on `provided.al2`, `java11`, `java17`, `python3.10`, `python3.11`, `ruby3.2` to AL2023-based equivalents immediately.

**Supported runtimes (July 2026)**: `nodejs24.x`/`nodejs22.x` · `python3.14`–`python3.12` · `java25`/`java21` · `dotnet10`/`dotnet8` · `ruby4.0`/`ruby3.3` · `provided.al2023` — all on x86_64 and arm64 (Graviton).

**SnapStart GA**: Java 11+, Python 3.12+, .NET 8+ (expanded to 23 additional regions June 2025).

⚠️ **Version Lock**: Patterns target July 2026 service state. Do not apply pre-2023 patterns without verifying against the Lambda Developer Guide.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 10 mandatory patterns: execution-env reuse, least-privilege IAM, idempotency, observability, secrets, right-sizing, DLQ/destinations, versions/aliases, runtime currency, recursion guard
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 7 architectural decisions: packaging, cold-start strategy, CPU arch, concurrency control, orchestration model, VPC, HTTP front door
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 9 critical anti-patterns with ❌ wrong / ✅ correct code pairs
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Lambda ↔ API Gateway, SQS, DynamoDB Streams, Step Functions, EventBridge
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 scenarios: API backend, async pipeline, anti-pattern trap
- **[Verification Loop](#verification-loop)** — CLI validation commands
- **[Quick Reference](#quick-reference)** — Service limits and essential commands
- **[External Resources](#external-resources)** — Official documentation

---

## Blueprints & Guardrails

### ✅ Always Do

For full patterns with executable code, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Mandatory patterns** (Complex tier — all 10 required; security-critical, multi-service):

- **Initialize clients/connections outside the handler** — Execution environment reuse reduces latency and cost; never store mutable user/session state in globals.
- **Least-privilege execution role** — One role per function; scope `Action` and `Resource` to exact ARNs; no `*` wildcards in production.
- **Idempotent handlers on at-least-once sources** — SQS/Kinesis/DynamoDB Streams deliver at least once; use idempotency keys + Powertools Idempotency or conditional DynamoDB writes.
- **Structured JSON logging + async EMF metrics** — CloudWatch Logs Insights + X-Ray tracing; emit custom metrics via EMF asynchronously, not synchronous `PutMetricData`.
- **Secrets outside code + KMS-encrypted env vars** — Retrieve from Secrets Manager or SSM Parameter Store at runtime; encrypt env vars with a customer-managed KMS key.
- **Right-size memory and timeout — measure, don't guess** — Run AWS Lambda Power Tuning; read `Max Memory Used` from CloudWatch `REPORT` lines.
- **Async error handling: DLQ/on-failure destinations + partial batch response** — Async invocations need a DLQ or Destination; stream/queue event sources need `ReportBatchItemFailures`.
- **Versions + aliases for safe deploy and rollback** — CodeDeploy canary/linear traffic shifting; rollback = repoint alias, not code rollback.
- **Stay on a supported runtime; own the upgrade cadence** — Trusted Advisor "Functions Using Deprecated Runtimes"; subscribe to Health Dashboard (180-day deprecation notice).
- **Guard against recursive invocation loops** — Never write to a function's own trigger source; set reserved concurrency to `0` immediately to throttle a runaway function.

### ⚠️ Ask First

For decision matrices with trade-offs and cost profiles, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Decision points** (confirm before committing to an approach):

- **Packaging: .zip archive vs container image** — Prefer .zip unless deps exceed 250 MB unzipped or an existing container pipeline is required.
- **Cold-start strategy: none vs SnapStart vs Provisioned Concurrency** — On-demand for async/batch; SnapStart for spiky latency-sensitive traffic (supported runtimes only); Provisioned Concurrency for sustained low-latency.
- **CPU architecture: arm64 vs x86_64** — Default to arm64 (Graviton) unless native deps or AVX2 workloads pin to x86_64.
- **Concurrency control: unreserved vs reserved vs provisioned** — Reserve concurrency to protect fragile downstreams (RDS, rate-limited APIs); account default is 1,000.
- **Orchestration: Step Functions vs EventBridge vs direct async** — Multi-step workflows with retry/compensation → Step Functions; event fan-out → EventBridge; simple fire-and-forget → async invoke + DLQ.
- **Networking: VPC-attached vs non-VPC** — Skip VPC unless the function needs private-subnet resources; VPC adds ENI management overhead and requires NAT Gateway for internet egress.
- **HTTP front door: API Gateway vs ALB vs Function URL** — Public production APIs → API Gateway + WAF; existing ALB stack → ALB; simple internal/webhook → Function URL with IAM auth.

### 🚫 Never Do

For ❌ wrong / ✅ correct code pairs and detection guidance, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Critical prohibitions**:

- **Hardcoded secrets or plaintext env vars** — CRITICAL: credential leak → account/data compromise. Use Secrets Manager + KMS.
- **Wildcard execution-role permissions in production** — CRITICAL: privilege escalation → full-account blast radius. Scope to exact ARNs.
- **Non-idempotent handler on an at-least-once source** — HIGH: duplicate side effects (double charges, double inserts, double emails).
- **Orchestrating workflows by chaining Lambda invocations in code** — HIGH: cascading failure, no retry visibility, tightly-coupled monolith. Use Step Functions.
- **Running on a deprecated runtime** — HIGH: unpatched CVEs, eventual create/update block.
- **Async invocations with no DLQ or on-failure destination** — HIGH: silent event loss after retries exhaust.
- **SQS visibility timeout less than or equal to function timeout** — MEDIUM: duplicate concurrent processing of the same message.
- **Memory guessing without right-sizing** — MEDIUM: chronic over/under-provisioning and cost waste.
- **Mutable global user/session state in execution environment** — MEDIUM: cross-invocation data leak across tenants.

---

## Integration Patterns

For full integration code with imports and configuration, see [Integration Patterns](./blueprints/integration-patterns.md).

**Key integrations**:

- **Lambda ↔ API Gateway** — Sync HTTP with throttling, WAF, auth, usage plans; arm64 + SnapStart or Provisioned Concurrency for latency SLOs.
- **Lambda ↔ SQS** — Queue-based load leveling; visibility timeout must be ≥ 6× function timeout; enable partial batch response (`ReportBatchItemFailures`).
- **Lambda ↔ DynamoDB Streams** — Stream processing with `ReportBatchItemFailures`; idempotent writes keyed on record sequence number.
- **Lambda ↔ Step Functions** — State machine orchestrates Lambda tasks with built-in retries, catch, and compensation; avoid chaining Lambdas directly.
- **Lambda ↔ EventBridge** — Event fan-out to multiple Lambda targets; each consumer scales independently; use schema registry for contract governance.

**Common issues**:

- **Cold starts on latency-critical sync paths** → Enable SnapStart (supported runtime) or Provisioned Concurrency with Application Auto Scaling.
- **Duplicate message processing** → Verify idempotency key usage; confirm SQS visibility timeout ≥ function timeout.
- **Unexpected throttling** → Check reserved concurrency ceiling; request account-level concurrency limit increase.
- **Silent event loss on async invocations** → Confirm `DestinationConfig.OnFailure` or `DeadLetterConfig.TargetArn` is set.

---

## Verification Loop

Run after any Lambda configuration or architecture change.

### 1. Detect deprecated runtimes

```bash
DEPRECATED="python3.10 python3.11 nodejs16.x java11 java17 ruby3.2 provided.al2 go1.x dotnet6"
aws lambda list-functions \
  --query 'Functions[*].[FunctionName,Runtime]' \
  --output text | awk '{print $2, $1}' | sort
# Expected: no runtime in the DEPRECATED list above
```

### 2. Verify execution role has no wildcards

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query 'Role' --output text
# Then inspect the role:
aws iam get-role-policy --role-name "$ROLE_NAME" --policy-name "$POLICY_NAME"
# Expected: no Action:"*" or Resource:"*" in production statements
```

### 3. Confirm async error handling configured

```bash
aws lambda get-function-event-invoke-config \
  --function-name "$FUNCTION_NAME"
# Expected: DestinationConfig.OnFailure.Destination or DeadLetterConfig.TargetArn is populated
```

### 4. Confirm SQS visibility timeout

```bash
VIS=$(aws sqs get-queue-attributes --queue-url "$QUEUE_URL" \
  --attribute-names VisibilityTimeout \
  --query 'Attributes.VisibilityTimeout' --output text)
TMO=$(aws lambda get-function-configuration --function-name "$FUNCTION_NAME" \
  --query 'Timeout' --output text)
echo "Visibility: $VIS s | Function timeout: $TMO s | 6x timeout: $((TMO * 6)) s"
# Expected: VIS >= TMO * 6
```

### 5. Confirm concurrency settings on DB-backed functions

```bash
aws lambda get-function-concurrency --function-name "$FUNCTION_NAME"
# Expected: ReservedConcurrentExecutions set (not null) for any function with fragile downstream
```

**Troubleshooting**:

- `Throttling` errors → Increase reserved concurrency or request account-level limit increase via Support.
- `DestinationDeliveryFailures` → Verify SQS/SNS resource policy grants Lambda `sqs:SendMessage`.
- `Init Duration` high on CloudWatch REPORT → Enable SnapStart (if Java 11+/Python 3.12+/.NET 8+) or Provisioned Concurrency.
- `Max Memory Used` near configured limit → Increase memory and re-run Power Tuning.

---

## Quick Reference

**Essential CLI commands**:

```bash
# List all functions with runtimes
aws lambda list-functions --query 'Functions[*].[FunctionName,Runtime]' --output table

# Get full function config (role, timeout, memory, VPC, env vars)
aws lambda get-function-configuration --function-name "$FUNCTION_NAME"

# Invoke synchronously for smoke test
aws lambda invoke --function-name "$FUNCTION_NAME" \
  --payload '{"key":"val"}' output.json && cat output.json

# Update runtime to supported version
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" --runtime python3.13

# Emergency throttle (set reserved concurrency to 0)
aws lambda put-function-concurrency \
  --function-name "$FUNCTION_NAME" --reserved-concurrent-executions 0
```

**Critical service limits** (source: [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html), accessed 2026-07-31):

| Resource | Limit | Notes |
|---|---|---|
| Memory | 128 MB – 10,240 MB | 1 MB increments; CPU proportional to memory |
| Timeout | 900 s (15 min) | Hard max; use Step Functions for longer flows |
| Payload (sync) | 6 MB | RequestResponse invocation type |
| Payload (async) | 1 MB | Event invocation type |
| Response streaming | 200 MB | 2 MBps after first 6 MB |
| Package (.zip) | 50 MB zipped / 250 MB unzipped | Layers count toward unzipped limit |
| Container image | 10 GB (ECR) | Uncompressed size |
| Layers | 5 max | Total unzipped size ≤ 250 MB |
| Default concurrency | 1,000 / account | Increasable; reserving reduces shared pool |
| Burst scaling | 1,000 environments / 10 s | Then +500/min |

---

## External Resources

### Official Documentation (continuously updated)

- [Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/) — primary reference (accessed 2026-07-31)
- [Best practices for AWS Lambda functions](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Lambda runtimes — supported and deprecated](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)
- [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)
- [Security in AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/lambda-security.html)
- [AWS Lambda pricing](https://aws.amazon.com/lambda/pricing/)

### Framework Guidance (⚠️ Serverless Applications Lens — dated 2022-07; supporting only)

- [Well-Architected Serverless Applications Lens — Pillars](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/the-pillars-of-the-well-architected-framework.html)
- [Serverless Lens — Design principles](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html)
- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)

### Tooling

- [Powertools for AWS Lambda](https://docs.aws.amazon.com/powertools/) — idempotency, logging, metrics, batch (Python/TypeScript/Java/.NET)
- [AWS Lambda Power Tuning](https://github.com/alexcasalboni/aws-lambda-power-tuning) — memory/cost optimization state machine
- [Serverless Land](https://serverlessland.com/) — official AWS serverless patterns (accessed 2026-07-31)

### Research Source

- [Research file](../../../StoryBeat/docs/research_cloud_AWS_Lambda_Serverless_v2026-07.md) — source-dated 2026-07-31
