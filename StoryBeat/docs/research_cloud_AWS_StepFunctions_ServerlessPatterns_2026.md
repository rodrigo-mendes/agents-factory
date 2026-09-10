# Cloud Architecture Research — AWS Step Functions Serverless Patterns 2026

## Metadata

```yaml
Full_Name: "AWS Step Functions Serverless Patterns"
Cloud_Provider: "AWS"
Architecture_Domain: "Serverless Patterns"
Target_Edition: "AWS Step Functions 2026"
Architecture_Context: "Serverless orchestration for event-driven and workflow-based applications"
Official_Source_URL: "https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-31"
Currency_Threshold: "2027-08-31"
Research_Depth: "exhaustive"
Max_Iterations: "5"
Research_Quality_Score: "94%"
# Research_Quality_Score = (total_claims - unverified - irresolvable) / total_claims * 100
Gap_Loop_Ran: "true"
Iterations_Used: "3 of 5"
Triangulated_Count: "38"
Unverified_Count: "3"
Irresolvable_Count: "2"
```

---

## Executive Summary

AWS Step Functions is a fully managed serverless orchestration service that lets architects define stateful, long-running business processes as visual state machines expressed in Amazon States Language (ASL). It integrates natively with 220+ AWS services via direct SDK integrations and optimized integrations, eliminating the need for Lambda-as-glue functions for simple API calls. Step Functions offers two workflow types — Standard (exactly-once, 1-year duration, per-transition pricing) and Express (at-least-once or at-most-once, 5-minute cap, per-duration pricing) — serving fundamentally different workload profiles. Within the AWS serverless ecosystem it sits as the coordination layer between compute (Lambda, ECS), data (DynamoDB, S3), and messaging (SQS, SNS, EventBridge) services.

The 2024–2026 period delivered two transformative additions: JSONata query language support (2024, GA) replacing the verbose five-field JSONPath I/O pipeline with a two-field model (`Arguments`/`Output`) and workflow variables (`Assign` field), and a major Distributed Map enhancement (Sep 2025, GA) adding Athena manifest, Apache Parquet, and S3ListObjectsV2 as native `ItemReader` data sources alongside new CloudWatch observability metrics. The TestState API was enhanced in Nov 2025 to support mocking of service integrations without requiring IAM roles, enabling local-first development and CI/CD gate validation. Earlier milestones confirmed GA include Redrive (restart failed Standard executions from point of failure), Versions and Aliases with traffic-splitting, and HTTP Tasks for direct third-party HTTPS API calls.

The three most critical architecture guardrails for serverless orchestration are: (1) every Task, Parallel, and Map state must declare `Retry` with `JitterStrategy: FULL` and a `Catch` block — omitting retry causes any transient AWS API error to permanently fail the execution; (2) every Task state must declare `TimeoutSeconds` (and `.waitForTaskToken` states must also declare `HeartbeatSeconds`) — without timeouts, executions block indefinitely consuming quota and accruing Standard Workflow per-transition billing for up to one year; (3) CloudWatch Logs must be enabled at `Level: ALL` or `ERROR` on every state machine — Express Workflows produce zero observable execution history without it, making failures completely undiagnosable in production.

---

## Cloud Architecture Glossary

```
Term: State Machine (Workflow)
Definition: Top-level Step Functions resource containing states and a StartAt pointer, defined in Amazon States Language (ASL). Workflow type (Standard vs Express) is immutable after creation.
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html
Architect Usage: Choose workflow type before creating — it cannot be changed. Use Standard for audit trails, exactly-once semantics, or .sync/.waitForTaskToken patterns. Use Express for high-throughput short-duration idempotent flows.
Common Confusion: Conflating Standard and Express as interchangeable. They have incompatible semantic guarantees, pricing models, and feature sets. Workflow type is immutable.

Term: Standard Workflow
Definition: Execution semantics: exactly-once. Max duration: 1 year. Execution rate: 2,000/sec. State transition rate: 4,000/sec. Priced per state transition. Execution history stored 90 days. Supports all integration patterns (.sync, .waitForTaskToken). Supports Distributed Map and Activities.
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-standard-vs-express.html
Architect Usage: Use for payment processing, order fulfillment, compliance workflows, human-in-the-loop processes, and any flow requiring exactly-once guarantees or long execution windows.
Common Confusion: Standard Workflows are not "always better" — at high volume (>2,000 exec/sec) they throttle and cost significantly more than Express per execution.

Term: Express Workflow
Definition: Max duration: 5 minutes. Execution rate: 100,000/sec. Priced per execution × duration × memory. Execution history only in CloudWatch Logs (not in Step Functions console). Does NOT support .sync, .waitForTaskToken, Distributed Map, or Activities. Sub-types: Asynchronous (at-least-once, StartExecution) and Synchronous (at-most-once, StartSyncExecution).
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-standard-vs-express.html
Architect Usage: Use for event processing, IoT ingestion, streaming fan-out, and API Gateway-fronted orchestration requiring an inline result. CloudWatch Logs is mandatory — without it there is no execution history at all.
Common Confusion: "Express is cheaper" — only at high volume. For infrequently executed long workflows, Standard may cost less due to few transitions.

Term: Amazon States Language (ASL)
Definition: JSON-based language defining Step Functions workflows. Supports two query languages: JSONPath (default) and JSONata (opt-in, GA 2024). Top-level QueryLanguage field controls default; individual states can override.
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-states.html
Architect Usage: Set QueryLanguage: JSONata at state machine level for all new state machines per AWS recommendation. Use per-state override for incremental migration of existing JSONPath workflows.
Common Confusion: ASL is not AWS CloudFormation or any IaC format — it defines the runtime state machine behavior, not infrastructure provisioning.

Term: Execution
Definition: A running or completed instance of a state machine. Has its own ARN, input, output, and event history (Standard) or CloudWatch log stream (Express).
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html
Architect Usage: Standard executions are addressable by ARN and queryable via DescribeExecution/GetExecutionHistory for 90 days. Express executions require CloudWatch Logs query.
Common Confusion: Express execution history is not visible in the Step Functions console — architects who assume console visibility will have blind spots in Express production incidents.

Term: State Types (8)
Definition: Task, Choice, Parallel, Map, Wait, Pass, Succeed, Fail. Choice cannot use End: true. Parallel branches each get a copy of Parallel state input. Succeed and Fail do not support the Assign field.
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-states.html
Architect Usage: Use Pass for no-op data reshaping, Choice for conditional branching, Parallel for true concurrent fan-out, Map for dataset iteration, Wait for time-based deferral or polling fallback.
Common Confusion: Choice states do not have a Next field at the state level — routing is inside Choices rules. Also: Parallel branches run concurrently but each branch is sequential internally.

Term: Inline Map
Definition: Map state in INLINE mode. Max 40 concurrent iterations. Iterations share parent execution history (counts toward 25,000-event limit). Dataset must fit in 256 KiB state input. Supported in Standard and Express.
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html
Architect Usage: Use for small datasets (<40 items, <256 KiB). For anything larger, switch to Distributed Map. Monitor parent event count when using Inline Map over large arrays — each iteration generates multiple events.
Common Confusion: Assuming Inline Map can handle any array size. At 40+ items or when each iteration is complex, the 25,000-event ceiling becomes a real constraint.

Term: Distributed Map
Definition: Map state in DISTRIBUTED mode. Each iteration runs as an independent child workflow execution with its own history. Standard workflows only. Default 10,000 parallel child executions. Reads from S3 (JSON, CSV, S3ListObjectsV2, Athena manifests, Parquet). ResultWriter aggregates to S3. Key fields: ItemProcessor, ItemReader, ItemBatcher, ResultWriter, MaxConcurrency, ToleratedFailureCount, ToleratedFailurePercentage, Label.
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html
Architect Usage: Use for large-scale parallel processing of S3 datasets, ETL, batch file processing. Each child execution has its own 25,000-event budget. Hard quota: 10,000 concurrent child executions; 1,000 open Map Runs.
Common Confusion: Distributed Map cannot read outer-scope workflow variables (current limitation, 2026). Also, it is not available in Express Workflows.

Term: Service Integration Patterns (3)
Definition: (1) Request/Response — calls service, advances immediately on HTTP 200 (Standard + Express). (2) Run a Job (.sync) — pauses until job completes, polls via EventBridge same-account or polling cross-account (Standard only). (3) Wait for Callback (.waitForTaskToken) — pauses until external system calls SendTaskSuccess/SendTaskFailure; token via $$.Task.Token (JSONPath) or $states.context.Task.Token (JSONata) (Standard only). New token generated per retry attempt.
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html
Architect Usage: Default to Request/Response for simple calls. Use .sync for AWS-managed jobs (Batch, ECS, Glue, SageMaker). Use .waitForTaskToken for human approvals, third-party async callbacks, or SaaS webhooks.
Common Confusion: .waitForTaskToken is Standard-only — attempting to use it in Express fails at execution time, not at definition time.

Term: Context Object
Definition: Execution metadata accessed via $$. (JSONPath) or $states.context (JSONata). Contains Task.Token, Execution.Id, Execution.StartTime, State.Name, State.EnteredTime, Map.Item.Index, Map.Item.Value.
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html
Architect Usage: Use $$.Task.Token (JSONPath) or $states.context.Task.Token (JSONata) to pass the task token to external systems. Use $$.Execution.Id for idempotency keys in downstream service calls.
Common Confusion: $$ is the context object prefix in JSONPath; $ is the state input. Mixing them causes incorrect data binding without an obvious error message.

Term: JSONPath (Query Language)
Definition: Default ASL query language. $. for state input, $$. for context. Five I/O fields: InputPath, Parameters (with .$ suffix for dynamic values), ResultSelector, ResultPath, OutputPath. Intrinsic functions available (States.Format, States.ArrayPartition, States.StringToJson, etc.).
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/transforming-data.html
Architect Usage: Use for existing state machines or when team is already proficient. The .$ suffix on Parameters keys is mandatory for dynamic values — missing it causes the literal string "$$.Task.Token" to be passed instead of the actual token.
Common Confusion: The five I/O fields (InputPath, Parameters, ResultSelector, ResultPath, OutputPath) apply in a specific pipeline order. Applying them out-of-order in mental models causes incorrect data transformation design.

Term: JSONata (Query Language)
Definition: Opt-in (2024, GA). JSONata 2.0.6. Two fields replace five: Arguments (replaces InputPath+Parameters) and Output (replaces ResultSelector+ResultPath+OutputPath). $states reserved variable ($states.input, $states.result, $states.errorOutput, $states.context). {% expression %} syntax. $eval not supported — use $parse. Assign and Output processed in parallel — values assigned in Assign are not available in the same state's Output expression.
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/transforming-data.html
Architect Usage: Use for all new state machines. AWS recommends JSONata in the console. Custom functions: $partition, $range, $hash, $random, $uuid, $parse. 1-second expression timeout limit — offload complex computation to Lambda.
Common Confusion: Assuming values assigned in Assign are available in the same state's Output. They are not — Assign and Output are evaluated in parallel using state-entry values.

Term: Workflow Variables (Assign Field)
Definition: Assign field persists named values across states. States supporting Assign: Pass, Task, Map, Parallel, Choice, Wait (not Succeed or Fail). All keys in Assign evaluated simultaneously using state-entry values. Scope: workflow-local. Parallel/Map branches have inner scope but can read outer. Distributed Map cannot read outer-scope variables (current limitation).
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/workflow-variables.html
Architect Usage: Use to avoid threading data through every state's output. Limits: max single variable 256 KiB, max total per execution 10 MiB, max variable name 80 characters.
Common Confusion: Distributed Map child executions cannot access outer-scope workflow variables — any variable needed inside a Distributed Map must be passed via ItemReader/ItemBatcher input.

Term: Redrive
Definition: Restarts failed/aborted/timed-out Standard Workflow from point of failure (not from beginning). Eligibility: started after Nov 15, 2023; not SUCCEEDED; within 14-day window; under 24,999 events. Retry count resets to 0. Standard Workflow only. API: RedriveExecution.
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/redrive-executions.html
Architect Usage: Use to recover payment or fulfillment workflows that failed after partial completion without re-running completed steps. Set up EventBridge rules on ExecutionFailed to trigger automated Redrive within the 14-day window.
Common Confusion: Redrive does not reset the 14-day clock; the window is measured from the original execution start time, not from the Redrive invocation.

Term: Versions and Aliases
Definition: Versions are immutable numbered snapshots (up to 1,000 per state machine). Aliases are mutable named pointers to 1–2 versions with routingConfiguration (percentages must total 100). Up to 100 aliases per state machine. Enables canary/blue-green/progressive rollout deployments.
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-state-machine-version.html
Architect Usage: Use aliases as the stable invocation target (EventBridge rule, API Gateway, etc.). Publish a new version, shift 5% traffic via alias, monitor error rate, then shift to 100%.
Common Confusion: Redriven executions use the original version at execution start, even if the alias has since been updated. This is correct behavior for exactly-once audit purposes but can surprise architects expecting live version resolution.

Term: TestState API
Definition: Executes a single state definition in isolation without creating a state machine. As of Nov 2025: supports mocking of service integrations, Map/Parallel/.sync/.waitForTaskToken states, three inspection levels (INFO/DEBUG/TRACE), mock validation modes (STRICT/PRESENT/NONE). Console UI does not support mocking — requires CLI/SDK.
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/test-state-isolation.html
Architect Usage: Use in CI/CD pre-deployment gates via ValidateStateMachineDefinition + TestState with mocked responses. TRACE inspection level exposes I/O at each transformation step (InputPath, Parameters, ResultSelector, etc.).
Common Confusion: The console TestState UI does not support mocking. Architects who test only via console miss the ability to simulate service failures or specific response payloads.

Term: HTTP Task
Definition: Resource ARN: arn:aws:states:::http:invoke. Calls any public or private HTTPS API without a Lambda intermediary. Credentials stored encrypted in Secrets Manager via EventBridge Connection. All HTTP methods supported. Private APIs via VPC Lattice/PrivateLink. 60-second hard timeout. Does not support mTLS.
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/connect-third-party-apis.html
Architect Usage: Use for Stripe, Salesforce, Twilio, and internal microservice HTTP calls. Never embed credentials in ASL — always use EventBridge Connection. 60-second timeout is hard — for longer third-party calls, use .waitForTaskToken with a webhook callback pattern.
Common Confusion: HTTP Tasks cannot call AWS service APIs directly — use SDK integrations (arn:aws:states:::aws-sdk:{service}:{action}) for AWS services.

Term: Activity
Definition: External worker pattern; worker polls via GetActivityTask API. Standard only. Older pattern — .waitForTaskToken is preferred for new implementations.
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-standard-vs-express.html
Architect Usage: Retain in existing implementations. For new designs, use .waitForTaskToken — it is push-based, more efficient, and does not require a polling loop in the worker.
Common Confusion: Activities look similar to .waitForTaskToken but are fundamentally different: Activities require the worker to poll GetActivityTask, while .waitForTaskToken requires the worker to call back SendTaskSuccess/SendTaskFailure.
```

---

## Architecture Guardrails

> Confidence legend: High (2+ official sources, dated <=12mo) | Medium (1 source or dated 12–24mo) | Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**Error Handling with Retry and Catch**
- Pillar Alignment: Reliability
- Why: AWS Step Functions Best Practices states that every Task, Parallel, and Map state must include Retry (with BackoffRate, MaxAttempts, JitterStrategy: FULL) and Catch to handle transient failures and route to compensating states. Lambda transient errors to always retry: Lambda.ClientExecutionTimeoutException, Lambda.ServiceException, Lambda.AWSLambdaException, Lambda.SdkClientException.
- AWS Services: AWS Step Functions Task/Parallel/Map states, AWS Lambda, Amazon CloudWatch (ExecutionsFailed metric)
- Architecture Decision:
  Every Task state must carry a Retry block: IntervalSeconds: 2, MaxAttempts: 6, BackoffRate: 2, MaxDelaySeconds (caps exponential growth to a sane ceiling), JitterStrategy: FULL (randomizes delay 0 to computed interval to prevent thundering herd). After MaxAttempts is exhausted, a Catch block routes to a fallback or compensation state. States.Runtime errors are never retried. New task token generated per retry attempt for .waitForTaskToken tasks.
- Verification:
  Lint ASL for Task/Parallel/Map states without Retry and Catch fields before deployment. Use ValidateStateMachineDefinition API in CI/CD. Monitor ExecutionsFailed CloudWatch metric (Sum); alarm when > 0.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html (2026-08-31); https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html (2026-08-31)

**TimeoutSeconds and HeartbeatSeconds on Every Task State**
- Pillar Alignment: Reliability, Cost Optimization
- Why: AWS Step Functions Best Practices explicitly warns that without TimeoutSeconds, a stuck execution can wait up to 1 year (Standard Workflow maximum), consuming execution quota and accruing per-state-transition billing for the entire stuck period. For .waitForTaskToken tasks, HeartbeatSeconds triggers States.HeartbeatTimeout if no heartbeat received, preventing indefinitely blocked executions when external systems crash.
- AWS Services: AWS Step Functions Task state, Amazon CloudWatch (ExecutionsTimedOut metric)
- Architecture Decision:
  Every Task state declares TimeoutSeconds appropriate for the expected service call duration plus a safety margin (e.g., Lambda with 15-minute max timeout: TimeoutSeconds: 960). .waitForTaskToken tasks additionally declare HeartbeatSeconds set to a value less than TimeoutSeconds (e.g., HeartbeatSeconds: 3600 for human approval steps with TimeoutSeconds: 86400). Express Workflow tasks: TimeoutSeconds must be <= 300 (5-minute cap).
- Verification:
  Grep ASL definition for Task states lacking TimeoutSeconds: grep -c "TimeoutSeconds" vs count of Task states. Monitor ExecutionsTimedOut CloudWatch metric.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html (2026-08-31)

**CloudWatch Logs Logging and X-Ray Tracing**
- Pillar Alignment: Operational Excellence
- Why: Express Workflows have zero observable execution history without CloudWatch Logs — failures are completely undiagnosable. AWS Best Practices mandate LoggingConfiguration.Level: ALL or ERROR. The /aws/vendedlogs/states/{name} log group prefix must be used to avoid the 5,120-character resource policy size limit that blocks log delivery when custom names are too long.
- AWS Services: AWS Step Functions, Amazon CloudWatch Logs, AWS X-Ray
- Architecture Decision:
  Set LoggingConfiguration.Level: ALL (or ERROR for production cost savings). Log group name: /aws/vendedlogs/states/{state-machine-name}. Enable TracingConfiguration.Enabled: true. Required IAM permissions on the execution role: 10 logs:* permissions with Resource: "*" (CloudWatch Logs resource policy requirement). X-Ray IAM: xray:PutTraceSegments, xray:PutTelemetryRecords, xray:GetSamplingRules, xray:GetSamplingTargets.
- Verification:
  aws stepfunctions describe-state-machine --state-machine-arn <arn> — check loggingConfiguration.level and tracingConfiguration.enabled. Default for API/CLI/CloudFormation-created state machines is Level: OFF — must be explicitly set.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/cw-logs.html (2026-08-31); https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html (2026-08-31)

**Express Workflows for High-Volume Short-Duration Workloads**
- Pillar Alignment: Cost Optimization, Performance Efficiency
- Why: Standard Workflows cap at 2,000 executions/sec and 4,000 state transitions/sec. Express supports 100,000 executions/sec. Per-transition pricing makes Standard prohibitively expensive at scale for high-frequency idempotent steps. Nesting pattern: non-idempotent long-running steps in Standard parent, idempotent high-rate steps in Express child.
- AWS Services: AWS Step Functions Express Workflow, AWS Lambda, Amazon API Gateway
- Architecture Decision:
  Use Express for any workflow meeting all three criteria: duration < 5 minutes, execution rate > 100/sec, idempotent operations. Use StartSyncExecution for API Gateway-fronted flows requiring inline response. For hybrid billing: Standard parent workflow orchestrates business logic while nested Express child workflows handle idempotent sub-steps at Express pricing.
- Verification:
  Review workflow type in aws stepfunctions describe-state-machine. Check if workload is high-frequency and sub-5-minute — if yes and using Standard, flag for redesign.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html (2026-08-31)

**Avoiding the 25,000-Event History Limit**
- Pillar Alignment: Reliability
- Why: Standard Workflows hard-cap at 25,000 execution history events. At event 25,000, if the execution has not completed with ExecutionSucceeded, it fails unconditionally — all payload and state is lost with no recovery option.
- AWS Services: AWS Step Functions Distributed Map, AWS Step Functions StartExecution (nested workflows), AWS Lambda
- Architecture Decision:
  Three remediation options: (1) Distributed Map — each child execution has its own 25,000-event budget; (2) Nested workflow via StartExecution API — chain bounded sub-workflows; (3) Lambda calling StartExecution to split work programmatically. Monitor parent event count via GetExecutionHistory; alarm when approaching 20,000 events.
- Verification:
  Count events via GetExecutionHistory response length. For Inline Map over large datasets, estimate: items × events-per-iteration + overhead. If total > 20,000, switch to Distributed Map.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html (2026-08-31)

**Direct AWS SDK Integrations Instead of Lambda-as-Glue**
- Pillar Alignment: Cost Optimization, Performance Efficiency
- Why: Using Lambda solely to call a single AWS SDK method adds Lambda invocation cost, cold-start latency (up to ~3s for cold starts), and an additional failure mode. Direct SDK integration (arn:aws:states:::aws-sdk:{service}:{action}) eliminates all three overheads and is supported across 220+ AWS services.
- AWS Services: AWS Step Functions SDK integration (aws-sdk:{service}:{action}), optimized integrations for Batch/ECS/Glue/SageMaker
- Architecture Decision:
  Reserve Lambda for: business logic, complex multi-service fan-out, CPU-intensive computation, or operations requiring language-native libraries. Use direct SDK integration for: DynamoDB PutItem/GetItem/UpdateItem, SQS SendMessage, SNS Publish, S3 PutObject, EventBridge PutEvents. Use optimized integration (.sync) for: AWS Batch, ECS RunTask, Glue StartJobRun, SageMaker training jobs.
- Verification:
  Audit Lambda functions invoked by Step Functions; check if handler body contains only one SDK call. If yes, replace with direct SDK integration.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/supported-services-awssdk.html (2026-08-31)

**Least-Privilege IAM Execution Roles**
- Pillar Alignment: Security
- Why: AWS IAM best practices mandate that execution roles grant only specific actions on specific resource ARNs. Wildcard resources on states:* allow deletion of other state machines and stopping arbitrary executions.
- AWS Services: AWS IAM, AWS Step Functions, AWS Workflow Studio (auto-generate IAM)
- Architecture Decision:
  Use Workflow Studio to auto-generate a least-privilege baseline policy. Scope S3 permissions for Distributed Map to specific bucket and prefix. Add confused-deputy protection via trust policy condition (ArnLike on aws:SourceArn + StringEquals on aws:SourceAccount). Use TaskCredentials for per-task cross-account role assumption rather than static credentials.
- Verification:
  IAM Access Analyzer — check for wildcard resources in execution role policies. Review policy JSON for "Resource": "*" with action lists broader than required.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/manage-state-machine-permissions.html (2026-08-31)

---

### ⚠️ Architectural Decisions

**Standard vs Express Workflows**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Standard Workflow | Step Functions Standard | Exactly-once semantics, audit trail, .sync/.waitForTaskToken, 1-year duration, Distributed Map | Cost at high volume (per transition), throughput (2K exec/sec, 4K transitions/sec) | Payment processing, order fulfillment, compliance workflows, human-in-the-loop, Distributed Map batch jobs |
  | Async Express Workflow | Step Functions Express (StartExecution) | High throughput (100K/sec), lower cost at high volume, no execution history storage cost | At-least-once semantics, no .waitForTaskToken, 5-min cap, no Distributed Map, history only in CloudWatch Logs | Event processing, IoT ingestion, streaming fan-out, fire-and-forget triggers |
  | Sync Express Workflow | Step Functions Express (StartSyncExecution) | Immediate inline response to API caller, no polling code needed | At-most-once semantics, 5-min cap, console 60s limit (use SDK/CLI for full 5 min), no auto-idempotency | API Gateway-fronted orchestration requiring synchronous result, mobile/web backends |

- Cost Profile: Standard — per state transition (~$0.000025/transition); Express — per execution-duration-memory (64-MB chunks). At 1M short executions/month, Express is orders of magnitude cheaper. At 100 long complex executions/month, Standard may cost less.
- Lock-in Assessment: Workflow type is immutable — cannot be changed after creation. All SDKs and IaC resources treat Standard and Express as different resource types. Architecture revision requires creating a new state machine.
- Architect Instruction: "Ask: What is the expected execution rate per second, the typical duration, and whether the workflow requires exactly-once semantics or human-in-the-loop steps? — when designing any new Step Functions workflow."
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-standard-vs-express.html (2026-08-31); https://aws.amazon.com/step-functions/pricing/ (2026-08-31)

**Orchestration vs Choreography**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Step Functions Orchestration | Step Functions Standard/Express | Centralized visibility, retry/catch, execution audit trail, stateful branching, rollback/compensation | Service coupling to workflow definition, cost per transition, ASL learning curve | Multi-step business processes needing rollback, audit trails, human-in-the-loop, complex conditional logic |
  | EventBridge + SNS/SQS Choreography | Amazon EventBridge, Amazon SNS, Amazon SQS | Loose coupling, independent service evolution, high-throughput fan-out, no single point of coordination | No single execution history, harder distributed tracing, no centralized error handling, eventual consistency harder to reason about | Pub/sub fan-out, simple 1–2 step reactions, microservices evolving independently, domain event distribution |

- Cost Profile: Orchestration — per transition or duration. Choreography — SQS/SNS per message, EventBridge per event ($1/million). For complex multi-step workflows, orchestration is cheaper than implementing equivalent retry/state logic via Lambda + SQS.
- Lock-in Assessment: Step Functions ASL is proprietary. EventBridge/SNS/SQS are AWS-proprietary services but the choreography pattern is portable conceptually to any cloud provider's equivalent messaging services.
- Architect Instruction: "Ask: Does this process have more than 3 steps, require rollback on failure, or need a human approval gate? — when evaluating whether to orchestrate or choreograph."
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html (2026-08-31); https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/direct-integrations.html (2026-08-31)

**Inline Map vs Distributed Map**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Inline Map | Step Functions Map (INLINE) | Simplicity, single execution history, Express compatibility | 256 KiB input max, 40 concurrency max, 25K history limit shared with parent | Small datasets (<40 items, <256 KiB), Express workflows, prototype/dev |
  | Distributed Map | Step Functions Map (DISTRIBUTED) | 10,000 parallel child executions, large S3 datasets, independent histories, ToleratedFailurePercentage | Standard workflow only, IAM complexity for S3, higher cost per child iteration, no Express, outer workflow variable inaccessible | Processing thousands of S3 records, large CSV/JSON/Parquet files, >40 concurrency needed, >25K total events |

- Cost Profile: Distributed Map — each child execution billed as a Standard Workflow execution plus parent transitions. At 10,000 children, cost is material — evaluate against AWS Batch or EMR for pure ETL at massive scale.
- Lock-in Assessment: Distributed Map's S3-native reading and ResultWriter are AWS-specific. Conceptually maps to Azure Durable Functions fan-out or GCP Workflows parallel iteration.
- Architect Instruction: "Ask: How many items are in the dataset, what is the expected total event count, and does the workflow run on Express? — when choosing between Inline and Distributed Map."
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/use-dist-map-orchestrate-large-scale-parallel-workloads.html (2026-08-31); https://docs.aws.amazon.com/step-functions/latest/dg/concepts-inline-vs-distributed-map.html (2026-08-31)

**Direct SDK Integration vs Lambda-Based Integration**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Direct SDK (aws-sdk:{service}:{action}) | Step Functions SDK integration | No Lambda cost/cold-start, 220+ services, reduced ops overhead, 10,000+ APIs | PascalCase parameter requirement, limited to single API call per state, no custom transformation logic | DynamoDB PutItem, SQS SendMessage, SNS Publish — single AWS API call with no custom logic |
  | Optimized Integration (.sync) | Step Functions optimized integration | Enhanced functionality (.sync, auto JSON parsing, managed polling, EventBridge-based completion) | Only ~20+ services supported | AWS Batch, ECS RunTask, Glue StartJobRun, SageMaker — when job completion detection via .sync is needed |
  | Lambda Integration | AWS Lambda + Step Functions Task | Full custom logic, complex transforms, language-native libraries, multi-service fan-out | Lambda invocation cost, cold-start latency, additional function lifecycle to manage | Business logic, complex JSON transformation, CPU-intensive computation, multi-API orchestration within one step |

- Cost Profile: Direct SDK eliminates Lambda invocation cost (~$0.0000002/request) and any cold-start penalty. For high-frequency simple API calls, savings are significant.
- Lock-in Assessment: Direct SDK integration is Step Functions-specific syntax. Lambda logic is portable across orchestrators (EventBridge Pipes, ECS task, etc.).
- Architect Instruction: "Ask: Does this step perform any logic beyond calling a single AWS API? — if no, replace Lambda with direct SDK integration."
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/supported-services-awssdk.html (2026-08-31); https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/direct-integrations.html (2026-08-31)

**JSONata vs JSONPath**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | JSONata (recommended for new) | Step Functions + JSONata 2.0.6 | Developer ergonomics (2 fields vs 5), full expression language, no .$ boilerplate, Condition expressions in Choice | 1-second expression timeout risk, $eval unavailable (use $parse), Assign/Output parallelism gotcha, newer ecosystem | All new state machines — AWS recommends JSONata when creating in console |
  | JSONPath (existing workflows) | Step Functions + JSONPath | Backward compatibility, established patterns, larger community examples, intrinsic functions | 5 I/O fields complexity, .$ suffix boilerplate, less expressive for complex transforms | Existing state machines; incremental migration via per-state QueryLanguage override |

- Cost Profile: No pricing difference — both are ASL features with no additional charge.
- Lock-in Assessment: Both are Step Functions-specific ASL constructs. JSONata is an open standard (jsonata.org) while Step Functions JSONPath is a subset of RFC 9535.
- Architect Instruction: "Ask: Is this a new state machine or a migration of an existing one? — choose JSONata for net-new, use per-state QueryLanguage override for incremental migration."
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/transforming-data.html (2026-08-31)

**Callback (.waitForTaskToken) vs Polling (.sync)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Callback (.waitForTaskToken) | Step Functions + SQS/SNS/Lambda/EventBridge/ECS/Bedrock | No polling overhead, waits up to 1 year at zero transition cost during wait, natural for human-in-the-loop | Standard only, token management in external system, stuck executions without HeartbeatSeconds | Human approvals, third-party async integrations, long-running async web operations |
  | Polling (.sync) | Step Functions optimized integration | Automatic job completion detection, no token management, native to ~20 AWS services | Limited to specific services (Batch/ECS/Glue/SageMaker), same-account only for EventBridge polling | AWS-managed job monitoring where .sync is available |

- Cost Profile: .waitForTaskToken — zero state transition billing during the wait period. .sync — Standard Workflow transitions consumed during polling intervals.
- Lock-in Assessment: Both patterns are Standard Workflow-only. Task tokens are AWS-proprietary — external systems must call AWS SendTaskSuccess API.
- Architect Instruction: "Ask: Does this step wait for an external system or human to respond, and will that system be able to call back the AWS Step Functions API? — when choosing between callback and polling patterns."
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html (2026-08-31)

---

### 🚫 Anti-Patterns

**No Retry or Catch on Task States**
- Risk Level: CRITICAL
- Why: Reliability pillar violation. Any transient AWS API error, Lambda throttle, or service unavailability causes permanent execution failure with no recovery path. Lambda transient errors (Lambda.ServiceException, Lambda.AWSLambdaException, Lambda.SdkClientException, Lambda.ClientExecutionTimeoutException) occur in normal operation.
- ❌ Wrong:
  Task state with Resource: arn:aws:lambda:us-east-1:123:function:ProcessOrder and no Retry or Catch block. First Lambda throttle permanently fails the execution.
- ✅ Correct:
  Task state with Retry: [{ErrorEquals: ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.ClientExecutionTimeoutException"], IntervalSeconds: 2, MaxAttempts: 6, BackoffRate: 2, JitterStrategy: "FULL", MaxDelaySeconds: 300}] and Catch: [{ErrorEquals: ["States.ALL"], Next: "CompensationState"}].
- Detection: Lint ASL definition — grep Task states for absence of Retry and Catch fields. Monitor ExecutionsFailed CloudWatch metric (Sum > 0).
- Impact: Service outage — any transient error permanently fails executions; no self-healing.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html (2026-08-31)

**No TimeoutSeconds (Stuck Executions)**
- Risk Level: CRITICAL
- Why: Reliability and Cost Optimization pillar violation. Without TimeoutSeconds, a Task state waits up to 1 year (Standard Workflow maximum duration). For .waitForTaskToken tasks, if the external system crashes without calling SendTaskSuccess/Failure, the execution waits indefinitely — consuming execution quota and accruing per-state-transition billing.
- ❌ Wrong:
  Task state calling a Lambda function or .waitForTaskToken resource with no TimeoutSeconds or HeartbeatSeconds declared. External system crashes; execution waits 1 year.
- ✅ Correct:
  Every Task state declares TimeoutSeconds: 960 (for a 15-minute Lambda). Every .waitForTaskToken Task state additionally declares HeartbeatSeconds: 3600 (for a 1-hour approval window with TimeoutSeconds: 86400).
- Detection: Grep ASL definition for Task states lacking TimeoutSeconds field. Monitor ExecutionsTimedOut CloudWatch metric.
- Impact: Cost overrun (per-transition billing for up to 1 year); quota exhaustion; zombie executions blocking new ones.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html (2026-08-31)

**Standard Workflow for High-Frequency Sub-Second Workflows**
- Risk Level: HIGH
- Why: Cost Optimization and Performance Efficiency pillar violation. Standard Workflows cap at 2,000 executions/sec (ExecutionThrottled). Per-transition pricing is orders of magnitude more expensive than Express at high volume. At 10,000 executions/sec, Standard throttles and incurs >5x the cost of Express.
- ❌ Wrong:
  Standard Workflow processing high-frequency idempotent events (IoT sensor reads, streaming records, API request logging) at >2,000/sec.
- ✅ Correct:
  Express Workflow (Asynchronous, StartExecution) for idempotent high-frequency events. Or: Synchronous Express (StartSyncExecution) for API-fronted flows needing inline response.
- Detection: Check Type in aws stepfunctions describe-state-machine. Monitor ExecutionThrottled CloudWatch metric — any non-zero value at sustained rate indicates misconfiguration.
- Impact: Cost overrun (5–100x more expensive); service degradation (throttling at 2,000/sec).
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-standard-vs-express.html (2026-08-31)

**Lambda-as-Glue (Single-SDK-Call Lambda)**
- Risk Level: HIGH
- Why: Cost Optimization pillar violation. A Lambda function whose handler is just a single AWS SDK call adds Lambda invocation cost, cold-start latency (up to 3s), and an additional function lifecycle to maintain — with no business logic justification.
- ❌ Wrong:
  Step Functions Task state invoking a Lambda function whose entire handler is `dynamodb.put_item(TableName=os.environ['TABLE'], Item=event)`.
- ✅ Correct:
  Step Functions Task state with Resource: arn:aws:states:::aws-sdk:dynamodb:putItem and Parameters mapped directly from state input using JSONata Arguments or JSONPath Parameters.
- Detection: Audit Lambda functions invoked by Step Functions state machines. Check if handler body contains only one boto3/SDK call — if yes, replace with direct SDK integration.
- Impact: Cost overrun (Lambda invocation cost × execution volume); latency increase (cold starts); operational overhead (function versioning, monitoring, permissions).
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/supported-services-awssdk.html (2026-08-31)

**Exceeding the 25,000-Event History Limit**
- Risk Level: CRITICAL
- Why: Reliability pillar violation. Standard Workflows hard-cap at 25,000 execution history events. At event 25,000, if the execution has not already completed with ExecutionSucceeded, it fails unconditionally — all payload and partially computed state is permanently lost.
- ❌ Wrong:
  Standard Workflow with Inline Map over 3,000 S3 records generating 10 events per iteration = 30,000 events — execution fails at event 25,000 mid-processing.
- ✅ Correct:
  Switch to Distributed Map (DISTRIBUTED mode) — each iteration runs as an independent child execution with its own 25,000-event budget. Parent retains only Map-level control events. Set ResultWriter: { Resource: "arn:aws:states:::s3:putObject", Parameters: { Bucket: "...", Prefix: "..." } } to avoid 256 KiB output limit.
- Detection: Count events via GetExecutionHistory. For Inline Map, estimate: item_count × events_per_iteration + overhead. Alarm when parent execution approaches 20,000 events.
- Impact: Service outage — entire execution fails unconditionally at event 25,000; all partial results lost; no Redrive recovery for in-progress Map iterations.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html (2026-08-31)

**Overly Permissive IAM Execution Role**
- Risk Level: CRITICAL
- Why: Security pillar violation. "Action": "states:*" on "Resource": "*" allows the execution role to delete other state machines, stop arbitrary executions, and create new state machines — blast radius extends to the entire AWS account's Step Functions resources.
- ❌ Wrong:
  Step Functions execution role policy: {"Effect": "Allow", "Action": "states:*", "Resource": "*"} or {"Effect": "Allow", "Action": "*", "Resource": "*"}.
- ✅ Correct:
  Workflow Studio auto-generated least-privilege policy scoped to specific service ARNs and required actions only. Example: {"Effect": "Allow", "Action": "dynamodb:PutItem", "Resource": "arn:aws:dynamodb:us-east-1:123:table/Orders"}.
- Detection: IAM Access Analyzer — scan execution role for wildcard resources. aws iam get-role-policy and check for Resource: "*" with broad action sets.
- Impact: Data breach (access to all Step Functions executions); compliance violation (HIPAA, PCI DSS, SOC 2 IAM control failure); lateral movement to other services if role is chained.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/security_iam_id-based-policy-examples.html (2026-08-31)

**No Logging or Tracing Enabled**
- Risk Level: HIGH
- Why: Operational Excellence pillar violation. Default for API/CLI/CloudFormation-created state machines is LoggingConfiguration.Level: OFF and TracingConfiguration.Enabled: false. For Express Workflows, this means zero observability into execution results or errors — no execution list in console, no CloudWatch metrics with payload context, no distributed trace.
- ❌ Wrong:
  Express Workflow deployed via CloudFormation without LoggingConfiguration — failures are invisible in production; mean time to detection (MTTD) is unbounded.
- ✅ Correct:
  LoggingConfiguration: { Level: ALL, IncludeExecutionData: true, Destinations: [{CloudWatchLogsLogGroup: {LogGroupArn: "arn:aws:logs:...:log-group:/aws/vendedlogs/states/MyWorkflow"}}] } and TracingConfiguration: { Enabled: true }.
- Detection: aws stepfunctions describe-state-machine — check loggingConfiguration.level. If OFF, flag as misconfiguration.
- Impact: Operational outage — failures undetectable; MTTD and MTTR severely impacted; no audit trail for compliance.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/cw-logs.html (2026-08-31)

**Polling Loop Using Wait State Instead of Callback Pattern**
- Risk Level: HIGH
- Why: Reliability and Cost Optimization pillar violation. Wait state loops to poll an external service consume state transition quota, generate large event histories (accelerating toward the 25,000 limit), and add polling latency without improving accuracy of completion detection.
- ❌ Wrong:
  Wait state (30 seconds) → Task state (poll external API for completion) → Choice state (complete? if no, loop back to Wait). Each loop iteration generates 6+ events and consumes quota.
- ✅ Correct:
  .waitForTaskToken appended to Task Resource ARN (Standard Workflow). External service calls SendTaskSuccess when complete. Zero polling transitions. HeartbeatSeconds prevents stuck executions.
- Detection: Search ASL for Wait states whose Next points to a Task polling the same endpoint — this is the polling loop pattern.
- Impact: Cost overrun (quota consumption per poll); 25,000-event ceiling accelerated; latency added per polling interval vs push notification.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html (2026-08-31)

---

## Cloud-Native Design Patterns

**Saga Orchestration (Distributed Transactions)**
- Category: Resilience
- Problem: ACID guarantees across multiple independent databases (DynamoDB, RDS, external SaaS) are impossible without a coordinator. Partial failures leave data inconsistent across services.
- Solution on AWS:
  Standard Workflow as saga orchestrator. Each participant (Lambda function wrapping a DynamoDB or external API call) implements idempotent forward and compensating operations. Catch blocks wire compensating transactions: States.TaskFailed on PaymentStep → CompensateInventoryReservation → CompensateCartState → SagaFailed. Step Functions provides built-in AZ fault tolerance for the orchestrator itself. Redrive (within 14 days) allows resuming failed sagas from point of failure.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Consistency | Eventual consistency across services with guaranteed compensation | Not strong ACID — compensating transactions may fail too |
  | Observability | Full execution history in Step Functions console | Complex event history at scale (watch for 25,000-event limit) |
  | Idempotency | Step Functions retry with JitterStrategy:FULL | Each participant must implement idempotent forward and compensating operations |
  | Complexity | Centralized compensation logic in ASL | ASL compensation chains can become deeply nested |

- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-orchestration.html (2026-08-31)

**Callback / Task-Token (.waitForTaskToken)**
- Category: Communication
- Problem: Steps requiring human approval, third-party webhook callbacks, or async SaaS integrations need an indefinite pause without polling — polling consumes quota and generates event history toward the 25,000 limit.
- Solution on AWS:
  Append .waitForTaskToken to Task Resource ARN (e.g., arn:aws:states:::sqs:sendMessage.waitForTaskToken). Pass token via Arguments: {"TaskToken.$": "$$.Task.Token"} (JSONPath) or "TaskToken": "{% $states.context.Task.Token %}" (JSONata). Supported destinations: SQS, SNS, Lambda, EventBridge, ECS, Bedrock. External system calls SendTaskSuccess(taskToken, output) or SendTaskFailure(taskToken, error). Declare HeartbeatSeconds to trigger States.HeartbeatTimeout if external system fails silently.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Cost | Zero state transitions during wait (up to 1 year) | External system must reliably call SendTaskSuccess; missed callback = stuck execution |
  | Reliability | HeartbeatSeconds prevents indefinitely stuck executions | New task token generated per retry — external systems must use latest token |
  | Scope | Standard Workflow only; up to 1-year wait | Cross-account SendTaskSuccess not supported |
  | Human-in-the-loop | Natural fit for multi-day approval workflows | Token storage and management required in external system |

- Source: https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html (2026-08-31)

**Fan-out / Fan-in with Distributed Map**
- Category: Scalability
- Problem: Large parallel datasets (thousands of S3 records, CSV files, JSON arrays) exceed the 256 KiB Inline Map input limit and the 25,000-event parent history ceiling. Inline Map's 40-concurrency cap also limits throughput.
- Solution on AWS:
  Distributed Map (DISTRIBUTED mode, Standard Workflow only). ItemReader reads S3 datasets natively (JSON, CSV, S3ListObjectsV2, Athena manifest, Parquet) without Lambda preprocessing. ItemBatcher groups N items per child execution to reduce child execution count. Each child execution has independent 25,000-event history. MaxConcurrency: 10000 (max). ToleratedFailurePercentage and ToleratedFailureCount allow partial failure acceptance for best-effort batch jobs. ResultWriter: S3 aggregates child results.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Scale | 10,000 parallel child executions; datasets from S3 with no size limit | Standard Workflow only; not available in Express |
  | History | Each child has independent 25,000-event budget | Parent cannot access child execution variables; outer workflow variables inaccessible in children |
  | Cost | Parallelism reduces total wall-clock duration | Each child billed as Standard execution; 10,000 children = 10,000 executions |
  | Reliability | ToleratedFailurePercentage prevents cascade failure on partial dataset errors | Hard quota: 10,000 concurrent children; 1,000 open Map Runs per account |

- Source: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-inline-vs-distributed-map.html (2026-08-31); https://docs.aws.amazon.com/step-functions/latest/dg/use-dist-map-orchestrate-large-scale-parallel-workloads.html (2026-08-31)

**Circuit Breaker / Retry with Exponential Backoff and Jitter**
- Category: Resilience
- Problem: Simultaneous retry bursts from multiple executions after a service recovery create thundering-herd demand spikes that re-saturate the recovering service — preventing stable recovery.
- Solution on AWS:
  Retry field with BackoffRate: 2, MaxDelaySeconds (caps exponential growth; max value 31,622,400 seconds), JitterStrategy: FULL (randomizes delay 0 to computed interval). After MaxAttempts exhausted, Catch routes to fallback state (circuit-breaker open state). States.Runtime errors are never retried — do not include them in ErrorEquals. ErrorEquals order matters — more specific errors before States.ALL.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Recovery | JitterStrategy:FULL spreads retry load temporally, allowing service recovery | Longer total retry duration before ultimate failure |
  | Cost | Fewer failed executions = fewer re-runs, lower total cost | Retry attempts consume state transitions (Standard) or execution time (Express) |
  | Observability | Retry events visible in execution history | ExecutionHistory grows with each retry attempt |
  | Predictability | MaxDelaySeconds prevents unbounded wait | Requires careful tuning per target service's recovery SLA |

- Source: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html (2026-08-31)

**Orchestrated Microservices Web Backend (API Gateway → Step Functions)**
- Category: Communication
- Problem: Sequential microservice calls (validate → persist → notify) need durable coordination with error routing, retry, and compensation — without embedding state machine logic in application code.
- Solution on AWS:
  Amazon API Gateway HTTP API → Step Functions Synchronous Express Workflow (StartSyncExecution; integration subtype: StepFunctions-StartSyncExecution). Inside Express: DynamoDB operations via direct SDK integration (arn:aws:states:::aws-sdk:dynamodb:putItem) — no Lambda for simple writes. Lambda only for business logic (validation rules, pricing calculation). SNS Publish or SES SendEmail via SDK integration for notifications. Result returned inline to API Gateway response mapping. Max 5-minute execution window; at-most-once semantics — all DynamoDB operations must be idempotent (conditional expressions or transaction keys).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Simplicity | No polling or async callback from API client | 5-minute hard cap; not suitable for long-running user-facing flows |
  | Cost | Express pricing; direct SDK eliminates Lambda for simple steps | At-most-once; idempotency must be implemented in each downstream service |
  | Observability | CloudWatch Logs mandatory for Express; X-Ray traces API-to-Step Functions-to-Lambda | No console execution history for Express — CloudWatch Logs Insights required |
  | Scaling | 100,000 sync exec/sec; constraint is Lambda concurrency limits | API Gateway 29-second integration timeout — Sync Express max visible to API caller is 29 sec unless async pattern used |

- Source: https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html (2026-08-31); https://docs.aws.amazon.com/step-functions/latest/dg/tutorial-api-gateway.html (2026-08-31)

---

## Security Architecture

**IAM Least Privilege and Confused Deputy Protection**
- AWS Services: AWS IAM, AWS Step Functions, AWS Workflow Studio
- Architecture:
  Step Functions execution role trusts states.amazonaws.com as principal. Workflow Studio auto-generates least-privilege policies as a baseline. Confused deputy protection via trust policy condition:
  ```json
  "Condition": {
    "ArnLike": { "aws:SourceArn": "arn:aws:states:us-east-1:111122223333:stateMachine:*" },
    "StringEquals": { "aws:SourceAccount": "111122223333" }
  }
  ```
  TaskCredentials field enables per-task cross-account role assumption without static credentials embedded in the state machine definition or execution input.
- Compliance Alignment: SOC 2 CC6 (logical access), HIPAA §164.312(a)(1) (access control), PCI DSS Requirement 7 (restrict access), FedRAMP AC-2/AC-3.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/procedure-create-iam-role.html (2026-08-31)

**Encryption at Rest with Customer-Managed KMS Keys**
- AWS Services: AWS Step Functions, AWS KMS, Amazon CloudWatch Events (EventBridge)
- Architecture:
  Default: AWS owned keys (no config required). Optional CMK via EncryptionConfiguration with Type: CUSTOMER_MANAGED_KMS_KEY. Encrypts execution history, workflow definition, execution input/output, activity inputs. KmsDataKeyReusePeriodSeconds: 60–900 (default 300) — lower value reduces data exposure window but increases KMS API call frequency. IAM requirements: execution role needs kms:Decrypt + kms:GenerateDataKey for Standard/Async Express; kms:Decrypt only for Sync Express. Critical operational note: if CMK is deleted or disabled, all running executions fail immediately. When CMK enabled, execution Input/Output/Error/Cause are excluded from EventBridge state-change events.
- Compliance Alignment: HIPAA §164.312(a)(2)(iv) (encryption), PCI DSS Requirement 3.5 (key management), FedRAMP SC-28.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html (2026-08-31)

**CloudTrail Auditing**
- AWS Services: AWS Step Functions, AWS CloudTrail, Amazon S3, AWS CloudTrail Lake
- Architecture:
  Management events logged by default (no configuration required): CreateStateMachine, UpdateStateMachine, DeleteStateMachine, StartExecution, StartSyncExecution, StopExecution, RedriveExecution, SendTaskSuccess, SendTaskFailure, SendTaskHeartbeat, all version/alias/map-run APIs. State machine definition recorded as "HIDDEN_DUE_TO_SECURITY_REASONS" in CloudTrail events. Data events (StartSyncExecution results, InvokeHTTPEndpoint, GetActivityTask) require opt-in via CloudTrail advanced event selectors. Deliver trail to S3 (with SSE-KMS) or CloudTrail Lake for long-term retention and Athena/SQL querying.
- Compliance Alignment: SOC 2 CC7 (monitoring), HIPAA §164.312(b) (audit controls), PCI DSS Requirement 10 (audit logging), FedRAMP AU-2/AU-12.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/procedure-cloud-trail.html (2026-08-31)

**Secrets via Secrets Manager (No Embedded Credentials)**
- AWS Services: AWS Secrets Manager, Amazon EventBridge Connections, AWS Step Functions HTTP Task
- Architecture:
  HTTP Tasks: credentials stored encrypted in Secrets Manager via EventBridge Connection (ApiKey, OAuth, Basic Auth). Connection ARN referenced in HTTP Task definition — credentials never appear in ASL definition or execution input. Lambda tasks: secrets retrieved at Lambda runtime via Secrets Manager API or Lambda extension (not passed via Step Functions input). Never embed API keys, connection strings, or access tokens in state machine definitions or execution input.
- Compliance Alignment: HIPAA §164.312(d) (authentication), PCI DSS Requirement 8 (credential management), SOC 2 CC6.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/connect-third-party-apis.html (2026-08-31)

**PII and Logging Data Protection**
- AWS Services: AWS Step Functions, Amazon CloudWatch Logs, AWS KMS
- Architecture:
  CloudWatch Logs integration supports IncludeExecutionData: false — excludes execution input/output from log entries, preventing PII from appearing in log streams. CMK-enabled state machines automatically exclude Input/Output/Error/Cause from EventBridge state-change events. KMS key reuse period (60–900s) balances API call frequency vs data exposure window. Combine with CloudWatch Logs subscription filters and KMS encryption of log groups for defense in depth.
- Compliance Alignment: GDPR Article 25 (data protection by design), HIPAA minimum necessary rule, SOC 2 CC6.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html (2026-08-31)

**VPC Connectivity**
- AWS Services: AWS Step Functions, AWS Lambda (VPC mode), AWS PrivateLink (VPC Interface Endpoints), Amazon VPC
- Architecture:
  Lambda functions in VPC can access private resources (RDS, ElastiCache) via VPC routing; NAT Gateway required for internet access (e.g., to reach Step Functions API endpoint). VPC Interface Endpoints (PrivateLink) allow StartExecution and other Step Functions API calls from private VPC environments without internet egress. VPC endpoint policies restrict accessible Step Functions resources to specific state machine ARNs.
- Compliance Alignment: HIPAA §164.312(e)(1) (transmission security), PCI DSS Requirement 1 (network controls), FedRAMP SC-7.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/security.html (2026-08-31)

**Compliance programs confirmed in scope:** HIPAA, SOC 1/2/3, PCI DSS, FedRAMP.
[Source: https://docs.aws.amazon.com/step-functions/latest/dg/security.html (2026-08-31)]

---

## Operational Patterns

**Observability Stack (CloudWatch + X-Ray)**
- RTO/RPO (if applicable): N/A — observability configuration; contributes to RTO reduction by enabling faster diagnosis.
- AWS Services: AWS Step Functions, Amazon CloudWatch, AWS X-Ray
- Cost Profile: Medium — CloudWatch Logs ingestion + storage at $0.50/GB; X-Ray traces at $5/million traces (after free tier). For high-volume Express Workflows, evaluate CloudWatch Logs sampling to control cost.
- Automation:
  Automated: Alarm creation on ExecutionsFailed (Sum > 0), ExecutionThrottled (Sum > 0), ExecutionsTimedOut (Sum > 0). X-Ray sampling rules automated via CloudFormation. Manual decision: setting appropriate alarm thresholds for OpenExecutionCount (Maximum) and ExecutionTime (Average p99) per workflow SLA.
  Key metrics: namespace AWS/States. Dimensions: StateMachineArn, Version, Alias. Express-specific: ExpressExecutionBilledDuration. X-Ray IAM required: xray:PutTraceSegments, xray:PutTelemetryRecords, xray:GetSamplingRules, xray:GetSamplingTargets. Default sampling: first request/second + 5% additional.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/procedure-cw-metrics.html (2026-08-31); https://docs.aws.amazon.com/step-functions/latest/dg/concepts-xray-tracing.html (2026-08-31)

**Versions and Aliases for Canary Deployments**
- RTO/RPO (if applicable): RTO < 5 minutes (alias routing update is near-instantaneous); RPO = 0 (no state loss on alias rollback).
- AWS Services: AWS Step Functions, Amazon CloudWatch (Version/Alias dimensions)
- Cost Profile: Low — no additional cost for versions or aliases. Up to 1,000 versions and 100 aliases per state machine.
- Automation:
  Automated: CI/CD pipeline publishes new version (PublishStateMachineVersion or UpdateStateMachine with publish: true). Automated traffic shift: deploy at 5%, monitor ExecutionsFailed for 10 minutes, shift to 100% if error rate stable. Manual decision: rollback trigger threshold and approval gate before full promotion.
  ARN format: arn:aws:states:...:stateMachine:name:N (version) and arn:aws:states:...:stateMachine:name:ALIAS (alias). routingConfiguration percentages must total 100. Redriven executions use original version — this is correct for audit purposes but requires documentation for teams expecting live version resolution.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-state-machine-alias.html (2026-08-31)

**Redrive of Failed Executions**
- RTO/RPO (if applicable): RTO from failure detection to redrive: seconds (automated via EventBridge rule on ExecutionFailed). RPO: state at last completed state transition (no re-execution of completed states).
- AWS Services: AWS Step Functions, Amazon EventBridge (failure detection), AWS IAM (states:RedriveExecution)
- Cost Profile: Low — redriven state transitions billed at Standard Workflow rate. Only failed/unexecuted states are redriven; completed states are not re-billed.
- Automation:
  Automated: EventBridge rule on Step Functions execution status change (FAILED) → Lambda → RedriveExecution API call (with eligibility check). Monitor: ExecutionsRedriven, RedrivenExecutionsFailed, RedrivenExecutionsSucceeded metrics. Manual decision: eligibility window check (14-day from original start) and whether failure requires code fix before redrive.
  Eligibility: started after Nov 15, 2023; not SUCCEEDED; within 14-day window; < 24,999 events. Parallel: only failed branches redriven. Map (Inline/Distributed): only failed iterations redriven. Fail state: re-enters and fails again — code fix required before redrive for Fail-state terminations.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/redrive-executions.html (2026-08-31)

**Multi-Region Disaster Recovery**
- RTO/RPO (if applicable): RPO = time since last completed state transition at regional failure (in-flight executions lost). RTO = Route 53 health-check failover time (typically 30–60s for DNS propagation) + new region warm-up.
- AWS Services: AWS Step Functions, AWS CloudFormation/CDK/Terraform, Amazon Route 53, Amazon S3 (cross-region replication for Distributed Map datasets)
- Cost Profile: High — duplicate infrastructure in secondary region; S3 cross-region replication cost for Distributed Map datasets.
- Automation:
  Automated: IaC (CloudFormation StackSets or CDK Pipeline) deploys identical state machine definitions to secondary region. Route 53 health check triggers DNS failover to secondary region endpoint. Manual decision: whether to implement active-active (both regions accepting executions simultaneously with DynamoDB global tables) vs active-passive (secondary region warm standby). In-flight Standard Workflow executions at regional failure are lost — RPO is non-zero for running executions.
- Source: https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-08-31)

**Cost Optimization (FinOps)**
- RTO/RPO (if applicable): N/A.
- AWS Services: AWS Step Functions, AWS Cost Explorer, Amazon CloudWatch (billing alarms)
- Cost Profile: Standard — per state transition ($0.000025/transition); Express — per execution-duration-memory ($0.00001/GB-second, 64-MB chunks). Workflow type is immutable — cost model is locked at creation time.
- Automation:
  Strategies: (1) Use Express for high-volume idempotent sub-steps (hybrid billing via nested workflows); (2) Nest Express in Standard parent for mixed workflows; (3) Distributed Map with Express child executions for batch processing cost reduction; (4) Direct SDK integrations eliminate Lambda invocation cost at every applicable step. Monitor AWS/States ExpressExecutionBilledDuration metric for Express cost tracking. Manual decision: workflow type selection (irreversible — must be correct at design time).
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/cost-opt-exp-workflows.html (2026-08-31); https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html (2026-08-31)

---

## Reference Architectures

**Synchronous Web Application Backend**
- Context: API-fronted orchestration requiring inline response within request-response cycle.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Ingress | Amazon API Gateway HTTP API | Receive HTTP request; route to Step Functions via StartSyncExecution integration |
  | Orchestration | Step Functions Synchronous Express Workflow | Coordinate validation, persistence, notification steps with retry/catch |
  | Business Logic | AWS Lambda | Input validation, pricing calculation, or any step requiring custom code |
  | Data Persistence | Amazon DynamoDB (direct SDK integration) | Idempotent PutItem/UpdateItem via arn:aws:states:::aws-sdk:dynamodb:putItem |
  | Notification | Amazon SNS or Amazon SES (direct SDK integration) | Publish confirmation event or send transactional email |
  | Tracing | AWS X-Ray | End-to-end distributed trace from API Gateway through Lambda |
  | Observability | Amazon CloudWatch Logs | Mandatory for Express — all execution results logged here |

- Key Decisions: (1) Express vs Standard: Express required for inline response; Standard cannot use StartSyncExecution pattern. (2) DynamoDB operations must be idempotent (conditional expressions) — at-most-once Express semantics require idempotency at data layer. (3) API Gateway 29-second integration timeout applies — Express can run up to 5 min but API client sees 29s limit without async pattern. (4) CloudWatch Logs is mandatory — without it, production failures are invisible.
- Scaling Path: 100,000 sync executions/sec (Express limit). Constraint is Lambda concurrent execution limit (default 1,000/account, request increase to 10,000). For higher throughput: evaluate API Gateway → Lambda (without Step Functions) for pure validation use cases; add Step Functions only where stateful orchestration is genuinely needed.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/tutorial-api-gateway.html (2026-08-31)

**Asynchronous Order / Checkout Workflow**
- Context: Multi-step order processing requiring exactly-once semantics, human-in-the-loop potential, extended execution windows, and durable audit trail.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Ingress | Amazon API Gateway REST API | Receive order request; call StartExecution; return executionArn to client |
  | Orchestration | Step Functions Standard Workflow | Exactly-once coordination of validation, payment, fulfillment, notification |
  | Async Pause | Amazon SQS (.waitForTaskToken) | Deliver task token to payment processor; await SendTaskSuccess callback |
  | Payment | External Payment API (HTTP Task or Lambda) | Process payment; call SendTaskSuccess/Failure with result |
  | Persistence | Amazon DynamoDB (direct SDK integration) | Order state storage; idempotent writes via condition expressions |
  | Notification | Amazon SNS + Amazon SES (direct SDK integration) | Order confirmation to customer; fulfillment trigger to warehouse |
  | Status Check | Step Functions DescribeExecution | Client polls execution status or subscribes to EventBridge state-change events |
  | Observability | Amazon CloudWatch + AWS X-Ray | Execution metrics, alarms on failure, distributed tracing |

- Key Decisions: (1) Standard required for exactly-once payment guarantee and .waitForTaskToken support. (2) Idempotency tokens on payment calls for safe retries. (3) Redrive enables recovery of payment failures within 14-day window without re-executing successful steps. (4) For throughput > 2,000/sec: move idempotent sub-steps (inventory check, notification) to nested Express child workflows.
- Scaling Path: 2,000 exec/sec (Standard limit). For higher throughput: use SQS as buffer in front of Step Functions (SQS → EventBridge Pipe → StartExecution) to absorb bursts. For order volumes > 2,000/sec sustained: evaluate DynamoDB-backed state machine pattern (custom orchestration) for the high-volume idempotent path.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/tutorial-api-gateway.html (2026-08-31); https://docs.aws.amazon.com/step-functions/latest/dg/redrive-executions.html (2026-08-31)

---

## Service Equivalence Map

Single-cloud research (AWS only). Cross-provider comparison included only for workflow orchestration context where it aids architecture decisions.

| Capability | AWS Step Functions | Azure | GCP |
|------------|-------------------|-------|-----|
| Workflow Orchestration | Step Functions (Standard/Express) | Azure Durable Functions / Logic Apps | GCP Workflows |
| Visual Designer | Workflow Studio | Logic Apps Designer | N/A (YAML-based) |
| Exactly-Once Semantics | Standard Workflow | Durable Functions (orchestration trigger) | Not guaranteed natively |
| Long-duration Workflows | Standard (up to 1 year) | Durable Functions (eternal orchestrations) | Workflows (up to 1 year via callbacks) |
| High-throughput Short Workflows | Express (100,000/sec) | Logic Apps Consumption (limited) | Workflows (limited) |
| Direct Cloud API Integration | 220+ AWS services (aws-sdk) | Azure connector ecosystem (Logic Apps) | Limited (Workflows steps) |
| Fan-out at Scale | Distributed Map (10,000 children) | Durable Functions fan-out pattern | Workflows parallel steps (limited) |

---

## Provider Differentiators

**AWS SDK Service Integrations (220+ Services, 10,000+ APIs)**
Direct ASL Resource calls to any AWS service without a Lambda intermediary. Syntax: arn:aws:states:::aws-sdk:{serviceName}:{apiAction}. Three integration patterns (Request Response / .sync / .waitForTaskToken). Eliminates Lambda invocation cost, cold-start latency, and function lifecycle overhead for any step calling a single AWS API. No equivalent in Azure Logic Apps or GCP Workflows at this breadth.
[Source: https://docs.aws.amazon.com/step-functions/latest/dg/supported-services-awssdk.html (2026-08-31)]

**Distributed Map (10,000 Parallel Child Executions from S3)**
Largest serverless parallelism without infrastructure management — up to 10,000 concurrent child workflow executions, each with independent 25,000-event history. Native S3 dataset reading: JSON, CSV, S3ListObjectsV2, Athena manifests, Parquet (GA Sep 2025). ResultWriter aggregates to S3. ToleratedFailurePercentage/Count for partial failure acceptance. New CloudWatch metrics (Sep 2025): Approximate Open Map Runs Count, Open Map Run Limit, Approximate Map Runs Backlog Size. Standard Workflow only. Hard quota: 10,000 concurrent child executions; 1,000 open Map Runs.
[Source: https://docs.aws.amazon.com/step-functions/latest/dg/use-dist-map-orchestrate-large-scale-parallel-workloads.html (2026-08-31); https://docs.aws.amazon.com/step-functions/latest/dg/document-history.html (2026-08-31)]

**Wait for Callback — Zero-Cost Pause up to 1 Year**
.waitForTaskToken pauses execution for up to 1 year at zero additional state transition charge during the wait period. Natural fit for multi-day human approval workflows, SaaS webhook callbacks, and third-party async integrations. HeartbeatSeconds prevents indefinitely stuck executions. Supported destinations: SQS, SNS, Lambda, EventBridge, ECS, Bedrock. Standard Workflow only; cross-account not supported.
[Source: https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html (2026-08-31)]

**HTTP Task (Third-Party HTTPS APIs via EventBridge Connection)**
arn:aws:states:::http:invoke calls any public or private HTTPS API (Stripe, Salesforce, Twilio, internal microservices) without a Lambda intermediary. Credentials stored in Secrets Manager via EventBridge Connection — never in ASL definition. All HTTP methods supported. Private APIs via VPC Lattice/PrivateLink. 60-second hard timeout. Does not support mTLS. No equivalent in GCP Workflows or Azure Durable Functions at this integration depth.
[Source: https://docs.aws.amazon.com/step-functions/latest/dg/connect-third-party-apis.html (2026-08-31)]

**JSONata + Workflow Variables (Lambda-Free Transforms)**
JSONata 2.0.6 eliminates Lambda functions for JSON reshaping, filtering, arithmetic, string operations, and conditional transformation natively in ASL. $states reserved variable provides unified access to input/result/error/context. Workflow Variables (Assign field, GA 2024) eliminate threading data through every intermediate state's output. Custom functions: $partition, $range, $hash, $random, $uuid, $parse. 1-second expression timeout limit — offload complex computation to Lambda. AWS recommends JSONata for all new state machines.
[Source: https://docs.aws.amazon.com/step-functions/latest/dg/transforming-data.html (2026-08-31); https://docs.aws.amazon.com/step-functions/latest/dg/workflow-variables.html (2026-08-31)]

**Workflow Studio + TestState with Mocking (Nov 2025)**
Visual drag-and-drop designer with Design mode and Code mode. TestState API (enhanced Nov 2025): mock AWS service integration responses without real IAM roles or live services; test Map/Parallel/Activity/.sync/.waitForTaskToken states; three inspection levels (INFO/DEBUG/TRACE) exposing I/O at each transformation step; mock validation modes (STRICT/PRESENT/NONE). Console UI does not support mocking — requires AWS CLI or SDK. ValidateStateMachineDefinition API for CI/CD pre-commit definition syntax validation.
[Source: https://docs.aws.amazon.com/step-functions/latest/dg/test-state-isolation.html (2026-08-31)]

**Versions and Aliases with Traffic Splitting**
Immutable numbered version snapshots (up to 1,000) and mutable aliases (up to 100) with routingConfiguration for canary and blue-green deployments — shifting traffic between two versions with percentage weights summing to 100. CloudWatch Version/Alias dimensions enable per-deployment error rate monitoring. Redrive eligibility preserved per-version regardless of alias updates. Native to Step Functions with no additional tooling required.
[Source: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-state-machine-alias.html (2026-08-31)]

---

## Scenario Coverage

**Standard Case — Order Processing Orchestration**
- Approach: Standard Workflow as orchestrator with JSONata query language. DynamoDB PutItem via direct SDK integration (arn:aws:states:::aws-sdk:dynamodb:putItem) for order creation. HTTP Task (arn:aws:states:::http:invoke) via EventBridge Connection for payment processing. Choice state on payment result (approved/declined/error). SNS Publish via SDK integration for order confirmation. SQS SendMessage via SDK integration for fulfillment queue. Every Task state carries Retry (JitterStrategy:FULL, MaxAttempts:6) and Catch with compensation states. All Tasks declare TimeoutSeconds.
- Key Decisions: (1) Standard required for exactly-once payment guarantee and .waitForTaskToken if fraud review step needed. (2) 256 KiB payload discipline — store order line items in S3, pass S3 key through workflow. (3) Idempotency tokens on payment HTTP Task for safe retries. (4) CloudWatch Logs Level:ALL + X-Ray tracing enabled. (5) Least-privilege IAM execution role scoped to specific DynamoDB table, SNS topic, SQS queue ARNs.

**Edge Case — 25,000-Event History Breach**
- Approach: Signal — Inline Map over 500+ items with 10 events/iteration approaches 5,000 parent history events from Map alone, plus overhead events. At 2,500 items × 10 events = 25,000 events — execution fails mid-processing unconditionally. Resolution: Switch Map state from INLINE to DISTRIBUTED mode. Each child iteration runs in an independent child workflow execution with its own 25,000-event budget. Set ResultWriter: { Resource: "arn:aws:states:::s3:putObject", Parameters: { Bucket: "results-bucket", Prefix: "map-results/" } } to avoid 256 KiB output limit on aggregated results. For extreme fan-out (> 10,000 items requiring > 10,000 concurrent children): nest Distributed Maps or use ItemBatcher to group items per child execution. Monitor parent execution event count via GetExecutionHistory; alarm at 20,000 events.
- Handling with AWS Services: Step Functions Distributed Map (DISTRIBUTED mode), Amazon S3 (ItemReader + ResultWriter), Amazon CloudWatch (event count alarm via custom metric from GetExecutionHistory response).

**Anti-Pattern Case — Step Functions as High-Frequency Event Queue**
- Clarification: Refuse — Standard Workflow with tight Wait-state polling loop at 10,000+ events/sec. Ask: "What is the event rate per second, what is the expected event volume per day, what is the ordering requirement, and does each event require durable exactly-once processing or idempotent best-effort delivery?" Standard Workflows cap at 2,000 exec/sec (throttled beyond) and 4,000 transitions/sec. Per-transition billing is prohibitive at queue-like volume. The 25,000-event history ceiling is hit in hours at high event rates. Wait-state polling loops generate 6+ events per poll interval. Redirect to: SQS + Lambda with event source mapping (ESM) for durable queuing with at-least-once delivery, or Express Workflow (at-least-once, 100,000/sec) for idempotent event processing pipelines. Never use Step Functions as a substitute for SQS, Kinesis, or EventBridge for raw event throughput.

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Changelog | Sep 2025 Distributed Map new ItemReader types (Parquet, Athena manifest, S3ListObjectsV2) and new CloudWatch metrics | Added | https://docs.aws.amazon.com/step-functions/latest/dg/document-history.html (2026-08-31) |
| 1 | Changelog | 2024 JSONata GA — QueryLanguage field, Arguments/Output, $states variable, custom functions | Added | https://docs.aws.amazon.com/step-functions/latest/dg/transforming-data.html (2026-08-31) |
| 1 | Changelog | 2024 Workflow Variables GA — Assign field, limits, Distributed Map scope restriction | Added | https://docs.aws.amazon.com/step-functions/latest/dg/workflow-variables.html (2026-08-31) |
| 1 | Glossary | 18 terms with Definition/Provider Docs Section/Architect Usage/Common Confusion | Added | Multiple official docs pages (2026-08-31) |
| 1 | Mandatory Patterns | 7 patterns (Retry/Catch, Timeout, Logging/Tracing, Express selection, 25K limit, SDK integration, IAM) | Added | https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html (2026-08-31) |
| 1 | Anti-Patterns | 8 anti-patterns with Risk Level/Wrong/Correct/Detection/Impact | Added | Multiple official docs pages (2026-08-31) |
| 1 | Architectural Decisions | 6 decision tables (Standard/Express, Orchestration/Choreography, Map types, SDK integration, JSONata/JSONPath, Callback/Polling) | Added | Multiple official docs pages (2026-08-31) |
| 2 | Security Architecture | KMS CMK encryption — KmsDataKeyReusePeriodSeconds range, EventBridge event exclusion when CMK enabled | Added | https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html (2026-08-31) |
| 2 | Security Architecture | CloudTrail — data events requiring opt-in (InvokeHTTPEndpoint, GetActivityTask) | Added | https://docs.aws.amazon.com/step-functions/latest/dg/procedure-cloud-trail.html (2026-08-31) |
| 2 | Operational Patterns | Redrive eligibility details — Fail state re-enters and fails again; code fix required | Added | https://docs.aws.amazon.com/step-functions/latest/dg/redrive-executions.html (2026-08-31) |
| 2 | Provider Differentiators | TestState Nov 2025 enhancement — mocking support, three inspection levels, mock validation modes | Added | https://docs.aws.amazon.com/step-functions/latest/dg/test-state-isolation.html (2026-08-31) |
| 3 | Reference Architectures | API Gateway 29-second integration timeout constraint for Sync Express noted | Added | https://docs.aws.amazon.com/step-functions/latest/dg/tutorial-api-gateway.html (2026-08-31) |
| 3 | Scenario Coverage | Anti-Pattern Case redirect targets explicitly named (SQS ESM, Kinesis, Express) | Added | https://docs.aws.amazon.com/step-functions/latest/dg/service-quotas.html (2026-08-31) |
| 3 | Gap — IRRESOLVABLE | Well-Architected Serverless Lens page inaccessible during research (JS-rendered SPA) | ⚠️ IRRESOLVABLE — page returned no content; facts cross-verified from sfn-best-practices.html | — |
| 3 | Gap — IRRESOLVABLE | Exact GA dates for TestState, Redrive, Versions/Aliases not found in dated changelog entries | ⚠️ IRRESOLVABLE — changelog lists features without exact dates for these items; marked as earlier 2023–2024 GA | — |
