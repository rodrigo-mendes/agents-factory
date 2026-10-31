# Ask-First Decisions

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Every decision here is put to the user; none has a default.

## C1. JVM, SnapStart or native

JVM + SnapStart and native are mutually exclusive: SnapStart does not support OS-only runtimes ([AWS SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)). Never choose for the user.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. JVM `function.zip` on `java21` or `java17.al2023` (`java25`: see C2, Java 25 with Quarkus 3.40 is (unverified)), no SnapStart | Simplest build, no GraalVM; full JVM library compatibility | Cold start includes JVM and Quarkus boot | Infrequent or latency-tolerant invocations |
| B. JVM + SnapStart | AWS: "as low as sub-second startup performance"; no extra SnapStart cost on Java managed runtimes | Published versions or aliases only; no provisioned concurrency, EFS, S3 Files, ephemeral storage above 512 MB; uniqueness and connection-state work; Java snapshots deleted after 14 days without invocation (version `Inactive`, next invoke `SnapStartNotReadyException`; a rollback to an old version has to wait for `Active`) | Latency-sensitive APIs and flows "at scale" |
| C. Native `function.zip` (`bootstrap`) on an OS-only runtime | Guide: "smaller memory footprint and faster cold boot startup time" | Native build (GraalVM or Mandrel, Linux binary, container build on non-Linux); no SnapStart; `DISABLE_SIGNAL_HANDLERS=true`; native-only extras such as `quarkus.ssl.native=true` plus `cacerts` for HTTPS | Memory or cold-start sensitive, native-compatible dependencies |

- Pairing option C with `provided.al2023` is an inference (medium confidence): the guide does not name that runtime; AWS lists `provided.al2023` as the only supported OS-only runtime ([AWS runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)).
- AWS: SnapStart works best "at scale"; infrequently invoked functions "might not experience the same performance improvements". Use provisioned concurrency instead when "strict cold start latency requirements" cannot be met by SnapStart.
- The native build guide lists 4-8 GB of build-host RAM in its table (medium confidence, M11; read to 100,000 of 101,875 characters, L1) ([native guide](https://quarkus.io/version/3.40/guides/building-native-image)).
- Ask: "JVM, JVM + SnapStart, or native? Latency target, invocation frequency, use of provisioned concurrency, EFS or large ephemeral storage, native compatibility of dependencies, CI capacity for native builds?"

## C2. Java runtime identifier (JVM builds)

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `java21` | Matches the Java 21 builder images of the 3.40 native guide | page not recorded | First candidate to propose (medium confidence); not a documented default |
| `java25` | Newest runtime | Quarkus 3.40 support of Java 25 not confirmed on a page read (unverified) | Team standardised on 25 and has tested it |
| `java17.al2023` | Matches the guide minimum "JDK 17+" | Older language level | Bytecode must stay at 17 |

Avoid `java17` (AL2, deprecation 2027-06-30). Ask: "Which Java level does the project compile to? The runtime must be at least that level." Source: [AWS runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html), [aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda).

## C3. SnapStart optimisations (when option B is chosen)

The guide says the optimisations are "automatically enabled" with the AWS Lambda extension; the reference also lists `quarkus.snapstart.full-warmup` (default `true`), which the guide does not mention ([SnapStart guide](https://quarkus.io/version/3.40/guides/aws-lambda-snapstart), [all-config](https://quarkus.io/version/3.40/guides/all-config)).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Defaults | More work done before the snapshot | Static initialisation is captured in the snapshot (uniqueness review needed) | Most functions |
| Custom `META-INF/quarkus-preload-classes.txt` (one class per line, built from `-verbose:class` CloudWatch logs) | More classes warm | Maintenance of the list | Measured cold-start gaps |
| Priming in `beforeCheckpoint` | Clients ready after restore | Must respect the uniqueness and connection rules | SDK or HTTP clients on the hot path |
| `JAVA_TOOL_OPTIONS=-XX:+TieredCompilation -XX:TieredStopAtLevel=1` | Guide: "recommended to use tiered compilation when using SnapStart" | Peak JIT performance (inference, medium confidence) | SnapStart functions |

Individual switches (the first three default `true`, medium confidence, M9): `quarkus.snapstart.preload-classes`, `quarkus.snapstart.generate-application-class-list`, `quarkus.snapstart.initialize-classes`; `quarkus.snapstart.enabled=false` turns the optimisations off. Priming in a static block "may prevent the native compilation" (guide). Ask: "Does init-time state need to be unique, and should clients be primed in a CRaC hook or a static block?"

## C4. Memory and timeout

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| 128 MB (AWS default) | Cost | The guide says the 128 MB default "may be too small" (container section) | Not the guide's starting point |
| 256 MB or more | Boot CPU share | Cost per millisecond | The guide's example uses `--memory-size 256`; X-Ray needs "at least the 256MB" |
| Higher memory for JVM cold start | Shorter init (CPU proportional to memory; 1,769 MB is about 1 vCPU) | Cost | Measure with AWS Lambda Power Tuning (named on the AWS memory page) |
| Timeout above the 3 s default (maximum 900 s) | Covers a JVM first invocation | Longer stuck invocations | Whether 3 s is enough for a JVM Quarkus cold first call is (unverified); ask for measured duration |

Do not hard-code numbers beyond what the guide states. Source: [memory](https://docs.aws.amazon.com/lambda/latest/dg/configuration-memory.html), [timeout](https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html), [aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda).

## C5. Typed vs stream handler

| Option | Optimizes | Best when |
|---|---|---|
| `RequestHandler<I, O>` (guide sample `TestLambda`) | Jackson binding; the common runtime depends on `quarkus-jackson` (POM) | Stable, Jackson-mappable payloads (criterion: medium confidence) |
| `RequestStreamHandler` (guide sample `StreamLambda`) | Full control of the payload bytes | Raw or non-JSON payloads (criterion: medium confidence) |

Ask: "Is the payload shape stable and Jackson-mappable?" Source: [aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda), [common POM](https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-common/3.40.1.1/quarkus-amazon-lambda-common-3.40.1.1.pom).

## C6. Restore-time budget

The Quarkus 3.40 SnapStart guide says "Restoration is limited to 2 seconds." AWS says runtime load plus `afterRestore()` hooks must complete within the timeout limit (10 seconds) or Lambda throws `SnapStartTimeoutException` ([SnapStart guide](https://quarkus.io/version/3.40/guides/aws-lambda-snapstart), [AWS hooks](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks-java.html)). Both quotes are High; which limit applies is (unverified) (register U10). Keep `afterRestore` work minimal and ask how much work it does.

## C7. Native handler value and AWS event input types

- The guide does not state the handler setting for a native (OS-only) function (unverified). Do not invent one; ask which value the deployment tooling expects.
- `aws-lambda-java-events` is on the classpath through `quarkus-amazon-lambda-common` 3.40.1.1, but the 3.40 guide does not document SQS, SNS, S3 or EventBridge classes as handler input (unverified). Do not present them as documented; ask for the event source.
