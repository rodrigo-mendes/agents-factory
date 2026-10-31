---
name: quarkus-lambda-code-standards
description: "Code standards for Quarkus 3.40 AWS Lambda Java: thin handlers, tenant from the verified token, secrets, JSON logs with MDC, Quarkiverse 3.23.0 SDK clients, per-entry error checks, idempotency, offline tests. Use when editing or reviewing Java of a Quarkus Lambda that uses quarkus-amazon-lambda, -http or -rest."
applyTo: "**/src/main/java/**/*.java,**/src/test/java/**/*.java"
---

# Quarkus Lambda code standards (Quarkus 3.40, amazon-services 3.23.0)

Technical facts live in the nine knowledge skills named below. This rule states what to check and
where to look; it does not duplicate skill bodies. Tags `(unverified)` and `(medium confidence)`
from a skill apply here too.

Activation: a glob cannot test file content, so the pattern covers Maven/Gradle main and test Java
sources only. Apply this rule **only when the build declares** `quarkus-amazon-lambda`,
`quarkus-amazon-lambda-http` or `quarkus-amazon-lambda-rest`; otherwise ignore it.

Overlap: the OCI `java-functions-*` rules govern OCI Functions projects, a different cloud and
project kind; they do not apply here. Quarkus Lambda that also uses Camel Quarkus: the
camel-quarkus-integrator rules also load, the more restrictive wins. For clean-code and refactor
questions see `quarkus-clean-code`. Quarkus 4 and Quarkiverse 4.0.0.Beta* are out of scope.

## Skills

| Need | Skill |
|---|---|
| Plain handlers, handler string, packaging, SnapStart | `developing-quarkus-amazon-lambda-v3-40` |
| HTTP API / REST API handlers, event mapping | `developing-quarkus-amazon-lambda-http-v3-40` |
| Cognito, roles, tenant from token | `securing-quarkus-lambda-cognito-v3-40` |
| DynamoDB, S3, HTTP client, credentials | `integrating-quarkus-amazon-data-v3-40` |
| SQS, SNS, EventBridge, SSM, Secrets Manager | `integrating-quarkus-amazon-messaging-v3-40` |
| Offline tests | `testing-quarkus-amazon-lambda-v3-40` |
| JSON logs, MDC | `logging-quarkus-lambda-v3-40` |
| Traces | `tracing-quarkus-lambda-v3-40` |
| Custom metrics | `monitoring-quarkus-lambda-v3-40` |

## Always

- Keep the handler string `QuarkusStreamHandler::handleRequest` and select the user class with
  `quarkus.lambda.handler`; keep handlers and resources thin (`developing-quarkus-amazon-lambda-v3-40`).
- Take the tenant from a verified token claim; a path tenant must only equal it, answer 403 otherwise
  (`securing-quarkus-lambda-cognito-v3-40`, `multi-tenant-isolation`).
- Read secrets from Secrets Manager or SSM; keep the default credentials chain
  (`integrating-quarkus-amazon-messaging-v3-40`, `integrating-quarkus-amazon-data-v3-40`).
- Log JSON through JBoss Logging (`logging-quarkus-lambda-v3-40`).
- Inject SDK clients through CDI and add the HTTP client artifact explicitly
  (`integrating-quarkus-amazon-data-v3-40`).
- Check the per-entry result of every batch publish; return `SQSBatchResponse` from SQS handlers;
  make every event handler idempotent (`integrating-quarkus-amazon-messaging-v3-40`).
- Close every `S3 ResponseInputStream`; paginate Query and Scan (`integrating-quarkus-amazon-data-v3-40`).
- Test against the mock event server with `quarkus-junit` and RestAssured
  (`testing-quarkus-amazon-lambda-v3-40`).

## Ask First

- MDC in JVM mode: put `AWSRequestId` and `tenantId` yourself and clear them in `finally` (medium confidence, logging M2); `requestId` in family rule 7 names the concept, the MDC key is `AWSRequestId`.

- JVM, JVM + SnapStart or native; HTTP client type; tracing stack; metric approach; tenant isolation
  tier: each skill marks these as ADR decisions, never a default. Ask, then record the ADR.
- Anything a loaded skill lists in its Ask-First table.

## Never

- Take the tenant from the path, a header or the body alone.
- Put secrets or static access keys in environment-variable literals, `application.properties`, logs
  or traces; do not log `System.getenv()` or the whole event (`logging-quarkus-lambda-v3-40`).
- Add Log4j dependencies (`logging-quarkus-lambda-v3-40`).
- Write EMF through the Quarkus logger: use one raw stdout line (`monitoring-quarkus-lambda-v3-40`).
- Use `quarkus-test-amazon-lambda` or `LambdaClient` (removed in 3.31) (`testing-quarkus-amazon-lambda-v3-40`).
- Treat HTTP 200 of a batch publish as full success, or throw from an SQS handler for one bad record.
- Use an unbounded id (`requestId`, `userId`, unbounded `tenantId`) as a metric dimension.
- Create unique ids or secrets at init when SnapStart is on (`developing-quarkus-amazon-lambda-v3-40`).

## Verify

- Grep for `log4j`, `quarkus-test-amazon-lambda`, `LambdaClient`, `AWS_SECRET_ACCESS_KEY` and
  `System.getenv()`: review each match against the skills.
- Grep for `Log.info(` near EMF JSON and for `tenant` read from `@PathParam` without a claim check.
- Run `./mvnw test` (or `mvn test`) after any change.
