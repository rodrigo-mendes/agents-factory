# Research: Live, read-only validation of AWS observability for a Lambda workload with AWS CLI v2 (AWS docs state 2026-10-28)

> Unit **V1** -> future knowledge skill `validating-aws-observability` (package `aws-observability`) with bundled bash
> scripts `check-logs.sh`, `check-metrics.sh`, `check-traces.sh`, `check-alarms.sh`, `check-dashboards.sh`,
> `validate-observability.sh`, `lib-common.sh` (written later by the skill author from this file).
> Source item: "prove logs, metrics, traces, alarms and dashboards work, after a smoke test".
> Spec followed: `.claude/skills/researching-technical-frameworks/SKILL.md` + `blueprints/output-format-template.md`.
> Shape model (structure only, **no facts taken**): `packages/oci-observability/.apm/skills/validating-oci-observability/`
> (`SKILL.md`, `scripts/README.md`): one script per pillar, a shared `lib-common.sh`, an orchestrator that prints a
> PASS/FAIL table, and a separate, explicitly gated alarm-trigger step.

**Citation convention.** Every claim carries a source ID: `[Sn]` = official AWS page, `[Fn]` = row n of
`workspace/quarkus-aws-saas/_family_facts_v3.40.md` (orchestrator-verified AWS facts, applied as given),
`[Rn]` = rule n of `_family_rules_v3.40.md`, `[P]` = repo proposal (design choice for the scripts, **not an AWS fact**).
All AWS pages were read on **2026-10-28**. URL, read date and how much of each page was read are in the
[Source Bibliography](#source-bibliography). Tags: **(unverified)** = no fetched official page confirms it;
**(medium confidence)** = single source, inference, partly read page, or AWS pages that disagree.

**Version pin.** The "version" is the AWS CLI v2 command reference as published on 2026-10-28. Every CLI reference page
fetched shows **"AWS CLI 2.39.0 Command Reference"** [S7][S8][S17][S24][S42]. It is used together with the CloudWatch,
CloudWatch Logs, X-Ray, Lambda, API Gateway and SNS guides of the same date. AWS docs carry no semantic version, so older
snapshots, AWS CLI v1 behaviour (pager, retry defaults) and blogs are out of scope. Where CLI v1 differs, the doc says so.

**Approval relay.** Scope, the 16 units, names and the 7 packages were approved by the user on 2026-10-28
("Approve, start pilot U1"); the fan-out was approved on 2026-10-28 ("Fix pilot, then fan-out (Recommended)"). Both are
recorded in `workspace/quarkus-aws-saas/PIPELINE_STATE.md#approvals`. This file restates that relay. It is not a new approval.

**Scope.** COVERED: read-only CLI commands, required parameters, JSON paths to assert on, pagination and time-window
rules and IAM read permissions for the 5 pillars (logs, metrics, traces, alarms, dashboards), plus credentials/region,
exit codes, output/query, pager, retries and Windows notes. One mutating command, `set-alarm-state`, is covered as
**Ask-First**. NOT COVERED (names only): provisioning (`provisioning-aws-cloudwatch-v6`, `provisioning-aws-xray-v6`),
observability design (`monitoring-cloudwatch-observability`, `tracing-aws-xray`), code instrumentation
(`logging-quarkus-lambda-v3-40`, `tracing-quarkus-lambda-v3-40`, `monitoring-quarkus-lambda-v3-40`), and the smoke
invocation itself. The validator takes the smoke start time as input; deploy and smoke are D1
(`research_AWS_LambdaDeploy_2026-10.md`).

**Contents.** Metadata · Executive Summary · Architectural Guardrails (✅ A1–A10, ⚠️ K1–K7, 🚫 N1–N11) · Migration
Guide · Implementation Blueprint (lib-common, 5 checks, orchestrator, command allowlist/denylist, IAM) · Quality Control ·
Production Readiness · Reference Implementations · Source Bibliography · Research Gaps · Research Iteration Changelog ·
Completion Checklist · Agent Operation Notes · Verification Loop (self-check commands for this file).

---

## Metadata

```yaml
Full_Name: "Live read-only validation of Lambda observability (CloudWatch Logs/Logs Insights, CloudWatch metrics + EMF, X-Ray / CloudWatch Transaction Search, CloudWatch alarms + SNS, CloudWatch dashboards) with AWS CLI v2"
Target_Version: "AWS CLI v2 command reference 2.39.0 + CloudWatch / CloudWatch Logs / X-Ray / Lambda / API Gateway / SNS docs as of 2026-10-28"
Release_Date: "n/a (continuously published docs); snapshot date 2026-10-28"
Support_Status: Active (current docs)
Primary_Docs: https://docs.aws.amazon.com/cli/latest/reference/ (logs, cloudwatch, xray, sns, lambda sub-references)
Official_Repo: "n/a"
Research_Date: 2026-10-28
Domain_Complexity: Complex   # 5 pillars x 6 services, two trace back-ends (X-Ray vs Transaction Search), strict read-only boundary with one gated mutating command, log content may carry PII/secrets
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 9         # A1-A9 carry ✓✓; A10 (IAM) is single-source and downgraded to 🟡
Unverified_Count: 6           # unverified-only items still open (U6-U10, U18); IRRESOLVABLE counted separately
Irresolvable_Count: 5         # U1-U5
Research_Quality_Score: 92%   # ~(140 claims - 6 unverified - 5 irresolvable) / 140; approximation
Family_inputs: "_family_facts_v3.40.md rows F34 (X-Ray SDK maintenance), F35 (API GW REST/HTTP split), F38 (API GW -> Lambda errors); _family_rules_v3.40.md rules 7, 9, 10, 11, 12"
Deviations_from_agent_workflow: "Caller forbade sub-agents, background tasks and plan mode (scope approved by the user 2026-10-28, relayed above). All pages fetched directly. File written directly instead of via research-synthesizer. No AWS command was executed."
```

---

## Executive Summary

This document covers how a script can **prove, read-only, that a Lambda workload's observability works after a smoke
test**, using AWS CLI v2 (reference 2.39.0, docs state 2026-10-28). Each pillar has one assertion chain:
**logs** - the log group exists with retention set (`describe-log-groups` → `logGroups[].retentionInDays` [S7]); then a
Logs Insights query (`start-query` → poll `get-query-results` until `status` = `Complete` [S9][S10]) counts JSON lines
that carry the required fields with `ispresent()` [S14] (`requestId`/`tenantId` per [R7]). **Metrics** -
`get-metric-data` on `AWS/Lambda` `Invocations`/`Errors`/`Throttles` (`Sum`, period 60) and `Duration` [S17][S20], plus
the custom EMF namespace; assert `MetricDataResults[].StatusCode` = `Complete` and the value sums [S17]. **Traces** -
first read `xray get-trace-segment-destination` [S31]. With `XRay` use `get-trace-summaries` → `batch-get-traces` (max
5 IDs per call [S27]) and parse each `Segments[].Document` JSON string [S25][S35]. With `CloudWatchLogs`
(Transaction Search) `batch-get-traces` cannot find traces [S27], so use `start-trace-retrieval` →
`list-retrieved-traces` [S32][S33]. **Alarms** - `describe-alarms` (`StateValue`, `ActionsEnabled`, `AlarmActions` [S42])
plus SNS subscription confirmation [S46][S48]. **Dashboards** - `list-dashboards`/`get-dashboard`, then parse the
`DashboardBody` JSON string and cross-check each referenced metric, log group and alarm [S49][S51].

What the 2026-10-28 docs say that a skill must not get wrong: (1) **Transaction Search changes the trace API.**
`BatchGetTraces` "You cannot find traces through this API if Transaction Search is enabled" [S27]. Only an indexed
percentage of spans (1% free by default) becomes X-Ray trace summaries [S29][S40]. (2) **Lambda tracing must be
`Active`.** In `PassThrough` mode, which is the default, Lambda "does not send traces automatically" [S39]. With an HTTP
API there is no API Gateway node at all [F35]. (3) **Time units differ per API.** `filter-log-events` uses epoch
**milliseconds** [S8], `start-query` uses epoch **seconds** [S9], CloudWatch/X-Ray timestamp parameters take ISO 8601 or
epoch seconds [S6][S26]. (4) **Freshness.** Lambda sends metrics in 1-minute intervals [S21]. A new custom metric can
take up to 2 minutes for statistics and up to 15 minutes to appear in `list-metrics` [S23][S19], so `list-metrics` is not
a freshness probe. (5) **No API proves a dashboard renders.** `get-dashboard` returns only the body [S49].
`get-metric-widget-image` renders a metric graph server-side [S52], but that is not the dashboard (see K7).
(6) **`set-alarm-state` is the only mutating command.** It invokes the alarm's real actions (an `ALARM` state "sends an
SNS message"). Metric alarms return to their actual state "quickly, often within seconds"; composite alarms are not
guaranteed to return [S43]. `CloudWatchReadOnlyAccess` does not grant it [S53].

Domain complexity tier: **Complex**. The workload spans six services (CloudWatch Logs, CloudWatch, X-Ray/Transaction
Search, Lambda, API Gateway, SNS). Trace retrieval depends on account-wide state (`get-trace-segment-destination` [S31]).
The validator must hold a strict read-only boundary with one approval-gated exception. Log content may hold PII, so
`--unmask` and printing raw messages are forbidden [S8][R7]. The CLI docs also disagree on the default retry mode
([S4] vs [S5]).

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**A1 — Deterministic CLI environment for every call (region, profile, output, pager, retries, exit codes)**
> Confidence: 🟢 High | [✓✓ Triangulated | S1 (2026-10-28) + S2 (2026-10-28) + S3 (2026-10-28) + S5 (2026-10-28)]
- Why: Command-line options override env vars, and env vars override profile settings [S5]. `AWS_REGION` overrides
  `AWS_DEFAULT_REGION` and the profile `region` [S5]. `AWS_PROFILE` selects the profile and `--profile` overrides it [S5].
  By default CLI v2 sends all output through the OS pager. Setting `AWS_PAGER` to an empty string disables it, or use
  `--no-cli-pager` per command [S2]. The default pager is `less` with `FRX` flags on Linux/macOS and `more` on Windows
  [S2]. With `--output json` the CLI runs `--query` once over the fully paginated structure [S3]. Return codes [S1]: `0`
  success; `1` S3 transfer failure (S3 commands only); `2` parse failure (all commands); `130` SIGINT; `252` invalid
  syntax/unknown parameter/bad value; `253` invalid environment or configuration (e.g. missing credentials); `254` the
  service returned an error; `255` "The command failed. There were errors generated by the AWS CLI or by the AWS service".
- Retry mode: set `AWS_RETRY_MODE` explicitly because the docs disagree on the default (Contradiction C1). [S4] says
  standard mode "is the default mode for the AWS CLI version 2", with default max attempts 3 (2 retries), throttling
  errors and HTTP 500/502/503/504 retried, and exponential backoff capped at 20 s. [S5] says "legacy (default), standard,
  and adaptive". Adaptive mode is "experimental" [S4].
- Code:
  ```bash
  # Representative — adapt to your environment (AWS CLI v2 / ref 2.39.0, docs 2026-10-28)
  export AWS_PAGER=""                                  # [S2][S5] empty string disables the pager
  export AWS_RETRY_MODE="${AWS_RETRY_MODE:-standard}"  # explicit because [S4] and [S5] disagree on the default
  : "${AWS_REGION:?AWS_REGION must be set}"            # [S5] overrides AWS_DEFAULT_REGION and profile region
  aws --output json --no-cli-pager logs describe-log-groups --log-group-name-prefix "/aws/lambda/${FN}"
  rc=$?
  case "$rc" in 0) :;; 252) echo "syntax/parameter";; 253) echo "env/credentials";;
                254) echo "service error";; 255) echo "CLI/service failure";; 130) echo "interrupted";; esac
  ```
- Source: [S1][S2][S3][S4][S5] (2026-10-28)

**A2 — One smoke window, converted to the unit each API expects**
> Confidence: 🟢 High | [✓✓ Triangulated | S8 + S9 + S6 + S26 (2026-10-28)]
- Why: `filter-log-events --start-time/--end-time` are `long` epoch **milliseconds** [S8]. `start-query` takes epoch
  **seconds** and the range is inclusive [S9]. CLI `timestamp` parameters (`get-metric-data`, `get-metric-statistics`,
  `get-trace-summaries`, `describe-alarm-history`) accept ISO 8601 or Unix seconds [S6]. X-Ray `StartTime`/`EndTime` are
  "Unix time seconds" [S26]. `get-metric-data` `StartTime` is inclusive and `EndTime` exclusive. Start times under 15
  days old round down to the minute, so align start/end to the period [S17]. In CLI v2 every response DateTime is
  translated to ISO 8601 by default [S6].
- Code:
  ```bash
  # Representative — SMOKE_START_S captured by the caller just before the smoke test
  END_S=$(date -u +%s)
  START_MS=$(( SMOKE_START_S * 1000 )); END_MS=$(( END_S * 1000 ))       # filter-log-events [S8]
  aws logs start-query --start-time "$SMOKE_START_S" --end-time "$END_S" ...   # seconds [S9]
  M_START=$(( SMOKE_START_S / 60 * 60 )); M_END=$(( (END_S / 60 + 1) * 60 ))  # align to Period=60 [S17]
  ```
- Source: [S6][S8][S9][S17][S26] (2026-10-28)

**A3 — Logs: retention check + Logs Insights query with status polling and field-presence assertion**
> Confidence: 🟢 High | [✓✓ Triangulated | S7 + S9 + S10 + S14 + S11 (2026-10-28)]
- Why: The function's log group name is `LoggingConfig.LogGroup` (default `/aws/lambda/<function name>`) [S54].
  `describe-log-groups` returns `logGroups[].retentionInDays`, possible values 1…3653 [S7]. `--log-group-name-prefix` and
  `--log-group-name-pattern` are mutually exclusive [S7]. `start-query` requires `--start-time`, `--end-time` and
  `--query-string`, plus exactly one of `--log-group-name`/`--log-group-names`/`--log-group-identifiers` (each list up to
  50) [S9]. It returns `queryId` [S9]. `get-query-results` returns `status` ∈ `Scheduled|Running|Complete|Failed|
  Cancelled|Timeout|Unknown`. While `Running` only partial results are returned, so retry on `Scheduled`/`Running` [S10].
  `results` is an array of arrays of `{field,value}`, and `statistics.recordsMatched` counts matching events [S10].
  `ispresent(field)` "Returns `true` if the field exists" [S14]. Boolean `and`/`or`/`not` are supported [S14]. Queries
  time out after 60 minutes, and query results are available for 7 days [S15][S9]. Insights discovers Lambda log fields
  only "for the first embedded JSON fragment in each log event" and extracts at most 200 JSON fields [S11]. Field
  discovery works only for the Standard log class [S11].
- Required fields: `requestId` and `tenantId` on application JSON lines, and no PII [R7]. With Lambda's own JSON log
  format the Java built-in key is `"AWSrequestId"` [S13]. The `requestId`/`tenantId` names in [R7] are application fields
  emitted by the Quarkus JSON logger (out of scope: `logging-quarkus-lambda-v3-40`), so the script takes the field names
  as parameters (see U16). Lambda "doesn't double-encode any logs that are already JSON encoded" [S13].
- Code:
  ```bash
  # Representative — note: --query-string is the Insights query; --query is the CLI JMESPath filter
  QID=$(aws --output text logs start-query --log-group-name "$LG" \
        --start-time "$SMOKE_START_S" --end-time "$END_S" --query-language CWLI \
        --query-string 'filter ispresent(requestId) | stats count(*) as withReq, sum(ispresent(tenantId)) as withTenant' \
        --query queryId)
  for i in $(seq 1 "${MAX_POLLS:-30}"); do
    R=$(aws --output json logs get-query-results --query-id "$QID")
    case "$(jq -r .status <<<"$R")" in
      Complete) break ;; Scheduled|Running) sleep "${POLL_S:-2}" ;; *) echo "FAIL query $(jq -r .status <<<"$R")"; exit 1 ;;
    esac
  done
  jq -r '.results[0][] | "\(.field)=\(.value)"' <<<"$R"   # assert withReq >= N_SMOKE and withTenant == withReq
  ```
  `sum(ispresent(...))` as an aggregation is **(unverified)**. The safe equivalent is a second query with
  `filter ispresent(requestId) and not ispresent(tenantId) | stats count(*) as missingTenant`, asserting 0. It uses only
  documented functions and operators [S14].
- Source: [S7][S9][S10][S11][S13][S14][S15][S54] (2026-10-28)

**A4 — Logs: `filter-log-events` pagination is token-driven (empty pages are not the end)**
> Confidence: 🟢 High | [✓✓ Triangulated | S8 + S2 (2026-10-28)]
- Why: A page holds up to 1 MB or 10,000 events "and might only be partially full, or even empty". "If the results don't
  include a `nextToken`, then pagination is finished" [S8]. Set `--start-time` explicitly "to reduce the chances of empty
  pages" [S8]. The CLI auto-paginates by default [S2]. `--log-group-name` and `--log-group-identifier` are mutually
  exclusive and one is required [S8]. `--log-stream-names` and `--log-stream-name-prefix` cannot be combined [S8].
  `searchedLogStreams` is deprecated and "returns an empty list" [S8]. `--unmask` defaults to `false` and needs
  `logs:Unmask` [S8]. `FilterLogEvents` returns only the original, untransformed events [S8].
- Code:
  ```bash
  # Representative — let the CLI auto-paginate; cap output; never print messages (PII) [R7]
  aws --output json logs filter-log-events --log-group-name "$LG" \
      --start-time "$START_MS" --end-time "$END_MS" --filter-pattern '"tenantId"' \
      --max-items 200 --query 'length(events)'
  ```
- Source: [S2][S8] (2026-10-28)

**A5 — Metrics: `get-metric-data` on exact dimensions, `Sum` for invocation metrics, `StatusCode` check**
> Confidence: 🟢 High | [✓✓ Triangulated | S17 + S18 + S20 + S21 + S23 (2026-10-28)]
- Why: Invocation metrics are "binary indicators… View these metrics with the `Sum` statistic" [S20]. `Throttles` and
  other invocation errors "don't count as either `Invocations` or `Errors`" [S20]. The `Errors` timestamp "reflects when
  the Event Function was invoked" [S20]. Use `Duration` with `Average`/`Max` or percentiles [S20]. Lambda sends metrics
  in 1-minute intervals [S21]. Up to 500 `MetricDataQuery` per call [S17]. `Id` must start with a lowercase letter [S17].
  `Period` is a multiple of 60 for standard resolution [S17]. Retention: <60 s → 3 h (high-resolution custom only), 60 s →
  15 days, 300 s → 63 days, 3600 s → 455 days [S17][S18]. Result `StatusCode` ∈ `Complete|InternalError|PartialData|
  Forbidden`; on `PartialData` repeat with `NextToken` [S17]. `get-metric-statistics` must match the published dimension
  combination exactly. It returns ≤1,440 points per call, and the points are not in chronological order [S18]. A new
  custom metric may take up to 2 minutes for statistics and up to 15 minutes to appear in `list-metrics` [S23][S19].
- Code:
  ```bash
  # Representative — q.json in the current directory (see U12 for Windows paths)
  cat > q.json <<EOF
  [ {"Id":"inv","MetricStat":{"Metric":{"Namespace":"AWS/Lambda","MetricName":"Invocations","Dimensions":[{"Name":"FunctionName","Value":"$FN"}]},"Period":60,"Stat":"Sum"}},
    {"Id":"err","MetricStat":{"Metric":{"Namespace":"AWS/Lambda","MetricName":"Errors","Dimensions":[{"Name":"FunctionName","Value":"$FN"}]},"Period":60,"Stat":"Sum"}},
    {"Id":"thr","MetricStat":{"Metric":{"Namespace":"AWS/Lambda","MetricName":"Throttles","Dimensions":[{"Name":"FunctionName","Value":"$FN"}]},"Period":60,"Stat":"Sum"}},
    {"Id":"dur","MetricStat":{"Metric":{"Namespace":"AWS/Lambda","MetricName":"Duration","Dimensions":[{"Name":"FunctionName","Value":"$FN"}]},"Period":60,"Stat":"Maximum"}} ]
  EOF
  aws --output json cloudwatch get-metric-data --metric-data-queries file://q.json \
      --start-time "$M_START" --end-time "$M_END" \
      --query 'MetricDataResults[].{id:Id,status:StatusCode,sum:sum(Values)}'
  # assert: every status == "Complete"; inv.sum >= N_SMOKE; err.sum == EXPECTED_ERRORS; thr.sum == 0
  ```
- Source: [S17][S18][S19][S20][S21][S23] (2026-10-28)

**A6 — Traces: detect the trace back-end first, then branch (X-Ray APIs vs Transaction Search retrieval)**
> Confidence: 🟢 High | [✓✓ Triangulated | S27 + S29 + S31 + S32 + S33 (2026-10-28)]
- Why: `get-trace-segment-destination` returns `Destination` ∈ `XRay|CloudWatchLogs` and `Status` ∈ `PENDING|ACTIVE`.
  "The Transaction Search feature requires a CloudWatchLogs destination" [S31]. The doc's expected response when
  Transaction Search is active is `{"Destination":"CloudWatchLogs","Status":"ACTIVE"}`. It "can take 10 minutes for
  spans to become available" after enabling [S29]. With Transaction Search enabled, `BatchGetTraces` cannot find traces
  [S27][S25]. Retrieve instead with `start-trace-retrieval` (required `--trace-ids` up to 100, `--start-time`,
  `--end-time` in epoch seconds; returns `RetrievalToken`; retrievals time out after 60 minutes) [S32]. Then poll
  `list-retrieved-traces --retrieval-token`: while `RetrievalStatus` ≠ `COMPLETE` "the API will return an empty
  response". `--trace-format` is `XRAY|OTEL`; `Traces` holds max 5 per page and `Spans` max 100 [S33]. Spans are stored
  in the `aws/spans` log group in OpenTelemetry semantic-convention format [S28][S30].
- Code:
  ```bash
  # Representative
  read -r DEST STATUS < <(aws --output text xray get-trace-segment-destination --query '[Destination,Status]')
  if [ "$DEST" = "CloudWatchLogs" ]; then
    TOKEN=$(aws --output text xray start-trace-retrieval --trace-ids $IDS \
            --start-time "$SMOKE_START_S" --end-time "$END_S" --query RetrievalToken)
    # poll: aws --output json xray list-retrieved-traces --retrieval-token "$TOKEN" --trace-format XRAY
    #       until .RetrievalStatus == "COMPLETE"; FAIL on FAILED|CANCELLED|TIMEOUT
  else
    : # X-Ray path, see A7
  fi
  ```
  Where `$IDS` comes from on the Transaction Search path is Ask-First K2.
- Source: [S25][S27][S28][S29][S30][S31][S32][S33] (2026-10-28)

**A7 — Traces (X-Ray path): summaries → full traces → assert segment origins; Lambda must be `Active`**
> Confidence: 🟢 High | [✓✓ Triangulated | S24 + S26 + S27 + S35 + S37 + S39 + S54 (2026-10-28)]
- Why: Precondition: `get-function-configuration` → `TracingConfig.Mode` = `Active` [S54]. In `PassThrough` (the
  default) Lambda "does not send traces automatically", even when the header asks for sampling [S39]. Lambda records two
  segments per trace, origins `AWS::Lambda` (service) and `AWS::Lambda::Function` (function), both named after the
  function [S39]. The function segment's subsegment layout is changing (old style: `Initialization`/`Invocation`/
  `Overhead`; new style: no `Invocation`, customer subsegments attached directly to the function segment) [S39], so never
  assert on `Invocation`. A REST API stage segment has `origin` `AWS::ApiGateway::Stage`, `name` `<api-name>/<stage>`
  (example `testxray/dev`), and a `Lambda` subsegment with `namespace` `aws` [S37]. Stage tracing shows as
  `tracingEnabled` on the stage [S38]. An HTTP API has no X-Ray tracing, so the trace starts at the Lambda segment [F35].
  `get-trace-summaries` requires `--start-time`/`--end-time`. `--time-range-type` ∈ `TraceId|Event|Service`, and the
  default search uses TraceId time [S24][S35]. The output key is `TraceSummaries[]` (`Id`, `HasFault`, `HasError`,
  `HasThrottle`, `Http.HttpStatus`, `ServiceIds[]`, `IsPartial`) [S24][S26]. `batch-get-traces` takes 1–5 trace IDs
  [S27]. `Segments[].Document` is a string [S25] holding processed segment JSON [S35]. A DynamoDB call appears as a
  subsegment `name` `DynamoDB`, `namespace` `aws`, plus an inferred segment with `origin` `AWS::DynamoDB::Table` [S35].
  That example comes from the X-Ray SDK for Java, so names under OpenTelemetry instrumentation are (medium confidence),
  U15. X-Ray SDKs are in maintenance mode since 2026-02-25 [F34]. Filter expressions: `service("name")`,
  `service(id(name: "n", type: "AWS::Lambda::Function"))`, keywords `ok|error|fault|throttle`, `http.status`,
  `annotation[key]` [S34].
- Code:
  ```bash
  # Representative — jq parses the Document string with fromjson
  IDS=$(aws --output json xray get-trace-summaries --start-time "$SMOKE_START_S" --end-time "$END_S" \
          --filter-expression "service(id(name: \"$FN\", type: \"AWS::Lambda::Function\"))" \
          --query 'TraceSummaries[].Id' | jq -r '.[:5][]')
  aws --output json xray batch-get-traces --trace-ids $IDS > traces.json
  jq -r '[.Traces[].Segments[].Document | fromjson | .origin] | unique[]' traces.json
  # assert REST API: contains AWS::ApiGateway::Stage, AWS::Lambda, AWS::Lambda::Function
  # assert HTTP API: contains AWS::Lambda, AWS::Lambda::Function and NOT AWS::ApiGateway::Stage [F35]
  jq '[.Traces[].Segments[].Document | fromjson | .. | objects | select(.namespace? == "aws" and .name? == "DynamoDB")] | length' traces.json
  ```
- Source: [S24][S25][S26][S27][S34][S35][S37][S38][S39][S54] + [F34][F35] (2026-10-28)

**A8 — Alarms: describe with explicit alarm types; assert actions wired and SNS subscriptions confirmed**
> Confidence: 🟢 High | [✓✓ Triangulated | S42 + S45 + S46 + S48 (2026-10-28)]
- Why: If `--alarm-types` is omitted "only metric alarms are returned, even if composite alarms or log alarms exist"
  [S42]. Values are `CompositeAlarm|MetricAlarm|LogAlarm` [S42]. `--alarm-name-prefix` cannot be combined with
  `--alarm-names` (max 100) [S42]. Fields to assert per `MetricAlarms[]`: `StateValue` ∈ `OK|ALARM|INSUFFICIENT_DATA`,
  `ActionsEnabled`, `AlarmActions[]`/`OKActions[]`/`InsufficientDataActions[]` (ARNs), `StateReason`,
  `StateUpdatedTimestamp`, `TreatMissingData` ∈ `breaching|notBreaching|ignore|missing`, `EvaluationState` [S42].
  `INSUFFICIENT_DATA` = "The alarm has just started, the metric is not available, or not enough data" [S45]. Alarms with
  a period ≥1 minute are evaluated every minute [S45]. For SNS actions, `list-subscriptions-by-topic --topic-arn` returns
  `Subscriptions[].SubscriptionArn/Protocol/Endpoint` (100 per call, paginated) [S46][S47]. An unconfirmed subscription
  "will show as `PendingConfirmation`" (stated for the console [S48]; same value in CLI output is (medium confidence),
  U13).
- Code:
  ```bash
  # Representative
  aws --output json cloudwatch describe-alarms --alarm-name-prefix "$ALARM_PREFIX" \
      --alarm-types MetricAlarm CompositeAlarm \
      --query 'MetricAlarms[].{n:AlarmName,s:StateValue,e:ActionsEnabled,a:AlarmActions}'
  aws --output json sns list-subscriptions-by-topic --topic-arn "$TOPIC_ARN" \
      --query 'Subscriptions[].{arn:SubscriptionArn,p:Protocol}'
  # FAIL if ActionsEnabled==false or AlarmActions empty; FAIL if any arn == "PendingConfirmation"
  ```
- Source: [S42][S45][S46][S47][S48] (2026-10-28)

**A9 — Dashboards: list → get → parse `DashboardBody` → cross-check every reference; report render as unverifiable**
> Confidence: 🟢 High | [✓✓ Triangulated | S49 + S50 + S51 (2026-10-28)]
- Why: `list-dashboards` (`--dashboard-name-prefix`) is paginated on `DashboardEntries[]` (`DashboardName`,
  `DashboardArn`, `LastModified`, `Size`), up to 1000 per page [S50]. `get-dashboard --dashboard-name` returns
  `DashboardArn`, `DashboardName` and `DashboardBody`, a **JSON string** [S49]. The body must contain a `widgets` array of
  0–500 widgets [S51]. Widget `type` ∈ `metric|text|log|alarm|explorer|chart` [S51]. A metric widget has
  `properties.metrics` rows `[Namespace, MetricName, DimName, DimValue, …, {options}]`. In rows after the first, `"."`
  repeats the previous row's value [S51]. A metric widget requires `properties.region` [S51]. Alarms are referenced in
  `properties.annotations.alarms` (metric widget) or `properties.alarms` (alarm widget) [S51]. A log widget requires
  `region` and `query`, and the query starts with `SOURCE '<log-group>'` entries separated by `|` [S51]. None of the
  fetched pages documents an API that reports whether a dashboard renders; see K7 for the partial
  `get-metric-widget-image` check [S52].
- Code:
  ```bash
  # Representative
  BODY=$(aws --output json cloudwatch get-dashboard --dashboard-name "$DASH" --query DashboardBody | jq -r .)
  jq -r '.widgets[] | select(.type=="log") | .properties.query' <<<"$BODY" | grep -o "SOURCE '[^']*'"
  jq -r '.widgets[] | (.properties.alarms // .properties.annotations.alarms // [])[]' <<<"$BODY"
  jq -c '.widgets[] | select(.type=="metric") | {region: .properties.region, rows: .properties.metrics}' <<<"$BODY"
  # resolve "." against the previous row, then: describe-log-groups / describe-alarms --alarm-names /
  # get-metric-data (A5) for each reference; WARN "render not provable via API"
  ```
- Source: [S49][S50][S51][S52] (2026-10-28)

**A10 — IAM: least-privilege read set; `SetAlarmState` granted separately and only for the approved test**
> Confidence: 🟡 Medium | single source for the action set (managed policy S53); per-action access levels (unverified), U2
- Why: AWS managed policy `CloudWatchReadOnlyAccess` (v25, edited 2026-09-22) covers `cloudwatch:Describe*`/`Get*`/
  `List*`/`BatchGet*`, `logs:Get*`/`List*`/`Describe*`/`StartQuery`/`StopQuery`/`FilterLogEvents`, `xray:BatchGet*`/
  `Get*`/`List*`/`StartTraceRetrieval`/`CancelTraceRetrieval` and `sns:Get*`/`List*` [S53]. It does **not** include
  `cloudwatch:SetAlarmState`, `lambda:GetFunctionConfiguration` or `apigateway:GET` [S53]. Transaction Search docs advise
  `CloudWatchReadOnlyAccess` to use Transaction Search [S29]. `--unmask` needs `logs:Unmask` [S8] and is forbidden (N8).
- Code: see [IAM read set](#iam-read-set-least-privilege) in the Implementation Blueprint.
- Source: [S8][S29][S53] (2026-10-28)

### ⚠️ Conditional Patterns

**K1 — `set-alarm-state` notification test (the ONLY mutating command; requires explicit user approval)**
> Confidence: 🟢 High (facts) | decision = user
- Options: A) skip, alarms validated read-only (A8); B) run `set-alarm-state --state-value ALARM` on **one named alarm**
  after approval, then verify `describe-alarm-history --history-item-type Action`.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A skip | Zero side effects | Does not prove the notification path end to end | Shared/prod accounts, on-call topics |
  | B set-alarm-state | Proves alarm → action (SNS message sent) [S43] | Sends a real notification to real subscribers [S43]; needs `cloudwatch:SetAlarmState`, which `CloudWatchReadOnlyAccess` lacks [S53] | Dev/test accounts with an approved alarm and audience |

- Facts: "Temporarily sets the state of an alarm for testing purposes. When the updated state differs from the previous
  value, the action configured for the appropriate state is invoked… changing the alarm state to `ALARM` sends an SNS
  message" [S43]. "Metric alarms returns to their actual state quickly, often within seconds… typically only visible in
  the alarm's History tab… or through DescribeAlarmHistory" [S43]. Composite alarm: "not guaranteed to return to its
  actual state. It returns to its actual state only once any of its children alarms change state" [S43]. Auto Scaling
  actions need `--state-reason-data` [S43]. Required parameters: `--alarm-name`, `--state-value`, `--state-reason` (max
  1023 chars); output is "None" [S43]. History: `describe-alarm-history --alarm-name --history-item-type
  StateUpdate|Action|ConfigurationUpdate|…`; `HistoryData` is a JSON string [S44].
- Agent: "Ask the user to approve, per run, the exact alarm name and that its subscribers will receive a test
  notification. Never on composite alarms without stating that the state may not revert [S43]."
- Source: [S43][S44][S45][S53] (2026-10-28)

**K2 — Trace IDs and retrieval path when Transaction Search is ACTIVE**
> Confidence: 🟡 Medium
- Options: A) `get-trace-summaries` for IDs (only indexed spans become trace summaries; 1% free by default [S29][S40])
  then `start-trace-retrieval`/`list-retrieved-traces` [S32][S33]; B) Logs Insights over `aws/spans`. The documented
  attribute examples are `durationNano`, `attributes.db.statement`, `attributes.http.response.status_code` and
  `attributes.aws.local.service` [S41]; the trace-ID field name is (unverified), U4. C) Ask the user to raise the indexing
  percentage. That is a mutating `update-indexing-rule` call [S29], forbidden for the validator; route to
  `provisioning-aws-xray-v6`.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A summaries + retrieval | Same assertions as A7 (`--trace-format XRAY`) | Smoke traces may not be indexed at 1% (medium confidence) | Indexing % raised or many smoke calls |
  | B Insights on `aws/spans` | Sees all ingested spans [S28] | Field names partly unverified (U4); charged per GB scanned [S15] | Low-volume dev accounts |

- Agent: "Ask user which path; report `INCONCLUSIVE` (not FAIL) when A returns zero summaries at the default 1% index rate."
- Source: [S15][S28][S29][S32][S33][S40][S41] (2026-10-28)

**K3 — Logs evidence: Logs Insights vs `filter-log-events`**
> Confidence: 🟡 Medium
- Options: A) Insights (`start-query`) for counts and field presence [S9][S14]; B) `filter-log-events` with a filter
  pattern [S8].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A Insights | Field-level assertions with `ispresent` [S14]; JSON discovery [S11] | Charged per GB of uncompressed data scanned [S15]; 100 concurrent queries shared with dashboards and scheduled queries [S9][S15] | Default for field assertions |
  | B FilterLogEvents | No query lifecycle | Text-pattern only; 5–25 TPS by Region [S12]; pages may be empty [S8] | Insights unavailable / Infrequent Access class (no field discovery [S11]) |

- Agent: "Default A; ask before scanning large windows."
- Source: [S8][S9][S11][S12][S14][S15] (2026-10-28)

**K4 — JSON handling: CLI `--query` (JMESPath) vs `jq`**
> Confidence: 🟢 High (facts) | 🟡 tool choice
- Options: A) `--query` only (built into the CLI [S3]); B) `jq` for parsing `Document`/`DashboardBody` strings.
- Tradeoffs: `--query` works on the final structure only with `--output json|yaml|yaml-stream` [S3]. It cannot parse a
  JSON-in-string field such as `Segments[].Document` [S25] or `DashboardBody` [S49], so those need `jq` (`fromjson`).
  Installing `jq` is an extra dependency; the CLI guide only links it as a tool [S3].
- Agent: "Ask whether `jq` may be a hard prerequisite; if not, limit to A and mark trace/dashboard deep checks SKIPPED."
- Source: [S3][S25][S49] (2026-10-28)

**K5 — Wait budget after the smoke test**
> Confidence: 🟡 Medium
- Options: fixed wait vs poll-until-deadline. Known delays: Lambda metrics sent in 1-minute intervals [S21]; new custom
  metric statistics up to 2 min, `list-metrics` up to 15 min [S23][S19]; spans after enabling Transaction Search up to
  10 min [S29]; logs ingestion-to-query delay **not documented on a fetched page** (U1, IRRESOLVABLE).
- Agent: "Ask user for the deadline (e.g. 5–15 min) and the poll interval; report `INCONCLUSIVE` at deadline, not FAIL."
- Source: [S19][S21][S23][S29] (2026-10-28)

**K6 — Custom EMF namespace, metric names and dimension sets**
> Confidence: 🟢 High (facts) | inputs = user
- Facts: An EMF document must be a valid JSON object with `_aws.CloudWatchMetrics[]` (`Namespace`, `Dimensions` =
  array of DimensionSets, `Metrics[]` `Name`/`Unit`/`StorageResolution`) and `_aws.Timestamp` (ms; no more than 14 days
  past, 2 hours future) [S22]. A DimensionSet has ≤30 keys [S22]. A log event has ≤100 MetricDefinitions in total [S22].
  "Every DimensionSet used creates a new metric". High-cardinality dimensions such as `requestId` create a metric per
  value [S22]. Bounded dimensions only, per [R7]. `StorageResolution` default 60 [S22]. EMF delivery is "at least one
  time" [S22]. Retrieval must use the exact dimension set that was published [S18].
- Agent: "Ask the user for namespace, metric names and the exact DimensionSet; never guess; flag `tenantId` as a
  dimension unless an ADR exists [R7]."
- Source: [S18][S22] + [R7] (2026-10-28)

**K7 — Partial render proof with `get-metric-widget-image`**
> Confidence: 🟡 Medium
- Facts: `get-metric-widget-image --metric-widget '<json>' --output-format png` returns `MetricWidgetImage`
  (base64-encoded). Limits: 100 metrics and a 100 KB payload per graph, 20 TPS; not available in GovCloud (US) [S52].
- Tradeoffs: proves CloudWatch can graph the metric rows taken from a dashboard metric widget. It does not prove that the
  console dashboard (log/alarm/text widgets, variables, layout) renders [S51][S52]. It writes a PNG locally.
- Agent: "Ask whether to render per-widget PNGs for human review; never report it as 'dashboard renders'."
- Source: [S51][S52] (2026-10-28)

### 🚫 Forbidden Patterns

**N1 — Running any mutating AWS command other than the approved `set-alarm-state` (K1)**
> Severity: Critical
> Confidence: 🟢 High
- Why: The validator's contract is read-only. Mutations change the system under test and need provisioning-skill
  ownership. The denylist is in [Command allowlist / denylist](#command-allowlist--denylist).
- Impact: Silent configuration drift (e.g. retention or indexing changed by a "validator"), real cost, or real alerts.
- ❌ Wrong:
  ```bash
  aws logs put-retention-policy --log-group-name "$LG" --retention-in-days 30   # "fixing" a FAIL
  aws xray update-indexing-rule --name Default --rule '{"Probabilistic":{"DesiredSamplingPercentage":100}}'
  ```
- ✅ Correct:
  ```bash
  echo "FAIL logs.retention: retentionInDays missing on $LG -> route to provisioning-aws-cloudwatch-v6"
  exit 1
  ```
- Source: [S7][S29] (2026-10-28)

**N2 — `--output text` combined with `--query` on a paginated command**
> Severity: High
> Confidence: 🟢 High
- Why: With `--output text` "the output is paginated *before* the `--query` filter is applied, and the AWS CLI runs the
  query once on *each page*" [S3]. Paginated commands list which keys the query must target in that mode [S7][S8][S42].
- Impact: Duplicated or extra elements, e.g. `[0]` returns the first item of every page.
- ❌ Wrong:
  ```bash
  aws logs describe-log-groups --output text --query 'logGroups[0].logGroupName'
  ```
- ✅ Correct:
  ```bash
  aws logs describe-log-groups --output json --query 'logGroups[0].logGroupName'
  ```
- Source: [S3][S7] (2026-10-28)

**N3 — Treating an empty `filter-log-events` page as "no logs"**
> Severity: High
> Confidence: 🟢 High
- Why: Pages can be partially full or empty while a `nextToken` still exists [S8].
- Impact: False FAIL on the logs pillar.
- ❌ Wrong:
  ```bash
  aws logs filter-log-events --log-group-name "$LG" --no-paginate --query 'length(events)'   # 0 => "FAIL"
  ```
- ✅ Correct:
  ```bash
  aws --output json logs filter-log-events --log-group-name "$LG" --start-time "$START_MS" --end-time "$END_MS" \
      --query 'length(events)'          # CLI follows nextToken by default [S2]
  ```
- Source: [S2][S8] (2026-10-28)

**N4 — Calling `batch-get-traces` without checking the trace destination**
> Severity: High
> Confidence: 🟢 High
- Why: "You cannot find traces through this API if Transaction Search is enabled since trace is not indexed in X-Ray" [S27].
- Impact: False FAIL on the traces pillar in every Transaction Search account.
- ❌ Wrong:
  ```bash
  aws xray batch-get-traces --trace-ids "$ID"     # empty Traces => "tracing broken"
  ```
- ✅ Correct:
  ```bash
  aws --output text xray get-trace-segment-destination --query Destination   # CloudWatchLogs => start-trace-retrieval [S32]
  ```
- Source: [S27][S31][S32] (2026-10-28)

**N5 — Requiring an API Gateway trace node for an HTTP API**
> Severity: Medium
> Confidence: 🟢 High
- Why: HTTP APIs do not support X-Ray tracing. With `quarkus-amazon-lambda-http` the trace starts at the Lambda
  segment [F35]. API Gateway tracing docs cover REST APIs (`AWS::ApiGateway::Stage`) [S36][S37].
- Impact: Permanent false FAIL for HTTP API workloads.
- ❌ Wrong:
  ```bash
  jq -e 'index("AWS::ApiGateway::Stage")' origins.json || echo FAIL   # applied to an HTTP API
  ```
- ✅ Correct:
  ```bash
  case "$API_TYPE" in REST) need="AWS::ApiGateway::Stage AWS::Lambda AWS::Lambda::Function";;
                      HTTP) need="AWS::Lambda AWS::Lambda::Function";; esac
  ```
- Source: [F35][S36][S37][S39] (2026-10-28)

**N6 — Using `list-metrics` as proof that fresh data arrived**
> Severity: Medium
> Confidence: 🟢 High
- Why: New metrics take "up to 15 minutes" to appear [S19][S23]. `--recently-active PT3H` is "an approximation" [S19].
  Metrics without data in two weeks are not listed [S19].
- Impact: False FAIL right after the smoke test, or false PASS from old data.
- ❌ Wrong:
  ```bash
  aws cloudwatch list-metrics --namespace "$NS" --recently-active PT3H   # non-empty => "metrics OK"
  ```
- ✅ Correct:
  ```bash
  aws --output json cloudwatch get-metric-data --metric-data-queries file://q.json \
      --start-time "$M_START" --end-time "$M_END" --query 'MetricDataResults[].[StatusCode,sum(Values)]'
  ```
- Source: [S17][S19][S23] (2026-10-28)

**N7 — Mixing epoch units between APIs**
> Severity: High
> Confidence: 🟢 High
- Why: `filter-log-events` = ms [S8]; `start-query` = s [S9]; X-Ray = s [S26].
- Impact: The window lands in 1970 or ~50,000 years ahead, the query returns nothing, and the pillar falsely FAILs.
- ❌ Wrong:
  ```bash
  aws logs start-query --start-time "$START_MS" --end-time "$END_MS" ...
  ```
- ✅ Correct:
  ```bash
  aws logs start-query --start-time "$SMOKE_START_S" --end-time "$END_S" ...
  ```
- Source: [S8][S9][S26] (2026-10-28)

**N8 — Printing raw log messages or unmasking sensitive data in validator output**
> Severity: Critical
> Confidence: 🟢 High
- Why: Logs must carry no PII [R7]. `--unmask` shows masked sensitive data and needs `logs:Unmask` [S8]. The validator
  only needs counts and field presence [S10][S14].
- Impact: PII/secrets copied into CI logs or chat transcripts.
- ❌ Wrong:
  ```bash
  aws logs filter-log-events --log-group-name "$LG" --unmask --query 'events[].message' --output text
  ```
- ✅ Correct:
  ```bash
  aws --output json logs get-query-results --query-id "$QID" --query 'statistics.recordsMatched'
  ```
- Source: [S8][S10][S14] + [R7] (2026-10-28)

**N9 — Reporting "dashboard renders" from `get-dashboard`/`list-dashboards`**
> Severity: Medium
> Confidence: 🟢 High
- Why: `get-dashboard` returns only `DashboardArn`, `DashboardBody`, `DashboardName` [S49]. `list-dashboards` returns
  only name/ARN/`LastModified`/`Size` [S50].
- Impact: False assurance of on-call dashboards.
- ❌ Wrong:
  ```bash
  aws cloudwatch get-dashboard --dashboard-name "$DASH" >/dev/null && echo "PASS dashboard renders"
  ```
- ✅ Correct:
  ```bash
  echo "PASS dashboard.structure (widgets resolve to existing metrics/log groups/alarms); render: NOT PROVABLE VIA API"
  ```
- Source: [S49][S50][S51] (2026-10-28)

**N10 — Leaving the interactive pager or the region implicit in scripts**
> Severity: High
> Confidence: 🟢 High
- Why: CLI v2 pipes output through the OS default pager (`less`, `more` on Windows) [S2]. A Region must be set
  explicitly or by default [S5].
- Impact: Hung CI jobs waiting on the pager; calls to the wrong Region (empty results read as FAIL).
- ❌ Wrong:
  ```bash
  aws cloudwatch describe-alarms
  ```
- ✅ Correct:
  ```bash
  AWS_PAGER="" aws --region "$AWS_REGION" --output json cloudwatch describe-alarms --alarm-types MetricAlarm CompositeAlarm
  ```
- Source: [S2][S5][S42] (2026-10-28)

**N11 — Omitting `--alarm-types` when composite alarms are part of the design**
> Severity: Medium
> Confidence: 🟢 High
- Why: The default returns only metric alarms [S42].
- Impact: Composite alarms are never checked, so a false PASS.
- ❌ Wrong:
  ```bash
  aws --output json cloudwatch describe-alarms --alarm-name-prefix "$P"
  ```
- ✅ Correct:
  ```bash
  aws --output json cloudwatch describe-alarms --alarm-name-prefix "$P" --alarm-types MetricAlarm CompositeAlarm
  ```
- Source: [S42] (2026-10-28)

---

## Migration Guide

> Confidence: 🟢 High | Sources: [S27][S29][S39][S2][S4][S8] (2026-10-28) + [F34]

**Breaking Changes** (relative to older X-Ray / CLI v1-era scripts):
1. **Transaction Search** (account-wide switch [S29]): spans go to `aws/spans` [S28]. `BatchGetTraces` cannot find
   traces [S27]. Retrieval moves to `StartTraceRetrieval`/`ListRetrievedTraces`/`GetRetrievedTracesGraph` [S32][S33].
   Only an indexed share (1% by default) yields trace summaries [S29][S40].
2. **Lambda `PassThrough` no longer sends traces automatically** even when API Gateway adds a sampled header. "If your
   solution depends on this passive tracing behavior, switch to `Active` tracing" [S39].
3. **Lambda segment layout change**: the new style has no `Invocation` subsegment and attaches customer subsegments to
   `AWS::Lambda::Function`, with annotations `aws.responseLatency`, `aws.responseDuration`, `aws.runtimeOverhead`,
   `aws.extensionOverhead` [S39]. The rollout runs "during the coming weeks" except China/GovCloud [S39], so both
   layouts may coexist (medium confidence on timing).
4. **X-Ray SDKs and Daemon are in maintenance mode since 2026-02-25.** OpenTelemetry is recommended [F34]; trace
   validation must therefore accept OpenTelemetry-produced traces (U15).
5. **CLI v2 vs v1**: v2 adds the client-side pager [S2], uses standard retry mode by default per [S4] (v1: legacy) and
   ISO 8601 response timestamps [S6].
6. **`filter-log-events --interleaved`/`searchedLogStreams`**: `searchedLogStreams` "is no longer supported… returns an
   empty list" (since 2020-05-15) [S8].
7. **Logs Insights languages**: `--query-language` ∈ `CWLI|SQL|PPL`. The 100,000-result pagination applies to Logs
   Insights QL only [S9][S10]. The doc states no default, so pass `CWLI` explicitly [S9].

**Upgrade Steps** (for an existing validator):
1. Add the destination probe (`get-trace-segment-destination`) before any trace call (A6).
2. Add the `TracingConfig.Mode == Active` precondition (A7).
3. Drop assertions on `Invocation`/`Overhead` subsegments (A7).
4. Export `AWS_PAGER=""` and `AWS_RETRY_MODE` explicitly (A1).
5. Pass `--query-language CWLI` (A3).

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| AWS CLI | v2 (ref 2.39.0 read) | — | v1 lacks the pager and differs on retry defaults [S2][S4] |
| `jq` | (unverified) | — | Needed for `fromjson` on `Document`/`DashboardBody` (K4); version not from AWS docs |
| API Gateway | REST API for X-Ray node | — | HTTP API: no X-Ray [F35] |
| Lambda tracing | `Active` | — | `PassThrough` sends nothing [S39] |
| Log class | Standard | — | Field discovery only for Standard [S11] |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | official CLI reference + official guides] for the commands; the script
> skeleton, file names and exit-code scheme are **[P] repo proposals** that follow the OCI validator's shape.

**Lifecycle** (inputs → 5 checks → table):
```bash
#!/usr/bin/env bash
# lib-common.sh — Representative — adapt to your environment (AWS CLI v2 ref 2.39.0; docs 2026-10-28)
set -uo pipefail
export AWS_PAGER=""                                   # [S2][S5]
export AWS_RETRY_MODE="${AWS_RETRY_MODE:-standard}"   # explicit; [S4] vs [S5] disagree on the default (C1)
: "${AWS_REGION:?set AWS_REGION}"                     # [S5]; AWS_PROFILE optional [S5]
: "${FN:?function name}" "${SMOKE_START_S:?epoch seconds before the smoke test}"
API_TYPE="${API_TYPE:-REST}"                          # REST|HTTP|NONE [F35]
REQ_FIELDS="${REQ_FIELDS:-requestId tenantId}"        # [R7]; names are app-defined (U16)
END_S=$(date -u +%s)

awsj() { aws --output json --no-cli-pager "$@"; }     # always JSON for --query [S3]
rc_text() {                                           # [S1]
  case "$1" in 0) echo ok;; 1) echo "s3 transfer";; 2) echo "parse";; 130) echo SIGINT;;
               252) echo "invalid syntax/parameter";; 253) echo "invalid env/credentials";;
               254) echo "service error";; 255) echo "CLI/service failure";; *) echo "rc=$1";; esac; }
# [P] script exit scheme: 0 PASS · 1 FAIL · 2 INCONCLUSIVE (deadline/indexing) · 3 PRECONDITION (rc 253, missing jq, tracing off)
result() { printf '%-12s %-13s %s\n' "$1" "$2" "$3"; }   # pillar  PASS|FAIL|INCONCLUSIVE|SKIPPED  detail
```

**check-logs.sh** (A3, A4):
```bash
# Representative
LG=$(aws --output text lambda get-function-configuration --function-name "$FN" --query 'LoggingConfig.LogGroup')  # [S54]
RET=$(awsj logs describe-log-groups --log-group-name-prefix "$LG" \
        --query "logGroups[?logGroupName=='$LG'] | [0].retentionInDays")                           # [S7]
[ "$RET" = "null" ] && result logs.retention FAIL "no retentionInDays on $LG" || result logs.retention PASS "$RET days"
# Insights: count lines with requestId, and lines missing tenantId (documented functions only [S14])
q_count() { aws --output text logs start-query --log-group-name "$LG" --start-time "$SMOKE_START_S" --end-time "$END_S" \
              --query-language CWLI --query-string "$1" --query queryId; }                            # [S9]
poll()    { for i in $(seq 1 "${MAX_POLLS:-30}"); do R=$(awsj logs get-query-results --query-id "$1")
              case "$(jq -r .status <<<"$R")" in Complete) echo "$R"; return 0;;
                Scheduled|Running) sleep "${POLL_S:-2}";; *) return 1;; esac; done; return 2; }       # [S10]
R1=$(poll "$(q_count 'filter ispresent(requestId) | stats count(*) as n')")
R2=$(poll "$(q_count 'filter ispresent(requestId) and not ispresent(tenantId) | stats count(*) as n')")
# PASS if n(R1) >= N_SMOKE and n(R2) == 0; never print @message [R7]
```

**check-metrics.sh** (A5, K6): build `q.json` (A5 code), then for the custom namespace add one `MetricStat` per
`(MetricName, exact DimensionSet)` from user input [S18][S22]. FAIL on any `StatusCode` ≠ `Complete` after following
`NextToken` [S17]. INCONCLUSIVE if `inv` sum is 0 before the K5 deadline.

**check-traces.sh** (A6, A7, K2):
```bash
# Representative
MODE=$(aws --output text lambda get-function-configuration --function-name "$FN" --query 'TracingConfig.Mode')   # [S54]
[ "$MODE" = "Active" ] || { result traces PRECONDITION "TracingConfig.Mode=$MODE (PassThrough sends nothing [S39])"; exit 3; }
DEST=$(aws --output text xray get-trace-segment-destination --query Destination)                              # [S31]
IDS=$(awsj xray get-trace-summaries --start-time "$SMOKE_START_S" --end-time "$END_S" \
        --filter-expression "service(id(name: \"$FN\", type: \"AWS::Lambda::Function\"))" \
        --query 'TraceSummaries[].Id' | jq -r '.[:5][]')                                                       # [S24][S34]
[ -z "$IDS" ] && { result traces INCONCLUSIVE "no trace summaries (Transaction Search index % ?)"; exit 2; }
if [ "$DEST" = "XRay" ]; then awsj xray batch-get-traces --trace-ids $IDS > traces.json                       # [S27]
  DOCS='.Traces[].Segments[].Document'
else TOKEN=$(aws --output text xray start-trace-retrieval --trace-ids $IDS \
              --start-time "$SMOKE_START_S" --end-time "$END_S" --query RetrievalToken)                       # [S32]
  for i in $(seq 1 "${MAX_POLLS:-30}"); do awsj xray list-retrieved-traces --retrieval-token "$TOKEN" --trace-format XRAY > traces.json
    case "$(jq -r .RetrievalStatus traces.json)" in COMPLETE) break;; SCHEDULED|RUNNING) sleep "${POLL_S:-5}";; *) exit 1;; esac
  done                                                                                                         # [S33]
  DOCS='.Traces[].Spans[].Document'   # XRAY format documents (medium confidence on identical shape to BatchGetTraces)
fi
jq -r "[$DOCS | fromjson | .origin] | unique[]" traces.json   # compare with API_TYPE expectations (A7, N5)
```

**check-alarms.sh** (A8): `describe-alarms --alarm-name-prefix … --alarm-types MetricAlarm CompositeAlarm` → per
alarm: `ActionsEnabled==true`, `AlarmActions` non-empty; for each `arn:aws:sns:` action run `list-subscriptions-by-topic`
and FAIL on `PendingConfirmation`. The optional `--trigger <alarm-name>` path runs only with recorded user approval (K1),
then `describe-alarm-history --history-item-type Action --start-date <T0>` [S43][S44].

**check-dashboards.sh** (A9, K7): `list-dashboards --dashboard-name-prefix` → for each, `get-dashboard` → `jq` parse →
resolve `"."` rows → check each metric with `get-metric-data` over the smoke window (data present), each `SOURCE` log
group with `describe-log-groups`, each alarm with `describe-alarms --alarm-names` (≤100 per call) [S42][S51]. Always
print `render: NOT PROVABLE VIA API` (N9).

**validate-observability.sh** [P]: source `lib-common.sh`, run the 5 checks with a shared deadline (K5), print a
`pillar | status | detail` table, exit with the worst status.

### Command allowlist / denylist

| Class | Commands | Source |
|---|---|---|
| ✅ Read (allowed) | `logs describe-log-groups`, `logs filter-log-events`, `logs start-query`, `logs get-query-results`, `logs stop-query` (own query only); `cloudwatch get-metric-data`, `get-metric-statistics`, `list-metrics`, `describe-alarms`, `describe-alarm-history`, `list-dashboards`, `get-dashboard`, `get-metric-widget-image` (K7); `xray get-trace-segment-destination`, `get-trace-summaries`, `batch-get-traces`, `start-trace-retrieval`, `list-retrieved-traces`; `sns list-subscriptions-by-topic`; `lambda get-function-configuration`; `apigateway get-stage` (field `tracingEnabled`) | [S7]–[S10], [S17]–[S19], [S24]–[S25], [S31]–[S33], [S38], [S42]–[S44], [S46], [S49]–[S50], [S52], [S54]; `start-trace-retrieval`/`stop-query` are in `CloudWatchReadOnlyAccess` [S53] but "initiate"/"stop" a process (medium confidence on "read" class, U14) |
| ⚠️ Ask-First (only mutating) | `cloudwatch set-alarm-state` | [S43] (K1) |
| 🚫 Forbidden | `logs put-retention-policy`, `delete-retention-policy`, `create-log-group`, `delete-log-group`, `put-resource-policy`, `put-metric-filter`, `put-subscription-filter`, `associate-kms-key`; `cloudwatch put-metric-alarm`, `put-composite-alarm`, `delete-alarms`, `enable-alarm-actions`, `disable-alarm-actions`, `put-dashboard`, `delete-dashboards`, `put-metric-data`; `xray update-trace-segment-destination`, `update-indexing-rule`, `put-trace-segments`, sampling-rule/group create/update/delete; `lambda update-function-configuration`, `lambda invoke` (smoke is a precondition, not part of the validator); `apigateway update-stage`/`create-stage`; `sns publish`, `subscribe`, `confirm-subscription` | Command names from [S29][S38][S39][S7][S13]; the list is a [P] policy |

### IAM read set (least privilege)

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
Action names follow the API operation names. All except `lambda:GetFunctionConfiguration` and `apigateway:GET` fall
under the `CloudWatchReadOnlyAccess` wildcards [S53]. Per-action access levels and resource-level scoping are
(unverified), U2. `cloudwatch:SetAlarmState` goes in a **separate, temporary** statement only for K1 [S43][S53].
`logs:Unmask` must not be granted (N8) [S8].

**Integration**: validator ↔ Quarkus Lambda (field names from `logging-quarkus-lambda-v3-40`, EMF from
`monitoring-quarkus-lambda-v3-40`, tracing from `tracing-quarkus-lambda-v3-40`; all out of scope) ↔ API Gateway
REST/HTTP [F35] ↔ D2 (`research_AWS_LambdaDebug_2026-10.md`): a FAIL here routes to the D2 symptom tree. API Gateway →
Lambda errors: 500 when Lambda rejects the invoke, 502 on function error or a malformed response [F38]. A smoke test
that saw 5xx should expect `Errors`/`Throttles` accordingly (A5).

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment (no AWS calls)
bash -n lib-common.sh check-*.sh validate-observability.sh        # syntax only
command -v aws && aws --version                                   # expect "aws-cli/2." prefix (v2 required)
command -v jq || echo "PRECONDITION: jq missing (K4)"
grep -nE 'aws [a-z0-9-]+ (put|delete|create|update|enable|disable|publish|subscribe|invoke|associate)' check-*.sh \
  && echo "FAIL: forbidden mutating command in scripts (N1)"
grep -n 'set-alarm-state' check-*.sh                               # expect: only inside the approval-gated branch (K1)
grep -n -- '--unmask' check-*.sh && echo "FAIL N8"
grep -n -- '--output text' check-*.sh                              # review each: never with --query on paginated commands (N2)
```

**Mocking** [P] (no AWS fact; offline tests stub the `aws` binary with fixture JSON shaped like the documented outputs):
```bash
# tests/stub-aws.sh — put first on PATH
aws() { case "$*" in
  *"get-trace-segment-destination"*) echo '{"Destination":"CloudWatchLogs","Status":"ACTIVE"}';;   # shape from [S29]
  *"get-query-results"*)             echo '{"status":"Complete","results":[[{"field":"n","value":"3"}]],"statistics":{"recordsMatched":3}}';;  # [S10]
  *"describe-alarms"*)               echo '{"MetricAlarms":[{"AlarmName":"a","StateValue":"OK","ActionsEnabled":true,"AlarmActions":["arn:aws:sns:eu-west-1:111122223333:t"]}]}';;  # [S42]
  *) echo '{}';; esac; }
export -f aws
```
Test cases: Transaction Search active → no `batch-get-traces` call (N4); HTTP API → no Stage node required (N5);
`Running`→`Complete` poll (A3); `PendingConfirmation` → FAIL (A8); exit 253 → PRECONDITION (A1).

---

## Production Readiness

- **Performance / throttling** (default quotas, per account per Region): `DescribeLogGroups` 10 TPS; `FilterLogEvents`
  25 TPS in us-east-1, 5 TPS in ap-northeast-3/ap-southeast-3/ca-west-1/eu-central-1/il-central-1, 10 TPS elsewhere;
  `StartQuery` 10 TPS; `GetQueryResults` 10 TPS [S12]. 100 concurrent Logs Insights QL queries including dashboard
  queries, shared with scheduled queries; 15 concurrent PPL/SQL [S9][S15]. `GetMetricWidgetImage` 20 TPS [S52].
  `ListSubscriptionsByTopic` 30 TPS [S47]. X-Ray `GetTraceSummaries`/`BatchGetTraces` may return `ThrottledException`
  (429) [S26][S27]. CLI standard retry retries throttling codes with backoff (max 20 s), 3 attempts by default [S4].
- **Scalability**: `start-query` up to 50 log groups per list and 10 data sources per query [S9]. `get-metric-data`
  500 queries / 100,800 points [S17]. `get-metric-statistics` 1,440 points [S18]. `describe-alarms --alarm-names` 100
  [S42]. `list-dashboards` 1000 per page [S50]. `batch-get-traces` 5 IDs [S27]. `start-trace-retrieval` 100 IDs [S32].
- **Monitoring of the validator itself**: EMF parse/validation failures are tracked by metrics in `AWS/Logs` [S22]
  (metric names (unverified), U10).
- **Cost**: Logs Insights charged per GB of uncompressed data scanned [S15]; keep windows to the smoke window (A2).
  Span ingestion is charged separately from log ingestion [S30]. `GetMetricData` pricing (unverified), U18.
- **Security**: read-only role (A10). No `--unmask`; print only counts, IDs and statuses (N8, [R7]). `set-alarm-state`
  only with per-run approval (K1). Credentials come only from `AWS_PROFILE`/env/SSO chain [S5], never from the scripts.
- **Windows / Git Bash** (only what AWS documents): exit code via `$?` (bash), `$lastexitcode` (PowerShell),
  `%errorlevel%` (cmd) [S1]. Quoting rules differ by shell; the guide's examples assume Linux-like shells [S3]. Windows
  default pager is `more` and `setx AWS_PAGER` persists the setting [S2]. `AWS_CLI_FILE_ENCODING` (e.g. `UTF-8` when the
  Windows locale is `CP1252`) [S5]. `fileb://` paths resolve relative to the current working directory [S6]. MSYS/Git
  Bash path conversion of `/aws/lambda/...` arguments is **not documented by AWS** (U5, IRRESOLVABLE; community advice
  rejected per source hierarchy).

---

## Reference Implementations

- AWS X-Ray "Getting data from AWS X-Ray": `get-trace-summaries` → `batch-get-traces` shell pipeline using
  `date +%s` and `--query 'TraceSummaries[*].Id' --output text` [S35]. That pipeline uses `--output text`, which is
  acceptable there only because the result is a flat ID list; prefer JSON per N2.
- Enable Transaction Search, step 4 (verify with `get-trace-segment-destination`) [S29].
- API Gateway REST stage trace segment example (`AWS::ApiGateway::Stage`, `Lambda` subsegment) [S37].
- Logs Insights span queries over `aws/spans` (`durationNano`, `attributes.*`) [S41].
- Dashboard body examples (metric/log/alarm widgets) [S51].
- Repo shape model (no facts): `packages/oci-observability/.apm/skills/validating-oci-observability/scripts/README.md`.
- Sibling research: D1 deploy `research_AWS_LambdaDeploy_2026-10.md`, D2 debug `research_AWS_LambdaDebug_2026-10.md`
  (same CLI ref 2.39.0).

---

## Source Bibliography

**Primary** (all official AWS; read 2026-10-28; "full" = whole page returned by the fetch tool):

| ID | Page | URL | Read |
|---|---|---|---|
| S1 | AWS CLI return codes | https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-returncodes.html | full |
| S2 | CLI pagination & client-side pager | https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-pagination.html | full |
| S3 | CLI filtering output (`--query`, JMESPath, jq) | https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-filter.html | full |
| S4 | CLI retries | https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-retries.html | full |
| S5 | CLI environment variables | https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html | full |
| S6 | CLI common parameter types (timestamp, blob) | https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-parameters-types.html | full |
| S7 | `logs describe-log-groups` | https://docs.aws.amazon.com/cli/latest/reference/logs/describe-log-groups.html | full (tool summary) |
| S8 | `logs filter-log-events` | https://docs.aws.amazon.com/cli/latest/reference/logs/filter-log-events.html | full (tool summary) |
| S9 | `logs start-query` | https://docs.aws.amazon.com/cli/latest/reference/logs/start-query.html | full (tool summary) |
| S10 | `logs get-query-results` | https://docs.aws.amazon.com/cli/latest/reference/logs/get-query-results.html | full (tool summary) |
| S11 | Logs Insights supported logs and discovered fields | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData-discoverable-fields.html | full |
| S12 | CloudWatch Logs quotas | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/cloudwatch_limits_cwl.html | full |
| S13 | Lambda JSON and plain text log formats | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html | full |
| S14 | Logs Insights functions | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-operations-functions.html | full |
| S15 | Analyzing log data with Logs Insights | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html | full |
| S16 | CloudWatch Logs API PutLogEvents | https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_PutLogEvents.html | full |
| S17 | `cloudwatch get-metric-data` | https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-metric-data.html | full (tool summary) |
| S18 | `cloudwatch get-metric-statistics` | https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-metric-statistics.html | full (tool summary) |
| S19 | `cloudwatch list-metrics` | https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/list-metrics.html | full (tool summary) |
| S20 | Types of metrics for Lambda | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html | full |
| S21 | Using CloudWatch metrics with Lambda | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html | full |
| S22 | Embedded metric format specification | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html | full |
| S23 | Publish custom metrics (PutMetricData / EMF) | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html | full |
| S24 | `xray get-trace-summaries` | https://docs.aws.amazon.com/cli/latest/reference/xray/get-trace-summaries.html | full (tool summary) |
| S25 | `xray batch-get-traces` | https://docs.aws.amazon.com/cli/latest/reference/xray/batch-get-traces.html | full (tool summary) |
| S26 | X-Ray API GetTraceSummaries | https://docs.aws.amazon.com/xray/latest/api/API_GetTraceSummaries.html | full |
| S27 | X-Ray API BatchGetTraces | https://docs.aws.amazon.com/xray/latest/api/API_BatchGetTraces.html | full |
| S28 | CloudWatch Transaction Search | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search.html | full |
| S29 | Enable Transaction Search | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-TransactionSearch.html | full |
| S30 | Spans (`aws/spans` log group) | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search-ingesting-span-log-groups.html | full |
| S31 | `xray get-trace-segment-destination` | https://docs.aws.amazon.com/cli/latest/reference/xray/get-trace-segment-destination.html | full (tool summary) |
| S32 | `xray start-trace-retrieval` | https://docs.aws.amazon.com/cli/latest/reference/xray/start-trace-retrieval.html | full (tool summary) |
| S33 | `xray list-retrieved-traces` | https://docs.aws.amazon.com/cli/latest/reference/xray/list-retrieved-traces.html | full (tool summary) |
| S34 | X-Ray filter expressions | https://docs.aws.amazon.com/xray/latest/devguide/xray-console-filters.html | full |
| S35 | Getting data from AWS X-Ray | https://docs.aws.amazon.com/xray/latest/devguide/xray-api-gettingdata.html | full |
| S36 | API Gateway: trace REST APIs with X-Ray | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-xray.html | full |
| S37 | API Gateway: X-Ray traces for APIs | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-understanding-xray-traces.html | full |
| S38 | API Gateway: set up X-Ray with REST APIs | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-enabling-xray.html | full |
| S39 | Lambda: visualize invocations with X-Ray | https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html | full |
| S40 | Transaction Search: ingesting spans / trace summaries | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search-ingesting-spans.html | full |
| S41 | Transaction Search: searching and analyzing spans | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search-search-analyze-spans.html | full |
| S42 | `cloudwatch describe-alarms` | https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/describe-alarms.html | full (tool summary) |
| S43 | `cloudwatch set-alarm-state` | https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/set-alarm-state.html | full (tool summary) |
| S44 | `cloudwatch describe-alarm-history` | https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/describe-alarm-history.html | full (tool summary) |
| S45 | CloudWatch alarm evaluation | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/alarm-evaluation.html | full |
| S46 | `sns list-subscriptions-by-topic` | https://docs.aws.amazon.com/cli/latest/reference/sns/list-subscriptions-by-topic.html | full (tool summary) |
| S47 | SNS API ListSubscriptionsByTopic | https://docs.aws.amazon.com/sns/latest/api/API_ListSubscriptionsByTopic.md | full |
| S48 | SNS: confirm your subscription | https://docs.aws.amazon.com/sns/latest/dg/SendMessageToHttp.confirm.html | full |
| S49 | `cloudwatch get-dashboard` | https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-dashboard.html | full (tool summary) |
| S50 | `cloudwatch list-dashboards` | https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/list-dashboards.html | full (tool summary) |
| S51 | Dashboard body structure and syntax | https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/CloudWatch-Dashboard-Body-Structure.html | **partly read**: full text saved (74.4 KB), read lines 1–46, 180–270, 494–523, 596–605 plus grep of region/SOURCE/alarms/"."/Required (medium confidence for sections not read) |
| S52 | `cloudwatch get-metric-widget-image` | https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-metric-widget-image.html | full (tool summary) |
| S53 | AWS managed policy CloudWatchReadOnlyAccess (v25, edited 2026-09-22) | https://docs.aws.amazon.com/aws-managed-policy/latest/reference/CloudWatchReadOnlyAccess.html | full |
| S54 | `lambda get-function-configuration` | https://docs.aws.amazon.com/cli/latest/reference/lambda/get-function-configuration.html | full (tool summary, selected fields) |

"Tool summary" means the fetch tool returned a structured extract with verbatim quotes rather than the raw page. The
quoted sentences are taken as page text (medium confidence for anything paraphrased).

**Repo-internal (policy, not AWS facts)**: [F34] [F35] [F38] = `workspace/quarkus-aws-saas/_family_facts_v3.40.md` rows
34, 35, 38; [R7] [R9]–[R12] = `_family_rules_v3.40.md`; shape model `packages/oci-observability/.apm/skills/validating-oci-observability/{SKILL.md,scripts/README.md}` (shape only).

**Fetched but unusable** (no facts taken): `https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-error-handling.html`
(returned only a title; replaced by S1); Service Authorization Reference pages `list_amazoncloudwatch.html`,
`list_awsx-ray.html`, `list_amazoncloudwatchlogs.html` (returned only a title; the tool's "from memory" table was
**discarded**); `https://repost.aws/knowledge-center/cloudwatch-logs-query-errors` (HTTP 403).

**Validation (rejected per source hierarchy, listed for audit only)**: search results from newrelic.com and
datadoghq.com (metric delay), kerneltalks.com and cloudbees (Git Bash), prismatic.io (PendingConfirmation), dev.to
(ingestion lag). None is used as evidence.

**All Deep-Links**: see table above (organized by pillar: S1–S6 CLI; S7–S16 logs; S17–S23 metrics; S24–S41 traces;
S42–S48 alarms; S49–S52 dashboards; S53–S54 IAM/Lambda config).

---

## Research Gaps

> Every gap that survives all gap-loop iterations must also appear as an IRRESOLVABLE row in §7.

```
Gap: U1 — Delay between Lambda log emission and availability in Logs Insights / FilterLogEvents
Impact: Fixed waits may be too short (false FAIL) or too long
Workaround: poll-until-deadline with INCONCLUSIVE at deadline (K5)
Follow-up: AWS Knowledge Center (repost.aws, 403 to the tool) or AWS Support
§7-ref: Iteration 2 — IRRESOLVABLE
```
```
Gap: U2 — IAM access level (Read/List/Write) and resource-level scoping per action
Impact: Least-privilege policy cannot be narrowed below Resource "*" with confidence
Workaround: rely on CloudWatchReadOnlyAccess wildcards [S53]; SetAlarmState separate
Follow-up: Service Authorization Reference pages (did not render in the fetch tool)
§7-ref: Iteration 1 — IRRESOLVABLE
```
```
Gap: U3 — Exact GetTraceSummaries behaviour when Transaction Search is ACTIVE (only indexed spans? all?)
Impact: Smoke traces may be invisible to get-trace-summaries at the 1% default index rate
Workaround: K2 (retrieval API / Logs Insights on aws/spans); report INCONCLUSIVE, not FAIL
Follow-up: X-Ray API reference change log / AWS Support
§7-ref: Iteration 2 — IRRESOLVABLE (medium-confidence inference from [S29][S40] only)
```
```
Gap: U4 — Field name of the trace ID inside aws/spans span records
Impact: Logs Insights trace lookup by ID cannot be written with confidence
Workaround: filter by documented attributes (attributes.aws.local.service [S41]) and count spans
Follow-up: span schema page for Transaction Search
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: U5 — Git Bash / MSYS argument path conversion for log-group names like /aws/lambda/x
Impact: Scripts on Windows Git Bash may send mangled names
Workaround: none from AWS; test in the target shell (Ask-First)
Follow-up: AWS CLI user guide Windows troubleshooting (no page found)
§7-ref: Iteration 1 — IRRESOLVABLE (community-only sources rejected)
```
Unverified (not IRRESOLVABLE, open): **U6** whether `retentionInDays` is absent when logs never expire ([S7] does not
say); **U7** alarm-history retention period ([S44] does not say); **U8** maximum `get-trace-summaries` time window
([S24][S26] do not say); **U9** X-Ray trace retention (not fetched); **U10** `AWS/Logs` EMF failure metric names (not
fetched); **U18** `GetMetricData` pricing (not fetched). **(medium confidence)**: **U11** `CompositeAlarms[]` carries the
same `ActionsEnabled`/`AlarmActions` fields; **U12** `file://q.json` relative path on Windows (S6 states it for
`fileb://`); **U13** `PendingConfirmation` in CLI output (S48 states it for the console); **U14** `start-trace-retrieval`/
`stop-query` classed as read; **U15** DynamoDB subsegment naming under OpenTelemetry ([S35] example is X-Ray SDK for
Java); **U16** application JSON field names (`requestId`/`tenantId` per [R7]; Lambda's own Java key is `AWSrequestId`
[S13]); **U17** Insights field discovery when the Lambda log format is Text (S11: "first embedded JSON fragment");
`list-retrieved-traces` `Spans[].Document` shape identical to `BatchGetTraces` documents ([S33] says "see
BatchGetTraces").

**Contradictions (AWS vs AWS; no family-fact contradiction found):**
- **C1** default retry mode: [S4] "Standard mode… is the default mode for the AWS CLI version 2" vs [S5] `AWS_RETRY_MODE`
  "legacy (default), standard, and adaptive". URLs: S4, S5. Resolution: set `AWS_RETRY_MODE` explicitly (A1).
- **C2** `list-dashboards` `LastModified`: description "milliseconds since Jan 1, 1970" vs example ISO 8601 string [S50].
  Consistent with [S6] (v2 translates response DateTimes to ISO 8601).
- **C3** `get-metric-data` `Timestamps` "formatted in Unix timestamp format" vs ISO 8601 example output [S17]; [S6] as in C2.
- **C4** `get-trace-summaries` CLI example output is a flat URL list that does not match the documented
  `TraceSummaries` structure [S24]. Use the structure from [S26][S35].
- Family facts F34, F35, F38: consistent with S36–S39 (no contradiction).

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Metrics | Delay before new metric statistics / list-metrics visibility | Resolved: up to 2 min (statistics), up to 15 min (list-metrics) | [S23] (2026-10-28) |
| 1 | Traces/Logs | Lambda `TracingConfig.Mode` and `LoggingConfig.LogGroup` JSON paths | Added | [S54] (2026-10-28) |
| 1 | Alarms | `PendingConfirmation` in SNS API reference | Not found in API page; carried to iteration 2 | [S47] (2026-10-28) |
| 1 | IAM | Per-action access levels | ⚠️ IRRESOLVABLE — Service Authorization Reference did not render in the fetch tool (U2) | — |
| 1 | Windows | Git Bash path conversion | ⚠️ IRRESOLVABLE — no AWS page; only community sources (rejected) (U5) | — |
| 2 | Alarms | `PendingConfirmation` value | Resolved (medium confidence): stated for the SNS console | [S48] (2026-10-28) |
| 2 | Logs | Ingestion-to-query delay | PutLogEvents API has no delay statement; repost.aws 403 → ⚠️ IRRESOLVABLE (U1) | [S16] (2026-10-28) |
| 2 | Traces | Trace summaries under Transaction Search | Updated: summaries come from indexed spans (1% default); exact GetTraceSummaries behaviour ⚠️ IRRESOLVABLE (U3) | [S29][S40] (2026-10-28) |
| 3 | Traces | `aws/spans` field names for Logs Insights | Added documented examples (`durationNano`, `attributes.*`); trace-ID field ⚠️ IRRESOLVABLE (U4) | [S41] (2026-10-28) |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Complex)
- [x] All scope areas cited (logs, metrics, traces incl. Transaction Search, alarms incl. Ask-First set-alarm-state, dashboards, credentials/region, exit codes, output/query, pager, retries, Windows)
- [x] Pattern counts driven by domain needs (10 ✅ / 7 ⚠️ / 11 🚫)
- [x] Every anti-pattern has alternative (each ✅ alternative uses High-confidence options only [R9])
- [x] All CLI commands validated/marked as representative (none executed)
- [x] Integration examples complete (API GW REST/HTTP, Quarkus field names parameterized, D2 routing)
- [x] Sources dated and linked (S1–S54, 2026-10-28; partly read S51 flagged)
- [x] Security documented (read-only role, no --unmask, gated set-alarm-state)
- [x] 1+ copy-paste working example (marked Representative)
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated (A1–A9) or downgraded to 🟡 Medium (A10)
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in §7

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: A1–A9 (✓✓). Destination probe before traces (A6). Exact-dimension
  `get-metric-data` with `Sum` for invocation metrics (A5). Explicit `--alarm-types` (N11). JSON output with `--query`
  (N2). Unit conversion per API (A2/N7). The denylist (N1).
- **Medium Confidence (validate with user)**: A10 IAM scoping (U2). K2 trace-ID source under Transaction Search (U3/U4).
  K5 wait budget (U1). K7 widget-image render proof. `PendingConfirmation` in CLI output (U13). OpenTelemetry segment
  names (U15). Application field names (U16).
- **Low Confidence (must ask human)**: U1–U5 IRRESOLVABLE items; any Windows Git Bash behaviour (U5); `set-alarm-state`
  (K1) always needs explicit per-run approval, and that approval cannot come from an agent message.
- **Edge Cases (pause)**: Transaction Search `Status` = `PENDING` [S31] (wait up to 10 min [S29], then INCONCLUSIVE).
  Lambda segment-format rollout in progress [S39]. Log group in Infrequent Access class (no field discovery [S11]).
  GovCloud (no `get-metric-widget-image` [S52]).
- **Emergency Stop**: any request to "fix" a FAIL from the validator (route to `provisioning-aws-cloudwatch-v6` /
  `provisioning-aws-xray-v6`). Exit code 253 (credentials/config) → stop, do not retry [S1].

---

## Verification Loop

```bash
# Self-check of this research file (run from workspace/quarkus-aws-saas/)
F=research_AWS_ObservabilityValidation_2026-10.md
grep -E "^### ✅|^### ⚠️|^### 🚫" "$F"                      # expect 3 tiers
grep -E "^## (Metadata|Executive Summary|Architectural Guardrails|Migration Guide|Implementation Blueprint|Quality Control|Production Readiness|Reference Implementations|Source Bibliography|Research Gaps|Research Iteration Changelog|Completion Checklist|Agent Operation Notes)" "$F"
grep -c '```' "$F"                                          # expect an even number
grep -c "✅ Correct" "$F"                                   # expect >= 11 (N1–N11)
grep -c "2026-10-28" "$F"                                   # dated sources
grep -ci "version" "$F"                                     # expect >= 5
```
