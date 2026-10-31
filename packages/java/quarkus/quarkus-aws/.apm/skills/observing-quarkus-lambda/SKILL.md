---
name: observing-quarkus-lambda
description: "Composes the logging, tracing and metrics skills for Quarkus 3.40 Lambda backends: decision order, requestId/tenantId correlation across logs, X-Ray and EMF, hand-off to infra. Use when a task spans two or more pillars. Not for one pillar, alarms, dashboards, Terraform or Quarkus 4."
---

# Observing Quarkus AWS Lambda functions (umbrella)

> Version lock: every claim applies to **Quarkus 3.40 LTS, patch 3.40.1.1** (`quarkus-amazon-lambda`, `quarkus-logging-json`, `quarkus-amazon-lambda-xray`) and the three pillar skills listed below, all researched **2026-10-28**. This umbrella adds no new facts: each statement comes from a pillar skill and keeps that skill's tag.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).

## Version Context

| Item | Value | Source |
|---|---|---|
| Quarkus | 3.40 LTS, released 2026-09-30, community-maintained until 2027-09-30; patch 3.40.1.1 (2026-10-19) | https://quarkus.io/releases (via the pillar skills) |
| Pillar: logs | [logging-quarkus-lambda-v3-40](../logging-quarkus-lambda-v3-40/SKILL.md) | fetched 2026-10-28 |
| Pillar: traces | [tracing-quarkus-lambda-v3-40](../tracing-quarkus-lambda-v3-40/SKILL.md) | fetched 2026-10-28 |
| Pillar: metrics | [monitoring-quarkus-lambda-v3-40](../monitoring-quarkus-lambda-v3-40/SKILL.md) | fetched 2026-10-28 |
| X-Ray SDK | maintenance mode since 2026-02-25, security fixes only, no end date | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html |

**Version-lifetime risk** (as of 2026-10-28; details in [register](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Each pillar skill is locked to 3.40.x; a new Quarkus minor needs new pillar skills and a new umbrella review.
- Quarkus 4.0.0 is "Upcoming" with no date; reject Quarkus 4 content.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Composition rule](#composition-rule)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Ask-first decisions (ADR order)](./blueprints/ask-first-decisions.md)
- [Never-do patterns](./blueprints/never-do-patterns.md)
- [Correlation recipe](./blueprints/correlation-recipe.md)
- [Verification Loop](./blueprints/verification-loop.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Take the decisions in ADR order before writing code**: tracing stack, metric approach, tenant representation. See [ask-first decisions](./blueprints/ask-first-decisions.md). Detail: [patterns](./blueprints/always-do-patterns.md#1-decide-in-order).
- **Use one correlation key set across the pillars**: `tenantId` as the trace annotation and the tenant as the chosen metric dimension or root property; for the log MDC keys per invocation mode see Ask First 6. See [patterns](./blueprints/always-do-patterns.md#2-one-key-set).
- **Set `Mode=Active` and the two X-Ray actions, JSON logging on, and an explicit log-group retention** as the minimum baseline for all pillars: each is an Always Do of its pillar skill ([tracing](../tracing-quarkus-lambda-v3-40/SKILL.md#-always-do), [logging](../logging-quarkus-lambda-v3-40/SKILL.md#-always-do)). See [patterns](./blueprints/always-do-patterns.md#3-baseline-per-pillar).
- **When EMF is the chosen approach, write it with `System.out.println`, not through the Quarkus logger, whose default console format prefixes timestamp and level** ([monitoring never-do](../monitoring-quarkus-lambda-v3-40/blueprints/never-do-patterns.md); the JSON-logging case is in [N3](./blueprints/never-do-patterns.md#n3-emf-through-the-logger)). See [patterns](./blueprints/always-do-patterns.md#4-emf-on-raw-stdout).
- **Read function health from `AWS/Lambda` built-in metrics** and emit business outcomes only ([monitoring](../monitoring-quarkus-lambda-v3-40/SKILL.md#-always-do)). See [patterns](./blueprints/always-do-patterns.md#5-built-in-metrics-first).
- **Verify on a deployed function**: one JSON log line with `mdc`, one trace with the annotation, one metric in the namespace. See [Verification Loop](./blueprints/verification-loop.md).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| 1. Tracing stack (ADR, never a default) | X-Ray SDK (documented by Quarkus, maintenance mode since 2026-02-25) vs `quarkus-opentelemetry` (AWS-recommended; no Quarkus Lambda export route found documented in the pillar's pages (medium confidence, absence of evidence, M7); never send the default gRPC OTLP export to the X-Ray endpoint (tracing F9, High); prove one documented route in a PoC) vs Powertools tracing (out of scope (unverified)). [Detail](./blueprints/ask-first-decisions.md#1-tracing-stack) | "X-Ray SDK or OpenTelemetry? Record the ADR." |
| 2. Metric approach (never a default that relies on an (unverified) option) | hand-written EMF; `aws-embedded-metrics` (last release 2024-08-02, behaviour in Quarkus (unverified)); Powertools metrics (unverified); Micrometer plus own registry (push on a frozen Lambda (unverified)); `PutMetricData`. Propose hand-written EMF. [Detail](./blueprints/ask-first-decisions.md#2-metric-approach) | "Which emission path? Existing standard? Can you run a deployed smoke test?" |
| 3. Tenant as dimension, property or proxy | A `TenantId` dimension (needs ADR when unbounded), B root property plus Logs Insights, C bounded proxy plus property (proposal without ADR). The same choice fixes the log and trace key. [Detail](./blueprints/ask-first-decisions.md#3-tenant-representation) | "How many tenants now and at most? Per-tenant alarms? Metric budget?" |
| 4. Who produces JSON and Lambda `LogFormat` | `quarkus-logging-json` (proposed by the logging skill) vs Powertools logging (unverified); Lambda `LogFormat` Text vs JSON changes how EMF lines may be filtered (medium confidence). [Detail](./blueprints/ask-first-decisions.md#4-log-producer-and-lambda-logformat) | "Is Powertools mandated? Does any filter parse plain-text `REPORT` lines?" |
| 5. API Gateway type | REST API shows an API Gateway node in the trace; HTTP API does not (the trace starts at the Lambda segment). [Detail](./blueprints/ask-first-decisions.md#5-api-gateway-type) | "Must the API Gateway node appear in the trace?" |
| 6. JVM with SnapStart or native | Mutually exclusive; native needs `quarkus-amazon-lambda-xray` on the X-Ray path; MDC per mode differs (medium confidence): in JVM mode the function puts `AWSRequestId` and `tenantId` in MDC and clears them in `finally` (medium confidence, as in the logging skill); under SnapStart the `AWS_LAMBDA_LOG_GROUP_NAME` and `AWS_LAMBDA_LOG_STREAM_NAME` variables are unavailable (medium confidence). [Detail](./blueprints/ask-first-decisions.md#6-jvm-with-snapstart-or-native) | "Which mode was chosen in the Lambda skill?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Put `requestId`, `orderId`, `userId` or an unbounded `tenantId` in an EMF dimension ([monitoring](../monitoring-quarkus-lambda-v3-40/SKILL.md#-never-do)) | Bounded dimensions plus the identifier as a root property; tenant per Ask First 3 |
| Put PII or secrets in logs, annotations, metadata or span attributes ([logging](../logging-quarkus-lambda-v3-40/SKILL.md#-never-do), [tracing](../tracing-quarkus-lambda-v3-40/SKILL.md#-never-do)) | An opaque `tenantId` and the Lambda request id |
| Emit EMF through `Log.info(...)`: the default console format prefixes timestamp and level ([monitoring](../monitoring-quarkus-lambda-v3-40/SKILL.md#-never-do); JSON-logging case: [N3](./blueprints/never-do-patterns.md#n3-emf-through-the-logger)) | One raw line with `System.out.println` |
| Use a trace annotation key other than the family key (for example `tenant_id`) ([tracing](../tracing-quarkus-lambda-v3-40/SKILL.md#-never-do)); SDK handling of such keys: [never-do](./blueprints/never-do-patterns.md) | `tenantId` (one key across the pillars) |
| Present X-Ray SDK or OpenTelemetry as the default | Ask First 1 and an ADR |
| Load the umbrella and a pillar skill for the same pillar | Umbrella for the whole task, pillar skill for one pillar |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Composition rule

**Load this umbrella for a full observability task** (two or more pillars, or "make this Lambda observable"). **Load one pillar skill for one pillar.** Never load the umbrella and a pillar skill for the same pillar in one task: the umbrella links to the pillars, it does not repeat their rules. Following a link from this skill into a pillar's blueprint on demand is not loading that pillar skill.

| Task | Load |
|---|---|
| Logs, traces and metrics together, or correlation between them | this skill; open the pillar blueprints it links to only when needed (that is not loading the pillar skill) |
| Only JSON logs, MDC, log groups | `logging-quarkus-lambda-v3-40` |
| Only X-Ray or OpenTelemetry traces | `tracing-quarkus-lambda-v3-40` |
| Only custom metrics (EMF) | `monitoring-quarkus-lambda-v3-40` |
| Alarms, dashboards, log-infrastructure design | `monitoring-cloudwatch-observability` (name only) |
| X-Ray design, sampling rules, groups | `tracing-aws-xray` (name only) |

## The three pillars in code

| Pillar | What the function does | Source skill |
|---|---|---|
| Logs | `quarkus-logging-json` writes JSON on stdout; `requestId` and `tenantId` go into MDC and are cleared in `finally` (medium confidence, as in the logging skill) | logging: [MDC and request id](../logging-quarkus-lambda-v3-40/blueprints/mdc-and-request-id.md) |
| Traces | Lambda `Mode=Active`; one stack (X-Ray SDK or OpenTelemetry); `tenantId` as indexed annotation, the rest as metadata | tracing: [always-do A1 to A9](../tracing-quarkus-lambda-v3-40/blueprints/always-do-patterns.md) |
| Metrics | when EMF is chosen: one EMF document per invocation as one raw stdout line, bounded dimensions, flush before return | monitoring: [EMF implementation](../monitoring-quarkus-lambda-v3-40/blueprints/emf-implementation.md) |

Combined handler sketch: [correlation recipe](./blueprints/correlation-recipe.md).

## Hand-off to infrastructure

This skill stops at application code. Infrastructure and validation are done elsewhere (names only):

| Need | Hand off to |
|---|---|
| Provision and check observability infrastructure (log groups, tracing config, alarms) on AWS | the `aws-observability` agent and the `validating-aws-observability` skill |
| Alarm and dashboard design, log-infrastructure design | `monitoring-cloudwatch-observability` |
| X-Ray design (groups, sampling, Transaction Search) | `tracing-aws-xray` |
| Terraform for log groups, retention, X-Ray | `provisioning-aws-cloudwatch-v6`, `provisioning-aws-xray-v6`, `provisioning-aws-lambda-v6` |
| Powertools | `implementing-lambda-powertools-java` |

Hand over the decisions of Ask First 1 to 6 as the input; the Lambda-side facts (`Mode=Active`, role actions, retention) are listed in the [baseline](./blueprints/always-do-patterns.md#3-baseline-per-pillar).

## Quick Reference

| Aspect | Value | Source skill |
|---|---|---|
| Request id spelling (stated once here; family rule 7's `requestId` names the concept, not the key) | log MDC key `AWSRequestId` (medium confidence); EMF root property `requestId` (never a dimension); trace metadata key `AWSRequestId` (illustrative, medium confidence, M5) | logging, monitoring, tracing |
| MDC keys | `AWSRequestId` (poll loop spelling, medium confidence), `tenantId` | logging |
| Insights field path | `mdc.AWSRequestId`, `mdc.tenantId` (medium confidence) | logging |
| Trace annotation | key `tenantId`, alphanumerics and dots only, up to 50 indexed per trace; how the SDK handles an invalid key is (unverified, U10) | tracing |
| Trace on Lambda | `Mode=Active`; Lambda alone samples 1 request/s + 5%, not configurable | tracing |
| EMF limits | 100 MetricDefinitions, 30 keys per DimensionSet, 1 MB per document | monitoring |
| Timestamp | epoch milliseconds, 14 days past to 2 hours future | monitoring |
| Retention | log group default indefinite; set explicitly | logging |

## External Resources

All pillar sources were fetched 2026-10-28; see each pillar's bibliography.

- [Logging bibliography](../logging-quarkus-lambda-v3-40/blueprints/unverified-and-risks.md#source-bibliography)
- [Tracing bibliography](../tracing-quarkus-lambda-v3-40/blueprints/unverified-and-risks.md#source-bibliography)
- [Monitoring bibliography](../monitoring-quarkus-lambda-v3-40/blueprints/unverified-and-risks.md#source-bibliography)
- [X-Ray SDK maintenance timeline](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html)
- [Full bibliography of this skill](./blueprints/unverified-and-risks.md#source-bibliography)
