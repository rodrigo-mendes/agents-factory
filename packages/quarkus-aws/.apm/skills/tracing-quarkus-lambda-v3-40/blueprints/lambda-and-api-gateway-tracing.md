# Lambda and API Gateway Tracing Facts

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Platform facts that bound the "API Gateway -> Lambda -> DynamoDB" trace. Infrastructure is Terraform (family rule 4): `provisioning-aws-xray-v6`, `tracing-aws-xray` (design), by name only.

## Contents

- [Modes and segments](#modes-and-segments)
- [Trace header propagation](#trace-header-propagation)
- [Client integrations](#client-integrations)
- [Limits and security](#limits-and-security)
- [Performance](#performance)

## Modes and segments

| Item | Fact | Source |
|---|---|---|
| Active vs PassThrough | "With `Active` tracing, Lambda automatically creates trace segments for Event Function invocations and sends them to X-Ray. `PassThrough` mode, on the other hand, simply propagates the tracing context to downstream services." Default is PassThrough | https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html |
| Service and function segments | `AWS::Lambda` (scheduling, environment creation, code/layer download) and `AWS::Lambda::Function`; "If the `AWS::Lambda::Function` segment shows an error, your function had an issue". Errors, faults and throttles map to 4xx, 5xx and 429 | https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html |
| New-style segment | No `Invocation` subsegment: "customer subsegments are attached directly to the `AWS::Lambda::Function` segment", which carries `aws.responseLatency`, `aws.responseDuration`, `aws.runtimeOverhead`, `aws.extensionOverhead`. Queries relying on `Invocation` must allow for both styles | https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html |
| SnapStart | A `Restore` subsegment shows snapshot restore, runtime load and after-restore hooks; "You aren't charged for the time spent outside the microVM to restore a snapshot" | https://docs.aws.amazon.com/lambda/latest/dg/java-tracing.html |
| API Gateway root | REST API: X-Ray supported, stage sampling rules. HTTP API: not supported, so the trace starts at the Lambda segment (family fact, verified by the orchestrator 2026-10-28) | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html |
| Event sources | SQS traces "are automatically linked to downstream Lambda"; MSK, self-managed Kafka, Amazon MQ and DocumentDB mappings are not supported ([F10](./never-do-patterns.md#f10-unsupported-event-source-mappings)) | https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html |

## Trace header propagation

- A tracing header "can originate from the X-Ray SDK, an AWS service, or the client request"; header format and `Lineage` ("should not be directly used") are on the X-Ray concepts page.
- Java 17+: Lambda stores the header in the system property `com.amazonaws.xray.traceHeader`; `_X_AMZN_TRACE_ID` is not used there and is not defined on OS-only runtimes ([F3](./never-do-patterns.md#f3-env-var-trace-header)).
- Quarkus 3.40.1.1: `AbstractLambdaPollLoop` sets that property from the `Lambda-Runtime-Trace-Id` header (constant in `AmazonLambdaApi`) and never clears it. The loop being the one used by native functions only is (medium confidence).
- Lambda sets `AWS_XRAY_CONTEXT_MISSING=LOG_ERROR` "to avoid throwing runtime errors from the X-Ray SDK" and `AWS_XRAY_DAEMON_ADDRESS`.
- With Active tracing on the X-Ray path: "there is no additional configuration required to use the X-Ray SDK. Lambda will create a segment representing the Lambda handler invocation, and you can create sub-segments".

Sources: https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html ; https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html ; https://docs.aws.amazon.com/xray/latest/devguide/xray-migration-opentelemetry.html ; https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AmazonLambdaApi.java

## Client integrations

- **DynamoDB (X-Ray):** an instrumented client records a `DynamoDB` subsegment with `aws.table_name`, `aws.operation` and `aws.request_id`; "each table appears as a separate node in the service map". DynamoDB sends no segment of its own, so "X-Ray uses subsegments to generate inferred segments". Client creation: [integrating-quarkus-amazon-data-v3-40](../../integrating-quarkus-amazon-data-v3-40/SKILL.md).
- **DynamoDB (OTel):** `quarkus.dynamodb.telemetry.enabled=true` ([A6](./always-do-patterns.md#a6-otel-client-telemetry)).
- **SQS:** X-Ray links upstream producer traces to the Lambda trace. On the OTel path Quarkiverse 3.23.x has `quarkus.otel.instrumentation.aws-sdk.experimental-use-propagator-for-messaging` (default `false`, currently only SQS) and "the X-Ray propagator is always used" for messaging.
- **Custom spans (OTel):** `@WithSpan` "will create a new Span"; `@AddingSpanAttributes` "will not create a new span but will add annotated method parameters to attributes"; `@SpanAttribute` on parameters. "The instrumentation documented in this section has been tested with Quarkus and works in both standard and native mode."

```java
// Quarkus 3.40.1.1 + quarkus-opentelemetry - CDI bean called by the Lambda handler
// (class shape from the tracing guide; body illustrative, medium confidence)
@ApplicationScoped
public class OrderService {
    @WithSpan("order.save")
    public void save(@SpanAttribute("tenantId") String tenantId, Order order) {
        // DynamoDB call with quarkus.dynamodb.telemetry.enabled=true -> child client span
    }
}
```

Sources: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-awssdkclients.html ; https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html ; https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/opentelemetry.html ; https://quarkus.io/version/3.40/guides/opentelemetry-tracing

## Limits and security

- Segment documents up to 64 kB; 50 indexed annotations per trace; trace data retained 30 days. Pricing: free tier, then "X-Ray charges for trace storage and retrieval" (amounts: page not recorded).
- OTLP traces endpoint limits: 5 MB uncompressed per request, 10,000 spans per request, 200 KB per span, 16 KB per resource+scope.
- "Your application can remove `X-Amzn-Trace-Id` from incoming requests to avoid issues caused by users adding trace IDs or sampling decisions".
- OTLP `headers` (for example `authorization=Bearer ...`) are credentials: take them from Secrets Manager or SSM (family rule 5). Least privilege: only the two X-Ray actions ([A2](./always-do-patterns.md#a2-execution-role-permissions)).
- PII rules: [F4](./never-do-patterns.md#f4-pii-in-trace-data).

Sources: https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html ; https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLPEndpoint.html

## Performance

- X-Ray "adds many classes" ([A4](./always-do-patterns.md#a4-memory)).
- The AWS Lambda Layer for OpenTelemetry enables only AWS SDK and HTTP instrumentation by default "To reduce Lambda cold starts"; `OTEL_INSTRUMENTATION_COMMON_DEFAULT_ENABLED=true` enables all.
- AWS: "For reduced cold starts, consider using OpenTelemetry manual instrumentation".

Sources: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals-Enable-LambdaMain.html ; https://docs.aws.amazon.com/xray/latest/devguide/xray-migration-opentelemetry.html
