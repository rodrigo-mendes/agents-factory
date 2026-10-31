# Unverified Register, Risks and Bibliography

Research date: none of its own. This umbrella adds no new research; every item below is carried from a pillar skill (2026-10-28) with the same text and tag. Back to [SKILL.md](../SKILL.md).

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- Quarkus 3.40 LTS released 2026-09-30, community-maintained until 2027-09-30; patch 3.40.1.1 (2026-10-19) (High; https://quarkus.io/releases). Quarkus 4.0.0 is "Upcoming" with no date; reject Quarkus 4 content.
- AWS X-Ray SDKs and daemon are in maintenance mode since 2026-02-25 with no end date (High; https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html). Not end of life: the X-Ray versus OpenTelemetry choice is an ADR.
- `aws-embedded-metrics-java` last shipped 2024-08-02, more than 12 months ago (monitoring skill): freshness risk.
- The umbrella depends on three version-locked pillar skills; when one of them changes, review this skill.

## Unverified items

12 unverified items (do not assert them). Items documentation cannot settle are listed once here; there is no separate irresolvable class.

| ID | Item | Carried from | Impact and workaround |
|---|---|---|---|
| U1 | Powertools for AWS Lambda (Java) logging inside Quarkus (needs log4j2 or logback; Quarkus says "Do not include any Log4j dependencies") | logging U2 | ADR spike; `implementing-lambda-powertools-java` by name only |
| U2 | Request id key spelling: Lambda Java JSON `AWSrequestId` vs Quarkus `AWSRequestId`; case sensitivity of Logs Insights field names | logging U8 | Query both spellings or standardise on the MDC key |
| U3 | Whether `org.jboss.logging.MDC` (poll loop) and `org.jboss.logmanager.MDC` (guide) share one store | logging U4 | Use the guide's class; check one JSON line shows `mdc` |
| U4 | OpenTelemetry export route to X-Ray for a Quarkus Lambda: UDP span exporter wiring, AWS propagator through `quarkus.otel.propagators`, AWS Lambda Layer next to `quarkus-opentelemetry`, SigV4 on the OTLP exporter | tracing U1 to U4 | PoC; never send gRPC OTLP to the X-Ray endpoint |
| U5 | Re-initialisation of tracer state after SnapStart restore | tracing U6 | Test on a published version |
| U6 | Powertools tracing inside a Quarkus Lambda | tracing U10 | Pointer only |
| U7 | `aws-embedded-metrics-java` 4.2.0 under Lambda JSON log format, in Quarkus and in native image | monitoring U2 | Deployed test before adoption |
| U8 | Whether the mock event server sends a `Lambda-Runtime-Trace-Id` header in dev and test | tracing U11 | Do not assert a trace id in local tests |
| U9 | Writing a trace id into a log line or an EMF property: no pillar skill states it | this umbrella (coverage gap) | Do not claim it; a deployed test would be needed |
| U10 | How the X-Ray SDK treats annotation keys with invalid characters (dropped, rejected or sanitised) | tracing U8 | Use valid keys (`tenantId` or `tenant.id`) |
| U11 | Powertools metrics 2.11.0 on Quarkus 3.40 (JVM and native); not stated on any page | monitoring U1 | Hand-written EMF; if mandated, functional API tested in a deployed function |
| U12 | Push registries (Micrometer CloudWatch, OTel periodic export) on a frozen Lambda; no official statement | monitoring U3 | Prefer EMF; force a publish before the handler returns and verify |

## Irresolvable items

0 irresolvable items. Facts that documentation cannot resolve are listed once under unverified items.

## Medium-confidence items

8 medium-confidence items.

| ID | Item | Carried from | Why medium |
|---|---|---|---|
| M1 | Request id per mode: native, dev and test (poll loop) put `AWSRequestId` into MDC; the JVM managed-runtime path sets none | logging M2 | Source code at tag 3.40.1.1, absence of MDC code |
| M2 | Logs Insights queries `mdc.<key>` on Quarkus output | logging M9 | Inference from the discovered-fields page |
| M3 | HTTP API traces start at the `AWS::Lambda` segment | tracing C3 (https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html) | Upgraded to High by the orchestrator verification on 2026-10-28; the umbrella states it untagged and keeps this row as the record |
| M4 | EMF lines without `level` are dropped when `ApplicationLogLevel` is WARN or higher; a raw EMF line stays at the root with Lambda JSON log format | monitoring M8, M9 | Inference from two High statements |
| M5 | The combined handler sketch and the join procedure of the correlation recipe | this umbrella | Class shapes and keys come from the pillar skills; the combined body is illustrative |
| M6 | `AWS_LAMBDA_LOG_GROUP_NAME` and `AWS_LAMBDA_LOG_STREAM_NAME` are unavailable under SnapStart, so the MDC id is the stable correlation key | logging M15 | Single AWS page; research tag medium |
| M7 | No end-to-end OpenTelemetry to X-Ray export route for a Quarkus 3.40 Lambda is documented in the pages the tracing skill read | tracing M9 | Absence of evidence in pages read through summarisation |
| M8 | `quarkus-logging-json` places an EMF string logged through the Quarkus logger inside its own JSON document | monitoring M12 | Inference from the extension's purpose; no page read shows it |

## Coverage limits

0 coverage limits of its own. The coverage limits of the pillar skills (logging L1 to L3, tracing L1 to L6, monitoring L1 to L7) apply to the items carried from them.

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) Powertools logging in Quarkus | SKILL.md Ask First 4; ask-first 4 | U1 |
| (unverified) key spelling, case sensitivity | correlation-recipe, how to join | U2 |
| (unverified) MDC classes share a store | not asserted; follow the logging skill | U3 |
| (unverified) OTel export route | SKILL.md Ask First 1; ask-first 1; correlation-recipe OTel path | U4 |
| (unverified) SnapStart tracer re-initialisation | ask-first 6 | U5 |
| (unverified) Powertools tracing in Quarkus | SKILL.md Ask First 1 | U6 |
| (unverified) `aws-embedded-metrics` under Quarkus | SKILL.md Ask First 2; ask-first 2 | U7 |
| (unverified) mock event server trace header | correlation-recipe, does not claim | U8 |
| (unverified) trace id in a log line | correlation-recipe, does not claim | U9 |
| (unverified) invalid annotation key handling | SKILL.md Never Do and Quick Reference; never-do N4 | U10 |
| (unverified) Powertools metrics on Quarkus | SKILL.md Ask First 2; ask-first 2 | U11 |
| (unverified) push registries on a frozen Lambda | SKILL.md Ask First 2; ask-first 2 | U12 |
| (medium confidence) per-mode MDC; MDC put in JVM mode and cleared in `finally` | SKILL.md Ask First 6 and pillars table; always-do 2; ask-first 6; evaluation 1 and 2 | M1 |
| (medium confidence, absence of evidence) no documented OTel to X-Ray route for a Quarkus Lambda | SKILL.md Ask First 1; ask-first 1; correlation-recipe OTel path; evaluation 5 | M7 |
| (medium confidence) `quarkus-logging-json` wraps an EMF string inside its own JSON | always-do 4; never-do N3 | M8 |
| (medium confidence, illustrative) request id as trace metadata key `AWSRequestId` | SKILL.md Quick Reference; correlation-recipe key set | M5 |
| (medium confidence) `mdc.<key>` queries | SKILL.md Quick Reference; correlation-recipe; verification-loop | M2 |
| HTTP API trace start (stated High, no tag) | SKILL.md Ask First 5; ask-first 5 | M3 (record) |
| (medium confidence) EMF without `level`; raw EMF at the root | SKILL.md Ask First 4; always-do 4; ask-first 4 | M4 |
| (medium confidence) illustrative bodies | always-do, never-do, correlation-recipe | M5 |
| (medium confidence) SnapStart log environment variables | SKILL.md Ask First 6; ask-first 6 | M6 |

## Source Bibliography

No source of its own. Sources are those of the pillar skills (all read 2026-10-28):

- [Logging bibliography](../../logging-quarkus-lambda-v3-40/blueprints/unverified-and-risks.md#source-bibliography)
- [Tracing bibliography](../../tracing-quarkus-lambda-v3-40/blueprints/unverified-and-risks.md#source-bibliography)
- [Monitoring bibliography](../../monitoring-quarkus-lambda-v3-40/blueprints/unverified-and-risks.md#source-bibliography)
- Orchestrator-verified facts (2026-10-28), with their pages: X-Ray maintenance mode (https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html), API Gateway feature split (https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html), Quarkus logging guide (https://quarkus.io/version/3.40/guides/logging), no Quarkiverse CloudWatch registry (https://repo1.maven.org/maven2/io/quarkiverse/micrometer/registry/), `BatchGetTraces` with Transaction Search (https://docs.aws.amazon.com/xray/latest/api/API_BatchGetTraces.html).

Community sources: none used.
