# Never-Do Patterns

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). Source ids resolve in the [source bibliography](./source-bibliography.md). Tags map to the [register](./unverified-and-risks.md#tag-to-register-mapping). Severity wording: low, moderate, high, critical.

## Contents

- [N1 Mutating command while diagnosing](#n1-mutating-command-while-diagnosing)
- [N2 Healthy because Errors is 0](#n2-healthy-because-errors-is-0)
- [N3 StatusCode 200 read as success](#n3-statuscode-200-read-as-success)
- [N4 IteratorAge for an SQS backlog](#n4-iteratorage-for-an-sqs-backlog)
- [N5 Lambda throttle expected as 429](#n5-lambda-throttle-expected-as-429)
- [N6 Raw dumps in the report](#n6-raw-dumps-in-the-report)
- [N7 Role simulation as proof of invoke permission](#n7-role-simulation-as-proof-of-invoke-permission)
- [N8 Web Functions error types in Event Function diagnosis](#n8-web-functions-error-types-in-event-function-diagnosis)

## N1 Mutating command while diagnosing

Severity: critical. The debugger is read-only; fixes belong to the code owner or the deployer. Several diagnostic-looking commands mutate: `update-event-source-mapping` (S8, S27), `update-function-configuration` (AWS suggests "a trivial update" to refresh credentials, S2), `add-permission` (S13, S25), `update-alias` (S4), `put-function-concurrency` or concurrency 0 to stop a loop (S1), `aws apigatewayv2 update-stage --access-log-settings` (S19), `logs create-log-group` (S19), `iam attach-role-policy` (S7). Impact: changes production behaviour, can drop or delay messages and voids the read-only guarantee.

```bash
# ❌ WRONG
aws lambda update-event-source-mapping --uuid <uuid> --metrics-config Metrics=EventCount
aws lambda add-permission --function-name my-function --principal apigateway.amazonaws.com ...
aws lambda update-function-configuration --function-name my-function --timeout 30
```

```bash
# ✅ CORRECT
aws lambda list-event-source-mappings --function-name my-function     # read the ESM (S27)
aws lambda get-policy --function-name my-function                     # read the policy (S57)
aws lambda get-function-configuration --function-name my-function     # read the timeout (S42)
# then hand off, in the report only: "Fix required: <what>, owner: deployer or integrator"
```

## N2 Healthy because Errors is 0

Severity: high. "Throttled requests and other invocation errors don't count as either `Invocations` or `Errors`" (S8), and API Gateway returns 500 when Lambda rejects the invoke (S16). Impact: throttling, permission and KMS failures go unnoticed while clients see 500.

```text
# ❌ WRONG
Errors(Sum)=0 over 1h  =>  "Lambda is fine, the 500s are an API Gateway problem"
# ✅ CORRECT
Check Errors(Sum) AND Throttles(Sum) AND ConcurrentExecutions(Max) AND API Gateway $context.integration.integrationStatus   (S8, S23, S53)
```

## N3 StatusCode 200 read as success

Severity: high. Function errors return 200 with `X-Amz-Function-Error` (CLI JSON key `FunctionError`) (S2, S5); the deploy smoke test also checks for no `FunctionError` key (In3). Impact: false-positive post-deploy verification.

```text
# ❌ WRONG
{"StatusCode": 200, "ExecutedVersion": "7", "FunctionError": "..."}  ->  "OK"
# ✅ CORRECT
{"StatusCode": 200, "ExecutedVersion": "7"} with no FunctionError key and the expected payload shape  ->  "OK"   (S5, In3)
```

## N4 IteratorAge for an SQS backlog

Severity: moderate. `IteratorAge` is "For DynamoDB, Kinesis, and Amazon DocumentDB event sources" (S8). For SQS use `AWS/SQS ApproximateAgeOfOldestMessage` (seconds, dimension `QueueName`) (S43). Impact: an empty graph read as "no backlog".

```bash
# ❌ WRONG
aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name IteratorAge ...   # SQS-triggered function
# ✅ CORRECT
aws cloudwatch get-metric-statistics --namespace AWS/SQS --metric-name ApproximateAgeOfOldestMessage \
  --dimensions Name=QueueName,Value=my-queue --statistics Maximum --period 60 --start-time <iso> --end-time <iso>   # (S43, S58)
```

The age metric excludes poison-pill messages received 3 or more times and not deleted on standard queues; read the DLQ's `ApproximateNumberOfMessagesVisible` too (S43).

## N5 Lambda throttle expected as 429

Severity: moderate. Lambda `TooManyRequestsException` is an invocation rejection, so API Gateway returns 500 (S5, S16). A 429 from API Gateway is its own throttling (`THROTTLED`) or usage-plan quota (`QUOTA_EXCEEDED`) (S24); account default 10,000 RPS, burst 5,000 (S17). Impact: the wrong service's limits are examined.

```text
# ❌ WRONG
Client got 429  ->  raise Lambda reserved concurrency
# ✅ CORRECT
Client got 429                          ->  API Gateway throttle or usage plan (stage, method, account limits)   (S17, S24)
Client got 500 and Lambda Throttles > 0 ->  Lambda concurrency                                                   (S8, S16)
```

A 503 on this path: see Ask First [C7](./ask-first-decisions.md#c7-irresolvable-strings-and-status).

## N6 Raw dumps in the report

Severity: high. The AWS sample log output includes `"AWS_SESSION_TOKEN": "AgoJb3JpZ2luX2VjELj..."` (S11); REST Data tracing "can result in logging sensitive data" and is not recommended for production (S20); no personal data in logs (In2, rule 7). Impact: credentials or personal data leak into transcripts and tickets.

```text
# ❌ WRONG
Report: "Log line: ... AWS_SESSION_TOKEN: AgoJb3Jp... , event body: {email: ..., card: ...}"
# ✅ CORRECT
Report: "RequestId <id>, REPORT Status: error Error Type: Runtime.ExitError, Max Memory Used 128/128 MB; secrets redacted"
```

## N7 Role simulation as proof of invoke permission

Severity: moderate. Invoke permission for services lives in the function's resource-based policy (S1, S25); the simulator does not fetch resource policies and does not support them for roles (S38). Impact: "Invalid permissions" 500s are missed.

```bash
# ❌ WRONG
aws iam simulate-principal-policy --policy-source-arn <fn-execution-role> --action-names lambda:InvokeFunction
# ✅ CORRECT
aws lambda get-policy --function-name my-function --qualifier prod   # principal, action, SourceArn stage and method (S25, S57)
```

## N8 Web Functions error types in Event Function diagnosis

Severity: moderate. `Runtime.OutOfMemory`, `Runtime.Unreachable` and `lambda-web-error-type` headers belong to the separate Lambda Web Functions page (S62); an Event Function crash appears as REPORT `Status: error Error Type: Runtime.ExitError` (S6). Impact: searching for strings Event Functions never emit.

```text
# ❌ WRONG
filter @message like /Runtime.OutOfMemory/        # Web Functions error type (S62)
# ✅ CORRECT
filter @type = "REPORT" and @maxMemoryUsed = @memorySize    # AWS query for 100% memory (S11)
```
