# Unverified Register, Risks and Bibliography

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 81% (approximate), a deep run using all 3 iterations, and 4 triangulated claims. Family facts verified by the orchestrator on 2026-10-28 keep the tags of the family facts file. The research file marked U1, U2, U3 and U6 as irresolvable after its gap loop; this register lists them once under unverified items, because their text tag is (unverified).

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30; latest patch 3.40.1.1 (2026-10-19) (High; https://quarkus.io/releases). The 3.40 documentation is new and may still change.
- Quarkus 4.0.0 is "Upcoming" with no date on the releases page (High). Beta1 was published 2026-10-01 and the final release is "planned for the end of November" (High; https://quarkus.io/blog/quarkus-4-0-0-beta1-released/). Quarkus 4 content is rejected for this skill; the 3.40 patterns are not asserted for Quarkus 4.
- `quarkus.log.console.json.enable` is deprecated for removal since 3.19 (High; source at tag 3.40.1.1, `JsonLogConfig.java`); a later release may remove it.
- The AWS pages on Lambda advanced logging controls are current ("latest") documentation, not versioned; re-read them before relying on a limit or a default.
- AWS runtimes: `java25`, `java21`, `java17.al2023` and `provided.al2023` deprecate 2029-06-30; `java17` (AL2) 2027-06-30 (High; https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html).

## Unverified items

10 unverified items (do not assert them). U1 to U9 are the research gaps; U10 is an observation of the research body that is tagged (unverified) there but was not filed as a gap.

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | What the Lambda Java managed runtime does with plain-text `System.out` lines (not `LambdaLogger`, not Log4j2) when `LogFormat=JSON`: wrapped with the request id, or passed as is | Decides whether "Quarkus plain text plus Lambda JSON" is viable; use `quarkus-logging-json`. Not resolvable from documentation |
| U2 | Whether Powertools for AWS Lambda (Java) logging works with Quarkus 3.40, JVM or native. Powertools requires log4j2 or logback; Quarkus says "Do not include any Log4j dependencies" | Treat as an ADR spike; point to `implementing-lambda-powertools-java` by name only. Not resolvable from documentation |
| U3 | Whether any Quarkus 3.40 component other than the Lambda poll loop reads `AWS_LAMBDA_LOG_LEVEL` or `AWS_LAMBDA_LOG_FORMAT` (the poll loop does not, M2) | Lambda `LoggingConfig` alone does not change Quarkus levels or format; set Quarkus config explicitly. Not resolvable from documentation |
| U4 | Whether `org.jboss.logging.MDC` (used by the Quarkus Lambda poll loop) and `org.jboss.logmanager.MDC` (used in the 3.40 guide) share one store | Use `org.jboss.logmanager.MDC` as in the guide; verify one JSON line shows `mdc` |
| U5 | How JUL-originated levels (SEVERE, WARNING, FINE) are rendered in the JSON `level` field and whether Lambda accepts them (an invalid level becomes INFO) | Test the output of a dependency that logs through JUL |
| U6 | CloudWatch Logs per-GB prices (Standard, Infrequent Access, Insights scan); the pricing page examples conflict ($0.25 vs $0.50 per GB for the same scenario) | State the free tier only; do not quote prices. Not resolvable from the rendered page |
| U7 | Native-image specific limitations of `quarkus-logging-json` in 3.40 (none stated) | Build native in CI and check one JSON line |
| U8 | Request id key spelling: Lambda Java JSON uses `AWSrequestId`; the AWS log4j2 example and the Quarkus poll loop use `AWSRequestId`; whether Logs Insights field names are case sensitive is not stated | Query both spellings or standardise on the MDC key |
| U9 | System-log JSON format and the `@type` / `@requestId` discovered fields on OS-only runtimes and with `LogFormat=JSON` (including whether `@type = "REPORT"` still matches) | Verify with one invoke |
| U10 | Interaction of Quarkus async console logging (`quarkus.log.console.async.enabled`, default `false`) with the Lambda freeze after the handler returns | Keep the default `false` |

## Irresolvable items

0 irresolvable items. Facts that documentation cannot resolve are listed once under unverified items (U1, U2, U3, U6 carry the note "not resolvable from documentation").

## Medium-confidence items

20 medium-confidence items.

| ID | Item | Why medium |
|---|---|---|
| M1 | Quarkus JSON key names `level`, `timestamp`, `mdc` and the default timestamp format `ISO_OFFSET_DATE_TIME` | Read from jboss-logmanager `StructuredFormatter` on the main branch; the version used by 3.40.1.1 was not confirmed (L3) |
| M2 | Request id per mode: native, dev and test (poll loop) put `AWSRequestId` into MDC and remove it in `finally`; the JVM managed-runtime path sets none; the poll loop does not read `AWS_LAMBDA_LOG_*` | Source code at tag 3.40.1.1, not a guide statement; the JVM part rests on absence of MDC code |
| M3 | Level-less text lines are treated as INFO and dropped when `ApplicationLogLevel` is above INFO | Inference from the log-level filtering page |
| M4 | `quarkus.log.level` can be overridden at runtime with `QUARKUS_LOG_LEVEL` | Inferred from the guide calling only `min-level` build-time, plus env var ordinal 300 |
| M5 | Multi-line `System.out` becomes several CloudWatch events | `aws-lambda-java-log4j2` README, main branch |
| M6 | One JSON record per line keeps a stack trace in one event | Inference |
| M7 | `ISO_OFFSET_DATE_TIME` output satisfies the RFC 3339 timestamp Lambda requires | Inference |
| M8 | `log-format=ecs` renames `timestamp` to `@timestamp` and `level` to `log.level`; `gcp` renames `level` to `severity`; so Lambda level filtering breaks | Read from `LoggingJsonRecorder.java` at tag; consequence is an inference |
| M9 | Logs Insights queries `mdc.<key>` on Quarkus output | Inference from the discovered-fields page (dot notation for nested JSON) |
| M10 | Adding `quarkus-logging-json` turns console JSON on ("effectively true"): `enabled` has no default and falls back to the deprecated `enable` (default `true`) | Derived from code at tag, not stated on a page |
| M11 | `ApplicationLogLevel=TRACE` via the CLI: the AWS table lists TRACE, the CLI text lists DEBUG, INFO, WARN, ERROR, FATAL | Two statements on one page that differ |
| M12 | The sentence that tests need the `java.util.logging.manager` system property set to `org.jboss.logmanager.LogManager`: which test setups need it | Context of the sentence only partly read |
| M13 | Create the log group with retention in IaC before the first invoke | Inference from "automatically creates a log group ... when it's first invoked" |
| M14 | `logs:PutLogEvents` is required, is part of `AWSLambdaBasicExecutionRole`, and is not added automatically when the log group is set through the CLI | Single AWS page; research tag medium |
| M15 | `AWS_LAMBDA_LOG_GROUP_NAME` and `AWS_LAMBDA_LOG_STREAM_NAME` are unavailable under SnapStart | Single AWS page; research tag medium |
| M16 | `quarkus.log.level=${AWS_LAMBDA_LOG_LEVEL:INFO}` behaves as expected (Lambda sets the variable only when application log-level filtering is configured) | Combination of two High facts; the behaviour itself was not observed |
| M17 | Relative size or cost of the three `exception-output-type` options | Not stated on any page |
| M18 | Illustrative method bodies (handlers, filter placement for the HTTP extension, `application.properties` composition, the representative `get-function-configuration` output shape) | Class shapes and keys come from pages; the bodies are not from a guide |
| M19 | MDC values left after an invocation leak into a later invocation in the Quarkus Lambda runtime | The AWS reuse rule is High; MDC thread reuse in the Quarkus Lambda runtime is an inference |
| M20 | `aws-lambda-java-core` 1.4.0 as managed by `quarkus-bom` 3.40.1.1 | BOM of 419,419 characters read by targeted extraction only (L3); the entry was found but the rest of the BOM was not checked (family rule 13) |

## Coverage limits

5 coverage limits (parts of pages not read, or read through summarisation).

| ID | Limit |
|---|---|
| L1 | https://quarkus.io/version/3.40/guides/all-config was read in three windows (0 to 232,437 characters); only core logging keys were found, no `quarkus.log.console.json.*` and no `quarkus.lambda.*` keys in the served text |
| L2 | https://quarkus.io/version/3.40/guides/config-reference was read only for the targeted sections (environment variable mapping, ordinals, property expressions) |
| L3 | https://repo1.maven.org/maven2/io/quarkus/quarkus-bom/3.40.1.1/quarkus-bom-3.40.1.1.pom (419,419 characters) was read by targeted extraction only (`aws-lambda-java-core` 1.4.0 found; the jboss-logmanager and jboss-logging versions were not reached) |
| L4 | No Quarkus 3.40 changelog or migration-wiki page on logging was fetched |
| L5 | https://aws.amazon.com/cloudwatch/pricing/ was read 0 to 100,000 of 154,061 characters and the price tables were not rendered |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence) request id per mode, JVM sets no MDC, poll loop does not read AWS_LAMBDA_LOG_* | SKILL.md Ask First and pointer; always-do-patterns 6; mdc-and-request-id; lambda-logging-controls; quarkus-json-config; migration-notes | M2 |
| (unverified) Quarkus reading AWS_LAMBDA_LOG_* outside the poll loop | SKILL.md Ask First; lambda-logging-controls; mdc-and-request-id; ask-first-decisions A4 | U3 |
| (unverified) plain-text stdout under LogFormat=JSON | SKILL.md Ask First; ask-first-decisions A1; lambda-logging-controls | U1 |
| (unverified) Powertools logging with Quarkus | SKILL.md Ask First; ask-first-decisions A1; never-do-patterns F2; evaluation-scenarios | U2 |
| (unverified) same MDC store for the two MDC classes | SKILL.md Ask First; mdc-and-request-id; always-do-patterns 6; ask-first-decisions A2; verification-loop; evaluation-scenarios | U4 |
| (unverified) JUL level rendering | quarkus-json-config; ask-first-decisions A6 | U5 |
| (unverified) prices | SKILL.md Ask First; lambda-logging-controls; ask-first-decisions A5 | U6 |
| (unverified) native-specific limits of the JSON extension | quarkus-json-config | U7 |
| (unverified) request id key spelling and case | SKILL.md Ask First; mdc-and-request-id; always-do-patterns 6; ask-first-decisions A2; evaluation-scenarios | U8 |
| (unverified) REPORT discovered fields with JSON system logs or OS-only runtimes | verification-loop; lambda-logging-controls | U9 |
| (unverified) async console logging and the freeze | quarkus-json-config | U10 |
| (medium confidence) JSON key names and timestamp format | always-do-patterns 7; quarkus-json-config; ask-first-decisions A6 | M1 |
| (medium confidence) level-less lines dropped above INFO | ask-first-decisions A6; lambda-logging-controls | M3 |
| (medium confidence) runtime override of quarkus.log.level | SKILL.md Ask First; ask-first-decisions A4; never-do-patterns F6; evaluation-scenarios | M4 |
| (medium confidence) multi-line stdout splits events | never-do-patterns F4; quarkus-json-config | M5 |
| (medium confidence) stack trace stays in one event | never-do-patterns F4; quarkus-json-config | M6 |
| (medium confidence) RFC 3339 match | always-do-patterns 7; quarkus-json-config | M7 |
| (medium confidence) ECS and GCP key renames | SKILL.md Ask First; ask-first-decisions A6; never-do-patterns F7; quarkus-json-config; evaluation-scenarios | M8 |
| (medium confidence) Logs Insights `mdc.<key>` queries | SKILL.md Quick Reference; verification-loop; mdc-and-request-id; ask-first-decisions A2 | M9 |
| (medium confidence) "effectively true" JSON default | always-do-patterns 1; quarkus-json-config; migration-notes | M10 |
| (medium confidence) TRACE via the CLI | lambda-logging-controls; ask-first-decisions A4 | M11 |
| (medium confidence) `java.util.logging.manager` test property context | verification-loop; quarkus-json-config | M12 |
| (medium confidence) log group before first invoke | always-do-patterns 5; lambda-logging-controls | M13 |
| (medium confidence) PutLogEvents permission | always-do-patterns 8; lambda-logging-controls | M14 |
| (medium confidence) SnapStart log environment variables | always-do-patterns 9 | M15 |
| (medium confidence) expression on AWS_LAMBDA_LOG_LEVEL | SKILL.md Ask First; ask-first-decisions A4 | M16 |
| (medium confidence) exception-output size effect | SKILL.md Ask First; ask-first-decisions A7; quarkus-json-config | M17 |
| (medium confidence) illustrative bodies, filter placement, representative output shape | always-do-patterns 6; mdc-and-request-id; ask-first-decisions A2; quarkus-json-config; verification-loop | M18 |
| (medium confidence) MDC leak across invocations | always-do-patterns 6; never-do-patterns F8; mdc-and-request-id | M19 |
| (medium confidence) `aws-lambda-java-core` 1.4.0 from a partly read BOM | SKILL.md Version Context | M20 |
| (unverified) and (medium confidence) tags inside scenario expectations | evaluation-scenarios | U2, U4, U8, M2, M4, M8 |

## Source Bibliography

The full table is in [source-bibliography.md](./source-bibliography.md).
