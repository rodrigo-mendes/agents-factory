# Unverified Register, Risks and Bibliography

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 91%, a deep run using all 3 iterations, and 7 triangulated Always-Do patterns. Its header counts 7 unverified and 3 irresolvable items; this register lists 9 and 8. Differences: U8 (a 503 note inside the research's forbidden-pattern F5) and U9 (family fact row 21, which of two restore limits applies) were added; I4 to I8 are AWS-vs-AWS conflicts that the research lists as "cite both ways" and this register records as irresolvable, following the sibling `deploying-aws-lambda` register. U1 to U7 are the research's seven items. Every inline tag of the research keeps a row below. All commands are representative; none was executed (L4).

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- AWS docs are continuously published without a version number; the snapshot is 2026-10-28 (CLI reference 2.39.0). Quotas, limits and CLI flags can change without notice.
- AWS states that the new-format log messages and trace segments are rolling out to all Regions except China and GovCloud; the old and new REPORT, timeout and crash lines coexist. Re-check [log formats](./platform-log-formats.md#old-and-new-style-during-the-transition) and the X-Ray segment change before reuse after 2026-10-28.
- Lambda Web Functions, Managed Instances, MicroVMs and durable functions are documented next to Event Functions with different logs and limits; they are out of scope.
- The Quarkus restore limit (2 s) and the AWS limit (10 s) are both High quotes; if either page changes, U9 changes.
- The read-only boundary and the owner split are repo policy, not AWS facts.

## Unverified items

10 unverified items (do not assert them).

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | Value set of the `X-Amz-Function-Error` header (the Invoke page only says "if present") | Test for presence only |
| U2 | `Runtime.ImportModuleError` token; the page shows "Unable to import module 'function'" | Quote the page string, not the token |
| U3 | Text of the X-Ray field in the plain-text REPORT line (`XRAY TraceId`) | Use the Logs Insights fields `@xrayTraceId`, `@xraySegmentId` |
| U4 | Whether `@type` and `@duration` discovery works on JSON-format platform records | Ask for the log format; match `type` and `record.metrics.*` |
| U5 | Exact name of the EventBridge failed-target-invocation metric (`FailedInvocations`) | Use the rule DLQ attributes and DLQ metrics (S45) |
| U6 | Maximum time range of one `get-trace-summaries` call | Keep windows short; ask the user |
| U7 | Logs Insights and Live Tail pricing comparison (pricing page not read) | Ask before a billable scan |
| U8 | A 503 for the API Gateway plus Lambda path (the brief's "429/503"); no page read documents it | Use 500, 502, 504 and 429 as documented |
| U9 | Which SnapStart restore limit applies: the Quarkus guide says restoration is limited to 2 seconds, AWS says 10 seconds (family fact row 21; both quotes High) | Cite both, choose none |
| U10 | Whether `aws logs tail --follow` starts a billable Live Tail session (S39 notes do not record it) | Never use `--follow`; read with `logs tail --since` or `filter-log-events` |

## Irresolvable items

8 irresolvable items (no fetched page states it, or two official pages disagree).

| ID | Item | Why irresolvable and what to do |
|---|---|---|
| I1 | OOM string "Runtime exited with error: signal: killed" for Event Functions | No Event Function page read contains it; Web Functions has `Runtime.OutOfMemory` (different product, S62). Infer from REPORT `Max Memory Used` equal to `Memory Size` plus `Status`, `Error Type` |
| I2 | REST execution-log strings "Execution failed due to configuration error: Invalid permissions on Lambda function" (K1) and "Malformed Lambda proxy response" (K2) | Knowledge Center pages returned HTTP 403; search snippet only. Decide by status 500 or 502 plus `integrationStatus` |
| I3 | HTTP API integration-timeout status code (504 or 503) | No page read states it; REST gateway responses are REST-specific. Read `$context.error.responseType` in the HTTP API access log |
| I4 | `--log-type Tail`: "first 4 KB" (S11) versus "The last 4 KB" (S5) | Two AWS pages disagree. State "4 KB, base64, synchronous only"; use CloudWatch Logs for full output |
| I5 | One vCPU "At 1.8 GB" (S35) versus at 1,769 MB (S54) | Two AWS pages differ; quote both |
| I6 | SQS provisioned-mode `MaximumPollers` "2-10,000" (S44) versus "2-2000" (S48) | Two AWS pages disagree; quote both |
| I7 | `@maxMemoryUsed` divisor 1000*1000 (S10) versus 1024*1024 (S11); the unit is inferred as bytes | Compare the two fields with each other, never convert |
| I8 | `@initDuration` used in the AWS SnapStart query (S32) but absent from the discovered-field lists (S9, S11) | Use `Init Duration` text matching for classic functions; quote the AWS SnapStart query as is |

## Medium-confidence items

10 medium-confidence items.

| ID | Item | Why medium |
|---|---|---|
| M1 | `FunctionName` as the `AWS/Lambda` metric dimension name | The metrics landing page (S59) gives no dimension list |
| M2 | `$context.awsEndpointRequestId` equals the Lambda RequestId in the REPORT line | Described only as "the AWS endpoint's request ID" |
| M3 | EventBridge invoke permission: principal `events.amazonaws.com`, source the rule ARN | Search snippet only |
| M4 | An SDK `AccessDeniedException` surfaces as a function error; client-side env-var decrypt needs `kms:Decrypt` on the role | Inference from S2, S33, S61, not a page statement |
| M5 | HTTP APIs have access logs only (no execution-log feature) | Not described on the pages read |
| M6 | `aws sqs get-queue-attributes` for `VisibilityTimeout` and `RedrivePolicy` | Named from the SQS API; page not fetched |
| M7 | Matching JSON platform records with `type = 'platform.report'` and `record.metrics.*` | Built from S12 and S51, not an AWS query |
| M8 | A manual SQS receive on the source queue behaves like Lambda's and hides messages | Inference from S44 |
| M9 | IAM action names of the read-only principal | Inferred from API names |
| M10 | `Billed Duration` rounding (S8) is consistent with init billing shown in S6 examples | Two pages read together |

## Coverage limits

6 coverage limits (pages partly read, not read, or commands not run).

| ID | Limit |
|---|---|
| L1 | CLI reference pages S36 to S42 and S56 to S58 were read through a targeted extraction, not reviewed end-to-end; no verbatim quote is recorded for the `logs tail` default start, the `nextToken` 24-hour expiry, `logs:Unmask`, epoch-second times, the 50-log-group and 100,000 limits and the 60-minute timeout, so they carry (medium confidence, L1) |
| L2 | S18, S44, S55 and S59 are landing pages or partial pages; S59 has no dimension list |
| L3 | K1 and K2 returned HTTP 403; two API Gateway pages returned only a title; `java-exceptions` returned S2 content, so the Java error-object format was not read |
| L4 | All commands are representative; the research executed none and made no AWS call |
| L5 | Scope: Event Functions in commercial Regions; Web Functions, Managed Instances, MicroVMs, durable functions, China and GovCloud are not covered |
| L6 | Evaluation fixtures are static strings copied from AWS pages; status values in the API Gateway 500 fixture are illustrative |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) `X-Amz-Function-Error` value set | tree A-B step 1 | U1 |
| (unverified) `Runtime.ImportModuleError` token | tree C-E C5 | U2 |
| (unverified) X-Ray field in the REPORT line | platform-log-formats REPORT fields | U3 |
| (unverified) discovery on JSON platform records | SKILL.md Ask First; ask-first C3; platform-log-formats JSON | U4 |
| (unverified) EventBridge `FailedInvocations` metric name | tree F-H H1 | U5 |
| (unverified) `get-trace-summaries` time range | SKILL.md Ask First; ask-first C4; allowlist | U6 |
| (unverified) Logs Insights and Live Tail pricing | SKILL.md Ask First; ask-first C2; logs-insights; allowlist | U7 |
| (unverified) a 503 on the API Gateway plus Lambda path | tree A-B A5; never-do N5 (pointer); ask-first C7 | U8 |
| (medium confidence, L1) log CLI facts from S39 to S41, S56 (tail default, nextToken expiry, unmask, query limits) | allowlist Choosing the log tool; logs-insights Running one | L1 |
| (unverified) which SnapStart restore limit applies | SKILL.md Ask First and Quick Reference; ask-first C6; tree A-B B5 | U9 |
| (unverified) OOM string | tree C-E C3; ask-first C7 | I1 (irresolvable; text tag (unverified)) |
| (unverified) REST execution-log strings | tree A-B A3 and A4; always-do 8; ask-first C7 | I2 (irresolvable; text tag (unverified)) |
| (unverified) HTTP API timeout status | tree A-B A5; ask-first C7 | I3 (irresolvable; text tag (unverified)) |
| (unverified) first or last 4 KB of the log tail | SKILL.md Quick Reference; platform-log-formats; ask-first C5 | I4 (irresolvable; text tag (unverified)) |
| (unverified) one vCPU threshold | tree C-E C4 | I5 (irresolvable; text tag (unverified)) |
| (unverified) SQS `MaximumPollers` range | tree F-H scaling reference | I6 (irresolvable; text tag (unverified)) |
| (unverified) memory divisor and unit | logs-insights field table; tree C-E C4 | I7 (irresolvable; text tag (unverified)) |
| (unverified) `@initDuration` field | logs-insights field table | I8 (irresolvable; text tag (unverified)) |
| (medium confidence) `FunctionName` dimension | allowlist notes | M1 |
| (medium confidence) `awsEndpointRequestId` correlation | logs-insights access-log table | M2 |
| (medium confidence) EventBridge invoke principal | tree F-H H; always-do 8 | M3 |
| (medium confidence) SDK `AccessDeniedException` mapping | tree C-E C7 | M4 |
| (medium confidence) HTTP APIs have access logs only | SKILL.md Ask First; ask-first C1 | M5 |
| (medium confidence) `sqs get-queue-attributes` | tree F-H branch F; allowlist notes | M6 |
| (medium confidence) JSON platform-record match | SKILL.md Ask First; ask-first C3; platform-log-formats JSON | M7 |
| (medium confidence) manual SQS receive | allowlist refused table | M8 |
| (medium confidence) IAM action names | allowlist principal section | M9 |
| (medium confidence) billed-duration rounding | platform-log-formats interpretation rules | M10 |
| (unverified) and (medium confidence) tags inside scenario expectations | evaluation-scenarios | U9, I1, I2, I3, I4, I5, I7 |
| (unverified) `logs tail --follow` billing | read-only allowlist (logs tail row); aws-lambda-debugger agent | U10 |

Convention (same as `deploying-aws-lambda`): every irresolvable item I1 to I8 carries the text tag (unverified); (medium confidence) is reserved for the M items. Each item has one class.

## Source Bibliography

62 AWS pages (S1 to S62), 2 Knowledge Center pages that could not be fetched (K1, K2) and 3 internal sources (In1 to In3) are listed with URL and read completeness in [source bibliography](./source-bibliography.md). All AWS pages were read on 2026-10-28; the CLI reference pages show AWS CLI 2.39.0. Community sources: none used.
