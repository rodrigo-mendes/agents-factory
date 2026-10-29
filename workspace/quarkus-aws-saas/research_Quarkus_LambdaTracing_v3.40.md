# Research: Distributed tracing for Quarkus 3.40 LTS (3.40.1.1) AWS Lambda functions with AWS X-Ray

Unit U12 of the quarkus-aws-saas family. Future skill: `tracing-quarkus-lambda-v3-40` (package `quarkus-aws`).
Source item: "observability in code: traces (X-Ray end to end API GW -> Lambda -> DynamoDB)".
Family facts applied as given: `workspace/quarkus-aws-saas/_family_facts_v3.40.md`, `workspace/_family_facts_v3.40.md`.
Family rules applied as given: `workspace/quarkus-aws-saas/_family_rules_v3.40.md` (rules 3, 7, 9-12 in particular), `workspace/_family_rules_v3.40.md`, and `.claude/skills/building-agent-packages/blueprints/policy/` (evidence rule, tag notation).

All pages were read on **2026-10-28** with the WebFetch tool. Text in double quotes was returned verbatim by the tool. The tool limits verbatim quotes on some pages to about 125 characters; there the wording is a tool paraphrase and is marked "(paraphrase)". Partly read pages are listed as coverage limits (L-ids) in Research Gaps.

Out of scope (names only): logging (U11), metrics (U13), X-Ray infrastructure design and Terraform (`tracing-aws-xray`, `provisioning-aws-xray-v6`), Powertools tracing (`implementing-lambda-powertools-java`), Quarkus 4.

---

## Metadata

```yaml
Full_Name: Distributed tracing for Quarkus AWS Lambda functions - quarkus-amazon-lambda-xray (AWS X-Ray SDK for Java) and quarkus-opentelemetry, exporting to AWS X-Ray
Target_Version: Quarkus 3.40 LTS, patch 3.40.1.1 (quarkus-amazon-lambda-xray 3.40.1.1); Quarkiverse quarkus-amazon-services 3.23.x (3.23.0)
Release_Date: Quarkus 3.40 released 2026-09-30; 3.40.1.1 released 2026-10-19 (family fact, https://quarkus.io/releases)
Support_Status: Quarkus 3.40 LTS, community-maintained until 2027-09-30 (family fact). AWS X-Ray SDKs and daemon in maintenance mode since 2026-02-25 (security fixes only) (https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html)
Primary_Docs: https://quarkus.io/version/3.40/guides/aws-lambda (section "Tracing with AWS XRay and GraalVM") ; https://quarkus.io/version/3.40/guides/opentelemetry ; https://quarkus.io/version/3.40/guides/opentelemetry-tracing
Secondary_Docs: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/opentelemetry.html ; https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html ; https://docs.aws.amazon.com/lambda/latest/dg/java-tracing.html ; https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html
Registry: https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-xray/3.40.1.1/quarkus-amazon-lambda-xray-3.40.1.1.pom ; https://repo1.maven.org/maven2/io/quarkus/quarkus-bom/3.40.1.1/quarkus-bom-3.40.1.1.pom
Official_Repo: https://github.com/quarkusio/quarkus/tree/3.40.1.1/extensions/amazon-lambda-xray
Research_Date: 2026-10-28
Domain_Complexity: Complex
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 6
Unverified_Count: 12
Irresolvable_Count: 0
Research_Quality_Score: 87%   # ~95 sourced claims; 12 unverified; 0 irresolvable -> (95-12)/95
Execution_Notes: >
  Caller constraints honoured: no sub-agents (P2.parallel skipped, all pages fetched by this agent),
  no plan mode (scope approval relayed by the caller from PIPELINE_STATE.md#approvals, 2026-10-28;
  recorded here as a relay, not as an approval by this agent), file written directly instead of via
  research-synthesizer.
```

---

## Executive Summary

Quarkus 3.40 documents exactly one Lambda-specific tracing path. The AWS Lambda guide's section "Tracing with AWS XRay and GraalVM" says that if you build native images and want X-Ray tracing you add `quarkus-amazon-lambda-xray`, because "The AWS X-Ray library is not fully compatible with GraalVM". It also says to turn on tracing with `--tracing-config Mode=Active` (in `manage.sh`) or `Tracing: Active` (SAM), and to use "at least the 256MB" of memory (https://quarkus.io/version/3.40/guides/aws-lambda, read 2026-10-28). The extension's source at tag 3.40.1.1 does only native-image work. Its single build step `XrayBuildStep` registers X-Ray SDK classes, including `com.amazonaws.xray.interceptors.TracingInterceptor`, for runtime initialisation and reflection, adds the SDK's JSON resources (default sampling rules, operation whitelist), and registers Apache HTTP client proxies (https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-xray/deployment/src/main/java/io/quarkus/amazon/lambda/xray/XrayBuildStep.java). Its POM pulls in `com.amazonaws:aws-xray-recorder-sdk-aws-sdk-v2`, which `quarkus-bom` 3.40.1.1 manages at 2.18.3, plus `quarkus-apache-httpclient`. The extension metadata says `status: "stable"`. The second option is `quarkus-opentelemetry`, where tracing is "supported and on by default". Its guides do not mention AWS Lambda at all. The only serverless hint is `quarkus.otel.simple=true`, "e.g. in a serverless environment", which exports spans as they end (https://quarkus.io/version/3.40/guides/opentelemetry-tracing). Quarkiverse amazon-services 3.23.x documents OpenTelemetry instrumentation of AWS SDK v2 clients. The `quarkus-opentelemetry` extension "will automatically inject an interceptor", but only into clients with `quarkus.<extension>.telemetry.enabled=true`, which defaults to `false` (https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/opentelemetry.html).

What changed around Quarkus 3.40 is the AWS side, not the Quarkus API. On **2026-02-25** the AWS X-Ray SDKs and daemon entered maintenance mode: "AWS will limit X-Ray SDK and Daemon releases to address security issues only". AWS gives no end date and says "We recommend to migrate to OpenTelemetry" (https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html). So the only Lambda tracing path that Quarkus documents is built on an SDK that gets security fixes only. The path AWS recommends (OpenTelemetry) has no Lambda guidance in the Quarkus 3.40 guides. Choosing between them is therefore an Ask-First / ADR decision (C1), never a default. Platform facts also limit the "API GW -> Lambda -> DynamoDB" goal. Lambda's default mode is `PassThrough`, which "does not send traces automatically" (https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html). For Java 17+, Lambda passes the trace header in the system property `com.amazonaws.xray.traceHeader`, not in `_X_AMZN_TRACE_ID`. `_X_AMZN_TRACE_ID` is not defined at all on OS-only runtimes (https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html). Quarkus's own poll loop sets that same system property from the `Lambda-Runtime-Trace-Id` header (source at tag 3.40.1.1). Finally, API Gateway **HTTP APIs do not support X-Ray tracing**; only REST APIs do (https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html). `quarkus-amazon-lambda-http` targets HTTP APIs (family fact 25), so a trace that includes an API Gateway node requires a REST API, that is the preview `quarkus-amazon-lambda-rest`.

The three critical patterns: (1) set Lambda `TracingConfig` `Mode=Active` and give the execution role `xray:PutTraceSegments` and `xray:PutTelemetryRecords`; without that, no segments are sent whatever the code does. (2) Instrument the AWS SDK v2 clients explicitly. On the X-Ray path that means `TracingInterceptor` (in native it also needs `quarkus-amazon-lambda-xray`). On the OTel path it means `quarkus.<client>.telemetry.enabled=true` plus `quarkus-opentelemetry`. Without it there are no DynamoDB subsegments. (3) Record only bounded, non-PII keys such as `tenantId` as searchable annotations. Annotation keys are alphanumeric plus dot only, at most 50 annotations per trace are indexed, and "Anyone that you grant read access to X-Ray can view this data" (https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java.html). The domain complexity is **Complex**: two instrumentation stacks with different support status, two build modes (JVM/SnapStart vs native, family rule 3), three AWS services in the trace path with different tracing support, and security/PII and sampling concerns.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (versioned Quarkus 3.40 page, source/registry at tag 3.40.1.1, Quarkiverse 3.23.x page, or official AWS service page read 2026-10-28; AWS pages are treated as official platform pages, as in U1) | 🟡 Medium (partly read page, legacy/undated ADOT page, inference that combines two sources) | 🔴 Low (unverified, verify before use)
> Family evidence rule applied: a single versioned official source is enough for High. The template's rule that one source means Medium is superseded by `policy/evidence-rule.md`.

### ✅ Mandatory Patterns

**A1. Turn on Lambda active tracing (`TracingConfig` `Mode=Active`); the default `PassThrough` sends nothing**
> Confidence: 🟢 High | [✓✓ Triangulated | Quarkus 3.40 aws-lambda guide (2026-10-28) + Lambda services-xray (2026-10-28) + Lambda java-tracing (2026-10-28)]
- Why: "With `Active` tracing, Lambda automatically creates trace segments for Event Function invocations and sends them to X-Ray. `PassThrough` mode, on the other hand, simply propagates the tracing context to downstream services." "If you do not have `Active` tracing turned on, Lambda defaults to `PassThrough` tracing mode." In PassThrough, Lambda "does not send traces automatically. This is true even if the tracing header contains a decision to sample the request." The Quarkus guide gives the same switch: `--tracing-config Mode=Active` in `manage.sh` `cmd_create()`, or `Tracing: Active` in SAM (paraphrase of the guide section). The infrastructure itself is written in Terraform (family rule 4) and is out of scope here (`provisioning-aws-xray-v6`, names only).
- Code (artifact contract value, Quarkus 3.40.1.1 function.zip):
  ```bash
  # Representative - adapt to your environment (Quarkus 3.40.1.1 function, any runtime)
  aws lambda update-function-configuration --function-name my-function \
    --tracing-config Mode=Active
  # Expected: "TracingConfig": {"Mode": "Active"} in the response
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html (2026-10-28); https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28)

**A2. Give the execution role the X-Ray write permissions**
> Confidence: 🟢 High | [✓✓ Triangulated | Lambda services-xray (2026-10-28) + Lambda java-tracing (2026-10-28)]
- Why: "Lambda needs the following permissions to send trace data to X-Ray": `xray:PutTraceSegments` and `xray:PutTelemetryRecords`. "These permissions are included in the AWSXRayDaemonWriteAccess managed policy." The console adds them when you turn tracing on there. IaC must add them itself.
- Code (permission list only; the IAM resources live in `provisioning-aws-*-v6`):
  ```text
  # Lambda execution role - tracing actions (Quarkus 3.40.1.1 function)
  xray:PutTraceSegments
  xray:PutTelemetryRecords
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html (2026-10-28)

**A3. Native build + X-Ray SDK: add `io.quarkus:quarkus-amazon-lambda-xray`**
> Confidence: 🟢 High | [✓✓ Triangulated | Quarkus 3.40 aws-lambda guide (2026-10-28) + XrayBuildStep.java at tag 3.40.1.1 (2026-10-28) + POM 3.40.1.1 (2026-10-28)]
- Why: the guide says "If you are building native images, and want to use AWS X-Ray Tracing with your lambda" you need this dependency, and "The AWS X-Ray library is not fully compatible with GraalVM". At tag 3.40.1.1 the build step registers `AWSXRay`, `AWSXRayRecorder`, `TracingInterceptor`, `LocalizedSamplingStrategy` and `ThreadLocalStorage` as runtime-initialised classes. It also registers the X-Ray entity and sampling classes for reflection, includes `DefaultOperationParameterWhitelist.json`, `DefaultSamplingRules.json` and `sdk.properties`, and adds Apache HTTP client proxies. The POM ("Allow X-Ray to run with Quarkus Lambda support") depends on `quarkus-amazon-lambda-common`, `quarkus-core`, `quarkus-apache-httpclient`, `com.amazonaws:aws-xray-recorder-sdk-aws-sdk-v2` and `org.jboss.logging:commons-logging-jboss-logging`.
- Code (Quarkus 3.40.1.1; version from the Quarkus platform BOM):
  ```xml
  <!-- Quarkus 3.40.1.1 - X-Ray SDK for Java in a native Lambda -->
  <dependency>
    <groupId>io.quarkus</groupId>
    <artifactId>quarkus-amazon-lambda-xray</artifactId>
  </dependency>
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28); https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-xray/3.40.1.1/quarkus-amazon-lambda-xray-3.40.1.1.pom (2026-10-28)

**A4. Give an X-Ray-instrumented Quarkus Lambda at least 256 MB, and the same memory for JVM and native**
> Confidence: 🟢 High | single versioned source (Quarkus 3.40 aws-lambda guide, 2026-10-28)
- Why: the guide says X-Ray "adds many classes" to the distribution, so use "at least the 256MB" memory size. It also recommends the same memory setting for native and non-native builds so that performance comparisons are fair (paraphrase).
- Code (artifact contract value):
  ```text
  # Lambda function configuration (Quarkus 3.40.1.1 + quarkus-amazon-lambda-xray)
  MemorySize >= 256   # identical for the JVM and native variants
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28)

**A5. X-Ray path: instrument AWS SDK v2 clients with `com.amazonaws.xray.interceptors.TracingInterceptor`**
> Confidence: 🟢 High | [✓✓ Triangulated | X-Ray SDK for Java "AWS SDK calls" page (2026-10-28) + X-Ray to OTel Java migration page (2026-10-28)]
- Why: "Include the `aws-xray-recorder-sdk-aws-sdk-v2 module` instead, then instrument individual clients by configuring them with a `TracingInterceptor`." With an instrumented DynamoDB client "the SDK adds the table name to the segment", so each table becomes its own service-map node. The alternative `aws-xray-recorder-sdk-aws-sdk-v2-instrumentor` instruments every v2 client automatically. Using the Quarkiverse-managed client instead is covered in C6.
- Code (plain AWS SDK v2 builder as in the AWS page; Quarkus 3.40.1.1 with the `aws-xray-recorder-sdk-aws-sdk-v2` 2.18.3 from quarkus-bom):
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
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-awssdkclients.html (2026-10-28); https://docs.aws.amazon.com/xray/latest/devguide/xray-migration-opentelemetry.html (2026-10-28)

**A6. OTel path with Quarkiverse 3.23.x clients: set `quarkus.<extension>.telemetry.enabled=true` (default `false`)**
> Confidence: 🟢 High | [✓✓ Triangulated | Quarkiverse 3.23.x OpenTelemetry page (2026-10-28) + Quarkiverse 3.23.x DynamoDB page (2026-10-28)]
- Why: "Adding the `quarkus-opentelemetry` extension will automatically inject an interceptor" into clients that opt in, "by setting the configuration property `quarkus.<extension>.telemetry.enabled` to true. This setting is set to `false` by default." DynamoDB: `quarkus.dynamodb.telemetry.enabled`, env `QUARKUS_DYNAMODB_TELEMETRY_ENABLED`: "OpenTelemetry AWS SDK instrumentation will be enabled if the OpenTelemetry extension is present and this value is true." Whether this key is fixed at build time is not marked per key on the page (see M3). "It is not necessary to wrap Sqs or Bedrock Runtime clients." `quarkus-bom` 3.40.1.1 manages `io.opentelemetry.instrumentation:opentelemetry-aws-sdk-2.2` at 2.28.1-alpha.
- Code (Quarkus 3.40.1.1 + quarkus-amazon-services 3.23.0):
  ```properties
  # Quarkus 3.40.1.1 / Quarkiverse amazon-services 3.23.x - requires io.quarkus:quarkus-opentelemetry
  quarkus.dynamodb.telemetry.enabled=true
  ```
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/opentelemetry.html (2026-10-28); https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html (2026-10-28, chars 0-100000 of 104004)

**A7. Put searchable tenant context in annotations that follow the X-Ray key rules; keep everything else as metadata**
> Confidence: 🟢 High | [✓✓ Triangulated | X-Ray SDK for Java annotations page (2026-10-28) + X-Ray concepts (2026-10-28)]
- Why: "Annotations are key-value pairs with string, number, or Boolean values. Annotations are indexed for use with filter expressions." Keys: "up to 500 alphanumeric characters. You cannot use spaces or symbols other than a dot or period ( . )". Values: "up to 1,000 Unicode characters". "X-Ray indexes up to 50 annotations per trace." Metadata is "not indexed". In Lambda you add data to subsegments you create: "You can't access the function segment directly" (services-xray). Family rule 7 allows `tenantId` in telemetry (no PII). Whether the tenant set is bounded is C7.
- Code (X-Ray SDK path; Quarkus 3.40.1.1; method bodies are illustrative (medium confidence)):
  ```java
  // Quarkus 3.40.1.1 + X-Ray SDK for Java 2.18.3
  import com.amazonaws.xray.AWSXRay;
  import com.amazonaws.xray.entities.Subsegment;

  Subsegment sub = AWSXRay.beginSubsegment("## OrderService.save");
  try {
      sub.putAnnotation("tenantId", tenantId);       // indexed, alphanumeric key, bounded value
      sub.putMetadata("order", "itemCount", count);   // not indexed, no PII
      repository.save(order);
  } catch (RuntimeException e) {
      sub.addException(e);
      throw e;
  } finally {
      AWSXRay.endSubsegment();
  }
  ```
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-segment.html (2026-10-28); https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html (2026-10-28)

**A8. OTel path: map the tenant attribute to an X-Ray annotation with `aws.xray.annotations`**
> Confidence: 🟢 High | [✓✓ Triangulated | X-Ray migration overview (2026-10-28) + X-Ray to OTel Java migration (2026-10-28)]
- Why: "By default, OpenTelemetry span attributes are converted to metadata in X-Ray raw data. To convert specific attributes to annotations instead, add their keys to the `aws.xray.annotations` attributes list." "Server Spans convert to X-Ray segments. Other Spans convert to X-Ray sub-segments."
- Code (OTel API as in the AWS page; `Tracer` injection as in the Quarkus 3.40 tracing guide):
  ```java
  // Quarkus 3.40.1.1 + quarkus-opentelemetry (OTel API 1.62.0 per quarkus-bom)
  import io.opentelemetry.api.common.AttributeKey;
  import io.opentelemetry.api.trace.Span;
  import io.opentelemetry.api.trace.Tracer;
  import io.opentelemetry.context.Scope;
  import jakarta.inject.Inject;
  import java.util.List;

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
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html (2026-10-28); https://docs.aws.amazon.com/xray/latest/devguide/xray-migration-opentelemetry.html (2026-10-28); https://quarkus.io/version/3.40/guides/opentelemetry-tracing (2026-10-28)

**A9. OTel path on Lambda: export each span as it ends (`quarkus.otel.simple=true`), not in batches**
> Confidence: 🟢 High | [✓✓ Triangulated | Quarkus 3.40 opentelemetry-tracing guide (2026-10-28) + Quarkus 3.40 opentelemetry config reference (2026-10-28) + AWS OTel Lambda manual instrumentation (2026-10-28)]
- Why: Quarkus describes `quarkus.otel.simple` (default `false`) as "Should we use simple processor for spans and log records. This will disable batch processing and the exporter will send telemetry data right away", and the tracing guide names "a serverless environment" as the use case. AWS's manual OTel Lambda recipe also asks for "A Simple Span Processor". The batch processor's defaults are `quarkus.otel.bsp.schedule.delay` `5S` and `quarkus.otel.bsp.export.timeout` `30S`. Why a batch can be lost when Lambda freezes the environment is not stated on these pages (U5).
- Code:
  ```properties
  # Quarkus 3.40.1.1 - quarkus-opentelemetry on AWS Lambda
  quarkus.otel.simple=true
  ```
- Source: https://quarkus.io/version/3.40/guides/opentelemetry-tracing (2026-10-28); https://quarkus.io/version/3.40/guides/opentelemetry (2026-10-28); https://docs.aws.amazon.com/xray/latest/devguide/xray-migration-opentelemetry.html (2026-10-28)

### ⚠️ Conditional Patterns

**C1. Instrumentation stack: X-Ray SDK for Java (`quarkus-amazon-lambda-xray`) vs OpenTelemetry (`quarkus-opentelemetry`) - ADR required**
> Confidence: 🟢 High for each fact; the recommendation is the user's
- Options: (A) X-Ray SDK for Java 2.18.3 (+ `quarkus-amazon-lambda-xray` for native); (B) `quarkus-opentelemetry` with an X-Ray-compatible export (C2); (C) Powertools for AWS Lambda (Java) tracing, which is out of scope and only a pointer: "an opinionated thin wrapper for AWS X-Ray Java SDK" (https://docs.aws.amazon.com/powertools/java/latest/core/tracing/, 2026-10-28). The page does not mention Quarkus, so Quarkus compatibility is (unverified) (U10). See `implementing-lambda-powertools-java`.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A X-Ray SDK | The only Lambda tracing path documented by Quarkus 3.40 (native support via the extension); X-Ray SDK needs no extra configuration in Lambda once active tracing is on ("there is no additional configuration required to use the X-Ray SDK", AWS migration page) | Maintenance mode since 2026-02-25: security fixes only, no new features; AWS "recommend[s] to migrate to OpenTelemetry" | Short-lived system, native build required now, accepted migration debt in an ADR |
  | B OpenTelemetry | AWS-recommended standard ("It is recommended to adopt OpenTelemetry"); Quarkus tracing "supported and on by default"; Quarkiverse SDK instrumentation; works in native per the tracing guide's manual-instrumentation section | No Lambda guidance in Quarkus 3.40 guides; the export route to X-Ray from a Quarkus Lambda is not documented end to end (C2, U1-U4) | New system expected to outlive the 3.40 LTS window; team accepts a PoC of the export route |
  | C Powertools | Lambda-specific helpers | Wraps the X-Ray SDK (same maintenance status); Quarkus not mentioned | Out of scope here |

- Agent: "Ask user: X-Ray SDK (documented by Quarkus, maintenance mode since 2026-02-25) or OpenTelemetry (AWS-recommended, Quarkus Lambda export route not documented)? Record the choice in an ADR."
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html (2026-10-28); https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html (2026-10-28); https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28); https://quarkus.io/version/3.40/guides/opentelemetry (2026-10-28)

**C2. OTel export route from a Quarkus Lambda to X-Ray**
> Confidence: 🟡 Medium (each route's AWS facts are High; their combination with Quarkus is not documented)
- Options:
  - (a) **X-Ray UDP span exporter to Lambda's X-Ray endpoint.** AWS's manual Lambda recipe uses `software.amazon.distro.opentelemetry:aws-distro-opentelemetry-xray-udp-span-exporter:0.1.0` with a Simple Span Processor, a parent-based always-on sampler, `LambdaResource`, and `AwsXrayLambdaPropagator` (`io.opentelemetry.contrib:opentelemetry-aws-xray-propagator`). Quarkus accepts `quarkus.otel.traces.exporter` = "the full qualified name of a class implementing `io.opentelemetry.sdk.trace.export.SpanExporter`" (build-time property) and `quarkus.otel.propagators` = values "from `PropagatorType` or the full qualified name of a class implementing `io.opentelemetry.context.propagation.TextMapPropagator`". Wiring the AWS exporter and propagator into Quarkus this way is (unverified) (U1, U2). The contrib artifacts are not managed by quarkus-bom 3.40.1.1, so you would pin versions yourself (see L3).
  - (b) **AWS Lambda Layer for OpenTelemetry** (`AWS_LAMBDA_EXEC_WRAPPER=/opt/otel-instrument`, policy `CloudWatchLambdaApplicationSignalsExecutionRolePolicy`; for tracing only, `OTEL_AWS_APPLICATION_SIGNALS_ENABLED=false`). AWS marks it "(Recommended)" in the migration guide. The ADOT page lists Java 11, 17 and 21 runtimes (medium confidence, undated page) and does not mention `provided.al2023` or GraalVM native, so native is not covered (medium confidence, absence of evidence). How the layer interacts with `quarkus-opentelemetry`'s own SDK, which would mean two SDKs, is (unverified) (U3). The legacy ADOT Java wrapper layer "describes the legacy approach" and supports Java 8, 11 and 17 (medium confidence).
  - (c) **OTLP to the CloudWatch/X-Ray traces endpoint** `https://xray.<region>.amazonaws.com/v1/traces`. It needs SigV4 ("The endpoint authenticates callers using Signature 4 authentication") and HTTP only ("doesn't support gRPC"), and "Make sure Transaction Search is enabled before you use the OTLP Endpoint for traces". The Quarkus 3.40 OTel guide documents headers but no SigV4 signing, so direct export from the Quarkus OTLP exporter is (unverified) (U4). AWS documents collector-less export only "using the AWS Distro for OpenTelemetry (ADOT) SDK".
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | (a) UDP exporter | No layer, no collector; AWS states "For reduced cold starts, consider using OpenTelemetry manual instrumentation" | Exporter 0.1.0 and contrib artifacts outside quarkus-bom; Quarkus wiring unverified | JVM or native; PoC accepted |
  | (b) Lambda layer | AWS-managed, zero code, Application Signals | Java managed runtimes only (native not listed); two-SDK interaction with quarkus-opentelemetry unverified | JVM (+ SnapStart) build |
  | (c) OTLP endpoint | Standard OTLP, Transaction Search | SigV4 required; no gRPC; Quarkus SigV4 support not documented | Only with a signing component proven in a PoC |

- Agent: "Ask user which export route to prove in a PoC; none is documented end to end for Quarkus 3.40 on Lambda."
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-migration-opentelemetry.html (2026-10-28); https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals-Enable-LambdaMain.html (2026-10-28); https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLPEndpoint.html (2026-10-28); https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLPGettingStarted.html (2026-10-28); https://aws-otel.github.io/docs/getting-started/lambda (2026-10-28, undated page); https://quarkus.io/version/3.40/guides/opentelemetry (2026-10-28)

**C3. API Gateway type at the trace root: REST API (traced) vs HTTP API (not traced)**
> Confidence: 🟢 High (each fact); the impact on the Quarkus extension choice combines facts
- Options: (A) REST API + `quarkus-amazon-lambda-rest`: "API Gateway supports X-Ray tracing for all API Gateway REST API endpoint types", X-Ray sampling rules per stage (`AWS::ApiGateway::Stage`, service name `{api-name}/{stage-name}`). The extension is "preview" and its generated `sam.native.yaml` uses the deprecated `Runtime: provided` (family facts 25, 27). (B) HTTP API + `quarkus-amazon-lambda-http`: the "AWS X-Ray tracing" row reads REST API Yes, HTTP API No. The trace then starts at the `AWS::Lambda` segment (inference, medium confidence).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | REST API | API Gateway node, stage-level sampling rules, end-to-end "API GW -> Lambda -> DynamoDB" | REST features cost more; Quarkus REST extension preview | The source item literally needs the API GW node |
  | HTTP API | Lower price, JWT authorizer (U3 research) | No API Gateway segment; Lambda default sampling only | Lambda -> DynamoDB part is enough |

- Agent: "Ask user whether the API Gateway node must appear in the trace; if yes, REST API is required."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html (2026-10-28); https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-xray.html (2026-10-28); https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-configuring-xray-sampling-rules.html (2026-10-28)

**C4. JVM + SnapStart vs native, effects on tracing (family rule 3)**
> Confidence: 🟢 High for the facts; the effects are listed, not chosen
- Options: (A) JVM on `java21`/`java25`/`java17.al2023`, optionally SnapStart; (B) native on an OS-only runtime.
- Facts: native + X-Ray SDK needs `quarkus-amazon-lambda-xray` (A3). `_X_AMZN_TRACE_ID` "is not defined for OS-only runtimes", and for Java 17+ the header is in `com.amazonaws.xray.traceHeader` (F5). The Quarkus poll loop at 3.40.1.1 sets that property from `Lambda-Runtime-Trace-Id` and never clears it. Which runtime mode uses the poll loop is (medium confidence) (M1). SnapStart functions get a `Restore` subsegment that shows snapshot restore, runtime load and after-restore hooks. Tracing mode cannot be changed on a published version, and SnapStart runs only on published versions (family fact 16). The Quarkus 3.40 SnapStart guide says nothing about tracing. Whether tracer, exporter or ID-generator state captured in the snapshot needs re-initialising after restore is (unverified) (U6). The AWS Lambda Layer for OpenTelemetry lists only Java managed runtimes (C2 b).
- Agent: "Ask user JVM+SnapStart or native (ADR, family rule 3); then apply the tracing consequences above."
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html (2026-10-28); https://quarkus.io/version/3.40/guides/aws-lambda-snapstart (2026-10-28); https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AbstractLambdaPollLoop.java (2026-10-28)

**C5. Sampling strategy**
> Confidence: 🟢 High for each fact
- Options and facts: (A) Lambda Active tracing with no upstream decision: "The sampling rate is 1 request per second and 5 percent of additional requests. You can't configure the X-Ray sampling rate for your functions." (B) Upstream decision: "Typically, an upstream service, such as Amazon API Gateway ... decides whether incoming requests should be traced ... Lambda uses that header". REST API stages use X-Ray sampling rules (Reservoir, Rate 0-100, Service type `AWS::ApiGateway::Stage`). (C) OTel sampler inside the function: `quarkus.otel.traces.sampler` default `parentbased_always_on`; `quarkus.otel.traces.sampler.arg` default `1.0d` (used with `traceidratio`/`parentbased_traceidratio`). The tracing guide calls the sampler "build-time only" and the arg runtime. A CDI `Sampler` producer is supported. X-Ray remote sampling is "Supported in OTel Java" (AWS migration feature table) via `AwsXrayRemoteSampler` (`io.opentelemetry.contrib:opentelemetry-aws-xray`); use with Quarkus is (unverified) (U7). (D) Transaction Search: "enables the capture of trace spans for Lambda function invocation without sampling" (cost implications: page not recorded).
- Agent: "Ask user the sampling target per API stage (reservoir/rate) and whether Transaction Search is in scope (cost)."
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html (2026-10-28); https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-configuring-xray-sampling-rules.html (2026-10-28); https://quarkus.io/version/3.40/guides/opentelemetry-tracing (2026-10-28); https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals-Enable-LambdaMain.html (2026-10-28)

**C6. Where to attach the X-Ray `TracingInterceptor` for Quarkiverse-managed clients**
> Confidence: 🟡 Medium (combination of two High facts)
- Options: (A) Quarkiverse 3.23.x `quarkus.dynamodb.interceptors` ("List of execution interceptors that will have access to read and modify the request and response objects"; class names implementing `software.amazon.awssdk.core.interceptor.ExecutionInterceptor`, loaded via CDI first with a no-arg constructor fallback). Setting it to `com.amazonaws.xray.interceptors.TracingInterceptor` is an inference (medium confidence) (M2). (B) Build the client yourself as in A5. (C) `aws-xray-recorder-sdk-aws-sdk-v2-instrumentor` for all clients. It is not a dependency of `quarkus-amazon-lambda-xray` and its native-image registration is not covered by `XrayBuildStep` (inference, medium confidence).
- Agent: "Ask user whether clients are Quarkiverse-managed (prefer A after a test) or hand-built (B)."
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html (2026-10-28, partial); https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-awssdkclients.html (2026-10-28)

**C7. `tenantId` as an annotation: confirm it is bounded and not PII**
> Confidence: 🟢 High for the X-Ray limits; boundedness is a family/ADR decision
- Facts: up to 50 annotations indexed per trace; key alphanumeric plus dot; value up to 1,000 characters; annotations are searchable with `annotation[key]` filter expressions. Family rule 7 forbids PII and unbounded tenant cardinality in metric dimensions without an ADR. The caller asks for "bounded values" for the tenantId annotation.
- Agent: "Ask user to confirm that tenantId is an opaque identifier (no name/email) and whether the tenant population needs an ADR."
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-segment.html (2026-10-28); `_family_rules_v3.40.md` rule 7

### 🚫 Forbidden Patterns

**F1. Expecting traces with Lambda in `PassThrough` (the default) because API Gateway sampled the request**
> Severity: high
> Confidence: 🟢 High
- Why: in PassThrough Lambda "does not send traces automatically. This is true even if the tracing header contains a decision to sample the request." AWS notes the old passive behaviour changed: "If your solution depends on this passive tracing behavior, switch to `Active` tracing."
- Impact: no `AWS::Lambda` / `AWS::Lambda::Function` segments, so the DynamoDB subsegments have no parent in X-Ray.
- ❌ Wrong:
  ```text
  TracingConfig: (not set)      # defaults to PassThrough
  ```
- ✅ Correct:
  ```text
  TracingConfig: Mode=Active    # A1, plus xray:PutTraceSegments / xray:PutTelemetryRecords (A2)
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html (2026-10-28)

**F2. Expecting an API Gateway node in X-Ray from an HTTP API (`quarkus-amazon-lambda-http`)**
> Severity: high
> Confidence: 🟢 High
- Why: AWS X-Ray tracing: REST API "Yes", HTTP API "No". `quarkus-amazon-lambda-http` serves HTTP API payload 2.0 (family fact 25).
- Impact: the "API GW -> Lambda -> DynamoDB" trace has no API Gateway segment, and there are no stage sampling rules.
- ❌ Wrong:
  ```text
  HTTP API (payload 2.0) + quarkus-amazon-lambda-http  -> expect API Gateway segment in the trace
  ```
- ✅ Correct:
  ```text
  REST API stage with X-Ray tracing enabled + quarkus-amazon-lambda-rest  (choice and trade-offs: C3)
  ```
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html (2026-10-28); https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-xray.html (2026-10-28)

**F3. Reading `_X_AMZN_TRACE_ID` from the environment in a Quarkus Java 17+ or native Lambda**
> Severity: moderate
> Confidence: 🟢 High
- Why: "For Java runtime versions 17 and later, this environment variable is not used. Instead, Lambda stores tracing information in the `com.amazonaws.xray.traceHeader` system property." It "is not defined for OS-only runtimes (the `provided` runtime family)". Quarkus 3.40.1.1's poll loop sets `System.setProperty("com.amazonaws.xray.traceHeader", traceId)` from the `Lambda-Runtime-Trace-Id` header.
- Impact: `System.getenv("_X_AMZN_TRACE_ID")` returns null, so log correlation or manual propagation silently loses the trace ID.
- ❌ Wrong:
  ```java
  String header = System.getenv("_X_AMZN_TRACE_ID");   // null on java17+/java21/java25 and on provided.al2023
  ```
- ✅ Correct:
  ```java
  // Quarkus 3.40.1.1 on java21 (managed) or native (custom runtime loop)
  String header = System.getProperty("com.amazonaws.xray.traceHeader");
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html (2026-10-28); https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AbstractLambdaPollLoop.java (2026-10-28)

**F4. PII or secrets in annotations, metadata or span attributes**
> Severity: high
> Confidence: 🟢 High
- Why: "Anyone that you grant read access to X-Ray can view this data" (annotations and metadata). Quarkus: "The End User attributes are personally identifiable information"; `quarkus.otel.traces.eusp.enabled` defaults to `false`. GenAI message capture (`quarkus.otel.instrumentation.genai.capture-message-content`, default `false`) carries data-privacy concerns (Quarkiverse 3.23.x). Family rule 7: no PII.
- Impact: personal data is exposed to every X-Ray reader; compliance breach.
- ❌ Wrong:
  ```java
  sub.putAnnotation("email", user.email());
  span.setAttribute("customer.name", customer.name());
  ```
  ```properties
  quarkus.otel.traces.eusp.enabled=true
  ```
- ✅ Correct:
  ```java
  sub.putAnnotation("tenantId", tenantId);          // opaque, bounded (C7)
  ```
  ```properties
  # keep the defaults
  quarkus.otel.traces.eusp.enabled=false
  quarkus.otel.instrumentation.genai.capture-message-content=false
  ```
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java.html (2026-10-28); https://quarkus.io/version/3.40/guides/opentelemetry-tracing (2026-10-28); https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/opentelemetry.html (2026-10-28)

**F5. Annotation keys with underscores, hyphens or spaces**
> Severity: moderate
> Confidence: 🟢 High
- Why: "The key for an X-Ray annotation can have up to 500 alphanumeric characters. You cannot use spaces or symbols other than a dot or period ( . )". How the SDK handles an invalid key is (unverified) (U8).
- Impact: the annotation cannot be used in `annotation[key]` filter expressions as intended.
- ❌ Wrong:
  ```java
  sub.putAnnotation("tenant_id", tenantId);
  ```
- ✅ Correct:
  ```java
  sub.putAnnotation("tenantId", tenantId);   // or "tenant.id"
  ```
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-segment.html (2026-10-28)

**F6. Annotating the Lambda function segment instead of a subsegment**
> Severity: moderate
> Confidence: 🟢 High
- Why: "You can use the X-Ray SDK to extend the `Invocation` subsegment with additional subsegments for downstream calls, annotations, and metadata. You can't access the function segment directly or record work done outside of the handler invocation scope."
- Impact: annotations are not recorded where expected; work done outside the handler is not traced.
- ❌ Wrong:
  ```java
  AWSXRay.getCurrentSegment().putAnnotation("tenantId", tenantId);   // function segment is Lambda-owned
  ```
- ✅ Correct:
  ```java
  Subsegment sub = AWSXRay.beginSubsegment("## handle");             // A7 pattern
  try { sub.putAnnotation("tenantId", tenantId); /* work */ } finally { AWSXRay.endSubsegment(); }
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html (2026-10-28)

**F7. Trying to change the tracing mode of a published version / SnapStart alias in place**
> Severity: moderate
> Confidence: 🟢 High
- Why: "Tracing mode is part of the version-specific configuration when you publish a version of your function. You can't change the tracing mode on a published version." SnapStart only runs on published versions/aliases (family fact 16).
- Impact: the update has no effect on the version serving traffic; the trace gap persists.
- ❌ Wrong:
  ```text
  update-function-configuration --tracing-config Mode=Active on version 7 (already published)
  ```
- ✅ Correct:
  ```text
  set Mode=Active on the unpublished function configuration, then publish a new version and move the alias
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/java-tracing.html (2026-10-28)

**F8. Trying to set the Lambda function's sampling rate with X-Ray sampling rules**
> Severity: moderate
> Confidence: 🟢 High
- Why: "The sampling rate is 1 request per second and 5 percent of additional requests. You can't configure the X-Ray sampling rate for your functions."
- Impact: the rule has no effect on Lambda's own sampling; you get unexpected trace volume or gaps.
- ❌ Wrong:
  ```text
  X-Ray sampling rule with Service type AWS::Lambda::Function, Rate 50   # expecting Lambda to honour it
  ```
- ✅ Correct:
  ```text
  sampling rule on the upstream REST API stage (Service type AWS::ApiGateway::Stage) - see C5
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html (2026-10-28); https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-configuring-xray-sampling-rules.html (2026-10-28)

**F9. Sending Quarkus's default gRPC OTLP export to the X-Ray traces endpoint**
> Severity: moderate
> Confidence: 🟢 High
- Why: Quarkus `quarkus.otel.exporter.otlp.traces.protocol` defaults to `grpc` (default endpoint `http://localhost:4317`). The CloudWatch traces endpoint "supports only HTTP and doesn't support gRPC" and needs SigV4.
- Impact: export fails; spans are dropped.
- ❌ Wrong:
  ```properties
  quarkus.otel.exporter.otlp.traces.endpoint=https://xray.eu-west-1.amazonaws.com
  # protocol left at the default grpc, no SigV4
  ```
- ✅ Correct:
  ```text
  choose an export route documented by AWS for Lambda (C2): UDP span exporter or the AWS Lambda Layer for OpenTelemetry
  ```
- Source: https://quarkus.io/version/3.40/guides/opentelemetry (2026-10-28); https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLPEndpoint.html (2026-10-28)

**F10. Expecting X-Ray traces from Kafka, MQ or DocumentDB event source mappings**
> Severity: moderate
> Confidence: 🟢 High
- Why: "X-Ray tracing is currently not supported for Lambda Event Functions with Amazon Managed Streaming for Apache Kafka (Amazon MSK), self-managed Apache Kafka, Amazon MQ with ActiveMQ and RabbitMQ, or Amazon DocumentDB event source mappings."
- Impact: those triggers produce no Lambda trace.
- ❌ Wrong:
  ```text
  MSK event source mapping + Active tracing -> expect producer-to-Lambda trace
  ```
- ✅ Correct:
  ```text
  SQS (traces "are automatically linked" to downstream Lambda) or API Gateway REST API as the traced entry point
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html (2026-10-28)

---

## Migration Guide

> Confidence: 🟢 High for the X-Ray SDK status | Sources: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html (2026-10-28) + https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html (2026-10-28)

**Breaking changes / status changes**:
- ⚠️ Migration Note: the AWS X-Ray SDKs and daemon have been in **maintenance mode since February 25th, 2026**. "The SDKs/Daemon will not receive new feature enhancements." The end date is "N/A". Every X-Ray SDK for Java page read today carries this notice. `quarkus-amazon-lambda-xray` 3.40.1.1 depends on that SDK (`aws-xray-recorder-sdk-aws-sdk-v2` 2.18.3 via quarkus-bom). Patterns A3, A5, A7 and F6 are therefore tagged with this note in the skill.
- Lambda changed its trace segment format ("old-style" vs "new-style"). The new style has no `Invocation` subsegment: "customer subsegments are attached directly to the `AWS::Lambda::Function` segment", which carries the annotations `aws.responseLatency`, `aws.responseDuration`, `aws.runtimeOverhead` and `aws.extensionOverhead`. Dashboards or queries that rely on `Invocation` must allow for both.
- Lambda PassThrough no longer sends traces passively (F1).
- Quarkus 3.40 Migration Guide (wiki, last edited 2026-10-01): no items about OpenTelemetry, Lambda, X-Ray or tracing. The 3.34-3.39 guides were not read (U9).
- The Quarkus 3.40 AWS Lambda guide's X-Ray section has no Maven block; the dependency is named only in prose.

**X-Ray to OpenTelemetry mapping (AWS)**: Recorder -> Tracer Provider/Tracers; Service Plugins -> Resource Detector; Segment -> (Server) Span; Sub-segment -> (non-Server) Span; Annotations/Metadata -> Attributes; X-Ray Trace Context Propagation -> W3C Trace Context Propagation; Daemon -> OpenTelemetry Collector. In Lambda: "Use an auto-instrumentation Lambda Layer" or "Manually set up OpenTelemetry ... Configure a Simple Span Processor with an X-Ray UDP Span Exporter ... Set up an X-Ray Lambda propagator".

**Upgrade steps (X-Ray SDK -> OTel, Quarkus 3.40.1.1)**: representative order; route per C2, not proven for Quarkus:
1. Record the C1 decision in an ADR.
2. Replace `quarkus-amazon-lambda-xray` / `TracingInterceptor` with `io.quarkus:quarkus-opentelemetry` and `quarkus.<client>.telemetry.enabled=true` (A6).
3. Replace `beginSubsegment`/`putAnnotation` with `Tracer` spans + `aws.xray.annotations` (A8).
4. Set `quarkus.otel.simple=true` (A9) and an export route proven in a PoC (C2).
5. Keep Lambda `Mode=Active` (A1) for the Lambda service segments.

**Compatibility Matrix** (managed versions from https://repo1.maven.org/maven2/io/quarkus/quarkus-bom/3.40.1.1/quarkus-bom-3.40.1.1.pom, all 419,419 chars read in 5 windows, 2026-10-28):

| Dependency | Version (quarkus-bom 3.40.1.1) | Notes |
|------------|------------|-------|
| `com.amazonaws:aws-xray-recorder-sdk-aws-sdk-v2` | 2.18.3 | the only aws-xray artifact managed; AWS pages' examples show BOM 2.11.0 (example, not a requirement) |
| `io.opentelemetry:opentelemetry-api` | 1.62.0 | `-incubator` 1.62.0-alpha |
| `io.opentelemetry.instrumentation:opentelemetry-instrumentation-api` / `-annotations` | 2.28.1 | |
| `io.opentelemetry.instrumentation:opentelemetry-aws-sdk-2.2` / `-2.2-autoconfigure` | 2.28.1-alpha | used by Quarkiverse telemetry (A6) |
| `io.opentelemetry.instrumentation:opentelemetry-aws-lambda-core-1.0`, `-aws-lambda-events-3.11`, `-aws-lambda-events-common-2.2` | 2.28.1-alpha | managed, but no Quarkus guide uses them (U2) |
| `io.opentelemetry.contrib:*` (xray propagator, aws-xray, aws-resources) | not managed | pin yourself if used (C2 a) |
| `io.opentelemetry.semconv:opentelemetry-semconv` | 1.41.1 | |
| `com.amazonaws:aws-lambda-java-core` / `-events` | 1.4.0 / 3.16.1 | |
| quarkus-amazon-services | 3.23.0 | family fact 17 (built on Quarkus 3.40.0) |

---

## Implementation Blueprint

> Confidence: 🟢 High for each property and dependency; the assembled examples are (medium confidence) where noted

**Step 1 - Choose the stack (C1) and the API type (C3).** Record both in an ADR.

**Step 2a - X-Ray SDK path (JVM or native), Quarkus 3.40.1.1**
```xml
<!-- Quarkus 3.40.1.1: native needs the extension (A3). In JVM mode the guide does not require it;
     adding com.amazonaws:aws-xray-recorder-sdk-aws-sdk-v2 directly is an option (M4, medium confidence) -->
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-amazon-lambda-xray</artifactId>
</dependency>
```
```properties
# Quarkiverse 3.23.x managed client + X-Ray interceptor (C6 option A - inference, medium confidence)
quarkus.dynamodb.interceptors=com.amazonaws.xray.interceptors.TracingInterceptor
```
Lifecycle, as documented by AWS for X-Ray SDK on Lambda: "after your Lambda has Active Tracing enabled, there is no additional configuration required to use the X-Ray SDK. Lambda will create a segment representing the Lambda handler invocation, and you can create sub-segments" (https://docs.aws.amazon.com/xray/latest/devguide/xray-migration-opentelemetry.html). Lambda sets `AWS_XRAY_CONTEXT_MISSING=LOG_ERROR` "to avoid throwing runtime errors from the X-Ray SDK" and `AWS_XRAY_DAEMON_ADDRESS` (https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html).

**Step 2b - OpenTelemetry path, Quarkus 3.40.1.1**
```xml
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-opentelemetry</artifactId>
</dependency>
```
```properties
# Quarkus 3.40.1.1 quarkus-opentelemetry - documented keys and defaults
# quarkus.otel.traces.enabled=true                 (default true, build time)
# quarkus.otel.metrics.enabled=false               (default false; metrics are U13)
# quarkus.otel.logs.enabled=false                  (default false; logs are U11)
quarkus.otel.simple=true                           # A9 (default false)
quarkus.otel.service.name=orders-fn                # default ${quarkus.application.name:unset}
# quarkus.otel.propagators=tracecontext,baggage    (default; X-Ray propagator: C2, U2)
# quarkus.otel.traces.sampler=parentbased_always_on (default; build time per tracing guide)
quarkus.dynamodb.telemetry.enabled=true            # A6 (default false)
# export route: see C2 - no Quarkus-documented route to X-Ray from Lambda
```
Custom spans (Quarkus 3.40 tracing guide): `@WithSpan` "will create a new Span"; `@AddingSpanAttributes` "will not create a new span but will add annotated method parameters to attributes"; `@SpanAttribute` on parameters; `@Inject Tracer tracer`. "The instrumentation documented in this section has been tested with Quarkus and works in both standard and native mode." (https://quarkus.io/version/3.40/guides/opentelemetry-tracing)

```java
// Quarkus 3.40.1.1 + quarkus-opentelemetry - CDI bean called by the Lambda handler
// (class shape from the tracing guide; body illustrative, medium confidence)
import io.opentelemetry.instrumentation.annotations.SpanAttribute;
import io.opentelemetry.instrumentation.annotations.WithSpan;
import jakarta.enterprise.context.ApplicationScoped;

@ApplicationScoped
public class OrderService {
    @WithSpan("order.save")
    public void save(@SpanAttribute("tenantId") String tenantId, Order order) {
        // DynamoDB call with quarkus.dynamodb.telemetry.enabled=true -> child client span
    }
}
```

**Step 3 - Lambda configuration** (artifact contract, IaC in `provisioning-aws-*-v6`): `TracingConfig Mode=Active` (A1), the two X-Ray actions (A2), `MemorySize >= 256` with X-Ray (A4), and the tracing mode set before `publish-version` (F7).

**Integration**: Quarkus Lambda ↔ DynamoDB (X-Ray): an instrumented client records a `DynamoDB` subsegment with `aws.table_name`, `aws.operation` and `aws.request_id`; "each table appears as a separate node in the service map" (https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-awssdkclients.html). DynamoDB doesn't send its own segment, so "X-Ray uses subsegments to generate inferred segments" (https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html).

**Integration**: Quarkus Lambda ↔ SQS: "Traces from upstream message producers, such as Amazon SQS, are automatically linked to traces from downstream Lambda Event Functions" (services-xray). On the OTel path, Quarkiverse 3.23.x `quarkus.otel.instrumentation.aws-sdk.experimental-use-propagator-for-messaging` (default `false`, "currently only SQS; SNS may follow") and "the X-Ray propagator is always used" for messaging.

---

## Quality Control

**Verification Commands**:
```bash
# Representative - adapt to your environment (Quarkus 3.40.1.1 Lambda)
# 1. Tracing mode on the version that serves traffic
aws lambda get-function-configuration --function-name my-function --qualifier live \
  --query 'TracingConfig.Mode'
# Expected: "Active"

# 2. Dependencies present (X-Ray path)
mvn -q dependency:tree -Dincludes=com.amazonaws:aws-xray-recorder-sdk-aws-sdk-v2
# Expected: com.amazonaws:aws-xray-recorder-sdk-aws-sdk-v2:jar:2.18.3

# 3. Dependencies present (OTel path)
mvn -q dependency:tree -Dincludes=io.opentelemetry.instrumentation:opentelemetry-aws-sdk-2.2
# Expected: ...opentelemetry-aws-sdk-2.2:jar:2.28.1-alpha (when quarkus.<client>.telemetry.enabled=true is used; inclusion path (unverified))

# 4. Static checks on code (no AWS call)
grep -rn "_X_AMZN_TRACE_ID" src/main/java      # Expected: no match (F3)
grep -rnE 'putAnnotation\("[^"]*[_ -][^"]*"' src/main/java   # Expected: no match (F5)
grep -rn "eusp.enabled=true" src/main/resources  # Expected: no match (F4)

# 5. After an invocation, traces exist
aws xray get-trace-summaries --start-time $(date -d '-10 min' +%s) --end-time $(date +%s) \
  --filter-expression 'service("my-function")'
# Expected: at least one TraceSummary (sampling permitting: 1 rps + 5%)
```

**Mocking / tests**:
- The pages read do not document testing tracing in Quarkus Lambda tests. The Lambda mock event server (family fact 14) sends no `Lambda-Runtime-Trace-Id` header as far as documented (unverified) (U11).
- X-Ray SDK without a segment: Lambda sets `AWS_XRAY_CONTEXT_MISSING=LOG_ERROR` in AWS. In local tests the default context-missing behaviour of SDK 2.18.3 is (unverified) (U12). Set `AWS_XRAY_CONTEXT_MISSING=LOG_ERROR` in the test environment as a precaution (medium confidence).
- OTel: `quarkus.otel.sdk.disabled=true` (runtime, default `false`) or `quarkus.otel.exporter.otlp.enabled=false` ("Telemetry is still generated and propagated, but not sent", paraphrase) keep tests from exporting (https://quarkus.io/version/3.40/guides/opentelemetry). An in-memory span exporter for assertions is not documented on the pages read (gap). Testing patterns are U5's scope (`research_Quarkus_AmazonLambdaTesting_v3.40.md`).

---

## Production Readiness

- **Performance**: X-Ray "adds many classes" and the guide asks for at least 256 MB (A4). The AWS Lambda Layer for OpenTelemetry enables only AWS SDK and HTTP instrumentation by default "To reduce Lambda cold starts"; `OTEL_INSTRUMENTATION_COMMON_DEFAULT_ENABLED=true` enables all. AWS: "For reduced cold starts, consider using OpenTelemetry manual instrumentation". SnapStart shows its cost in the `Restore` subsegment; "You aren't charged for the time spent outside the microVM to restore a snapshot".
- **Scalability / limits**: segment documents "can be up to 64 kB"; 50 indexed annotations per trace; trace data retained 30 days. OTLP traces endpoint: 5 MB uncompressed per request, 10,000 spans per request, 200 KB per span, 16 KB per resource+scope. Quarkus attribute count limits default 128 (`quarkus.otel.attribute.count.limit`); value length has no default limit (paraphrase). Pricing: free tier, then "X-Ray charges for trace storage and retrieval" (amounts: page not recorded).
- **Monitoring**: Lambda segments `AWS::Lambda` (service: scheduling, environment creation, code/layer download) and `AWS::Lambda::Function` ("If the `AWS::Lambda::Function` segment shows an error, your function had an issue"). Errors, faults and throttles map to 4xx, 5xx and 429. Metrics and logs belong to U13 and U11.
- **Security**: F4 (no PII; "Anyone that you grant read access to X-Ray can view this data"). Tracing header security: "A tracing header can originate from the X-Ray SDK, an AWS service, or the client request. Your application can remove `X-Amzn-Trace-Id` from incoming requests to avoid issues caused by users adding trace IDs or sampling decisions". `Lineage` "should not be directly used". OTLP `headers` (for example `authorization=Bearer ...`) are credentials and come from Secrets Manager/SSM (family rule 5). Least privilege: the X-Ray actions only (A2).
- **Error handling**: the X-Ray SDK records exceptions on subsegments (`addException`, A7). `AWS_XRAY_CONTEXT_MISSING=LOG_ERROR` in Lambda.

---

## Reference Implementations

- AWS OTel manual Lambda instrumentation (`ListBucketsLambda` with `TracingRequestHandler`, `AwsXrayUdpSpanExporterBuilder`, `AwsXrayLambdaPropagator`, `AwsSdkTelemetry`): https://docs.aws.amazon.com/xray/latest/devguide/xray-migration-opentelemetry.html#xray-migration-lambda (2026-10-28). Not Quarkus; the handler base class conflicts with `QuarkusStreamHandler` (inference, medium confidence).
- AWS Lambda Java sample apps with active tracing (`s3-java`, `java-basic`, `java-events`, `layer-java`): https://github.com/awsdocs/aws-lambda-developer-guide/tree/main/sample-apps (page not recorded: listed on java-tracing, not fetched).
- Quarkus extension source at tag: https://github.com/quarkusio/quarkus/tree/3.40.1.1/extensions/amazon-lambda-xray (2026-10-28, partial listing).
- Quarkiverse custom `AwsSdkTelemetry` producer (`@Produces @Singleton @Unremovable`): https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/opentelemetry.html (2026-10-28, code paraphrased by the tool).
- Community examples: none used.

---

## Source Bibliography

**Primary (versioned Quarkus 3.40 / source and registry at 3.40.1.1 / Quarkiverse 3.23.x)**

| # | URL | Read | Coverage | Used for |
|---|---|---|---|---|
| S1 | https://quarkus.io/version/3.40/guides/aws-lambda | 2026-10-28 | X-Ray section; quotes limited to about 125 chars by the tool (L1) | extension purpose, Mode=Active, Tracing: Active, 256 MB, no OTel/_X_AMZN_TRACE_ID in body |
| S2 | https://quarkus.io/version/3.40/guides/opentelemetry | 2026-10-28 | 0-100,000 + 100,000-106,169 (full, 2 windows) + config-reference re-query | otel keys/defaults, exporter, protocol, propagators, sampler, simple, bsp, service name, agent not for native |
| S3 | https://quarkus.io/version/3.40/guides/opentelemetry-tracing | 2026-10-28 | Full per tool (no truncation note) | @WithSpan, Tracer, sampler, EUSP PII, native note, serverless simple, xray propagator coordinates |
| S4 | https://quarkus.io/version/3.40/guides/aws-lambda-snapstart | 2026-10-28 | Targeted query (no tracing mention) | absence of tracing guidance |
| S5 | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-xray/3.40.1.1/quarkus-amazon-lambda-xray-3.40.1.1.pom | 2026-10-28 | Full | name, description, dependencies |
| S6 | https://repo1.maven.org/maven2/io/quarkus/quarkus-bom/3.40.1.1/quarkus-bom-3.40.1.1.pom | 2026-10-28 | All 419,419 chars in 5 windows; targeted extraction (L3) | managed xray/otel/lambda versions |
| S7 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-xray/deployment/src/main/java/io/quarkus/amazon/lambda/xray/XrayBuildStep.java | 2026-10-28 | Full | native-image registrations |
| S8 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-xray/runtime/src/main/resources/META-INF/quarkus-extension.yaml | 2026-10-28 | Full | status stable, guide anchor |
| S9 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AbstractLambdaPollLoop.java | 2026-10-28 | Targeted extraction | trace header -> system property, not cleared |
| S10 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AmazonLambdaApi.java | 2026-10-28 | Targeted extraction | `Lambda-Runtime-Trace-Id` constant |
| S11 | https://github.com/quarkusio/quarkus/tree/3.40.1.1/extensions/amazon-lambda-xray (+ runtime/src/main, deployment listing) | 2026-10-28 | Partial directory listings (L2) | module layout |
| S12 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/opentelemetry.html | 2026-10-28 | Full per tool (2 passes); Java sample paraphrased | telemetry.enabled, aws-sdk keys, SQS propagator, GenAI capture |
| S13 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html | 2026-10-28 | 0-100,000 of 104,004 (L4) | dynamodb telemetry.enabled, interceptors |
| S14 | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40 | 2026-10-28 | Full (short page) | no tracing items |

**Primary (AWS official, current pages)**

| # | URL | Read | Used for |
|---|---|---|---|
| S15 | https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html | 2026-10-28 | Active/PassThrough, default, permissions, sampling, segments, unsupported ESMs, function segment access |
| S16 | https://docs.aws.amazon.com/lambda/latest/dg/java-tracing.html | 2026-10-28 | options (ADOT, X-Ray SDK, Powertools), CLI/CFN, layers, Restore subsegment, published-version rule |
| S17 | https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html | 2026-10-28 | `_X_AMZN_TRACE_ID`, `com.amazonaws.xray.traceHeader`, `AWS_XRAY_*` |
| S18 | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java.html | 2026-10-28 | maintenance notice, submodules, BOM 2.11.0 example, visibility of annotations |
| S19 | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html | 2026-10-28 | maintenance mode 2026-02-25, end N/A |
| S20 | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html | 2026-10-28 | concept mapping, aws.xray.annotations, Lambda options |
| S21 | https://docs.aws.amazon.com/xray/latest/devguide/xray-migration-opentelemetry.html | 2026-10-28 | Java OTel deps, AwsSdkTelemetry, TracingInterceptor, Lambda manual recipe |
| S22 | https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html | 2026-10-28 | header format, header security, Lineage, 50 annotations, 64 kB, 30 days |
| S23 | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-segment.html | 2026-10-28 | annotation key/value rules, putAnnotation/putMetadata |
| S24 | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-awssdkclients.html | 2026-10-28 | TracingInterceptor, DynamoDB subsegment |
| S25 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLPEndpoint.html | 2026-10-28 | traces endpoint, SigV4, HTTP only, limits |
| S26 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLPGettingStarted.html | 2026-10-28 | Transaction Search prerequisite, collector-less ADOT SDK |
| S27 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals-Enable-LambdaMain.html | 2026-10-28 | AWS Lambda Layer for OpenTelemetry, /opt/otel-instrument, policy, sampling env vars |
| S28 | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-xray.html | 2026-10-28 | REST API tracing support |
| S29 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html | 2026-10-28 | HTTP API: no X-Ray |
| S30 | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-configuring-xray-sampling-rules.html | 2026-10-28 | stage sampling rules |
| S31 | https://docs.aws.amazon.com/powertools/java/latest/core/tracing/ | 2026-10-28 | pointer only: wraps X-Ray SDK; Quarkus not mentioned (page footer 2026-10-06) |

**Official AWS project docs (undated, medium confidence)**

| # | URL | Read | Used for |
|---|---|---|---|
| S32 | https://aws-otel.github.io/docs/getting-started/lambda/lambda-java | 2026-10-28 | legacy ADOT Java wrapper layer (Java 8/11/17), exec wrappers, "legacy approach" |
| S33 | https://aws-otel.github.io/docs/getting-started/lambda | 2026-10-28 | new layer, Java 11/17/21, /opt/otel-instrument, cold-start defaults; Java ARN table not rendered (L5) |

**Family facts (applied as given)**: rows 9, 14, 16, 17, 25, 27 of `_family_facts_v3.40.md`.

**Validation (community)**: none used. A WebSearch on 2026-10-28 ("Powertools for AWS Lambda Java tracing Quarkus GraalVM native support") returned AWS pages only; it was used just to locate S31.

---

## Research Gaps

```
Contradictions with family facts: none found.
Source differences (not family facts), reported:
  D1 X-Ray SDK version: AWS pages show aws-xray-recorder-sdk-bom 2.11.0 as an example (S16, S18);
     quarkus-bom 3.40.1.1 manages aws-xray-recorder-sdk-aws-sdk-v2 2.18.3 (S6). Follow the Quarkus BOM.
  D2 ADOT Java layer runtimes: legacy wrapper page lists Java 8/11/17 (S32); new layer page lists Java 11/17/21 (S33);
     neither lists java25 or provided.al2023.
  D3 The AWS Lambda java-tracing Gradle example uses aws-xray-recorder-sdk-aws-sdk (SDK v1 handler) next to the
     v2 instrumentor (S16); the X-Ray SDK pages pair -aws-sdk-v2 with -aws-sdk-v2-instrumentor (S18, S24).

U1 (unverified): wiring AwsXrayUdpSpanExporter (0.1.0) into quarkus-opentelemetry via quarkus.otel.traces.exporter=<FQCN> or a CDI SpanExporter bean.
U2 (unverified): using AwsXrayLambdaPropagator / AwsXrayPropagator via quarkus.otel.propagators (FQCN or a PropagatorType value "xray"/"xray-lambda");
    the Quarkus page does not list PropagatorType values; contrib artifacts are not managed by quarkus-bom.
U3 (unverified): AWS Lambda Layer for OpenTelemetry (/opt/otel-instrument) together with quarkus-opentelemetry in a JVM Quarkus Lambda.
U4 (unverified): SigV4 signing of the Quarkus OTLP exporter for https://xray.<region>.amazonaws.com/v1/traces.
U5 (unverified): span loss with the batch span processor when Lambda freezes the environment (reason behind A9 not stated on a page).
U6 (unverified): re-initialisation of X-Ray SDK / OTel SDK state (connections, ID generators) after SnapStart restore.
U7 (unverified): AwsXrayRemoteSampler with Quarkus (CDI Sampler producer) on Lambda.
U8 (unverified): X-Ray SDK behaviour for annotation keys with invalid characters (dropped, rejected, or sanitised).
U9 (unverified): absence of tracing-related breaking changes in Quarkus 3.34-3.39 migration guides (not read).
U10 (unverified): Powertools for AWS Lambda (Java) tracing inside a Quarkus Lambda (pointer only, out of scope).
U11 (unverified): whether the Quarkus mock event server sends a Lambda-Runtime-Trace-Id header in dev/test.
U12 (unverified): default AWS_XRAY_CONTEXT_MISSING behaviour of X-Ray SDK 2.18.3 outside Lambda.

M1 (medium confidence): AbstractLambdaPollLoop is the runtime loop used by native (custom runtime) Quarkus Lambdas; on managed java runtimes the AWS runtime sets the property (S17).
M2 (medium confidence): quarkus.dynamodb.interceptors=com.amazonaws.xray.interceptors.TracingInterceptor as the way to trace Quarkiverse-managed clients.
M3 (medium confidence): whether quarkus.<extension>.telemetry.enabled and quarkus.dynamodb.interceptors are fixed at build time (the table header applies to the page; per-key markers not visible to the tool).
M4 (medium confidence): JVM-only X-Ray use without quarkus-amazon-lambda-xray (the guide scopes the extension to native builds).
M5 (medium confidence): illustrative method bodies (A7, Step 2b) and the X-Ray SDK reading com.amazonaws.xray.traceHeader in native Quarkus.
M6 (medium confidence): ADOT github.io pages are undated (copyright 2020-2023) and partly rendered.
M7 (medium confidence): HTTP API traces start at the AWS::Lambda segment (inference from S29 + S15).
M8 (medium confidence, absence of evidence): AWS Lambda Layer for OpenTelemetry does not support OS-only runtimes / Quarkus native.

L1 (coverage limit): S1 X-Ray section returned under a ~125-char quote limit; wording outside quotes is tool paraphrase.
L2 (coverage limit): S11 GitHub directory listings partial ("View all files" truncation); the runtime module showed only resources/META-INF.
L3 (coverage limit): S6 read in 5 windows with targeted extraction only (aws, opentelemetry); other entries not reviewed.
L4 (coverage limit): S13 read 0-100,000 of 104,004 characters.
L5 (coverage limit): S33 Java layer ARN table not rendered by the tool.
L6 (coverage limit): all pages read through WebFetch summarisation; quotes are marked; everything else is paraphrase.

Gap: no Quarkus-documented OTel export route from Lambda to X-Ray (U1-U4).
Impact: the AWS-recommended stack (OTel) cannot be given as an Always Do for Quarkus 3.40 Lambda.
Workaround: Ask-First C1/C2 plus a PoC; the X-Ray SDK path stays documented but in maintenance mode.
Follow-up: Quarkus 3.40 source for quarkus-opentelemetry (PropagatorType enum, exporter SPI); ADOT Java docs for the UDP exporter; AWS re:Post/official blog for Quarkus.
§7-ref: Iteration 3 - left unverified (not IRRESOLVABLE: each has a follow-up page).
```

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Executive Summary / A3 | What `quarkus-amazon-lambda-xray` does exactly (guide only says "not fully compatible with GraalVM") | Resolved: native-image registrations only (XrayBuildStep), deps from POM, status stable | S7, S5, S8 (2026-10-28) |
| 1 | Compatibility Matrix | X-Ray SDK and OTel versions managed by Quarkus 3.40.1.1 | Resolved: aws-xray-recorder-sdk-aws-sdk-v2 2.18.3; otel api 1.62.0; instrumentation 2.28.1(-alpha); contrib not managed | S6 (2026-10-28) |
| 1 | C1 / Migration Guide | X-Ray SDK maintenance status and dates | Resolved: maintenance mode from 2026-02-25, end N/A, security fixes only | S19, S18 (2026-10-28) |
| 2 | F3 / C4 | `_X_AMZN_TRACE_ID` in Java and native | Resolved: not used for Java 17+, undefined on OS-only; Quarkus poll loop sets com.amazonaws.xray.traceHeader | S17, S9, S10 (2026-10-28) |
| 2 | C3 / F2 | API Gateway type and X-Ray | Resolved: HTTP API no X-Ray; REST yes; stage sampling rules | S29, S28, S30 (2026-10-28) |
| 2 | A6 | Quarkiverse 3.23.x OpenTelemetry page (not read by U4) | Resolved: telemetry.enabled default false; aws-sdk experimental keys; SQS propagator | S12, S13 (2026-10-28) |
| 3 | C2 / F9 | X-Ray OTLP endpoint requirements | Resolved: HTTP only, SigV4, Transaction Search, limits | S25, S26 (2026-10-28) |
| 3 | C2 | AWS Lambda Layer for OpenTelemetry for Java | Resolved: /opt/otel-instrument, Java 11/17/21, tracing-only env var; native not mentioned | S27, S33 (2026-10-28) |
| 3 | Research Gaps | U1-U12 | Left (unverified): MAX_ITERATIONS=3 reached; not IRRESOLVABLE, each has a follow-up page | - |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Complex)
- [x] All scope areas cited (quarkus-amazon-lambda-xray exact behaviour and deps; quarkus-opentelemetry on Lambda as far as documented; ADOT layer; X-Ray OTLP endpoint; Active/PassThrough; `_X_AMZN_TRACE_ID` and header propagation; SDK v2 TracingInterceptor vs OTel AWS SDK instrumentation; Quarkiverse 3.23.x OTel page; sampling; native and SnapStart effects; annotations/metadata and no-PII; X-Ray SDK maintenance status)
- [x] Pattern counts driven by domain needs (9 / 7 / 10)
- [x] Every anti-pattern has alternative (F2, F9 alternatives point to Ask-First items per family rule 9)
- [x] All CLI commands marked as representative
- [x] Integration examples complete within scope (DynamoDB, SQS; IaC deferred to provisioning-aws-*-v6 per family rule 4)
- [x] Sources dated and linked
- [x] Security documented (PII, header spoofing, least privilege, OTLP header secrets)
- [x] 1+ copy-paste working example (A5 client builder, A7 subsegment, A6/A9 properties)
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns triangulated where two sources exist (A1, A2, A3, A5, A6, A7, A8, A9); A4 High on a single versioned page per the family evidence rule
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced (U-items logged in iteration 3)

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: A1-A9, F1-F10, the Compatibility Matrix versions, the X-Ray SDK maintenance date, the HTTP API / REST API tracing support, and the Lambda env var / system property facts.
- **Medium Confidence (validate with user)**: M1-M8; C2 and C6 as a whole; illustrative code bodies.
- **Low Confidence (must ask human)**: U1-U12; any claim that a specific OTel export route works from a Quarkus 3.40 Lambda.
- **Edge Cases (pause)**: the X-Ray SDK is in maintenance mode, which is not EOL (no end date), so no stop, but C1 must be an ADR. Quarkus 3.40.1.1 is 9 days old; the 3.40 LTS line is 28 days old.
- **Emergency Stop**: not triggered (official Quarkus 3.40, Quarkiverse 3.23.x and AWS sources available).
