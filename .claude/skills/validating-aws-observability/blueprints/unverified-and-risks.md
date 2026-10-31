# Unverified Register, Risks and Bibliography

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 92%, a deep run using all 3 iterations, 9 triangulated Always-Do patterns (A1 to A9) and one medium pattern (A10). Its header counts 6 unverified and 5 irresolvable items; this register lists 9 and 6: U7 (`sum(ispresent())`) and U8 (`jq` version) were tagged in the research text without a number, U9 (`describe-alarm-history --alarm-types`) was added by the P6 fix, and I6 is contradiction C1 (retry default). Research ids are kept in the Research id column. Family facts F34, F35, F38 and family rules 7 and 9 to 12 keep their tags. No AWS command was executed by the research, and the scripts of this skill were not run against AWS (L3).

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- AWS docs and the CLI reference carry no semantic version; the snapshot is 2026-10-28 (reference 2.39.0). Quotas, flags and output shapes can change without notice.
- Transaction Search and the Lambda X-Ray segment layout are changing features; the X-Ray SDKs and Daemon are in maintenance mode since 2026-02-25. Re-read the trace pages before relying on them.
- CLI v1 behaviour (pager, retry defaults) is out of scope.

## Unverified items

9 unverified items (do not assert them).

| ID | Research id | Item | Impact and workaround |
|---|---|---|---|
| U1 | U6 | Whether `retentionInDays` is absent when logs never expire | Script treats absence as FAIL by repo policy; `--allow-no-retention` downgrades |
| U2 | U7 | Alarm history retention period | Run the trigger test and read the history at once |
| U3 | U8 | Maximum `get-trace-summaries` time window | Keep the smoke window short |
| U4 | U9 | X-Ray trace retention | Validate soon after the smoke test |
| U5 | U10 | Names of the `AWS/Logs` EMF failure metrics | Do not alarm on them from this skill |
| U6 | U18 | `GetMetricData` pricing | Keep windows to the smoke window |
| U7 | A3 note | `sum(ispresent(...))` as an Insights aggregation | Use the two-query form with documented functions |
| U8 | Compat matrix | Minimum `jq` version | Retired for the scripts: since 2026-10-28 they need only Python 3 (standard library); the manual `jq` one-liners in the blueprints are optional |
| U9 | P6 fix | `describe-alarm-history` accepts `--alarm-types MetricAlarm\|CompositeAlarm` (page S44 read only as a summary; the flag exists for `describe-alarms`) | `trigger-alarm-test.py` passes it and falls back to the default on CLI exit 252 (K11) |

## Irresolvable items

6 irresolvable items (no fetched page states it, or two official pages disagree).

| ID | Research id | Item | What to do |
|---|---|---|---|
| I1 | U1 | Delay between a Lambda log line and its availability in Insights or `filter-log-events` | Poll to a deadline, report WARN (inconclusive) |
| I2 | U2 | IAM access level and resource-level scoping per action (Service Authorization pages did not render) | Use the managed-policy wildcards; ask before narrowing |
| I3 | U3 | How `get-trace-summaries` behaves under Transaction Search (indexed spans only?) | Offer `--trace-ids`; WARN, not FAIL |
| I4 | U4 | Trace id field name in `aws/spans` records | Count spans by documented attributes only |
| I5 | U5 | Git Bash argument conversion for `/aws/lambda/x` | Test in the target shell (K10) |
| I6 | C1 | Default retry mode: the retries page says standard is the CLI v2 default, the environment variables page says `legacy (default)` | Set `AWS_RETRY_MODE` explicitly |

## Medium-confidence items

14 medium-confidence items.

| ID | Research id | Item | Why medium |
|---|---|---|---|
| M1 | U11 | `CompositeAlarms[]` carries the same `ActionsEnabled` and `AlarmActions` fields | Inferred from the metric alarm shape |
| M2 | U12 | `file://q.json` relative to the current directory on Windows | Documented for `fileb://` only |
| M3 | U13 | `PendingConfirmation` shows in CLI output | Stated for the SNS console |
| M4 | U14 | `start-trace-retrieval` and `stop-query` classed as read | They start or stop a process |
| M5 | U15 | Subsegment names (`DynamoDB`) under OpenTelemetry | Example is from the X-Ray SDK for Java |
| M6 | U16 | Application JSON field names `requestId` and `tenantId` | Application-defined; Lambda's own Java key is `AWSrequestId` |
| M7 | U17 | Insights field discovery when the Lambda log format is Text | Page says first embedded JSON fragment |
| M8 | note | `list-retrieved-traces` `Spans[].Document` equals the `BatchGetTraces` document shape | Page says "see BatchGetTraces" |
| M9 | K2 | Smoke traces may not be indexed at the 1% default | Inference from the indexing docs |
| M10 | Migration 3 | Rollout timing of the new Lambda segment layout | Page says "during the coming weeks" |
| M11 | C2, C3, C4 | CLI example outputs disagree with descriptions (timestamps, `get-trace-summaries`) | Parse the documented structure |
| M12 | script | An Insights count query with no result row means zero | Repo design choice |
| M13 | script | Dashboard alarm references may be names or ARNs | Page read in part; script accepts both |
| M14 | A10 | The read action set comes from one managed policy page | Single source |

## Coverage limits

5 coverage limits.

| ID | Limit |
|---|---|
| L1 | The dashboard body page was read in part: lines 1-46, 180-270, 494-523 and 596-605 plus searches for region, SOURCE, alarms, "." and Required |
| L2 | CLI reference pages S7-S10, S17-S19, S24-S25, S31-S33, S42-S44, S46, S49-S50, S52 and S54 were read through a tool summary with verbatim quotes, not as raw pages |
| L3 | All CLI commands are representative; neither the research nor this skill's author ran them against AWS. The scripts are tested offline with a fake `aws` only |
| L4 | Unusable fetches, no facts taken: the CLI error-handling page (title only), three Service Authorization Reference pages (title only), the Knowledge Center page on query errors (HTTP 403); community search results were rejected by the source hierarchy |
| L5 | Known script limitations (scripts not changed by this fix): `check-logs.py` prints no plan line (resolved log group, window) before `start-query`, so the caller cannot match the approval `scope` and `window` from the output; exit 0 can include WARN and SKIPPED pillars; `check-traces.py`, `check-alarms.py` and `check-dashboards.py` accept `--wait-seconds` and `--retry-seconds` but ignore them; the billable reads are gated by the flags `--i-have-logs-insights-approval` (`check-logs.py`) and `--i-have-trace-retrieval-approval` (`check-traces.py`, Transaction Search path), and `trigger-alarm-test.py` by `--i-have-user-approval`, but each flag is a caller assertion: no script can verify the relayed approval line itself; `tests/run_tests.py` (including the two "without approval" tests) passes offline against the fake `aws` (137 checks, 2026-10-28); `check-traces.py` does not cap `--trace-ids` at 5 although `batch-get-traces` takes 1 to 5 |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) log ingestion-to-query delay | SKILL.md Ask First and Quick Reference; ask-first K5; pillar-logs; scripts README | I1 (irresolvable; text tag (unverified)) |
| (unverified) IAM per-action access levels | ask-first K8; command-allowlist-and-iam | I2 (irresolvable; text tag (unverified)) |
| (unverified) `get-trace-summaries` behaviour under Transaction Search | ask-first K2; pillar-traces | I3 (irresolvable; text tag (unverified)) |
| (unverified) trace id field in `aws/spans` | ask-first K2; pillar-traces | I4 (irresolvable; text tag (unverified)) |
| (unverified) Git Bash path conversion | SKILL.md Ask First; ask-first K10; cli-environment | I5 (irresolvable; text tag (unverified)) |
| (unverified) default retry mode | SKILL.md Ask First; ask-first K9; evaluation scenario 6 | I6 (irresolvable; text tag (unverified)) |
| (unverified) retention absent when never expire | pillar-logs; scripts check-logs | U1 |
| (unverified) alarm history retention | ask-first K1; pillar-alarms | U2 |
| (unverified) maximum `get-trace-summaries` window | pillar-traces | U3 |
| (unverified) X-Ray trace retention | pillar-traces | U4 |
| (unverified) `AWS/Logs` EMF failure metric names | pillar-metrics | U5 |
| (unverified) `GetMetricData` pricing | pillar-metrics | U6 |
| (unverified) `sum(ispresent())` aggregation | pillar-logs | U7 |
| (unverified) minimum `jq` version (retired: the scripts no longer use `jq`) | none | U8 |
| (unverified) `describe-alarm-history --alarm-types` | SKILL.md Ask First K11; ask-first K11; pillar-alarms; trigger-alarm-test.py | U9 |
| (medium confidence) composite alarm fields | pillar-alarms | M1 |
| (medium confidence) `file://` relative path on Windows | cli-environment; pillar-metrics | M2 |
| (medium confidence) `PendingConfirmation` in CLI output | pillar-alarms | M3 |
| (medium confidence) read class of `start-trace-retrieval` and `stop-query` | command-allowlist-and-iam; pillar-traces Decision flow | M4 |
| (medium confidence) OpenTelemetry subsegment names | pillar-traces | M5 |
| (medium confidence) application JSON field names | ask-first K6; pillar-logs | M6 |
| (medium confidence) Insights discovery with the Text format | ask-first K3; pillar-logs | M7 |
| (medium confidence) `Spans[].Document` shape | pillar-traces; scripts README | M8 |
| (medium confidence) smoke traces may not be indexed | ask-first K2; pillar-traces; evaluation scenario 2 | M9 |
| (medium confidence) segment layout rollout timing | pillar-traces | M10 |
| (medium confidence) CLI example outputs disagree | cli-environment; pillar-metrics; pillar-traces; pillar-dashboards | M11 |
| (medium confidence) count query with no row is zero | pillar-logs; scripts README | M12 |
| (medium confidence) dashboard alarm references name or ARN | pillar-dashboards | M13 |
| (medium confidence) IAM action set from one page | ask-first K8; command-allowlist-and-iam | M14 |
| (known limitation) no plan line before `start-query`; approval flags are caller assertions; `--trace-ids` over 5; exit 0 with WARN or SKIPPED; ignored wait options | SKILL.md Approval lines and exit-code note; pillar-logs; always-do A3; scripts README | L5 |

## Source Bibliography

All pages read 2026-10-28. Research ids S1 to S54 are kept. "Summary" = L2.

- CLI user guide, base `https://docs.aws.amazon.com/cli/latest/userguide/`: S1 `cli-usage-returncodes.html`, S2 `cli-usage-pagination.html`, S3 `cli-usage-filter.html`, S4 `cli-configure-retries.html`, S5 `cli-configure-envvars.html`, S6 `cli-usage-parameters-types.html`.
- CLI reference, base `https://docs.aws.amazon.com/cli/latest/reference/` (all summary): S7 `logs/describe-log-groups.html`, S8 `logs/filter-log-events.html`, S9 `logs/start-query.html`, S10 `logs/get-query-results.html`, S17 `cloudwatch/get-metric-data.html`, S18 `cloudwatch/get-metric-statistics.html`, S19 `cloudwatch/list-metrics.html`, S24 `xray/get-trace-summaries.html`, S25 `xray/batch-get-traces.html`, S31 `xray/get-trace-segment-destination.html`, S32 `xray/start-trace-retrieval.html`, S33 `xray/list-retrieved-traces.html`, S42 `cloudwatch/describe-alarms.html`, S43 `cloudwatch/set-alarm-state.html`, S44 `cloudwatch/describe-alarm-history.html`, S46 `sns/list-subscriptions-by-topic.html`, S49 `cloudwatch/get-dashboard.html`, S50 `cloudwatch/list-dashboards.html`, S52 `cloudwatch/get-metric-widget-image.html`, S54 `lambda/get-function-configuration.html`.
- CloudWatch Logs guide, base `https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/`: S11 `CWL_AnalyzeLogData-discoverable-fields.html`, S12 `cloudwatch_limits_cwl.html`, S14 `CWL_QuerySyntax-operations-functions.html`, S15 `AnalyzingLogData.html`. S16 `https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_PutLogEvents.html`.
- Lambda guide, base `https://docs.aws.amazon.com/lambda/latest/dg/`: S13 `monitoring-cloudwatchlogs-logformat.html`, S20 `monitoring-metrics-types.html`, S21 `monitoring-metrics.html`, S39 `services-xray.html`, family fact F38 `services-apigateway-errors.html`.
- CloudWatch monitoring guide, base `https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/`: S22 `CloudWatch_Embedded_Metric_Format_Specification.html`, S23 `publishingMetrics.html`, S28 `CloudWatch-Transaction-Search.html`, S29 `Enable-TransactionSearch.html`, S30 `CloudWatch-Transaction-Search-ingesting-span-log-groups.html`, S40 `CloudWatch-Transaction-Search-ingesting-spans.html`, S41 `CloudWatch-Transaction-Search-search-analyze-spans.html`, S45 `alarm-evaluation.html`.
- X-Ray: S26 `https://docs.aws.amazon.com/xray/latest/api/API_GetTraceSummaries.html`, S27 `https://docs.aws.amazon.com/xray/latest/api/API_BatchGetTraces.html`, S34 `https://docs.aws.amazon.com/xray/latest/devguide/xray-console-filters.html`, S35 `https://docs.aws.amazon.com/xray/latest/devguide/xray-api-gettingdata.html`, family fact F34 `https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html`.
- API Gateway, base `https://docs.aws.amazon.com/apigateway/latest/developerguide/`: S36 `apigateway-xray.html`, S37 `apigateway-understanding-xray-traces.html`, S38 `apigateway-enabling-xray.html`, family fact F35 `http-api-vs-rest.html`.
- SNS: S47 `https://docs.aws.amazon.com/sns/latest/api/API_ListSubscriptionsByTopic.md`, S48 `https://docs.aws.amazon.com/sns/latest/dg/SendMessageToHttp.confirm.html`.
- S51 (read in part, L1) `https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/CloudWatch-Dashboard-Body-Structure.html`; S53 `https://docs.aws.amazon.com/aws-managed-policy/latest/reference/CloudWatchReadOnlyAccess.html` (v25, edited 2026-09-22).
- Internal, not AWS facts, factory provenance (names only, not shipped with the skill): `_family_facts_v3.40.md` rows F34, F35, F38 and `_family_rules_v3.40.md` rules 7, 9 to 12; research file `research_AWS_ObservabilityValidation_2026-10.md`; approval line forms from `approval-lines.md` of the skill `coordinating-quarkus-aws-handoffs`.
