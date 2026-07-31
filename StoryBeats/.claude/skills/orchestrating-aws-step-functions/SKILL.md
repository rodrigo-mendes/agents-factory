---
name: orchestrating-aws-step-functions
description: "Designs and implements serverless workflow orchestration with AWS Step Functions (2025 feature set — JSONata, Variables, Distributed Map, Redrive). Use when architecting state machines for microservice coordination, data/ML pipelines, or large-scale parallel processing on AWS."
---

## Function

Specialist in serverless workflow orchestration with AWS Step Functions — Standard/Express workflow design, Distributed Map fan-out, error handling with Retry/Catch/Redrive, and JSONata-based data transforms.

## Version Context

**Technology**: AWS Step Functions
**Target Version**: 2025 feature set (pinned 2026-07-31; review after 2027-07-31)
**Support Status**: GA — continuously updated

**Defining architectural shift**: **JSONata + Variables** (GA 2024-11-22) replaces the legacy `InputPath`/`Parameters`/`ResultPath`/`OutputPath` data-threading model. Pre-2024 JSONPath-only guidance is incomplete for new workflows.

**Key recent capabilities**:
- Variables + JSONata expressions — `Arguments`/`Output`/`Assign` fields (2024-11-22)
- KMS customer-managed-key encryption for workflows/logs/activities (2024-06-25)
- Redrive — restart failed Standard executions from the point of failure (2023-11-15)
- Distributed Map — 10,000-way parallelism over S3-scale data (GA 2022-12-01, extended 2025)
- TestState API — validate a single state without deploying (2023-11-26)
- Enhanced retriers — `MaxDelaySeconds`, `JitterStrategy` (2023-09-07)

**Deprecations**: None — JSONPath is retained. JSONata is additive and mutually exclusive per state.

⚠️ **Version Lock**: Workflow type is **immutable after creation** — "Copy to new" is the only migration path. Do not mix JSONPath fields (`ResultPath`) with JSONata fields (`Output`) in the same state.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 7 mandatory patterns with ASL code examples
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 4 architectural decisions with trade-off matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 6 anti-patterns with ❌ wrong / ✅ correct ASL pairs
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Lambda, S3, CloudWatch Logs, KMS, SQS patterns
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 test cases: canonical, edge, misuse
- **[Verification Loop](#verification-loop)** — AWS CLI commands to validate deployed state machines
- **[Quick Reference](#quick-reference)** — Service limits and essential CLI commands

---

## Blueprints & Guardrails

Domain complexity: **Complex** — 7 mandatory / 4 ask-first / 6 never-do (security-critical, multi-layer).

### ✅ Always Do

For full ASL code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

- **Choose workflow type by idempotency + duration — treat the choice as permanent.** Standard = exactly-once / up to 1 year / per-transition billing. Express = at-least-once async or at-most-once sync / ≤5 min / per-execution billing. Cannot be changed after creation; "Copy to new" is the only migration.
- **Set `TimeoutSeconds` on every Task state.** Without it, Activity/Task states hang indefinitely when a worker is unresponsive. Add `HeartbeatSeconds` (less than task timeout) on all `.waitForTaskToken` Tasks.
- **Retry Lambda transient exceptions explicitly.** Add a retrier covering `Lambda.ServiceException`, `Lambda.AWSLambdaException`, `Lambda.SdkClientException`, `Lambda.ClientExecutionTimeoutException` (`MaxAttempts: 6`, `BackoffRate: 2`). Match `Lambda.Unknown` / `Sandbox.Timedout` in a separate entry. Append `States.ALL` catcher last.
- **Offload payloads >256 KiB to S3 and pass the object ARN between states.** `States.DataLimitExceeded` is a terminal error — not catchable by `States.ALL`. Write the large object to S3; pass `{ "bucket": "...", "key": "..." }`.
- **Enable CloudWatch Logs with the `/aws/vendedlogs/states/` prefix.** Express workflows have no native execution history — CloudWatch Logs is the only audit trail. The `/aws/vendedlogs/` prefix avoids the 5,120-char resource-policy limit and 10-policy-per-region/account cap.
- **Scope the execution IAM role to exact ARNs — no wildcards.** Grant only the actions/resources the Tasks invoke. For Distributed Map, scope `states:StartExecution` and `states:DescribeExecution` to the specific state-machine and execution ARNs.
- **Use Distributed Map or nested child executions to stay under 25,000 events.** Standard executions fail at event 25,000. Distributed Map gives each iteration an isolated child execution history; nested executions spread work across histories.

### ⚠️ Ask First

For full decision matrices, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **Standard vs. Express workflow type** — Ask: "Is every step idempotent AND does the workflow complete in ≤5 min?" If no to either → Standard. Nest Express children inside a Standard parent for high-volume idempotent steps.
- **JSONPath (legacy) vs. JSONata (2024-11-22)** — Ask: "Is this a new workflow needing data transforms (math, date, string)?" If yes → JSONata + Variables; use TestState API to validate expressions. Existing JSONPath workflows: keep as-is unless migrating.
- **Inline Map vs. Distributed Map** — Ask: "Does the dataset exceed 256 KiB, require >40 concurrency, or risk hitting 25,000 events?" If yes to any → Distributed Map (Standard-only). Set `ToleratedFailurePercentage` / `ToleratedFailureCount` before deploying.
- **Service integration pattern** — Ask: "Must the workflow block on a downstream managed job (→ `.sync`) or an external/human callback (→ `.waitForTaskToken`)?" Both are Standard-only; Express supports only Request-Response.

### 🚫 Never Do

For ❌/✅ ASL code pairs, see [Never Do Patterns](./blueprints/never-do-patterns.md).

- **Task state with no `TimeoutSeconds`.** Execution hangs forever. Add `"TimeoutSeconds": 300` minimum; `"HeartbeatSeconds": 60` for `.waitForTaskToken`.
- **Non-idempotent steps (payments, job starts) in an Express workflow.** Async Express is at-least-once — the step may double-execute. Put non-idempotent steps in a Standard parent; nest Express only for idempotent work.
- **Passing >256 KiB payloads directly between states.** Causes terminal `States.DataLimitExceeded`. Write to S3, pass ARN.
- **Lambda Task with no explicit Retry or with only a `States.ALL` retrier.** `States.ALL` does not catch `States.DataLimitExceeded` or `States.Runtime`; transient Lambda 500s fail the run without retrying.
- **Execution role with `Resource: "*"` on `states:*` or `lambda:InvokeFunction`.** Enables privilege escalation across the account. Scope to exact ARNs.
- **Single Standard execution iterating tens of thousands of inline steps.** Hits 25,000-event quota and fails with `ExecutionFailed`. Use Distributed Map or nested executions.

---

## Integration Patterns

For complete code examples, see [Integration Patterns](./blueprints/integration-patterns.md).

- **Step Functions ↔ Lambda** — Task with `arn:aws:states:::lambda:invoke`, explicit Retry block on 4 transient error codes, and `TimeoutSeconds`.
- **Step Functions ↔ S3** — Distributed Map `ItemReader` (CSV/JSON/manifest/Parquet) + `ResultWriter`; large-payload offload via S3 ARN pass-through.
- **Step Functions ↔ CloudWatch Logs** — Log group `/aws/vendedlogs/states/<name>`; log level `ALL` (non-prod) / `ERROR` (prod) to manage cost.
- **Step Functions ↔ KMS** — Customer-managed key for workflow definition + execution data + activity I/O (optional; verify compliance scope before making mandatory).
- **Step Functions ↔ SQS/SNS** — `.waitForTaskToken` Task publishes token to queue/topic; consumer calls `SendTaskSuccess`/`SendTaskFailure`; `HeartbeatSeconds` guards against stuck tasks.

**Common problems**:
- `States.DataLimitExceeded` not caught by `Catch` → not catchable; prevent by offloading to S3 before the state transition
- Express workflow execution history missing → CloudWatch Logs required; verify `/aws/vendedlogs/states/<name>` log group exists
- Execution stuck indefinitely → Task missing `TimeoutSeconds`; add field and redeploy

---

## Verification Loop

Run after deploying or modifying any state machine:

### 1. Verify workflow type
```bash
aws stepfunctions describe-state-machine \
  --state-machine-arn <arn> \
  --query 'type'
# Expected: "STANDARD" or "EXPRESS"
```

### 2. Audit Task states for missing TimeoutSeconds
```bash
aws stepfunctions describe-state-machine \
  --state-machine-arn <arn> \
  --query 'definition' --output text | \
  python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
missing = [k for k,v in d.get('States',{}).items()
           if v.get('Type')=='Task' and 'TimeoutSeconds' not in v]
print('MISSING TimeoutSeconds:', missing or 'none')
"
# Expected: MISSING TimeoutSeconds: none
```

### 3. Verify CloudWatch Logs config
```bash
aws stepfunctions describe-state-machine \
  --state-machine-arn <arn> \
  --query 'loggingConfiguration'
# Expected: level not "OFF"; logGroupArn contains "vendedlogs"
```

### 4. Check for DataLimitExceeded errors
```bash
aws logs filter-log-events \
  --log-group-name /aws/vendedlogs/states/<name> \
  --filter-pattern "DataLimitExceeded"
# Expected: no events
```

**Troubleshooting**:
- `ExecutionTimedOut` → Task `TimeoutSeconds` too low or absent; increase or add it
- `ExecutionFailed` at high event count → Near 25,000-event quota; migrate to Distributed Map
- `States.DataLimitExceeded` → Upstream Task returning >256 KiB; offload to S3

---

## Quick Reference

**Essential CLI commands**:
```bash
# Start a Standard execution
aws stepfunctions start-execution --state-machine-arn <arn> --input '{"key":"value"}'

# Validate a single state (TestState API — no deployment needed)
aws stepfunctions test-state --definition file://state.json --input '{}' --inspection-level TRACE

# Redrive a failed Standard execution from the point of failure
aws stepfunctions redrive-execution --execution-arn <execution-arn>

# Describe a Distributed Map Run
aws stepfunctions describe-map-run --map-run-arn <arn>
```

**Critical limits**:

| Resource | Limit | Scope |
|---|---|---|
| State payload | 256 KiB | Per state transition |
| Execution history events | 25,000 | Per Standard execution |
| Standard max runtime | 1 year | Per execution |
| Express max runtime | 5 min (console: 60 s sync) | Per execution |
| Distributed Map concurrency | 10,000 child executions | Per Map state |
| Inline Map concurrency | 40 iterations | Per Map state |
| CloudWatch Logs resource policy | 5,120 chars / 10 policies | Per region/account |

---

## Blueprints Directory Structure

```
orchestrating-aws-step-functions/
├── SKILL.md                           <- This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md          <- 7 mandatory patterns with ASL code
    ├── ask-first-decisions.md         <- 4 decision matrices with trade-off tables
    ├── never-do-patterns.md           <- 6 anti-patterns with wrong/correct ASL pairs
    ├── integration-patterns.md        <- Cross-service integration examples
    └── evaluation-scenarios.md        <- 3 test scenarios: canonical, edge, misuse
```

---

## External Resources

### Official AWS Step Functions Documentation (all accessed 2026-07-31)
- [What is Step Functions?](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html)
- [Choosing workflow type](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html)
- [Best practices](https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html)
- [Error handling (Retry/Catch)](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html)
- [Distributed Map state](https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html)
- [Transforming data with JSONata](https://docs.aws.amazon.com/step-functions/latest/dg/transforming-data.html)
- [Workflow Variables](https://docs.aws.amazon.com/step-functions/latest/dg/workflow-variables.html)
- [Redrive executions](https://docs.aws.amazon.com/step-functions/latest/dg/redrive-executions.html)
- [Step Functions API Reference](https://docs.aws.amazon.com/step-functions/latest/apireference)
- [Pricing](https://aws.amazon.com/step-functions/pricing/)
- [Recent feature launches](https://docs.aws.amazon.com/step-functions/latest/dg/recent-launches.html)

### Dated Announcements
- [Variables + JSONata (2024-11-22)](https://aws.amazon.com/blogs/compute/simplifying-developer-experience-with-variables-and-jsonata-in-aws-step-functions/)
- [KMS customer-managed keys (2024-06-25)](https://aws.amazon.com/about-aws/whats-new/2024/07/aws-step-functions-customer-managed-keys/)
- [HTTPS endpoints + TestState API (2023-11-26)](https://aws.amazon.com/about-aws/whats-new/2023/11/aws-step-functions-https-endpoints-teststate-api/)
- [Enhanced error handling (2023-09-07)](https://aws.amazon.com/about-aws/whats-new/2023/09/aws-step-functions-enhanced-error-handling/)
- [Distributed Map GA (2022-12-01)](https://aws.amazon.com/about-aws/whats-new/2022/12/aws-step-functions-large-scale-parallel-workflows-data-processing-serverless-applications/)
- [Distributed Map data sources + observability (2025-09-18)](https://aws.amazon.com/about-aws/whats-new/2025/09/aws-step-functions-data-source-options-observability-distributed-map/)
- [Metrics dashboard (2025-10-30)](https://aws.amazon.com/about-aws/whats-new/2025/10/aws-step-functions-metrics-dashboard/)

### Research Input
- Research file: `StoryBeats/docs/research_cloud_AWS_Serverless-Orchestration-StepFunctions_2025.md` — source research (2026-07-31); currency threshold 2027-07-31
