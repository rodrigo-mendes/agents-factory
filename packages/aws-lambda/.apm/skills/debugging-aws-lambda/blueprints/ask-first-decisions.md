# Ask-First Decisions

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). Source ids resolve in the [source bibliography](./source-bibliography.md). Tags map to the [register](./unverified-and-risks.md#tag-to-register-mapping). Questions go to the user through the orchestrator; the debugger never decides on its own.

## Contents

- [C1 API Gateway logging](#c1-api-gateway-logging)
- [C2 Log tool and window](#c2-log-tool-and-window)
- [C3 Log format](#c3-log-format)
- [C4 X-Ray evidence](#c4-x-ray-evidence)
- [C5 Reproducing by invoking](#c5-reproducing-by-invoking)
- [C6 SnapStart evidence](#c6-snapstart-evidence)
- [C7 Irresolvable strings and status](#c7-irresolvable-strings-and-status)
- [C8 Out-of-scope products and Regions](#c8-out-of-scope-products-and-regions)

## C1 API Gateway logging

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A: ask the deployer to enable logging | exact integration error text (S13) | a mutating stage change the debugger cannot make; REST also needs the account `cloudWatchRoleArn` per Region (S18, S20) | a 5xx with no Lambda-side error |
| B: Lambda-side evidence only | no change needed | cannot see a 500 caused by a missing invoke permission, because Lambda never ran (S16) | function errors visible in Lambda logs |
| C: REST metrics `5XXError`, `IntegrationLatency`, `Latency` | cheap, always on (dimensions `ApiName`, `Stage`) (S50) | per-method dimensions need detailed metrics, at extra cost (S50) | trend or rate questions |

Facts: REST execution log group `API-Gateway-Execution-Logs_{rest-api-id}/{stage_name}`; events truncated at 1 KB with standard logging; levels `ERROR` and `INFO`; AWS recommends not using Data tracing for production APIs; CloudWatch Logs delivery, once configured, replaces standard execution logging and the managed group no longer receives new events (S20). The HTTP API logging page documents access logging to a log group you create (S19); an execution-log feature for HTTP APIs is not described on the pages read, so HTTP APIs having access logs only is (medium confidence).

Question: "May the deployer enable API Gateway logging, or do we continue with Lambda-side evidence only?"

## C2 Log tool and window

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `logs tail` | fast look at recent events (S39) | no aggregation | live reproduction, last minutes |
| `filter-log-events` | exact lines for one RequestId (S40) | pagination, millisecond timestamps | one request's START to REPORT |
| Logs Insights | aggregation over REPORT lines (S10, S11) | scan is billable; the pricing page was not read (unverified) | cold-start percentage, memory, p99 |

Details of each tool: [allowlist](./read-only-allowlist.md#choosing-the-log-tool). Question: "Which UTC time window, and is a billable Logs Insights scan acceptable?"

## C3 Log format

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Text (default for all runtimes) | matches every AWS sample query (`@type = "REPORT"`, `like /Task timed out/`) (S10, S11) | unstructured application logs | functions on the default format |
| JSON (`LoggingConfig.LogFormat`) | structured filters and the `logsDropped` event (S2, S51) | whether `@type` and `@duration` discovery works on JSON platform records is not stated (unverified) | functions already on JSON |

Read `LoggingConfig.LogFormat` first ([step 0](./tree-a-b-entry-and-invocation.md#step-0-control-plane)). For JSON, match `type = 'platform.report'` and `record.metrics.*` (medium confidence). Question: "Is the function's log format Text or JSON?"

## C4 X-Ray evidence

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Active tracing on | `AWS::Lambda` segment error means a Lambda service problem; `AWS::Lambda::Function` segment error means a function problem (S52) | sampled only: 1 request per second and 5 percent of additional requests (S52) | latency and timeout branches |
| PassThrough (default) | none | no Lambda traces (S52) | tracing off, use logs |
| X-Ray Transaction Search enabled | none through this API | "You cannot find traces through this API" (S37) | use the console, ask the user |

The maximum time range of `get-trace-summaries` is not stated (unverified). Segment structure is changing ([old and new style](./platform-log-formats.md#old-and-new-style-during-the-transition)). Question: "Is Active tracing enabled (`TracingConfig.Mode`)?"

## C5 Reproducing by invoking

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `invoke --invocation-type DryRun` | zero execution, status 204 (S5) | proves only the caller's permission, not API Gateway's | testing the invoke permission of the agent's principal |
| Real invoke (`RequestResponse`, `--log-type Tail`) | fresh evidence; 4 KB, base64, synchronous only (S5, S11) | executes function code, side effects possible; not read-only, so not the debugger's to run | route to the deployer: `aws-lambda-deployer` runs it only under `approval: smoke payload=<file or sha256> ...` (deploy smoke rules, In3) |
| No invoke | strictly read-only | depends on existing logs | default |

Which 4 KB the tail returns is disputed: "first 4 KB" (S11) versus "last 4 KB" (S5) (unverified). Question: "Should the deployer run a side-effect-free smoke payload? The approval line must come from the user through the orchestrator."

## C6 SnapStart evidence

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| SnapStart on (published versions only; https://docs.aws.amazon.com/lambda/latest/dg/snapstart-monitoring.html, S32) | restore instead of init | `Init Duration` absent from REPORT; it is in `INIT_REPORT`; REPORT has `Restore Duration` and `Billed Restore Duration` (S32) | Java managed runtimes |
| SnapStart off | classic REPORT `Init Duration` (S11) | the 10 s init limit applies (S6) | OS-only runtime such as Quarkus native (SnapStart does not support OS-only runtimes: https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html) |

Restore limit: AWS says the runtime load plus `afterRestore()` must finish within 10 seconds or Lambda throws `SnapStartTimeoutException` (S5, S6, S31); the Quarkus 3.40 SnapStart guide says "Restoration is limited to 2 seconds" (https://quarkus.io/version/3.40/guides/aws-lambda-snapstart). Both quotes are High; which limit applies is (unverified). Quote both, choose none. Question: "Is SnapStart on for this version (`SnapStart.OptimizationStatus`)?"

## C7 Irresolvable strings and status

| Item | State | What to do |
|---|---|---|
| OOM string "Runtime exited with error: signal: killed" | not on any Event Function page read (unverified) | infer from REPORT `Max Memory Used` equal to `Memory Size` and `Status`, `Error Type` (S6, S11); never quote the string |
| REST log strings "Execution failed due to configuration error: Invalid permissions on Lambda function" and "Malformed Lambda proxy response" | Knowledge Center pages returned HTTP 403; search snippet only (unverified) | decide by status 500 or 502 plus `integrationStatus` (S16, S23, S53) |
| HTTP API integration-timeout status code (504 or 503) | no page read states it (unverified) | read `$context.error.responseType` in the HTTP API access log (S13, S23) |
| A 503 on the API Gateway plus Lambda path (U8) | no page read documents it (unverified) | use 500, 502, 504 and 429 as documented |

Question: "Do you have a log line that carries the string, or should the verdict rest on the REPORT fields and status codes?"

## C8 Out-of-scope products and Regions

Lambda Web Functions (own error taxonomy, S62), Managed Instances, MicroVMs and durable functions have different logs and limits (S6, S54, S62). China and GovCloud Regions are excluded from the log-format change (S6). Question: "Which function type and Region is this? Is it an Event Function in a commercial Region?"
