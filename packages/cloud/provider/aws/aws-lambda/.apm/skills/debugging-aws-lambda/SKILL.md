---
name: debugging-aws-lambda
description: "Diagnoses deployed AWS Lambda Event Functions by symptom with read-only commands, per AWS docs of 2026-10-28. Use when API Gateway, SQS or EventBridge callers see 429, 500, 502, 504, timeouts, init or SnapStart errors. Not for fixes, deploys or builds."
---

# Debugging AWS Lambda (Event Functions)

> Docs lock: every claim applies to the **AWS Lambda, API Gateway, CloudWatch Logs, SQS and EventBridge documentation and the AWS CLI v2 reference as published on 2026-10-28** (CLI reference pages show AWS CLI 2.39.0). AWS docs carry no semantic version. Research date **2026-10-28**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping). Where two AWS pages disagree, both are cited and none is chosen.
> Scope: finding the cause of a failure in a deployed function, read-only, entered through API Gateway (REST or HTTP API, Lambda proxy), an SQS event source mapping or an EventBridge rule. Also the evidence checklist for post-deploy verification. The debugger never changes anything: every fix leaves as a work-order for the code owner or the deployer.
> Neighbours, by name only: `deploying-aws-lambda` ([SKILL.md](../deploying-aws-lambda/SKILL.md), owns apply, publish, alias and rollback), `developing-quarkus-amazon-lambda-v3-40` (building and handler), `logging-quarkus-lambda-v3-40`, `tracing-quarkus-lambda-v3-40`, `monitoring-cloudwatch-observability` (dashboards and alarms), `tracing-aws-xray`, `validating-aws-observability` (scripts that run the same read-only checks), `aws-lambda-debugger` (agent that runs this procedure).

## Version Context

| Item | Value | Source (fetched 2026-10-28) |
|---|---|---|
| AWS Lambda Developer Guide | continuously published, snapshot 2026-10-28; standard functions are called "Event Functions" | https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-execution.html |
| AWS CLI v2 reference | 2.39.0 as shown on the reference pages | https://docs.aws.amazon.com/cli/latest/reference/lambda/get-function-configuration.html |
| API Gateway Developer Guide (REST and HTTP APIs) | snapshot 2026-10-28 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-troubleshooting-lambda.html |
| CloudWatch Logs User Guide (Logs Insights) | snapshot 2026-10-28 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-examples.html |
| System log format | AWS says it is rolling out new-format log lines and trace segments to all Regions except China and GovCloud | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html |
| Out of scope | Lambda Web Functions (own error taxonomy), Managed Instances, MicroVMs, durable functions | https://docs.aws.amazon.com/lambda/latest/dg/web-functions-troubleshooting.html |
| Read-only boundary | unit policy of the debugger, not an AWS fact | page not recorded (repo policy) |

**Version-lifetime risk** (as of 2026-10-28; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- The log-format and X-Ray segment changes are in transition; queries must match both REPORT styles ([log formats](./blueprints/platform-log-formats.md#old-and-new-style-during-the-transition)).
- AWS docs change without a version number; re-read the pages before reusing this skill after 2026-10-28.

## Quick Navigation

- [Diagnosis procedure](#diagnosis-procedure)
- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Tree: steps 0-1, branches A and B](./blueprints/tree-a-b-entry-and-invocation.md)
- [Tree: branches C, D and E](./blueprints/tree-c-e-function-latency-network.md)
- [Tree: branches F, G and H](./blueprints/tree-f-h-queues-state-events.md)
- [REPORT, INIT_REPORT and RESTORE_REPORT formats](./blueprints/platform-log-formats.md)
- [Logs Insights fields and queries](./blueprints/logs-insights-and-fields.md)
- [Read-only allowlist and refused commands](./blueprints/read-only-allowlist.md)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Ask-first decisions in depth](./blueprints/ask-first-decisions.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Verdict, hand-off and post-deploy checks](./blueprints/verdict-and-handoff.md)
- [Verification Loop](./blueprints/verdict-and-handoff.md#verification-loop)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Source bibliography](./blueprints/source-bibliography.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Diagnosis procedure

Collect first: function name, alias or version, Region, entry (REST, HTTP API, SQS, EventBridge), UTC time window, symptom. Every step is read-only.

| Step | What | Detail |
|---|---|---|
| 0 | Read the control plane: `State`, `StateReasonCode`, `LastUpdateStatus`, `Version`, `Timeout`, `MemorySize`, `SnapStart`, `LoggingConfig`, `TracingConfig`. Not `Active` and `Successful` goes to branch G | [step 0](./blueprints/tree-a-b-entry-and-invocation.md#step-0-control-plane) |
| 1 | Classify: invocation error (Invoke 4xx/5xx, metric `Throttles`) or function error (200 plus `X-Amz-Function-Error`, metric `Errors`) | [step 1](./blueprints/tree-a-b-entry-and-invocation.md#step-1-classify) |
| 2 | Follow the branch for the symptom (table below), reading the REPORT line before application logs | [log formats](./blueprints/platform-log-formats.md) |
| 3 | Gather evidence: RequestId, REPORT fields, metric values, `$context` variables, trace segments; redact secrets | [verdict](./blueprints/verdict-and-handoff.md#diagnosis-verdict) |
| 4 | Verdict with the branch letter, then a work-order to the owner. No AWS call changes anything. Record: mode A `diagnosis-NN.md` (outcome `success`, `partial`, `failed` or `needs-input`), mode B `verify-E7-<nn>.md` (`pass` or `fail`) | [work-order](./blueprints/verdict-and-handoff.md#work-order-format), [outcomes](./blueprints/verdict-and-handoff.md#record-and-outcome-vocabulary) |

| Branch | Symptom | First read-only step | Detail |
|---|---|---|---|
| A | API Gateway client sees 429, 403, 500, 502, 504 or wrong data | `$context.integration.integrationStatus` vs `$context.integration.status` in the access log | [A, B](./blueprints/tree-a-b-entry-and-invocation.md#branch-a-api-gateway-entry) |
| B | Lambda refused the invoke (429, 502 KMS or ENI, 409, 408, 413) | Invoke error name, `StateReasonCode`, `Throttles` | [A, B](./blueprints/tree-a-b-entry-and-invocation.md#branch-b-invocation-errors) |
| C | Function ran and failed: timeout, init, crash, memory, handler, payload | REPORT `Status`, `Error Type`, `Max Memory Used` | [C-E](./blueprints/tree-c-e-function-latency-network.md#branch-c-function-errors) |
| D | Slow first requests, cold starts | `Init Duration` or `Restore Duration` in the REPORT line | [C-E](./blueprints/tree-c-e-function-latency-network.md#branch-d-cold-start-and-latency) |
| E | Timeouts after VPC attach, DNS, no internet | VPC and subnet route facts from the configuration | [C-E](./blueprints/tree-c-e-function-latency-network.md#branch-e-vpc-and-network) |
| F | SQS messages reprocessed, backlog, DLQ filling | `list-event-source-mappings`, SQS `ApproximateAgeOfOldestMessage` | [F-H](./blueprints/tree-f-h-queues-state-events.md#branch-f-sqs-event-source-mapping) |
| G | `Pending`, `Inactive`, `Failed` update, old code still running | `State`, `LastUpdateStatus`, reason codes | [F-H](./blueprints/tree-f-h-queues-state-events.md#branch-g-control-plane-state) |
| H | EventBridge rule target not invoked or function failing asynchronously | async metrics, rule DLQ attributes | [F-H](./blueprints/tree-f-h-queues-state-events.md#branch-h-eventbridge-asynchronous) |

## Blueprints & Guardrails

### ✅ Always Do

- **Use only the read-only allowlist and hand every fix over as a work-order.** The allowlisted commands return data only ([CLI reference](https://docs.aws.amazon.com/cli/latest/reference/lambda/get-function-configuration.html)). The read-only boundary is repo policy: [allowlist](./blueprints/read-only-allowlist.md). See [patterns](./blueprints/always-do-patterns.md#1-read-only-allowlist).
- **Start a Logs Insights `start-query` or an X-Ray `start-trace-retrieval` only with the line `approval: logs-insights scope=<log-group or "xray"> window=<min> by=<user> at=<UTC> relayed-by=<orchestrator>`.** They start a billable query or retrieval; without the line those evidence sources are `not verified`. Repo policy: [allowlist](./blueprints/read-only-allowlist.md#allowlist).
- **Classify invocation error vs function error before anything else.** A function error returns status 200 with an `X-Amz-Function-Error` header; 400 and 500-series codes are reserved for invocation errors ([execution troubleshooting](https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-execution.html)). See [patterns](./blueprints/always-do-patterns.md#2-classify-invocation-vs-function-error).
- **Map the API Gateway status to the failing side.** Lambda rejecting the invoke (including throttling) gives 500, a function error or malformed proxy response gives 502, body `{"message": "Internal server error"}`, and API Gateway never retries ([Lambda errors with API Gateway](https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway-errors.html)). See [patterns](./blueprints/always-do-patterns.md#3-map-the-api-gateway-status).
- **Confirm which version or alias ran before reading anything else.** The START log line shows the executed version ([execution troubleshooting](https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-execution.html)). See [patterns](./blueprints/always-do-patterns.md#4-confirm-the-executed-version).
- **Read the REPORT line before application logs.** `Status`, `Error Type`, `Init Duration`, `Max Memory Used` and `Memory Size` come from the platform ([execution environment lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)). See [formats](./blueprints/platform-log-formats.md#report-fields).
- **Check function state and last update status before blaming code.** While `LastUpdateStatus` is `InProgress` or `Failed`, invocations keep using the previous code ([function states](https://docs.aws.amazon.com/lambda/latest/dg/functions-states.html)). See [patterns](./blueprints/always-do-patterns.md#6-check-control-plane-state).
- **Query `Errors` and `Throttles` separately.** Throttled requests do not count as `Invocations` or `Errors` ([metric types](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html)). See [patterns](./blueprints/always-do-patterns.md#7-query-metrics-with-the-right-statistic).
- **Separate the two permission planes.** Who may invoke is the function's resource-based policy; what the code may call is the execution role ([API Gateway invoke](https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html)). See [patterns](./blueprints/always-do-patterns.md#8-separate-the-two-permission-planes).
- **For SQS, verify the settings that decide where failed messages go.** Source queue visibility timeout of at least six times the function timeout and `maxReceiveCount` of at least 5 ([SQS ESM configuration](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html)). See [patterns](./blueprints/always-do-patterns.md#9-sqs-configuration).
- **Wait 5 to 10 minutes before concluding that missing logs mean not invoked.** Logs can lag or be lost to permissions or throttling ([execution troubleshooting](https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-execution.html)). See [patterns](./blueprints/always-do-patterns.md#10-allow-for-log-latency-and-loss).
- **Redact secrets and personal data in every report.** AWS's own sample log output prints `AWS_SESSION_TOKEN` ([viewing logs](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-view.html)). See [patterns](./blueprints/always-do-patterns.md#11-redact-secrets).
- **Match both the old and the new REPORT styles.** Timeout and crash lines differ between them during AWS's rollout ([execution environment lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)). See [formats](./blueprints/platform-log-formats.md#old-and-new-style-during-the-transition).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| API Gateway logging is off | A: ask the deployer to enable it. B: Lambda-side evidence only. C: REST metrics `5XXError`, `IntegrationLatency`, `Latency`. HTTP APIs may have access logs only (medium confidence). See [C1](./blueprints/ask-first-decisions.md#c1-api-gateway-logging) | "May the deployer enable API Gateway logging, or do we continue with Lambda-side evidence?" |
| Which log tool | `tail`, `filter-log-events` (ms) or Logs Insights (seconds, billable; pricing not read) (unverified). See [C2](./blueprints/ask-first-decisions.md#c2-log-tool-and-window) | "Which time window, and is a billable Logs Insights scan acceptable?" |
| Text or JSON log format | JSON platform records use `type` and `record.metrics.*` (medium confidence); field discovery on them is not stated (unverified). See [C3](./blueprints/ask-first-decisions.md#c3-log-format) | "Is `LoggingConfig.LogFormat` Text or JSON?" |
| X-Ray evidence | Active tracing gives service-vs-code segments, sampled only; the max time range of `get-trace-summaries` is not stated (unverified). See [C4](./blueprints/ask-first-decisions.md#c4-x-ray-evidence) | "Is Active tracing enabled on the function and API?" |
| Reproduce by invoking | DryRun proves only the caller's permission; a real invoke executes code and is not the debugger's: route it to the deployer (`aws-lambda-deployer`, `approval: smoke payload=<file or sha256> ...`). See [C5](./blueprints/ask-first-decisions.md#c5-reproducing-by-invoking) | "Should the deployer run a side-effect-free smoke payload under an `approval: smoke` line?" |
| SnapStart functions | Evidence moves to `INIT_REPORT` and `RESTORE_REPORT`; the Quarkus guide says restoration is limited to 2 seconds, AWS says 10 seconds, which applies is (unverified). See [C6](./blueprints/ask-first-decisions.md#c6-snapstart-evidence) | "Is SnapStart on for this version?" |
| Strings that no fetched page confirms | The OOM string, REST execution-log strings and the HTTP API timeout status are irresolvable (I1-I3). See [C7](./blueprints/ask-first-decisions.md#c7-irresolvable-strings-and-status) | "Do you have a log line that carries the string, or should the verdict rest on the REPORT fields?" |
| Out-of-scope products and Regions | Web Functions, Managed Instances, MicroVMs, durable functions, China and GovCloud have other logs and limits. See [C8](./blueprints/ask-first-decisions.md#c8-out-of-scope-products-and-regions) | "Which function type and Region is this?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Run a mutating command (`update-function-configuration`, `update-event-source-mapping`, `add-permission`, `update-alias`, `put-function-concurrency`, `apigatewayv2 update-stage`, `logs create-log-group`, `iam attach-role-policy`) ([execution troubleshooting](https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-execution.html), [HTTP API troubleshooting](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-troubleshooting-lambda.html)) | Read with `get-function-configuration`, `get-policy`, `list-event-source-mappings`, then write a work-order for the owner. [Refused list](./blueprints/read-only-allowlist.md#refused-commands) |
| Declare the function healthy because `Errors` is 0 ([metric types](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html)) | Check `Errors`, `Throttles`, `ConcurrentExecutions` and API Gateway `integrationStatus` together |
| Read Invoke `StatusCode` 200 as success ([Invoke](https://docs.aws.amazon.com/lambda/latest/api/API_Invoke.html)) | Look for the `FunctionError` key and the executed version too |
| Judge an SQS backlog with `IteratorAge`, which is for DynamoDB, Kinesis and DocumentDB sources ([metric types](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html)) | Read `AWS/SQS ApproximateAgeOfOldestMessage` and the DLQ's `ApproximateNumberOfMessagesVisible` ([SQS metrics](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-available-cloudwatch-metrics.html)) |
| Expect a Lambda throttle to reach the client as 429; it arrives as 500 ([Lambda errors with API Gateway](https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway-errors.html)) | A client 429 points to API Gateway throttling or quota; a 500 with `Throttles` above 0 points to Lambda concurrency |
| Paste environment dumps, tokens, event bodies or Data-tracing output into a report ([REST execution logging](https://docs.aws.amazon.com/apigateway/latest/developerguide/rest-api-execution-logging.html)) | Report RequestId, REPORT fields and branch letter; redact the rest |
| Treat `simulate-principal-policy` on the execution role as proof that API Gateway may invoke ([simulate-principal-policy](https://docs.aws.amazon.com/cli/latest/reference/iam/simulate-principal-policy.html)) | Read the function's resource-based policy with `get-policy --qualifier <alias>` |
| Search Event Function logs for Web Functions error types such as `Runtime.OutOfMemory` ([Web Functions troubleshooting](https://docs.aws.amazon.com/lambda/latest/dg/web-functions-troubleshooting.html)) | Read the REPORT lines with `filter-log-events` (allowlist), or run `@type = "REPORT" and @maxMemoryUsed = @memorySize` only through the `approval: logs-insights` gate; read `Status` and `Error Type`. `start-live-tail` stays refused (no approval line exists for it) |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Function error vs invocation error | function error: 200 plus `X-Amz-Function-Error`; invocation error: 4xx/5xx | https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-execution.html |
| API Gateway to Lambda status | Lambda rejects invoke: 500; function error or wrong response format: 502; no retries | https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway-errors.html |
| API Gateway own statuses (REST gateway responses) | `THROTTLED` 429, `QUOTA_EXCEEDED` 429, `INTEGRATION_TIMEOUT` 504, `API_CONFIGURATION_ERROR` 500 | https://docs.aws.amazon.com/apigateway/latest/developerguide/supported-gateway-response-types.html |
| Integration timeout | REST 50 ms to 29 s (raisable for Regional and private APIs); HTTP API 30 s maximum, not raisable | REST: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html ; HTTP API: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html |
| Init phase limit | 10 s on-demand, retried at first invoke with the function timeout; up to 15 min for provisioned concurrency and SnapStart | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html |
| Function timeout | maximum 900 s; the console default is 3 s | https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-configuration.html |
| Account concurrency | default 1,000; RPS limit is 10 times concurrency | https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html |
| API Gateway account throttle | default 10,000 RPS, burst 5,000 (2,500 and 1,250 in some Regions) | https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html |
| Log latency | 5 to 10 minutes after an invocation | https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-execution.html |
| SQS ESM settings | visibility timeout at least 6 times the function timeout; `maxReceiveCount` at least 5 | https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html |
| Async retries (EventBridge target) | function errors retried twice (1 min, then 2 min); EventBridge retries 24 h, 185 attempts | Lambda: https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html ; EventBridge (S47): https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html |
| Log tail (`--log-type Tail`) | 4 KB, base64, synchronous only; first or last 4 KB: pages disagree (unverified) | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-view.html |
| SnapStart restore limit | AWS 10 s (`SnapStartTimeoutException`); Quarkus guide 2 s; which applies is (unverified) (U9) | https://docs.aws.amazon.com/lambda/latest/api/API_Invoke.html ; https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks-java.html ; https://quarkus.io/version/3.40/guides/aws-lambda-snapstart |

## External Resources

All fetched 2026-10-28.

- Troubleshoot invocation issues: https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-invocation.html
- Troubleshoot execution issues: https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-execution.html
- Handling Lambda errors with an API Gateway API: https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway-errors.html
- Full bibliography: [source bibliography](./blueprints/source-bibliography.md)
