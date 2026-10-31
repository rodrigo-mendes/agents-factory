# Research: Debugging deployed AWS Lambda functions by symptom (AWS docs state 2026-10-28, read-only diagnosis)

> Unit **D2** -> future knowledge skill `debugging-aws-lambda` (package `aws-lambda`; consumer agent `aws-lambda-debugger`,
> read-only, also used for post-deploy verification). Source item: "debug Lambdas by symptom".
> Runtime-agnostic; Java/Quarkus notes only where an AWS page documents Java. Deploy procedure is D1
> (`workspace/quarkus-aws-saas/research_AWS_LambdaDeploy_2026-10.md` [I3]) and is referenced, not repeated.
> Spec followed: `.claude/skills/researching-technical-frameworks/SKILL.md` + `blueprints/output-format-template.md`.

**Citation convention.** Every claim carries a source ID `[Sn]` (AWS official page) or `[In]` (repo-internal file) or `[Kn]`
(AWS Knowledge Center on repost.aws, which could not be fetched; search snippet only). All AWS pages were read on
**2026-10-28**; URL, read date and read-completeness per ID are in [Source Bibliography](#source-bibliography).
`[In]` sources are repo policy, **not AWS facts**. Tags: **(unverified)** = no official page fetched confirms it;
**(medium confidence)** = single source, inference, internally inconsistent AWS pages, or partly read page.

**Version pin.** The "version" here is the AWS Lambda Developer Guide, API Gateway Developer Guide, CloudWatch Logs User
Guide, SQS/EventBridge guides and the AWS CLI v2 reference as published on 2026-10-28 (CLI reference pages show
**AWS CLI 2.39.0** [S36][S38][S39][S42]). AWS docs carry no semantic version; older snapshots, blogs and the SAM/CDK guides
are out of scope. "Lambda Web Functions" (a separate product with its own error taxonomy [S62]) are **out of scope**:
their `Runtime.OutOfMemory` and similar error types must not be mixed into Event Function diagnosis.

**Approval relay.** Scope, unit list, names and packages approved by the user on 2026-10-28 ("Approve, start pilot U1";
fan-out "Fix pilot, then fan-out (Recommended)"), recorded in `workspace/quarkus-aws-saas/PIPELINE_STATE.md#approvals`.
This file restates the relay; it is not a new approval.

---

## Metadata

```yaml
Full_Name: AWS Lambda (Event Functions) runtime diagnosis by symptom - API Gateway (REST/HTTP), SQS ESM, EventBridge; read-only tools
Target_Version: "AWS Lambda / API Gateway / CloudWatch Logs / SQS / EventBridge docs + AWS CLI v2 reference as of 2026-10-28 (CLI ref 2.39.0)"
Release_Date: "n/a (continuously published docs); snapshot date 2026-10-28"
Support_Status: Active (current docs)
Primary_Docs: https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting.html (sub-pages S1-S4)
Official_Repo: "n/a (CLI reference https://docs.aws.amazon.com/cli/latest/reference/)"
Research_Date: 2026-10-28
Domain_Complexity: Complex   # multi-service (APIGW, Lambda, SQS, EventBridge, IAM, KMS, VPC, X-Ray), security-relevant (permissions, secrets in logs), strict read-only boundary
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 7         # Always-Do patterns with ✓✓ badge (AWS-fact patterns); A1 (read-only allowlist) is repo policy + AWS facts
Unverified_Count: 7
Irresolvable_Count: 3
Research_Quality_Score: 91%   # ~(112 total claims - 7 unverified - 3 irresolvable) / 112
Family_inputs: workspace/quarkus-aws-saas/_family_facts_v3.40.md (rows 11, 15, 16, 21, 33) ; _family_rules_v3.40.md (rules 9-12)
Deviations_from_agent_workflow: "Caller forbade sub-agents, background tasks and plan mode (scope approved by the user 2026-10-28, relayed above); all pages fetched directly; file written directly instead of via research-synthesizer. No AWS command was executed."
```

---

## Executive Summary

This document captures **how to diagnose a deployed AWS Lambda Event Function from its symptom**, using only read-only
tools, as AWS documents it on 2026-10-28. The entry points covered are API Gateway REST and HTTP API Lambda proxy
integrations (synchronous [S60]), Amazon SQS event source mappings (ESM [S60]) and EventBridge rules (asynchronous
[S60]). The core of the research is an **elimination tree**: first classify the failure as an *invocation error*
(Lambda refused or could not run the function; 4xx/5xx from the Invoke API [S2][S5]) or a *function error* (the code or
runtime failed; HTTP 200 with an `X-Amz-Function-Error` header [S2][S5]); then follow the branch for the entry service,
reading the REPORT / INIT_REPORT / RESTORE_REPORT platform log lines [S6][S11][S32], the function state fields
(`State`, `LastUpdateStatus`, `StateReasonCode` [S29][S30]), CloudWatch metrics (`Errors`, `Throttles`, `Duration`,
`ConcurrentExecutions`, SQS `ApproximateAgeOfOldestMessage` [S8][S43]), API Gateway logs (`$context.integrationErrorMessage`
[S13][S23][S53]) and X-Ray traces [S36][S37][S52].

What the 2026-10-28 docs say that a skill must not get wrong: (1) API Gateway turns **every** Lambda problem into an
internal error - Lambda rejecting the invoke (including Lambda throttling) gives **500**, a function error or a malformed
proxy response gives **502**, body `{"message": "Internal server error"}`, and API Gateway never retries [S16][S21];
API Gateway's own throttling is **429** (`THROTTLED`) and its integration timeout is **504** (`INTEGRATION_TIMEOUT`,
REST gateway responses [S24]); the REST integration timeout is 50 ms-29 s (raisable for Regional/private APIs at a cost
in throttle quota) and the HTTP API maximum is 30 s, not raisable [S15][S14]. (2) The `Init` phase is limited to
**10 seconds** on on-demand functions and is then retried at the first invocation with the configured function timeout
("suppressed init", `Sandbox.Timedout`, "Task timed out after 3.00 seconds") [S1][S6]; the limit does not apply to
provisioned concurrency or SnapStart (up to 15 minutes) [S6]. (3) The REPORT line now carries `Status:` and, for crashes,
`Error Type:` fields in the new log format that AWS is rolling out [S6]. (4) `Throttles` are **not** counted in `Errors`
or `Invocations` [S8]. (5) The 4 KB `--log-type Tail` excerpt is described as "first 4 KB" [S11] and "last 4 KB" [S5]
(AWS pages disagree; same finding as D1 [I3]).

Domain complexity tier: **Complex** - seven services, permission and KMS failures that look alike from the outside, a
strict read-only boundary (the agent must refuse every mutating command and route fixes to the integrator/deployer), and
log content that can contain credentials (the AWS sample `get-logs.sh` output prints `AWS_SESSION_TOKEN` [S11]). Three
critical patterns: (a) classify invocation vs function error before anything else [S2][S5]; (b) for API Gateway, read
`$context.integrationErrorMessage` / `$context.integration.integrationStatus` vs `$context.integration.status` to tell a
Lambda-service problem from a function-code problem [S13][S23][S53]; (c) read the REPORT line's `Init Duration`,
`Max Memory Used` vs `Memory Size`, `Status` and `Error Type` before reading application logs [S6][S11].

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)
> All commands in this section are **read-only** unless marked M (mutating). M commands are listed only so the agent can
> recognise and refuse them (see F1).

### ✅ Mandatory Patterns

**A1. Read-only command allowlist; everything else is refused and handed off**
> Confidence: 🟢 High for the command semantics | [✓✓ Triangulated | CLI reference 2.39.0 (2026-10-28) + Lambda dev guide (2026-10-28)]; the allowlist itself is repo policy [I2][I3]
- Why: the debugger is read-only by unit definition. The listed commands only return data: `get-function-configuration`
  "Returns the version-specific settings" [S42]; `get-policy` "Returns the resource-based IAM policy" [S57];
  `simulate-principal-policy` "does not perform the API operations; it only checks the authorization" [S38];
  `logs tail` / `filter-log-events` / `start-query` + `get-query-results` read log events [S39][S40][S41][S56];
  `xray get-trace-summaries` / `batch-get-traces` read traces [S36][S37]; `cloudwatch get-metric-statistics` reads
  datapoints [S58]; `lambda get-account-settings` reads quotas [S26].
- Code:
  ```bash
  # Representative — adapt to your environment (AWS docs 2026-10-28, CLI 2.39.0). READ-ONLY allowlist.
  aws lambda get-function-configuration --function-name my-function:prod          # [S42]
  aws lambda get-function --function-name my-function --query 'Configuration.[State, LastUpdateStatus]'  # [S29]
  aws lambda get-policy --function-name my-function --qualifier prod              # [S57]
  aws lambda get-account-settings                                                 # [S26]
  aws lambda list-event-source-mappings --function-name my-function               # [S27] (named there)
  aws logs tail /aws/lambda/my-function --since 30m                               # [S39]
  aws logs filter-log-events --log-group-name /aws/lambda/my-function \
      --start-time <epoch-ms> --end-time <epoch-ms> --filter-pattern "REPORT"     # [S40]
  aws logs start-query --log-group-name /aws/lambda/my-function \
      --start-time <epoch-s> --end-time <epoch-s> --query-string '<query>'        # [S41]
  aws logs get-query-results --query-id <id>                                      # [S56]
  aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Throttles \
      --dimensions Name=FunctionName,Value=my-function --start-time <iso> --end-time <iso> \
      --period 60 --statistics Sum                                                # [S58][S8]
  aws xray get-trace-summaries --start-time <epoch> --end-time <epoch> --filter-expression '<expr>'  # [S36]
  aws xray batch-get-traces --trace-ids <trace-id>                                # [S37]
  aws iam simulate-principal-policy --policy-source-arn <execution-role-arn> \
      --action-names secretsmanager:GetSecretValue --resource-arns <secret-arn>   # [S38]
  ```
- Note: the `FunctionName` dimension name for `AWS/Lambda` is not stated on the pages read (S59 gives no dimension list)
  - (medium confidence).
- Source: [S36][S37][S38][S39][S40][S41][S42][S56][S57][S58] (2026-10-28)

**A2. Classify the failure first: invocation error vs function error**
> Confidence: 🟢 High | [✓✓ Triangulated | troubleshooting-execution (2026-10-28) + Invoke API reference (2026-10-28)]
- Why: "When your function code or the Lambda runtime return an error, the status code in the response from Lambda is
  200 OK. The presence of an error in the response is indicated by a header named `X-Amz-Function-Error`. 400 and
  500-series status codes are reserved for invocation errors." [S2]. The Invoke API: "The status code in the API response
  doesn't reflect function errors. Error codes are reserved for errors that prevent your function from executing, such as
  permissions errors, quota errors, or issues with your function's code and configuration." [S5]. `Throttles` and other
  invocation errors "don't count as either `Invocations` or `Errors`" [S8].
- Code:
  ```text
  # Decision (AWS docs 2026-10-28)
  Invoke API status 4xx/5xx (e.g. 429 TooManyRequestsException, 502 KMS*/ENI*/EC2*, 409 SnapStartNotReady)  -> invocation error -> branch B
  Invoke API status 200 + X-Amz-Function-Error present                                                     -> function error   -> branch C
  Metric view: Throttles>0 => invocation error class; Errors>0 => function error class (Errors excludes throttles)  [S8]
  ```
- The value set of `X-Amz-Function-Error` (e.g. `Unhandled` / `Handled`) is not listed on the Invoke API page, which only
  says "If present, indicates that an error occurred during function execution" [S5] - **(unverified)** for the values.
- Source: [S2] [S5] [S8] (2026-10-28)

**A3. For API Gateway, map the HTTP status and read the integration-level log variables**
> Confidence: 🟢 High | [✓✓ Triangulated | Lambda services-apigateway-errors (2026-10-28) + API Gateway gateway responses / access-log variables (2026-10-28)]
- Why: "If the Lambda API rejects the invocation request, API Gateway returns a 500 error code. If the Event Function runs
  but returns an error, or returns a response in the wrong format, API Gateway returns a 502. In both cases, the body of
  the response from API Gateway is `{"message": "Internal server error"}`." and "API Gateway does not retry any Lambda
  invocations" [S16]. REST proxy: "If the function output is of a different format, API Gateway returns a `502 Bad
  Gateway` error response." [S21]. REST gateway responses: `INTEGRATION_TIMEOUT` 504, `INTEGRATION_FAILURE` 504,
  `THROTTLED` 429 ("usage plan-, method-, stage-, or account-level throttling limits exceeded"), `QUOTA_EXCEEDED` 429,
  `API_CONFIGURATION_ERROR` 500, `MISSING_AUTHENTICATION_TOKEN` 403 (incl. unsupported method/resource) [S24].
  Access-log variables: `$context.integration.integrationStatus` = "For Lambda proxy integration, the status code returned
  from AWS Lambda, not from the backend Lambda function code"; `$context.integration.status` = "For Lambda proxy
  integrations, this is the status code that your Lambda function code returns"; `$context.integrationErrorMessage` /
  `$context.integration.error` = integration error message [S23][S53].
- Code:
  ```text
  # API Gateway access-log format fragment for diagnosis (REST and HTTP APIs; variables per S23/S53, 2026-10-28)
  $context.requestId $context.status $context.error.responseType "$context.error.message"
  $context.integration.integrationStatus $context.integration.status "$context.integrationErrorMessage"
  $context.integrationLatency $context.awsEndpointRequestId
  # Reading: integrationStatus != 200  -> Lambda service refused/failed the invoke (branch B)
  #          integrationStatus == 200 and status 502 -> function error or malformed proxy response (branch C / A3b)
  ```
- HTTP API: "add the `$context.integrationErrorMessage` logging variable to your log format"; "If your logs don't include
  an error message, add `$context.error.message` and `$context.error.responseType`" [S13].
- Whether `$context.awsEndpointRequestId` equals the Lambda RequestId in the REPORT line is not stated (it is "The AWS
  endpoint's request ID" [S23][S53]) - **(medium confidence)** as a correlation key.
- Source: [S13] [S16] [S21] [S23] [S24] [S53] (2026-10-28)

**A4. Confirm which version/alias actually ran before reading anything else**
> Confidence: 🟢 High | [✓✓ Triangulated | troubleshooting-execution (2026-10-28) + Invoke API (2026-10-28)]
- Why: "first determine that the caller has invoked the intended version or alias ... The version of the function that was
  invoked is always shown in the START log line" [S2]; Invoke returns `ExecutedVersion` - "When you invoke a function
  with an alias, this indicates which version the alias resolved to" [S5]. Log streams are named
  `YYYY/MM/DD[Function version][Execution environment GUID]` [S11]. If API Gateway invokes `$LATEST` instead of the alias
  with provisioned concurrency, cold starts appear [S1].
- Code:
  ```text
  START RequestId: c3252230-c73d-49f6-8844-968c01d1e2e1 Version: $LATEST      # S6 example: Version field = executed version
  ```
- Source: [S1] [S2] [S5] [S11] (2026-10-28)

**A5. Read the platform report lines (REPORT / INIT_REPORT / RESTORE_REPORT) and their exact fields**
> Confidence: 🟢 High | [✓✓ Triangulated | lambda-runtime-environment (2026-10-28) + monitoring-cloudwatchlogs-view (2026-10-28) + snapstart-monitoring (2026-10-28)]
- Why: three platform lines exist for every invocation (START, END, REPORT) [S11]; REPORT fields are `RequestId`,
  `Duration` ("total invocation time for the handler function, excluding `INIT` code"), `Billed Duration`, `Memory Size`,
  `Max Memory Used`, `Init Duration` ("the time taken to run the `INIT` section") [S11]; the new format "includes an
  additional `status` field in the `REPORT` line. In the case of a runtime or extension crash, the `REPORT` line also
  includes a field `ErrorType`" [S6]; SnapStart adds `Restore Duration` and `Billed Restore Duration` and moves
  `Init Duration` into `INIT_REPORT` [S32]; init failures emit `INIT_REPORT ... Phase: init Status: timeout|error Error
  Type: ...` [S6].
- Code:
  ```text
  # Exact examples from AWS pages (2026-10-28)
  REPORT RequestId: 527cb862-4f5e-49a9-9ae4-a7edc90f0fda Duration: 3016.78 ms Billed Duration: 3101 ms Memory Size: 128 MB Max Memory Used: 31 MB Init Duration: 84.00 ms Status: timeout     # S6 new style
  REPORT RequestId: 5b866fb1-7154-4af6-8078-6ef6ca4c2ddd Duration: 133.61 ms Billed Duration: 214 ms Memory Size: 128 MB Max Memory Used: 31 MB Init Duration: 80.00 ms Status: error Error Type: Runtime.ExitError   # S6 new style
  2024-03-04T17:22:38.033Z b70435cc-... Task timed out after 3.00 seconds                                 # S6 old style timeout line
  RequestId: c3252230-... Error: Runtime exited without providing a reason                                # S6 old style crash
  Runtime.ExitError
  INIT_REPORT Init Duration: 1236.04 ms Phase: init Status: timeout                                       # S6
  INIT_REPORT Init Duration: 1236.04 ms Phase: init Status: error Error Type: Extension.Crash             # S6
  RESTORE_REPORT Restore Duration: 1236.04 ms Status: timeout                                             # S6
  RESTORE_REPORT Restore Duration: 1236.04 ms Status: error Error Type: Runtime.ExitError                 # S6
  ```
- Interpretation rules (sourced): `Init Duration` present = new execution environment (cold start; query in S11 uses
  `strcontains(@message, "Init Duration")` for cold-start %) [S11]; for SnapStart "The cold start duration is the sum of
  `Restore Duration` + `Duration`" [S32]; a REPORT `Duration` larger than START->REPORT wall time indicates a suppressed
  init after a previous failure [S6]; `Max Memory Used` equal to `Memory Size` - AWS query "Invocations using 100% of
  assigned memory" uses `@maxMemoryUsed=@memorySize` [S11].
- The X-Ray fields in the plain-text REPORT line (`XRAY TraceId:` ...) are not shown on any page read; only the Logs
  Insights fields `@xrayTraceId` / `@xraySegmentId` are documented [S9][S11] - **(unverified)** for the line text.
- Source: [S6] [S11] [S32] (2026-10-28)

**A6. Check the function's control-plane state before blaming code**
> Confidence: 🟢 High | [✓✓ Triangulated | functions-states (2026-10-28) + FunctionConfiguration API (2026-10-28)]
- Why: "Event Functions can only be successfully invoked while active"; `Pending` -> "Any invocations or other API actions
  that operate on the function fail"; `Inactive` -> "the invocation fails and Lambda sets the function to pending state";
  while `LastUpdateStatus` is `InProgress` or `Failed`, "Invocations continue to use the function's previous code and
  configuration" [S29]. `StateReasonCode` / `LastUpdateStatusReasonCode` values include `InsufficientRolePermissions`,
  `SubnetOutOfIPAddresses`, `EniLimitExceeded`, `KMSKeyAccessDenied`, `KMSKeyNotFound`, `InvalidStateKMSKey`,
  `DisabledKMSKey`, `InvalidRuntime`, `InvalidZipFileException`, `FunctionError.InitTimeout`,
  `FunctionError.RuntimeInitError`, `FunctionError.InvalidEntryPoint`, `FunctionError.PermissionDenied`,
  `FunctionError.InitResourceExhausted` (full list in S30) [S30]. State values also include `Deactivating`,
  `Deactivated`, `ActiveNonInvocable`, `Deleting` [S30].
- Code:
  ```bash
  # Representative — adapt to your environment (2026-10-28)
  aws lambda get-function-configuration --function-name my-function:prod \
    --query '{State:State,Reason:StateReasonCode,Upd:LastUpdateStatus,UpdReason:LastUpdateStatusReasonCode,Ver:Version,Timeout:Timeout,Mem:MemorySize,SnapStart:SnapStart,Vpc:VpcConfig,Kms:KMSKeyArn,Log:LoggingConfig,Trace:TracingConfig}'
  # Expected healthy: State=Active, LastUpdateStatus=Successful   [S29]
  ```
- Family fact (row 33 [I1]): for SnapStart, confirm `SnapStart.OptimizationStatus=On` and `State=Active` on the version.
- "A deploy that did not take effect" (old behaviour after a deploy) is diagnosed here: `LastUpdateStatus=Failed` keeps
  the previous code [S29]; the deploy procedure itself is D1 [I3].
- Source: [S29] [S30] [S42] (2026-10-28)

**A7. Query metrics with the statistic AWS prescribes, and alarm on throttles separately**
> Confidence: 🟢 High | [✓✓ Triangulated | monitoring-metrics-types (2026-10-28) + troubleshooting-invocation (2026-10-28)]
- Why: invocation metrics "View these metrics with the `Sum` statistic"; performance metrics (`Duration`) "with the
  `Average` or `Max` statistic" and percentiles; concurrency metrics "view these metrics with the `Max` statistic" [S8].
  `Errors` = "invocations that result in a function error ... The runtime returns errors for issues such as timeouts and
  configuration errors"; error rate = `Errors`/`Invocations`; "the timestamp on an error metric reflects when the Event
  Function was invoked, not when the error occurred" [S8]. `ConcurrentExecutions` reaching the account quota or reserved
  concurrency means "Lambda throttles additional invocation requests" [S8]; `ProvisionedConcurrencySpilloverInvocations`
  > 0 means cold starts beyond provisioned concurrency [S1][S8]. Lambda sends metrics "in 1-minute intervals" [S59].
- Code:
  ```text
  Errors (Sum) / Invocations (Sum)        -> function error rate                      [S8]
  Throttles (Sum) > 0                      -> TooManyRequestsException; not in Errors  [S8]
  ConcurrentExecutions (Max) vs quota      -> aws lambda get-account-settings           [S8][S26]
  Duration (p99/Max) vs configured Timeout -> timeouts; Duration excludes cold start    [S8]
  AsyncEventAge / AsyncEventsDropped       -> EventBridge (async) backlog / loss        [S8]
  ```
- Source: [S1] [S8] [S26] [S59] (2026-10-28)

**A8. Separate the two permission planes: resource-based policy (who may invoke) vs execution role (what the code may call)**
> Confidence: 🟢 High | [✓✓ Triangulated | Lambda services-apigateway (2026-10-28) + troubleshooting-invocation (2026-10-28) + IAM CLI simulate-principal-policy (2026-10-28)]
- Why: "API Gateway gets permission to invoke your function from the function's resource-based policy" [S25]; "You grant
  other services and accounts permission to invoke a function in the function's resource-based policy" [S1]; the HTTP API
  troubleshooting page shows logs saying "API Gateway didn't have the required permissions to invoke the Lambda function"
  [S13]. The execution role "grants the function permission to access AWS services and resources" [S61].
  `simulate-principal-policy` evaluates identity-based policies (and SCPs) of the given principal; it "does not
  automatically retrieve policies for the specified resources" and resource-based policies are "not supported for IAM
  roles" [S38].
- Code:
  ```bash
  # Who may invoke? (read-only)                                                    [S57][S25]
  aws lambda get-policy --function-name my-function --qualifier prod --query Policy --output text
  #   expect Principal.Service=apigateway.amazonaws.com, Action=lambda:InvokeFunction,
  #   aws:SourceArn arn:aws:execute-api:<region>:<acct>:<api-id>/<stage>/<METHOD>/<path> (wildcards allowed)
  #   (EventBridge: Principal events.amazonaws.com, source = rule ARN - (medium confidence), search snippet only)
  # What may the code call? (read-only)                                             [S38]
  aws iam simulate-principal-policy --policy-source-arn arn:aws:iam::123456789012:role/my-fn-role \
      --action-names dynamodb:PutItem --resource-arns arn:aws:dynamodb:...:table/t
  #   EvalDecision: allowed | explicitDeny | implicitDeny ; MatchedStatements ; ResourceSpecificResults
  ```
- REST APIs: the execution-log message "Execution failed due to configuration error: Invalid permissions on Lambda function"
  appears only in an AWS Knowledge Center article that could not be fetched (HTTP 403) [K1] - exact string
  **(medium confidence)**. Region rule: "the Region identifier in the source ARN must match the Region of the function,
  not the Region of the API" [S25].
- An `AccessDeniedException` raised by the function's own SDK call surfaces as a function error in the function's log
  (branch C); this mapping is an inference from S2/S61, not a page statement - **(medium confidence)**.
- Source: [S1] [S13] [S25] [S38] [S57] [S61] (2026-10-28)

**A9. SQS ESM: verify the queue/ESM configuration that decides where failed messages go**
> Confidence: 🟢 High | [✓✓ Triangulated | services-sqs-configure (2026-10-28) + services-sqs-errorhandling (2026-10-28) + SQS metrics (2026-10-28)]
- Why: by default "if your function encounters an error while processing a batch, all messages in that batch become
  visible in the queue again after the visibility timeout expires" [S44]; "set the source queue's visibility timeout to at
  least six times the configuration timeout on your function" (plus `MaximumBatchingWindowInSeconds` when batching)
  and `maxReceiveCount` "to at least 5" [S48]; "If your function throws an exception, the entire batch is considered a
  complete failure" even with `ReportBatchItemFailures` [S27]; complete-failure responses include invalid JSON, empty or
  null `itemIdentifier`, or an ID that doesn't exist [S27]; for throttling Lambda "continues to retry the message until
  the message's timestamp exceeds your queue's visibility timeout, at which point Lambda drops the message" [S27].
  Monitor `NumberOfMessagesDeleted` (drop to 0 = failures not reported correctly) and `ApproximateAgeOfOldestMessage`
  [S27]; for a DLQ use `ApproximateNumberOfMessagesVisible` [S43].
- Code:
  ```bash
  # Representative — adapt to your environment (2026-10-28)
  aws lambda list-event-source-mappings --function-name my-function \
    --query 'EventSourceMappings[].{UUID:UUID,State:State,Why:StateTransitionReason,Last:LastProcessingResult,Resp:FunctionResponseTypes,Batch:BatchSize,Window:MaximumBatchingWindowInSeconds,Scaling:ScalingConfig,Metrics:MetricsConfig}'
  # ESM State: Creating|Enabling|Enabled|Disabling|Disabled|Updating|Deleting   [S49]
  aws sqs get-queue-attributes --queue-url <url> --attribute-names VisibilityTimeout RedrivePolicy   # (medium confidence: command named from SQS API, page not fetched)
  ```
- Source: [S27] [S43] [S44] [S48] [S49] (2026-10-28)

**A10. Allow for log latency and log loss before concluding "no logs = not invoked"**
> Confidence: 🟢 High | [✓✓ Triangulated | troubleshooting-execution (2026-10-28) + monitoring-cloudwatchlogs (2026-10-28)]
- Why: "It might take 5 to 10 minutes for logs to show up after a function invocation" [S2][S7]; missing logs can be a
  missing execution-role permission (`logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` /
  `AWSLambdaBasicExecutionRole`) [S2][S7], CloudWatch Logs throttling, or Lambda dropping logs above ~2 MB/s per stream
  (`logsDropped` event in JSON format) [S2][S12]. Default log group `/aws/lambda/<function-name>` unless configured
  otherwise [S7].
- Source: [S2] [S7] [S12] (2026-10-28)

### ⚠️ Conditional Patterns

**C1. API Gateway logs are not enabled - how to proceed**
> Confidence: 🟢 High (facts) / decision is the user's
- Options: A) ask the user (via the orchestrator) to enable logging, then reproduce; B) diagnose from Lambda logs/metrics
  and X-Ray only; C) for REST, use API Gateway metrics `5XXError`, `IntegrationLatency`, `Latency` [S50].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A enable logs | Exact integration error text [S13] | Needs a mutating change (stage settings; REST also needs the account `cloudWatchRoleArn` per Region [S18][S20]) - the debugger cannot do it | 5xx with no Lambda-side error |
  | B Lambda side only | No change needed | Cannot see 500 caused by missing invoke permission (Lambda never ran) [S16] | Function errors visible in Lambda logs |
  | C APIGW metrics | Cheap, always on (ApiName/Stage) [S50] | Per-method dimensions need detailed metrics (extra cost) [S50] | Trend/rate questions |

- Facts: REST execution log group `API-Gateway-Execution-Logs_{rest-api-id}/{stage_name}`, events truncated at 1 KB with
  standard logging; levels `ERROR`/`INFO`; "We recommend that you don't use Data tracing for production APIs" [S20];
  CloudWatch Logs delivery replaces the managed group when configured [S20]. HTTP APIs: the logging page documents
  access logging to a log group you create [S19]; an HTTP API execution-log feature is not described on the pages read
  - **(medium confidence)** that HTTP APIs have access logs only.
- Agent: "Ask user whether API Gateway logging can be enabled (by the deployer, not the debugger) or whether to continue
  with Lambda-side evidence only."
- Source: [S13] [S16] [S18] [S19] [S20] [S50] (2026-10-28)

**C2. Which log tool: `tail`, `filter-log-events` or Logs Insights**
> Confidence: 🟡 Medium (cost comparison unverified)
- Options: A) `aws logs tail` (default start "ten minutes in the past", relative `--since` like `5m`, no compound units)
  [S39]; B) `filter-log-events` (epoch **milliseconds**, filter pattern, paginated, `nextToken` expires after 24 h) [S40];
  C) `start-query` + `get-query-results` (epoch **seconds**, up to 50 log groups, limit up to 100,000, statuses
  `Scheduled|Running|Complete|Failed|Cancelled|Timeout|Unknown`, queries time out after 60 minutes) [S41][S56].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | tail | Fast look at recent events [S39] | No aggregation | Live repro, last minutes |
  | filter-log-events | Exact lines for a RequestId [S40] | Pagination, ms timestamps | One request's START..REPORT |
  | Logs Insights | Aggregation over REPORT lines [S10][S11] | Charged per data scanned (unverified - pricing page not read) | Cold-start %, memory, p99 |

- Agent: "Ask user for the time window and whether a Logs Insights scan (billable) is acceptable."
- Source: [S10] [S11] [S39] [S40] [S41] [S56] (2026-10-28)

**C3. Plain-text vs JSON log format changes how lines are matched**
> Confidence: 🟡 Medium
- Options: Text (default for all runtimes) or JSON (`LoggingConfig.LogFormat`) [S51]. In JSON, platform lines become
  objects with `time`, `type` (e.g. `platform.report`), `record` [S51], whose metrics are `billedDurationMs`,
  `durationMs`, `initDurationMs`, `maxMemoryUsedMB`, `memorySizeMB`, `restoreDurationMs` [S12]; application logs carry
  `timestamp`, `level`, `message`, `requestId` (Java: `AWSrequestId`) [S51].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Text | Matches every AWS sample query (`@type = "REPORT"`, `like /Task timed out/`) [S10][S11] | Unstructured app logs | Default functions |
  | JSON | Structured filters, `logsDropped` event [S2][S51] | Whether `@type`/`@duration` discovery works on JSON platform records is not stated - (unverified) | Functions already on JSON |

- Agent: "Read `LoggingConfig.LogFormat` from get-function-configuration first; for JSON, match `type = 'platform.report'`
  and `record.metrics.*` (medium confidence)."
- Source: [S10] [S11] [S12] [S51] (2026-10-28)

**C4. Is X-Ray evidence available?**
> Confidence: 🟢 High (facts)
- Options: A) Active tracing on: inspect `AWS::Lambda` (service) vs `AWS::Lambda::Function` (code) segments - "If the
  `AWS::Lambda` segment shows an error, the Lambda service had an issue. If the `AWS::Lambda::Function` segment shows an
  error, your Event Function had an issue" [S52]; B) PassThrough (default): no Lambda traces [S52]; C) X-Ray Transaction
  Search enabled: "You cannot find traces through this API" [S37].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Traces | Service vs code fault, downstream latency [S52] | Sampled only: "1 request per second and 5 percent of additional requests" [S52] | Latency/timeout branches |
  | Logs only | Every invocation | No downstream breakdown | Tracing off |

- Facts: `get-trace-summaries` requires `--start-time`/`--end-time`; summary fields `HasError` (400-series),
  `HasFault` (500-series), `HasThrottle` (429), `ResponseTime` [S36]; `batch-get-traces --trace-ids` returns `Segments[].Document`
  and `UnprocessedTraceIds` [S37]. Segment structure is changing (old: `Initialization`/`Invocation`/`Overhead`/`Restore`
  subsegments; new: `Init` subsegment plus annotations `aws.responseLatency`, `aws.responseDuration`,
  `aws.runtimeOverhead`, `aws.extensionOverhead`) [S52]. The CLI page's example output for get-trace-summaries is a URL
  list, not `TraceSummaries` - treat as a doc defect [S36]. Maximum time range per call: not stated [S36] - (unverified).
- Agent: "Ask user whether Active tracing is enabled (TracingConfig.Mode) before planning X-Ray steps."
- Source: [S36] [S37] [S52] (2026-10-28)

**C5. Reproducing by invoking the function**
> Confidence: 🟢 High (facts) / decision is the user's
- Options: A) `aws lambda invoke --invocation-type DryRun` - "Validate parameter values and verify that the user or role
  has permission to invoke the function", status 204 [S5]; B) real invoke (`RequestResponse`) with `--log-type Tail`
  (sync only, 4 KB, base64) [S5][S11] - **executes function code**, side effects possible; C) no invoke, logs only.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | DryRun | Zero execution [S5] | Proves only the caller's permission | Testing invoke permission of the agent's principal |
  | Real invoke | Fresh evidence | Side effects; not read-only | Side-effect-free payload approved by user (D1 smoke rules [I3]) |
  | None | Strictly read-only | Depends on existing logs | Default |

- Agent: "Ask user before any real invoke; DryRun does not prove that API Gateway may invoke (different principal)."
- Source: [S5] [S11] [I3] (2026-10-28)

**C6. SnapStart functions: where init and restore evidence lives**
> Confidence: 🟢 High
- Options: SnapStart on (published versions only [I1 row 16]) vs off.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | SnapStart on | Restore instead of init | `Init Duration` absent from REPORT; it is in `INIT_REPORT`; REPORT has `Restore Duration`/`Billed Restore Duration` [S32] | Java managed runtimes |
  | Off | Classic REPORT `Init Duration` [S11] | 10 s init limit applies [S6] | Native/OS-only runtime (family: Quarkus native [I1 row 16]) |

- Agent: "Read `SnapStart` from get-function-configuration, then choose INIT_REPORT/RESTORE_REPORT or REPORT."
- Source: [S6] [S11] [S32] [I1] (2026-10-28)

### 🚫 Forbidden Patterns

**F1. Running any mutating AWS command while diagnosing**
> Severity: Critical
> Confidence: 🟢 High (command semantics from AWS pages; prohibition is unit policy [I3])
- Why: the agent is read-only; fixes belong to the integrator (code) or deployer (D1) [I3]. Several "diagnostic-looking"
  commands mutate: `update-event-source-mapping` (changes ESM, e.g. metrics/response types) [S8][S27];
  `update-function-configuration` (AWS even recommends "a trivial update" to refresh credentials - a mutation) [S2];
  `add-permission` [S13][S25]; `update-alias` rollback [S4]; `put-function-concurrency` / setting concurrency to 0 to stop
  a loop [S1]; `aws apigatewayv2 update-stage --access-log-settings` to enable logs [S19]; `logs create-log-group` [S19];
  `iam attach-role-policy` [S7]; SQS receive on the source queue hides messages for the visibility timeout [S44]
  (inference that a manual receive behaves like Lambda's - (medium confidence)).
- Impact: changes production behaviour, can drop or delay messages, and voids the read-only guarantee.
- ❌ Wrong:
  ```bash
  aws lambda update-event-source-mapping --uuid <uuid> --metrics-config Metrics=EventCount   # mutates the ESM
  aws lambda add-permission --function-name my-function --principal apigateway.amazonaws.com ...  # mutates policy
  aws lambda update-function-configuration --function-name my-function --timeout 30          # mutates function
  ```
- ✅ Correct:
  ```bash
  aws lambda list-event-source-mappings --function-name my-function     # read the ESM          [S27]
  aws lambda get-policy --function-name my-function                     # read the policy       [S57]
  aws lambda get-function-configuration --function-name my-function     # read the timeout      [S42]
  # then hand off: "Fix required: <what>, owner: deployer/integrator" (agent output, no AWS call)
  ```
- Source: [S1] [S2] [S7] [S13] [S19] [S25] [S27] [S42] [S44] [S57] (2026-10-28)

**F2. Declaring the function healthy because `Errors` = 0**
> Severity: High
> Confidence: 🟢 High
- Why: "Throttled requests and other invocation errors don't count as either `Invocations` or `Errors`" [S8]; API Gateway
  returns 500 when Lambda rejects the invoke [S16].
- Impact: throttling or permission/KMS failures go unnoticed while clients see 500s.
- ❌ Wrong:
  ```text
  Errors(Sum)=0 over 1h  =>  "Lambda is fine, the 500s are an API Gateway problem"
  ```
- ✅ Correct:
  ```text
  Check Errors(Sum) AND Throttles(Sum) AND ConcurrentExecutions(Max) AND APIGW $context.integration.integrationStatus  [S8][S23][S53]
  ```
- Source: [S8] [S16] [S23] [S53] (2026-10-28)

**F3. Reading Invoke `StatusCode: 200` as success**
> Severity: High
> Confidence: 🟢 High
- Why: function errors return 200 with `X-Amz-Function-Error` (CLI JSON key `FunctionError`) [S2][S5]; D1 smoke test
  checks "no `FunctionError` key" [I3].
- Impact: false-positive post-deploy verification.
- ❌ Wrong:
  ```text
  {"StatusCode": 200, "ExecutedVersion": "7", "FunctionError": "..."}  ->  "OK"
  ```
- ✅ Correct:
  ```text
  {"StatusCode": 200, "ExecutedVersion": "7"} and no FunctionError key and payload is the expected shape  ->  "OK"   [S5][I3]
  ```
- Source: [S2] [S5] [I3] (2026-10-28)

**F4. Using `IteratorAge` to judge an SQS backlog**
> Severity: Medium
> Confidence: 🟢 High
- Why: `IteratorAge` is "For DynamoDB, Kinesis, and Amazon DocumentDB event sources" [S8]; for SQS use
  `AWS/SQS ApproximateAgeOfOldestMessage` (seconds, dimension `QueueName`) [S43]; ESM metrics for SQS
  (`PolledEventCount`, `InvokedEventCount`, `FailedInvokeEventCount`, `DeletedEventCount`, `FilteredOutEventCount`) exist
  only when `EventCount` metrics are enabled on the ESM [S8].
- Impact: empty graph read as "no backlog".
- ❌ Wrong:
  ```bash
  aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name IteratorAge ...   # SQS-triggered function
  ```
- ✅ Correct:
  ```bash
  aws cloudwatch get-metric-statistics --namespace AWS/SQS --metric-name ApproximateAgeOfOldestMessage \
    --dimensions Name=QueueName,Value=my-queue --statistics Maximum --period 60 --start-time <iso> --end-time <iso>  # [S43][S58]
  ```
- Note: `ApproximateAgeOfOldestMessage` excludes messages received 3+ times and not deleted on standard queues
  ("poison-pill messages ... are excluded") [S43] - check the DLQ's `ApproximateNumberOfMessagesVisible` too [S43].
- Source: [S8] [S43] [S58] (2026-10-28)

**F5. Expecting a Lambda throttle to reach the API client as 429**
> Severity: Medium
> Confidence: 🟢 High
- Why: Lambda `TooManyRequestsException` is an invocation rejection -> API Gateway returns **500** [S5][S16]; **429**
  from API Gateway means API Gateway's own throttling (`THROTTLED`) or usage-plan quota (`QUOTA_EXCEEDED`) [S24]
  (account default 10,000 RPS, burst bucket 5,000; 2,500/1,250 in some Regions [S17]).
- Impact: looking at the wrong service's limits.
- ❌ Wrong:
  ```text
  Client got 429  ->  raise Lambda reserved concurrency
  ```
- ✅ Correct:
  ```text
  Client got 429  ->  API Gateway throttle/usage plan (stage/method/account limits)        [S17][S24]
  Client got 500 + Lambda Throttles>0 / integrationStatus 429  ->  Lambda concurrency    [S8][S16][S23]
  ```
- Note: the brief's "throttling 429/503" is not what the pages say for API Gateway + Lambda; 503 for this path is not
  documented on any page read - (unverified).
- Source: [S5] [S8] [S16] [S17] [S23] [S24] (2026-10-28)

**F6. Pasting raw environment dumps or Data-tracing logs into the diagnosis report**
> Severity: High
> Confidence: 🟢 High
- Why: the AWS sample log output includes `"AWS_SESSION_TOKEN": "AgoJb3JpZ2luX2VjELj..."` [S11]; REST Data tracing
  "can result in logging sensitive data" and is not recommended for production [S20]; family rule 7 forbids PII in logs
  [I2].
- Impact: credential/PII leak into chat transcripts and tickets.
- ❌ Wrong:
  ```text
  Report: "Log line: ... AWS_SESSION_TOKEN: AgoJb3Jp... , event body: {email: ..., card: ...}"
  ```
- ✅ Correct:
  ```text
  Report: "RequestId <id>, REPORT Status: error Error Type: Runtime.ExitError, Max Memory Used 128/128 MB; secrets redacted"
  ```
- Source: [S11] [S20] [I2] (2026-10-28)

**F7. Treating `simulate-principal-policy` on the execution role as proof that API Gateway/EventBridge may invoke**
> Severity: Medium
> Confidence: 🟢 High
- Why: invoke permission for services lives in the function's resource-based policy [S1][S25]; the simulator does not
  fetch resource policies and does not support them for roles [S38].
- Impact: missed "Invalid permissions" 500s.
- ❌ Wrong:
  ```bash
  aws iam simulate-principal-policy --policy-source-arn <fn-execution-role> --action-names lambda:InvokeFunction
  ```
- ✅ Correct:
  ```bash
  aws lambda get-policy --function-name my-function --qualifier prod   # principal, action, SourceArn stage/method   [S25][S57]
  ```
- Source: [S1] [S25] [S38] [S57] (2026-10-28)

**F8. Mixing Lambda Web Functions error types into Event Function diagnosis**
> Severity: Medium
> Confidence: 🟢 High
- Why: `Runtime.OutOfMemory`, `Runtime.Unreachable`, `lambda-web-error-type` headers belong to the separate Lambda Web
  Functions product page [S62]; Event Function crashes appear as REPORT `Status: error Error Type: Runtime.ExitError`
  [S6].
- Impact: searching for strings Event Functions never emit.
- ❌ Wrong:
  ```text
  filter @message like /Runtime.OutOfMemory/        # Web Functions error type   [S62]
  ```
- ✅ Correct:
  ```text
  filter @type = "REPORT" and @maxMemoryUsed = @memorySize    # AWS query for 100% memory  [S11]
  ```
- Source: [S6] [S11] [S62] (2026-10-28)

---

## Migration Guide

> Confidence: 🟡 Medium | Sources: lambda-runtime-environment (2026-10-28) + services-xray (2026-10-28) + IAM CLI (2026-10-28). AWS docs are not versioned; these are "changes in progress" stated on current pages.

**Breaking changes (doc state 2026-10-28)**:
- ⚠️ Migration Note - **System log format change**: "AWS is currently implementing changes ... all functions in all AWS
  Regions except the China and GovCloud regions will transition to use the new-format log messages and trace segments"
  [S6][S52]. Old style: separate `Task timed out after N seconds` / `Error: Runtime exited without providing a reason`
  lines; new style: `REPORT ... Status: timeout` / `Status: error Error Type: Runtime.ExitError` and no separate line
  [S6]. Queries must match both (`like /Task timed out/` OR `Status: timeout`) during the transition.
- ⚠️ Migration Note - **X-Ray segment change**: `Invocation`/`Overhead` subsegments replaced by `aws.*` annotations on
  `AWS::Lambda::Function` [S52].
- ⚠️ Migration Note - **simulate-principal-policy output**: "The simulator now returns a single `EvaluationResult` per
  action, regardless of how many resource ARNs are provided"; per-resource decisions in `ResourceSpecificResults` [S38].
- ⚠️ Migration Note - **REST execution logs**: CloudWatch Logs delivery, when configured, "replaces standard execution
  logging"; the managed group `API-Gateway-Execution-Logs_{rest-api-id}/{stage_name}` "no longer receives new events" [S20].
- Terminology: the Lambda guide now says "Lambda Event Function"; "Lambda Web Functions", "Lambda Managed Instances",
  "Lambda MicroVMs" and "durable functions" are separate features with different limits [S6][S54][S62] - out of scope.

**Upgrade steps** (for skills/queries written against older docs):
1. Make timeout/crash queries match both old and new REPORT styles [S6].
2. Read `ResourceSpecificResults` when simulating against several ARNs [S38].
3. Locate REST execution logs via the stage's delivery configuration, not only the managed log group name [S20].

**Compatibility matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| AWS CLI v2 | 2.39.0 (reference version read) | n/a | `lambda`, `logs`, `xray`, `iam`, `cloudwatch` pages [S36]-[S42] |
| Log format | Text (default) | JSON | Platform-event JSON `record.metrics.*` [S12][S51] |
| Java runtimes (family) | `java17`/`java17.al2023`/`java21`/`java25` | n/a | family fact row 15 [I1]; JSON app logs supported for all Java runtimes except Java 8 on AL1 [S51] |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | Lambda troubleshooting pages + API Gateway pages + CLI reference, all 2026-10-28]

**Lifecycle (the read-only diagnosis loop)**:
```text
// Init:    collect context -> function name, alias/version, Region, entry (REST | HTTP API | SQS | EventBridge), UTC window, symptom
// Usage:   Step 0 state -> Step 1 classify -> Step 2 branch (A..H) -> Step 3 evidence -> Step 4 verdict + hand-off
// Cleanup: none (no resources created); redact secrets in the report (F6)
```

**Step 0 - control plane** (A6): `get-function-configuration --function-name <fn>:<alias>` -> `State`, `StateReasonCode`,
`LastUpdateStatus`, `LastUpdateStatusReasonCode`, `Version`, `Timeout`, `MemorySize`, `VpcConfig`, `KMSKeyArn`,
`SnapStart`, `LoggingConfig`, `TracingConfig` [S30][S42]. Not `Active`/`Successful` -> branch G.

**Step 1 - classify** (A2): invocation error (Invoke 4xx/5xx; metric `Throttles`; APIGW `integrationStatus` != 200)
vs function error (200 + `X-Amz-Function-Error`; metric `Errors`; APIGW `integration.status` from code) [S2][S5][S8][S23].

**Step 2 - elimination tree by symptom**

```text
A. API Gateway entry (REST or HTTP API, Lambda proxy)                                        [S13][S16][S21][S24]
 A1 Client 429 ............. APIGW throttle/usage plan (THROTTLED / QUOTA_EXCEEDED) - not Lambda        [S17][S24]
 A2 Client 403 ............. MISSING_AUTHENTICATION_TOKEN (wrong method/path/stage), ACCESS_DENIED, WAF  [S24]
 A3 Client 500 ............. Lambda rejected the invoke -> go to B (permission, throttle, KMS, ENI, state) [S16]
     REST log: "Execution failed due to configuration error: Invalid permissions on Lambda function"   [K1] (medium confidence)
     HTTP API: $context.integrationErrorMessage shows missing invoke permission                          [S13]
     SnapStart version still Pending -> "you might get a 500 error in API Gateway"                     [S31]
     Also API_CONFIGURATION_ERROR (500) for invalid API config                                         [S24]
 A4 Client 502 ............. Function ran: function error -> C; or response not in proxy format          [S16][S21]
     REST/HTTP 1.0 format: {isBase64Encoded, statusCode, headers, multiValueHeaders, body}               [S21][S22]
     HTTP 2.0 format: valid JSON without statusCode is inferred as 200 application/json                  [S22]
     REST log string "Malformed Lambda proxy response" only in AWS Knowledge Center [K2] (medium confidence)
 A5 Client 504 ............. Integration timeout: REST 50 ms-29 s (raisable for Regional/private), HTTP 30 s max  [S15][S14][S24]
     -> compare Lambda Duration/Timeout; long work should not sit behind a sync API (D1/architecture)
     HTTP API timeout status code: not stated on pages read (unverified)
 A6 Client 200 but wrong data  -> A4 of the tree in reverse: check executed version (A4 pattern)          [S2][S5]

B. Lambda invocation errors (Invoke API status, StateReasonCode, APIGW integrationStatus)              [S1][S5][S29][S30]
 B1 429 TooManyRequestsException (retryAfterSeconds) ...... concurrency: account (ConcurrentInvocationLimitExceeded)
     or function (ReservedFunctionConcurrentInvocationLimitExceeded); default account 1,000; RPS limit = 10x concurrency;
     scaling 1,000 envs / 10 s per function; >=100 unreserved always kept                                  [S5][S26][S54]
     Evidence: Throttles(Sum), ConcurrentExecutions(Max), ClaimedAccountConcurrency, get-account-settings  [S8][S26]
     "One function is using all concurrency" -> reserved concurrency question for the owner                 [S1]
 B2 502 KMSAccessDeniedException | KMSDisabledException | KMSInvalidStateException | KMSNotFoundException
     "Lambda couldn't decrypt the environment variables ..." ; StateReasonCode KMSKeyAccessDenied/DisabledKMSKey/... [S5][S30]
     KMSDisabledException: key disabled or grant revoked                                                     [S1]
     Default aws/lambda key needs no KMS permissions; customer managed key uses a grant Lambda creates      [S33]
 B3 502 ENILimitReachedException | SubnetIPAddressLimitReachedException | EC2ThrottledException | EC2AccessDeniedException
     | ENINotReadyException | InvalidSubnetIDException | InvalidSecurityGroupIDException                    [S5]
     ENI quota 3,000 per VPC                                                                                [S3][S54]
 B4 409 ResourceConflictException ... "currently in the following state: Pending" (VPC create)            [S1][S5]
     502 ResourceNotReadyException ... "function is inactive and its VPC connection is no longer available" [S5]
 B5 SnapStart: 409 SnapStartNotReadyException (version Inactive after 14 days idle or recycled; wait for Active) [S5][S31][I1 row 33]
     408 SnapStartTimeoutException (restore + afterRestore > 10 s; network/credential issues) ; 400 SnapStartException
     (afterRestore hook error) ; 409 SnapStartRegenerationFailureException                                    [S5][S6][S31]
     Quarkus guide says "Restoration is limited to 2 seconds" - cite both, do not choose                      [I1 row 21]
 B6 Other: 413 RequestTooLargeException (6 MB sync / 1 MB async), 400 RecursiveInvocationException,
     502 InvalidRuntimeException, 502 InvalidZipFileException, 500 ServiceException                          [S5][S54]
 B7 Caller not authorised: "is not authorized to perform: lambda:InvokeFunction" (identity side of caller)  [S1]

C. Function errors (REPORT Status/Error Type; function log; X-Amz-Function-Error)                          [S2][S6]
 C1 Timeout ............ "Task timed out after N seconds" / REPORT "Status: timeout"; Duration ~ Timeout     [S6]
     Downstream slowness, large payloads, VPC egress (-> E)                                                [S2][S3][S35]
     Max timeout 900 s; console default 3 s                                                                [S35][S54]
 C2 Init failure ....... INIT_REPORT Status: timeout|error ; "Sandbox.Timedout"; Init limit 10 s (on-demand),
     retried at first invoke with function timeout (suppressed init); 15 min for PC/SnapStart               [S1][S6]
     StateReasonCode FunctionError.InitTimeout / RuntimeInitError / InitResourceExhausted                   [S30]
 C3 Crash .............. REPORT "Status: error Error Type: Runtime.ExitError" / "Runtime exited without providing a reason" [S6]
     Query "Invocations where Lambda exited": filter @message like /Process exited/                        [S11]
     "Runtime exited with error: signal: killed" for OOM: not found on any page (IRRESOLVABLE)
 C4 Memory ............. Max Memory Used = Memory Size (query @maxMemoryUsed=@memorySize); leaks grow across
     warm invokes; large payload OOM; "the execution environment stops the function"                       [S2][S11][S35]
 C5 Handler/class ...... "Class not found: function.Handler" ; "No public method named handleRequest with appropriate
     method signature found on class function.Handler" = handler config doesn't match code (Java strings) [S4]
     Family: Quarkus handler must be io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest   [I1 row 11]
     Runtime.ImportModuleError token: not on pages read (unverified); page shows "Unable to import module 'function'" [S4]
     Couldn't find valid bootstrap(s) (Runtime.InvalidEntrypoint) for provided.al2023 zip                  [S1]
 C6 Payload/JSON ....... malformed input, URL-encoded S3 keys, Java null "Records"/"eventSourceARN" casing   [S2][S44]
 C7 AccessDenied in SDK call -> execution role (simulate-principal-policy) ; KMS for client-side env decrypt needs
     kms:Decrypt on the role                                                                                [S33][S38][S61] (mapping: medium confidence)
 C8 Java perf after 11->17+: JAVA_TOOL_OPTIONS=-XX:-TieredCompilation reverts compiler behaviour             [S2]

D. Cold start / latency                                                                                      [S6][S11][S32]
 D1 Cold-start % : filter @type="REPORT" | stats sum(strcontains(@message,"Init Duration"))/count(*)*100      [S11]
 D2 SnapStart latency query (AWS, uses @initDuration + parsed restoreDuration)                               [S32]
 D3 PC configured but cold starts: check alias invoked (not $LATEST), ProvisionedConcurrencySpilloverInvocations,
     10 RPS per provisioned concurrency                                                                       [S1]
 D4 Cold starts typically <1% of invocations; <100 ms to >1 s                                                [S6]

E. VPC / network                                                                                             [S3][S46]
 E1 Timeouts/ETIMEDOUT after VPC attach: no NAT route from private subnet ("Connecting a function to a public
     subnet doesn't give it internet access")                                                                 [S3][S46]
 E2 AWS services without internet: VPC endpoints                                                              [S3]
 E3 Intermittent TCP/UDP with NACLs: allow 1024-65535 both ways                                               [S3]
 E4 UNKNOWNHOSTEXCEPTION: DNS (20 concurrent TCP DNS connections max, not increasable)                        [S3]
     SnapStart Java 11 DNS negative cache (AWS_LAMBDA_JAVA_NETWORKADDRESS_CACHE_NEGATIVE_TTL=0; not needed Java 17+) [S31]

F. SQS event source mapping                                                                                  [S27][S43][S44][S48][S49]
 F1 Messages reprocessed : whole batch returned after visibility timeout unless ReportBatchItemFailures [S27][S44]
 F2 Batch always fails  : exception thrown, invalid JSON, empty/null/unknown itemIdentifier                  [S27]
 F3 Backlog            : ApproximateAgeOfOldestMessage, ApproximateNumberOfMessagesVisible; throttled retries
     dropped after visibility timeout                                                                         [S27][S43]
 F4 DLQ filling        : DLQ ApproximateNumberOfMessagesVisible; maxReceiveCount (recommend >=5)              [S43][S48]
 F5 Config             : visibility timeout >= 6x function timeout (+ batching window); ESM State/StateTransitionReason/LastProcessingResult [S48][S49]
 F6 ESM metrics        : enabled only with MetricsConfig EventCount; FailedInvokeEventCount includes non-empty BatchItemFailures [S8]

G. Control-plane state                                                                                       [S29][S30][S4]
 G1 Pending >6 min: AWS lists Update*/PublishVersion as unblock (mutating -> hand-off)                        [S1]
 G2 LastUpdateStatus Failed: old code keeps running                                                           [S29]
 G3 Inactive: invoke reactivates (Pending) ; failure returns to Inactive                                      [S29][S30]

H. EventBridge (rule -> Lambda, asynchronous)                                                                [S34][S45][S47][S60]
 H1 EventBridge -> Lambda delivery fails (permissions/NO_RESOURCE are not retried; others retried 24 h / 185 times)
     EventBridge metric for failed target invocation; DLQ attributes RULE_ARN, TARGET_ARN, ERROR_CODE (e.g. NO_PERMISSIONS,
     THROTTLING, TIMEOUT), ERROR_MESSAGE, EXHAUSTED_RETRY_CONDITION, RETRY_ATTEMPTS                           [S45][S47]
     Exact metric name "FailedInvocations": not on pages read (unverified); DLQ metrics InvocationsSentToDLQ /
     InvocationsFailedToBeSentToDLQ                                                                           [S45]
 H2 Lambda accepted the event, function failed: Lambda async retries function errors twice (1 min, then 2 min);
     throttles/5xx up to 6 h with backoff 1 s -> 5 min; then DLQ / on-failure destination                    [S34]
     Metrics AsyncEventsReceived, AsyncEventAge, AsyncEventsDropped, DeadLetterErrors, DestinationDeliveryFailures [S8]
 H3 Duplicates are possible even without errors (eventually consistent queue)                                [S34][S5]
```

**Integration**: debugger ↔ Logs Insights (exact AWS queries, text log format)
```text
# Timeouts per 30 min                                         [S11]
filter @message like /Task timed out/
| stats count() by bin(30m)

# Crashes per 30 min                                           [S11]
filter @message like /Process exited/
| stats count() by bin(30m)

# Cold-start percentage                                        [S11]
filter @type = "REPORT"
| stats sum(strcontains(@message, "Init Duration"))/count(*) * 100 as
  coldStartPct, avg(@duration)
  by bin(5m)

# Invocations at 100% memory                                   [S11]
filter @type = "REPORT" and @maxMemoryUsed=@memorySize
| stats
    count_distinct(@requestId)
    by bin(30m)

# Slow invocations, deduplicated (@duration in ms)             [S10]
fields @timestamp, @requestId, @message, @logStream
| filter @type = "REPORT" and @duration > 1000
| sort @timestamp desc
| dedup @requestId
| limit 20

# Highest billed invocations                                   [S11]
filter @type = "REPORT"
| fields @requestId, @billedDuration
| sort by @billedDuration desc
| limit 100

# SnapStart latency percentiles (AWS Lambda Insights query)    [S32]
filter @type = "REPORT"
  | parse @log /\d+:\/aws\/lambda\/(?<function>.*)/
  | parse @message /Restore Duration: (?<restoreDuration>.*?) ms/
  | stats
count(*) as invocations,
pct(@duration+coalesce(@initDuration,0)+coalesce(restoreDuration,0), 50) as p50,
pct(@duration+coalesce(@initDuration,0)+coalesce(restoreDuration,0), 99) as p99
group by function, (ispresent(@initDuration) or ispresent(restoreDuration)) as coldstart
  | sort by coldstart desc
```

**Logs Insights field reference (Lambda)**:

| Field | Meaning / unit | Source |
|---|---|---|
| `@timestamp`, `@logStream`, `@message`, `@log` (`account-id:log-group-name`), `@ingestionTime` | system fields | [S9] |
| `@requestId` | invocation RequestId (unchanged across retries) | [S9][S11] |
| `@type` | e.g. `"REPORT"` | [S9][S10] |
| `@duration`, `@billedDuration` | milliseconds | [S9][S10] |
| `@maxMemoryUsed`, `@memorySize` | bytes - inferred from AWS queries dividing by 1024*1024 [S11] or 1000*1000 [S10] (medium confidence; pages disagree on divisor) | [S9][S10][S11] |
| `@initDuration` | used by the AWS SnapStart query with `ispresent()`; not in the discovered-field lists | [S32] vs [S9][S11] (medium confidence) |
| `@xrayTraceId`, `@xraySegmentId` | only when the line has an X-Ray trace ID / X-Ray enabled | [S9][S11] |
| Discovery limit | "only for the first embedded JSON fragment in each log event"; Standard log class only; max 200 JSON fields | [S9] |

**Integration**: debugger ↔ API Gateway access log (diagnostic JSON format; variables per [S23][S53])
```json
{ "requestId":"$context.requestId", "status":"$context.status",
  "responseType":"$context.error.responseType", "error":"$context.error.message",
  "integrationStatus":"$context.integration.integrationStatus", "functionStatus":"$context.integration.status",
  "integrationError":"$context.integrationErrorMessage", "integrationLatency":"$context.integrationLatency",
  "awsEndpointRequestId":"$context.awsEndpointRequestId" }
```
Enabling it is a mutating stage change (C1) - the debugger proposes it, the deployer applies it. Access log template
size limit 3 KB (REST and HTTP) [S14][S15].

---

## Quality Control

**Verification Commands** (for this research file and for the future skill's evaluation fixtures):
```bash
# Representative — adapt to your environment; none of these were executed by this research
F=workspace/quarkus-aws-saas/research_AWS_LambdaDebug_2026-10.md
grep -E "^### ✅|^### ⚠️|^### 🚫" "$F"                    # Expected: 3 lines
grep -E "^## " "$F"                                       # Expected: the 13 template headings in order
grep -cE '^ *`{3}' "$F"                                   # Expected: even number (every code block closed)
grep -c "✅ Correct" "$F"                                 # Expected: >= 8 (one per F1-F8)
grep -n "(unverified)" "$F" | wc -l                       # Expected: matches Unverified list in Research Gaps
# Read-only guard for the future agent: no mutating verbs in allowlisted commands
grep -nE "aws (lambda|apigateway|apigatewayv2|iam|sqs|logs|events) (update|put|add|delete|create|attach|remove|publish|purge|start-message-move|tag|untag)" <agent-or-skill-file>
# Expected: matches only inside F1 "❌ Wrong" blocks
```

**Mocking** (the debugger runs no tests against AWS; evaluation uses recorded log fixtures):
```text
# Fixture set for evaluation-scenarios.md (strings copied from AWS pages 2026-10-28)
fixture_timeout_new = "REPORT RequestId: 527cb862-... Duration: 3016.78 ms Billed Duration: 3101 ms Memory Size: 128 MB Max Memory Used: 31 MB Init Duration: 84.00 ms Status: timeout"   # S6
fixture_crash_new   = "REPORT RequestId: 5b866fb1-... Duration: 133.61 ms ... Status: error Error Type: Runtime.ExitError"   # S6
fixture_init_to     = "INIT_REPORT Init Duration: 1236.04 ms Phase: init Status: timeout"                                 # S6
fixture_snap_to     = '{ "cause": "Lambda couldn\'t restore the snapshot within the timeout limit. (Service: Lambda, Status Code: 408, ...)", "error": "Lambda.SnapStartTimeoutException"}'  # S31
fixture_apigw_500   = HTTP 500 {"message": "Internal server error"} + integrationStatus 403/429                            # S16 (status values illustrative)
# Expected verdicts: C1 timeout ; C3 crash ; C2 init timeout ; B5 SnapStart restore ; A3 -> B
# Guarantee: fixtures are static strings; no AWS call; judge checks the branch letter and that no mutating command is proposed
```

---

## Production Readiness

- **Performance**: cold starts "typically occur in under 1% of invocations", "under 100 ms to over 1 second" [S6]; memory
  raises CPU proportionally (one vCPU at 1,769 MB per quotas [S54]; "At 1.8 GB" per troubleshooting-configuration [S35] -
  AWS pages differ slightly, (medium confidence)); network bandwidth 625 Mbps per execution environment [S54].
- **Scalability**: account concurrency 1,000 default; 10x RPS rule; 1,000 environments / 10 s per function; 900 reservable
  by default [S26][S54]; SQS standard ESM starts with 5 concurrent invokes, adds up to 300/min, max 1,250 (on-demand) [S48];
  API Gateway 10,000 RPS account throttle (burst 5,000) vs Lambda 1,000 concurrency mismatch called out by AWS [S17][S54].
- **Monitoring (checklist for post-deploy verification)**: `Errors`/`Invocations` (Sum), `Throttles` (Sum), `Duration`
  p99 vs timeout, `ConcurrentExecutions` (Max), `ProvisionedConcurrencySpilloverInvocations`, `AsyncEventAge`,
  `AsyncEventsDropped` [S8]; API Gateway `5XXError` (Average = rate), `IntegrationLatency`, `Latency` [S50]; SQS
  `ApproximateAgeOfOldestMessage`, `NumberOfMessagesDeleted`, DLQ `ApproximateNumberOfMessagesVisible` [S27][S43].
  Metric dashboards/alarm design is out of scope (owned by `monitoring-cloudwatch-observability`, `tracing-aws-xray`).
- **Security**: read-only principal for the agent (permissions such as `logs:FilterLogEvents`, `logs:StartQuery`,
  `lambda:GetFunctionConfiguration`, `lambda:GetPolicy`, `iam:SimulatePrincipalPolicy`, `xray:GetTraceSummaries`,
  `xray:BatchGetTraces`, `cloudwatch:GetMetricStatistics` - exact IAM action names inferred from API names,
  (medium confidence)); `filter-log-events --unmask` requires `logs:Unmask` - do not request it [S40]; redact secrets (F6);
  Live Tail is billed per minute and needs `logs:StartLiveTail` [S11].

---

## Reference Implementations

- AWS sample app with REST API + X-Ray tracing: `https://github.com/awsdocs/aws-lambda-developer-guide/tree/main/sample-apps/nodejs-apig` (linked from S16/S25; not fetched).
- SQS partial batch response examples incl. Java (`SQSBatchResponse.BatchItemFailure`) on S27; serverless-snippets repo `https://github.com/aws-samples/serverless-snippets/tree/main/lambda-function-sqs-report-batch-item-failures` (linked from S27; not fetched).
- Canonical Logs Insights queries: S10 "Queries for Lambda logs" and S11 "Useful Insights queries".
- HTTP API 500 walk-through with `$context.integrationErrorMessage`: S13.
- D1 deploy/rollback procedure for any fix this debugger hands off: [I3].

---

## Source Bibliography

**Primary** (all AWS official pages, read 2026-10-28; "full" = whole page text returned by the fetch tool; CLI pages were
returned as structured extracts of the relevant sections and are marked "extract"):

| ID | Page | URL | Read |
|---|---|---|---|
| S1 | Troubleshoot invocation issues in Lambda | https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-invocation.html | full |
| S2 | Troubleshoot execution issues in Lambda | https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-execution.html | full |
| S3 | Troubleshoot networking issues in Lambda | https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-networking.html | full |
| S4 | Troubleshoot deployment issues in Lambda | https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-deployment.html | full |
| S5 | Invoke (Lambda API) | https://docs.aws.amazon.com/lambda/latest/api/API_Invoke.html | full |
| S6 | Understanding the Lambda execution environment lifecycle | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html | full |
| S7 | Sending Lambda Event Function logs to CloudWatch Logs | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html | full |
| S8 | Types of metrics for Lambda Event Functions | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html | full |
| S9 | Supported logs and discovered fields (CloudWatch Logs) | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData-discoverable-fields.html | full |
| S10 | Sample queries (CloudWatch Logs Insights) | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-examples.html | full |
| S11 | Viewing CloudWatch logs for Lambda Event Functions | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-view.html | full |
| S12 | Lambda Telemetry API Event schema reference | https://docs.aws.amazon.com/lambda/latest/dg/telemetry-schema-reference.html | full |
| S13 | Troubleshooting issues with HTTP API Lambda integrations | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-troubleshooting-lambda.html | full |
| S14 | Quotas for configuring and running an HTTP API | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html | full |
| S15 | Quotas for configuring and running a REST API | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html | full |
| S16 | Handling Lambda errors with an API Gateway API | https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway-errors.html | full |
| S17 | Amazon API Gateway quotas (account level) | https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html | full |
| S18 | Set up CloudWatch logging for REST APIs | https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-logging.html | full (landing page) |
| S19 | Configure logging for HTTP APIs | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-logging.html | full |
| S20 | Execution logging for REST APIs | https://docs.aws.amazon.com/apigateway/latest/developerguide/rest-api-execution-logging.html | full |
| S21 | Lambda proxy integrations in API Gateway (REST) | https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html | full |
| S22 | Create AWS Lambda proxy integrations for HTTP APIs | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html | full |
| S23 | Customize HTTP API access logs (variables) | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-logging-variables.html | full |
| S24 | Gateway response types for API Gateway | https://docs.aws.amazon.com/apigateway/latest/developerguide/supported-gateway-response-types.html | full |
| S25 | Invoking a Lambda Event Function using an API Gateway endpoint | https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html | full |
| S26 | Understanding Lambda Event Function scaling | https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html | full |
| S27 | Handling errors for an SQS event source in Lambda | https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html | full |
| S28 | Understanding retry behavior in Lambda Event Functions | https://docs.aws.amazon.com/lambda/latest/dg/invocation-retries.html | full |
| S29 | Lambda Event Function states | https://docs.aws.amazon.com/lambda/latest/dg/functions-states.html | full |
| S30 | FunctionConfiguration (Lambda API type) | https://docs.aws.amazon.com/lambda/latest/api/API_FunctionConfiguration.html | full |
| S31 | Troubleshooting SnapStart errors | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-troubleshooting.html | full |
| S32 | Monitoring for Lambda SnapStart | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-monitoring.html | full |
| S33 | Securing Lambda environment variables | https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars-encryption.html | full |
| S34 | How Lambda handles errors and retries with asynchronous invocation | https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html | full |
| S35 | Troubleshoot configuration issues in Lambda | https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-configuration.html | full |
| S36 | AWS CLI 2.39.0 xray get-trace-summaries | https://docs.aws.amazon.com/cli/latest/reference/xray/get-trace-summaries.html | extract |
| S37 | AWS CLI 2.39.0 xray batch-get-traces | https://docs.aws.amazon.com/cli/latest/reference/xray/batch-get-traces.html | extract |
| S38 | AWS CLI 2.39.0 iam simulate-principal-policy | https://docs.aws.amazon.com/cli/latest/reference/iam/simulate-principal-policy.html | extract |
| S39 | AWS CLI 2.39.0 logs tail | https://docs.aws.amazon.com/cli/latest/reference/logs/tail.html | extract |
| S40 | AWS CLI 2.39.0 logs filter-log-events | https://docs.aws.amazon.com/cli/latest/reference/logs/filter-log-events.html | extract |
| S41 | AWS CLI 2.39.0 logs start-query | https://docs.aws.amazon.com/cli/latest/reference/logs/start-query.html | extract |
| S42 | AWS CLI 2.39.0 lambda get-function-configuration | https://docs.aws.amazon.com/cli/latest/reference/lambda/get-function-configuration.html | extract |
| S43 | Available CloudWatch metrics for Amazon SQS | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-available-cloudwatch-metrics.html | full |
| S44 | Using Lambda with Amazon SQS | https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html | full (landing + sections) |
| S45 | Using dead-letter queues to process undelivered events in EventBridge | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html | full |
| S46 | Enable internet access for VPC-connected Lambda Event Functions | https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc-internet.html | full |
| S47 | How EventBridge retries delivering events | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html | full |
| S48 | Creating and configuring an Amazon SQS event source mapping | https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html | full |
| S49 | EventSourceMappingConfiguration (Lambda API type) | https://docs.aws.amazon.com/lambda/latest/api/API_EventSourceMappingConfiguration.html | full |
| S50 | Amazon API Gateway dimensions and metrics (REST) | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-metrics-and-dimensions.html | full |
| S51 | Configuring JSON and plain text log formats | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html | full |
| S52 | Visualize Lambda Event Function invocations using AWS X-Ray | https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html | full |
| S53 | Variables for access logging for API Gateway (REST) | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-variables-for-access-logging.html | full |
| S54 | Lambda quotas | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html | full |
| S55 | Invoking a Lambda Event Function asynchronously | https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html | full (landing page) |
| S56 | AWS CLI 2.39.0 logs get-query-results | https://docs.aws.amazon.com/cli/latest/reference/logs/get-query-results.html | extract |
| S57 | AWS CLI 2.39.0 lambda get-policy | https://docs.aws.amazon.com/cli/latest/reference/lambda/get-policy.html | extract |
| S58 | AWS CLI 2.39.0 cloudwatch get-metric-statistics | https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-metric-statistics.html | extract |
| S59 | Using CloudWatch metrics with Lambda | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html | full (landing page; no dimension list) |
| S60 | Invoking Lambda with events from other AWS services | https://docs.aws.amazon.com/lambda/latest/dg/lambda-services.html | full |
| S61 | Defining Lambda Event Function permissions with an execution role | https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html | full |
| S62 | Troubleshooting Lambda Web Functions (used only to exclude) | https://docs.aws.amazon.com/lambda/latest/dg/web-functions-troubleshooting.html | full |

**Not read / failed**:
- K1 AWS Knowledge Center "Resolve API Gateway REST API Lambda integration errors" https://repost.aws/knowledge-center/api-gateway-rest-api-lambda-integrations - HTTP 403 on fetch; only a web-search snippet quoting "Execution failed due to configuration error: Invalid permissions on Lambda function" (2026-10-28).
- K2 AWS Knowledge Center "Resolve HTTP 502 errors from API Gateway REST APIs with Lambda functions" https://repost.aws/knowledge-center/malformed-502-api-gateway - HTTP 403; not read.
- https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-troubleshooting-lambda.html and https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execute-api-quotas.html - fetch returned only the title "Amazon API Gateway" (no content); replaced by S15/S16/S21/S24.
- https://docs.aws.amazon.com/lambda/latest/dg/java-exceptions.html - fetch returned the troubleshooting-execution page (S2) content; Java error-object page not read.

**Validation**: none - community sources were not used (Source Hierarchy). Web searches (docs.aws.amazon.com / repost.aws
filters) were used only to locate pages: "Malformed Lambda proxy response" (2026-10-28), "Invalid permissions on Lambda
function" x2 (2026-10-28), "signal: killed" (2026-10-28), Java error format (2026-10-28), EventBridge async (2026-10-28).

**Internal**: I1 `workspace/quarkus-aws-saas/_family_facts_v3.40.md` (rows 11, 15, 16, 21, 33); I2
`workspace/quarkus-aws-saas/_family_rules_v3.40.md` (rules 7, 9-12); I3 `workspace/quarkus-aws-saas/research_AWS_LambdaDeploy_2026-10.md` (D1).

**All deep-links by section**: Guardrails A1 S26/S36-S42/S56-S58; A2 S2/S5/S8; A3 S13/S16/S21/S23/S24/S53; A4 S1/S2/S5/S11;
A5 S6/S11/S32; A6 S29/S30/S42; A7 S1/S8/S26/S59; A8 S1/S13/S25/S38/S57/S61/K1; A9 S27/S43/S44/S48/S49; A10 S2/S7/S12;
C1 S13/S16/S18-S20/S50; C2 S10/S11/S39-S41/S56; C3 S10-S12/S51; C4 S36/S37/S52; C5 S5/S11; C6 S6/S11/S32;
F1-F8 as listed per entry; Tree A S13-S17/S21-S24/S31; B S1/S3/S5/S26/S30/S31/S33/S54; C S1/S2/S4/S6/S11/S30/S33/S35/S38/S44/S61;
D S1/S6/S11/S32; E S3/S31/S46; F S8/S27/S43/S44/S48/S49; G S1/S4/S29/S30; H S8/S34/S45/S47/S60.

---

## Research Gaps

> Every gap that survives all gap-loop iterations must also appear as an IRRESOLVABLE row in §7.

```
Gap: Exact OOM message "Runtime exited with error: signal: killed" for Event Functions
Impact: Skill cannot quote the string; OOM must be inferred from REPORT Max Memory Used = Memory Size and Status/Error Type
Workaround: Use S11 query @maxMemoryUsed=@memorySize and S6 Runtime.ExitError; tag the string (unverified)
Follow-up: Lambda Java/Node logging pages; AWS Knowledge Center "Lambda out of memory" (repost.aws blocked for the fetch tool)
§7-ref: Iteration 2 — IRRESOLVABLE
```
```
Gap: REST execution-log strings "Execution failed due to configuration error: Invalid permissions on Lambda function" and "Malformed Lambda proxy response"
Impact: Exact strings only (medium confidence) from an AWS Knowledge Center search snippet; status codes 500/502 are High [S16][S21]
Workaround: Diagnose by status + $context.integration.integrationStatus / $context.integrationErrorMessage [S23][S53]
Follow-up: human read of K1/K2 in a browser
§7-ref: Iteration 1 — IRRESOLVABLE
```
```
Gap: HTTP API integration-timeout status code (504 vs 503) and whether HTTP APIs have execution logs
Impact: Branch A5 for HTTP APIs relies on REST gateway-response table [S24] (REST-specific)
Workaround: Use $context.integrationErrorMessage / $context.error.responseType in HTTP API access logs [S13][S23]
Follow-up: HTTP API "Working with AWS Lambda proxy integrations" sub-pages / error-handling page
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: Remaining (unverified) items (not IRRESOLVABLE because not searched exhaustively within the 3-iteration budget):
  1. X-Amz-Function-Error value set (Unhandled/Handled) [S5 silent]
  2. Runtime.ImportModuleError token (S4 shows only "Unable to import module 'function'")
  3. Plain-text REPORT "XRAY TraceId" field text
  4. Logs Insights field discovery for JSON-format platform records
  5. EventBridge metric name "FailedInvocations" (S45 says "a target invocation failed" metric without name)
  6. Max time range for get-trace-summaries (S36 silent)
  7. Logs Insights / Live Tail pricing comparison (pricing page not read)
Impact: wording-level; branches still decidable from High facts
Workaround: keep tags; skill states them as (unverified)
Follow-up: Invoke response docs for SDKs; EventBridge monitoring page (eb-monitoring); CloudWatch pricing page
```
```
Gap: AWS-internal inconsistencies to cite both ways (not contradictions with family facts)
  - "--log-type Tail" returns "first 4 KB" [S11] vs LogResult "The last 4 KB" [S5] (also in D1 [I3])
  - Memory divisor 1000*1000 [S10] vs 1024*1024 [S11] for @maxMemoryUsed
  - One vCPU "At 1.8 GB" [S35] vs "At 1,769 MB" [S54]
  - SQS provisioned-mode MaximumPollers 2-10,000 [S44] vs "maximum (2-2000)" [S48]
  - @initDuration used in an AWS query [S32] but absent from the discovered-field lists [S9][S11]
  - "Billed Duration ... rounded up to the nearest millisecond" [S8] while S6 examples bill more than Duration (3004.92 ms -> 3117 ms with Init Duration 111.23 ms), consistent with init billing [S6 link "AWS Lambda standardizes billing for init phase"] (medium confidence)
Impact: wording/precision only
Workaround: skill quotes both URLs
Follow-up: AWS doc feedback
```

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Tree A3 / A8 | REST "Invalid permissions on Lambda function" string | Two docs-domain searches; only repost.aws KC hit; KC fetch HTTP 403 -> kept (medium confidence) | K1 (2026-10-28) |
| 1 | Tree A4 | "Malformed Lambda proxy response" -> 502 | Status code resolved from docs; exact string ⚠️ IRRESOLVABLE on docs (KC 403) | [S21][S16] (2026-10-28) |
| 1 | Tree A | REST troubleshooting + quotas pages empty on fetch | Replaced by REST quotas table, gateway responses, Lambda APIGW errors | [S15][S24][S16] (2026-10-28) |
| 2 | Tree C3 | "Runtime exited with error: signal: killed" | Docs search: no page contains it; Web Functions page has Runtime.OutOfMemory (different product) -> ⚠️ IRRESOLVABLE — string not on any official Event Function page | [S62] (2026-10-28) |
| 2 | Field ref | `@initDuration` availability | Resolved (medium): used in AWS SnapStart Lambda Insights query; absent from discovered-field lists | [S32] vs [S9][S11] (2026-10-28) |
| 2 | Tree C5 | Java handler error strings | Resolved: "Class not found: function.Handler", "No public method named handleRequest ..." | [S4] (2026-10-28) |
| 2 | Tree C5 | Java error-object page | java-exceptions URL returned S2 content; Java errorType/stackTrace format left out | — |
| 3 | Tree H | EventBridge -> Lambda invocation mode | Resolved: "asynchronous invocation (event buses and rules)" | [S60] (2026-10-28) |
| 3 | Tree H | EventBridge retry defaults / DLQ attributes | Resolved: 24 h, 185 attempts; non-retried permission/missing-resource errors; DLQ attributes | [S47][S45] (2026-10-28) |
| 3 | Tree A5 | HTTP API timeout status code | Not found on S13/S14/S19/S22/S23 -> ⚠️ IRRESOLVABLE — no page read states it | — |
| 3 | A1 | X-Ray CLI options and output fields | Resolved from CLI 2.39.0 reference | [S36][S37] (2026-10-28) |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Complex)
- [x] All scope areas cited (APIGW 5xx/429, invoke errors, init/timeout/crash/memory, throttling, permissions, KMS, VPC, SnapStart, SQS ESM, EventBridge, cold start, tools)
- [x] Pattern counts driven by domain needs (10 Always, 6 Conditional, 8 Forbidden)
- [x] Every anti-pattern has alternative (F1-F8 ❌/✅)
- [x] All CLI commands validated/marked as representative (none executed)
- [x] Integration examples complete (Logs Insights, API Gateway access-log format)
- [x] Sources dated and linked (2026-10-28; read completeness per ID)
- [x] Security documented (read-only allowlist, secret redaction, Data tracing, `--unmask`)
- [x] 1+ copy-paste working example (AWS queries verbatim from S10/S11/S32)
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated (A1-A10 ✓✓; A1 allowlist itself is repo policy)
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in §7 (3 IRRESOLVABLE rows; the (unverified) list and AWS inconsistencies are tracked, not IRRESOLVABLE)

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: A1-A10 reads; status-code mapping 500/502 (APIGW+Lambda) [S16][S21],
  504/429 REST gateway responses [S24], timeout quotas 29 s REST / 30 s HTTP [S15][S14], init limit 10 s [S6], REPORT
  field names [S6][S11][S32], Invoke error list [S5], state/reason codes [S30], SQS visibility/DLQ rules [S27][S48],
  EventBridge retry 24 h/185 [S47], async retries [S34]; refuse every mutating command (F1).
- **Medium Confidence (validate with user)**: exact REST execution-log strings [K1][K2]; `@initDuration` field;
  memory unit/divisor; HTTP API logging limited to access logs; AccessDenied-in-SDK -> function error mapping; IAM action
  names for the read-only principal; `FunctionName` dimension name; Quarkus 2 s vs AWS 10 s restore limit [I1 row 21].
- **Low Confidence (must ask human)**: IRRESOLVABLE items (OOM "signal: killed" string, HTTP API timeout status code,
  exact KC strings); any real `invoke` (C5); enabling API Gateway logs (C1, hand-off to deployer).
- **Edge Cases (pause)**: Lambda Managed Instances, Web Functions, MicroVMs or durable functions in the account (different
  logs/limits [S6][S54][S62]); China/GovCloud Regions (log-format change excluded there [S6]).
- **Emergency Stop**: a request that requires a mutating command to "confirm" a hypothesis; a request to paste raw
  environment variables or tokens.

> Version lock reminder: everything above is the AWS documentation state of **2026-10-28** (AWS CLI reference 2.39.0);
> re-verify the log-format transition [S6] and X-Ray segment change [S52] before reuse after that date.
