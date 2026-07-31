# Ask First Decisions — AWS Step Functions

4 architectural decisions requiring confirmation before implementation. Each is a **permanent or hard-to-reverse** choice.

---

## Decision A — Standard vs. Express workflow type

**Source**: [Choosing workflow type](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html) (accessed 2026-07-31)

**Trigger question**: "Is every step idempotent AND does the workflow complete in ≤5 minutes?"

| Option | Idempotency guarantee | Max runtime | History | `.sync` / `.waitForTaskToken` | Distributed Map | Billing |
|---|---|---|---|---|---|---|
| **Standard** | Exactly-once | 1 year | 90-day native + CloudWatch | Supported | Supported | Per state transition |
| **Express async** | At-least-once | 5 min | CloudWatch Logs only | Not supported | Not supported | Per execution + duration + memory |
| **Express sync** (`StartSyncExecution`) | At-most-once | 5 min (console: 60 s) | CloudWatch Logs only | Not supported | Not supported | Per execution + duration + memory |

**Decision rule**:
- Any step non-idempotent (payment, EMR start, provisioning) → **Standard**
- Workflow may exceed 5 minutes → **Standard**
- Need audit history, `.sync`, or Distributed Map → **Standard**
- All steps idempotent, ≤5 min, high frequency → **Express async**
- Synchronous API composition returning result to caller → **Express sync**
- Mixed (non-idempotent steps + high-volume idempotent steps) → **Standard parent + nested Express children**

Lock-in note: Type is **immutable after creation**. "Copy to new" in the console is the only migration path.

---

## Decision B — Query language: JSONPath (legacy) vs. JSONata (2024-11-22)

**Source**: [Transforming data with JSONata](https://docs.aws.amazon.com/step-functions/latest/dg/transforming-data.html) · [Variables](https://docs.aws.amazon.com/step-functions/latest/dg/workflow-variables.html) (accessed 2026-07-31)

**Trigger question**: "Is this a new workflow that needs data transforms (math, date, string operations)?"

| Option | Fields | Transform capability | Cross-state variables | When to choose |
|---|---|---|---|---|
| **JSONPath** | `InputPath`, `Parameters`, `ResultPath`, `OutputPath` | Reference + extract only; math/date needs Lambda glue | No native variables | Maintaining existing workflows; teams standardized on JSONPath |
| **JSONata** | `Arguments`, `Output`, `Assign` | Full expressions: math, date, string, array ops | `Variables` (`$$.<name>`) persist across states | New workflows; eliminate pass-through states and Lambda glue |

Fields are **mutually exclusive per state** — do not mix `ResultPath` (JSONPath) with `Output` (JSONata) in the same state definition.

JSONata example — compute and carry a value across states without a Lambda:
```json
{
  "QueryLanguage": "JSONata",
  "States": {
    "ComputeDiscount": {
      "Type": "Pass",
      "Assign": {
        "discountRate": "{% $price > 100 ? 0.15 : 0.05 %}"
      },
      "Next": "ApplyDiscount"
    },
    "ApplyDiscount": {
      "Type": "Pass",
      "Output": {
        "finalPrice": "{% $price * (1 - $discountRate) %}"
      },
      "End": true
    }
  }
}
```

Validate expressions with TestState API before deploying:
```bash
aws stepfunctions test-state \
  --definition file://state.json \
  --input '{"price": 120}' \
  --inspection-level TRACE
```

Cost note: JSONata can reduce state transitions (fewer Pass/glue states) → lower cost on Standard.

---

## Decision C — Inline Map vs. Distributed Map

**Source**: [Distributed Map state](https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html) (accessed 2026-07-31)

**Trigger questions**: "Does the dataset exceed 256 KiB? Require >40 concurrency? Risk hitting 25,000 events?"

| Option | Max concurrency | Input source | History | Workflow type | When to choose |
|---|---|---|---|---|---|
| **Inline Map** (default) | 40 iterations | In-state payload (≤256 KiB) | Shared execution history (counts toward 25,000) | Standard or Express | Small in-memory arrays, ≤40 items |
| **Distributed Map** (`Mode: DISTRIBUTED`) | 10,000 child executions | S3 objects, CSV, JSON, manifest, Parquet/Athena (2025-09-18) | Isolated child execution per iteration | Standard-only | Dataset >256 KiB, >40 concurrency, or history at risk |

Distributed Map additional parameters to set before deploying:
- `MaxConcurrency` — default 0 = 10,000; tune to downstream service limits
- `ItemBatcher.MaxItemsPerBatch` — amortizes per-child-execution overhead
- `ToleratedFailurePercentage` / `ToleratedFailureCount` — partial-failure budget
- `ExecutionType: EXPRESS` for child workflows when item processing is idempotent (cost saving)

Cost note: Distributed Map bills each child execution separately. Use `ItemBatcher` to reduce the number of child executions for large datasets.

---

## Decision D — Service integration pattern

**Source**: [Connecting to resources](https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html) (accessed 2026-07-31)

**Trigger question**: "Must the workflow block on a downstream managed job OR wait for an external/human callback?"

| Pattern | Resource suffix | Availability | Blocks on | When to choose |
|---|---|---|---|---|
| **Request-Response** | (none / default) | Standard + Express | Nothing — continues immediately | Fire-and-continue; Express workflows |
| **Run-a-Job** | `.sync:2` | Standard only | AWS managed job completion (Glue, ECS, EMR, Batch, SageMaker, etc.) | Long-running managed-job orchestration; avoids polling Lambda |
| **Wait-for-Callback** | `.waitForTaskToken` | Standard only | Explicit `SendTaskSuccess` / `SendTaskFailure` call (up to 1 year) | Human-in-the-loop, external approval, async 3rd-party systems |

`.waitForTaskToken` example with SQS and heartbeat:
```json
{
  "WaitForApproval": {
    "Type": "Task",
    "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
    "Parameters": {
      "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/ApprovalQueue",
      "MessageBody": {
        "taskToken.$": "$$.Task.Token",
        "requestId.$": "$.requestId",
        "approvalUrl.$": "States.Format('https://approvals.example.com/approve?token={}', $$.Task.Token)"
      }
    },
    "TimeoutSeconds": 86400,
    "HeartbeatSeconds": 3600,
    "Next": "ProcessApproval"
  }
}
```

Cost note: `.sync` and `.waitForTaskToken` keep a Standard execution alive — billed per transition, not per second. This is cheaper than busy-polling with a Lambda loop for long waits.
