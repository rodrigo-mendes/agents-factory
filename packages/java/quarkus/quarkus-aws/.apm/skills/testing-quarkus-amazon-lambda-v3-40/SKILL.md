---
name: testing-quarkus-amazon-lambda-v3-40
description: "Guides offline tests of Quarkus 3.40 LTS AWS Lambdas: mock event server, quarkus-junit with RestAssured, @QuarkusIntegrationTest, Dev Services, optional SAM emulation. Use when writing Lambda tests. Not for handler code, Terraform deployment, Cognito design or Quarkus 4."
---

# Testing Quarkus AWS Lambda (offline) 3.40

> Version lock: every claim applies to **Quarkus 3.40 LTS, patch 3.40.1.1** (`quarkus-amazon-lambda`, `-http`, `-rest`) only. Research date **2026-10-28**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: testing Lambdas without AWS: mock event server, `@QuarkusTest` + RestAssured, `@QuarkusIntegrationTest`, Dev Services, optional SAM local. Neighbours, by name only: `developing-quarkus-junit-v3-40` (generic `@QuarkusTest`, `@InjectMock`, profiles), `developing-quarkus-amazon-lambda-http-v3-40` (HTTP mapping), `securing-quarkus-lambda-cognito-v3-40` (security model), `integrating-quarkus-amazon-data-v3-40` and `integrating-quarkus-amazon-messaging-v3-40` (SDK clients), `provisioning-aws-lambda-v6` (Terraform). Handler and packaging: [developing-quarkus-amazon-lambda-v3-40](../developing-quarkus-amazon-lambda-v3-40/SKILL.md). Quarkus 4 is out of scope.

## Version Context

| Item | Value | Source (fetched 2026-10-28) |
|---|---|---|
| Quarkus | 3.40 LTS, released 2026-09-30, community-maintained until 2027-09-30; patch 3.40.1.1 released 2026-10-19 | https://quarkus.io/releases |
| Test mechanism | Mock AWS Lambda event server started in dev and test mode; RestAssured default port set to 8081 in test mode | https://quarkus.io/version/3.40/guides/aws-lambda |
| Test dependencies | `io.quarkus:quarkus-junit` + `io.rest-assured:rest-assured` (the guide's Gradle sample) | https://quarkus.io/version/3.40/guides/aws-lambda |
| Removed | `quarkus-test-amazon-lambda` and `LambdaClient` removed in 3.31; last Central version 3.30.8 | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 |
| Mockito integration | `io.quarkus:quarkus-junit-mockito` 3.40.1.1 (depends on `quarkus-junit`) | https://repo1.maven.org/maven2/io/quarkus/quarkus-junit-mockito/3.40.1.1/quarkus-junit-mockito-3.40.1.1.pom |
| Dev Services for AWS | Quarkiverse amazon-services 3.23.0 "built on Quarkus 3.40.0"; pairing with patch 3.40.1.1 (medium confidence) | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html ; https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom |

**Version-lifetime risk** (as of 2026-10-28; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0 is "Upcoming" with no date on the releases page. Pin 3.40.x; Quarkus 4 content is rejected.
- Quarkiverse Dev Services defaults differ between the 3.23.x page (LocalStack) and the unversioned `dev` page (Floci); this skill follows 3.23.x.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [HTTP Lambda tests and secured endpoints](./blueprints/http-lambda-testing.md)
- [Mock event server behaviour](./blueprints/mock-event-server.md)
- [Ask-first decisions in depth](./blueprints/ask-first-decisions.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Verification Loop](./blueprints/verification-loop.md)
- [Migration notes](./blueprints/migration-notes.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Test handlers with `@QuarkusTest` and RestAssured against the mock event server.** The extension "boots up a mock AWS Lambda event server in Quarkus Dev and Test mode" ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)). See [patterns](./blueprints/always-do-patterns.md#1-plain-handler-test).
- **Declare `quarkus-junit` and `rest-assured` in test scope.** The guide's Gradle sample lists both ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)). See [patterns](./blueprints/always-do-patterns.md#2-test-dependencies).
- **Configure the mock server ports with `quarkus.lambda.mock-event-server.dev-port` and `test-port`.** These are the names the guide documents ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)). See [patterns](./blueprints/always-do-patterns.md#3-mock-event-server-keys).
- **For HTTP Lambdas call the REST endpoint with RestAssured, or POST a raw API Gateway event to `/_lambda_`.** Both are in the HTTP guide ([aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). See [HTTP testing](./blueprints/http-lambda-testing.md#1-endpoint-and-raw-event-tests).
- **Put the identity into the API Gateway event and set `quarkus.lambda-http.enable-security=true` for secured HTTP Lambdas.** The guide says security is opt-in ([aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). See [HTTP testing](./blueprints/http-lambda-testing.md#2-secured-endpoints).
- **Run `@QuarkusIntegrationTest` for the built artifact.** It supports all features "except injecting into tests" ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)). That the mock event server also starts there is in [patterns](./blueprints/always-do-patterns.md#4-integration-and-native-tests). See [patterns](./blueprints/always-do-patterns.md#4-integration-and-native-tests).
- **Know that configuring `endpoint-override` disables Dev Services for that client.** Choosing between Dev Services, `@InjectMock` and `endpoint-override` is Ask First C1 ([Dev Services 3.23.x](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html)). See [patterns](./blueprints/always-do-patterns.md#5-dev-services-for-aws-calls).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Dev Services container vs `@InjectMock` vs `endpoint-override` | A: container, realistic SDK calls, Docker required. B: mock the CDI bean, fast, not in `@QuarkusIntegrationTest`. C: own container, disables Dev Services. See [decisions](./blueprints/ask-first-decisions.md#c1-dev-services-injectmock-or-endpoint-override) | "Is Docker available in CI? Must the test exercise the AWS SDK call or only business logic?" |
| Dev Services stack provider | `localstack` (default in 3.23.x, image `localstack/localstack:4.13`; both (medium confidence), M13), `ministack`, `moto`, `floci` (`:latest` images). See [decisions](./blueprints/ask-first-decisions.md#c2-dev-services-stack-provider) | "Keep LocalStack, or change provider and pin the image?" |
| Optional SAM local emulation | Mock server only (default) vs `sam local invoke` / `start-api` (Docker + SAM CLI). Never deployment. See [decisions](./blueprints/ask-first-decisions.md#c3-optional-sam-local-emulation) | "Do you want Lambda-container emulation locally?" |
| Fixed vs random mock-server port | Default 8081, a fixed port, or `0`. Whether RestAssured follows a random port is (unverified). The short keys `quarkus.lambda.test-port` / `dev-port` exist, are not deprecated, and the start-up reads only the `mock-event-server.*` names, so those are the names to use (all (medium confidence), M9, from source at tag 3.40.1.1). See [decisions](./blueprints/ask-first-decisions.md#c4-fixed-or-random-mock-server-port) | "Do tests run in parallel on shared hosts?" |
| Secured HTTP Lambda: event claims vs `@TestSecurity` | Claims in the event are documented; `@TestSecurity` through the Lambda path is (unverified). See [decisions](./blueprints/ask-first-decisions.md#c5-secured-http-lambda-event-claims-or-testsecurity) | "Which identity mechanism does the endpoint use?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Use `quarkus-test-amazon-lambda` or `LambdaClient`; removed in 3.31, no 3.40.1.1 artifact ([wiki](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31)) | Use `quarkus-junit` + RestAssured against the mock event server ([guide](https://quarkus.io/version/3.40/guides/aws-lambda)) |
| Use `@InjectMock` or `@Inject` in a `@QuarkusIntegrationTest` ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)) | Mock in `@QuarkusTest` only ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)) |
| Treat `sam.*.yaml` or `sam deploy` as the deployment path ([guide](https://quarkus.io/version/3.40/guides/aws-lambda)) | Use SAM only as local emulation; deployment is Terraform with `provisioning-aws-lambda-v6` consuming `function.zip` |

**Team practice (family/team policy, outside the tiers; not a statement of the guide).** Do not call real AWS from unit tests; choose the test double through Ask First C1 (Dev Services container or `@InjectMock`). The mock-server port key names are advice in Ask First (port row), not a prohibition.

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Mock server ports | dev `8080` (`quarkus.lambda.mock-event-server.dev-port`), test `8081` (`...test-port`); `0` = random | https://quarkus.io/version/3.40/guides/all-config |
| Mock server switch | `quarkus.lambda.mock-event-server.enabled`, default `true` (medium confidence, M12); starts even if `quarkus.devservices.enabled=false` | https://quarkus.io/version/3.40/guides/all-config |
| Plain handler test | `given().contentType("application/json").body(in).when().post()` (RestAssured, port 8081; reconstructed code, medium confidence, M1) | https://quarkus.io/version/3.40/guides/aws-lambda |
| HTTP raw event | `post("/_lambda_")` with `APIGatewayV2HTTPEvent` (HTTP API) or `AwsProxyRequest` (REST API) | https://quarkus.io/version/3.40/guides/aws-lambda-http |
| HTTP security keys | `quarkus.lambda-http.enable-security` default `false` (medium confidence); `map-cognito-to-roles` default `true` (medium confidence); `cognito-role-claim` default `cognito:groups` (medium confidence) | https://quarkus.io/version/3.40/guides/all-config |
| Handler error | the mock server returns status 500 to the test client (medium confidence) | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/event-server/src/main/java/io/quarkus/amazon/lambda/runtime/MockEventServer.java |
| Integration test | `@QuarkusIntegrationTest`; no injection into the test; mock server also started | https://quarkus.io/version/3.40/guides/aws-lambda |
| Dev Services | `quarkus.aws.devservices.provider` default `localstack`; image `localstack/localstack:4.13` (both medium confidence, M13); off per service with `quarkus.<service>.devservices.enabled=false` | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html |
| SAM local (optional) | `sam local invoke --template target/sam.jvm.yaml --event payload.json`; `sam local start-api` for HTTP | https://quarkus.io/version/3.40/guides/aws-lambda |
| Representative commands | `./mvnw test`, `./mvnw verify -DskipITs=false` | https://quarkus.io/version/3.40/guides/getting-started-testing |

## External Resources

All fetched 2026-10-28.

- AWS Lambda guide: https://quarkus.io/version/3.40/guides/aws-lambda
- AWS Lambda HTTP guide: https://quarkus.io/version/3.40/guides/aws-lambda-http
- Configuration reference: https://quarkus.io/version/3.40/guides/all-config
- Testing guide: https://quarkus.io/version/3.40/guides/getting-started-testing
- Security testing: https://quarkus.io/version/3.40/guides/security-testing
- Migration guide 3.31: https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31
- Dev Services (amazon-services 3.23.x): https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
