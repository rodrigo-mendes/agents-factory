# Packaging and Artifact Contract

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. IaC is out of scope here: Terraform belongs to `provisioning-aws-lambda-v6`, never SAM or CDK.

## Create the project

```bash
# Representative - adapt to your environment
mvn archetype:generate \
  -DarchetypeGroupId=io.quarkus \
  -DarchetypeArtifactId=quarkus-amazon-lambda-archetype \
  -DarchetypeVersion=3.40.1.1
```

The guide gives the archetype coordinates; command flags beyond the coordinates are (medium confidence). Alternative: code.quarkus.io with the `quarkus-amazon-lambda` extension; Gradle users run `gradle wrapper` afterwards ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)).

## Dependency

```xml
<!-- Quarkus 3.40.1.1: version from the Quarkus BOM -->
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-amazon-lambda</artifactId>
</dependency>
```

Transitives (POM 3.40.1.1): `quarkus-amazon-lambda-common` brings `aws-lambda-java-core` and `aws-lambda-java-events` (excludes `joda-time`); also `quarkus-core`, `quarkus-arc`, `quarkus-jackson`, `quarkus-devservices`, `jackson-datatype-joda` ([POM](https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda/3.40.1.1/quarkus-amazon-lambda-3.40.1.1.pom), [common POM](https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-common/3.40.1.1/quarkus-amazon-lambda-common-3.40.1.1.pom)). The `aws-lambda-java-*` versions are managed by the Quarkus BOM; the versions page is not recorded.

## Handler lifecycle

```java
// Quarkus 3.40.1.1 (illustrative bodies, medium confidence)
// init: CDI beans are built at boot (cold start, or before the snapshot with SnapStart)
@ApplicationScoped
public class ProcessingService {
    public OutputObject process(InputObject in) { return new OutputObject(); }
}

// usage: one invocation = one handleRequest call on the selected @Named handler
@Named("test")
public class TestLambda implements RequestHandler<InputObject, OutputObject> {
    @Inject ProcessingService service;   // injection works because QuarkusStreamHandler bootstraps Quarkus
    @Override
    public OutputObject handleRequest(InputObject input, Context context) {
        return service.process(input);
    }
}
```

CDI details: skill `developing-quarkus-arc-v3-40`.

## Artifact contract consumed by Terraform

| Contract item | JVM build | Native build | Source |
|---|---|---|---|
| Package | `target/function.zip` | `target/function.zip`, executable renamed `bootstrap` | https://quarkus.io/version/3.40/guides/aws-lambda |
| Runtime | `java21` or `java17.al2023` (`java25`: Ask First C2) | `provided.al2023` (pairing: medium confidence) | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html |
| Handler | `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest` | not stated by the guide (unverified) | https://quarkus.io/version/3.40/guides/aws-lambda |
| Environment | `QUARKUS_LAMBDA_HANDLER` (optional override) | `DISABLE_SIGNAL_HANDLERS=true`, optional `QUARKUS_LAMBDA_HANDLER` | https://quarkus.io/version/3.40/guides/all-config |
| Memory | the guide's container section uses 256 MB and says the 128 MB default "may be too small" | same | https://quarkus.io/version/3.40/guides/aws-lambda |
| SnapStart | optional: `ApplyOn=PublishedVersions` plus a published version or alias | not supported | https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html |
| Extra zip content | `src/main/zip.jvm/` | `src/main/zip.native/` (a custom `bootstrap` script there makes the executable be named `runner`) | https://quarkus.io/version/3.40/guides/aws-lambda |

`manage.sh` (`create`, `delete`, `update`, `invoke`; prefix `native` for native) and `sam.*.yaml` are generated helpers and read `LAMBDA_ROLE_ARN`. They are not the deployment path of this family, but they help a local smoke test: `sam local invoke --template target/sam.jvm.yaml --event payload.json` (needs Docker) ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)).

## Dev mode and mock event server (detail: `testing-quarkus-amazon-lambda-v3-40`)

- In dev and test mode the extension "boots up a mock AWS Lambda event server"; it is also started for `@QuarkusIntegrationTest`, "so will work with native binaries too".
- Ports: dev 8080 (`quarkus.lambda.mock-event-server.dev-port`, env `QUARKUS_LAMBDA_MOCK_EVENT_SERVER_DEV_PORT`), test 8081 (`quarkus.lambda.mock-event-server.test-port`); `0` means random.
- Disable with `quarkus.lambda.mock-event-server.enabled=false`; the reference says the setting "will start event server even if quarkus.devservices.enabled=false" (default `true`, medium confidence, M9).
- Use the `mock-event-server.*` names. The reference also lists `quarkus.lambda.dev-port` and `quarkus.lambda.test-port`; they are not deprecated, but the mock-server start-up code reads only the `mock-event-server.*` names (medium confidence, from source at tag 3.40.1.1).
- "For your unit tests, you can also invoke on the mock event server using any HTTP client you want." ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda), [all-config](https://quarkus.io/version/3.40/guides/all-config))

## Scope-limited integration notes

- `quarkus-amazon-lambda-xray` exists; the guide says to add it for native builds, enable active tracing and use at least 256 MB. Detail belongs to `tracing-quarkus-lambda-v3-40`.
- AWS SDK clients: the guide pins an old `aws.sdk2.version` example (`2.10.69`) and points to Quarkiverse extensions. Do not reuse that version; see `integrating-quarkus-amazon-data-v3-40` and `integrating-quarkus-amazon-messaging-v3-40`.
- HTTPS from native: `quarkus.ssl.native=true` plus bundled `cacerts` and a bootstrap script passing `-Djavax.net.ssl.trustStore` ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)).
- Funqy: the 3.40 guide body neither mentions nor recommends it; it appears only as the navigation link "Funqy AWS Lambda binding" (medium confidence, absence of evidence, M10).

## Verification Loop

```bash
# Representative - adapt to your environment (Quarkus 3.40.1.1)
./mvnw quarkus:dev            # mock event server on :8080 (dev)
./mvnw test                   # mock event server on :8081 (test)
./mvnw install                # expected: target/function.zip, manage.sh, bootstrap-example.sh, sam.jvm.yaml, sam.native.yaml
unzip -l target/function.zip  # native build: expected entry 'bootstrap'
grep -n "quarkus.lambda.handler" src/main/resources/application.properties   # expected: one value when more than one handler class exists
grep -rn "quarkus.snapstart.enable=" src/main/resources/ && echo "deprecated since 3.26: use quarkus.snapstart.enabled"
```
