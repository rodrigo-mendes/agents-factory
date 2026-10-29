# Always-do patterns

Back to [SKILL.md](../SKILL.md). Each pattern states one High claim with its source; caveats live in [ask-first decisions](./ask-first-decisions.md). Commands are representative (AWS CLI 2.39.0, docs read 2026-10-28; none executed against AWS by the author). The `bash` blocks are manual CLI forms and use `jq` for brevity; the scripts do the same with Python 3 and need no `jq`.

## Contents

- [A1 Deterministic CLI environment](#a1-deterministic-cli-environment)
- [A2 One smoke window converted per API](#a2-one-smoke-window-converted-per-api)
- [A3 Logs retention then Logs Insights](#a3-logs-retention-then-logs-insights)
- [A4 Logs pagination by token](#a4-logs-pagination-by-token)
- [A5 Metrics on exact dimensions](#a5-metrics-on-exact-dimensions)
- [A6 Traces destination first](#a6-traces-destination-first)
- [A7 Traces on the X-Ray path](#a7-traces-on-the-x-ray-path)
- [A8 Alarms with explicit types](#a8-alarms-with-explicit-types)
- [A9 Dashboards parse and cross-check](#a9-dashboards-parse-and-cross-check)

## A1 Deterministic CLI environment

Options override environment variables, which override profile settings ([env vars](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)). CLI v2 uses a pager unless `AWS_PAGER` is empty ([pagination](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-pagination.html)). With `--output json` the `--query` runs once over the paginated structure ([filtering](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-filter.html)). Return codes 252-255 are listed in [CLI environment and exit codes](./cli-environment-and-exit-codes.md).

```bash
export AWS_PAGER=""
export AWS_RETRY_MODE="${AWS_RETRY_MODE:-standard}"   # explicit, see the retry-mode decision
: "${AWS_REGION:?set AWS_REGION}"
aws --region "$AWS_REGION" --output json --no-cli-pager lambda get-function-configuration --function-name "$FN"
rc=$?; case "$rc" in 0) :;; 253) echo "credentials/config: stop";; 252|254|255) echo "CLI/service error";; esac
```

## A2 One smoke window converted per API

The caller records `SMOKE_START_S` (epoch seconds) just before the smoke test. `filter-log-events` takes epoch milliseconds ([reference](https://docs.aws.amazon.com/cli/latest/reference/logs/filter-log-events.html)); `start-query` takes epoch seconds ([reference](https://docs.aws.amazon.com/cli/latest/reference/logs/start-query.html)); X-Ray `StartTime` and `EndTime` are Unix seconds ([API](https://docs.aws.amazon.com/xray/latest/api/API_GetTraceSummaries.html)). Conversions: see the table in [CLI environment and exit codes](./cli-environment-and-exit-codes.md#time-units-per-api).

## A3 Logs retention then Logs Insights

`describe-log-groups` returns `logGroups[].retentionInDays` ([reference](https://docs.aws.amazon.com/cli/latest/reference/logs/describe-log-groups.html)). `start-query` needs `--start-time`, `--end-time`, `--query-string` and one log group option; poll `get-query-results` until `status` is `Complete`; `ispresent(field)` returns true if the field exists ([get-query-results](https://docs.aws.amazon.com/cli/latest/reference/logs/get-query-results.html), [functions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-operations-functions.html)). Details: [pillar logs](./pillar-logs.md). `start-query` is billed per GB scanned: run it only under `approval: logs-insights scope=<log-group> window=<min> by=<user> at=<UTC> relayed-by=<orchestrator>`; `check-logs.py` makes the call only with `--i-have-logs-insights-approval` (otherwise `WARN logs.query not verified`); it prints no plan line first, so match scope and window beforehand.

```bash
QID=$(aws --output json logs start-query --log-group-name "$LG" --start-time "$SMOKE_START_S" --end-time "$END_S" \
      --query-language CWLI --query-string 'filter ispresent(requestId) | stats count(*) as n' | jq -r .queryId)
# poll: aws --output json logs get-query-results --query-id "$QID" | jq -r .status   # until Complete
```

## A4 Logs pagination by token

A `filter-log-events` page can be partly full or empty; pagination is finished only when the result has no `nextToken` ([reference](https://docs.aws.amazon.com/cli/latest/reference/logs/filter-log-events.html)). The CLI follows tokens by default, so never pass `--no-paginate` and read `length(events)` from one page.

```bash
aws --output json logs filter-log-events --log-group-name "$LG" --start-time "$START_MS" --end-time "$END_MS" \
    --filter-pattern '"tenantId"' --max-items 200 --query 'length(events)'
```

## A5 Metrics on exact dimensions

Invocation metrics are viewed with `Sum`; `Throttles` do not count as `Invocations` or `Errors` ([metric types](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html)). `get-metric-data` takes up to 500 queries, `Id` starts with a lowercase letter, and each result has a `StatusCode` of `Complete`, `InternalError`, `PartialData` or `Forbidden` ([reference](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-metric-data.html)). Details: [pillar metrics](./pillar-metrics.md).

```bash
aws --output json cloudwatch get-metric-data --metric-data-queries file://q.json \
    --start-time "$M_START" --end-time "$M_END" \
    --query 'MetricDataResults[].{id:Id,status:StatusCode,sum:sum(Values)}'
```

## A6 Traces destination first

`get-trace-segment-destination` returns `Destination` `XRay` or `CloudWatchLogs` and `Status` `PENDING` or `ACTIVE`; Transaction Search requires `CloudWatchLogs` ([reference](https://docs.aws.amazon.com/cli/latest/reference/xray/get-trace-segment-destination.html)). `BatchGetTraces` cannot find traces when Transaction Search is enabled, because they are not indexed in X-Ray ([API](https://docs.aws.amazon.com/xray/latest/api/API_BatchGetTraces.html)). Details: [pillar traces](./pillar-traces.md).

```bash
DEST=$(aws --output json xray get-trace-segment-destination | jq -r .Destination)
[ "$DEST" = "CloudWatchLogs" ] && echo "use start-trace-retrieval + list-retrieved-traces (needs approval: logs-insights scope=xray)" || echo "use batch-get-traces"
```

## A7 Traces on the X-Ray path

Lambda sends no traces automatically in `PassThrough`, the default; set `TracingConfig.Mode` to `Active` ([Lambda and X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)). `batch-get-traces` takes 1 to 5 trace ids and each `Segments[].Document` is a JSON string ([reference](https://docs.aws.amazon.com/cli/latest/reference/xray/batch-get-traces.html)). An HTTP API adds no X-Ray node, so the trace starts at the Lambda segment ([API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html)).

```bash
aws --output json xray batch-get-traces --trace-ids $IDS > traces.json
jq -r '[.Traces[].Segments[].Document | fromjson | .origin] | unique[]' traces.json
```

## A8 Alarms with explicit types

Without `--alarm-types`, `describe-alarms` returns only metric alarms even if composite or log alarms exist; `--alarm-name-prefix` cannot be combined with `--alarm-names` ([reference](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/describe-alarms.html)). Assert `ActionsEnabled`, a non-empty `AlarmActions` and the `StateValue`; for SNS actions read `list-subscriptions-by-topic` ([reference](https://docs.aws.amazon.com/cli/latest/reference/sns/list-subscriptions-by-topic.html)). Details: [pillar alarms](./pillar-alarms.md).

```bash
aws --output json cloudwatch describe-alarms --alarm-name-prefix "$P" --alarm-types MetricAlarm CompositeAlarm \
    --query 'MetricAlarms[].{n:AlarmName,s:StateValue,e:ActionsEnabled,a:AlarmActions}'
```

## A9 Dashboards parse and cross-check

`get-dashboard` returns `DashboardArn`, `DashboardName` and `DashboardBody`, a JSON string; `list-dashboards` returns only name, ARN, last-modified and size ([get-dashboard](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-dashboard.html), [list-dashboards](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/list-dashboards.html)). No documented API reports whether a dashboard renders, so report render as not provable. Details: [pillar dashboards](./pillar-dashboards.md).

```bash
BODY=$(aws --output json cloudwatch get-dashboard --dashboard-name "$DASH" | jq -r .DashboardBody)
jq -r '.widgets[] | select(.type=="log") | .properties.query' <<<"$BODY" | grep -o "SOURCE '[^']*'"
```
