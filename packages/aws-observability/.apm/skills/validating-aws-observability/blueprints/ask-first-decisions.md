# Ask-first decisions

Back to [SKILL.md](../SKILL.md). Ask the user (through the orchestrator) before acting. An agent's own message is never an approval.

## Contents

- [K1 set-alarm-state notification test](#k1-set-alarm-state-notification-test)
- [K2 Trace ids under Transaction Search](#k2-trace-ids-under-transaction-search)
- [K3 Logs evidence: Insights or filter-log-events](#k3-logs-evidence-insights-or-filter-log-events)
- [K4 JSON-in-string fields](#k4-json-in-string-fields)
- [K5 Wait budget after the smoke test](#k5-wait-budget-after-the-smoke-test)
- [K6 Custom EMF namespace and dimension sets](#k6-custom-emf-namespace-and-dimension-sets)
- [K7 Partial render proof](#k7-partial-render-proof)
- [K8 IAM scoping](#k8-iam-scoping)
- [K9 Retry mode](#k9-retry-mode)
- [K10 Git Bash on Windows](#k10-git-bash-on-windows)
- [K11 describe-alarm-history --alarm-types](#k11-describe-alarm-history---alarm-types)

## K1 set-alarm-state notification test

The only mutating command of this skill; script `trigger-alarm-test.py`.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A skip; validate alarms read-only | zero side effects | does not prove alarm to action end to end | shared or production accounts, on-call topics |
| B `set-alarm-state --state-value ALARM` on one named alarm, then `describe-alarm-history --history-item-type Action` | proves the action ran | sends a real SNS message to real subscribers; needs `cloudwatch:SetAlarmState`, which `CloudWatchReadOnlyAccess` lacks | dev or test accounts with an approved alarm and audience |

- Facts ([set-alarm-state](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/set-alarm-state.html)): when the new state differs, the configured action runs and `ALARM` sends an SNS message; a metric alarm returns to its actual state quickly, often within seconds; a composite alarm is not guaranteed to return until a child alarm changes state; `--alarm-name`, `--state-value`, `--state-reason` (max 1023 characters) are required; Auto Scaling actions need `--state-reason-data`. Alarm history retention is (unverified).
- Protocol: ask per run, naming the exact alarm and that its subscribers get a test notification. The agent passes `--i-have-user-approval` only with the line `approval: alarm-test alarm=<name> by=<user> at=<UTC> relayed-by=<orchestrator>` that the orchestrator relayed for that alarm. Never on a composite alarm without saying its state may not revert.
- Ask: "May I send a test ALARM state to alarm X now? Its SNS subscribers will be notified."

## K2 Trace ids under Transaction Search

With Transaction Search active only an indexed share of spans (1% free by default) becomes trace summaries, so smoke traces may not be indexed (medium confidence); whether `get-trace-summaries` returns only indexed traces is (unverified).

| Option | Optimizes | Sacrifices |
|---|---|---|
| A `get-trace-summaries` then `start-trace-retrieval` and `list-retrieved-traces` | same assertions as the X-Ray path | zero summaries at the default index rate |
| B Logs Insights on `aws/spans` | sees all ingested spans | trace id field name is (unverified); billed per GB scanned; needs `approval: logs-insights scope=aws/spans ...` |
| C user raises the indexing percentage | more summaries | mutating `update-indexing-rule`, forbidden here; route to `provisioning-aws-xray-v6` |

Ask: "Which path, A or B? Report INCONCLUSIVE, not FAIL, when A returns no summaries."

## K3 Logs evidence: Insights or filter-log-events

| Option | Optimizes | Sacrifices |
|---|---|---|
| A Logs Insights (no default; needs `approval: logs-insights scope=<log-group> ...`) | field assertions with `ispresent`; JSON field discovery | billed per GB scanned; 100 concurrent queries shared with dashboards and scheduled queries |
| B `filter-log-events` | no query lifecycle | text patterns only; low TPS quota; empty pages |

Insights discovers Lambda JSON fields only in the first embedded JSON fragment of each event (at most 200 fields) and only for the Standard log class; with the Text log format the behaviour is (medium confidence). Ask before scanning a large window.

## K4 JSON-in-string fields

`--query` cannot parse `Segments[].Document` or `DashboardBody` (JSON in a string). The skill's scripts parse them with the Python 3 standard library (`json`), so no `jq` is needed; the manual one-liners in the pillar blueprints use `jq` with `fromjson`. Ask: "Is Python 3 available where the checks run? If not, mark trace and dashboard deep checks SKIPPED."

## K5 Wait budget after the smoke test

Known delays: Lambda sends metrics in 1-minute intervals; a new custom metric takes up to 2 minutes for statistics and up to 15 minutes to appear in `list-metrics`; spans can take up to 10 minutes after Transaction Search is enabled; the log ingestion-to-query delay is (unverified). Ask for a deadline (for example 5 to 15 minutes) and a poll interval (`--wait-seconds`, `--retry-seconds`); at the deadline report WARN (inconclusive), not FAIL.

## K6 Custom EMF namespace and dimension sets

EMF needs `_aws.CloudWatchMetrics[]` with `Namespace`, `Dimensions` (DimensionSets of at most 30 keys), `Metrics[]`; at most 100 metric definitions per event; every DimensionSet used creates a new metric and a high-cardinality dimension such as `requestId` creates one per value ([EMF specification](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). Retrieval needs the exact published dimension set. Ask for namespace, metric names and the exact set; never guess. Flag `tenantId` as a dimension unless an ADR exists (family rule 7). Application field names such as `requestId` and `tenantId` are (medium confidence) because Lambda's own Java key is `AWSrequestId`; pass them with `--fields`.

## K7 Partial render proof

`get-metric-widget-image --metric-widget '<json>' --output-format png` returns `MetricWidgetImage` (base64); limits: 100 metrics and 100 KB per graph, 20 TPS, not in GovCloud (US) ([reference](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-metric-widget-image.html)). It proves CloudWatch can graph the metric rows of a widget; it does not prove the console dashboard (log, alarm and text widgets, variables, layout) renders, and it writes a PNG locally. Ask: "Render per-widget PNGs for human review?" Never report it as "dashboard renders".

## K8 IAM scoping

The read action set comes from one managed policy page (medium confidence); per-action access levels and resource-level scoping are (unverified). Start from the set in [command allowlist and IAM](./command-allowlist-and-iam.md) with `Resource "*"`; grant `cloudwatch:SetAlarmState` in a separate, temporary statement only for K1. Ask before narrowing below the managed policy.

## K9 Retry mode

Two AWS pages disagree on the default (see [CLI environment](./cli-environment-and-exit-codes.md#retry-mode); (unverified)). The scripts use `standard`; adaptive is documented as experimental. Ask only if the user wants another value.

## K10 Git Bash on Windows

AWS documents nothing about argument path conversion for names such as `/aws/lambda/x` ((unverified)). The Python scripts call `aws` directly (no shell in between), but Git Bash can still convert the arguments it passes to `python`; the scripts print a note when `MSYSTEM` is set. Ask the user to run `describe-log-groups` once in the target shell and compare the group name before trusting a PASS or FAIL on Windows.

## K11 describe-alarm-history --alarm-types

Without `--alarm-types`, `describe-alarm-history` is expected to cover metric alarms only, as `describe-alarms` does ([describe-alarms](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/describe-alarms.html)); that `describe-alarm-history` accepts `--alarm-types MetricAlarm|CompositeAlarm` is (unverified): the CLI page was read only through a summary (register U9, S44). `trigger-alarm-test.py` passes the flag and, if the CLI rejects it (exit 252), warns and falls back to the default; with that fallback a composite alarm's Action history may be missing, so the Action check can FAIL falsely. Ask the user whether to accept that, or to read the history in the console. The script also refuses an alarm already in `ALARM` (the state would not change, so no action runs) and prints a RECOVERY line when a CLI error follows `set-alarm-state`.
