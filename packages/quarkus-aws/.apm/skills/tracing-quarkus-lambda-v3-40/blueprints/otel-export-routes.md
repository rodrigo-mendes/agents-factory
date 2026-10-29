# OpenTelemetry Export Routes to X-Ray (C2)

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Plain statement: **no OTel to X-Ray export route is documented end to end for a Quarkus 3.40 Lambda in the pages read** (medium confidence, absence of evidence, M9). The Quarkus 3.40 OpenTelemetry guides do not mention AWS Lambda; every route below is AWS-documented for OpenTelemetry in general, and its combination with Quarkus is unconfirmed. Prove one in a PoC and record it in the ADR ([C1](./ask-first-decisions.md#c1-x-ray-sdk-or-opentelemetry)).

## Contents

- [C2. OTel export route](#c2-otel-export-route)
- [F9. gRPC OTLP to X-Ray endpoint](#f9-grpc-otlp-to-x-ray-endpoint)
- [Documented Quarkus keys](#documented-quarkus-keys)

## C2. OTel export route

**Route (a): X-Ray UDP span exporter.** AWS's manual Lambda recipe uses `software.amazon.distro.opentelemetry:aws-distro-opentelemetry-xray-udp-span-exporter:0.1.0` with a Simple Span Processor, a parent-based always-on sampler, `LambdaResource` and `AwsXrayLambdaPropagator` (`io.opentelemetry.contrib:opentelemetry-aws-xray-propagator`). Quarkus accepts `quarkus.otel.traces.exporter` = "the full qualified name of a class implementing `io.opentelemetry.sdk.trace.export.SpanExporter`" (build-time property) and `quarkus.otel.propagators` = values "from `PropagatorType` or the full qualified name of a class implementing `io.opentelemetry.context.propagation.TextMapPropagator`". Wiring the AWS exporter into Quarkus this way is (unverified); using the AWS propagator through `quarkus.otel.propagators` is (unverified). The contrib artifacts are not managed by quarkus-bom 3.40.1.1: pin versions yourself. AWS: "For reduced cold starts, consider using OpenTelemetry manual instrumentation".

**Route (b): AWS Lambda Layer for OpenTelemetry.** `AWS_LAMBDA_EXEC_WRAPPER=/opt/otel-instrument`, policy `CloudWatchLambdaApplicationSignalsExecutionRolePolicy`; for tracing only, `OTEL_AWS_APPLICATION_SIGNALS_ENABLED=false`. The AWS migration guide marks it "(Recommended)". The ADOT page lists Java 11, 17 and 21 and does not mention `provided.al2023` or GraalVM native, so native is not covered (medium confidence, absence of evidence); the ADOT pages are undated and partly rendered (medium confidence). The legacy ADOT Java wrapper layer "describes the legacy approach" (Java 8, 11, 17; source difference D2). How the layer interacts with the SDK of `quarkus-opentelemetry` (two SDKs) is (unverified).

**Route (c): OTLP to `https://xray.<region>.amazonaws.com/v1/traces`.** "The endpoint authenticates callers using Signature 4 authentication"; HTTP only ("doesn't support gRPC"); "Make sure Transaction Search is enabled before you use the OTLP Endpoint for traces". The Quarkus 3.40 guide documents OTLP headers but no SigV4 signing, so direct export from the Quarkus OTLP exporter is (unverified). AWS documents collector-less export only "using the AWS Distro for OpenTelemetry (ADOT) SDK".

| Route | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| (a) UDP exporter | No layer, no collector | Exporter 0.1.0 and contrib artifacts outside quarkus-bom; Quarkus wiring unverified | JVM or native; PoC accepted |
| (b) Lambda layer | AWS-managed, zero code, Application Signals | Java managed runtimes only (native not listed); two-SDK interaction unverified | JVM (+ SnapStart) build |
| (c) OTLP endpoint | Standard OTLP, Transaction Search | SigV4 required; no gRPC; Quarkus SigV4 support not documented | Only with a signing component proven in a PoC |

Ask: "Which export route do you prove in a PoC? None is documented end to end for Quarkus 3.40 on Lambda."

Sources: https://docs.aws.amazon.com/xray/latest/devguide/xray-migration-opentelemetry.html ; https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals-Enable-LambdaMain.html ; https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLPEndpoint.html ; https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLPGettingStarted.html ; https://aws-otel.github.io/docs/getting-started/lambda ; https://quarkus.io/version/3.40/guides/opentelemetry

## F9. gRPC OTLP to X-Ray endpoint

Quarkus `quarkus.otel.exporter.otlp.traces.protocol` defaults to `grpc` (default endpoint `http://localhost:4317`). The CloudWatch traces endpoint "supports only HTTP and doesn't support gRPC" and needs SigV4. Impact: export fails, spans are dropped. Severity: high.

```properties
# 🚫 WRONG - default grpc protocol, no SigV4
quarkus.otel.exporter.otlp.traces.endpoint=https://xray.eu-west-1.amazonaws.com
```

```text
# ✅ CORRECT - decide the route first (Ask First C2); the table above lists the AWS-documented routes
```

Sources: https://quarkus.io/version/3.40/guides/opentelemetry ; https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLPEndpoint.html

## Documented Quarkus keys

| Key | Documented default | Note |
|---|---|---|
| `quarkus.otel.traces.enabled` | `true` | build time |
| `quarkus.otel.metrics.enabled` / `quarkus.otel.logs.enabled` | `false` / `false` | metrics and logs belong to the neighbour skills |
| `quarkus.otel.simple` | `false` | set `true` on Lambda ([A9](./always-do-patterns.md#a9-simple-span-processor)) |
| `quarkus.otel.propagators` | `tracecontext,baggage` | X-Ray propagator: route (a) |
| `quarkus.otel.traces.sampler` | `parentbased_always_on` | build time per the tracing guide |
| `quarkus.otel.exporter.otlp.enabled` | page not recorded | `false`: "Telemetry is still generated and propagated, but not sent" (paraphrase) |
| `quarkus.otel.sdk.disabled` | `false` (runtime) | keeps tests from exporting |
| `quarkus.otel.attribute.count.limit` | `128` | value length has no default limit (paraphrase) |
| `quarkus.otel.instrumentation.aws-sdk.experimental-use-propagator-for-messaging` | `false` | Quarkiverse 3.23.x, SQS only; "the X-Ray propagator is always used" for messaging |

Source: https://quarkus.io/version/3.40/guides/opentelemetry ; https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/opentelemetry.html
