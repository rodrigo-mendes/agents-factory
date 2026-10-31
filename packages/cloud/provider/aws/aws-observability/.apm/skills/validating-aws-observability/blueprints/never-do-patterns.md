# Never-do patterns

Back to [SKILL.md](../SKILL.md). High-confidence rows only; every alternative is High too. Unconfirmed alternatives live in [ask-first decisions](./ask-first-decisions.md).

## Contents

- [N1 Mutating commands](#n1-mutating-commands)
- [N2 Text output with query](#n2-text-output-with-query)
- [N3 Empty page means no logs](#n3-empty-page-means-no-logs)
- [N4 Trace reads without the destination](#n4-trace-reads-without-the-destination)
- [N5 API Gateway node for an HTTP API](#n5-api-gateway-node-for-an-http-api)
- [N6 list-metrics as freshness proof](#n6-list-metrics-as-freshness-proof)
- [N7 Mixed epoch units](#n7-mixed-epoch-units)
- [N8 Printing log messages or unmasking](#n8-printing-log-messages-or-unmasking)
- [N9 Dashboard renders from get-dashboard](#n9-dashboard-renders-from-get-dashboard)
- [N10 Implicit pager or Region](#n10-implicit-pager-or-region)
- [N11 Alarms without alarm types](#n11-alarms-without-alarm-types)

## N1 Mutating commands

The validator is read-only; the single exception is `cloudwatch set-alarm-state` under an `approval: alarm-test alarm=<name> ...` line ([set-alarm-state](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/set-alarm-state.html)). Impact: silent drift of retention or indexing, real cost, real alerts. Full denylist: [command allowlist and IAM](./command-allowlist-and-iam.md).

```bash
# 🚫 WRONG: "fixing" a FAIL
aws logs put-retention-policy --log-group-name "$LG" --retention-in-days 30
# ✅ CORRECT: report and route
echo "FAIL logs.retention: not set on $LG -> route to provisioning-aws-cloudwatch-v6"; exit 1
```

## N2 Text output with query

With `--output text` the output is paginated before `--query` and the query runs once on each page ([filtering](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-filter.html)). Impact: duplicated or extra elements.

```bash
# 🚫 WRONG
aws logs describe-log-groups --output text --query 'logGroups[0].logGroupName'
# ✅ CORRECT
aws logs describe-log-groups --output json --query 'logGroups[0].logGroupName'
```

## N3 Empty page means no logs

A `filter-log-events` page can be empty while a `nextToken` exists ([reference](https://docs.aws.amazon.com/cli/latest/reference/logs/filter-log-events.html)). Impact: false FAIL.

```bash
# 🚫 WRONG
aws logs filter-log-events --log-group-name "$LG" --no-paginate --query 'length(events)'
# ✅ CORRECT: the CLI follows nextToken by default
aws --output json logs filter-log-events --log-group-name "$LG" --start-time "$START_MS" --end-time "$END_MS" --query 'length(events)'
```

## N4 Trace reads without the destination

`BatchGetTraces` cannot find traces when Transaction Search is enabled ([API](https://docs.aws.amazon.com/xray/latest/api/API_BatchGetTraces.html)). Impact: false FAIL on every Transaction Search account.

```bash
# 🚫 WRONG: empty Traces read as "tracing broken"
aws xray batch-get-traces --trace-ids "$ID"
# ✅ CORRECT
aws --output json xray get-trace-segment-destination | jq -r .Destination   # then follow the path it names: see pillar-traces
```

## N5 API Gateway node for an HTTP API

HTTP APIs do not support X-Ray tracing; with `quarkus-amazon-lambda-http` the trace starts at the Lambda segment ([API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html)). Impact: permanent false FAIL.

```bash
# 🚫 WRONG: Stage node demanded for an HTTP API
# ✅ CORRECT
case "$API_TYPE" in REST) need="AWS::ApiGateway::Stage AWS::Lambda AWS::Lambda::Function";;
                    *)    need="AWS::Lambda AWS::Lambda::Function";; esac
```

## N6 list-metrics as freshness proof

New metrics can take up to 15 minutes to appear in `list-metrics`, and metrics without data in two weeks are not listed ([reference](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/list-metrics.html)). Impact: false FAIL after the smoke test or false PASS from old data.

```bash
# 🚫 WRONG
aws cloudwatch list-metrics --namespace "$NS" --recently-active PT3H     # non-empty => "metrics OK"
# ✅ CORRECT: read the datapoints of the smoke window
aws --output json cloudwatch get-metric-data --metric-data-queries file://q.json --start-time "$M_START" --end-time "$M_END"
```

## N7 Mixed epoch units

`filter-log-events` is milliseconds, `start-query` and X-Ray are seconds. Impact: the window lands in 1970 or the far future and the pillar falsely FAILs.

```bash
# 🚫 WRONG
aws logs start-query --start-time "$START_MS" --end-time "$END_MS" ...
# ✅ CORRECT
aws logs start-query --start-time "$SMOKE_START_S" --end-time "$END_S" ...
```

## N8 Printing log messages or unmasking

Logs must carry no PII (family rule 7); `--unmask` shows masked data and needs `logs:Unmask` ([reference](https://docs.aws.amazon.com/cli/latest/reference/logs/filter-log-events.html)). The validator needs only counts and field presence. Impact: PII or secrets in CI logs and transcripts.

```bash
# 🚫 WRONG
aws logs filter-log-events --log-group-name "$LG" --unmask --query 'events[].message' --output text
# ✅ CORRECT
aws --output json logs get-query-results --query-id "$QID" --query 'statistics.recordsMatched'
```

## N9 Dashboard renders from get-dashboard

`get-dashboard` returns only `DashboardArn`, `DashboardBody`, `DashboardName` ([reference](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-dashboard.html)). Impact: false assurance for on-call dashboards.

```bash
# 🚫 WRONG
aws cloudwatch get-dashboard --dashboard-name "$DASH" >/dev/null && echo "PASS dashboard renders"
# ✅ CORRECT
echo "PASS dashboard.structure (references exist); WARN render: NOT PROVABLE VIA API"
```

## N10 Implicit pager or Region

CLI v2 pages output through the OS pager and a Region must be set ([pagination](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-pagination.html), [env vars](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)). Impact: hung CI jobs and calls to the wrong Region read as FAIL.

```bash
# 🚫 WRONG
aws cloudwatch describe-alarms
# ✅ CORRECT
AWS_PAGER="" aws --region "$AWS_REGION" --output json cloudwatch describe-alarms --alarm-types MetricAlarm CompositeAlarm
```

## N11 Alarms without alarm types

The default returns only metric alarms ([reference](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/describe-alarms.html)). Impact: composite alarms never checked.

```bash
# 🚫 WRONG
aws --output json cloudwatch describe-alarms --alarm-name-prefix "$P"
# ✅ CORRECT
aws --output json cloudwatch describe-alarms --alarm-name-prefix "$P" --alarm-types MetricAlarm CompositeAlarm
```
