# Always-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. A5 and A7 use the X-Ray SDK, in maintenance mode since 2026-02-25 (security fixes only). Pick the stack first: [Ask First C1](./ask-first-decisions.md#c1-x-ray-sdk-or-opentelemetry).

## Contents

- [A1. Active tracing](#a1-active-tracing)
- [A2. Execution role permissions](#a2-execution-role-permissions)
- [A3. Native build extension](#a3-native-build-extension)
- [A4. Memory](#a4-memory)
- [A5. X-Ray client interceptor](#a5-x-ray-client-interceptor)
- [A6. OTel client telemetry](#a6-otel-client-telemetry)
- [A7. X-Ray annotations](#a7-x-ray-annotations)
- [A8. OTel annotations](#a8-otel-annotations)
- [A9. Simple span processor](#a9-simple-span-processor)

## A1. Active tracing

Lambda: "If you do not have `Active` tracing turned on, Lambda defaults to `PassThrough` tracing mode." PassThrough "does not send traces automatically. This is true even if the tracing header contains a decision to sample the request." The Quarkus guide's example uses the same switch (`--tracing-config Mode=Active` in `manage.sh`, `Tracing: Active` in SAM; both are the guide's examples, not this family's IaC). IaC is Terraform (family rule 4): `provisioning-aws-xray-v6` and `provisioning-aws-lambda-v6`, by name only.

```bash
# Representative - adapt to your environment (Quarkus 3.40.1.1 function.zip, any runtime)
aws lambda update-function-configuration --function-name my-function \
  --tracing-config Mode=Active
# Expected: "TracingConfig": {"Mode": "Active"} in the response
```

Sources: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html ; https://quarkus.io/version/3.40/guides/aws-lambda ; https://docs.aws.amazon.com/lambda/latest/dg/java-tracing.html

## A2. Execution role permissions

"Lambda needs the following permissions to send trace data to X-Ray": `xray:PutTraceSegments` and `xray:PutTelemetryRecords`; both are in the `AWSXRayDaemonWriteAccess` managed policy. The console adds them; IaC must add them itself.

```text
# Lambda execution role - tracing actions (Quarkus 3.40.1.1 function)
xray:PutTraceSegments
xray:PutTelemetryRecords
```

Source: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html

## A3. Native build extension

`io.quarkus:quarkus-amazon-lambda-xray` is **native-image support** for the X-Ray SDK, not a tracer. At tag 3.40.1.1 `XrayBuildStep` registers `AWSXRay`, `AWSXRayRecorder`, `TracingInterceptor`, `LocalizedSamplingStrategy` and `ThreadLocalStorage` for runtime initialisation, the X-Ray entity and sampling classes for reflection, the SDK JSON resources (`DefaultOperationParameterWhitelist.json`, `DefaultSamplingRules.json`, `sdk.properties`) and Apache HTTP client proxies. Its POM depends on `quarkus-amazon-lambda-common`, `quarkus-core`, `quarkus-apache-httpclient` and `com.amazonaws:aws-xray-recorder-sdk-aws-sdk-v2`. In JVM mode the guide does not require it; adding the SDK module directly is an option (medium confidence).

```xml
<!-- Quarkus 3.40.1.1 - version from the Quarkus platform BOM -->
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-amazon-lambda-xray</artifactId>
</dependency>
```

Sources: https://quarkus.io/version/3.40/guides/aws-lambda ; https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-xray/3.40.1.1/quarkus-amazon-lambda-xray-3.40.1.1.pom ; https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-xray/deployment/src/main/java/io/quarkus/amazon/lambda/xray/XrayBuildStep.java

## A4. Memory

The guide says X-Ray "adds many classes" and asks for "at least the 256MB".

```text
# Lambda function configuration (Quarkus 3.40.1.1 + X-Ray SDK)
MemorySize >= 256
```

Source: https://quarkus.io/version/3.40/guides/aws-lambda

## A5. X-Ray client interceptor

"Include the `aws-xray-recorder-sdk-aws-sdk-v2 module` instead, then instrument individual clients by configuring them with a `TracingInterceptor`." With an instrumented DynamoDB client "the SDK adds the table name to the segment" and each table is its own service-map node. Alternative: `aws-xray-recorder-sdk-aws-sdk-v2-instrumentor` instruments every v2 client. Quarkiverse-managed clients: [C6](./ask-first-decisions.md#c6-interceptor-placement-for-quarkiverse-clients).

```java
// Quarkus 3.40.1.1 + X-Ray SDK for Java 2.18.3 (maintenance mode since 2026-02-25)
import com.amazonaws.xray.interceptors.TracingInterceptor;
import software.amazon.awssdk.core.client.config.ClientOverrideConfiguration;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;

DynamoDbClient client = DynamoDbClient.builder()
    .overrideConfiguration(ClientOverrideConfiguration.builder()
        .addExecutionInterceptor(new TracingInterceptor())
        .build())
    .build();
```

Sources: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-awssdkclients.html ; https://docs.aws.amazon.com/xray/latest/devguide/xray-migration-opentelemetry.html

## A6. OTel client telemetry

"Adding the `quarkus-opentelemetry` extension will automatically inject an interceptor" into clients that opt in "by setting the configuration property `quarkus.<extension>.telemetry.enabled` to true. This setting is set to `false` by default." DynamoDB key: `quarkus.dynamodb.telemetry.enabled` (env `QUARKUS_DYNAMODB_TELEMETRY_ENABLED`). "It is not necessary to wrap Sqs or Bedrock Runtime clients." Whether the key is fixed at build time is not marked per key on the page (medium confidence). the quarkus-bom 3.40.1.1 POM manages `opentelemetry-aws-sdk-2.2` at 2.28.1-alpha (medium confidence, partial read of the BOM).

```properties
# Quarkus 3.40.1.1 / Quarkiverse amazon-services 3.23.x - requires io.quarkus:quarkus-opentelemetry
quarkus.dynamodb.telemetry.enabled=true
```

Sources: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/opentelemetry.html ; https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html

## A7. X-Ray annotations

"Annotations are key-value pairs with string, number, or Boolean values. Annotations are indexed for use with filter expressions." Keys: alphanumerics plus dot; values up to 1,000 characters; "X-Ray indexes up to 50 annotations per trace". Metadata is not indexed. In Lambda "You can't access the function segment directly", so annotate your own subsegment ([F6](./never-do-patterns.md#f6-function-segment-annotations)). Method bodies are illustrative (medium confidence).

```java
// Quarkus 3.40.1.1 + X-Ray SDK for Java 2.18.3 (maintenance mode since 2026-02-25)
import com.amazonaws.xray.AWSXRay;
import com.amazonaws.xray.entities.Subsegment;

Subsegment sub = AWSXRay.beginSubsegment("## OrderService.save");
try {
    sub.putAnnotation("tenantId", tenantId);       // indexed, valid key, opaque bounded value
    sub.putMetadata("order", "itemCount", count);   // not indexed, no PII
    repository.save(order);
} catch (RuntimeException e) {
    sub.addException(e);
    throw e;
} finally {
    AWSXRay.endSubsegment();
}
```

Sources: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-segment.html ; https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html

## A8. OTel annotations

"By default, OpenTelemetry span attributes are converted to metadata in X-Ray raw data. To convert specific attributes to annotations instead, add their keys to the `aws.xray.annotations` attributes list." "Server Spans convert to X-Ray segments. Other Spans convert to X-Ray sub-segments." Method body illustrative (medium confidence).

```java
// Quarkus 3.40.1.1 + quarkus-opentelemetry (OTel API 1.62.0 per quarkus-bom)
@Inject Tracer tracer;

Span span = tracer.spanBuilder("order.save").startSpan();
try (Scope ignored = span.makeCurrent()) {
    span.setAttribute("tenantId", tenantId);
    span.setAttribute(AttributeKey.stringArrayKey("aws.xray.annotations"), List.of("tenantId"));
    repository.save(order);
} finally {
    span.end();
}
```

Sources: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html ; https://docs.aws.amazon.com/xray/latest/devguide/xray-migration-opentelemetry.html ; https://quarkus.io/version/3.40/guides/opentelemetry-tracing

## A9. Simple span processor

Quarkus: `quarkus.otel.simple` (default `false`) means "Should we use simple processor for spans and log records. This will disable batch processing and the exporter will send telemetry data right away"; the tracing guide names "a serverless environment". AWS's manual OTel Lambda recipe also uses "A Simple Span Processor". Batch defaults: `quarkus.otel.bsp.schedule.delay` `5S`, `quarkus.otel.bsp.export.timeout` `30S`. Why a batch can be lost when Lambda freezes the environment is not stated on these pages (unverified).

```properties
# Quarkus 3.40.1.1 - quarkus-opentelemetry on AWS Lambda
quarkus.otel.simple=true
```

Sources: https://quarkus.io/version/3.40/guides/opentelemetry-tracing ; https://quarkus.io/version/3.40/guides/opentelemetry ; https://docs.aws.amazon.com/xray/latest/devguide/xray-migration-opentelemetry.html
