# Migration Notes

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28.

## Contents

- [Status changes](#status-changes)
- [X-Ray SDK to OpenTelemetry mapping](#x-ray-sdk-to-opentelemetry-mapping)
- [Upgrade steps](#upgrade-steps)
- [Compatibility matrix](#compatibility-matrix)
- [Source differences](#source-differences)

## Status changes

- **X-Ray SDK maintenance mode since 2026-02-25.** "The SDKs/Daemon will not receive new feature enhancements"; the end date is "N/A". Every X-Ray SDK for Java page carries this notice. `quarkus-amazon-lambda-xray` 3.40.1.1 depends on `aws-xray-recorder-sdk-aws-sdk-v2` 2.18.3 (quarkus-bom). Patterns A3, A5, A7 and F6 carry this note. Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html
- **Lambda segment format.** "Old-style" vs "new-style" segments; the new style has no `Invocation` subsegment ([facts](./lambda-and-api-gateway-tracing.md#modes-and-segments)).
- **PassThrough no longer sends traces passively** ([F1](./never-do-patterns.md#f1-passthrough-default)).
- **Quarkus 3.40 Migration Guide** (wiki, last edited 2026-10-01): no items about OpenTelemetry, Lambda, X-Ray or tracing. Whether the 3.34 to 3.39 guides hold tracing-related breaking changes is (unverified). Source: https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40
- The 3.40 AWS Lambda guide's X-Ray section has no Maven block; the dependency is named only in prose.

## X-Ray SDK to OpenTelemetry mapping

AWS mapping: Recorder -> Tracer Provider/Tracers; Service Plugins -> Resource Detector; Segment -> (Server) Span; Sub-segment -> (non-Server) Span; Annotations/Metadata -> Attributes; X-Ray Trace Context Propagation -> W3C Trace Context Propagation; Daemon -> OpenTelemetry Collector. In Lambda: "Use an auto-instrumentation Lambda Layer" or "Manually set up OpenTelemetry ... Configure a Simple Span Processor with an X-Ray UDP Span Exporter ... Set up an X-Ray Lambda propagator".

Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html ; https://docs.aws.amazon.com/xray/latest/devguide/xray-migration-opentelemetry.html

## Upgrade steps

Representative order; the export route is [C2](./otel-export-routes.md#c2-otel-export-route) and is not proven for Quarkus.

1. Record the [C1](./ask-first-decisions.md#c1-x-ray-sdk-or-opentelemetry) decision in an ADR.
2. Replace `quarkus-amazon-lambda-xray` and `TracingInterceptor` with `io.quarkus:quarkus-opentelemetry` and `quarkus.<client>.telemetry.enabled=true` ([A6](./always-do-patterns.md#a6-otel-client-telemetry)).
3. Replace `beginSubsegment` and `putAnnotation` with `Tracer` spans and `aws.xray.annotations` ([A8](./always-do-patterns.md#a8-otel-annotations)).
4. Set `quarkus.otel.simple=true` ([A9](./always-do-patterns.md#a9-simple-span-processor)) and an export route proven in a PoC.
5. Keep Lambda `Mode=Active` ([A1](./always-do-patterns.md#a1-active-tracing)) for the Lambda service segments.

## Compatibility matrix

Managed versions in https://repo1.maven.org/maven2/io/quarkus/quarkus-bom/3.40.1.1/quarkus-bom-3.40.1.1.pom (targeted extraction of the `aws` and `opentelemetry` entries only, L3). Every version below is (medium confidence) (M7).

| Dependency | Version (quarkus-bom 3.40.1.1, medium confidence) | Notes |
|---|---|---|
| `com.amazonaws:aws-xray-recorder-sdk-aws-sdk-v2` | 2.18.3 | the only aws-xray artifact managed |
| `io.opentelemetry:opentelemetry-api` | 1.62.0 | `-incubator` 1.62.0-alpha |
| `io.opentelemetry.instrumentation:opentelemetry-instrumentation-api` / `-annotations` | 2.28.1 | |
| `io.opentelemetry.instrumentation:opentelemetry-aws-sdk-2.2` / `-2.2-autoconfigure` | 2.28.1-alpha | used by Quarkiverse telemetry ([A6](./always-do-patterns.md#a6-otel-client-telemetry)) |
| `io.opentelemetry.instrumentation:opentelemetry-aws-lambda-core-1.0`, `-aws-lambda-events-3.11`, `-aws-lambda-events-common-2.2` | 2.28.1-alpha | managed, but no Quarkus guide uses them |
| `io.opentelemetry.contrib:*` (xray propagator, aws-xray, aws-resources) | not managed | pin yourself if used |
| `io.opentelemetry.semconv:opentelemetry-semconv` | 1.41.1 | |
| `com.amazonaws:aws-lambda-java-core` / `-events` | 1.4.0 / 3.16.1 | |
| quarkus-amazon-services | 3.23.0 | family fact: built on Quarkus 3.40.0 |

## Source differences

- D1: AWS pages show `aws-xray-recorder-sdk-bom` 2.11.0 as an example; quarkus-bom 3.40.1.1 manages `aws-xray-recorder-sdk-aws-sdk-v2` 2.18.3. Follow the Quarkus BOM.
- D2: the legacy ADOT Java wrapper page lists Java 8, 11, 17; the new layer page lists Java 11, 17, 21; neither lists `java25` or `provided.al2023`.
- D3: the AWS Lambda java-tracing Gradle example uses `aws-xray-recorder-sdk-aws-sdk` (SDK v1 handler) next to the v2 instrumentor; the X-Ray SDK pages pair `-aws-sdk-v2` with `-aws-sdk-v2-instrumentor`.
