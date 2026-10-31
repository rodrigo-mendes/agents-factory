# Pillar: dashboards

Back to [SKILL.md](../SKILL.md). Script: `scripts/check-dashboards.py`. AWS CLI 2.39.0 reference and CloudWatch dashboard docs read 2026-10-28. The manual `bash` forms below use `jq`; the Python scripts do not. The dashboard body page was read only in part (coverage limit L1).

## Contents

- [What can and cannot be proven](#what-can-and-cannot-be-proven)
- [Commands and JSON paths](#commands-and-json-paths)
- [Body structure](#body-structure)
- [Reference checks](#reference-checks)
- [Partial render proof](#partial-render-proof)
- [Script behaviour](#script-behaviour)

## What can and cannot be proven

`get-dashboard` returns only `DashboardArn`, `DashboardName` and `DashboardBody`; `list-dashboards` returns only name, ARN, last-modified and size. None of the fetched pages documents an API that reports whether a dashboard renders. The skill therefore checks structure and references and always reports `render: NOT PROVABLE VIA API` as WARN. Never write "dashboard renders" ([N9](./never-do-patterns.md#n9-dashboard-renders-from-get-dashboard)).

## Commands and JSON paths

| Step | Command | Read |
|---|---|---|
| exists | `cloudwatch list-dashboards --dashboard-name-prefix P` | `.DashboardEntries[].DashboardName`, `.DashboardArn`, `.LastModified`, `.Size`; paginated, up to 1000 per page |
| body | `cloudwatch get-dashboard --dashboard-name D` | `.DashboardBody` is a JSON string: `jq -r .DashboardBody` |
| metrics | `cloudwatch list-metrics --namespace NS --metric-name N` | `.Metrics[].Dimensions[]` |
| log groups | `logs describe-log-groups --log-group-name-prefix G` | `.logGroups[].logGroupName` |
| alarms | `cloudwatch describe-alarms --alarm-names A --alarm-types MetricAlarm CompositeAlarm` | `.MetricAlarms[]`, `.CompositeAlarms[]` |

The `LastModified` description says milliseconds while the example shows an ISO 8601 string; CLI v2 translates DateTimes to ISO 8601 (medium confidence).

## Body structure

From the [dashboard body structure](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/CloudWatch-Dashboard-Body-Structure.html) page (read in part):

- `widgets` is an array of 0 to 500 widgets; `type` is `metric`, `text`, `log`, `alarm`, `explorer` or `chart`.
- Metric widget: `properties.metrics` rows `[Namespace, MetricName, DimName, DimValue, ..., {options}]`; in rows after the first, `"."` repeats the previous row's value; `properties.region` is required.
- Alarms are referenced in `properties.annotations.alarms` (metric widget) or `properties.alarms` (alarm widget). Whether a reference is a name or an ARN is (medium confidence); the script accepts both.
- Log widget: `region` and `query` are required; the query starts with `SOURCE '<log-group>'` entries separated by `|`.

## Reference checks

```bash
BODY=$(aws --output json cloudwatch get-dashboard --dashboard-name "$DASH" | jq -r .DashboardBody)
jq -r '.widgets[] | select(.type=="log") | .properties.query' <<<"$BODY" | grep -o "SOURCE '[^']*'"
jq -r '.widgets[] | (.properties.alarms // .properties.annotations.alarms // [])[]' <<<"$BODY"
jq -c '.widgets[] | select(.type=="metric") | {region: .properties.region, rows: .properties.metrics}' <<<"$BODY"
```

Then: resolve `"."` against the previous resolved row; confirm each metric exists in `list-metrics` on its exact dimension set; each `SOURCE` log group in `describe-log-groups`; each alarm in `describe-alarms`. `list-metrics` is not a freshness probe: new metrics take up to 15 minutes to appear and metrics without data in two weeks are not listed ([list-metrics](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/list-metrics.html)); a FAIL on a very new metric may only be late, so re-run after the delay. Rows that are not `[Namespace, MetricName, ...]` (for example metric math) are counted and skipped, not evaluated.

## Partial render proof

Decision [K7](./ask-first-decisions.md#k7-partial-render-proof): `get-metric-widget-image` renders a metric graph server-side from the rows of one metric widget. It shows CloudWatch can graph those metrics. It does not show that log, alarm or text widgets, variables or layout render in the console. It writes a PNG locally, so it is not part of the scripts.

## Script behaviour

`check-dashboards.py (--dashboard NAME ... | --dashboard-prefix P)` prints `dash.<name>.exists` (only on failure), `.body`, `.metric`, `.log`, `.alarm` and always `.render` (WARN). Missing dashboard, invalid body, a metric widget without `region`, a metric, log group or alarm that cannot be found: FAIL. Exit codes: [CLI environment](./cli-environment-and-exit-codes.md#script-exit-code-mapping).
