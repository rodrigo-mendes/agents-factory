# Always-Do Patterns

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). Source ids resolve in the [source bibliography](./source-bibliography.md). Tags map to the [register](./unverified-and-risks.md#tag-to-register-mapping). Commands are representative and read-only; none was executed.

## Contents

- [1. Read-only allowlist](#1-read-only-allowlist)
- [2. Classify invocation vs function error](#2-classify-invocation-vs-function-error)
- [3. Map the API Gateway status](#3-map-the-api-gateway-status)
- [4. Confirm the executed version](#4-confirm-the-executed-version)
- [5. Read the platform report lines](#5-read-the-platform-report-lines)
- [6. Check control-plane state](#6-check-control-plane-state)
- [7. Query metrics with the right statistic](#7-query-metrics-with-the-right-statistic)
- [8. Separate the two permission planes](#8-separate-the-two-permission-planes)
- [9. SQS configuration](#9-sqs-configuration)
- [10. Allow for log latency and loss](#10-allow-for-log-latency-and-loss)
- [11. Redact secrets](#11-redact-secrets)
- [12. Hand fixes to the owner](#12-hand-fixes-to-the-owner)

## 1. Read-only allowlist

Use only the commands in the [allowlist](./read-only-allowlist.md#allowlist); refuse everything else and write a work-order. Why: fixes belong to the code owner or the deployer, and the allowlisted commands return data only (S38, S39, S40, S41, S42, S56, S57, S58).

## 2. Classify invocation vs function error

"When your function code or the Lambda runtime return an error, the status code in the response from Lambda is 200 OK. The presence of an error in the response is indicated by a header named `X-Amz-Function-Error`. 400 and 500-series status codes are reserved for invocation errors." (S2). Throttles and other invocation errors "don't count as either `Invocations` or `Errors`" (S8).

```text
Invoke status 4xx/5xx                              -> invocation error -> branch B
Invoke status 200 + X-Amz-Function-Error present   -> function error   -> branch C
Throttles > 0 => invocation class; Errors > 0 => function class (Errors excludes throttles)
```

## 3. Map the API Gateway status

"If the Lambda API rejects the invocation request, API Gateway returns a 500 error code. If the Event Function runs but returns an error, or returns a response in the wrong format, API Gateway returns a 502. In both cases, the body of the response from API Gateway is `{"message": "Internal server error"}`." API Gateway does not retry Lambda invocations (S16). The REST proxy page repeats the 502 for a different output format (S21). Own statuses: `THROTTLED` 429, `QUOTA_EXCEEDED` 429, `INTEGRATION_TIMEOUT` 504 (S24). Read `integrationStatus` against `status` ([format](./logs-insights-and-fields.md#api-gateway-access-log-format)).

## 4. Confirm the executed version

First determine that the caller invoked the intended version or alias; the START line always shows the executed version (S2). Invoke returns `ExecutedVersion`: "When you invoke a function with an alias, this indicates which version the alias resolved to" (S5). If API Gateway invokes `$LATEST` instead of the alias that has provisioned concurrency, cold starts appear (S1).

```text
START RequestId: c3252230-c73d-49f6-8844-968c01d1e2e1 Version: $LATEST     (AWS example, S6)
```

## 5. Read the platform report lines

Fields, exact examples and the old and new styles: [platform log formats](./platform-log-formats.md). Read `Status`, `Error Type`, `Init Duration` and `Max Memory Used` against `Memory Size` before any application log (S6, S11, S32).

## 6. Check control-plane state

"Event Functions can only be successfully invoked while active." `Pending`: invocations and other API actions fail; `Inactive`: the invocation fails and Lambda sets the function to `Pending`; while `LastUpdateStatus` is `InProgress` or `Failed`, invocations use the previous code and configuration (S29). The command and the reason codes are in [step 0](./tree-a-b-entry-and-invocation.md#step-0-control-plane) and [branch G](./tree-f-h-queues-state-events.md#branch-g-control-plane-state). For SnapStart also confirm `SnapStart.OptimizationStatus=On` and `State=Active` on the version (In1, row 33).

## 7. Query metrics with the right statistic

Invocation metrics with `Sum`; `Duration` with `Average` or `Max` and percentiles; concurrency metrics with `Max` (S8). Lambda sends metrics in 1-minute intervals (S59). The timestamp of an error metric is when the function was invoked, not when the error occurred (S8).

```text
Errors (Sum) / Invocations (Sum)         -> function error rate
Throttles (Sum) > 0                      -> TooManyRequestsException; not counted in Errors
ConcurrentExecutions (Max) vs quota      -> aws lambda get-account-settings
Duration (p99 or Max) vs configured Timeout -> timeouts; Duration excludes the cold start
AsyncEventAge, AsyncEventsDropped        -> EventBridge (asynchronous) backlog or loss
```

## 8. Separate the two permission planes

"API Gateway gets permission to invoke your function from the function's resource-based policy" (S25); other services and accounts are granted the same way (S1). The execution role "grants the function permission to access AWS services and resources" (S61).

```bash
aws lambda get-policy --function-name my-function --qualifier prod --query Policy --output text
# expect Principal.Service apigateway.amazonaws.com, Action lambda:InvokeFunction,
# aws:SourceArn arn:aws:execute-api:<region>:<acct>:<api-id>/<stage>/<METHOD>/<path> (wildcards allowed)   (S25)
aws iam simulate-principal-policy --policy-source-arn arn:aws:iam::123456789012:role/my-fn-role \
    --action-names dynamodb:PutItem --resource-arns arn:aws:dynamodb:...:table/t
# EvalDecision: allowed, explicitDeny or implicitDeny; MatchedStatements; ResourceSpecificResults   (S38)
```

The Region in the source ARN must match the function's Region, not the API's (S25). The EventBridge principal and source ARN are known from a search snippet only (medium confidence). A REST log string for invalid permissions exists only in a Knowledge Center snippet (medium confidence).

## 9. SQS configuration

Default: an error returns the whole batch after the visibility timeout (S44). Set the source queue visibility timeout to at least six times the function timeout (plus `MaximumBatchingWindowInSeconds`) and `maxReceiveCount` to at least 5 (S48). An exception makes the batch a complete failure even with `ReportBatchItemFailures` (S27). Command: [branch F](./tree-f-h-queues-state-events.md#branch-f-sqs-event-source-mapping). Monitor `NumberOfMessagesDeleted` and `ApproximateAgeOfOldestMessage` (S27), and the DLQ's `ApproximateNumberOfMessagesVisible` (S43).

## 10. Allow for log latency and loss

Logs may take 5 to 10 minutes to appear (S2, S7). Before "not invoked", check the execution role's log permissions, CloudWatch Logs throttling and the `logsDropped` event (S2, S12). Details: [log latency](./platform-log-formats.md#log-latency-and-loss).

## 11. Redact secrets

AWS's sample log output prints `"AWS_SESSION_TOKEN": "AgoJb3JpZ2luX2VjELj..."` (S11); REST Data tracing "can result in logging sensitive data" (S20); repo rule: no personal data in logs (In2, rule 7). Report RequestId, REPORT fields, branch letter and counts only.

## 12. Hand fixes to the owner

Every proposed change leaves as a [work-order](./verdict-and-handoff.md#work-order-format) to the code owner (integrator) or the deployer. The debugger makes no AWS call that changes state (In3).
