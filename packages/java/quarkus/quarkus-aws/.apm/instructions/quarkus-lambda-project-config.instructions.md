---
name: quarkus-lambda-project-config
description: "Build and runtime configuration of Quarkus 3.40 Lambda projects: Quarkus BOM, Quarkiverse amazon-services BOM 3.23.0, quarkus-logging-json, SnapStart and mock-event-server property names, dev/test profiles. Use when editing pom.xml or application.properties/yaml of a Quarkus Lambda."
applyTo: "**/pom.xml,**/src/main/resources/application.properties,**/src/main/resources/application.yaml,**/src/main/resources/application.yml"
---

# Quarkus Lambda project configuration (Quarkus 3.40, amazon-services 3.23.0)

Exact coordinates, defaults and property names are in the skills; refer there instead of
restating them. Tags `(unverified)` and `(medium confidence)` in a skill apply here too. The
orchestrator-verified family facts are carried by the skills listed below.

Activation: these globs match any Maven project and any application config. Apply this rule
**only when the build declares** `quarkus-amazon-lambda`, `quarkus-amazon-lambda-http` or
`quarkus-amazon-lambda-rest`; otherwise ignore it.

Overlap: OCI `java-functions-project-config` governs OCI Functions (different project kind). Camel
Quarkus Lambda modules also load the camel-quarkus-integrator rules; the more restrictive wins.

## Skills

- `developing-quarkus-amazon-lambda-v3-40`: handler, `function.zip`, SnapStart keys, runtimes.
- `developing-quarkus-amazon-lambda-http-v3-40`: `-http` vs `-rest`, `enable-security`.
- `integrating-quarkus-amazon-data-v3-40`, `integrating-quarkus-amazon-messaging-v3-40`: BOM, HTTP
  client artifact, credentials, config sources.
- `logging-quarkus-lambda-v3-40`: `quarkus-logging-json`, profile switches.
- `testing-quarkus-amazon-lambda-v3-40`: `mock-event-server` keys, test dependencies.

## Always

- Import the Quarkus 3.40 BOM and `io.quarkiverse.amazonservices:quarkus-amazon-services-bom:3.23.0`;
  declare the extensions without `<version>` (`integrating-quarkus-amazon-data-v3-40`).
- Add exactly one HTTP client artifact matching `quarkus.<svc>.sync-client.type`; add
  `url-connection-client` for SQS, SNS and EventBridge (`integrating-quarkus-amazon-messaging-v3-40`).
- Add `quarkus-logging-json` and set `%dev.` and `%test.quarkus.log.console.json.enabled=false`
  (`logging-quarkus-lambda-v3-40`).
- Write `quarkus.snapstart.enabled` (`developing-quarkus-amazon-lambda-v3-40`).
- Write `quarkus.lambda.mock-event-server.dev-port` / `test-port` (`testing-quarkus-amazon-lambda-v3-40`).
- Keep exactly one HTTP framework with `-http`/`-rest`; set `quarkus.lambda-http.enable-security=true`
  when the authorizer identity is needed (`developing-quarkus-amazon-lambda-http-v3-40`).
- Keep `quarkus.lambda.handler` equal to the handler's `@Named` value.
- Verify with `./mvnw clean verify` (or `mvn`), then check `target/function.zip` exists.

## Ask First

- The short mock-server keys `quarkus.lambda.test-port` / `dev-port` exist and are not deprecated, but the start-up code reads only `quarkus.lambda.mock-event-server.*` (medium confidence, testing M9): prefer the `mock-event-server.*` names; confirm before relying on the short ones.

- JVM, JVM + SnapStart or native: an ADR decision, never a default
  (`developing-quarkus-amazon-lambda-v3-40`). It also drives the HTTP client choice and the Java
  runtime identifier.
- X-Ray SDK vs OpenTelemetry (`tracing-quarkus-lambda-v3-40`) and the metric approach
  (`monitoring-quarkus-lambda-v3-40`).
- Dev Services provider and `endpoint-override` in the test profile (`testing-quarkus-amazon-lambda-v3-40`).

## Never

- Use Quarkiverse `4.0.0.Beta*` or any Quarkus 4 coordinate (`integrating-quarkus-amazon-data-v3-40`).
- Put a `<version>` on an extension managed by the BOM, or mix BOM versions.
- Write `quarkus.snapstart.enable` or `quarkus.log.console.json.enable` (deprecated).
- Add Log4j dependencies (`logging-quarkus-lambda-v3-40`).
- Add `quarkus-test-amazon-lambda` (removed in 3.31) (`testing-quarkus-amazon-lambda-v3-40`).
- Enable SnapStart on a native build, or enable `quarkus.log.console.json.pretty-print`.
- Put static AWS keys or secrets in `application.properties`, or set a global `endpoint-override`
  to localhost (`integrating-quarkus-amazon-data-v3-40`).
- Keep `QUARKUS_AWS_LAMBDA_FORCE_USER_NAME` outside local `sam local` tests.

## Verify

- Grep `pom.xml` for `4.0.0.Beta`, `log4j` and `quarkus-test-amazon-lambda`.
- Grep properties for `snapstart.enable\b`, `json.enable\b`, `lambda.test-port` (advisory: medium confidence), `endpoint-override`
  and `aws.credentials.type=static`.
- Run `./mvnw dependency:tree -Dincludes=io.quarkiverse.amazonservices` and check one BOM version.
