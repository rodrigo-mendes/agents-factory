# Always-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Every pattern is carried from a pillar skill; code is illustrative (medium confidence, M5 in the register).

## Contents

- [1. Decide in order](#1-decide-in-order)
- [2. One key set](#2-one-key-set)
- [3. Baseline per pillar](#3-baseline-per-pillar)
- [4. EMF on raw stdout](#4-emf-on-raw-stdout)
- [5. Built-in metrics first](#5-built-in-metrics-first)

## 1. Decide in order

Take the three ADR decisions before code: tracing stack ([tracing C1](../../tracing-quarkus-lambda-v3-40/blueprints/ask-first-decisions.md#c1-x-ray-sdk-or-opentelemetry)), metric approach ([monitoring D1](../../monitoring-quarkus-lambda-v3-40/blueprints/ask-first-decisions.md#d1-metric-approach)), tenant representation ([monitoring D2](../../monitoring-quarkus-lambda-v3-40/blueprints/ask-first-decisions.md#d2-tenant-as-dimension-or-in-the-log)). Reason for the order: the tracing stack changes which annotation code you write, the metric approach decides whether EMF lines go to stdout, and the tenant choice is reused by all three pillars. Details: [ask-first decisions](./ask-first-decisions.md).

## 2. One key set

| Identifier (spelling per pillar) | Log (logging skill) | Trace (tracing skill) | Metric (monitoring skill) |
|---|---|---|---|
| request id | MDC key `AWSRequestId`, cleared in `finally` (medium confidence) | X-Ray path: metadata (everything that is not `tenantId` goes to metadata); OTel path: span attribute, becomes metadata by default | EMF root property `requestId`, never a dimension |
| `tenantId` | MDC key, cleared in `finally` (medium confidence) | indexed annotation `tenantId` (X-Ray subsegment) or listed in `aws.xray.annotations` (OTel) | per Ask First 3: dimension `TenantId`, root property, or bounded proxy plus property |

The tenant value comes from the verified token, never from a request body (family rule 6, as quoted in the logging handler pattern).

## 3. Baseline per pillar

| Pillar | Baseline | Source |
|---|---|---|
| Logs | `io.quarkus:quarkus-logging-json`; `%dev.` and `%test.quarkus.log.console.json.enabled=false`; explicit log-group retention (HCL belongs to `provisioning-aws-cloudwatch-v6`) | [logging always-do](../../logging-quarkus-lambda-v3-40/blueprints/always-do-patterns.md) |
| Traces | Lambda `TracingConfig` `Mode=Active`; execution role `xray:PutTraceSegments` and `xray:PutTelemetryRecords`; at least 256 MB for an X-Ray-instrumented function; set before `publish-version` | [tracing always-do](../../tracing-quarkus-lambda-v3-40/blueprints/always-do-patterns.md), [never-do F7](../../tracing-quarkus-lambda-v3-40/blueprints/never-do-patterns.md#f7-published-version-tracing-mode) |
| Metrics | custom namespace not starting with `AWS/`; flat root members; units from CloudWatch; flush before return | [monitoring always-do](../../monitoring-quarkus-lambda-v3-40/blueprints/always-do-patterns.md) |

Infrastructure for this baseline is provisioned by the hand-off targets named in the [SKILL.md](../SKILL.md#hand-off-to-infrastructure), not here.

## 4. EMF on raw stdout

When EMF is the chosen approach, write it with `System.out.println`, one complete JSON object on one line; the Quarkus console format prefixes text, and `quarkus-logging-json` wrapping an EMF string inside its own JSON document is (medium confidence, M8) ([monitoring never-do](../../monitoring-quarkus-lambda-v3-40/blueprints/never-do-patterns.md)). With Lambda `LogFormat=JSON` a raw EMF line stays at the root only by inference (medium confidence, monitoring M9); verify on a deployed function ([verification loop](./verification-loop.md)).

## 5. Built-in metrics first

Read `Invocations`, `Errors`, `Throttles`, `Duration` and `ConcurrentExecutions` from `AWS/Lambda` and emit business outcomes only ([monitoring built-ins](../../monitoring-quarkus-lambda-v3-40/blueprints/cardinality-cost-and-builtins.md)). Cold start: `Init Duration` from the `REPORT` line via Logs Insights unless a billed `ColdStart` metric is chosen ([monitoring D5](../../monitoring-quarkus-lambda-v3-40/blueprints/ask-first-decisions.md#d5-cold-start-visibility)).
