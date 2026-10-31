# Pillar: traces

Back to [SKILL.md](../SKILL.md). Script: `scripts/check-traces.py`. AWS CLI 2.39.0 reference, X-Ray, CloudWatch Transaction Search, Lambda and API Gateway docs read 2026-10-28. The manual `bash` forms below use `jq`; the Python scripts do not.

## Contents

- [Decision flow](#decision-flow)
- [Precondition Lambda Active](#precondition-lambda-active)
- [X-Ray path](#x-ray-path)
- [Transaction Search branch](#transaction-search-branch)
- [Segment origins per API type](#segment-origins-per-api-type)
- [Instrumentation and layout notes](#instrumentation-and-layout-notes)
- [Limits](#limits)

## Decision flow

```text
lambda get-function-configuration -> TracingConfig.Mode == Active ?   no -> FAIL (PassThrough sends nothing)
xray get-trace-segment-destination -> Destination
  XRay            -> get-trace-summaries -> batch-get-traces (max 5 ids) -> parse Documents
  CloudWatchLogs  -> (Status ACTIVE?) -> start-trace-retrieval -> poll list-retrieved-traces -> parse Documents
```

`start-trace-retrieval` starts a retrieval and its read class is (medium confidence, M4): run it only under `approval: logs-insights scope=xray window=<min> by=<user> at=<UTC> relayed-by=<orchestrator>`. `check-traces.py` passes it only with `--i-have-trace-retrieval-approval`, to be given only with that relayed line; without the flag the Transaction Search path prints `WARN traces.retrieval not verified` and the pillar is `not verified` (exit 0). The X-Ray path (`batch-get-traces`) needs no flag.

## Precondition Lambda Active

In `PassThrough`, the default, Lambda does not send traces automatically, even when a sampling header asks for it; switch to `Active` ([Lambda and X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)). Read `TracingConfig.Mode` with `get-function-configuration`. A REST API stage shows tracing as `tracingEnabled` on the stage ([stage setup](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-enabling-xray.html)).

## X-Ray path

- `get-trace-summaries` needs `--start-time` and `--end-time`; `--time-range-type` is `TraceId`, `Event` or `Service` and the default search uses the TraceId time ([reference](https://docs.aws.amazon.com/cli/latest/reference/xray/get-trace-summaries.html)). Output key `TraceSummaries[]` with `Id`, `HasFault`, `HasError`, `HasThrottle`, `Http.HttpStatus`, `ServiceIds[]`, `IsPartial`. The CLI example output (a URL list) disagrees with the documented structure (medium confidence); use the structure. The maximum time window is (unverified).
- Filter expression for the function: `service(id(name: "FN", type: "AWS::Lambda::Function"))`; other keywords `ok`, `error`, `fault`, `throttle`, `http.status`, `annotation[key]` ([filters](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-filters.html)).
- `batch-get-traces` takes 1 to 5 ids; `Segments[].Document` is a JSON string: the script parses it with Python `json`; by hand, `jq` needs `fromjson`.

```bash
IDS=$(aws --output json xray get-trace-summaries --start-time "$SMOKE_START_S" --end-time "$END_S" \
        --filter-expression "service(id(name: \"$FN\", type: \"AWS::Lambda::Function\"))" | jq -r '[.TraceSummaries[].Id] | .[:5] | join(" ")')
aws --output json xray batch-get-traces --trace-ids $IDS > traces.json
jq -r '[.Traces[].Segments[].Document | fromjson | .origin] | unique[]' traces.json
```

## Transaction Search branch

- `Destination` `CloudWatchLogs` with `Status` `ACTIVE` means Transaction Search is on; after enabling, spans can take up to 10 minutes to become available. `BatchGetTraces` cannot find traces in that mode ([enable](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-TransactionSearch.html), [BatchGetTraces](https://docs.aws.amazon.com/xray/latest/api/API_BatchGetTraces.html)). `Status` `PENDING` is WARN (inconclusive).
- `start-trace-retrieval --trace-ids ID.. --start-time S --end-time E` (up to 100 ids, epoch seconds) returns `RetrievalToken`; a retrieval times out after 60 minutes ([reference](https://docs.aws.amazon.com/cli/latest/reference/xray/start-trace-retrieval.html)).
- `list-retrieved-traces --retrieval-token T --trace-format XRAY` returns an empty response until `RetrievalStatus` is `COMPLETE`; `--trace-format` is `XRAY` or `OTEL`; a page holds at most 5 traces and 100 spans ([reference](https://docs.aws.amazon.com/cli/latest/reference/xray/list-retrieved-traces.html)). The `Spans[].Document` shape equals the `BatchGetTraces` document shape only (medium confidence).
- Only an indexed share of spans (1% free by default) becomes trace summaries, so smoke traces may be missing (medium confidence); how `get-trace-summaries` behaves then is (unverified). Spans are stored in the `aws/spans` log group in OpenTelemetry semantic-convention format; documented query attributes are `durationNano`, `attributes.db.statement`, `attributes.http.response.status_code`, `attributes.aws.local.service`; the trace id field name is (unverified). Raising the indexing percentage is `update-indexing-rule`: forbidden here, route to `provisioning-aws-xray-v6`. Decision: [K2](./ask-first-decisions.md#k2-trace-ids-under-transaction-search).

```bash
read -r DEST STATUS < <(aws --output json xray get-trace-segment-destination | jq -r '[.Destination,.Status] | @tsv')
TOKEN=$(aws --output json xray start-trace-retrieval --trace-ids $IDS --start-time "$SMOKE_START_S" --end-time "$END_S" | jq -r .RetrievalToken)
aws --output json xray list-retrieved-traces --retrieval-token "$TOKEN" --trace-format XRAY | jq -r .RetrievalStatus   # repeat until COMPLETE
```

## Segment origins per API type

| API in front | Origins to require | Forbidden |
|---|---|---|
| none | `AWS::Lambda`, `AWS::Lambda::Function` | none |
| REST API (stage tracing on) | `AWS::ApiGateway::Stage`, `AWS::Lambda`, `AWS::Lambda::Function` | none |
| HTTP API | `AWS::Lambda`, `AWS::Lambda::Function` | `AWS::ApiGateway::Stage` (an HTTP API adds no X-Ray node) |

A REST stage segment has `name` `<api-name>/<stage>` and a `Lambda` subsegment with `namespace` `aws` ([API Gateway traces](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-understanding-xray-traces.html)). Lambda records two segments per trace named after the function ([Lambda and X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)). On the Transaction Search path an origin mismatch is WARN, because the document shape is (medium confidence).

## Instrumentation and layout notes

- X-Ray SDKs and the Daemon are in maintenance mode since 2026-02-25 (security fixes only); AWS recommends OpenTelemetry ([timeline](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html)). Subsegment names under OpenTelemetry, for example `DynamoDB` with `namespace` `aws`, are (medium confidence) because the documented example comes from the X-Ray SDK for Java.
- The Lambda function segment layout is changing: the old style has `Initialization`, `Invocation` and `Overhead` subsegments, the new style has no `Invocation`. Never assert on `Invocation`. Both layouts may coexist; the rollout timing is (medium confidence).
- X-Ray trace retention is (unverified).

## Limits

`GetTraceSummaries` and `BatchGetTraces` can return `ThrottledException` (429). Span ingestion is charged separately from log ingestion.
