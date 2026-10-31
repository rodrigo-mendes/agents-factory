---
name: tracing-quarkus-lambda-v3-40
description: "Guides distributed tracing from Quarkus 3.40 LTS Lambdas to AWS X-Ray: active tracing, quarkus-amazon-lambda-xray vs quarkus-opentelemetry, trace headers, SDK client spans, annotations. Use when adding traces to a Quarkus Lambda. Not for logging, metrics, Terraform, Powertools or Quarkus 4."
---

# Tracing Quarkus Lambda (X-Ray) 3.40

> Version lock: every claim applies to **Quarkus 3.40 LTS, patch 3.40.1.1** and **Quarkiverse quarkus-amazon-services 3.23.x**. Research date **2026-10-28**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: traces only, Lambda to X-Ray. Neighbours in the same package: [developing-quarkus-amazon-lambda-v3-40](../developing-quarkus-amazon-lambda-v3-40/SKILL.md) (handlers, SnapStart, native), [integrating-quarkus-amazon-data-v3-40](../integrating-quarkus-amazon-data-v3-40/SKILL.md) (DynamoDB client). By name only: `logging-quarkus-lambda-v3-40`, `monitoring-quarkus-lambda-v3-40`, `observing-quarkus-lambda`, `tracing-aws-xray` (X-Ray design), `provisioning-aws-xray-v6` (Terraform), `implementing-lambda-powertools-java` (Powertools tracing inside Quarkus is (unverified)). Quarkus 4 is out of scope.

## Version Context

| Item | Value | Source (fetched 2026-10-28) |
|---|---|---|
| Quarkus | 3.40 LTS, released 2026-09-30, community-maintained until 2027-09-30; patch 3.40.1.1 released 2026-10-19 | https://quarkus.io/releases |
| `quarkus-amazon-lambda-xray` | 3.40.1.1, metadata `status: "stable"`; it only registers X-Ray SDK classes for native image (`XrayBuildStep`); it is not a tracer by itself | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-xray/3.40.1.1/quarkus-amazon-lambda-xray-3.40.1.1.pom (version, name) ; https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-xray/runtime/src/main/resources/META-INF/quarkus-extension.yaml (status) ; https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-xray/deployment/src/main/java/io/quarkus/amazon/lambda/xray/XrayBuildStep.java (native registrations) |
| X-Ray SDK for Java | `aws-xray-recorder-sdk-aws-sdk-v2` 2.18.3 managed by the quarkus-bom 3.40.1.1 POM (medium confidence); AWS pages show BOM 2.11.0 as an example (source difference D1); **maintenance mode since 2026-02-25**, security fixes only, no end date | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html ; https://repo1.maven.org/maven2/io/quarkus/quarkus-bom/3.40.1.1/quarkus-bom-3.40.1.1.pom |
| `quarkus-opentelemetry` | tracing "supported and on by default"; OTel API 1.62.0, `opentelemetry-aws-sdk-2.2` 2.28.1-alpha managed by the quarkus-bom 3.40.1.1 POM (medium confidence); the 3.40 guides do not mention AWS Lambda | https://quarkus.io/version/3.40/guides/opentelemetry ; https://repo1.maven.org/maven2/io/quarkus/quarkus-bom/3.40.1.1/quarkus-bom-3.40.1.1.pom |
| Quarkiverse | quarkus-amazon-services 3.23.0 (family fact: built on Quarkus 3.40.0) | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom |
| Java 17+ trace header | system property `com.amazonaws.xray.traceHeader`, not `_X_AMZN_TRACE_ID` | https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html |

**Version-lifetime risk** (details in [register](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- The only Lambda tracing path the Quarkus 3.40 guide documents sits on an SDK in maintenance mode; for the AWS-recommended path (OpenTelemetry) no end-to-end route is documented for a Quarkus Lambda in the pages read (medium confidence, absence of evidence, M9). Say so plainly; never present either as the default.
- Quarkus 4.0.0 is "Upcoming" with no date; reject Quarkus 4 and Quarkiverse 4.0.0.Beta* content.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Ask-first decisions in depth](./blueprints/ask-first-decisions.md)
- [OTel export routes to X-Ray (C2)](./blueprints/otel-export-routes.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Lambda and API Gateway tracing facts](./blueprints/lambda-and-api-gateway-tracing.md)
- [Verification Loop](./blueprints/verification-loop.md#verification-loop)
- [Migration notes](./blueprints/migration-notes.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Set Lambda `TracingConfig` to `Mode=Active`.** The default `PassThrough` "does not send traces automatically" ([Lambda X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)). See [A1](./blueprints/always-do-patterns.md#a1-active-tracing).
- **Give the execution role `xray:PutTraceSegments` and `xray:PutTelemetryRecords`.** Lambda needs both to send trace data ([Lambda X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)). See [A2](./blueprints/always-do-patterns.md#a2-execution-role-permissions).
- **Add `io.quarkus:quarkus-amazon-lambda-xray` to a native build that uses the X-Ray SDK.** The guide: "The AWS X-Ray library is not fully compatible with GraalVM" ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)). See [A3](./blueprints/always-do-patterns.md#a3-native-build-extension).
- **Give an X-Ray-instrumented function at least 256 MB.** The guide asks for "at least the 256MB" because X-Ray "adds many classes" ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)). See [A4](./blueprints/always-do-patterns.md#a4-memory).
- **X-Ray path: attach `TracingInterceptor` to each AWS SDK v2 client.** Only instrumented clients create DynamoDB subsegments ([X-Ray SDK clients](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-awssdkclients.html)). See [A5](./blueprints/always-do-patterns.md#a5-x-ray-client-interceptor).
- **OTel path: set `quarkus.<extension>.telemetry.enabled=true` per Quarkiverse client.** The documented default is `false` ([Quarkiverse OpenTelemetry](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/opentelemetry.html)). See [A6](./blueprints/always-do-patterns.md#a6-otel-client-telemetry).
- **X-Ray path: put `tenantId` in a subsegment annotation and everything else in metadata.** Annotation keys allow alphanumerics and dots only ([X-Ray segments](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-segment.html)). See [A7](./blueprints/always-do-patterns.md#a7-x-ray-annotations).
- **OTel path: list annotation keys in the `aws.xray.annotations` span attribute.** By default span attributes become X-Ray metadata ([AWS migration](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html)). See [A8](./blueprints/always-do-patterns.md#a8-otel-annotations).
- **OTel path on Lambda: set `quarkus.otel.simple=true`.** The tracing guide names "a serverless environment" for it ([tracing guide](https://quarkus.io/version/3.40/guides/opentelemetry-tracing)). See [A9](./blueprints/always-do-patterns.md#a9-simple-span-processor).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| C1 Instrumentation stack (ADR, never a default) | A: X-Ray SDK 2.18.3 (medium confidence) (+ `quarkus-amazon-lambda-xray` for native), the only path documented by Quarkus 3.40, maintenance mode since 2026-02-25. B: `quarkus-opentelemetry`, AWS-recommended, no Lambda guidance in the Quarkus guides (medium confidence, absence of evidence, M9). Whichever stack is chosen, the X-Ray SDK is in maintenance mode since 2026-02-25. C: Powertools tracing, out of scope and (unverified) in Quarkus. See [C1](./blueprints/ask-first-decisions.md#c1-x-ray-sdk-or-opentelemetry) | "X-Ray SDK (documented, maintenance mode) or OpenTelemetry (AWS-recommended, Quarkus Lambda export route not documented)? Record the ADR." |
| C2 OTel export route to X-Ray | No route is documented end to end for a Quarkus Lambda in the pages read (medium confidence, absence of evidence, M9): UDP span exporter wiring (unverified) and AWS propagator through `quarkus.otel.propagators` (unverified); AWS Lambda Layer next to `quarkus-opentelemetry` (unverified); SigV4 on the OTLP exporter (unverified). See [C2](./blueprints/otel-export-routes.md#c2-otel-export-route) | "Which route do you prove in a PoC? None is documented for Quarkus 3.40 on Lambda." |
| C3 API Gateway type | REST API gets X-Ray and stage sampling rules; HTTP API has no X-Ray, so no API Gateway node (the trace starts at the Lambda segment). REST extension is preview. See [C3](./blueprints/ask-first-decisions.md#c3-api-gateway-type) and the [HTTP skill decisions](../developing-quarkus-amazon-lambda-http-v3-40/blueprints/ask-first-decisions.md) | "Must the API Gateway node appear in the trace? If yes a REST API is required." |
| C4 JVM with SnapStart or native | Mutually exclusive (family rule 3). Native needs the extension; on native (OS-only runtime) `_X_AMZN_TRACE_ID` is not defined and the property route is (medium confidence); SnapStart adds a `Restore` subsegment; re-initialising tracer state after restore is (unverified). See [C4](./blueprints/ask-first-decisions.md#c4-jvm-with-snapstart-or-native) | "JVM + SnapStart or native? Then apply the tracing consequences." |
| C5 Sampling | Lambda alone: 1 request/s + 5%, not configurable; upstream REST stage rules; OTel sampler in the function; Transaction Search. Remote sampler with Quarkus is (unverified). See [C5](./blueprints/ask-first-decisions.md#c5-sampling) | "Sampling target per stage? Is Transaction Search (cost) in scope?" |
| C6 Interceptor for Quarkiverse-managed clients | `quarkus.dynamodb.interceptors=<TracingInterceptor>` is an inference (medium confidence) vs a hand-built client. See [C6](./blueprints/ask-first-decisions.md#c6-interceptor-placement-for-quarkiverse-clients) | "Quarkiverse-managed clients (test option A) or hand-built?" |
| C7 `tenantId` annotation | Only an opaque, bounded identifier; at most 50 annotations are indexed per trace. See [C7](./blueprints/ask-first-decisions.md#c7-tenantid-annotation) | "Is `tenantId` opaque (no name or email)? Does the tenant population need an ADR?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Leave `TracingConfig` unset and expect traces because API Gateway sampled ([Lambda X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)) | `Mode=Active` plus the two X-Ray actions ([Lambda X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)). [F1](./blueprints/never-do-patterns.md#f1-passthrough-default) |
| Expect an API Gateway node from an HTTP API with `quarkus-amazon-lambda-http` ([AWS](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html)) | A REST API stage with X-Ray tracing; trade-offs in Ask First C3 ([AWS](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-xray.html)). [F2](./blueprints/never-do-patterns.md#f2-http-api-node) |
| Read `_X_AMZN_TRACE_ID` on Java 17+ managed runtimes ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)) | `System.getProperty("com.amazonaws.xray.traceHeader")` on Java 17+ ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)); native builds: see Ask First C4. [F3](./blueprints/never-do-patterns.md#f3-env-var-trace-header) |
| Put PII or secrets in annotations, metadata or span attributes, or turn `quarkus.otel.traces.eusp.enabled` on ([X-Ray SDK](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java.html)) | An opaque `tenantId` annotation; keep `eusp.enabled=false` ([tracing guide](https://quarkus.io/version/3.40/guides/opentelemetry-tracing)). [F4](./blueprints/never-do-patterns.md#f4-pii-in-trace-data) |
| Name annotation keys `tenant_id` (underscore, hyphen or space) ([X-Ray SDK](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-segment.html)) | `tenantId` or `tenant.id` ([X-Ray SDK](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-segment.html)). [F5](./blueprints/never-do-patterns.md#f5-invalid-annotation-keys) |
| Annotate the Lambda function segment ([Lambda X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)) | Begin a subsegment and annotate it ([Lambda X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)); X-Ray SDK is in maintenance mode since 2026-02-25. [F6](./blueprints/never-do-patterns.md#f6-function-segment-annotations) |
| Change tracing mode on a published version ([Lambda X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)) | Set `Mode=Active` before `publish-version`, then move the alias ([Lambda Java tracing](https://docs.aws.amazon.com/lambda/latest/dg/java-tracing.html)). [F7](./blueprints/never-do-patterns.md#f7-published-version-tracing-mode) |
| Set a sampling rule for `AWS::Lambda::Function` expecting Lambda to obey ([Lambda X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)) | A rule on the REST API stage, service type `AWS::ApiGateway::Stage` ([API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-configuring-xray-sampling-rules.html)). [F8](./blueprints/never-do-patterns.md#f8-lambda-sampling-rules) |
| Send Quarkus's default gRPC OTLP export to the X-Ray traces endpoint ([CloudWatch OTLP](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLPEndpoint.html)) | Take the route decision to Ask First C2 ([guide](https://quarkus.io/version/3.40/guides/opentelemetry)). [F9](./blueprints/otel-export-routes.md#f9-grpc-otlp-to-x-ray-endpoint) |
| Expect traces from MSK, self-managed Kafka, Amazon MQ or DocumentDB event source mappings ([Lambda X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)) | SQS or an API Gateway REST API as the traced entry point ([Lambda X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)). [F10](./blueprints/never-do-patterns.md#f10-unsupported-event-source-mappings) |

Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Lambda tracing config | `--tracing-config Mode=Active` (CLI). `Tracing: Active` (SAM) is the Quarkus guide's example only; IaC for this family is Terraform (`provisioning-aws-xray-v6`) | https://quarkus.io/version/3.40/guides/aws-lambda |
| Execution role actions | `xray:PutTraceSegments`, `xray:PutTelemetryRecords` (managed policy `AWSXRayDaemonWriteAccess`) | https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html |
| Lambda sampling (Active, no upstream decision) | 1 request/s + 5% of additional requests, not configurable | https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html |
| Annotation limits | key alphanumeric plus dot, value up to 1,000 characters, 50 indexed per trace | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-segment.html |
| `quarkus.<ext>.telemetry.enabled` | documented default `false`; build-time or runtime not marked per key (medium confidence) | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/opentelemetry.html |
| `quarkus.otel.simple` | documented default `false` | https://quarkus.io/version/3.40/guides/opentelemetry |
| `quarkus.otel.traces.sampler` / `.arg` | `parentbased_always_on` / `1.0d` | https://quarkus.io/version/3.40/guides/opentelemetry |
| `quarkus.otel.traces.eusp.enabled` | documented default `false` (End User attributes are PII) | https://quarkus.io/version/3.40/guides/opentelemetry-tracing |
| `quarkus.otel.exporter.otlp.traces.protocol` | documented default `grpc` | https://quarkus.io/version/3.40/guides/opentelemetry |
| Trace retention / segment size | 30 days / up to 64 kB | https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html |

## External Resources

All fetched 2026-10-28.

- Quarkus AWS Lambda guide (X-Ray section): https://quarkus.io/version/3.40/guides/aws-lambda
- Quarkus OpenTelemetry guides: https://quarkus.io/version/3.40/guides/opentelemetry , https://quarkus.io/version/3.40/guides/opentelemetry-tracing
- Quarkiverse OpenTelemetry (3.23.x): https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/opentelemetry.html
- Lambda and X-Ray: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html
- X-Ray SDK maintenance timeline: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html
- API Gateway REST vs HTTP: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
