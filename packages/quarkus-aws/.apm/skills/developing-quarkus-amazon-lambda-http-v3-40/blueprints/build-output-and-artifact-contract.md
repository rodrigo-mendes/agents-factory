# Build Output and Artifact Contract

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Packaging, native prerequisites and SnapStart: [U1 skill](../../developing-quarkus-amazon-lambda-v3-40/SKILL.md).

## Contents

- [Configuration keys](#configuration-keys)
- [Build output](#build-output)
- [Artifact contract](#artifact-contract)
- [Gateway and Lambda limits](#gateway-and-lambda-limits)
- [Verification Loop](#verification-loop)

## Configuration keys

Defaults are stated per key. Source: [all-config](https://quarkus.io/version/3.40/guides/all-config) unless stated. The four `quarkus.lambda-http.*` defaults and the `mock-event-server.enabled` default come from a partly read page (L2): (medium confidence, M9) until a verbatim quote is recorded.

| Key | Env var | Type | Default | Note |
|---|---|---|---|---|
| `quarkus.lambda-http.enable-security` | `QUARKUS_LAMBDA_HTTP_ENABLE_SECURITY` | boolean | `false` (medium confidence) | opt-in identity mapping; the guide states only "add … enable-security=true" |
| `quarkus.lambda-http.map-cognito-to-roles` | `QUARKUS_LAMBDA_HTTP_MAP_COGNITO_TO_ROLES` | boolean | `true` (medium confidence) | depth: `securing-quarkus-lambda-cognito-v3-40` |
| `quarkus.lambda-http.cognito-role-claim` | `QUARKUS_LAMBDA_HTTP_COGNITO_ROLE_CLAIM` | string | `cognito:groups` (medium confidence) | the guide's example override is `cognito:roles` |
| `quarkus.lambda-http.cognito-claim-matcher` | `QUARKUS_LAMBDA_HTTP_COGNITO_CLAIM_MATCHER` | string | `[^\[\] \t]+` (medium confidence) | regex for role values |
| `quarkus.lambda.mock-event-server.enabled` | `QUARKUS_LAMBDA_MOCK_EVENT_SERVER_ENABLED` | boolean | `true` (medium confidence) | dev and test |
| `quarkus.lambda.mock-event-server.dev-port` | `QUARKUS_LAMBDA_MOCK_EVENT_SERVER_DEV_PORT` | int | `8080` | |
| `quarkus.lambda.mock-event-server.test-port` | `QUARKUS_LAMBDA_MOCK_EVENT_SERVER_TEST_PORT` | int | `8081` | the reference description says "dev mode" |
| `quarkus.http.cors.enabled` | page not recorded | boolean | `false` (medium confidence, M11) | [security-cors](https://quarkus.io/version/3.40/guides/security-cors); effect on Lambda is (unverified) |
| `quarkus.native.march` | page not recorded | string | page not recorded | the aws-lambda-http guide states a default of `x86-64-v3`; its suggestion for Lambda is `x86-64-v2` |

The four `quarkus.lambda-http.*` keys appear under both the "Amazon Lambda HTTP" and the "Amazon Lambda AWS Gateway REST API" sections of the reference. Whether they are build-time fixed is (unverified).

## Build output

`./mvnw install` writes to `target/` (Maven) or `build/` (Gradle): `function.zip` (lambda deployment file), `sam.jvm.yaml` and `sam.native.yaml` (SAM CLI deployment scripts). Family policy: IaC goes through `provisioning-aws-lambda-v6` and `provisioning-aws-api-gateway-v6`; the templates are only the source of the values below.

## Artifact contract

Values read line by line from the 3.40.1.1 templates ([HTTP jvm](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/deployment/src/main/resources/http/sam.jvm.yaml), [HTTP native](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/deployment/src/main/resources/http/sam.native.yaml), [REST jvm](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/deployment/src/main/resources/http/sam.jvm.yaml), [REST native](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/deployment/src/main/resources/http/sam.native.yaml)). MemorySize and Timeout are the template's examples, not Quarkus defaults.

| Template value | HTTP jvm | HTTP native | REST jvm | REST native |
|---|---|---|---|---|
| Handler | `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest` | `not.used.in.provided.runtimei` | same as HTTP jvm | `not.used.in.provided.runtimei` |
| Runtime | `java21` | `provided.al2023` | `java21` | `provided` (do not copy, see [F4](./never-do-patterns.md#f4-copying-the-rest-native-runtime-provided-severity-high)) |
| CodeUri | `function.zip` | `function.zip` | `function.zip` | `function.zip` |
| MemorySize | `512` | `128` | `512` | `128` |
| Timeout | `15` | `15` | `15` | `15` |
| Policies | `AWSLambdaBasicExecutionRole` | same | same | same |
| Environment | none | `DISABLE_SIGNAL_HANDLERS: true` | none | `DISABLE_SIGNAL_HANDLERS: true` |
| Event | `Type: HttpApi` | `Type: HttpApi` | `Type: Api`, `Path: /{proxy+}`, `Method: any` | same as REST jvm |
| Globals.Api | `EndpointConfiguration: REGIONAL`, `BinaryMediaTypes: "*/*"` | same | same | same |
| Output URL | `https://${ServerlessHttpApi}.execute-api.${AWS::Region}.amazonaws.com/` | same | `https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/` | same |

Whether the `Globals: Api:` block has any effect on an `HttpApi` event is (unverified). The runtime pairing native with `provided.al2023` stays (medium confidence); the runtime decision is in the U1 skill.

## Gateway and Lambda limits

| Limit | Value | Source |
|---|---|---|
| Integration timeout | HTTP API 30 s (not raisable); REST API Regional or private 50 ms to 29 s (raisable); edge-optimized not raisable | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html ; https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html |
| API Gateway payload | 10 MB (HTTP and REST, not increasable) | same two pages |
| Lambda synchronous payload | 6 MB each for request and response | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html |
| Header sizes | HTTP API 10240 bytes; REST API 20480 bytes (8000 private); Lambda 1 MB request line plus headers | same pages |
| Lambda timeout | max 900 s | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html |
| Concurrency | default 1,000 per Region vs API Gateway default throttle 10,000 rps; AWS warns more requests can arrive than Lambda can handle; 10 synchronous requests per second per execution environment | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html |

Monitoring: execution logs and gateway X-Ray tracing exist only for REST APIs; CloudWatch metrics and access logs exist for both. Observability in code: `logging-quarkus-lambda-v3-40`, `tracing-quarkus-lambda-v3-40`, `monitoring-quarkus-lambda-v3-40`.

## Verification Loop

```bash
# Representative - adapt to your environment (Quarkus 3.40.1.1)
./mvnw quarkus:dev                       # mock event server on :8080
curl -i http://localhost:8080/hello      # Expected: 200 and JSON; binary endpoints return RAW bytes in dev
./mvnw verify                            # @QuarkusTest on the mock server, :8081
./mvnw install                           # Expected: target/function.zip, sam.jvm.yaml, sam.native.yaml
grep -E "Runtime:|Handler:|BinaryMediaTypes" target/sam.*.yaml
# Expected (REST native): "Runtime: provided" -> do not carry it into Terraform (F4)
grep -c "quarkus.lambda-http.enable-security=true" src/main/resources/application.properties
# Expected: 1 when the authorizer identity is needed
```

Self-check: exactly one HTTP framework dependency; extension matches the gateway; REST API has `*/*`; no `@Context` of the other gateway's event; Ask First C10 practices (explicit `Content-Type`) decided, if wanted; Terraform carries the runtime chosen in the U1 decision.
