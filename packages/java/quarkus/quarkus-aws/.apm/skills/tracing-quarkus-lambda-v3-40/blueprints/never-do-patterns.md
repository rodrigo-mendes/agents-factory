# Never-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. F9 (gRPC OTLP to the X-Ray endpoint) is in [otel-export-routes.md](./otel-export-routes.md#f9-grpc-otlp-to-x-ray-endpoint).

## Contents

- [F1. PassThrough default](#f1-passthrough-default)
- [F2. HTTP API node](#f2-http-api-node)
- [F3. Env var trace header](#f3-env-var-trace-header)
- [F4. PII in trace data](#f4-pii-in-trace-data)
- [F5. Invalid annotation keys](#f5-invalid-annotation-keys)
- [F6. Function segment annotations](#f6-function-segment-annotations)
- [F7. Published version tracing mode](#f7-published-version-tracing-mode)
- [F8. Lambda sampling rules](#f8-lambda-sampling-rules)
- [F10. Unsupported event source mappings](#f10-unsupported-event-source-mappings)

## F1. PassThrough default

Severity: high. In PassThrough Lambda "does not send traces automatically. This is true even if the tracing header contains a decision to sample the request." AWS: "If your solution depends on this passive tracing behavior, switch to `Active` tracing." Impact: no `AWS::Lambda` or `AWS::Lambda::Function` segments, so DynamoDB subsegments have no parent.

```text
# 🚫 WRONG
TracingConfig: (not set)      # defaults to PassThrough
# ✅ CORRECT
TracingConfig: Mode=Active    # A1, plus xray:PutTraceSegments / xray:PutTelemetryRecords (A2)
```

Source: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html

## F2. HTTP API node

Severity: high. AWS X-Ray tracing: REST API "Yes", HTTP API "No". `quarkus-amazon-lambda-http` serves HTTP API payload 2.0 (family fact). Impact: the "API GW -> Lambda -> DynamoDB" trace has no API Gateway segment and no stage sampling rules.

```text
# 🚫 WRONG
HTTP API (payload 2.0) + quarkus-amazon-lambda-http  -> expect an API Gateway segment in the trace
# ✅ CORRECT
REST API stage with X-Ray tracing enabled + quarkus-amazon-lambda-rest  (trade-offs: Ask First C3)
```

Sources: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html ; https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-xray.html

## F3. Env var trace header

Severity: moderate. "For Java runtime versions 17 and later, this environment variable is not used. Instead, Lambda stores tracing information in the `com.amazonaws.xray.traceHeader` system property." It "is not defined for OS-only runtimes (the `provided` runtime family)". Quarkus 3.40.1.1's poll loop sets `System.setProperty("com.amazonaws.xray.traceHeader", traceId)` from `Lambda-Runtime-Trace-Id`. Impact: `getenv` returns null, so log correlation or manual propagation silently loses the trace ID. This rule is limited to Java 17+ managed runtimes; that the X-Ray SDK reads the property inside a native Quarkus function is (medium confidence) and sits in C4.

```java
// 🚫 WRONG - null on java17+/java21/java25 managed runtimes
String header = System.getenv("_X_AMZN_TRACE_ID");
// ✅ CORRECT - Quarkus 3.40.1.1 on java21 (managed runtime)
String header = System.getProperty("com.amazonaws.xray.traceHeader");
```

Native builds on an OS-only runtime (the `provided.al2023` pairing is medium confidence): the variable is not defined there either; which property or loop a native Quarkus function relies on is an Ask First item, [C4](./ask-first-decisions.md#c4-jvm-with-snapstart-or-native).

Sources: https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html ; https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AbstractLambdaPollLoop.java

## F4. PII in trace data

Severity: high. "Anyone that you grant read access to X-Ray can view this data" (annotations and metadata). Quarkus: "The End User attributes are personally identifiable information"; `quarkus.otel.traces.eusp.enabled` defaults to `false`. GenAI message capture (`quarkus.otel.instrumentation.genai.capture-message-content`, documented default `false`) has data-privacy concerns. Family rule 7: no PII. Impact: personal data exposed to every X-Ray reader.

```java
// 🚫 WRONG
sub.putAnnotation("email", user.email());
span.setAttribute("customer.name", customer.name());
// ✅ CORRECT
sub.putAnnotation("tenantId", tenantId);          // opaque, bounded (Ask First C7)
```

```properties
# 🚫 WRONG
quarkus.otel.traces.eusp.enabled=true
# ✅ CORRECT - keep the documented defaults
quarkus.otel.traces.eusp.enabled=false
quarkus.otel.instrumentation.genai.capture-message-content=false
```

Sources: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java.html ; https://quarkus.io/version/3.40/guides/opentelemetry-tracing ; https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/opentelemetry.html

## F5. Invalid annotation keys

Severity: moderate. "The key for an X-Ray annotation can have up to 500 alphanumeric characters. You cannot use spaces or symbols other than a dot or period ( . )". How the SDK handles an invalid key (dropped, rejected or sanitised) is (unverified). Impact: the annotation cannot be used in `annotation[key]` filter expressions as intended.

```java
// 🚫 WRONG
sub.putAnnotation("tenant_id", tenantId);
// ✅ CORRECT
sub.putAnnotation("tenantId", tenantId);   // or "tenant.id"
```

Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-segment.html

## F6. Function segment annotations

Severity: moderate. "You can use the X-Ray SDK to extend the `Invocation` subsegment with additional subsegments for downstream calls, annotations, and metadata. You can't access the function segment directly or record work done outside of the handler invocation scope." Impact: annotations are not recorded where expected. X-Ray SDK is in maintenance mode since 2026-02-25.

```java
// 🚫 WRONG - the function segment is Lambda-owned
AWSXRay.getCurrentSegment().putAnnotation("tenantId", tenantId);
// ✅ CORRECT - A7 pattern
Subsegment sub = AWSXRay.beginSubsegment("## handle");
try { sub.putAnnotation("tenantId", tenantId); /* work */ } finally { AWSXRay.endSubsegment(); }
```

Source: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html

## F7. Published version tracing mode

Severity: moderate. "Tracing mode is part of the version-specific configuration when you publish a version of your function. You can't change the tracing mode on a published version." SnapStart runs only on published versions (family fact). Impact: the update does not affect the version serving traffic; the trace gap persists.

```text
# 🚫 WRONG
update-function-configuration --tracing-config Mode=Active   # targeting version 7, already published
# ✅ CORRECT
set Mode=Active on the unpublished configuration, publish a new version, move the alias
```

Sources: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html ; https://docs.aws.amazon.com/lambda/latest/dg/java-tracing.html

## F8. Lambda sampling rules

Severity: moderate. "The sampling rate is 1 request per second and 5 percent of additional requests. You can't configure the X-Ray sampling rate for your functions." Impact: a rule has no effect on Lambda's own sampling; trace volume or gaps surprise you.

```text
# 🚫 WRONG
X-Ray sampling rule, service type AWS::Lambda::Function, Rate 50   # expecting Lambda to honour it
# ✅ CORRECT
sampling rule on the upstream REST API stage (service type AWS::ApiGateway::Stage) - Ask First C5
```

Sources: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html ; https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-configuring-xray-sampling-rules.html

## F10. Unsupported event source mappings

Severity: moderate. "X-Ray tracing is currently not supported for Lambda Event Functions with Amazon Managed Streaming for Apache Kafka (Amazon MSK), self-managed Apache Kafka, Amazon MQ with ActiveMQ and RabbitMQ, or Amazon DocumentDB event source mappings." Impact: those triggers produce no Lambda trace.

```text
# 🚫 WRONG
MSK event source mapping + Active tracing -> expect a producer-to-Lambda trace
# ✅ CORRECT
SQS (traces "are automatically linked" to downstream Lambda) or an API Gateway REST API as the traced entry point
```

Source: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html
