# Logs Insights Fields, AWS Sample Queries and Access-Log Format

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). Source ids resolve in the [source bibliography](./source-bibliography.md). Tags map to the [register](./unverified-and-risks.md#tag-to-register-mapping). Queries are the AWS text (text log format); none was executed.

## Contents

- [Field reference](#field-reference)
- [AWS sample queries](#aws-sample-queries)
- [API Gateway access-log format](#api-gateway-access-log-format)

## Field reference

| Field | Meaning and unit | Source |
|---|---|---|
| `@timestamp`, `@logStream`, `@message`, `@log` (`account-id:log-group-name`), `@ingestionTime` | system fields | S9 |
| `@requestId` | invocation RequestId, unchanged across retries | S9, S11 |
| `@type` | for example `"REPORT"` | S9, S10 |
| `@duration`, `@billedDuration` | milliseconds | S9, S10 |
| `@maxMemoryUsed`, `@memorySize` | bytes inferred from AWS queries that divide by 1024*1024 (S11) or 1000*1000 (S10); the pages disagree on the divisor (unverified) | S9, S10, S11 |
| `@initDuration` | used by the AWS SnapStart query with `ispresent()` (S32) but absent from the discovered-field lists (S9, S11) (unverified) | S32, S9, S11 |
| `@xrayTraceId`, `@xraySegmentId` | only when the log line has an X-Ray trace id or X-Ray is enabled | S9, S11 |
| Discovery limit | "only for the first embedded JSON fragment in each log event"; Standard log class only; at most 200 JSON fields | S9 |

## AWS sample queries

Each query is the AWS wording; the source id is on the comment line.

```text
# Timeouts per 30 min (S11). Match the new style too: Status: timeout
filter @message like /Task timed out/
| stats count() by bin(30m)

# Crashes per 30 min (S11). Match the new style too: Error Type: Runtime.ExitError
filter @message like /Process exited/
| stats count() by bin(30m)

# Cold-start percentage (S11)
filter @type = "REPORT"
| stats sum(strcontains(@message, "Init Duration"))/count(*) * 100 as
  coldStartPct, avg(@duration)
  by bin(5m)

# Invocations at 100% memory (S11)
filter @type = "REPORT" and @maxMemoryUsed=@memorySize
| stats
    count_distinct(@requestId)
    by bin(30m)

# Slow invocations, deduplicated, @duration in ms (S10)
fields @timestamp, @requestId, @message, @logStream
| filter @type = "REPORT" and @duration > 1000
| sort @timestamp desc
| dedup @requestId
| limit 20

# Highest billed invocations (S11)
filter @type = "REPORT"
| fields @requestId, @billedDuration
| sort by @billedDuration desc
| limit 100

# SnapStart latency percentiles, AWS Lambda Insights query (S32)
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

Running one: `aws logs start-query --log-group-name /aws/lambda/my-function --start-time <epoch-s> --end-time <epoch-s> --query-string '<query>'`, then `aws logs get-query-results --query-id <id>`. Run it only with the line `approval: logs-insights scope=<log-group> window=<min> by=<user> at=<UTC> relayed-by=<orchestrator>`. Times are epoch seconds, up to 50 log groups, limit up to 100,000; statuses `Scheduled`, `Running`, `Complete`, `Failed`, `Cancelled`, `Timeout`, `Unknown`; a query times out after 60 minutes (all from CLI pages S41, S56 read by targeted extraction: medium confidence, L1). Scans are billable and the pricing page was not read (unverified), so [ask first](./ask-first-decisions.md#c2-log-tool-and-window).

## API Gateway access-log format

Variables per S23 (HTTP API) and S53 (REST). Reading rules are in [branch A](./tree-a-b-entry-and-invocation.md#branch-a-api-gateway-entry).

```text
$context.requestId $context.status $context.error.responseType "$context.error.message"
$context.integration.integrationStatus $context.integration.status "$context.integrationErrorMessage"
$context.integrationLatency $context.awsEndpointRequestId
```

```json
{ "requestId":"$context.requestId", "status":"$context.status",
  "responseType":"$context.error.responseType", "error":"$context.error.message",
  "integrationStatus":"$context.integration.integrationStatus", "functionStatus":"$context.integration.status",
  "integrationError":"$context.integrationErrorMessage", "integrationLatency":"$context.integrationLatency",
  "awsEndpointRequestId":"$context.awsEndpointRequestId" }
```

| Variable | Meaning (AWS wording) | Source |
|---|---|---|
| `$context.integration.integrationStatus` | for Lambda proxy integration, the status code returned from AWS Lambda, not from the backend function code | S23, S53 |
| `$context.integration.status` | for Lambda proxy integrations, the status code that the function code returns | S23, S53 |
| `$context.integrationErrorMessage`, `$context.integration.error` | integration error message | S23, S53 |
| `$context.awsEndpointRequestId` | the AWS endpoint's request id; being equal to the Lambda RequestId in the REPORT line is not stated (medium confidence) | S23, S53 |

The access-log template is limited to 3 KB (S14, S15). Enabling the log is a stage change that the debugger proposes and the deployer applies ([ask first C1](./ask-first-decisions.md#c1-api-gateway-logging)).
