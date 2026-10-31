# Ask-First Decisions (ADR order)

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Every decision here is put to the user; none has a default except where a pillar skill states a proposal. Each section summarises the pillar's own decision and links to it; the tradeoff tables live there.

## Contents

- [1. Tracing stack](#1-tracing-stack)
- [2. Metric approach](#2-metric-approach)
- [3. Tenant representation](#3-tenant-representation)
- [4. Log producer and Lambda LogFormat](#4-log-producer-and-lambda-logformat)
- [5. API Gateway type](#5-api-gateway-type)
- [6. JVM with SnapStart or native](#6-jvm-with-snapstart-or-native)

## 1. Tracing stack

Pillar decision: [tracing C1](../../tracing-quarkus-lambda-v3-40/blueprints/ask-first-decisions.md#c1-x-ray-sdk-or-opentelemetry). Options: A X-Ray SDK 2.18.3 (the only path the Quarkus 3.40 guide documents; maintenance mode since 2026-02-25, security fixes only, no end date); B `quarkus-opentelemetry` (AWS-recommended; the 3.40 guides do not mention Lambda); C Powertools tracing (out of scope, (unverified) in Quarkus). If B: no OTel export route to X-Ray was found documented end to end in the pillar's pages ([C2](../../tracing-quarkus-lambda-v3-40/blueprints/otel-export-routes.md#c2-otel-export-route), medium confidence, absence of evidence, M7); never send the default gRPC OTLP export to the X-Ray endpoint ([tracing F9](../../tracing-quarkus-lambda-v3-40/blueprints/otel-export-routes.md#f9-grpc-otlp-to-x-ray-endpoint), High); prove one documented route in a PoC. Never present either option as the default.

Ask: "X-Ray SDK (documented, maintenance mode) or OpenTelemetry (AWS-recommended, Quarkus Lambda export route not documented)? Record the ADR."

## 2. Metric approach

Pillar decision: [monitoring D1](../../monitoring-quarkus-lambda-v3-40/blueprints/ask-first-decisions.md#d1-metric-approach). Options: hand-written EMF; `aws-embedded-metrics` 4.2.0 (last release 2024-08-02, Quarkus and native behaviour (unverified)); Powertools `powertools-metrics` 2.11.0 (Quarkus support not stated on any page, (unverified)); `quarkus-micrometer` plus your own `MeterRegistry` with `micrometer-registry-cloudwatch2` (no Quarkiverse CloudWatch registry exists; push registry on a frozen Lambda (unverified)); OpenTelemetry metrics (same push question); `PutMetricData` (network call, IAM action, per-request charge). The monitoring skill proposes hand-written EMF unless the organisation already standardised on another path.

Interaction with decision 1: if OpenTelemetry is chosen for traces, its metrics path does not become the metric approach by itself; the push-on-frozen-Lambda question stays (unverified).

Ask: "Which emission path? Is there an existing standard (Powertools, Micrometer, OpenTelemetry)? Can you run a deployed smoke test?"

## 3. Tenant representation

Pillar decision: [monitoring D2](../../monitoring-quarkus-lambda-v3-40/blueprints/ask-first-decisions.md#d2-tenant-as-dimension-or-in-the-log) (family rule 7: no unbounded tenant cardinality without an ADR). A `TenantId` dimension (per-tenant alarms; each unique combination is a separate billed metric); B `tenantId` root property plus Logs Insights `stats ... by tenantId` (no per-tenant alarms); C bounded proxy dimension such as `TenantTier` plus the `tenantId` property (the monitoring skill's proposal when no ADR exists).

Consequences for the other pillars (stated by the tracing and logging skills, not new): the trace annotation `tenantId` must be an opaque, bounded identifier and at most 50 annotations are indexed per trace ([tracing C7](../../tracing-quarkus-lambda-v3-40/blueprints/ask-first-decisions.md#c7-tenantid-annotation)); the log field is the MDC key `tenantId`.

Ask: "How many tenants exist now and at most? Are per-tenant alarms required? What is the monthly metric budget? Is `tenantId` opaque (no name or email)?"

## 4. Log producer and Lambda LogFormat

Pillar decisions: [logging A1](../../logging-quarkus-lambda-v3-40/blueprints/ask-first-decisions.md#a1-who-produces-the-json), [A3](../../logging-quarkus-lambda-v3-40/blueprints/ask-first-decisions.md#a3-lambda-logformat), [monitoring D3](../../monitoring-quarkus-lambda-v3-40/blueprints/ask-first-decisions.md#d3-lambda-log-format-and-level). `quarkus-logging-json` is the option the logging skill proposes; Powertools logging needs log4j2 or logback while Quarkus says "Do not include any Log4j dependencies", so compatibility is (unverified). Lambda `LogFormat` JSON enables log-level filtering; EMF lines without `level` would be dropped when `ApplicationLogLevel` is WARN or higher (medium confidence). Decide logging first and pass the result to the metric smoke test.

Ask: "Must an existing Powertools standard be kept? Does any metric filter or query parse plain-text `REPORT` lines? Which log format and level will run in production?"

## 5. API Gateway type

Pillar decision: [tracing C3](../../tracing-quarkus-lambda-v3-40/blueprints/ask-first-decisions.md#c3-api-gateway-type). REST API gets X-Ray and stage sampling rules; HTTP API has no X-Ray, so no API Gateway node and the trace starts at the Lambda segment; with `quarkus-amazon-lambda-http` WAF cannot be attached at the API (both orchestrator-verified family facts, High). The extension choice itself belongs to [developing-quarkus-amazon-lambda-http-v3-40](../../developing-quarkus-amazon-lambda-http-v3-40/blueprints/ask-first-decisions.md#c1-http-api-or-rest-api).

Ask: "Must the API Gateway node appear in the trace? If yes a REST API is required."

## 6. JVM with SnapStart or native

Pillar decision: [tracing C4](../../tracing-quarkus-lambda-v3-40/blueprints/ask-first-decisions.md#c4-jvm-with-snapstart-or-native) and [Lambda C1](../../developing-quarkus-amazon-lambda-v3-40/blueprints/ask-first-decisions.md#c1-jvm-snapstart-or-native). Mutually exclusive. Observability consequences as the pillar skills state them: native needs `quarkus-amazon-lambda-xray` on the X-Ray path; SnapStart adds a `Restore` subsegment and re-initialising tracer state after restore is (unverified); the MDC request id is set by the poll loop in native, dev and test, and by nobody in JVM managed-runtime mode (medium confidence); `AWS_LAMBDA_LOG_GROUP_NAME` and `AWS_LAMBDA_LOG_STREAM_NAME` are not available under SnapStart, so the MDC id is the stable correlation key (medium confidence).

Ask: "Which mode was chosen in the Lambda skill? Then apply the consequences above."
