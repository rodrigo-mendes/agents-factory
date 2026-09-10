---
name: orchestrating-aws-step-functions
description: "Orchestrates serverless workflows with AWS Step Functions 2026. Use when designing, implementing, or reviewing Step Functions state machines — covering workflow type selection, error handling, IAM least-privilege configuration, observability setup, and parallel processing patterns."
---

## Function

Specialist in AWS Step Functions serverless orchestration patterns — workflow design, Amazon States Language (ASL), service integrations, error handling, and operational best practices for AWS 2026.

## Version Context

**Technology**: AWS Step Functions
**Target Edition**: AWS Step Functions 2026
**Research Date**: 2026-08-31
**Currency Threshold**: 2027-08-31
**Support Status**: Generally Available

**Key additions (2024–2026)**:
- **JSONata GA (2024)** — replaces 5-field JSONPath I/O pipeline with 2-field model (`Arguments`/`Output`); AWS recommends JSONata for all new state machines
- **Workflow Variables GA (2024)** — `Assign` field persists values across states; Distributed Map children cannot access outer-scope variables
- **Distributed Map enhancements (Sep 2025, GA)** — Athena manifest, Parquet, and S3ListObjectsV2 as native `ItemReader` sources; new CloudWatch observability metrics
- **TestState API with mocking (Nov 2025, GA)** — mock service integrations without IAM roles; three inspection levels (INFO/DEBUG/TRACE); console UI does NOT support mocking (use CLI/SDK)

**Workflow type is immutable** — Standard vs Express cannot be changed after creation. Make the correct choice at design time.

⚠️ **CRITICAL — Agent Warning**: Workflow type selection is irreversible. Verify Standard vs Express requirements before defining any state machine resource.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 operational rules
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 test scenarios (canonical, edge, misuse)
- **[Integration Patterns](#integration-patterns)** — Step Functions ↔ AWS service integrations
- **[Verification Loop](#verification-loop)** — Pre-deployment validation commands
- **[Quick Reference](#quick-reference)** — Critical limits and key commands
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

**1. Retry with JitterStrategy FULL on every Task, Parallel, and Map state**
Every Task/Parallel/Map state must include `Retry` with `IntervalSeconds: 2`, `MaxAttempts: 6`, `BackoffRate: 2`, `MaxDelaySeconds`, and `JitterStrategy: FULL` plus a `Catch` block routing to a compensating state. Lambda transient errors to always retry: `Lambda.ServiceException`, `Lambda.AWSLambdaException`, `Lambda.SdkClientException`, `Lambda.ClientExecutionTimeoutException`. Omitting Retry causes any transient AWS error to permanently fail the execution.

**2. TimeoutSeconds on every Task state; HeartbeatSeconds on every .waitForTaskToken Task**
Set `TimeoutSeconds` appropriate to expected duration plus safety margin (e.g., Lambda with 15-min max: `TimeoutSeconds: 960`). `.waitForTaskToken` tasks must also declare `HeartbeatSeconds` less than `TimeoutSeconds`. Without TimeoutSeconds, a stuck Standard Workflow waits up to 1 year, consuming quota and accruing per-transition billing.

**3. CloudWatch Logs at Level ALL or ERROR + X-Ray tracing on every state machine**
Set `LoggingConfiguration.Level: ALL` (or `ERROR` for production cost savings). Use log group prefix `/aws/vendedlogs/states/{name}` to avoid the 5,120-char resource policy limit. Set `TracingConfiguration.Enabled: true`. Express Workflows have zero observable history without CloudWatch Logs — failures are completely undiagnosable.

**4. JSONata query language for all new state machines**
Set `QueryLanguage: JSONata` at state machine level. Use `Arguments` (replaces InputPath+Parameters) and `Output` (replaces ResultSelector+ResultPath+OutputPath). Use `$states.context.Task.Token` for task tokens in JSONata. `Assign` and `Output` are evaluated in parallel — values assigned in `Assign` are NOT available in the same state's `Output` expression.

**5. Express Workflows for high-volume short-duration idempotent flows**
Use Express when all three apply: duration < 5 min, rate > 100/sec, idempotent operations. Use `StartSyncExecution` for API Gateway-fronted flows needing inline response. Standard caps at 2,000 exec/sec and 4,000 transitions/sec — high-frequency Standard Workflows throttle and cost 5–100x more than Express.

**6. Direct AWS SDK integrations instead of Lambda-as-glue**
Use `arn:aws:states:::aws-sdk:{service}:{action}` for any step calling a single AWS API (DynamoDB PutItem, SQS SendMessage, SNS Publish, S3 PutObject). Reserve Lambda for business logic, complex transforms, or multi-service fan-out. Lambda-as-glue adds invocation cost, cold-start latency (~3s), and lifecycle overhead with no business justification.

**7. Least-privilege IAM execution roles with confused-deputy protection**
Use Workflow Studio to auto-generate a least-privilege baseline. Scope S3 permissions for Distributed Map to specific bucket/prefix. Add trust policy condition: `ArnLike` on `aws:SourceArn` + `StringEquals` on `aws:SourceAccount`. Use `TaskCredentials` for cross-account role assumption. Never use `"Action": "states:*"` on `"Resource": "*"`.

### ⚠️ Ask First

**Standard vs Express Workflow** — Ask: "What is the expected execution rate per second, the typical duration, and whether the workflow requires exactly-once semantics, .waitForTaskToken, Distributed Map, or human-in-the-loop steps?" Workflow type is immutable after creation. See tradeoff table in research file.

**Orchestration vs Choreography** — Ask: "Does this process have more than 3 steps, require rollback on failure, or need a human approval gate?" If yes, orchestration (Step Functions) is appropriate. If the flow is a simple pub/sub fan-out with independent services, EventBridge + SQS/SNS choreography may be a better fit.

**Inline Map vs Distributed Map** — Ask: "How many items are in the dataset, what is the expected total event count, and does the workflow run on Express?" Use Inline Map for <40 items or Express workflows. Use Distributed Map for datasets exceeding 256 KiB, >40 concurrency, or when total events risk the 25,000 limit. Distributed Map is Standard-only.

**Direct SDK Integration vs Lambda Integration** — Ask: "Does this step perform any logic beyond calling a single AWS API?" If no, use direct SDK integration. If yes (business logic, conditional branching, multi-API call), use Lambda.

**JSONata vs JSONPath (migration context)** — Ask: "Is this a new state machine or migration of an existing one?" Use JSONata for net-new. For existing JSONPath state machines, use per-state `QueryLanguage` override for incremental migration to avoid breaking changes.

**Callback (.waitForTaskToken) vs Polling (.sync)** — Ask: "Does this step wait for an external system or human to respond, and will that system be able to call the AWS Step Functions API?" Use `.waitForTaskToken` for human approvals and third-party async integrations (zero polling cost, waits up to 1 year). Use `.sync` for AWS-managed jobs (Batch, ECS, Glue, SageMaker) that natively support it.

### 🚫 Never Do

| Anti-Pattern | Risk | Correct Alternative |
|---|---|---|
| Task state with no `Retry` or `Catch` block | CRITICAL — any transient error permanently fails execution | Add `Retry` with `JitterStrategy: FULL` + `Catch` routing to compensation state |
| Task state with no `TimeoutSeconds` | CRITICAL — Standard Workflow blocks up to 1 year; quota exhaustion + cost overrun | Declare `TimeoutSeconds` on every Task; add `HeartbeatSeconds` for `.waitForTaskToken` tasks |
| Standard Workflow for >2,000 exec/sec idempotent flows | HIGH — throttles at limit; 5–100x cost vs Express | Switch to Express Workflow (Async or Sync); use Standard only for exactly-once or human-in-the-loop |
| Lambda-as-glue (handler is one `sdk.call()`) | HIGH — invocation cost + cold-start + lifecycle overhead | Replace with direct SDK integration `arn:aws:states:::aws-sdk:{service}:{action}` |
| Inline Map over >2,500 items without estimating event count | CRITICAL — execution fails unconditionally at 25,000 events; all partial results lost | Switch to Distributed Map (DISTRIBUTED mode) with `ResultWriter` to S3 |
| `"Action": "states:*"` on `"Resource": "*"` in execution role | CRITICAL — blast radius covers all Step Functions in account; compliance violation | Auto-generate least-privilege policy via Workflow Studio; scope to specific ARNs |
| Express Workflow with no CloudWatch Logs | HIGH — zero observability; failures invisible in production | Set `LoggingConfiguration.Level: ALL`; use `/aws/vendedlogs/states/{name}` prefix |
| Wait-state polling loop instead of `.waitForTaskToken` | HIGH — consumes quota + event history; accelerates toward 25,000 limit | Append `.waitForTaskToken` to Task Resource ARN; declare `HeartbeatSeconds` |

---

## Integration Patterns

**Step Functions → DynamoDB (direct SDK)**
Use `arn:aws:states:::aws-sdk:dynamodb:putItem` with PascalCase parameters. Idempotent writes via `ConditionExpression: "attribute_not_exists(PK)"`. No Lambda intermediary.

**Step Functions → HTTP Task (third-party APIs)**
Use `arn:aws:states:::http:invoke`. Credentials stored via EventBridge Connection (never in ASL). Hard 60-second timeout — for longer third-party calls use `.waitForTaskToken` + webhook callback. Does not support mTLS. Cannot call AWS service APIs (use SDK integrations for those).

**Step Functions → SQS/SNS (.waitForTaskToken)**
Append `.waitForTaskToken` to resource ARN. Pass token via `"TaskToken": "{% $states.context.Task.Token %}"` (JSONata) or `"TaskToken.$": "$$.Task.Token"` (JSONPath). External system calls `SendTaskSuccess(token, output)`. Declare `HeartbeatSeconds` to prevent stuck executions when external system fails silently.

**Step Functions → Distributed Map (S3 fan-out)**
`ItemReader` reads S3 datasets (JSON, CSV, Parquet, Athena manifest, S3ListObjectsV2). Each iteration runs as independent child execution with its own 25,000-event budget. Set `ResultWriter` to S3 to avoid 256 KiB output limit. Hard quota: 10,000 concurrent child executions; 1,000 open Map Runs per account.

**Step Functions → API Gateway (synchronous backend)**
API Gateway HTTP API → `StartSyncExecution` (Synchronous Express). Returns inline result within request-response cycle. API Gateway integration timeout: **29 seconds** — Express can run up to 5 min, but the API caller sees 29s. DynamoDB operations must be idempotent (at-most-once Express semantics).

**Common problems**:
- `"States.Runtime"` in ErrorEquals → remove it; States.Runtime errors are never retriable
- Distributed Map cannot access outer-scope workflow variables → pass required data via `ItemReader`/`ItemBatcher` input
- New task token generated per retry in `.waitForTaskToken` → external system must use latest token, not cached one

---

## Verification Loop

Run after each state machine definition authoring or update.

### 1. Validate ASL Definition Syntax
```bash
aws stepfunctions validate-state-machine-definition \
  --definition file://state-machine.json
# Expected: {"result":"OK"}
# Exit code: 0
```

### 2. Lint for Missing Retry/Timeout (bash)
```bash
# Count Task states missing TimeoutSeconds
python3 -c "
import json, sys
sm = json.load(open('state-machine.json'))
states = sm.get('States', {})
missing = [n for n,s in states.items() if s.get('Type')=='Task' and 'TimeoutSeconds' not in s]
print('Missing TimeoutSeconds:', missing) if missing else print('OK: all Task states have TimeoutSeconds')
"
```

### 3. Check Logging and Tracing
```bash
aws stepfunctions describe-state-machine \
  --state-machine-arn <ARN> \
  --query '{logging:loggingConfiguration.level,tracing:tracingConfiguration.enabled}'
# Expected: {"logging":"ALL","tracing":true}
```

### 4. Verify IAM Role for No Wildcard Resources
```bash
aws iam get-role-policy --role-name <ROLE> --policy-name <POLICY> \
  | python3 -c "import json,sys; d=json.load(sys.stdin); stmts=d['PolicyDocument']['Statement']; print([s for s in stmts if s.get('Resource')=='*'])"
# Expected: [] (empty — no wildcard resource)
```

### 5. TestState with Mock (CI/CD gate — CLI only, not console)
```bash
aws stepfunctions test-state \
  --definition file://state.json \
  --role-arn <ROLE_ARN> \
  --input '{"orderId":"test-001"}' \
  --inspection-level TRACE \
  --reveal-secrets false
# Expected: {"status":"SUCCEEDED","inspectionData":{...}}
```

**Troubleshooting**:
- `HIDDEN_DUE_TO_SECURITY_REASONS` in CloudTrail events for definition → expected behavior
- Express execution missing from console → check CloudWatch Logs (`/aws/vendedlogs/states/{name}`)
- `ExecutionThrottled` > 0 on Standard Workflow → evaluate Express migration for high-rate paths

---

## Quick Reference

**Critical limits**:

| Resource | Limit | Scope |
|---|---|---|
| Standard Workflow execution history | 25,000 events | Per execution — fails unconditionally at limit |
| Standard Workflow execution rate | 2,000/sec | Per account/region — throttled beyond |
| Express Workflow execution rate | 100,000/sec | Per account/region |
| Express Workflow max duration | 5 minutes | Hard cap |
| Standard Workflow max duration | 1 year | Execution wait ceiling |
| Inline Map concurrency | 40 iterations | Hard cap |
| Distributed Map concurrency | 10,000 child executions | Hard quota |
| State input/output payload | 256 KiB | Per state — use S3 for larger payloads |
| Workflow variable max size | 256 KiB per variable, 10 MiB total | Per execution |
| HTTP Task timeout | 60 seconds | Hard — use `.waitForTaskToken` for longer calls |
| JSONata expression timeout | 1 second | Per expression — offload heavy computation to Lambda |

**Key IAM permissions for execution role (CloudWatch Logs)**:
`logs:CreateLogDelivery`, `logs:GetLogDelivery`, `logs:UpdateLogDelivery`, `logs:DeleteLogDelivery`, `logs:ListLogDeliveries`, `logs:PutLogEvents`, `logs:PutResourcePolicy`, `logs:DescribeResourcePolicies`, `logs:DescribeLogGroups` + `xray:PutTraceSegments`, `xray:PutTelemetryRecords`, `xray:GetSamplingRules`, `xray:GetSamplingTargets`

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/orchestrating-aws-step-functions/
├── SKILL.md                              <- This file (summary + guardrails)
└── blueprints/
    └── evaluation-scenarios.md           <- 3 test scenarios (canonical, edge, misuse)
```

---

## External Resources

### Official Documentation
- [AWS Step Functions Developer Guide](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html) — Primary reference (2026-08-31)
- [Standard vs Express Workflows](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-standard-vs-express.html) — Immutable type selection guide (2026-08-31)
- [AWS Step Functions Best Practices](https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html) — Official guardrails source (2026-08-31)
- [Amazon States Language Reference](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-states.html) — All state types and fields (2026-08-31)
- [Pricing](https://aws.amazon.com/step-functions/pricing/) — Standard vs Express cost models (2026-08-31)

### Security & Integrations
- [IAM Execution Roles](https://docs.aws.amazon.com/step-functions/latest/dg/manage-state-machine-permissions.html) — Least-privilege and confused-deputy patterns (2026-08-31)
- [Supported SDK Integrations (220+ services)](https://docs.aws.amazon.com/step-functions/latest/dg/supported-services-awssdk.html) — Direct SDK integration reference (2026-08-31)
- [CloudWatch Logs Integration](https://docs.aws.amazon.com/step-functions/latest/dg/cw-logs.html) — Logging configuration (2026-08-31)
- [Error Handling](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html) — Retry and Catch reference (2026-08-31)
- [Distributed Map](https://docs.aws.amazon.com/step-functions/latest/dg/use-dist-map-orchestrate-large-scale-parallel-workloads.html) — Sep 2025 enhancements (2026-08-31)
- [JSONata Transformations](https://docs.aws.amazon.com/step-functions/latest/dg/transforming-data.html) — Arguments/Output/Assign fields (2026-08-31)
- [TestState API with Mocking](https://docs.aws.amazon.com/step-functions/latest/dg/test-state-isolation.html) — Nov 2025 enhancement (2026-08-31)
- [Redrive Executions](https://docs.aws.amazon.com/step-functions/latest/dg/redrive-executions.html) — Point-of-failure restart (2026-08-31)
- [Versions and Aliases](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-state-machine-alias.html) — Canary deployment guide (2026-08-31)
