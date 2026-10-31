# Never-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Severity wording: low, moderate, high.

## Contents

- [F1. Pointing the Lambda handler at the user class](#f1-pointing-the-lambda-handler-at-the-user-class-severity-high)
- [F2. Several handler classes and no `quarkus.lambda.handler`](#f2-several-handler-classes-and-no-quarkuslambdahandler-severity-moderate)
- [F3. SnapStart on a native (OS-only runtime) function](#f3-snapstart-on-a-native-os-only-runtime-function-severity-high)
- [F4. Deprecated runtimes for new functions](#f4-deprecated-runtimes-for-new-functions-severity-moderate)
- [F5. Unique values created during init under SnapStart](#f5-unique-values-created-during-init-under-snapstart-severity-high)
- [F6. CRaC resource without a strong reference](#f6-crac-resource-without-a-strong-reference-severity-moderate)
- [F7. Native build without `DISABLE_SIGNAL_HANDLERS=true`](#f7-native-build-without-disable_signal_handlerstrue-severity-moderate)
- [F8. Deprecated `quarkus.snapstart.enable`](#f8-deprecated-quarkussnapstartenable-severity-low)

## F1. Pointing the Lambda handler at the user class (severity: high)

The guide says the handler "must be hardcoded" to `QuarkusStreamHandler::handleRequest`, which bootstraps Quarkus and performs injection ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)). Impact: Quarkus is not bootstrapped, so no CDI injection happens in the user handler (the guide's rationale).

```text
# ❌ WRONG
handler = com.example.TestLambda::handleRequest

# ✅ CORRECT
handler = io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest
# user handler chosen with quarkus.lambda.handler=test (or env QUARKUS_LAMBDA_HANDLER=test)
```

## F2. Several handler classes and no `quarkus.lambda.handler` (severity: moderate)

"If it finds more than one handler class, a build time exception will also be thrown." The guide's sample has `test`, `unused` and `stream` beans and selects one with `quarkus.lambda.handler=test` ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)). Impact: build failure.

```java
// ❌ WRONG
@Named("test")   public class TestLambda   implements RequestHandler<InputObject, OutputObject> { }
@Named("stream") public class StreamLambda implements RequestStreamHandler { }
// application.properties: (no quarkus.lambda.handler)
```

```properties
# ✅ CORRECT
quarkus.lambda.handler=test
```

## F3. SnapStart on a native (OS-only runtime) function (severity: high)

AWS says other managed runtimes and OS-only runtimes "are not supported" by SnapStart, and lists Java GraalVM Native Image as an OS-only use case ([AWS SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html), [OS-only runtimes](https://docs.aws.amazon.com/lambda/latest/dg/runtimes-provided.html)). Impact: SnapStart is not available. Whether the configuration is rejected or ignored is (unverified).

```text
# ❌ WRONG
runtime = provided.al2023 ; package = native function.zip ; SnapStart ApplyOn = PublishedVersions

# ✅ CORRECT (the decision is Ask First: C1)
JVM function.zip on java21 | java17.al2023 + SnapStart ApplyOn=PublishedVersions + published version/alias
# or: native function.zip on an OS-only runtime without SnapStart
```

## F4. Deprecated runtimes for new functions (severity: moderate)

`provided` was deprecated 2024-01-08 and `provided.al2` 2026-07-31. `java17` (AL2) deprecates 2027-06-30; `java17.al2023`, `java21` and `java25` deprecate 2029-06-30 ([AWS runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)). The 3.40 guide's container example still uses `public.ecr.aws/lambda/provided` and `public.ecr.aws/lambda/java:11`; do not copy those image tags ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)). Impact: no security patches after deprecation; function create and update are blocked later.

```text
# ❌ WRONG
runtime = provided.al2      # or provided, or java17

# ✅ CORRECT
runtime = <a non-deprecated Amazon Linux 2023 runtime from the AWS runtime table>   # the choice is Ask First C2
```

## F5. Unique values created during init under SnapStart (severity: high)

One snapshot initialises many execution environments, so content created at init "might not be unique when it is reused across execution environments" ([AWS uniqueness](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-uniqueness.html)). Impact: duplicate IDs or tokens across environments; weakened randomness.

```java
// ❌ WRONG: created before the snapshot
@ApplicationScoped class Ids { final String instanceId = UUID.randomUUID().toString(); }

// ✅ CORRECT: generate in the handler, or reset in afterRestore(); use java.security.SecureRandom
```

## F6. CRaC resource without a strong reference (severity: moderate)

The global context holds only a `WeakReference` ([AWS hooks](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks-java.html)). Impact: the hooks silently never run.

```java
// ❌ WRONG
Core.getGlobalContext().register(new MyResource());

// ✅ CORRECT
Resource myResource = new MyResource();      // keep the reference, for example a field of an @ApplicationScoped bean
Core.getGlobalContext().register(myResource);
```

## F7. Native build without `DISABLE_SIGNAL_HANDLERS=true` (severity: moderate)

The guide says the native `create-function` "must set" this variable ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)). The failure mode when it is missing is (unverified): the page does not state it.

```text
# ❌ WRONG
environment = {}            # native function

# ✅ CORRECT
environment = { DISABLE_SIGNAL_HANDLERS = "true" }
```

## F8. Deprecated `quarkus.snapstart.enable` (severity: low)

Deprecated since 3.26 ([all-config](https://quarkus.io/version/3.40/guides/all-config)). The SnapStart guide still shows it, which is why it keeps being copied.

```properties
# ❌ WRONG
quarkus.snapstart.enable=true

# ✅ CORRECT
quarkus.snapstart.enabled=true
```
