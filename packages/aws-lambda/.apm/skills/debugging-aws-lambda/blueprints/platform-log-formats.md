# Platform Log Formats: REPORT, INIT_REPORT, RESTORE_REPORT

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). Source ids resolve in the [source bibliography](./source-bibliography.md). Tags map to the [register](./unverified-and-risks.md#tag-to-register-mapping).

## Contents

- [Platform lines per invocation](#platform-lines-per-invocation)
- [REPORT fields](#report-fields)
- [Exact examples](#exact-examples)
- [Old and new style during the transition](#old-and-new-style-during-the-transition)
- [Interpretation rules](#interpretation-rules)
- [JSON log format](#json-log-format)
- [Log latency and loss](#log-latency-and-loss)

## Platform lines per invocation

Three platform lines exist for every invocation: START, END and REPORT (S11). The START line carries the executed `Version` (S2, S6): `START RequestId: c3252230-c73d-49f6-8844-968c01d1e2e1 Version: $LATEST` (AWS example, S6). Log streams are named `YYYY/MM/DD[Function version][Execution environment GUID]` (S11). The default log group is `/aws/lambda/<function-name>` unless configured otherwise (S7).

## REPORT fields

| Field | Meaning | Source |
|---|---|---|
| `RequestId` | Invocation id, unchanged across retries | S9, S11 |
| `Duration` | Total invocation time of the handler, excluding `INIT` code | S11 |
| `Billed Duration` | Billed time | S11 |
| `Memory Size` | Configured memory | S11 |
| `Max Memory Used` | Peak memory | S11 |
| `Init Duration` | Time taken to run the `INIT` section; present only on a cold start | S11 |
| `Status` | New style: added to the REPORT line (for example `timeout`, `error`) | S6 |
| `Error Type` | New style: added for a runtime or extension crash (for example `Runtime.ExitError`) | S6 |
| `Restore Duration`, `Billed Restore Duration` | SnapStart only; `Init Duration` moves to `INIT_REPORT` | S32 |

The AWS text calls the crash field `ErrorType` in one sentence and `Error Type` in the examples (S6); search for both spellings. The plain-text REPORT line for X-Ray (`XRAY TraceId:`) is not shown on any page read; only the Logs Insights fields `@xrayTraceId` and `@xraySegmentId` are documented (unverified).

## Exact examples

Copied from the AWS pages read on 2026-10-28 (S6); the first two are the new style.

```text
REPORT RequestId: 527cb862-4f5e-49a9-9ae4-a7edc90f0fda Duration: 3016.78 ms Billed Duration: 3101 ms Memory Size: 128 MB Max Memory Used: 31 MB Init Duration: 84.00 ms Status: timeout
REPORT RequestId: 5b866fb1-7154-4af6-8078-6ef6ca4c2ddd Duration: 133.61 ms Billed Duration: 214 ms Memory Size: 128 MB Max Memory Used: 31 MB Init Duration: 80.00 ms Status: error Error Type: Runtime.ExitError
```

Init and restore failures (S6):

```text
INIT_REPORT Init Duration: 1236.04 ms Phase: init Status: timeout
INIT_REPORT Init Duration: 1236.04 ms Phase: init Status: error Error Type: Extension.Crash
RESTORE_REPORT Restore Duration: 1236.04 ms Status: timeout
RESTORE_REPORT Restore Duration: 1236.04 ms Status: error Error Type: Runtime.ExitError
```

Format of the fields: `INIT_REPORT` has `Init Duration`, `Phase`, `Status`, optional `Error Type`; `RESTORE_REPORT` has `Restore Duration`, `Status`, optional `Error Type` (as in the examples above).

## Old and new style during the transition

AWS states on the page read that all Regions except China and GovCloud will move to the new-format log messages and trace segments (S6, S52). Queries must match both styles until the move is complete.

| Event | Old style | New style |
|---|---|---|
| Timeout | separate line `2024-03-04T17:22:38.033Z b70435cc-... Task timed out after 3.00 seconds` | REPORT line with `Status: timeout`; no separate line |
| Crash | separate lines `RequestId: c3252230-... Error: Runtime exited without providing a reason` and `Runtime.ExitError` | REPORT line with `Status: error Error Type: Runtime.ExitError` |

Match `like /Task timed out/` or `Status: timeout`; match `like /Process exited/` (S11) or `Error Type: Runtime.ExitError`. Old X-Ray subsegments `Initialization`, `Invocation`, `Overhead`, `Restore` become a single `Init` subsegment plus annotations `aws.responseLatency`, `aws.responseDuration`, `aws.runtimeOverhead`, `aws.extensionOverhead` (S52).

## Interpretation rules

- `Init Duration` present: new execution environment, a cold start (S11).
- SnapStart: "The cold start duration is the sum of `Restore Duration` + `Duration`" (S32).
- REPORT `Duration` larger than the START-to-REPORT wall time: suppressed init after an earlier failure (S6).
- `Max Memory Used` equal to `Memory Size`: AWS query "Invocations using 100% of assigned memory" uses `@maxMemoryUsed=@memorySize` (S11).
- Billing: `Billed Duration` is described as rounded up to the nearest millisecond (S8) while S6 examples bill more than `Duration` (3004.92 ms to 3117 ms with `Init Duration` 111.23 ms), consistent with init billing (medium confidence).

## JSON log format

`LoggingConfig.LogFormat` is Text by default for all runtimes, or JSON (S51). In JSON, platform lines become objects with `time`, `type` (for example `platform.report`) and `record` (S51); the metrics are `billedDurationMs`, `durationMs`, `initDurationMs`, `maxMemoryUsedMB`, `memorySizeMB`, `restoreDurationMs` (S12). Application logs carry `timestamp`, `level`, `message`, `requestId` (Java: `AWSrequestId`) (S51). Matching `type = 'platform.report'` and `record.metrics.*` in queries is (medium confidence); whether `@type` and `@duration` discovery works on JSON platform records is not stated (unverified). JSON application logs are supported for all Java runtimes except Java 8 on AL1 (S51).

## Log latency and loss

- Logs can take 5 to 10 minutes to appear after an invocation (S2, S7).
- Missing logs can mean a missing execution-role permission (`logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`, as in `AWSLambdaBasicExecutionRole`), CloudWatch Logs throttling, or Lambda dropping logs above about 2 MB/s per stream (a `logsDropped` event in JSON format) (S2, S7, S12).
- `--log-type Tail` on `invoke`: 4 KB, base64, synchronous only; "first 4 KB" (S11) versus "last 4 KB" (S5), pages disagree (unverified). Use CloudWatch Logs for full output.
