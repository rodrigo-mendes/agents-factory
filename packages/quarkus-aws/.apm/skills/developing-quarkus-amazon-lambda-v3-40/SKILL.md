---
name: developing-quarkus-amazon-lambda-v3-40
description: "Guides Quarkus 3.40 LTS plain AWS Lambda handlers with quarkus-amazon-lambda: function.zip packaging, JVM vs native, SnapStart. Use when writing non-HTTP Lambda handlers. Not for API Gateway HTTP, Cognito, AWS SDK clients, Terraform or Quarkus 4."
---

# Developing Quarkus AWS Lambda (plain handlers) 3.40

> Version lock: every claim applies to **Quarkus 3.40 LTS, patch 3.40.1.1 (`quarkus-amazon-lambda`)** only. Research date **2026-10-28**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: plain (non-HTTP) handlers, packaging, JVM vs native, SnapStart. Neighbours, by name only: `developing-quarkus-amazon-lambda-http-v3-40` (HTTP/API Gateway), `securing-quarkus-lambda-cognito-v3-40` (Cognito), `integrating-quarkus-amazon-data-v3-40` and `integrating-quarkus-amazon-messaging-v3-40` (AWS SDK clients), `testing-quarkus-amazon-lambda-v3-40` (testing in depth), `logging-quarkus-lambda-v3-40`, `tracing-quarkus-lambda-v3-40`, `monitoring-quarkus-lambda-v3-40` (observability), `provisioning-aws-lambda-v6` (Terraform), `architecting-lambda-serverless-patterns` (architecture), `developing-quarkus-arc-v3-40` (CDI), `developing-quarkus-junit-v3-40` (Quarkus tests). Quarkus 4 is out of scope.

## Version Context

| Item | Value | Source (fetched 2026-10-28) |
|---|---|---|
| Quarkus | 3.40 LTS, released 2026-09-30, community-maintained until 2027-09-30; patch 3.40.1.1 released 2026-10-19 | https://quarkus.io/releases |
| Extension | `io.quarkus:quarkus-amazon-lambda` 3.40.1.1, POM description "Write AWS Lambda functions"; archetype `quarkus-amazon-lambda-archetype` 3.40.1.1 | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda/3.40.1.1/quarkus-amazon-lambda-3.40.1.1.pom |
| Build prerequisites | JDK 17+; Maven 3.9.16 as listed by the guide (medium confidence) | https://quarkus.io/version/3.40/guides/aws-lambda |
| GraalVM (native) | "GraalVM for JDK 21 is required" is a minimum; Mandrel is recommended; `quarkus.native.builder-image` default is `mandrel`; the guide's examples use `quay.io/quarkus/ubi9-quarkus-mandrel-builder-image:jdk-21` (read to 100,000 of 101,875 characters; coverage limit L1 in the register) | https://quarkus.io/version/3.40/guides/building-native-image |
| Java managed runtimes | `java21`, `java25`, `java17.al2023` (AL2023, deprecation 2029-06-30); `java17` (AL2) deprecation 2027-06-30 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html |
| OS-only runtime | `provided.al2023` (deprecation 2029-06-30); `provided.al2` deprecated 2026-07-31; `provided` deprecated 2024-01-08 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html |
| Java 25 with Quarkus 3.40 | (unverified) | page not recorded |

**Version-lifetime risk** (as of 2026-10-28; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0 is "Upcoming" with no date on the releases page ([releases](https://quarkus.io/releases)). Pin 3.40.x.
- AWS runtime deprecations move on their own schedule: `provided.al2` 2026-07-31, `java17` (AL2) 2027-06-30, AL2023 runtimes 2029-06-30.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Ask-first decisions in depth](./blueprints/ask-first-decisions.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Packaging and artifact contract](./blueprints/packaging-and-artifact-contract.md)
- [Verification Loop](./blueprints/packaging-and-artifact-contract.md#verification-loop)
- [SnapStart](./blueprints/snapstart.md)
- [Migration notes](./blueprints/migration-notes.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Keep the Lambda handler string `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest`.** The guide says it "must be hardcoded" and it bootstraps Quarkus for injection ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)). See [patterns](./blueprints/always-do-patterns.md#1-handler-string).
- **Give the project at least one class implementing `RequestHandler<?, ?>` or `RequestStreamHandler`.** Without one the build fails ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)). See [patterns](./blueprints/always-do-patterns.md#2-handler-selection).
- **Make the `@Named` value of the handler equal `quarkus.lambda.handler`.** The CDI name must match the property ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)). See [patterns](./blueprints/always-do-patterns.md#2-handler-selection).
- **Deploy the `function.zip` written by the Quarkus build.** The guide lists it among the build outputs ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)). The native `bootstrap` rename is in [patterns](./blueprints/always-do-patterns.md#3-deployment-artifact).
- **Set `DISABLE_SIGNAL_HANDLERS=true` on a native function.** The guide says `create-function` "must set" it ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)). See [patterns](./blueprints/always-do-patterns.md#4-native-environment-variable).
- **Enable SnapStart only on published versions or aliases.** `$LATEST` is not supported ([AWS SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)). See [patterns](./blueprints/always-do-patterns.md#5-snapstart-on-published-versions).
- **Generate unique IDs, secrets and entropy after initialization when SnapStart is on.** Init-time content may repeat across execution environments ([AWS uniqueness](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-uniqueness.html)). See [patterns](./blueprints/always-do-patterns.md#6-uniqueness-after-init).
- **Keep a strong reference to every registered `org.crac.Resource`.** The context holds only a `WeakReference` ([AWS runtime hooks](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks-java.html)). See [patterns](./blueprints/always-do-patterns.md#7-crac-strong-reference).
- **Write `quarkus.snapstart.enabled`.** `quarkus.snapstart.enable` is deprecated since 3.26 ([all-config](https://quarkus.io/version/3.40/guides/all-config)). See [patterns](./blueprints/always-do-patterns.md#8-snapstart-property-name).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| JVM, JVM + SnapStart or native (never a default) | A: JVM `function.zip`, simplest build. B: JVM + SnapStart, "as low as sub-second startup", published versions only, no provisioned concurrency, EFS, S3 Files or ephemeral storage above 512 MB ([AWS SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)). C: native `function.zip` (`bootstrap`), smaller memory and faster cold boot, no SnapStart. Native on `provided.al2023` is an inference (medium confidence). See [decisions](./blueprints/ask-first-decisions.md#c1-jvm-snapstart-or-native) | "JVM, JVM + SnapStart or native? Latency target, invocation frequency, provisioned concurrency or EFS use, native compatibility of dependencies, CI capacity for native builds?" |
| Java runtime identifier (JVM builds) | `java21`, `java25`, `java17.al2023`; propose `java21` first (medium confidence); Java 25 with Quarkus 3.40 is (unverified) | "Which Java level does the project compile to? The runtime must be at least that level" |
| SnapStart optimisations | Keep defaults vs turn off `preload-classes`, `generate-application-class-list`, `initialize-classes`; custom preload list; CRaC priming; tiered compilation flag (trade-off is medium confidence) | "Does init-time state need to be unique, and are clients primed in a CRaC hook?" |
| Restore-time budget for `afterRestore` | Quarkus SnapStart guide: "Restoration is limited to 2 seconds"; AWS: runtime load plus `afterRestore()` within 10 seconds or `SnapStartTimeoutException`. Which limit applies is (unverified). Keep hooks minimal | "How much work runs in `afterRestore`?" |
| Memory and timeout | Platform range 128 to 10,240 MB, timeout default 3 s, max 900 s ([memory](https://docs.aws.amazon.com/lambda/latest/dg/configuration-memory.html), [timeout](https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html)); guide example uses 256 MB; whether 3 s covers a JVM cold first call is (unverified) | "What are the measured init and duration numbers?" |
| Typed vs stream handler | `RequestHandler<I, O>` with Jackson binding vs `RequestStreamHandler` with raw streams; selection criteria are medium confidence | "Is the payload shape stable and Jackson-mappable?" |
| Native handler setting | The guide does not state the handler value for an OS-only function (unverified) | "Which handler value does your deployment tooling expect for native?" |
| AWS event classes as input (SQS, SNS, S3, EventBridge) | The classes are on the classpath through `aws-lambda-java-events`; the 3.40 guide does not document using them as handler input (unverified) | "Which event source feeds the function?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Point the Lambda handler at the user class; the guide says the handler "must be hardcoded" ([guide](https://quarkus.io/version/3.40/guides/aws-lambda)) | Keep `QuarkusStreamHandler::handleRequest` and select the user class with `quarkus.lambda.handler` ([guide](https://quarkus.io/version/3.40/guides/aws-lambda)) |
| Ship several handler classes without `quarkus.lambda.handler`; the build throws ([guide](https://quarkus.io/version/3.40/guides/aws-lambda)) | Set `quarkus.lambda.handler=<@Named value>` ([guide](https://quarkus.io/version/3.40/guides/aws-lambda)) |
| Enable SnapStart on a native (OS-only runtime) function; AWS says OS-only runtimes "are not supported" ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)) | Pick JVM + SnapStart on a Java managed runtime, or native without SnapStart ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)) (Ask First C1) |
| Use new `provided`, `provided.al2` or `java17` (AL2) functions; all are deprecated or deprecate earlier ([AWS runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)) | Use a non-deprecated Amazon Linux 2023 runtime from the AWS runtime table; the choice is Ask First C2 ([AWS runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)) |
| Create unique IDs or secrets at init under SnapStart ([AWS uniqueness](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-uniqueness.html)) | Generate them in the handler or reset them in `afterRestore()`; use `java.security.SecureRandom` ([AWS uniqueness](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-uniqueness.html)) |
| Register a CRaC `Resource` as a temporary object; hooks do not run once it is garbage collected ([AWS hooks](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks-java.html)) | Hold the instance in a field and register that instance ([AWS hooks](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks-java.html)) |
| Deploy a native build without `DISABLE_SIGNAL_HANDLERS=true` ([guide](https://quarkus.io/version/3.40/guides/aws-lambda)) | Set `DISABLE_SIGNAL_HANDLERS=true` in the function environment ([guide](https://quarkus.io/version/3.40/guides/aws-lambda)) |
| Keep writing `quarkus.snapstart.enable` ([all-config](https://quarkus.io/version/3.40/guides/all-config)) | Write `quarkus.snapstart.enabled` ([all-config](https://quarkus.io/version/3.40/guides/all-config)) |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Handler string | `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest` | https://quarkus.io/version/3.40/guides/aws-lambda |
| User handler selection | `quarkus.lambda.handler` (env `QUARKUS_LAMBDA_HANDLER`) = `@jakarta.inject.Named` value | https://quarkus.io/version/3.40/guides/all-config |
| Build outputs | `function.zip`, `manage.sh`, `bootstrap-example.sh`, `sam.jvm.yaml`, `sam.native.yaml` in `target/` (Maven) or `build/` (Gradle) | https://quarkus.io/version/3.40/guides/aws-lambda |
| Extra zip content | `src/main/zip.jvm/` (JVM), `src/main/zip.native/` (native) | https://quarkus.io/version/3.40/guides/aws-lambda |
| Mock event server | dev 8080, test 8081 (`quarkus.lambda.mock-event-server.dev-port` / `test-port`, `0` = random, `enabled` default `true` (medium confidence, M9)) | https://quarkus.io/version/3.40/guides/all-config |
| SnapStart properties | `quarkus.snapstart.enabled` (default: page not recorded); `preload-classes`, `generate-application-class-list`, `initialize-classes`, `full-warmup` (these 4 default `true`, medium confidence, M9) | https://quarkus.io/version/3.40/guides/all-config |
| SnapStart limits | published versions/aliases only; no provisioned concurrency, EFS, S3 Files, ephemeral storage above 512 MB; Java snapshots deleted after 14 days without invocation: the version goes `Inactive` and the next invoke returns `SnapStartNotReadyException` (wait for `Active` before a rollback to an old version) | https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html ; https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html |
| SnapStart cost and regions | no extra cost on Java managed runtimes; all commercial Regions except Asia Pacific (New Zealand) and Asia Pacific (Taipei) | https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html |
| Memory and timeout (platform) | 128 MB default to 10,240 MB; 1,769 MB is about 1 vCPU; timeout default 3 s, max 900 s | https://docs.aws.amazon.com/lambda/latest/dg/configuration-memory.html ; https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html |
| Native HTTPS | `quarkus.ssl.native=true` plus bundled `cacerts` through a bootstrap script | https://quarkus.io/version/3.40/guides/aws-lambda |
| Representative commands | `./mvnw install`, `./mvnw install -Dnative`, `./mvnw install -Dnative -Dquarkus.native.container-build=true` | https://quarkus.io/version/3.40/guides/aws-lambda |

## External Resources

All fetched 2026-10-28.

- AWS Lambda guide: https://quarkus.io/version/3.40/guides/aws-lambda
- SnapStart guide: https://quarkus.io/version/3.40/guides/aws-lambda-snapstart
- Configuration reference: https://quarkus.io/version/3.40/guides/all-config
- Native image guide: https://quarkus.io/version/3.40/guides/building-native-image
- AWS Lambda runtimes: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html
- AWS SnapStart: https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
