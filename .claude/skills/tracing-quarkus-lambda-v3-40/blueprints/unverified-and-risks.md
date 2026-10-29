# Unverified Register, Risks and Bibliography

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 87%, a deep run using all 3 iterations, 6 triangulated claims and 12 unverified items. Family facts verified by the orchestrator on 2026-10-28 keep the tags of the family facts file.

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Source differences](#source-differences)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30; latest patch 3.40.1.1 (2026-10-19) (High; https://quarkus.io/releases). The 3.40 documentation is new and may still change.
- AWS X-Ray SDKs and daemon are in maintenance mode since 2026-02-25 with no end date (High; https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html). Not end of life, so no stop; the X-Ray versus OpenTelemetry choice is an ADR ([C1](./ask-first-decisions.md#c1-x-ray-sdk-or-opentelemetry)). The AWS-recommended OpenTelemetry stack cannot be an Always Do for Quarkus 3.40 Lambda because no export route was found documented in the pages read (medium confidence, absence of evidence, M9) ([C2](./otel-export-routes.md#c2-otel-export-route)).
- Quarkus 4.0.0 is "Upcoming" with no date on the releases page (High). Quarkus 4 and Quarkiverse 4.0.0.Beta* content is rejected for this skill.
- Quarkiverse 3.23.0 is the only 3.23.x on Central and is built on Quarkus 3.40.0 (family fact).

## Unverified items

12 unverified items (do not assert them).

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | Wiring `AwsXrayUdpSpanExporter` (0.1.0) into `quarkus-opentelemetry` via `quarkus.otel.traces.exporter=<FQCN>` or a CDI `SpanExporter` bean | Route (a) of C2 needs a PoC |
| U2 | Using `AwsXrayLambdaPropagator` / `AwsXrayPropagator` through `quarkus.otel.propagators` (FQCN or a `PropagatorType` value); the Quarkus page does not list the `PropagatorType` values | PoC; pin the contrib artifacts yourself |
| U3 | AWS Lambda Layer for OpenTelemetry (`/opt/otel-instrument`) together with `quarkus-opentelemetry` in a JVM Quarkus Lambda | PoC; possible two-SDK conflict |
| U4 | SigV4 signing of the Quarkus OTLP exporter for `https://xray.<region>.amazonaws.com/v1/traces` | Do not point the exporter there (F9) |
| U5 | Span loss with the batch span processor when Lambda freezes the environment; the reason behind A9 is not stated on a page | Keep `quarkus.otel.simple=true` |
| U6 | Re-initialisation of X-Ray SDK or OTel SDK state (connections, ID generators) after SnapStart restore | Test on a published version |
| U7 | `AwsXrayRemoteSampler` with Quarkus (CDI `Sampler` producer) on Lambda | Use a documented sampler (C5) |
| U8 | X-Ray SDK behaviour for annotation keys with invalid characters (dropped, rejected or sanitised) | Use valid keys (F5) |
| U9 | Absence of tracing-related breaking changes in the Quarkus 3.34 to 3.39 migration guides (not read) | Read them before an upgrade |
| U10 | Powertools for AWS Lambda (Java) tracing inside a Quarkus Lambda (pointer only, out of scope) | See `implementing-lambda-powertools-java` |
| U11 | Whether the Quarkus mock event server sends a `Lambda-Runtime-Trace-Id` header in dev and test | Do not assert a trace ID in local tests |
| U12 | Default `AWS_XRAY_CONTEXT_MISSING` behaviour of X-Ray SDK 2.18.3 outside Lambda | Observe in a local test |

## Irresolvable items

0 irresolvable items. Each unverified item above has a follow-up page (Quarkus `quarkus-opentelemetry` source for the `PropagatorType` enum and exporter SPI, ADOT Java docs for the UDP exporter, an AWS re:Post or official blog for Quarkus); they were left because the research reached its iteration limit.

## Medium-confidence items

9 medium-confidence items.

| ID | Item | Why medium |
|---|---|---|
| M1 | `AbstractLambdaPollLoop` is the runtime loop used by native (custom runtime) Quarkus Lambdas; on managed Java runtimes the AWS runtime sets the property | Inference from the source and the AWS env var page |
| M2 | `quarkus.dynamodb.interceptors=com.amazonaws.xray.interceptors.TracingInterceptor` as the way to trace Quarkiverse-managed clients; also grouped here: the inference that `aws-xray-recorder-sdk-aws-sdk-v2-instrumentor` is outside `XrayBuildStep` native registration | Combination of two High facts |
| M3 | Whether `quarkus.<extension>.telemetry.enabled` and `quarkus.dynamodb.interceptors` are fixed at build time | The table header applies to the page; per-key markers were not visible to the tool |
| M4 | JVM-only X-Ray use without `quarkus-amazon-lambda-xray` | The guide scopes the extension to native builds |
| M5 | Illustrative method bodies (A7, A8, `OrderService`) and the X-Ray SDK reading `com.amazonaws.xray.traceHeader` in native Quarkus | Class shapes come from pages; bodies do not |
| M6 | ADOT github.io pages are undated (copyright 2020-2023) and partly rendered | Undated page |
| M7 | Versions managed by the quarkus-bom 3.40.1.1 POM (`aws-xray-recorder-sdk-aws-sdk-v2` 2.18.3, OTel API 1.62.0, `opentelemetry-aws-sdk-2.2` 2.28.1-alpha; the same BOM manages `aws-lambda-java-core` 1.4.0 and `aws-lambda-java-events` 3.16.1, carried by other skills of the family) | Partial read of the BOM (L3), no verbatim quote recorded (family rule 13) |
| M8 | The AWS Lambda Layer for OpenTelemetry does not support OS-only runtimes or Quarkus native | Absence of evidence |
| M9 | No end-to-end route from `quarkus-opentelemetry` to X-Ray on a Quarkus 3.40 Lambda is documented | Absence of evidence in pages read through summarisation (L6); the Quarkus 3.40 guides do not mention AWS Lambda |

## Coverage limits

6 coverage limits (parts of pages not read, or read through summarisation).

| ID | Limit |
|---|---|
| L1 | The Quarkus AWS Lambda guide X-Ray section was returned under a quote limit of about 125 characters; wording outside quotes is tool paraphrase |
| L2 | GitHub directory listings of `extensions/amazon-lambda-xray` are partial; the runtime module showed only `resources/META-INF` |
| L3 | quarkus-bom 3.40.1.1 read in 5 windows with targeted extraction only (`aws`, `opentelemetry`); other entries not reviewed |
| L4 | Quarkiverse 3.23.x DynamoDB page read to 100,000 of 104,004 characters |
| L5 | The ADOT Java layer ARN table is not rendered by the tool |
| L6 | All pages were read through WebFetch summarisation; quoted sentences are marked, everything else is paraphrase |

## Source differences

3 source differences (not contradictions of family facts; the research found none).

| ID | Difference |
|---|---|
| D1 | X-Ray SDK version: AWS pages show `aws-xray-recorder-sdk-bom` 2.11.0 as an example; quarkus-bom manages 2.18.3. Follow the Quarkus BOM |
| D2 | ADOT Java layer runtimes: legacy wrapper page Java 8, 11, 17; new layer page Java 11, 17, 21; neither lists `java25` or `provided.al2023` |
| D3 | The Lambda java-tracing Gradle example uses `aws-xray-recorder-sdk-aws-sdk` (v1 handler) next to the v2 instrumentor; the X-Ray SDK pages pair `-aws-sdk-v2` with `-aws-sdk-v2-instrumentor` |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) UDP exporter wiring | SKILL.md Ask First C2; otel-export-routes route (a) | U1 |
| (unverified) AWS propagator through `quarkus.otel.propagators` | SKILL.md Ask First C2; otel-export-routes route (a) | U2 |
| (unverified) Lambda layer with `quarkus-opentelemetry` | SKILL.md Ask First C2; otel-export-routes route (b) | U3 |
| (unverified) SigV4 on the OTLP exporter | SKILL.md Ask First C2; otel-export-routes route (c) | U4 |
| (unverified) batch span loss | always-do A9 | U5 |
| (unverified) SnapStart re-initialisation | SKILL.md Ask First C4; ask-first C4 | U6 |
| (unverified) remote sampler | SKILL.md Ask First C5; ask-first C5 | U7 |
| (unverified) invalid annotation key handling | never-do F5; evaluation-scenarios 4 | U8 |
| (unverified) breaking changes 3.34 to 3.39 | migration-notes | U9 |
| (unverified) Powertools tracing in Quarkus | SKILL.md scope and Ask First C1; ask-first C1; evaluation-scenarios 3 | U10 |
| (unverified) mock event server trace header | verification-loop Tests | U11 |
| (unverified) context-missing default | verification-loop Tests | U12 |
| (medium confidence) poll loop and runtime mode; property route on native | SKILL.md Ask First C4; ask-first C4; never-do F3; lambda-and-api-gateway; evaluation-scenarios 2 | M1 |
| (medium confidence) interceptor on Quarkiverse clients; instrumentor outside `XrayBuildStep` | SKILL.md Ask First C6; ask-first C6 | M2 |
| (medium confidence) telemetry key build time or runtime | SKILL.md Quick Reference; always-do A6 | M3 |
| (medium confidence) JVM-only X-Ray use | always-do A3; ask-first C1 | M4 |
| (medium confidence) illustrative bodies, header property in native | always-do A7, A8; never-do F3; lambda-and-api-gateway | M5 |
| (medium confidence) undated ADOT pages | otel-export-routes route (b) | M6 |
| (medium confidence) BOM-managed versions | SKILL.md Version Context; always-do A6; verification-loop steps 2 and 3 | M7 |
| (medium confidence, absence of evidence) layer and native | otel-export-routes route (b); ask-first C4 | M8 |
| (medium confidence, absence of evidence) no documented OTel to X-Ray route | SKILL.md Version Context risk and Ask First C1, C2; ask-first C1; otel-export-routes; evaluation-scenarios 5 | M9 |
| coverage limits | register only; ask-first C6 (L4); migration-notes (L3) | L1 to L6 |
| source differences | SKILL.md Version Context (D1); otel-export-routes (D2); migration-notes (D1 to D3) | D1 to D3 |

## Source Bibliography

All read 2026-10-28.

**Quarkus 3.40, registry, source at 3.40.1.1, Quarkiverse 3.23.x**

| # | URL | Used for |
|---|---|---|
| S1 | https://quarkus.io/version/3.40/guides/aws-lambda | X-Ray section, Mode=Active, 256 MB (L1) |
| S2 | https://quarkus.io/version/3.40/guides/opentelemetry | otel keys, defaults, exporter, propagators, sampler, simple (read in full, 2 windows) |
| S3 | https://quarkus.io/version/3.40/guides/opentelemetry-tracing | `@WithSpan`, `Tracer`, EUSP PII, native note, serverless simple |
| S4 | https://quarkus.io/version/3.40/guides/aws-lambda-snapstart | absence of tracing guidance |
| S5 | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-xray/3.40.1.1/quarkus-amazon-lambda-xray-3.40.1.1.pom | name, description, dependencies |
| S6 | https://repo1.maven.org/maven2/io/quarkus/quarkus-bom/3.40.1.1/quarkus-bom-3.40.1.1.pom | managed versions (L3) |
| S7 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-xray/deployment/src/main/java/io/quarkus/amazon/lambda/xray/XrayBuildStep.java | native-image registrations |
| S8 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-xray/runtime/src/main/resources/META-INF/quarkus-extension.yaml | status stable |
| S9 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AbstractLambdaPollLoop.java | trace header to system property |
| S10 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AmazonLambdaApi.java | `Lambda-Runtime-Trace-Id` constant |
| S11 | https://github.com/quarkusio/quarkus/tree/3.40.1.1/extensions/amazon-lambda-xray | module layout (L2) |
| S12 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/opentelemetry.html | `telemetry.enabled`, SQS propagator, GenAI capture |
| S13 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html | DynamoDB telemetry key, interceptors (L4) |
| S14 | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40 | no tracing items |

**AWS official**

| # | URL | Used for |
|---|---|---|
| S15 | https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html | Active/PassThrough, permissions, sampling, segments, unsupported mappings |
| S16 | https://docs.aws.amazon.com/lambda/latest/dg/java-tracing.html | options, published-version rule, `Restore` subsegment |
| S17 | https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html | `_X_AMZN_TRACE_ID`, `com.amazonaws.xray.traceHeader`, `AWS_XRAY_*` |
| S18 | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java.html | maintenance notice, BOM 2.11.0 example, annotation visibility |
| S19 | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html | maintenance mode 2026-02-25 |
| S20 | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html | concept mapping, `aws.xray.annotations` |
| S21 | https://docs.aws.amazon.com/xray/latest/devguide/xray-migration-opentelemetry.html | Java OTel dependencies, Lambda manual recipe |
| S22 | https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html | header format and security, 50 annotations, 64 kB, 30 days |
| S23 | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-segment.html | annotation key and value rules |
| S24 | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-java-awssdkclients.html | `TracingInterceptor`, DynamoDB subsegment |
| S25 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLPEndpoint.html | traces endpoint, SigV4, HTTP only, limits |
| S26 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLPGettingStarted.html | Transaction Search prerequisite |
| S27 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals-Enable-LambdaMain.html | AWS Lambda Layer for OpenTelemetry |
| S28 | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-xray.html | REST API tracing |
| S29 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html | HTTP API: no X-Ray |
| S30 | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-configuring-xray-sampling-rules.html | stage sampling rules |
| S31 | https://docs.aws.amazon.com/powertools/java/latest/core/tracing/ | pointer only; Quarkus not mentioned |
| S32 | https://aws-otel.github.io/docs/getting-started/lambda/lambda-java | legacy ADOT wrapper layer (undated, older documentation under aws-otel.github.io; provenance only, no High claim rests on it, M6) |
| S33 | https://aws-otel.github.io/docs/getting-started/lambda | new layer, `/opt/otel-instrument` (undated, L5; older documentation under aws-otel.github.io; provenance only, M6) |

Family facts applied: rows on Quarkus 3.40 LTS, SnapStart, Quarkiverse 3.23.0, HTTP and REST extensions, X-Ray maintenance mode, the API Gateway feature split (HTTP API trace starts at the Lambda segment, High) and `BatchGetTraces` with Transaction Search of `workspace/quarkus-aws-saas/_family_facts_v3.40.md`. Community sources: none used.
