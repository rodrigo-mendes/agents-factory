# Read-Only Command Allowlist and Refused Commands

Research date 2026-10-28, AWS CLI 2.39.0 reference. Back to [SKILL.md](../SKILL.md). Source ids resolve in the [source bibliography](./source-bibliography.md). Tags map to the [register](./unverified-and-risks.md#tag-to-register-mapping). All commands are representative; none was executed (L4).

## Contents

- [Allowlist](#allowlist)
- [Choosing the log tool](#choosing-the-log-tool)
- [Refused commands](#refused-commands)
- [Invoking and Live Tail](#invoking-and-live-tail)
- [Principal of the debugger](#principal-of-the-debugger)

## Allowlist

The debugger is read-only by unit definition (repo policy, In3). These commands only return data, except `logs start-query` and `xray start-trace-retrieval`, which start a billable query or retrieval and are allowed only with the `approval: logs-insights ...` line relayed by the orchestrator. Other `start-*` verbs stay refused.

| Command | Reads | Source |
|---|---|---|
| `aws lambda get-function-configuration --function-name <fn>:<alias>` | version-specific settings, `State`, reason codes | S42 |
| `aws lambda get-function --function-name <fn> --query 'Configuration.[State, LastUpdateStatus]'` | state | S29 |
| `aws lambda get-policy --function-name <fn> --qualifier <alias>` | the resource-based policy | S57 |
| `aws lambda get-account-settings` | account quotas | S26 |
| `aws lambda list-event-source-mappings --function-name <fn>` | ESM state and settings | S27 |
| `aws logs tail /aws/lambda/<fn> --since 30m` (never `--follow`) | recent events; `--follow` is refused because whether it starts a billable Live Tail session is (unverified) | S39 |
| `aws logs filter-log-events --log-group-name <group> --start-time <epoch-ms> --end-time <epoch-ms> --filter-pattern "REPORT"` | events | S40 |
| `aws logs describe-log-groups --log-group-name-prefix /aws/lambda/<fn>` | log group existence and `retentionInDays` | `validating-aws-observability` (CLI 2.39.0) |
| `aws logs start-query ...` then `aws logs get-query-results --query-id <id>` | Logs Insights results; `start-query` starts a billable query, so it needs `approval: logs-insights scope=<log-group> window=<min> by=<user> at=<UTC> relayed-by=<orchestrator>` | S41, S56 |
| `aws cloudwatch get-metric-data`, `list-metrics` | metric datapoints on exact dimensions; metric discovery | `validating-aws-observability` (CLI 2.39.0) |
| `aws cloudwatch describe-alarms --alarm-types MetricAlarm CompositeAlarm`, `describe-alarm-history` | alarm definitions, state, history | `validating-aws-observability` (CLI 2.39.0) |
| `aws cloudwatch list-dashboards`, `get-dashboard` | dashboard names and body | `validating-aws-observability` (CLI 2.39.0) |
| `aws xray get-trace-segment-destination` | where traces are stored; read before any trace call | `validating-aws-observability` (CLI 2.39.0) |
| `aws xray start-trace-retrieval` then `list-retrieved-traces` | trace retrieval under Transaction Search; `start-trace-retrieval` starts a retrieval, so it needs an `approval: logs-insights scope=xray window=<min> ...` line | `validating-aws-observability` (CLI 2.39.0) |
| `aws sns list-subscriptions-by-topic --topic-arn <arn>` | subscription state; never print endpoints | `validating-aws-observability` (CLI 2.39.0) |
| `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Throttles --dimensions Name=FunctionName,Value=<fn> --start-time <iso> --end-time <iso> --period 60 --statistics Sum` | datapoints | S58, S8 |
| `aws xray get-trace-summaries --start-time <epoch> --end-time <epoch> --filter-expression '<expr>'` | trace summaries | S36 |
| `aws xray batch-get-traces --trace-ids <trace-id>` | segments | S37 |
| `aws iam simulate-principal-policy --policy-source-arn <execution-role-arn> --action-names <action> --resource-arns <arn>` | authorization check; it "does not perform the API operations" | S38 |

Notes:
- The `FunctionName` dimension name for `AWS/Lambda` is not stated on the pages read (medium confidence).
- `get-trace-summaries` requires `--start-time` and `--end-time`; its maximum time range is not stated (unverified). Summary fields: `HasError` (400-series), `HasFault` (500-series), `HasThrottle` (429), `ResponseTime`. The CLI page's example output is a URL list rather than `TraceSummaries`; treat it as a documentation defect (S36).
- `batch-get-traces` returns `Segments[].Document` and `UnprocessedTraceIds`; with X-Ray Transaction Search enabled "You cannot find traces through this API" (S37).
- `simulate-principal-policy` evaluates identity-based policies and SCPs of the principal; it "does not automatically retrieve policies for the specified resources" and resource-based policies are "not supported for IAM roles". It now returns one `EvaluationResult` per action; per-resource decisions are in `ResourceSpecificResults` (S38).
- `aws sqs get-queue-attributes` is named from the SQS API and its page was not fetched (medium confidence); use it only after the user accepts that.

## Choosing the log tool

| Tool | Facts | Source |
|---|---|---|
| `logs tail` | default start is ten minutes in the past; relative `--since` such as `5m`; no compound units (medium confidence, L1) | S39 |
| `filter-log-events` | epoch milliseconds, filter pattern, paginated, `nextToken` expires after 24 hours; `--unmask` needs `logs:Unmask`: never request it (medium confidence, L1) | S40 |
| `start-query` and `get-query-results` | epoch seconds (medium confidence, L1), aggregation over REPORT lines, billable scan (pricing page not read) (unverified); needs the `approval: logs-insights ...` line | S10, S11, S41, S56 |

Decision and question: [ask first C2](./ask-first-decisions.md#c2-log-tool-and-window).

## Refused commands

Any verb that creates, changes or deletes (`update-`, `put-`, `add-`, `delete-`, `create-`, `attach-`, `remove-`, `publish-`, `purge-`, `start-message-move`, `tag-`, `untag-`) is refused. Several look diagnostic but mutate:

| Command | Why it looks useful | Source |
|---|---|---|
| `aws lambda update-event-source-mapping` (for example `--metrics-config Metrics=EventCount`) | enable ESM metrics | S8, S27 |
| `aws lambda update-function-configuration` | AWS even suggests "a trivial update" to refresh credentials | S2 |
| `aws lambda add-permission` | fix a missing invoke permission | S13, S25 |
| `aws lambda update-alias` | roll back | S4 |
| `aws lambda put-function-concurrency` (or concurrency 0 to stop a loop) | stop a runaway loop | S1 |
| `aws apigatewayv2 update-stage --access-log-settings` | enable access logs | S19 |
| `aws logs create-log-group` | create the access-log group | S19 |
| `aws iam attach-role-policy` | add log permissions | S7 |
| SQS receive on the source queue | peek at messages; it hides them for the visibility timeout (inference that a manual receive behaves like Lambda's) (medium confidence) | S44 |

Refusal answer: name the command, say it mutates, then give the work-order ([format](./verdict-and-handoff.md#work-order-format)). The owner is the code owner (integrator) for code and handler, the deployer (`deploying-aws-lambda`) for configuration, permissions, aliases and stages.

## Invoking and Live Tail

- `aws lambda invoke --invocation-type DryRun` validates parameters and the caller's permission with status 204 and does not execute the function (S5). A real `RequestResponse` invoke executes code and is not read-only: [ask first C5](./ask-first-decisions.md#c5-reproducing-by-invoking).
- Live Tail (`start-live-tail`) is billed per minute and needs `logs:StartLiveTail` (S11). It is refused: no approval line exists for it; use `filter-log-events` or the `approval: logs-insights` gate.

## Principal of the debugger

Permissions that match the allowlist: `lambda:GetFunctionConfiguration`, `lambda:GetFunction`, `lambda:GetPolicy`, `lambda:ListEventSourceMappings`, `lambda:GetAccountSettings`, `logs:DescribeLogGroups`, `logs:FilterLogEvents`, `logs:StartQuery`, `logs:GetQueryResults`, `cloudwatch:GetMetricStatistics`, `cloudwatch:GetMetricData`, `cloudwatch:ListMetrics`, `cloudwatch:DescribeAlarms`, `cloudwatch:DescribeAlarmHistory`, `cloudwatch:ListDashboards`, `cloudwatch:GetDashboard`, `xray:GetTraceSummaries`, `xray:BatchGetTraces`, `xray:GetTraceSegmentDestination`, `xray:StartTraceRetrieval`, `xray:ListRetrievedTraces`, `sns:ListSubscriptionsByTopic`, `iam:SimulatePrincipalPolicy`. The action set for the observability commands follows the managed policy `CloudWatchReadOnlyAccess` as read by `validating-aws-observability` (medium confidence). The exact action names are inferred from the API names (medium confidence). Do not request `logs:Unmask`.
