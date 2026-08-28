---
Full_Name: "AWS Step Functions — Serverless Workflow Orchestration"
Cloud_Provider: "AWS"
Architecture_Domain: "Serverless Orchestration (Step Functions)"
Target_Edition: "AWS Step Functions — 2025 feature set (Amazon States Language with JSONata + Variables, GA 2024-11-22)"
Architecture_Context: "General-purpose serverless workflow orchestration — microservice coordination, data/ML pipelines, and large-scale parallel processing (assumed; no specific ARCHITECTURE_CONTEXT supplied by requester — see Assumptions)"
Official_Source_URL: "https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-07-31"
Currency_Threshold: "2027-07-31 (review after this date — Step Functions ships features frequently; re-verify launch table)"
---

# AWS Step Functions — Serverless Orchestration Research

> **Version note.** Step Functions has no numbered "edition." This research pins to the **current
> service state as of 2026-07-31**, whose defining architectural inflection is the **Amazon States
> Language (ASL) query-language mode**: legacy **JSONPath** vs. the newer **JSONata** mode plus
> **Variables** (both GA **2024-11-22**). Treat pre-2024 guidance that assumes JSONPath is the only
> data model as *incomplete*, not wrong. All facts below cite official AWS documentation with an
> access date of **2026-07-31**.

## Assumptions & Scope (Ask-First items surfaced, not blocked)

The invocation supplied a service (`aws step-functions`) but **no `ARCHITECTURE_CONTEXT`, compliance
scope, or cost/billing constraints**. Per this skill's Ask-First guardrails these would normally be
confirmed. Because the request was a direct "research and save," I proceeded with a **general-purpose
serverless-orchestration context** and explicitly flagged the following as *unverified against your
environment* — confirm before turning this into architecture decisions:

- **Compliance-specific constraints** (SOC2/HIPAA/PCI-DSS/GDPR): not applied. KMS customer-managed-key
  encryption is documented below as an *option*, not a mandate tied to your certification scope.
- **Cost prescriptions** tied to billing agreements: only general cost-model guidance is included
  (Standard = per state transition; Express = per execution + duration + memory).
- **Workflow-type default**: no assumption made about whether your workloads are long-running
  (Standard) or high-volume/short (Express) — this is the primary Ask-First decision below.

---

## Executive Summary

**AWS Step Functions** is AWS's serverless orchestration service. You define **state machines**
(called *workflows*) in the **Amazon States Language (ASL)** — a JSON-based DSL — where each step is a
*state* (Task, Choice, Parallel, Map, Wait, Pass, Succeed, Fail). Step Functions manages state,
checkpointing, retries, error handling, and parallelism so application code does not have to. It
integrates with **200+ AWS services** via SDK integrations and a curated set of **optimized
integrations**, using three service-integration patterns: **Request-Response** (default),
**Run-a-Job `.sync`**, and **Wait-for-Callback `.waitForTaskToken`**
([What is Step Functions?](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html),
accessed 2026-07-31).

The single most important architectural decision is **workflow type**, chosen at creation and
**immutable thereafter**: **Standard** (exactly-once, up to **1 year**, priced per state transition,
full 90-day execution history, supports `.sync`/`.waitForTaskToken`, Distributed Map, Activities) vs.
**Express** (at-least-once for async / at-most-once for sync, up to **5 minutes**, priced per
execution + duration + memory, history only via CloudWatch Logs, Request-Response only)
([Choosing workflow type](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html),
accessed 2026-07-31).

What changed most recently (see the full launch table): **Variables and JSONata** transformations
(2024-11-22) collapsed the historically painful `InputPath`/`Parameters`/`ResultPath`/`OutputPath`
data-threading model; **KMS customer-managed-key encryption** for workflows/logs/activities
(2024-06-25); **TestState API and HTTPS endpoints/HTTP Task** (2023-11-26); **Redrive** to restart
failed executions from the point of failure (2023-11-15); **enhanced error handling** —
`MaxDelaySeconds` + `JitterStrategy` on retriers (2023-09-07); and **Distributed Map** for
10,000-way parallelism over S3-scale datasets (GA 2022-12-01, continuously extended through 2025)
([Recent feature launches](https://docs.aws.amazon.com/step-functions/latest/dg/recent-launches.html),
accessed 2026-07-31). The three most critical guardrails for a general serverless context: **(1) pick
the right workflow type for idempotency semantics**, **(2) set explicit `TimeoutSeconds` on every
Task to avoid stuck executions**, and **(3) never pass >256 KiB payloads between states — use S3 ARNs**.

---

## Cloud Architecture Glossary

```
Term: State machine (Workflow)
Definition: A series of event-driven steps defined in Amazon States Language; the deployable Step Functions resource.
Provider Docs Section: welcome.html "What is Step Functions?"
Architect Usage: The unit of deployment, versioning (aliases), IAM role scoping, and logging config.
Common Confusion: Confused with a single "execution" (a running instance) — one state machine has many executions.
```
```
Term: State
Definition: A single step in a workflow. Types: Task, Choice, Parallel, Map, Wait, Pass, Succeed, Fail.
Provider Docs Section: workflow-states.md
Architect Usage: Only Task/Parallel/Map states can hold Retry/Catch; Pass and Wait cannot fail.
Common Confusion: "State" (a step) vs. "execution state" (the persisted data between transitions).
```
```
Term: Amazon States Language (ASL)
Definition: The JSON-based DSL used to define both Standard and Express state machines.
Provider Docs Section: concepts-amazon-states-language.md
Architect Usage: Same language for both workflow types; workflow type is a deploy-time property, not an ASL keyword.
Common Confusion: Assuming ASL differs by workflow type — it does not; the runtime semantics differ.
```
```
Term: Query language mode (JSONPath vs JSONata)
Definition: The data-transformation model of a state machine. JSONPath (legacy, InputPath/Parameters/ResultPath/OutputPath) or JSONata (Arguments/Output/Assign, GA 2024-11-22).
Provider Docs Section: transforming-data.md; workflow-variables.md
Architect Usage: Choose JSONata for new workflows needing math/date/string transforms and Variables; it reduces state count and custom Lambda glue.
Common Confusion: Mixing JSONPath fields (ResultPath) and JSONata fields (Output) in the same state — they are mutually exclusive per QueryLanguage.
```
```
Term: Execution
Definition: A running instance of a state machine performing tasks.
Provider Docs Section: welcome.html
Architect Usage: Billing, history retention, and idempotency guarantees are all per-execution.
Common Confusion: Standard executions are auditable for 90 days; Express executions are NOT captured by Step Functions (CloudWatch Logs only).
```
```
Term: Service integration pattern
Definition: How a Task calls another service — Request-Response (default), Run-a-Job (.sync), Wait-for-Callback (.waitForTaskToken).
Provider Docs Section: connect-to-resource.md
Architect Usage: .sync waits for a job (e.g., Glue/ECS/EMR) to finish; .waitForTaskToken pauses for external/human callback.
Common Confusion: Express workflows support ONLY Request-Response — no .sync / .waitForTaskToken.
```
```
Term: Task Token (.waitForTaskToken)
Definition: An opaque token injected via $$.Task.Token that pauses a Task until SendTaskSuccess/SendTaskFailure is called.
Provider Docs Section: connect-to-resource.md#connect-wait-token
Architect Usage: The canonical "human-in-the-loop" / async callback pattern (up to 1 year with Standard).
Common Confusion: Confused with .sync — .sync waits on an AWS job's completion; .waitForTaskToken waits on an explicit external callback.
```
```
Term: Distributed Map state
Definition: A Map state in DISTRIBUTED processing mode that runs each iteration as a separate child workflow execution, up to 10,000 in parallel.
Provider Docs Section: state-map-distributed.md
Architect Usage: Use for datasets >256 KiB, histories that would exceed 25,000 events, or >40 concurrent iterations.
Common Confusion: Inline Map (max 40 concurrency, shared history) vs Distributed Map (10,000 concurrency, isolated child histories). Distributed Map is Standard-only.
```
```
Term: Map Run
Definition: The resource (with its own ARN) representing the set of child workflow executions a Distributed Map starts, plus runtime settings.
Provider Docs Section: state-map-distributed.md
Architect Usage: Inspect via DescribeMapRun API / Map Run Details console page; child metrics carry a labelled state-machine ARN.
Common Confusion: A Map Run is not an execution — it is a control resource over many child executions.
```
```
Term: Activity
Definition: A worker that exists OUTSIDE Step Functions, polling GetActivityTask for work and returning results via SendTaskSuccess.
Provider Docs Section: concepts-activities.md
Architect Usage: For work on-prem, on EC2/containers, or any non-integrated compute; Standard-only.
Common Confusion: Activities require poller design (≥100 open polls/ARN recommended); not supported in Express.
```
```
Term: Redrive
Definition: Restarting a failed Standard execution from the point of failure, reusing state up to the failed state (GA 2023-11-15).
Provider Docs Section: redrive-executions.md
Architect Usage: Recovery without re-running already-succeeded, possibly non-idempotent, upstream steps.
Common Confusion: Retry attempt counters reset to 0 on redrive; redrive is distinct from starting a fresh execution.
```
```
Term: Standard vs Express workflow
Definition: The immutable execution model of a state machine. Standard = exactly-once/1-year/per-transition billing; Express = at-least-once(async)/at-most-once(sync)/5-min/per-execution billing.
Provider Docs Section: choosing-workflow-type.md
Architect Usage: Drives idempotency requirements, cost model, history/audit, and available integration patterns.
Common Confusion: Type cannot be changed after creation — "Copy to new" is the only migration path.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**1. Choose workflow type by idempotency + duration, and treat the choice as permanent**
- Pillar Alignment: Reliability, Cost Optimization (AWS Well-Architected)
- Why: "The workflow type can **not** be updated after you create a state machine." Standard is
  *exactly-once* (safe for non-idempotent actions like payments, starting EMR clusters); Express is
  *at-least-once* async / *at-most-once* sync (safe only for idempotent actions like a DynamoDB PUT).
- AWS Services: AWS Step Functions (Standard | Express)
- Architecture Decision: Long-running/auditable/non-idempotent → **Standard**. High-volume, ≤5 min,
  idempotent → **Express**. Nest Express children inside a Standard parent to combine both.
- Verification: `aws stepfunctions describe-state-machine --state-machine-arn <arn> --query type`
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html (accessed 2026-07-31)

**2. Set an explicit `TimeoutSeconds` on every Task (and `HeartbeatSeconds` for callbacks)**
- Pillar Alignment: Reliability
- Why: "Without an explicit timeout, Step Functions often relies solely on a response from an activity
  worker… an execution is stuck waiting for a response that will never come." For `.waitForTaskToken`,
  add `HeartbeatSeconds` (< task timeout) so a heartbeat failure is distinguishable from slowness.
- AWS Services: Step Functions Task state
- Architecture Decision: e.g. `"TimeoutSeconds": 300` on Task/Activity states; `HeartbeatSeconds` on
  `.waitForTaskToken` Tasks. Also settable at the state-machine level via top-level `TimeoutSeconds`.
- Verification: Grep the ASL definition for Task states lacking `TimeoutSeconds`.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#sfn-stuck-execution (accessed 2026-07-31)

**3. Handle transient Lambda service exceptions with an explicit Retry**
- Pillar Alignment: Reliability
- Why: "AWS Lambda can occasionally experience transient service errors… As a best practice,
  proactively handle these exceptions." Unhandled Lambda failures also surface as `Lambda.Unknown` /
  `Sandbox.Timedout` / `Lambda.TooManyRequestsException`.
- AWS Services: Step Functions Task (`arn:aws:states:::lambda:invoke`) + AWS Lambda
- Architecture Decision:
  ```json
  "Retry": [{
    "ErrorEquals": ["Lambda.ClientExecutionTimeoutException","Lambda.ServiceException","Lambda.AWSLambdaException","Lambda.SdkClientException"],
    "IntervalSeconds": 2, "MaxAttempts": 6, "BackoffRate": 2
  }]
  ```
  Add a final catch-all matching `Lambda.Unknown`, `Sandbox.Timedout`, `States.TaskFailed`.
- Verification: Inspect execution event history for `TaskRetry` events on injected failures.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#bp-lambda-serviceexception (accessed 2026-07-31)

**4. Never pass >256 KiB between states — offload to Amazon S3 and pass the ARN**
- Pillar Alignment: Reliability, Performance Efficiency
- Why: "Executions that pass large payloads… can be terminated. If the data… might grow to over
  256 KiB, use Amazon S3… and parse the ARN of the bucket in the `Payload` parameter." Exceeding the
  payload quota raises the terminal `States.DataLimitExceeded` error (not catchable by `States.ALL`).
- AWS Services: Step Functions + Amazon S3
- Architecture Decision: Store the large object in S3; pass `{ "bucket": "<arn>", "key": "data.json" }`
  and have the consuming Task/Lambda read directly from S3.
- Verification: Check CloudWatch for `States.DataLimitExceeded`; audit ASL for large inline payloads.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#avoid-exec-failures (accessed 2026-07-31)

**5. Enable CloudWatch Logs with the `/aws/vendedlogs/` prefix (mandatory visibility for Express)**
- Pillar Alignment: Operational Excellence
- Why: Express workflows are **not** captured by Step Functions history — "Logging must be enabled
  through Amazon CloudWatch Logs." CloudWatch Logs resource policies cap at 5,120 chars and 10 policies
  per region/account; the `/aws/vendedlogs/` prefix avoids the policy-size limit.
- AWS Services: Step Functions + Amazon CloudWatch Logs
- Architecture Decision: Log group named e.g. `/aws/vendedlogs/states/<name>`; set log level per env
  (ALL in non-prod, ERROR/FATAL in prod to control cost).
- Verification: `aws stepfunctions describe-state-machine … --query loggingConfiguration`
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#bp-cwl (accessed 2026-07-31)

**6. Scope the execution IAM role to least privilege (no wildcards on resources)**
- Pillar Alignment: Security
- Why: Step Functions assumes an IAM role to call integrated services. The Distributed Map permission
  example grants only `states:StartExecution` / `states:DescribeExecution` on the *specific*
  state-machine and execution ARNs — the documented least-privilege pattern.
- AWS Services: Step Functions + AWS IAM
- Architecture Decision: Grant only the actions/resources the workflow's Tasks invoke (e.g. the exact
  Lambda ARN, S3 bucket ARN, DynamoDB table ARN); scope Distributed Map to
  `arn:aws:states:<region>:<acct>:stateMachine:<name>` and its `execution:<name>:*`.
- Verification: IAM Access Analyzer policy validation; review for `Resource: "*"` on `states:*`.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html#dist-map-permissions (accessed 2026-07-31)

**7. Prevent history-quota execution failure on long/large workflows**
- Pillar Alignment: Reliability
- Why: Hard quota of **25,000 events** per execution history; at 24,999 the execution waits and fails
  with `ExecutionFailed` if event 25,000 is not `ExecutionSucceeded`.
- AWS Services: Step Functions (Distributed Map / nested executions)
- Architecture Decision: Use **Distributed Map** (each iteration = isolated child history) or start
  **nested child executions** from a Task to split work across execution histories.
- Verification: Monitor `ExecutionsFailed` and event counts on long-running state machines.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#bp-history-limit (accessed 2026-07-31)

### ⚠️ Architectural Decisions

**Decision A — Standard vs. Express workflow type**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | **Standard** | Step Functions Standard | Durability, exactly-once, 1-year runtime, full audit, `.sync`/callback, Distributed Map, Activities | Higher per-transition cost at very high volume | Non-idempotent steps (payments, EMR start), human-in-the-loop, orchestration you must audit |
  | **Express (Async)** | Step Functions Express | Throughput (100k/s start), near-unlimited transitions, low cost per short run | At-least-once (may re-run steps), 5-min cap, no native history, no `.sync`/callback | Idempotent high-volume event/stream/IoT ingestion |
  | **Express (Sync)** | Step Functions Express (`StartSyncExecution`) | Request/response microservice orchestration with a returned result | At-most-once, 5-min cap (console 60s), no history/`.sync` | API Gateway/Lambda-fronted synchronous microservice composition |

- Cost Profile: Standard = **per state transition**; Express = **per execution + duration + memory**
  (+ CloudWatch Logs cost). High-frequency short workflows are usually cheaper on Express.
- Lock-in Assessment: ASL is AWS-proprietary; both types share the language, so the *type* choice does
  not change portability — but it is **immutable** (only "Copy to new" migrates).
- Architect Instruction: "Ask whether every step is idempotent and whether the workflow completes in
  ≤5 minutes before choosing Express; if any step is non-idempotent or needs `.sync`/callback, choose
  Standard (optionally nesting Express children for the idempotent, high-volume portions)."
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html (accessed 2026-07-31)

**Decision B — Query language: JSONPath (legacy) vs. JSONata (2024-11-22)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | **JSONPath** | ASL `InputPath`/`Parameters`/`ResultPath`/`OutputPath` | Compatibility with pre-2024 workflows and tooling | Verbose data threading; needs Lambda glue for math/date/string ops | Maintaining existing workflows; teams standardized on JSONPath |
  | **JSONata** | ASL `Arguments`/`Output`/`Assign` + `Variables` | Fewer states, native date/math/string transforms, cross-state variables | Newer (verify tooling/IaC support); mutually exclusive with JSONPath fields per state | New workflows needing transforms or to eliminate pass-through states |

- Cost Profile: JSONata can **reduce state transitions** (fewer Pass states / less glue) → lower cost
  on Standard workflows and fewer Lambda invocations.
- Lock-in Assessment: Both AWS-proprietary within ASL; JSONata itself is an open-source language, but
  the ASL binding is AWS-specific.
- Architect Instruction: "Ask whether the workflow is greenfield and needs data transformation; if so,
  default to JSONata + Variables and use the TestState API to validate expressions before deploying."
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/transforming-data.html · https://aws.amazon.com/blogs/compute/simplifying-developer-experience-with-variables-and-jsonata-in-aws-step-functions/ (2024-11-22, accessed 2026-07-31)

**Decision C — Iteration model: Inline Map vs. Distributed Map**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | **Inline Map** | ASL `Map` (default mode) | Simplicity, shared execution history, low overhead | Max **40** concurrent iterations; counts against the 25,000-event history; dataset must fit in 256 KiB payload | Small in-memory arrays, ≤40 items needing modest parallelism |
  | **Distributed Map** | ASL `Map` `Mode: DISTRIBUTED` | Up to **10,000** parallel child executions; reads S3-scale CSV/JSON/manifests/Parquet; isolated child histories; failure thresholds | Standard-only; child-execution overhead; needs S3 read/write + StartExecution IAM | Dataset >256 KiB, >40 concurrency, or history would exceed 25,000 events |

- Cost Profile: Distributed Map bills each child execution; use `ItemBatcher` to amortize per-item
  overhead, and `ExecutionType: EXPRESS` for child workflows to cut cost on idempotent item processing.
- Lock-in Assessment: Native ASL; portability equal to any Step Functions workflow.
- Architect Instruction: "Ask for dataset size, required concurrency, and item idempotency; choose
  Distributed Map when any of (>256 KiB, >40 concurrency, >25k events) holds, and set
  `ToleratedFailurePercentage`/`ToleratedFailureCount` to your acceptable partial-failure budget."
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html (accessed 2026-07-31)

**Decision D — Service integration pattern: Request-Response vs `.sync` vs `.waitForTaskToken`**
- Options:

  | Option | Pattern | Optimizes | Sacrifices | Best When |
  |--------|---------|-----------|------------|-----------|
  | **Request-Response** | default | Simplicity; only option on Express | Doesn't wait for downstream job completion | Fire-and-continue calls; Express workflows |
  | **Run-a-Job `.sync`** | Standard-only, select services | Waits for job (Glue/ECS/EMR/Batch/SageMaker) to finish; polls for you | Standard-only; not all services support it | Long-running managed-job orchestration (ETL, training, containers) |
  | **Wait-for-Callback `.waitForTaskToken`** | Standard + specific services | Pauses up to 1 year for human/external callback | Standard-only; requires token plumbing + heartbeats | Human-in-the-loop, external approval, async 3rd-party systems |

- Cost Profile: `.sync` and `.waitForTaskToken` keep a Standard execution alive (per-transition billing,
  not per-second) — cheaper than busy-polling Lambda for long waits.
- Architect Instruction: "Ask whether the workflow must block on a downstream job or an external human
  action; if yes it must be Standard — Express cannot do `.sync` or `.waitForTaskToken`."
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.md · https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html (accessed 2026-07-31)

### 🚫 Anti-Patterns

> Every entry below gives a concrete ❌ Wrong / ✅ Correct pair using exact AWS service/ASL names.

**AP-1 — No `TimeoutSeconds` on Task/Activity states**
- Risk Level: HIGH
- Why: Reliability. An Activity/Task with no timeout can hang forever waiting for a response.
- ❌ Wrong: `"ActivityState": { "Type": "Task", "Resource": "arn:aws:states:us-east-1:123456789012:activity:HelloWorld", "Next": "NextState" }` (no timeout)
- ✅ Correct: add `"TimeoutSeconds": 300` (and `"HeartbeatSeconds": 60` when using `.waitForTaskToken`).
- Detection: Static scan of the ASL for Task states missing `TimeoutSeconds`.
- Impact: Stuck execution → cascading backlog, Standard per-transition cost accrues, SLA breach.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#sfn-stuck-execution (accessed 2026-07-31)

**AP-2 — Non-idempotent steps on an Express workflow**
- Risk Level: CRITICAL
- Why: Reliability/Correctness. Async Express is *at-least-once* — a step may run more than once.
- ❌ Wrong: Charging a payment or `StartJobRun` on EMR inside an **Express** state machine.
- ✅ Correct: Put non-idempotent steps in a **Standard** parent (exactly-once); nest an **Express**
  child only for idempotent work (e.g. `DynamoDB PutItem`, notifications).
- Detection: Review `type` of the state machine vs. the side-effect profile of its Tasks.
- Impact: Double charges / duplicate side effects / data corruption.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html (accessed 2026-07-31)

**AP-3 — Passing large (>256 KiB) payloads between states**
- Risk Level: HIGH
- Why: Reliability. Exceeding the payload quota raises terminal `States.DataLimitExceeded`
  (not catchable by `States.ALL`), failing the execution.
- ❌ Wrong: A Lambda Task returning a 2 MB JSON blob that the next Task consumes inline.
- ✅ Correct: Write the blob to `s3://amzn-s3-demo-large-payload-json/data.json`; pass
  `{ "bucket": "arn:aws:s3:::amzn-s3-demo-large-payload-json", "key": "data.json" }` and read in-Task.
- Detection: CloudWatch for `States.DataLimitExceeded`; inspect state output sizes.
- Impact: Hard execution failure; lost work if not redrivable.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#avoid-exec-failures (accessed 2026-07-31)

**AP-4 — Unhandled transient Lambda exceptions / relying on `States.ALL` alone**
- Risk Level: HIGH
- Why: Reliability. `States.ALL` does **not** catch `States.DataLimitExceeded` or `States.Runtime`,
  and transient Lambda 500s (`Lambda.ServiceException`, `Lambda.SdkClientException`) fail the run.
- ❌ Wrong: A `lambda:invoke` Task with no `Retry`, or only `"ErrorEquals": ["States.ALL"]`.
- ✅ Correct: Explicit retrier on `Lambda.ServiceException`/`AWSLambdaException`/`SdkClientException`/
  `ClientExecutionTimeoutException` (`MaxAttempts: 6`, `BackoffRate: 2`), plus a final `States.ALL`
  catcher last-in-array; match `Lambda.Unknown`/`Sandbox.Timedout` for unhandled runtime errors.
- Detection: Audit ASL Task states for missing Retry; inject faults and inspect history.
- Impact: Avoidable execution failures from recoverable transient errors.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html · https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#bp-lambda-serviceexception (accessed 2026-07-31)

**AP-5 — Over-broad execution IAM role**
- Risk Level: CRITICAL
- Why: Security (least privilege). A wildcard role lets a compromised workflow call any action/resource.
- ❌ Wrong: Execution role with `{ "Action": "states:*", "Resource": "*" }` or `lambda:InvokeFunction`
  on `Resource: "*"`.
- ✅ Correct: Scope to exact ARNs — e.g. `states:StartExecution` on
  `arn:aws:states:us-east-1:123456789012:stateMachine:myStateMachineName` and `states:DescribeExecution`
  on `…:execution:myStateMachineName:*`; `lambda:InvokeFunction` on the specific function ARN.
- Detection: IAM Access Analyzer; grep policies for `Resource": "*"`.
- Impact: Privilege escalation / lateral movement blast radius across the account.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html#dist-map-permissions (accessed 2026-07-31)

**AP-6 — Long-running Standard execution ignoring the 25,000-event history quota**
- Risk Level: MEDIUM
- Why: Reliability. At 25,000 events the execution fails with `ExecutionFailed`.
- ❌ Wrong: A single Standard execution looping/iterating tens of thousands of steps in-line.
- ✅ Correct: Use **Distributed Map** (isolated child histories) or start **nested child executions**
  from a Task to spread work across multiple histories.
- Detection: Monitor per-execution event counts; alarm on `ExecutionsFailed`.
- Impact: Late-stage failure of long, expensive workflows.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#bp-history-limit (accessed 2026-07-31)

---

## Cloud-Native Design Patterns

**Saga / Orchestration with compensation**
- Category: Communication / Resilience
- Problem: Coordinate a multi-service transaction where partial failures must be compensated.
- Solution on AWS: Standard workflow with per-Task `Catch` routing to compensating Tasks; `.sync` for
  managed jobs; `.waitForTaskToken` for external confirmation.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Correctness | Exactly-once, explicit compensation path | More states to author/maintain |
  | Cost | Per-transition (cheap for long waits) | Adds transitions vs. a single Lambda |

- Source: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html (accessed 2026-07-31)

**Human-in-the-loop approval (callback)**
- Category: Communication
- Problem: Pause a workflow until a person or external system approves.
- Solution on AWS: `.waitForTaskToken` Task publishing the token to SQS/SNS; resume via
  `SendTaskSuccess`/`SendTaskFailure`; `HeartbeatSeconds` guards against stuck tasks (up to 1 year).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Flexibility | Arbitrary external/human latency | Standard-only; token plumbing |
  | Reliability | Heartbeats detect worker death | Must handle token expiry/idempotency |

- Source: https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.md · callback-task-sample-sqs.md (accessed 2026-07-31)

**Large-scale parallel data processing (fan-out)**
- Category: Scalability / Data
- Problem: Process millions of S3 objects or CSV/JSON/Parquet rows concurrently.
- Solution on AWS: **Distributed Map** reading via `ItemReader` (S3 objects, CSV, JSON, manifests,
  Parquet — Parquet/Athena manifests added 2025-09-18), `ItemBatcher` to batch items, `MaxConcurrency`
  (default/0 → 10,000), `ResultWriter` to S3, and `ToleratedFailurePercentage`/`Count` thresholds.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Throughput | Up to 10,000 parallel child executions | Standard-only; child-execution overhead |
  | Resilience | Isolated child histories; partial-failure budget | Must not exceed downstream (e.g. Lambda) capacity |

- Source: https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html · https://aws.amazon.com/about-aws/whats-new/2025/09/aws-step-functions-data-source-options-observability-distributed-map/ (accessed 2026-07-31)

**Cost-optimized nesting (Express inside Standard)**
- Category: Migration / Cost
- Problem: A workflow mixes non-idempotent long-running steps with high-volume idempotent steps.
- Solution on AWS: Standard **parent** for non-idempotent/audited steps; nested **Express child** for
  idempotent, high-event-rate steps (billed per execution+duration+memory).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Cost | Cheaper high-volume portion on Express | Child adds CloudWatch Logs cost + complexity |
  | Correctness | Preserves exactly-once where it matters | Two state machines to manage |

- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#cost-opt-exp-workflows (accessed 2026-07-31)

---

## Security Architecture

**Identity — least-privilege execution role**
- AWS Services: IAM role assumed by the state machine; `iam:PassRole` at deploy time.
- Architecture: Grant only the actions the Tasks invoke, scoped to exact resource ARNs. For
  Distributed Map, add `states:StartExecution` + `states:DescribeExecution` scoped to the specific
  state-machine/execution ARNs, plus S3 read/write for `ItemReader`/`ResultWriter`.
- Compliance Alignment: Supports least-privilege controls (Well-Architected Security pillar);
  tag-based authorization via `aws:ResourceTag/...` conditions. *(Structure only — not legal advice.)*
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html#dist-map-permissions · https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#concepts-tagging (accessed 2026-07-31)

**Data — encryption with KMS customer-managed keys**
- AWS Services: Step Functions + AWS KMS.
- Architecture: Encrypt workflow definitions, execution data/logs, and activity inputs/outputs with a
  KMS **customer managed key** (launched 2024-06-25) instead of the default AWS-owned key, for
  key-rotation control and auditability.
- Compliance Alignment: Encryption-at-rest control; key policy governs access. *(Confirm against your
  certification scope before treating as mandatory — see Assumptions.)*
- Source: https://aws.amazon.com/about-aws/whats-new/2024/07/aws-step-functions-customer-managed-keys/ (2024-06-25, accessed 2026-07-31)

**Network — private connectivity for HTTP Task / calls**
- AWS Services: Step Functions HTTP Task (HTTPS endpoints, 2023-11-26); VPC-integrated targets via
  optimized integrations (e.g. ECS/EKS) and EventBridge Connections for third-party auth.
- Architecture: Use EventBridge API Connections to store third-party credentials for HTTP Tasks;
  HTTP Task times out at 60 s (`States.Http.Socket`).
- Source: https://aws.amazon.com/about-aws/whats-new/2023/11/aws-step-functions-https-endpoints-teststate-api/ (2023-11-26, accessed 2026-07-31)

---

## Operational Patterns

**Observability**
- AWS Services: CloudWatch Logs (execution history for Express; optional for Standard), CloudWatch
  Metrics (`ExecutionsFailed`, `ExecutionsTimedOut`, Map Run metrics), Step Functions **metrics
  dashboard** (2025-10-30), X-Ray tracing.
- Architecture: Prefix log groups with `/aws/vendedlogs/states` (avoids the 5,120-char resource-policy
  limit and 10-policy/region cap); set log level by environment to manage cost.
- Cost Profile: Medium — CloudWatch Logs ingestion is the primary driver for Express.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#bp-cwl · https://aws.amazon.com/about-aws/whats-new/2025/10/aws-step-functions-metrics-dashboard/ (accessed 2026-07-31)

**Failure recovery — Redrive**
- AWS Services: Step Functions Redrive (2023-11-15).
- Architecture: Restart a failed Standard execution from the point of failure; Retry counters for
  redriven Task/Parallel/Inline-Map states reset to 0 (fresh max-attempt budget on redrive).
- Cost Profile: Low — reuses prior successful state instead of re-running upstream work.
- Automation: Trigger redrive from an EventBridge rule on failure events + a Lambda handler.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/redrive-executions.html (accessed 2026-07-31)

**Development safety — TestState API**
- AWS Services: Step Functions TestState API (2023-11-26).
- Architecture: Validate a single state's input/output processing, JSONata expressions, and Variables
  before deploying — the recommended way to verify transforms.
- Source: https://aws.amazon.com/about-aws/whats-new/2023/11/aws-step-functions-https-endpoints-teststate-api/ (accessed 2026-07-31)

---

## Reference Architectures

**Standard order-processing workflow (mixed idempotency)**
- Context: Orchestrate payment (non-idempotent), inventory update, and notifications.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Orchestration (parent) | Step Functions **Standard** | Exactly-once; human approval via `.waitForTaskToken` |
  | Compute | AWS Lambda / ECS (`.sync`) | Business logic / long-running jobs |
  | High-volume child | Step Functions **Express** (nested) | Idempotent notifications/inventory writes |
  | State/Data | DynamoDB, S3 (large payloads) | Durable state; >256 KiB offload |
  | Security | IAM (scoped role), KMS CMK | Least privilege; encryption at rest |
  | Observability | CloudWatch Logs/Metrics, X-Ray | History, alarms, tracing |

- Key Decisions: Which steps are non-idempotent (→ Standard) vs. idempotent (→ nested Express).
- Scaling Path: Move fan-out steps to Distributed Map as volume grows.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#cost-opt-exp-workflows (accessed 2026-07-31)

**Large-scale S3 data pipeline (Distributed Map)**
- Context: Process millions of CSV/JSON/Parquet records from S3.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Orchestration | Step Functions **Standard** + Distributed Map | 10,000-way parallelism, isolated child histories |
  | Item source | S3 (`ItemReader`: CSV/JSON/manifest/Parquet) | Large-scale input |
  | Item compute | Lambda / ECS (child `ExecutionType: EXPRESS`) | Per-batch processing |
  | Results | S3 (`ResultWriter`) | Consolidated child outputs |

- Key Decisions: `MaxConcurrency` vs. downstream capacity; `ToleratedFailurePercentage`/`Count`;
  `ItemBatcher` batch size.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html (accessed 2026-07-31)

---

## Service Equivalence Map — Workflow Orchestration

> Equivalence ≠ feature parity. Validate against each provider's current docs before deciding.

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|--------------|-------|--------------------|
| **Serverless workflow orchestration** | Step Functions | Workflows | Logic Apps (Standard) / Durable Functions | OCI Functions + Resource Scheduler / Data Integration flows |
| **Long-running/stateful orchestration** | Step Functions **Standard** (up to 1 year) | Workflows (up to 1 year) | Durable Functions (orchestrator functions) | (No direct 1-year equivalent) |
| **High-volume short workflows** | Step Functions **Express** (≤5 min) | Workflows / Eventarc + Cloud Run | Logic Apps Consumption / Azure Functions | OCI Functions + Streaming |
| **Large-scale parallel fan-out** | Distributed Map (10,000 child execs) | Workflows parallel steps / Batch | Durable Functions fan-out/fan-in | OCI Data Flow (Spark) |
| **Human-in-the-loop / callback** | `.waitForTaskToken` | Workflows callbacks | Logic Apps approval / Durable external events | Custom (Functions + Queue) |
| **Visual authoring** | Workflow Studio | Workflows editor | Logic Apps Designer | OCI Console flows |
| **Definition language** | Amazon States Language (JSON) | Workflows YAML/JSON | Workflow Definition Language (JSON) / C#/JS orchestrator code | JSON/YAML config |

Source (AWS column): https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html · choosing-workflow-type.html (accessed 2026-07-31). Cross-provider names are for orientation only and are **not** re-verified against each provider's current docs in this AWS-scoped research — flag as *unverified* before multi-cloud decisions.

---

## Provider Differentiators (AWS Step Functions)

```
Differentiator: Distributed Map (10,000 parallel child executions over S3-scale data)
Category: Data / Scalability
Unique Value: Native serverless fan-out over CSV/JSON/manifest/Parquet directly from S3 with isolated child histories and failure thresholds — no cluster to manage.
Architecture Impact: Removes the 40-concurrency/256 KiB/25k-event ceilings of inline iteration.
When to Leverage: Batch data processing, vulnerability scanning, Monte Carlo, claims processing.
Caveat: Standard workflows only; child-execution overhead; respect downstream service limits.
Source: https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html (accessed 2026-07-31)
```
```
Differentiator: 200+ AWS SDK integrations + optimized .sync / .waitForTaskToken patterns
Category: Integration
Unique Value: Call thousands of AWS API actions declaratively, and wait on managed jobs or external callbacks without writing polling code.
Architecture Impact: Replaces glue Lambdas for service invocation and job waiting.
When to Leverage: Orchestrating Glue/EMR/ECS/SageMaker/Batch or human approvals.
Caveat: Express supports only Request-Response; .sync/.waitForTaskToken are Standard-only.
Source: https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html (accessed 2026-07-31)
```
```
Differentiator: Exactly-once Standard execution model with 1-year runtime + Redrive
Category: Reliability
Unique Value: Safe orchestration of non-idempotent actions with resume-from-failure recovery.
Architecture Impact: Enables sagas/human-in-the-loop without custom idempotency + checkpointing.
When to Leverage: Payments, provisioning, approvals, anything non-idempotent.
Caveat: Per-state-transition billing; 25,000-event history quota per execution.
Source: https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html · redrive-executions.md (accessed 2026-07-31)
```

---

## Recent Feature Launch Timeline (currency evidence)

| Launch date | Feature | Note |
|---|---|---|
| 2026-06-03 | AgentCore-powered agentic reasoning step | ⚠️ Very recent; verify GA/region scope |
| 2026-03-26 | +28 service integrations incl. Bedrock AgentCore | ⚠️ Verify before use |
| 2025-10-30 | Metrics dashboard | Observability |
| 2025-09-18 | Distributed Map: Athena manifests + Parquet, better observability | Data pipelines |
| 2025-02-07 | Distributed Map: expanded data source/output options | Data pipelines |
| 2024-11-22 | **Variables + JSONata transformations** | Core data-model shift |
| 2024-11-14 | IaC export to SAM/CloudFormation/Infrastructure Composer | Tooling |
| 2024-06-25 | **KMS customer-managed-key encryption** | Security |
| 2023-11-26 | **HTTPS endpoints (HTTP Task) + TestState API** | Integration/dev |
| 2023-11-15 | **Redrive** (restart from failure) | Reliability |
| 2023-09-07 | Enhanced error handling (`MaxDelaySeconds`, `JitterStrategy`) | Reliability |
| 2023-06-22 | Versions and aliases | Deployment |
| 2022-12-01 | **Distributed Map** | Scalability |

Source: https://docs.aws.amazon.com/step-functions/latest/dg/recent-launches.html (accessed 2026-07-31)

---

## Scenario Coverage

**Standard Case** — Microservice orchestration with mixed idempotency
- Approach: Standard parent (exactly-once) + nested Express children for idempotent high-volume steps;
  explicit `TimeoutSeconds`, Lambda transient-error `Retry`, scoped IAM role, CloudWatch logging.
- Key Decisions: Workflow type per step idempotency; JSONata vs JSONPath; integration pattern.

**Edge Case** — Millions of records to process under a partial-failure budget
- Approach: Distributed Map (`ExecutionType: EXPRESS` children), `ItemBatcher`, `MaxConcurrency`
  tuned to downstream limits, `ToleratedFailurePercentage`/`Count`, `ResultWriter` to S3, redrive on
  Map Run failure. Use nested executions/Distributed Map to avoid the 25,000-event history quota.

**Anti-Pattern Case** — Request to run payment processing on an Express workflow "for speed/cost"
- Clarification: Refuse/flag — Express async is *at-least-once* and may double-execute the charge.
  Ask: "Is every step idempotent and ≤5 min?" If no, use Standard (nest Express only for the
  idempotent portion).

---

## Source Bibliography (all accessed 2026-07-31)

### Primary — Official AWS Step Functions Developer Guide
- What is Step Functions? — https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html
- Choosing workflow type — https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html
- Handling errors (Retry/Catch, error names) — https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html
- Best practices — https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html
- Distributed Map state — https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html
- Transforming data with JSONata — https://docs.aws.amazon.com/step-functions/latest/dg/transforming-data.html
- Passing data with Variables — https://docs.aws.amazon.com/step-functions/latest/dg/workflow-variables.html
- Redrive executions — https://docs.aws.amazon.com/step-functions/latest/dg/redrive-executions.html
- Recent feature launches — https://docs.aws.amazon.com/step-functions/latest/dg/recent-launches.html

### Primary — AWS What's New / Compute Blog (dated announcements)
- Variables + JSONata (2024-11-22) — https://aws.amazon.com/blogs/compute/simplifying-developer-experience-with-variables-and-jsonata-in-aws-step-functions/
- KMS customer-managed keys (2024-06-25) — https://aws.amazon.com/about-aws/whats-new/2024/07/aws-step-functions-customer-managed-keys/
- HTTPS endpoints + TestState API (2023-11-26) — https://aws.amazon.com/about-aws/whats-new/2023/11/aws-step-functions-https-endpoints-teststate-api/
- Enhanced error handling (2023-09-07) — https://aws.amazon.com/about-aws/whats-new/2023/09/aws-step-functions-enhanced-error-handling/
- Distributed Map GA (2022-12-01) — https://aws.amazon.com/about-aws/whats-new/2022/12/aws-step-functions-large-scale-parallel-workflows-data-processing-serverless-applications/
- Distributed Map data sources + observability (2025-09-18) — https://aws.amazon.com/about-aws/whats-new/2025/09/aws-step-functions-data-source-options-observability-distributed-map/
- Metrics dashboard (2025-10-30) — https://aws.amazon.com/about-aws/whats-new/2025/10/aws-step-functions-metrics-dashboard/

### Reference — API
- Step Functions API Reference — https://docs.aws.amazon.com/step-functions/latest/apireference
- Pricing — https://aws.amazon.com/step-functions/pricing/

---

## Agent Operation Notes (for downstream skill authoring)

- **High confidence (autonomous)**: Standard vs Express semantics, error-handling fields/defaults,
  Distributed Map fields/limits, best-practice guardrails, launch dates — all from official DG pages.
- **Medium confidence (verify)**: 2026 launches (AgentCore step, +28 integrations) — verify GA/region
  before authoring skills that depend on them; cross-provider equivalence names (not re-verified here).
- **Must ask user (unverified)**: `ARCHITECTURE_CONTEXT`, compliance scope, cost/billing constraints,
  and whether workloads should default to Standard or Express — see Assumptions section.

> Recommended next step: run `/skill-best-practices-validator` on any SKILL.md derived from this
> research, and confirm the four Ask-First items above with the requester before producing ADRs.
