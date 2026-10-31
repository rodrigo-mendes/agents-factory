# Migration Notes

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. The 3.40 migration guide has no Lambda, AWS, Funqy or vertx-http item and says "Quarkus 3.40 LTS is the direct continuation of 3.39 so we don't expect any changes requiring manual intervention in 3.40" (last edited 2026-10-01; https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40). Changes between 3.33 and 3.39 were not read, so their absence is (unverified). Inherited 3.31 changes (`quarkus-junit5` renamed `quarkus-junit`, `quarkus.https.*` removal) apply as family facts.

## Template defect, not an API change

The REST extension's native SAM template still declares `Runtime: provided` ([F4](./never-do-patterns.md#f4-copying-the-rest-native-runtime-provided-severity-high)). When moving a REST native function to 3.40, take the runtime from the [U1 decision](../../developing-quarkus-amazon-lambda-v3-40/blueprints/ask-first-decisions.md#c1-jvm-snapstart-or-native), not from the template.

## Upgrade steps (representative)

1. Set the Quarkus platform BOM to 3.40.1.1 (archetype version `3.40.1.1`).
2. `./mvnw install` and diff `target/sam.jvm.yaml` and `target/sam.native.yaml` against the values in Terraform (handler `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest`, the runtime chosen in the U1 Ask-First decision, native env `DISABLE_SIGNAL_HANDLERS: true`).
3. For a REST API, confirm binary media types `*/*`.
4. Re-check the `quarkus.lambda-http.*` keys against the [3.40 defaults](./build-output-and-artifact-contract.md#configuration-keys).
5. Re-read the 3.40 guide: both extensions are preview and backward compatibility is not guaranteed.

## Compatibility matrix

| Dependency | Min | Max | Notes |
|---|---|---|---|
| Quarkus | 3.40.1.1 | 3.40.x | version-locked |
| JDK (build) | 17 | page not recorded | guide prerequisite "JDK 17+ installed with `JAVA_HOME` configured appropriately" |
| Lambda runtime (JVM) | `java21` | page not recorded | generated `sam.jvm.yaml`; the runtime choice is in the U1 skill |
| Lambda runtime (native) | `provided.al2023` | page not recorded | HTTP template value; REST template says `provided` (F4); pairing is (medium confidence) |
| Maven | 3.9.16 | page not recorded | listed by the guide, paraphrased by the tool (medium confidence) |
| `com.amazonaws:aws-lambda-java-core` | managed by the Quarkus BOM | page not recorded | declared in the HTTP POM, not in the REST POM's direct list |
| `org.eclipse.microprofile.jwt:microprofile-jwt-auth-api` | managed | page not recorded | declared in both POMs |
