# Pillar: metrics

Back to [SKILL.md](../SKILL.md). Script: `scripts/check-metrics.py`. AWS CLI 2.39.0 reference and CloudWatch and Lambda docs read 2026-10-28.

## Contents

- [Assertion chain](#assertion-chain)
- [Command and JSON paths](#command-and-json-paths)
- [Units, periods and retention](#units-periods-and-retention)
- [Delays](#delays)
- [Custom EMF metrics](#custom-emf-metrics)
- [Limits and cost](#limits-and-cost)
- [Script behaviour](#script-behaviour)

## Assertion chain

1. One `get-metric-data` call reads `AWS/Lambda` `Invocations`, `Errors`, `Throttles` (`Sum`, period 60) and `Duration` (`Maximum`) for dimension `FunctionName`.
2. Every `MetricDataResults[].StatusCode` is `Complete`; `PartialData` means repeat with `NextToken` (the CLI paginates by default).
3. `Invocations` Sum is at least the number of smoke calls, `Errors` equals the expected count, `Throttles` is 0. Throttles and other invocation errors do not count as `Invocations` or `Errors`, and the `Errors` timestamp reflects when the Event Function was invoked ([metric types](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html)). View invocation metrics with `Sum`; use `Duration` with `Average`, `Maximum` or percentiles.
4. API Gateway in front: a 500 means the Lambda API rejected the invocation (for example throttling), a 502 means a function error or a malformed response, and 429 comes from API Gateway's own throttling ([Lambda and API Gateway errors](https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway-errors.html)). Expect `Throttles` or `Errors` accordingly if the smoke test saw 5xx.

## Command and JSON paths

```bash
cd "$TMPDIR_FOR_Q"   # q.json lives here; file:// is read relative to the current directory
# q.json: [{"Id":"inv","MetricStat":{"Metric":{"Namespace":"AWS/Lambda","MetricName":"Invocations","Dimensions":[{"Name":"FunctionName","Value":"FN"}]},"Period":60,"Stat":"Sum"}}, ...]
aws --output json cloudwatch get-metric-data --metric-data-queries file://q.json \
    --start-time "$M_START" --end-time "$M_END" \
    --query 'MetricDataResults[].{id:Id,status:StatusCode,sum:sum(Values)}'
```

- Up to 500 `MetricDataQuery` per call; `Id` must start with a lowercase letter ([get-metric-data](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-metric-data.html)).
- Paths: `.MetricDataResults[].{Id, StatusCode, Values[], Timestamps[]}`. `Timestamps` are ISO 8601 in CLI v2 although the description says Unix; parse the structure, not the example (medium confidence).
- The `file://` relative path on Windows is (medium confidence); the research documents it for `fileb://`.
- `get-metric-statistics` needs the exact published dimension combination, returns at most 1,440 points per call and not in chronological order ([reference](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-metric-statistics.html)).

## Units, periods and retention

- `StartTime` is inclusive, `EndTime` exclusive; start times within the last 15 days round down to the minute, so align both to the period: `M_START=$((S/60*60))`, `M_END=$(((E/60+1)*60))`.
- `Period` is a multiple of 60 for standard resolution. Retention: periods under 60 s keep 3 hours (high-resolution custom metrics only), 60 s keeps 15 days, 300 s keeps 63 days, 3600 s keeps 455 days.
- Time parameters accept ISO 8601 or epoch seconds; see [CLI environment](./cli-environment-and-exit-codes.md#time-units-per-api).

## Delays

Lambda sends metrics in 1-minute intervals ([using metrics](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html)). A new custom metric can take up to 2 minutes for statistics and up to 15 minutes to appear in `list-metrics` ([publishing](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html)), so `list-metrics` is not a freshness probe. At the deadline an `Invocations` Sum of 0 is WARN (inconclusive).

## Custom EMF metrics

`--custom-namespace NS --custom 'Name:Dim=Value'` builds one `MetricStat` per metric on its exact dimension set. EMF timestamps must be at most 14 days in the past and 2 hours in the future; delivery is at least once; `StorageResolution` defaults to 60 ([EMF specification](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). Decision: [K6](./ask-first-decisions.md#k6-custom-emf-namespace-and-dimension-sets). EMF parse and validation failures are tracked by metrics in `AWS/Logs`; their names are (unverified). The Quarkiverse has no CloudWatch Micrometer registry (family fact), so custom metrics reach CloudWatch through EMF or the SDK.

## Limits and cost

`get-metric-data` allows 500 queries and 100,800 points per call; `GetMetricData` pricing is (unverified). Keep windows to the smoke window.

## Script behaviour

`check-metrics.py --function F [--min-invocations N] [--max-errors N] [--custom-namespace NS --custom ...] [--wait-seconds N]` prints `metrics.invocations`, `metrics.errors`, `metrics.throttles`, `metrics.duration`, `metrics.custom.<name>`. The datapoints of the window are aggregated by the statistic that was queried: `Invocations`, `Errors`, `Throttles` and a custom `Sum` or `SampleCount` are added; `Duration` and a custom `Maximum` take the largest value, a custom `Minimum` the smallest; a custom `Average` is the mean of the per-period averages (labelled so; it is not weighted by sample count). Adding per-period maxima is wrong. A custom metric passes when it has at least one datapoint. A status other than `Complete` is FAIL (`PartialData` is WARN); Sum 0 for invocations is WARN; below `--min-invocations`, errors above `--max-errors` or any throttle is FAIL.
