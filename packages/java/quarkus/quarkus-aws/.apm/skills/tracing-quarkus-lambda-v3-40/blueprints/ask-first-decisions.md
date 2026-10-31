# Ask-First Decisions

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Every decision here is put to the user; none has a default. C2 (OTel export route) is in [otel-export-routes.md](./otel-export-routes.md#c2-otel-export-route).

## Contents

- [C1. X-Ray SDK or OpenTelemetry](#c1-x-ray-sdk-or-opentelemetry)
- [C3. API Gateway type](#c3-api-gateway-type)
- [C4. JVM with SnapStart or native](#c4-jvm-with-snapstart-or-native)
- [C5. Sampling](#c5-sampling)
- [C6. Interceptor placement for Quarkiverse clients](#c6-interceptor-placement-for-quarkiverse-clients)
- [C7. tenantId annotation](#c7-tenantid-annotation)

## C1. X-Ray SDK or OpenTelemetry

AWS X-Ray SDKs and daemon are in maintenance mode since 2026-02-25: "AWS will limit X-Ray SDK and Daemon releases to address security issues only"; the end date is "N/A"; "We recommend to migrate to OpenTelemetry" ([timeline](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html)). Never present either option as the default; record an ADR.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. X-Ray SDK 2.18.3 (medium confidence) (+ `quarkus-amazon-lambda-xray` for native) | The only Lambda tracing path documented by Quarkus 3.40; "there is no additional configuration required to use the X-Ray SDK" once active tracing is on | Maintenance mode: security fixes only, no new features | Native build needed now, migration debt accepted in the ADR |
| B. `quarkus-opentelemetry` | AWS-recommended; Quarkus tracing "supported and on by default"; Quarkiverse SDK client instrumentation; documented to work in native for manual instrumentation | No Lambda guidance in the 3.40 guides; the export route to X-Ray is not documented end to end in the pages read (medium confidence, absence of evidence, M9) ([C2](./otel-export-routes.md#c2-otel-export-route)) | New system expected to outlive the 3.40 LTS window; a PoC of the export route is accepted |
| C. Powertools for AWS Lambda (Java) tracing | Lambda-specific helpers | "an opinionated thin wrapper for AWS X-Ray Java SDK" (same maintenance status); the page does not mention Quarkus, so compatibility is (unverified) | Out of scope: see `implementing-lambda-powertools-java` |

- JVM-only X-Ray use without `quarkus-amazon-lambda-xray` (SDK module added directly) is an option the guide does not cover (medium confidence).
- Ask: "X-Ray SDK (documented by Quarkus, maintenance mode since 2026-02-25) or OpenTelemetry (AWS-recommended, Quarkus Lambda export route not documented)? Record the choice in an ADR."

Sources: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html ; https://quarkus.io/version/3.40/guides/aws-lambda ; https://quarkus.io/version/3.40/guides/opentelemetry ; https://docs.aws.amazon.com/powertools/java/latest/core/tracing/

## C3. API Gateway type

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| REST API + `quarkus-amazon-lambda-rest` | API Gateway node, stage-level sampling rules, full "API GW -> Lambda -> DynamoDB" trace | REST features cost more; the extension is "preview"; its generated `sam.native.yaml` uses the deprecated `Runtime: provided` (never copy it) | The API Gateway node must appear in the trace |
| HTTP API + `quarkus-amazon-lambda-http` | Lower price, JWT authorizer | X-Ray tracing is REST only: no API Gateway segment, no stage rules; the trace starts at the `AWS::Lambda` segment | The Lambda to DynamoDB part is enough |

AWS: "API Gateway supports X-Ray tracing for all API Gateway REST API endpoint types"; the feature table says X-Ray tracing REST "Yes", HTTP "No". Sampling rules for a REST stage use service type `AWS::ApiGateway::Stage`, service name `{api-name}/{stage-name}`. HTTP API decisions of the sibling skill: [ask-first-decisions](../../developing-quarkus-amazon-lambda-http-v3-40/blueprints/ask-first-decisions.md).
Ask: "Must the API Gateway node appear in the trace? If yes, a REST API is required."

Sources: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html ; https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-xray.html ; https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-configuring-xray-sampling-rules.html

## C4. JVM with SnapStart or native

JVM + SnapStart and native are mutually exclusive (family rule 3; build and runtime choice: [developing-quarkus-amazon-lambda-v3-40](../../developing-quarkus-amazon-lambda-v3-40/SKILL.md)). Tracing consequences:

- Native + X-Ray SDK needs `quarkus-amazon-lambda-xray` ([A3](./always-do-patterns.md#a3-native-build-extension)).
- `_X_AMZN_TRACE_ID` "is not defined for OS-only runtimes", and for Java 17+ managed runtimes the header is in `com.amazonaws.xray.traceHeader` ([F3](./never-do-patterns.md#f3-env-var-trace-header), limited to managed runtimes). For native, reading the property is (medium confidence): the X-Ray SDK reading it inside a native Quarkus function is not confirmed. The Quarkus poll loop at 3.40.1.1 sets that property from the `Lambda-Runtime-Trace-Id` header and never clears it; that the loop is the one native (custom runtime) functions use, while managed Java runtimes get the property from the AWS runtime, is (medium confidence).
- SnapStart functions get a `Restore` subsegment (snapshot restore, runtime load, after-restore hooks). SnapStart runs only on published versions, and tracing mode cannot change on a published version ([F7](./never-do-patterns.md#f7-published-version-tracing-mode)). The Quarkus 3.40 SnapStart guide says nothing about tracing. Whether tracer, exporter or ID-generator state captured in the snapshot needs re-initialising after restore is (unverified).
- The AWS Lambda Layer for OpenTelemetry lists only Java managed runtimes; native is not covered (medium confidence, absence of evidence).
- Ask: "JVM + SnapStart or native (ADR, family rule 3)? Then apply the tracing consequences above."

Sources: https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html ; https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html ; https://quarkus.io/version/3.40/guides/aws-lambda-snapstart ; https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AbstractLambdaPollLoop.java

## C5. Sampling

| Option | Facts |
|---|---|
| A. Lambda Active tracing, no upstream decision | "The sampling rate is 1 request per second and 5 percent of additional requests. You can't configure the X-Ray sampling rate for your functions." |
| B. Upstream decision | "Typically, an upstream service, such as Amazon API Gateway ... decides whether incoming requests should be traced ... Lambda uses that header". REST stage rules: Reservoir, Rate 0-100, service type `AWS::ApiGateway::Stage` |
| C. OTel sampler in the function | `quarkus.otel.traces.sampler` default `parentbased_always_on` ("build-time only" per the tracing guide); `quarkus.otel.traces.sampler.arg` default `1.0d` (runtime; for `traceidratio` samplers); a CDI `Sampler` producer is supported. X-Ray remote sampling is "Supported in OTel Java" (`AwsXrayRemoteSampler`, `io.opentelemetry.contrib:opentelemetry-aws-xray`); use with Quarkus is (unverified) |
| D. Transaction Search | "enables the capture of trace spans for Lambda function invocation without sampling"; cost: page not recorded |

Ask: "Sampling target per API stage (reservoir/rate)? Is Transaction Search (cost) in scope?"

Sources: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html ; https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-configuring-xray-sampling-rules.html ; https://quarkus.io/version/3.40/guides/opentelemetry-tracing ; https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals-Enable-LambdaMain.html

## C6. Interceptor placement for Quarkiverse clients

| Option | Notes |
|---|---|
| A. `quarkus.dynamodb.interceptors=com.amazonaws.xray.interceptors.TracingInterceptor` | Quarkiverse 3.23.x documents `quarkus.dynamodb.interceptors` ("List of execution interceptors that will have access to read and modify the request and response objects"; classes implementing `ExecutionInterceptor`, loaded via CDI first, no-arg constructor fallback). Using it for the X-Ray interceptor is an inference (medium confidence) |
| B. Hand-built client | As in [A5](./always-do-patterns.md#a5-x-ray-client-interceptor); full control, bypasses the managed client |
| C. `aws-xray-recorder-sdk-aws-sdk-v2-instrumentor` | Instruments all v2 clients; it is not a dependency of `quarkus-amazon-lambda-xray` and `XrayBuildStep` does not cover its native registration (medium confidence) |

Ask: "Are the clients Quarkiverse-managed (prefer A after a test; see [integrating-quarkus-amazon-data-v3-40](../../integrating-quarkus-amazon-data-v3-40/SKILL.md)) or hand-built (B)?"

Sources: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html (read to 100,000 of 104,004 characters) ; https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-awssdkclients.html

## C7. tenantId annotation

Facts: up to 50 annotations indexed per trace; key alphanumeric plus dot; value up to 1,000 characters; searchable with `annotation[key]` filter expressions. Family rule 7: no PII, no unbounded tenant cardinality in metric dimensions without an ADR.
Ask: "Is `tenantId` an opaque identifier (no name or email)? Does the tenant population need an ADR?"

Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-segment.html
