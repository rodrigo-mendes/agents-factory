# Command allowlist, denylist and IAM

Back to [SKILL.md](../SKILL.md). The classes are a repo policy built on AWS command names; the command facts come from the CLI reference 2.39.0 read 2026-10-28.

## Contents

- [Allowed read commands](#allowed-read-commands)
- [The one approval-gated command](#the-one-approval-gated-command)
- [Forbidden commands](#forbidden-commands)
- [IAM read set](#iam-read-set)
- [Guard commands](#guard-commands)

## Allowed read commands

"Read" here means no resource is changed. `logs start-query` (billed per GB scanned) and `xray start-trace-retrieval` start a query or retrieval; they are the only `start-*` verbs allowed, and each needs an `approval: logs-insights scope=<log-group or "xray"> window=<min> ...` line.

| Service | Commands | Notes |
|---|---|---|
| `logs` | `describe-log-groups`, `filter-log-events`, `start-query`, `get-query-results`, `stop-query` (own query only) | `stop-query` stops a process: read class is (medium confidence) |
| `cloudwatch` | `get-metric-data`, `get-metric-statistics`, `list-metrics`, `describe-alarms`, `describe-alarm-history`, `list-dashboards`, `get-dashboard`, `get-metric-widget-image` (K7) | |
| `xray` | `get-trace-segment-destination`, `get-trace-summaries`, `batch-get-traces`, `list-retrieved-traces`, `start-trace-retrieval` | `start-trace-retrieval` initiates a retrieval: read class is (medium confidence) |
| `sns` | `list-subscriptions-by-topic` | never print endpoints |
| `lambda` | `get-function-configuration` | fields `TracingConfig.Mode`, `LoggingConfig.LogGroup` |
| `apigateway` | `get-stage` | field `tracingEnabled` (REST API stage) |

## The one approval-gated command

`cloudwatch set-alarm-state` ([reference](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/set-alarm-state.html)), only through `trigger-alarm-test.py --i-have-user-approval`, passed only with the line `approval: alarm-test alarm=<name> by=<user> at=<UTC> relayed-by=<orchestrator>`, after [K1](./ask-first-decisions.md#k1-set-alarm-state-notification-test).

## Forbidden commands

Never run these from the validator; a FAIL routes to a provisioning skill by name, it is not fixed here.

| Service | Commands |
|---|---|
| `logs` | `put-retention-policy`, `delete-retention-policy`, `create-log-group`, `delete-log-group`, `put-resource-policy`, `put-metric-filter`, `put-subscription-filter`, `associate-kms-key` |
| `cloudwatch` | `put-metric-alarm`, `put-composite-alarm`, `delete-alarms`, `enable-alarm-actions`, `disable-alarm-actions`, `put-dashboard`, `delete-dashboards`, `put-metric-data` |
| `xray` | `update-trace-segment-destination`, `update-indexing-rule`, `put-trace-segments`, sampling-rule and group create, update and delete |
| `lambda` | `update-function-configuration`, `invoke` (the smoke test is a precondition owned by the deploy skill) |
| `apigateway` | `update-stage`, `create-stage` |
| `sns` | `publish`, `subscribe`, `confirm-subscription` |

Provisioning owners, by name: `provisioning-aws-cloudwatch-v6`, `provisioning-aws-xray-v6`.

## IAM read set

The managed policy `CloudWatchReadOnlyAccess` (v25, edited 2026-09-22) covers `cloudwatch:Describe*`, `Get*`, `List*`, `BatchGet*`; `logs:Get*`, `List*`, `Describe*`, `StartQuery`, `StopQuery`, `FilterLogEvents`; `xray:BatchGet*`, `Get*`, `List*`, `StartTraceRetrieval`, `CancelTraceRetrieval`; `sns:Get*`, `List*`. It does not include `cloudwatch:SetAlarmState`, `lambda:GetFunctionConfiguration` or `apigateway:GET` ([policy page](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/CloudWatchReadOnlyAccess.html)). The Transaction Search docs advise this policy for using Transaction Search. The action set comes from that single page (medium confidence); per-action access levels and resource-level scoping are (unverified).

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "ObservabilityRead", "Effect": "Allow", "Resource": "*",
      "Action": [
        "logs:DescribeLogGroups", "logs:FilterLogEvents", "logs:StartQuery", "logs:GetQueryResults", "logs:StopQuery",
        "cloudwatch:GetMetricData", "cloudwatch:GetMetricStatistics", "cloudwatch:ListMetrics",
        "cloudwatch:DescribeAlarms", "cloudwatch:DescribeAlarmHistory", "cloudwatch:ListDashboards",
        "cloudwatch:GetDashboard", "cloudwatch:GetMetricWidgetImage",
        "xray:GetTraceSegmentDestination", "xray:GetTraceSummaries", "xray:BatchGetTraces",
        "xray:StartTraceRetrieval", "xray:ListRetrievedTraces",
        "sns:ListSubscriptionsByTopic", "lambda:GetFunctionConfiguration", "apigateway:GET" ] }
  ]
}
```

- Action names follow the API operation names.
- Do not grant `logs:Unmask`: `--unmask` needs it and the validator never uses it.
- `cloudwatch:SetAlarmState` belongs in a separate, temporary statement used only for K1.

## Guard commands

```bash
# run from the skill folder; expect no output from the first, only trigger-alarm-test.py from the second
# subcommands are quoted string literals in the Python scripts ("cloudwatch", "describe-alarms", ...)
grep -nE "(\"|')(put|delete|create|update|enable|disable|associate|confirm)-[a-z-]+(\"|')|(\"|')(publish|subscribe|invoke)(\"|')" scripts/*.py
grep -l 'set-alarm-state' scripts/*.py
grep -nE -- '--unmask|--interleaved|--output text' scripts/*.py        # expect no output
grep -noE "[\"']start-[a-z-]+[\"']" scripts/*.py | grep -vE "start-(query|trace-retrieval)[\"']"   # expect no output
# python3 scripts/tests/run_tests.py runs the same guards (python on Windows)
```
