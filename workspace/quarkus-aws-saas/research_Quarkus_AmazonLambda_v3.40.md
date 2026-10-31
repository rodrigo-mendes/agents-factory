# Research: Quarkus AWS Lambda extension (`quarkus-amazon-lambda`) on Quarkus 3.40 LTS (3.40.1.1)

Unit U1 of the quarkus-aws-saas family. Future skill: `developing-quarkus-amazon-lambda-v3-40` (package `quarkus-aws`).
Source item: "write AWS Lambdas with Quarkus (JVM, native, SnapStart)".
Family facts applied as given: `workspace/quarkus-aws-saas/_family_facts_v3.40.md`, `workspace/_family_facts_v3.40.md`.
Family rules applied as given: `workspace/quarkus-aws-saas/_family_rules_v3.40.md`, `workspace/_family_rules_v3.40.md`, and the evidence/tag policy in `.claude/skills/building-agent-packages/blueprints/policy/`.

All pages were read on **2026-10-28** through the WebFetch tool. Sentences in quotes were returned verbatim by the tool; paraphrased statements are marked as paraphrase where it matters. Pages read only in part are listed as coverage limits (L-ids) in the Research Gaps section.

---

## Metadata

```yaml
Full_Name: Quarkus AWS Lambda extension (io.quarkus:quarkus-amazon-lambda), plain (non-HTTP) handlers
Target_Version: Quarkus 3.40 LTS, patch 3.40.1.1 (extension and archetype 3.40.1.1)
Release_Date: Quarkus 3.40 released 2026-09-30; 3.40.1.1 released 2026-10-19 (family fact, https://quarkus.io/releases)
Support_Status: LTS, community-maintained until 2027-09-30 (family fact, https://quarkus.io/releases)
Primary_Docs: https://quarkus.io/version/3.40/guides/aws-lambda
Secondary_Docs: https://quarkus.io/version/3.40/guides/aws-lambda-snapstart ; https://quarkus.io/version/3.40/guides/all-config ; https://quarkus.io/version/3.40/guides/building-native-image
Registry: https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda/3.40.1.1/quarkus-amazon-lambda-3.40.1.1.pom
Platform_Docs: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html ; https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html
Official_Repo: https://github.com/quarkusio/quarkus (extensions/amazon-lambda) (page not recorded: not fetched)
Research_Date: 2026-10-28
Domain_Complexity: Standard
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 4
Unverified_Count: 9
Irresolvable_Count: 0
Research_Quality_Score: 87%   # ~70 sourced claims; 9 unverified; 0 irresolvable -> (70-9)/70
Execution_Notes: >
  Caller constraints honoured: no sub-agents (P2.parallel skipped), no plan mode (scope approval relayed by
  the caller from PIPELINE_STATE.md#approvals; recorded here as a relay, not as an approval by this agent),
  file written directly instead of via research-synthesizer.
```

---

## Executive Summary

`quarkus-amazon-lambda` (Quarkus 3.40.1.1, POM name "Quarkus - Amazon Lambda - Runtime", description "Write AWS Lambda functions") lets a Quarkus 3.40 application implement a plain AWS Lambda handler as a CDI bean. The developer writes a class that implements `RequestHandler<?, ?>` or `RequestStreamHandler`, the Lambda function's handler is always `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest` ("This handler bootstraps Quarkus and wraps your actual handler so that injection can be performed"), and the build produces `function.zip`, `manage.sh`, `bootstrap-example.sh`, `sam.jvm.yaml` and `sam.native.yaml` in `target/` (https://quarkus.io/version/3.40/guides/aws-lambda, read 2026-10-28). The same project can be built as a JVM artifact for a Java managed runtime (`java21`, `java25`, `java17.al2023`) or as a GraalVM/Mandrel native executable, renamed `bootstrap` inside `function.zip`, for an OS-only runtime. The Quarkus 3.40 guide does not name `provided.al2023`; it says "AWS Lambda Custom (Provided) Runtime" and its container example uses the image `public.ecr.aws/lambda/provided`. AWS lists `provided.al2023` as the only supported OS-only runtime (`provided.al2` deprecated 2026-07-31, `provided` deprecated 2024-01-08) (https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html, read 2026-10-28). Pairing Quarkus native with `provided.al2023` is therefore an inference (medium confidence), as the family facts already state.

For Quarkus 3.40 the relevant changes are configuration-level, not API-level. The SnapStart guide still shows `quarkus.snapstart.enable`, but the 3.40 configuration reference marks it "deprecated since `3.26`: use `quarkus.snapstart.enabled` instead". The reference also lists `quarkus.snapstart.full-warmup` (default `true`), which the SnapStart guide does not mention (https://quarkus.io/version/3.40/guides/all-config, read in part 2026-10-28). The handler property `quarkus.lambda.handler` maps to the environment variable `QUARKUS_LAMBDA_HANDLER`. SnapStart applies only to JVM builds on Java managed runtimes: AWS says OS-only runtimes "are not supported", so it is not available for Quarkus native (https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html, read 2026-10-28). Choosing JVM + SnapStart or native is an Ask-First decision (family rule 3), never a default.

The three critical patterns: (1) keep the Lambda handler string `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest` and select the user handler with `quarkus.lambda.handler` plus a matching `@Named`; (2) when deploying native, set `DISABLE_SIGNAL_HANDLERS=true` and ship the `function.zip` that contains `bootstrap`; (3) with SnapStart, make state that depends on uniqueness after restore (CRaC `afterRestore` hook or handler-time generation), invoke only published versions or aliases, and keep a strong reference to each registered `org.crac.Resource`. Domain complexity is **Standard**: one extension with two build modes, a platform runtime matrix, and SnapStart constraints, but no security or multi-service surface in this unit (that belongs to U2 to U5).

---

## Architectural Guardrails

> Confidence legend: 🟢 High (versioned official page or official platform page read 2026-10-28) | 🟡 Medium (unversioned/partly read page, or inference) | 🔴 Low (community or unverified, verify before use)
> Family evidence rule applied: a single versioned official source is enough for High. The template's "fewer than 2 sources means Medium" downgrade is superseded by `_family_rules` rule 5 and `policy/evidence-rule.md`.

### ✅ Mandatory Patterns

**A1. Lambda handler string is fixed to `QuarkusStreamHandler::handleRequest`**
> Confidence: 🟢 High | [✓✓ Triangulated | aws-lambda guide prose (2026-10-28) + same guide's container `CMD` (2026-10-28) + family fact row 4]
- Why: "Do not change the handler switch. This must be hardcoded to `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest`." "This handler bootstraps Quarkus and wraps your actual handler so that injection can be performed."
- Code (artifact contract value, Quarkus 3.40.1.1):
  ```text
  # Lambda function "handler" setting (JVM managed runtime)
  io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28)

**A2. Exactly one handler deployed, selected by `quarkus.lambda.handler` and a matching CDI name**
> Confidence: 🟢 High | [✓✓ Triangulated | aws-lambda guide (2026-10-28) + all-config reference (2026-10-28)]
- Why: a handler class must implement `RequestHandler<?, ?>` or `RequestStreamHandler`. With none, the build fails ("It must find a class in your project that implements this interface, or it will throw a build time failure"). With several, the build also fails unless the choice is made explicit ("If it finds more than one handler class, a build time exception will also be thrown"). "The CDI name of the handler class must match the value specified within the `quarkus.lambda.handler` property." The reference describes `quarkus.lambda.handler` (env `QUARKUS_LAMBDA_HANDLER`, string) as: "Handler names are specified on handler classes using the `@jakarta.inject.Named` annotation."
- Code (Quarkus 3.40.1.1; the class shapes are from the guide, the method bodies are illustrative (medium confidence)):
  ```java
  // Quarkus 3.40.1.1 - quarkus-amazon-lambda
  import com.amazonaws.services.lambda.runtime.Context;
  import com.amazonaws.services.lambda.runtime.RequestHandler;
  import jakarta.inject.Named;

  @Named("test")
  public class TestLambda implements RequestHandler<InputObject, OutputObject> {
      @Override
      public OutputObject handleRequest(InputObject input, Context context) {
          return new OutputObject(/* ... */);
      }
  }
  ```
  ```properties
  # src/main/resources/application.properties (Quarkus 3.40)
  quarkus.lambda.handler=test
  # runtime override on the Lambda function: environment variable QUARKUS_LAMBDA_HANDLER=test
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28); https://quarkus.io/version/3.40/guides/all-config (2026-10-28, characters 0-100,000 of 232,437)

**A3. Deploy the build-produced `function.zip`; native zips carry the executable as `bootstrap`**
> Confidence: 🟢 High
- Why: the build writes `function.zip`, `manage.sh`, `bootstrap-example.sh`, `sam.jvm.yaml` and `sam.native.yaml` to `target/` (Maven) or `build/` (Gradle). For native builds the zip renames the executable to `bootstrap`, which matches the AWS OS-only runtime model. Family rule 4 makes `function.zip` the only deployment artifact; IaC defers to `provisioning-aws-lambda-v6`.
- Code:
  ```bash
  # Representative — adapt to your environment (Quarkus 3.40.1.1)
  ./mvnw install                      # JVM build   -> target/function.zip
  ./mvnw install -Dnative             # native build -> target/function.zip (contains 'bootstrap')
  ./mvnw install -Dnative -Dquarkus.native.container-build=true   # non-Linux host, needs Docker
  # Expected: target/function.zip, target/manage.sh, target/bootstrap-example.sh,
  #           target/sam.jvm.yaml, target/sam.native.yaml
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28)

**A4. Native function sets `DISABLE_SIGNAL_HANDLERS=true`**
> Confidence: 🟢 High
- Why: for native deployment "the `aws lambda create-function` call must set a specific environment variable": `--environment 'Variables={DISABLE_SIGNAL_HANDLERS=true}'`.
- Code (artifact contract, not IaC):
  ```text
  # Native (OS-only runtime) Lambda environment variables
  DISABLE_SIGNAL_HANDLERS=true
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28)

**A5. SnapStart targets published versions or aliases, never `$LATEST`**
> Confidence: 🟢 High | [✓✓ Triangulated | snapstart.html (2026-10-28) + snapstart-activate.html (2026-10-28)]
- Why: "You can use SnapStart only on published function versions and aliases that point to versions. You can't use SnapStart on a function's unpublished version ($LATEST)." Activation is `ApplyOn=PublishedVersions` followed by publishing a version; check that `OptimizationStatus` is `On` and `State` is `Active`.
- Code:
  ```bash
  # Representative — adapt to your environment (AWS CLI v2; IaC equivalent lives in provisioning-aws-lambda-v6)
  aws lambda update-function-configuration --function-name my-function --snap-start ApplyOn=PublishedVersions
  aws lambda publish-version --function-name my-function
  aws lambda get-function-configuration --function-name my-function:1
  # Expected: "SnapStart": {"ApplyOn": "PublishedVersions", "OptimizationStatus": "On"}, "State": "Active"
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html (2026-10-28)

**A6. With SnapStart, generate unique content after initialization (handler time or `afterRestore`)**
> Confidence: 🟢 High
- Why: "To maintain uniqueness when using SnapStart, you must generate unique content after initialization. This includes unique IDs, unique secrets, and entropy that's used to generate pseudorandomness." For Java, AWS names `java.security.SecureRandom` as a SnapStart-safe CSPRNG and provides the SpotBugs-based scanner `aws-lambda-snapstart-java-rules`.
- Code (pattern from the AWS page, adapted to a Quarkus handler bean (medium confidence for the adaptation)):
  ```java
  // Quarkus 3.40.1.1, JVM build with SnapStart: unique id generated in the handler, not at init
  @Named("test")
  public class TestLambda implements RequestHandler<InputObject, OutputObject> {
      private static UUID sandboxId;           // NOT initialised in a static block / @PostConstruct
      @Override
      public OutputObject handleRequest(InputObject in, Context ctx) {
          if (sandboxId == null) sandboxId = UUID.randomUUID();
          // ...
      }
  }
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/snapstart-uniqueness.html (2026-10-28)

**A7. Registered CRaC `Resource` objects need a strong reference**
> Confidence: 🟢 High
- Why: "`Context` maintains only a `WeakReference` to the registered object. If a `Resource` is garbage collected, runtime hooks do not run." The Quarkus SnapStart guide example registers an `@ApplicationScoped @Startup` bean (`HelloPriming implements Resource`) from `@PostConstruct` via `Core.getGlobalContext().register(this)`. The CDI bean instance supplies the strong reference (inference, medium confidence).
- Code (shape from https://quarkus.io/version/3.40/guides/aws-lambda-snapstart; bodies illustrative):
  ```java
  // Quarkus 3.40.1.1 - SnapStart priming via CRaC
  import io.quarkus.runtime.Startup;
  import jakarta.annotation.PostConstruct;
  import jakarta.enterprise.context.ApplicationScoped;
  import org.crac.Context;
  import org.crac.Core;
  import org.crac.Resource;

  @Startup
  @ApplicationScoped
  public class HelloPriming implements Resource {
      @PostConstruct
      void init() { Core.getGlobalContext().register(this); }

      @Override
      public void beforeCheckpoint(Context<? extends Resource> context) throws Exception {
          // prime clients here (runs before the snapshot)
      }

      @Override
      public void afterRestore(Context<? extends Resource> context) throws Exception {
          // restore uniqueness / refresh ephemeral data here
      }
  }
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks-java.html (2026-10-28); https://quarkus.io/version/3.40/guides/aws-lambda-snapstart (2026-10-28)

### ⚠️ Conditional Patterns

**C1. Build/runtime mode: JVM on a Java managed runtime (optionally with SnapStart) vs native on an OS-only runtime** (family rule 3: always Ask First, never a default)
> Confidence: 🟢 High for each fact listed; 🟡 Medium for the pairing native ↔ `provided.al2023` (the guide does not name it)
- Options: A) JVM `function.zip` on `java21` / `java25` / `java17.al2023`, without SnapStart; B) JVM + Lambda SnapStart; C) native `function.zip` (`bootstrap`) on `provided.al2023` (medium confidence).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A JVM | Simplest build, no GraalVM; full JVM library compatibility | Cold start includes JVM + Quarkus boot | Infrequent or latency-tolerant invocations |
  | B JVM + SnapStart | AWS: "as low as sub-second startup performance"; no extra SnapStart cost on Java managed runtimes | Only published versions/aliases; no provisioned concurrency, EFS, S3 Files, ephemeral storage > 512 MB; uniqueness and connection-state work; snapshots of Java functions deleted after 14 days without invocation (`SnapStartNotReadyException`) | Latency-sensitive APIs/flows "at scale" |
  | C Native | Quarkus guide: "smaller memory footprint and faster cold boot startup time" | Native build (GraalVM/Mandrel, Linux binary, container build on non-Linux); no SnapStart (OS-only runtimes not supported); `DISABLE_SIGNAL_HANDLERS=true`; native-only extras (e.g. `quarkus.ssl.native=true` + cacerts for HTTPS) | Memory/cold-start sensitive and native-compatible dependencies |

- Agent: "Ask the user: JVM, JVM + SnapStart, or native? Factors: latency SLO, invocation frequency, use of provisioned concurrency/EFS/large ephemeral storage, native compatibility of dependencies, CI capacity for native builds (4-8 GB build-host RAM per the native guide's table)."
- Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html (2026-10-28); https://quarkus.io/version/3.40/guides/building-native-image (2026-10-28, partial: 0-100,000 of 101,875 chars)

**C2. Which Java managed runtime identifier (JVM builds)**
> Confidence: 🟢 High (runtime table); 🔴 for Java 25 support by Quarkus 3.40 (unverified)
- Options: `java21` (AL2023, deprecation 2029-06-30), `java25` (AL2023, deprecation 2029-06-30), `java17.al2023` (AL2023, deprecation 2029-06-30). Avoid `java17` (AL2, deprecation 2027-06-30).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | `java21` | Matches the Java 21 builder images used by the 3.40 native guide | none recorded | Default candidate to propose (medium confidence) |
  | `java25` | Newest runtime | Quarkus 3.40 support of Java 25 not confirmed on a page read (unverified) | Team already standardised on 25 and has tested it |
  | `java17.al2023` | Matches guide minimum "JDK 17+" | Older language level | Bytecode must stay at 17 |

- Agent: "Ask which Java level the project compiles to; the runtime must be ≥ that level."
- Source: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html (2026-10-28); https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28, prerequisite "JDK 17+")

**C3. Quarkus SnapStart optimisations (when B is chosen)**
> Confidence: 🟢 High for guide statements; 🟡 for property names shown only in the partly read reference
- Options: keep the defaults (optimisations "automatically enabled" with the AWS Lambda extension; class preloading, application class list generation, class initialisation and, per the reference, `quarkus.snapstart.full-warmup=true`), or turn individual ones off (`quarkus.snapstart.preload-classes=false`, `quarkus.snapstart.generate-application-class-list=false`, `quarkus.snapstart.initialize-classes=false`, `quarkus.snapstart.enabled=false`).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Defaults | More work done before the snapshot | Static initialisation captured in the snapshot (uniqueness review needed) | Most functions |
  | Custom `META-INF/quarkus-preload-classes.txt` (one class per line, list built from `-verbose:class` CloudWatch logs) | More classes warm | Maintenance of the list | Measured cold-start gaps |
  | Priming in `beforeCheckpoint` | Clients ready after restore | Must respect uniqueness / connection rules | SDK/HTTP clients on the hot path |
  | `JAVA_TOOL_OPTIONS=-XX:+TieredCompilation -XX:TieredStopAtLevel=1` | Guide: "recommended to use tiered compilation when using SnapStart" | Peak JIT performance (inference, medium confidence) | SnapStart functions |

- Agent: "Ask whether the function has init-time state that must be unique, and whether clients should be primed in a CRaC hook or a static block (the static block "may prevent the native compilation")."
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-snapstart (2026-10-28); https://quarkus.io/version/3.40/guides/all-config (2026-10-28, chars 100,000-232,437)

**C4. Memory and timeout sizing**
> Confidence: 🟢 High for platform limits; 🟡 Medium for the Quarkus-specific starting values
- Options: memory 128 MB (AWS default) to 10,240 MB in 1-MB steps (CPU proportional; 1,769 MB ≈ 1 vCPU); timeout default 3 s, max 900 s.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | 128 MB | Cost | Guide: default 128MB "may be too small" (container section); X-Ray needs "at least the 256MB" | Not recommended for JVM Quarkus (medium confidence) |
  | ≥ 256 MB | Boot CPU share | Cost per ms | Starting point named by the guide (`--memory-size 256`) |
  | Higher memory for JVM cold start | Shorter init (CPU proportional to memory) | Cost | Measure with AWS Lambda Power Tuning (named on the AWS memory page) |
  | Timeout above default 3 s | Covers JVM first invocation | Longer stuck invocations | Whether 3 s is enough for a JVM cold first call is unverified; ask for measured duration |

- Agent: "Ask for measured init/duration; do not hard-code numbers beyond 'memory ≥ 256 MB' from the guide."
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-memory.html (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html (2026-10-28); https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28)

**C5. `RequestHandler<I, O>` (typed, Jackson) vs `RequestStreamHandler` (raw streams)**
> Confidence: 🟢 High that both are supported; 🟡 for the selection criteria
- Options: typed POJO handler (guide sample `TestLambda implements RequestHandler<InputObject, OutputObject>`) or stream handler (`StreamLambda implements RequestStreamHandler`).
- Tradeoffs: typed handler gives Jackson binding (the common runtime depends on `quarkus-jackson`, POM); stream handler gives full control of the payload bytes (criteria: medium confidence).
- Agent: "Ask whether the payload shape is stable and Jackson-mappable."
- Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28); https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-common/3.40.1.1/quarkus-amazon-lambda-common-3.40.1.1.pom (2026-10-28)

### 🚫 Forbidden Patterns

**F1. Pointing the Lambda handler at the user class**
> Severity: high
> Confidence: 🟢 High
- Why: the guide says the handler "must be hardcoded" to `QuarkusStreamHandler::handleRequest`, which bootstraps Quarkus and performs injection.
- Impact: Quarkus is not bootstrapped, so no CDI injection happens in the user handler (per the guide's rationale).
- ❌ Wrong:
  ```text
  handler = com.example.TestLambda::handleRequest
  ```
- ✅ Correct:
  ```text
  handler = io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest
  # user handler chosen with quarkus.lambda.handler=test (or env QUARKUS_LAMBDA_HANDLER=test)
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28)

**F2. Several handler classes and no `quarkus.lambda.handler`**
> Severity: moderate
> Confidence: 🟢 High
- Why: "If it finds more than one handler class, a build time exception will also be thrown." The guide's sample has `test`, `unused` and `stream` beans and selects one with `quarkus.lambda.handler=test`.
- Impact: build failure.
- ❌ Wrong:
  ```java
  @Named("test")   public class TestLambda   implements RequestHandler<InputObject, OutputObject> { }
  @Named("stream") public class StreamLambda implements RequestStreamHandler { }
  // application.properties: (no quarkus.lambda.handler)
  ```
- ✅ Correct:
  ```properties
  quarkus.lambda.handler=test
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28)

**F3. Enabling SnapStart on a native (OS-only runtime) Quarkus function**
> Severity: high
> Confidence: 🟢 High | [✓✓ Triangulated | snapstart.html + runtimes-provided.html (both 2026-10-28)]
- Why: "Other managed runtimes ... and OS-only runtimes are not supported." Native Quarkus runs on the `provided` runtime family (AWS: OS-only runtimes host "Java GraalVM Native Image").
- Impact: SnapStart is not available; the configuration is rejected or has no effect (exact failure mode unverified).
- ❌ Wrong:
  ```text
  runtime = provided.al2023 ; package = native function.zip ; SnapStart ApplyOn = PublishedVersions
  ```
- ✅ Correct:
  ```text
  JVM function.zip on java21 | java25 | java17.al2023 + SnapStart ApplyOn=PublishedVersions + published version/alias
  # or: native function.zip on provided.al2023 without SnapStart (C1 decision)
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/runtimes-provided.html (2026-10-28)

**F4. Using deprecated runtimes `provided`, `provided.al2` or `java17` (AL2) for new functions**
> Severity: moderate
> Confidence: 🟢 High
- Why: `provided` was deprecated 2024-01-08 and `provided.al2` 2026-07-31. `java17` (AL2) deprecates 2027-06-30, while `java17.al2023`, `java21` and `java25` deprecate 2029-06-30. The 3.40 guide's container example still uses `public.ecr.aws/lambda/provided` and `public.ecr.aws/lambda/java:11`: do not copy those image tags.
- Impact: no security patches after deprecation; function create and update are blocked later.
- ❌ Wrong:
  ```text
  runtime = provided.al2      # or provided, or java17
  ```
- ✅ Correct:
  ```text
  runtime = provided.al2023   # native (pairing: medium confidence)
  runtime = java21            # JVM (or java25 / java17.al2023)
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html (2026-10-28); https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28)

**F5. Generating unique IDs, secrets or RNG seeds during init in a SnapStart function**
> Severity: high
> Confidence: 🟢 High
- Why: one snapshot initialises many execution environments, so content created at init "might not be unique when it is reused across execution environments".
- Impact: duplicate IDs or tokens across environments; weakened randomness.
- ❌ Wrong:
  ```java
  @ApplicationScoped class Ids { final String instanceId = UUID.randomUUID().toString(); } // created before snapshot
  ```
- ✅ Correct:
  ```java
  // generate in the handler, or reset in afterRestore(); use java.security.SecureRandom for randomness
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/snapstart-uniqueness.html (2026-10-28)

**F6. Registering a CRaC resource without a strong reference**
> Severity: moderate
> Confidence: 🟢 High
- Why: the global context holds only a `WeakReference`.
- Impact: the hooks silently never run.
- ❌ Wrong:
  ```java
  Core.getGlobalContext().register(new MyResource());
  ```
- ✅ Correct:
  ```java
  Resource myResource = new MyResource();      // keep the reference (e.g. a field of an @ApplicationScoped bean)
  Core.getGlobalContext().register(myResource);
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks-java.html (2026-10-28)

**F7. Deploying a native build without `DISABLE_SIGNAL_HANDLERS=true`**
> Severity: moderate
> Confidence: 🟢 High (requirement); failure mode (unverified)
- Why: the guide says the native `create-function` "must set" this variable.
- Impact: page does not state it (unverified).
- ❌ Wrong:
  ```text
  environment = {}            # native function
  ```
- ✅ Correct:
  ```text
  environment = { DISABLE_SIGNAL_HANDLERS = "true" }
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28)

---

## Migration Guide

> Confidence: 🟢 High for the deprecation (versioned config reference); no dedicated "3.40 amazon-lambda" migration page was found | Sources: https://quarkus.io/version/3.40/guides/all-config (2026-10-28, partial) + https://quarkus.io/version/3.40/guides/aws-lambda-snapstart (2026-10-28)

P2.changelog result: no Quarkus 3.40 migration note specific to `quarkus-amazon-lambda` was found on the pages read. A full read of the Quarkus wiki migration guides for 3.32 to 3.40 was not done (see U9).

**Breaking changes / deprecations relevant to this unit**:
- ⚠️ Migration Note: `quarkus.snapstart.enable` → `quarkus.snapstart.enabled` ("This property is deprecated since `3.26`: use `quarkus.snapstart.enabled` instead."). The Quarkus 3.40 SnapStart guide still shows `quarkus.snapstart.enable=true|false`, so prefer the reference name.
- Test artifact rename `quarkus-junit5` → `quarkus-junit` (Quarkus 3.31; inherited family fact). The 3.40 aws-lambda guide's Gradle sample already uses `testImplementation 'io.quarkus:quarkus-junit'`. Testing detail belongs to U6.
- Platform-side: `provided.al2` deprecated 2026-07-31; AL2 reaches end of life 2026-06-30; `java17` (AL2) deprecates 2027-06-30. Move to AL2023 runtimes (https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html, 2026-10-28).
- Both `quarkus.lambda.mock-event-server.dev-port` / `test-port` and `quarkus.lambda.dev-port` / `test-port` appear in the 3.40 reference. Whether the latter pair is deprecated was not visible (unverified). Use the `mock-event-server.*` names that the guide uses.

**Upgrade Steps** (representative):
1. Set the Quarkus platform/BOM to 3.40.1.1 (archetype `io.quarkus:quarkus-amazon-lambda-archetype:3.40.1.1`).
2. Replace `quarkus.snapstart.enable` with `quarkus.snapstart.enabled` if present.
3. Replace `quarkus-junit5` with `quarkus-junit` (see U6).
4. Move runtimes to `java21` / `java25` / `java17.al2023` (JVM) or `provided.al2023` (native, medium confidence).
5. Rebuild and redeploy `function.zip`; with SnapStart, publish a new version (a snapshot is per published version).

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| JDK (build) | 17 | page not recorded | Guide prerequisite "JDK 17+" (High) |
| Maven | 3.9.16 (as listed) | — | Guide prerequisite "Apache Maven 3.9.16" (High) |
| GraalVM / Mandrel (native) | "GraalVM for JDK 21 is required" | — | building-native-image 3.40 (High, partial read); default builder `quay.io/quarkus/ubi9-quarkus-mandrel-builder-image:jdk-21`. See the contradiction note in Research Gaps (G1) |
| `aws-lambda-java-core`, `aws-lambda-java-events` | managed by the Quarkus BOM | — | Transitive via `quarkus-amazon-lambda-common` 3.40.1.1 (joda-time excluded); versions page not recorded |
| `org.crac` API | page not recorded | — | Not a declared dependency of `quarkus-core` 3.40.1.1 (only a `runnerParentFirstArtifact` entry `org.crac:crac`). AWS shows `org.crac:crac:1.4.0`. Whether to add it explicitly: (unverified) |
| Lambda Java runtime | `java17.al2023` | `java25` | Java 25 with Quarkus 3.40 (unverified) |
| Lambda OS-only runtime | `provided.al2023` | — | Only supported OS-only runtime (High); Quarkus pairing (medium confidence) |

---

## Implementation Blueprint

> Confidence: 🟢 High for the steps quoted from the 3.40 guide; code bodies marked illustrative are (medium confidence)

**Step 1: Create the project (Quarkus 3.40.1.1)**
```bash
# Representative — adapt to your environment
mvn archetype:generate \
  -DarchetypeGroupId=io.quarkus \
  -DarchetypeArtifactId=quarkus-amazon-lambda-archetype \
  -DarchetypeVersion=3.40.1.1
# Alternative: code.quarkus.io with the quarkus-amazon-lambda extension. Gradle users run `gradle wrapper` afterwards.
```
Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28). The exact archetype command flags beyond the GAV are (medium confidence): the tool returned the GAV, not the full command line.

**Step 2: Dependency**
```xml
<!-- Quarkus 3.40.1.1: version from the Quarkus BOM -->
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-amazon-lambda</artifactId>
</dependency>
```
Transitives (POM 3.40.1.1): `quarkus-amazon-lambda-common` → `aws-lambda-java-core`, `aws-lambda-java-events` (excludes `joda-time`), `quarkus-core`, `quarkus-arc`, `quarkus-jackson`, `quarkus-devservices`, `jackson-datatype-joda`. Event classes for SQS/SNS/S3/EventBridge therefore sit on the classpath through `aws-lambda-java-events`. The 3.40 guide does not document their use (see U7).

**Step 3: Handler lifecycle (init, usage, cleanup)**
```java
// Quarkus 3.40.1.1 — init: CDI beans built at boot (cold start, or before the snapshot with SnapStart)
@ApplicationScoped
public class ProcessingService {                 // illustrative (medium confidence)
    public OutputObject process(InputObject in) { /* business logic */ return new OutputObject(); }
}

// usage: one invocation = one handleRequest call on the selected @Named handler
@Named("test")
public class TestLambda implements RequestHandler<InputObject, OutputObject> {
    @Inject ProcessingService service;           // injection works because QuarkusStreamHandler bootstraps Quarkus
    @Override
    public OutputObject handleRequest(InputObject input, Context context) {
        return service.process(input);
    }
}
// cleanup: no explicit per-invocation cleanup is documented in the 3.40 guide (unverified)
```

**Step 4: Stream handler variant**
```java
// Quarkus 3.40.1.1
@Named("stream")
public class StreamLambda implements RequestStreamHandler {
    @Override
    public void handleRequest(InputStream in, OutputStream out, Context context) throws IOException {
        in.transferTo(out);                      // illustrative (medium confidence)
    }
}
```

**Step 5: Dev mode / mock event server (only what the handler needs; detail in U6)**
- In dev and test mode the extension "boots up a mock AWS Lambda event server"; it is also started for `@QuarkusIntegrationTest`, "so will work with native binaries too".
- Ports: dev 8080 (`quarkus.lambda.mock-event-server.dev-port`, env `QUARKUS_LAMBDA_MOCK_EVENT_SERVER_DEV_PORT`), test 8081 (`quarkus.lambda.mock-event-server.test-port`). `0` means random. Disable with `quarkus.lambda.mock-event-server.enabled=false`. The reference describes `enabled` as "Setting to true will start event server even if quarkus.devservices.enabled=false" (default `true`).
- "For your unit tests, you can also invoke on the mock event server using any HTTP client you want."
- Source: https://quarkus.io/version/3.40/guides/aws-lambda ; https://quarkus.io/version/3.40/guides/all-config (2026-10-28)

**Step 6: Build and artifact contract consumed by Terraform (no IaC here; see `provisioning-aws-lambda-v6`)**

| Contract item | JVM build | Native build | Source / confidence |
|---|---|---|---|
| Package | `target/function.zip` | `target/function.zip` with executable renamed `bootstrap` | guide (High) |
| Runtime | `java21` / `java25` / `java17.al2023` | `provided.al2023` | runtimes page (High); native pairing (medium confidence) |
| Handler | `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest` | Handler value for the OS-only runtime is not stated by the guide (unverified) | guide (High) / (unverified) |
| Env vars | `QUARKUS_LAMBDA_HANDLER` (optional override) | `DISABLE_SIGNAL_HANDLERS=true` (+ optional `QUARKUS_LAMBDA_HANDLER`) | guide + all-config (High) |
| Memory | ≥ 256 MB suggested by the guide (container section; X-Ray) | same | guide (High) for the text; general applicability (medium confidence) |
| SnapStart | optional, `ApplyOn=PublishedVersions` + published version/alias | not supported | AWS (High) |
| Extra zip content | `src/main/zip.jvm/` | `src/main/zip.native/` (a custom `bootstrap` script there makes the executable be named `runner`) | guide (High) |

`manage.sh` (`create`, `delete`, `update`, `invoke`, prefix `native` for native) and `sam.*.yaml` are generated helpers. Under family rule 4 they are not the deployment path for this family (IaC is Terraform), but they help with local smoke tests (`sam local invoke --template target/sam.jvm.yaml --event payload.json`, Docker needed). `manage.sh` reads `LAMBDA_ROLE_ARN`.

**Step 7: SnapStart (JVM only)**: see A5 to A7 and C3. Restore limits: AWS says the runtime load plus `afterRestore()` hooks must complete within 10 seconds (`SnapStartTimeoutException`). The snapshot-time init can run up to 15 minutes (130 s or the configured timeout, whichever is higher). The Quarkus guide says "Restoration is limited to 2 seconds" (conflict, see G2).

**Integration notes (scope-limited)**:
- `quarkus-amazon-lambda-xray`: exists; the guide says to add it for native builds, enable active tracing, and use at least 256 MB. Detail belongs to U12.
- AWS SDK clients: the guide pins an old `aws.sdk2.version` `2.10.69` example and points to Quarkiverse extensions. Out of scope (U4/U5): do not reuse that version.
- HTTPS from native: `quarkus.ssl.native=true` plus bundled `cacerts` and a bootstrap script passing `-Djavax.net.ssl.trustStore` (guide, High). Detail belongs to whichever unit owns outbound HTTP.
- Funqy: the 3.40 guide body does not mention or recommend Funqy; it appears only as the navigation link "Funqy AWS Lambda binding".

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment (Quarkus 3.40.1.1)
./mvnw quarkus:dev            # mock event server on :8080 (dev); expected log: Quarkus started (exact text unverified)
./mvnw test                   # mock event server on :8081 (test)
./mvnw install                # expected: target/function.zip + manage.sh + bootstrap-example.sh + sam.jvm.yaml + sam.native.yaml
unzip -l target/function.zip  # native build: expected entry 'bootstrap'
grep -n "quarkus.lambda.handler" src/main/resources/application.properties   # expected: exactly one value when >1 handler class
grep -rn "quarkus.snapstart.enable=" src/main/resources/ && echo "deprecated since 3.26: use quarkus.snapstart.enabled"
sam local invoke --template target/sam.jvm.yaml --event payload.json          # optional local smoke test, needs Docker
```

**Mocking**: unit tests invoke the mock event server with any HTTP client (guide). Test patterns, `@QuarkusTest`/`@QuarkusIntegrationTest` usage and the event-server HTTP contract belong to U6. For SnapStart uniqueness, AWS offers the SpotBugs plugin `aws-lambda-snapstart-java-rules` (https://docs.aws.amazon.com/lambda/latest/dg/snapstart-uniqueness.html).
```java
// Quarkus 3.40.1.1 — illustrative only (medium confidence); endpoint path of the mock server is covered in U6
@QuarkusTest
class TestLambdaTest {
    @Test void handlesInput() { /* POST an InputObject JSON to the mock event server via RestAssured; assert OutputObject */ }
}
```

---

## Production Readiness

- **Performance**: native: "smaller memory footprint and faster cold boot startup time" (Quarkus guide). SnapStart: "as low as sub-second startup performance", working best "at scale"; infrequently invoked functions "might not experience the same performance improvements" (AWS). Tiered compilation flag recommended with SnapStart (Quarkus SnapStart guide).
- **Scalability**: SnapStart resumes new environments from one cached snapshot. It is incompatible with provisioned concurrency; use provisioned concurrency instead when "strict cold start latency requirements" cannot be met by SnapStart (AWS).
- **Cost**: SnapStart has no additional cost on Java managed runtimes. Duration charges include runtime hooks (AWS snapstart.html).
- **Monitoring**: SnapStart version states `Pending` / `Active` / `Inactive` / `Failed`. After 14 days without invocation (Java) the snapshot is deleted and the next call returns `SnapStartNotReadyException` (AWS snapstart-activate.html). Logging, metrics and tracing belong to U11 to U13.
- **Security**: with SnapStart, the runtime uses container credentials (`AWS_CONTAINER_CREDENTIALS_FULL_URI`, `AWS_CONTAINER_AUTHORIZATION_TOKEN`) instead of access-key env vars "to prevent credentials from expiring before the function is restored" (AWS). Network connections opened at init are "not guaranteed" after restore; AWS SDK connections "in most cases" resume. Refresh ephemeral data (temporary credentials, cached timestamps) in the handler. Secrets come from Secrets Manager/SSM (family rule 5; U4/U5).
- **Region**: SnapStart is available in all commercial Regions except Asia Pacific (New Zealand) and Asia Pacific (Taipei) (AWS, 2026-10-28). The Quarkus guide says only "not in all regions".

---

## Reference Implementations

- Quarkus 3.40 AWS Lambda guide samples (`TestLambda`, `UnusedLambda`, `StreamLambda`): https://quarkus.io/version/3.40/guides/aws-lambda
- Quarkus 3.40 SnapStart priming example (`HelloPriming implements org.crac.Resource`): https://quarkus.io/version/3.40/guides/aws-lambda-snapstart
- AWS CRaC runtime-hook example (`CRaCDemo`): https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks-java.html
- AWS SnapStart uniqueness examples (UUID in handler, `SecureRandom`): https://docs.aws.amazon.com/lambda/latest/dg/snapstart-uniqueness.html
- AWS SnapStart scanner: https://github.com/aws/aws-lambda-snapstart-java-rules (page not recorded: not fetched)
- Quarkus source for the extension (page not recorded: not fetched): https://github.com/quarkusio/quarkus/tree/3.40.1.1/extensions/amazon-lambda (tag path unverified)

---

## Source Bibliography

**Primary (versioned Quarkus 3.40 / registry)**
| # | URL | Read | Coverage | Used for |
|---|---|---|---|---|
| S1 | https://quarkus.io/version/3.40/guides/aws-lambda | 2026-10-28 | Full per tool ("not truncated"; ~40-50k chars estimated by the tool), read in 3 passes | handler rules, build outputs, native, env var, mock server, X-Ray, Funqy absence, container images |
| S2 | https://quarkus.io/version/3.40/guides/aws-lambda-snapstart | 2026-10-28 | Full per tool (~20k chars incl. navigation), 2 passes | SnapStart properties, preload file, CRaC priming, 2-s restore claim, tiered compilation |
| S3 | https://quarkus.io/version/3.40/guides/all-config | 2026-10-28 | All 232,437 chars read in 3 windows (0-100k, 100k-200k, 200k-end); only `quarkus.lambda.*` / `quarkus.snapstart.*` extracted | env var names, defaults, `enable` deprecation, `full-warmup` |
| S4 | https://quarkus.io/version/3.40/guides/building-native-image | 2026-10-28 | Partial: 0-100,000 of 101,875 chars (L1) | GraalVM for JDK 21 requirement, builder image, container build |
| S5 | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda/3.40.1.1/quarkus-amazon-lambda-3.40.1.1.pom | 2026-10-28 | Full | artifact existence, name/description, deps |
| S6 | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-common/3.40.1.1/quarkus-amazon-lambda-common-3.40.1.1.pom | 2026-10-28 | Full | transitive `aws-lambda-java-core` / `-events` |
| S7 | https://repo1.maven.org/maven2/io/quarkus/quarkus-core/3.40.1.1/quarkus-core-3.40.1.1.pom | 2026-10-28 | Full | `org.crac:crac` not a declared dependency |

**Primary (AWS Lambda Developer Guide, current pages)**
| # | URL | Read | Used for |
|---|---|---|---|
| S8 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html | 2026-10-28 | runtime identifiers and deprecation dates |
| S9 | https://docs.aws.amazon.com/lambda/latest/dg/runtimes-provided.html | 2026-10-28 | OS-only runtime, GraalVM Native Image use case, `provided.al2023` |
| S10 | https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html | 2026-10-28 | supported runtimes, limitations, regions, pricing, compatibility |
| S11 | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html | 2026-10-28 | activation, states, 14-day deletion, credentials |
| S12 | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks.html | 2026-10-28 | hook purposes (index page) |
| S13 | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks-java.html | 2026-10-28 | CRaC elements, order, 10-s restore limit, WeakReference |
| S14 | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-uniqueness.html | 2026-10-28 | uniqueness, CSPRNG, scanner |
| S15 | https://docs.aws.amazon.com/lambda/latest/dg/configuration-memory.html | 2026-10-28 | memory range, default, vCPU ratio |
| S16 | https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html | 2026-10-28 | timeout default/max |

**Family facts (orchestrator-verified, applied as given)**: https://quarkus.io/releases (via `_family_facts_v3.40.md`); https://quarkus.io/guides/aws-lambda (unversioned URL used in the family-facts table; this research used the versioned S1); https://camel.apache.org/camel-quarkus/latest/ (inherited GraalVM 25.0.4.1 fact, see G1).

**Validation (community)**: none used.

---

## Research Gaps

```
Gap G1 (family-fact contradiction candidate): GraalVM version for native builds.
  Quarkus 3.40 native guide: "GraalVM for JDK 21 is required"; default builder image ...mandrel-builder-image:jdk-21
  (https://quarkus.io/version/3.40/guides/building-native-image, read 2026-10-28, partial L1).
  Inherited family fact: "Camel Quarkus 3.40.x uses Camel 4.22.1, Quarkus 3.40.1, GraalVM 25.0.4.1"
  (https://camel.apache.org/camel-quarkus/latest/, workspace/_family_facts_v3.40.md).
Impact: which builder image / GraalVM to pin for native Lambda builds.
Workaround: do not pin a GraalVM version in the skill; use the Quarkus default builder image and say both pages exist.
Follow-up: orchestrator to decide (may be minimum vs tested version, not a true contradiction).
§7-ref: reported, not resolved by this unit (family facts are not edited here).

Gap G2 (source conflict, not a family fact): SnapStart restore time limit.
  Quarkus 3.40 SnapStart guide: "Restoration is limited to 2 seconds." (https://quarkus.io/version/3.40/guides/aws-lambda-snapstart)
  AWS: runtime load + afterRestore() must complete "within the timeout limit (10 seconds)" else SnapStartTimeoutException
  (https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks-java.html).
Impact: budget for afterRestore work.
Workaround: state the AWS 10-second platform limit as High; keep afterRestore work minimal; cite the Quarkus 2-second statement as conflicting.
Follow-up: orchestrator / human.

U1 (unverified): Lambda handler setting for the native (OS-only) function; the guide does not state it.
U2 (unverified): Quarkus 3.40 support of Java 25 at runtime (`java25`).
U3 (unverified): whether `org.crac` must be added explicitly for the SnapStart CRaC example (not a declared dep of quarkus-core 3.40.1.1).
U4 (unverified): whether `quarkus.lambda.dev-port` / `quarkus.lambda.test-port` are deprecated aliases.
U5 (unverified): failure mode of a native function without DISABLE_SIGNAL_HANDLERS=true.
U6 (unverified): exact behaviour when SnapStart is configured on an OS-only runtime (rejected vs ignored).
U7 (unverified): use of aws-lambda-java-events classes (SQSEvent, SNSEvent, S3Event, ScheduledEvent/EventBridge) as RequestHandler input types;
    the 3.40 guide does not cover them (scope said: only as far as the guide covers them -> it does not).
U8 (unverified): whether the default 3-second timeout suffices for a JVM Quarkus cold first invocation; the standard (non-SnapStart) init-phase limit was not read.
U9 (unverified): absence of breaking changes for quarkus-amazon-lambda between 3.33 and 3.40 (wiki migration guides not read).

M1 (medium confidence): native Quarkus ↔ provided.al2023 pairing (family fact wording).
M2 (medium confidence): method bodies / illustrative code (handlers, ProcessingService, test skeleton).
M3 (medium confidence): CDI bean as the strong reference for the CRaC Resource.
M4 (medium confidence): java21 as the default candidate to propose (aligned with jdk-21 builder images).
M5 (medium confidence): archetype command-line flags beyond the GAV.
M6 (medium confidence): typed vs stream handler selection criteria; tiered compilation trade-off.

L1 (coverage limit): building-native-image 3.40 read 0-100,000 of 101,875 characters.
L2 (coverage limit): all pages were read through WebFetch summarisation; verbatim quotes are marked as quotes, other wording is a paraphrase by the tool.
```

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Guardrails A2 | Environment variable name for `quarkus.lambda.handler` (guide says "an environment variable" without naming it) | Resolved: `QUARKUS_LAMBDA_HANDLER` | https://quarkus.io/version/3.40/guides/all-config (2026-10-28, chars 0-100k) |
| 1 | Implementation Step 5 | Mock event server keys, defaults, `enabled` semantics | Resolved / Added (`quarkus.lambda.dev-port`/`test-port` aliases found) | https://quarkus.io/version/3.40/guides/all-config (2026-10-28) |
| 2 | Migration Guide | `quarkus.snapstart.enable` status | Resolved: deprecated since 3.26, use `quarkus.snapstart.enabled` (⚠️ Migration Note) | https://quarkus.io/version/3.40/guides/all-config (2026-10-28, chars 100k-200k) |
| 3 | Guardrails C3 | Remaining SnapStart properties and defaults | Resolved: `preload-classes`, `initialize-classes`, `full-warmup`, `generate-application-class-list` (all default `true`) | https://quarkus.io/version/3.40/guides/all-config (2026-10-28, chars 200k-end) |
| 3 | Research Gaps | U1-U9 | Left (unverified): MAX_ITERATIONS=3 reached; not IRRESOLVABLE, as each has a follow-up page | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Standard)
- [x] All scope areas cited (handlers, CDI selection, QuarkusStreamHandler, archetype, build outputs, artifact contract, runtimes, provided.al2023 statement, SnapStart, cold start, memory/timeout, env vars, events (gap U7), X-Ray existence, dev mode/mock server, Funqy line)
- [x] Pattern counts driven by domain needs (7 / 5 / 7)
- [x] Every anti-pattern has alternative
- [x] All CLI commands marked as representative
- [x] Integration examples complete within scope (artifact contract table instead of IaC, per caller and family rule 4)
- [x] Sources dated and linked
- [x] Security documented (SnapStart credentials, uniqueness, connections)
- [x] 1+ copy-paste working example (A2 handler + properties; build commands)
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns triangulated where two sources exist (A1, A2, A5; F3); others High on a single versioned/official page per family evidence rule
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced (G1/G2 reported; U-items logged in iteration 3)

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: A1 to A7, F1 to F7 (except the failure modes tagged unverified), runtime identifiers/dates, SnapStart limitations, mock-server ports/keys, `quarkus.snapstart.enabled` rename.
- **Medium Confidence (validate with user)**: M1 to M6; any statement pairing native with `provided.al2023`; memory ≥ 256 MB as a general starting point.
- **Low Confidence (must ask human)**: U1 to U9; G1 (GraalVM 21 vs 25) and G2 (2 s vs 10 s restore limit).
- **Edge Cases (pause)**: Quarkus 3.40.1.1 is 9 days old (released 2026-10-19), but the 3.40 line is 28 days old (2026-09-30) and LTS. Pages are complete, so no pause.
- **Emergency Stop**: not triggered (official sources available; version is current LTS).
- **Decision rule**: JVM + SnapStart vs native is always C1 (Ask First), never a default (family rule 3).
