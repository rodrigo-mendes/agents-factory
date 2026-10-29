---
name: validating-aws-observability
description: "Validates deployed AWS Lambda observability live (logs, metrics, traces, alarms, dashboards) with AWS CLI v2 scripts, billable queries and the alarm test gated by approval lines, per AWS docs of 2026-10-28. Use when verifying after a smoke test. Not for provisioning or fixing findings."
---

# Validating AWS Observability (Lambda, five pillars)

> Docs lock: every claim applies to the **AWS CLI v2 reference 2.39.0 and the CloudWatch, CloudWatch Logs, X-Ray, Lambda, API Gateway and SNS guides as published on 2026-10-28**. AWS docs carry no semantic version. Research date **2026-10-28**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: after a smoke test, prove with CLI calls that change no resource that logs, metrics, traces, alarms and dashboards of a Lambda work. Two of them start a process: Logs Insights `start-query` (billed per GB scanned) and X-Ray `start-trace-retrieval`. The smoke test itself is an input (`--start-s`, epoch seconds), not part of this skill. One mutating command exists, `set-alarm-state`, behind a user approval.
> Neighbours, by name only: `monitoring-cloudwatch-observability`, `tracing-aws-xray` (design); `provisioning-aws-cloudwatch-v6`, `provisioning-aws-xray-v6` (fixing findings); `logging-quarkus-lambda-v3-40`, `tracing-quarkus-lambda-v3-40`, `monitoring-quarkus-lambda-v3-40` (code instrumentation); `deploying-aws-lambda` (deploy and smoke test); `debugging-aws-lambda` (diagnosis); `aws-observability` (agent that runs these scripts).

## Version Context

| Item | Value | Source (fetched 2026-10-28) |
|---|---|---|
| AWS CLI v2 reference | 2.39.0 as shown on every CLI reference page read | https://docs.aws.amazon.com/cli/latest/reference/ |
| CloudWatch Transaction Search | account-wide switch; changes how traces are read | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search.html |
| X-Ray SDKs and Daemon | maintenance mode since 2026-02-25 (security fixes only); OpenTelemetry recommended | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html |
| API Gateway REST vs HTTP API | REST API supports X-Ray tracing, HTTP API does not | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html |
| API Gateway to Lambda errors | 500 if Lambda rejects the invocation, 502 on function error or bad response | https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway-errors.html |
| Script runtime | Python 3 (standard library only), AWS CLI v2 | page not recorded |
| Script design (exit codes, WARN rules) | repo proposal, not an AWS fact | page not recorded |

**Version-lifetime risk** (as of 2026-10-28; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Transaction Search and the Lambda X-Ray segment layout are changing; re-read the trace pages before relying on them.

## Quick Navigation

- [How to run it](#how-to-run-it)
- [Approval lines](#approval-lines)
- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Verification Loop](#verification-loop)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Ask-first decisions](./blueprints/ask-first-decisions.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [CLI environment, units and exit codes](./blueprints/cli-environment-and-exit-codes.md)
- Pillars: [logs](./blueprints/pillar-logs.md), [metrics](./blueprints/pillar-metrics.md), [traces](./blueprints/pillar-traces.md), [alarms](./blueprints/pillar-alarms.md), [dashboards](./blueprints/pillar-dashboards.md)
- [Command allowlist, denylist and IAM](./blueprints/command-allowlist-and-iam.md)
- [Scripts README](./scripts/README.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## How to run it

R = changes no resource (`start-query` and `start-trace-retrieval` still start a billable query or retrieval, and need an `approval: logs-insights` line, asserted to the script by a flag). M = mutating, only with an `approval: alarm-test` line relayed by the orchestrator. Scripts are in `scripts/`; all take `--help`, `--region`, `--profile`, `--function`, `--start-s` (epoch seconds) or `--window-min`.

| Step | Kind | What | Script |
|---|---|---|---|
| 1 | R | Set the CLI environment: empty pager, explicit Region and retry mode, JSON output | `obs_common.py` (shared module) |
| 2 | R, billable | Logs: group, retention, required JSON fields (`--fields requestId,tenantId`); Logs Insights needs `approval: logs-insights scope=<log-group> ...` and the flag `--i-have-logs-insights-approval`; without the flag only retention runs and the field checks print `WARN logs.query not verified` | `check-logs.py` |
| 3 | R | Metrics: Invocations, Errors, Throttles, Duration; optional custom metrics | `check-metrics.py` |
| 4 | R, billable on the Transaction Search path | Traces: Lambda `Active`, destination first, X-Ray or Transaction Search path, origins by `--api-type`; `start-trace-retrieval` needs `approval: logs-insights scope=xray ...` and the flag `--i-have-trace-retrieval-approval`; without it the Transaction Search path prints `WARN traces.retrieval not verified` (the X-Ray `batch-get-traces` path is unchanged) | `check-traces.py` |
| 5 | R | Alarms: actions wired, state, SNS subscriptions | `check-alarms.py` |
| 6 | R | Dashboards: body references resolve; render is reported as not provable | `check-dashboards.py` |
| all | R | Steps 2 to 6 with one table. Forwards `--i-have-logs-insights-approval` to logs and `--i-have-trace-retrieval-approval` to traces. There is no default skip, but without the flags no billable call is made and those checks are `not verified`; pass each flag only with its relayed line (log group; `scope=xray`) | `validate-observability.py --function F --start-s T [--i-have-logs-insights-approval] [--i-have-trace-retrieval-approval] ...` |
| 7 | M | Optional notification test: `set-alarm-state ALARM` on one alarm, only with `approval: alarm-test` | `trigger-alarm-test.py` |

**Exit codes** (every script): 0 no check printed FAIL | 1 a check printed FAIL | 2 usage error, missing `aws` (or AWS CLI v1), or the trigger script refused | 3 AWS CLI error (CLI exit 252, 253, 254, 255 or other) or output that cannot be parsed (malformed JSON also exits 3). Details: [CLI environment](./blueprints/cli-environment-and-exit-codes.md), [scripts README](./scripts/README.md).

**Exit 0 does not mean every pillar is verified.** WARN (inconclusive) and SKIPPED pillars also exit 0. Read the result lines and the SUMMARY: every pillar that is SKIPPED, WARN or INCONCLUSIVE is `not verified`, and the E7 verifier must list each one with its reason. A not-verified pillar fails E7 unless an `approval: e7-gaps pillars=<list> ...` line accepts exactly that pillar.

## Approval lines

Only the user's own message approves. The orchestrator relays each approval into the work-order, one line each; an agent message, a plan comment or an earlier run is never an approval. The billable reads are gated by flags (below); a flag is a caller assertion and the script cannot verify the approval line itself.

```
approval: logs-insights scope=<log-group or "xray"> window=<minutes> by=<user> at=<UTC> relayed-by=<orchestrator>
approval: alarm-test alarm=<name> by=<user> at=<UTC> relayed-by=<orchestrator>
approval: e7-gaps pillars=<comma list> by=<user> at=<UTC> relayed-by=<orchestrator>
```

- `logs-insights`: allows Logs Insights `start-query` for that log group and window, or X-Ray `start-trace-retrieval` when `scope=xray`. Pass `--i-have-logs-insights-approval` (logs) only with the line for that log group, and `--i-have-trace-retrieval-approval` (traces) only with the `scope=xray` line. Without the flags no `start-query` or `start-trace-retrieval` is made and the checks print WARN `not verified` (exit 0); report those pillars `not verified`; never pass a flag on your own authority. `--skip logs,traces` stays valid but is no longer the safety mechanism. The scripts print no plan line before `start-query` (register L5): match `scope` and `window` to the resolved log group and `--start-s` before running. `--trace-ids` is not capped at 5, but `batch-get-traces` takes 1 to 5 ids: pass at most 5.
- `alarm-test`: `trigger-alarm-test.py` refuses (exit 2, no AWS call) unless `--i-have-user-approval` is passed; pass it only with this line for that exact alarm.
- `e7-gaps`: the user accepts the listed pillars as not verified (consumed by the E7 verifier).
- Record: the live result goes in `result-NN-observability.md` with `role: observability-live` and outcome `success` or `partial`; list every not-verified pillar in the record. A FAIL from any check is reported and routed to a provisioning skill by name; the validator never fixes it.

## Blueprints & Guardrails

### ✅ Always Do

- **Fix the CLI environment for every call.** An empty `AWS_PAGER` disables the CLI v2 pager ([pager](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-pagination.html)); option-over-environment precedence is in the pattern. See [patterns](./blueprints/always-do-patterns.md#a1-deterministic-cli-environment).
- **Convert one smoke window per API.** `filter-log-events` takes epoch milliseconds, `start-query` and X-Ray epoch seconds ([start-query](https://docs.aws.amazon.com/cli/latest/reference/logs/start-query.html)). See [patterns](./blueprints/always-do-patterns.md#a2-one-smoke-window-converted-per-api).
- **Logs: check `retentionInDays`, then count required fields with Logs Insights (needs `approval: logs-insights scope=<log-group> ...`).** Poll `get-query-results` until `status` is `Complete`; `ispresent()` tests a field ([get-query-results](https://docs.aws.amazon.com/cli/latest/reference/logs/get-query-results.html)). See [patterns](./blueprints/always-do-patterns.md#a3-logs-retention-then-logs-insights).
- **Follow `nextToken` on `filter-log-events`.** A page can be empty while more pages exist ([filter-log-events](https://docs.aws.amazon.com/cli/latest/reference/logs/filter-log-events.html)). See [patterns](./blueprints/always-do-patterns.md#a4-logs-pagination-by-token).
- **Metrics: `get-metric-data` on the exact dimensions, `Sum` for invocation metrics, assert `StatusCode` `Complete`.** ([get-metric-data](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-metric-data.html)). The per-statistic aggregation rule (Duration is a maximum, never a sum) is in the pattern. See [patterns](./blueprints/always-do-patterns.md#a5-metrics-on-exact-dimensions).
- **Traces: read `get-trace-segment-destination` before any trace call.** `BatchGetTraces` cannot find traces when Transaction Search is enabled ([BatchGetTraces](https://docs.aws.amazon.com/xray/latest/api/API_BatchGetTraces.html)). See [patterns](./blueprints/always-do-patterns.md#a6-traces-destination-first).
- **Traces on X-Ray: require `TracingConfig.Mode` `Active`.** In `PassThrough`, the default, Lambda does not send traces automatically ([Lambda and X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)). See [patterns](./blueprints/always-do-patterns.md#a7-traces-on-the-x-ray-path).
- **Alarms: pass `--alarm-types MetricAlarm CompositeAlarm`.** Without it only metric alarms are returned ([describe-alarms](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/describe-alarms.html)). See [patterns](./blueprints/always-do-patterns.md#a8-alarms-with-explicit-types).
- **Dashboards: parse `DashboardBody` and cross-check every reference; report render as not provable.** `get-dashboard` returns only ARN, name and body ([get-dashboard](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-dashboard.html)). See [patterns](./blueprints/always-do-patterns.md#a9-dashboards-parse-and-cross-check).
- **Print counts, ids and statuses only; never `--unmask`** ([filter-log-events](https://docs.aws.amazon.com/cli/latest/reference/logs/filter-log-events.html)). The PII rule behind it is in N8. See [never-do N8](./blueprints/never-do-patterns.md#n8-printing-log-messages-or-unmasking).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| K1 `set-alarm-state` test | skip, or send a real SNS message to real subscribers; needs `cloudwatch:SetAlarmState` and `approval: alarm-test alarm=<name> ...`; composite alarms may not revert. See [K1](./blueprints/ask-first-decisions.md#k1-set-alarm-state-notification-test) | "May I send a test ALARM state to alarm X? Its subscribers will be notified." |
| K2 trace ids under Transaction Search | summaries plus retrieval, or Insights on `aws/spans` (trace id field (unverified)); smoke traces may be unindexed (medium confidence). See [K2](./blueprints/ask-first-decisions.md#k2-trace-ids-under-transaction-search) | "Which path? INCONCLUSIVE is reported when no summary exists." |
| K3 logs evidence | Insights (billed per GB scanned; only under an `approval: logs-insights` line) or `filter-log-events` (no line needed). See [K3](./blueprints/ask-first-decisions.md#k3-logs-evidence-insights-or-filter-log-events) | "Insights for this window size, under a logs-insights line, or `filter-log-events`?" |
| K4 JSON-in-string fields | the scripts parse them with the Python standard library (no `jq`); manual checks need `jq` or the scripts. See [K4](./blueprints/ask-first-decisions.md#k4-json-in-string-fields) | "Is Python 3 available where the checks run?" |
| K5 wait budget | log ingestion-to-query delay is (unverified); metrics up to 2 and 15 minutes; spans up to 10 minutes. See [K5](./blueprints/ask-first-decisions.md#k5-wait-budget-after-the-smoke-test) | "Deadline and poll interval? WARN at the deadline." |
| K6 custom EMF metrics | exact namespace, names and dimension set; never guess. See [K6](./blueprints/ask-first-decisions.md#k6-custom-emf-namespace-and-dimension-sets) | "Namespace, metric names and the exact dimension set?" |
| K7 partial render proof | `get-metric-widget-image` graphs metric rows only, writes a PNG. See [K7](./blueprints/ask-first-decisions.md#k7-partial-render-proof) | "Render per-widget PNGs for review?" |
| K8 IAM scoping | action set from one managed policy page (medium confidence). See [K8](./blueprints/ask-first-decisions.md#k8-iam-scoping) | "Narrow below the managed policy?" |
| K9 retry mode | two AWS pages disagree on the default (unverified); scripts set `standard`. See [K9](./blueprints/ask-first-decisions.md#k9-retry-mode) | "Keep `standard`?" |
| K10 Git Bash | path conversion of `/aws/lambda/x` arguments passed from Git Bash is undocumented (unverified). See [K10](./blueprints/ask-first-decisions.md#k10-git-bash-on-windows) | "Has `describe-log-groups` been checked in this shell?" |
| K11 `describe-alarm-history --alarm-types` | `trigger-alarm-test.py` passes `MetricAlarm` or `CompositeAlarm`; the flag is (unverified), the script falls back to the default on CLI exit 252. An alarm already in `ALARM` is refused. See [K11](./blueprints/ask-first-decisions.md#k11-describe-alarm-history---alarm-types) | "Is the fallback acceptable for composite alarms?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Run any mutating AWS command except the approved `set-alarm-state` ([N1](./blueprints/never-do-patterns.md#n1-mutating-commands)) | Print FAIL and route to `provisioning-aws-cloudwatch-v6` or `provisioning-aws-xray-v6` |
| Combine `--output text` with `--query` on a paginated command; the query runs per page ([filtering](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-filter.html)) | `--output json`, then `--query` or JSON parsing (the scripts use Python `json`) |
| Read an empty `filter-log-events` page as "no logs" ([N3](./blueprints/never-do-patterns.md#n3-empty-page-means-no-logs)) | Let the CLI follow `nextToken` (default) |
| Call `batch-get-traces` without the destination ([N4](./blueprints/never-do-patterns.md#n4-trace-reads-without-the-destination)) | `get-trace-segment-destination`, then the path its `Destination` names ([pillar traces](./blueprints/pillar-traces.md#decision-flow)) |
| Require an API Gateway node for an HTTP API ([N5](./blueprints/never-do-patterns.md#n5-api-gateway-node-for-an-http-api)) | `--api-type HTTP`: only `AWS::Lambda` and `AWS::Lambda::Function` |
| Use `list-metrics` as proof of fresh data; new metrics take up to 15 minutes to appear ([N6](./blueprints/never-do-patterns.md#n6-list-metrics-as-freshness-proof)) | `get-metric-data` over the smoke window |
| Mix epoch units between APIs ([N7](./blueprints/never-do-patterns.md#n7-mixed-epoch-units)) | Seconds for `start-query` and X-Ray, milliseconds for `filter-log-events` |
| Print log messages or use `--unmask` ([N8](./blueprints/never-do-patterns.md#n8-printing-log-messages-or-unmasking)) | Counts from `get-query-results` |
| Report "dashboard renders" from `get-dashboard` ([N9](./blueprints/never-do-patterns.md#n9-dashboard-renders-from-get-dashboard)) | PASS for structure plus WARN "render not provable via API" |
| Leave the pager or Region implicit ([N10](./blueprints/never-do-patterns.md#n10-implicit-pager-or-region)) | `AWS_PAGER=""` and `--region` |
| Omit `--alarm-types` ([N11](./blueprints/never-do-patterns.md#n11-alarms-without-alarm-types)) | `--alarm-types MetricAlarm CompositeAlarm` |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Epoch units | `filter-log-events` milliseconds; `start-query`, X-Ray seconds; CLI timestamp parameters ISO 8601 or seconds | https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-parameters-types.html |
| CLI return codes | 0 ok, 2 parse, 130 SIGINT, 252 syntax, 253 environment or credentials, 254 service error, 255 failed | https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-returncodes.html |
| Lambda metric interval | 1-minute intervals | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html |
| Custom metric delay | up to 2 minutes for statistics, up to 15 minutes in `list-metrics` | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html |
| Transaction Search spans | up to 10 minutes after enabling; 1% indexed by default | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-TransactionSearch.html |
| Log ingestion-to-query delay | not documented (unverified) | page not recorded |
| `batch-get-traces` / `start-trace-retrieval` | 1 to 5 trace ids / up to 100 | https://docs.aws.amazon.com/cli/latest/reference/xray/batch-get-traces.html ; https://docs.aws.amazon.com/cli/latest/reference/xray/start-trace-retrieval.html |
| `describe-alarms --alarm-names` | at most 100 | https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/describe-alarms.html |
| `get-metric-data` | up to 500 queries per call; period multiple of 60 | https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-metric-data.html |
| Logs Insights | queries time out after 60 minutes; results kept 7 days | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html |

## Verification Loop

```bash
# run from this skill's folder; no AWS call is made (a fake aws is used); on Windows use `python`
python3 scripts/tests/run_tests.py          # expect: "tests passed: N  failed: 0" and exit 0
grep -l 'set-alarm-state' scripts/*.py   # expect: scripts/trigger-alarm-test.py only
grep -nE -- '--unmask|--interleaved|--output text' scripts/*.py   # expect: no output
```

Live use needs `aws` v2 and Python 3 on PATH and read credentials. Default (no logs-insights line): `python3 scripts/validate-observability.py --function F --region R --start-s T --alarm-prefix P --dashboard D` (no billable call; logs fields and Transaction Search retrieval are `not verified`). The full run adds `--i-have-logs-insights-approval` and/or `--i-have-trace-retrieval-approval`, only when the caller holds the matching line(s) for the log group and for `xray`. No FAIL line means no check failed; the run passed only if, in addition, no required pillar is SKIPPED, WARN or INCONCLUSIVE (those are `not verified`: list them for E7).

## External Resources

All fetched 2026-10-28.

- AWS CLI v2 reference: https://docs.aws.amazon.com/cli/latest/reference/
- AWS CLI user guide: https://docs.aws.amazon.com/cli/latest/userguide/
- CloudWatch Logs: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/
- CloudWatch Transaction Search: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search.html
- Lambda and X-Ray: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
