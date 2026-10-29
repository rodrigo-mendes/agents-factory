# Always-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1, `quarkus-amazon-lambda`. Fetched 2026-10-28. Class shapes come from the guides; method bodies are illustrative (medium confidence).

## Contents

- [1. Handler string](#1-handler-string)
- [2. Handler selection](#2-handler-selection)
- [3. Deployment artifact](#3-deployment-artifact)
- [4. Native environment variable](#4-native-environment-variable)
- [5. SnapStart on published versions](#5-snapstart-on-published-versions)
- [6. Uniqueness after init](#6-uniqueness-after-init)
- [7. CRaC strong reference](#7-crac-strong-reference)
- [8. SnapStart property name](#8-snapstart-property-name)

## 1. Handler string

The guide says: "Do not change the handler switch. This must be hardcoded to `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest`." It "bootstraps Quarkus and wraps your actual handler so that injection can be performed" ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)).

```text
# Lambda function "handler" setting (JVM managed runtime)
io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest
```

## 2. Handler selection

A handler class implements `RequestHandler<?, ?>` or `RequestStreamHandler`. With none the build fails; with several it also fails unless the choice is explicit. "The CDI name of the handler class must match the value specified within the `quarkus.lambda.handler` property." The reference describes the property (env `QUARKUS_LAMBDA_HANDLER`) as: "Handler names are specified on handler classes using the `@jakarta.inject.Named` annotation." ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda), [all-config](https://quarkus.io/version/3.40/guides/all-config))

```java
// Quarkus 3.40.1.1 - quarkus-amazon-lambda (bodies illustrative, medium confidence)
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

Stream variant (shape from the guide, body illustrative, medium confidence):

```java
@Named("stream")
public class StreamLambda implements RequestStreamHandler {
    @Override
    public void handleRequest(InputStream in, OutputStream out, Context context) throws IOException {
        in.transferTo(out);
    }
}
```

## 3. Deployment artifact

The build writes `function.zip`, `manage.sh`, `bootstrap-example.sh`, `sam.jvm.yaml` and `sam.native.yaml` to `target/` (Maven) or `build/` (Gradle). For native builds the zip renames the executable to `bootstrap`. This family deploys `function.zip` only; IaC belongs to `provisioning-aws-lambda-v6` ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)).

```bash
# Representative - adapt to your environment (Quarkus 3.40.1.1)
./mvnw install                                                  # JVM build    -> target/function.zip
./mvnw install -Dnative                                         # native build -> target/function.zip (contains 'bootstrap')
./mvnw install -Dnative -Dquarkus.native.container-build=true   # non-Linux host, needs Docker
unzip -l target/function.zip                                    # native build: expected entry 'bootstrap'
```

Contract table and zip extras: [packaging](./packaging-and-artifact-contract.md).

## 4. Native environment variable

For native deployment "the `aws lambda create-function` call must set a specific environment variable": `--environment 'Variables={DISABLE_SIGNAL_HANDLERS=true}'` ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)).

```text
# Native (OS-only runtime) Lambda environment variables
DISABLE_SIGNAL_HANDLERS=true
```

## 5. SnapStart on published versions

"You can use SnapStart only on published function versions and aliases that point to versions. You can't use SnapStart on a function's unpublished version ($LATEST)." Activation is `ApplyOn=PublishedVersions`, then publish a version; check `OptimizationStatus` `On` and `State` `Active` ([AWS SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html), [activation](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html)).

```bash
# Representative - adapt to your environment (AWS CLI v2; the IaC equivalent lives in provisioning-aws-lambda-v6)
aws lambda update-function-configuration --function-name my-function --snap-start ApplyOn=PublishedVersions
aws lambda publish-version --function-name my-function
aws lambda get-function-configuration --function-name my-function:1
# Expected: "SnapStart": {"ApplyOn": "PublishedVersions", "OptimizationStatus": "On"}, "State": "Active"
```

## 6. Uniqueness after init

"To maintain uniqueness when using SnapStart, you must generate unique content after initialization. This includes unique IDs, unique secrets, and entropy that's used to generate pseudorandomness." For Java, AWS names `java.security.SecureRandom` as a SnapStart-safe CSPRNG and offers the SpotBugs scanner `aws-lambda-snapstart-java-rules` ([AWS uniqueness](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-uniqueness.html)).

```java
// Quarkus 3.40.1.1, JVM build with SnapStart: unique id generated in the handler, not at init
// (pattern from the AWS page adapted to a Quarkus handler bean: medium confidence)
@Named("test")
public class TestLambda implements RequestHandler<InputObject, OutputObject> {
    private static UUID sandboxId;           // not initialised in a static block or @PostConstruct
    @Override
    public OutputObject handleRequest(InputObject in, Context ctx) {
        if (sandboxId == null) sandboxId = UUID.randomUUID();
        // ...
    }
}
```

## 7. CRaC strong reference

"`Context` maintains only a `WeakReference` to the registered object. If a `Resource` is garbage collected, runtime hooks do not run." The Quarkus SnapStart guide registers an `@ApplicationScoped @Startup` bean (`HelloPriming implements Resource`) from `@PostConstruct` through `Core.getGlobalContext().register(this)`. That the CDI bean instance supplies the strong reference is an inference (medium confidence) ([AWS hooks](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks-java.html), [SnapStart guide](https://quarkus.io/version/3.40/guides/aws-lambda-snapstart)).

```java
// Quarkus 3.40.1.1 - SnapStart priming via CRaC (shape from the guide; bodies illustrative, medium confidence)
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

Whether `org.crac` must be added to the build explicitly is (unverified): `quarkus-core` 3.40.1.1 does not declare it (only a `runnerParentFirstArtifact` entry `org.crac:crac`); AWS shows `org.crac:crac:1.4.0`.

## 8. SnapStart property name

The 3.40 configuration reference says of `quarkus.snapstart.enable`: "This property is deprecated since `3.26`: use `quarkus.snapstart.enabled` instead." The SnapStart guide still shows the old name, so prefer the reference ([all-config](https://quarkus.io/version/3.40/guides/all-config)).

```properties
quarkus.snapstart.enabled=true
```

```bash
# Expected: no output after migration
grep -rn "quarkus.snapstart.enable=" src/main/resources/
```
