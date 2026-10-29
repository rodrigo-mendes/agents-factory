# Research: Testing Quarkus AWS Lambda functions on Quarkus 3.40 LTS (3.40.1.1)

Unit U6 of the quarkus-aws-saas family. Future skill: `testing-quarkus-amazon-lambda-v3-40` (package `quarkus-aws`).
Source item: "test Quarkus Lambdas offline".
Family facts applied as given: `workspace/quarkus-aws-saas/_family_facts_v3.40.md`, `workspace/_family_facts_v3.40.md`.
Family rules applied as given: `workspace/quarkus-aws-saas/_family_rules_v3.40.md` (incl. rules 9-12), `workspace/_family_rules_v3.40.md`, and the evidence/tag policy in `.claude/skills/building-agent-packages/blueprints/policy/`.

All pages were read on **2026-10-28** through the WebFetch tool. Sentences in quotes were returned verbatim by the tool (the tool limits verbatim quotes to about 125 characters, so long code blocks were returned line by line or as a summary; this is stated where it matters). Paraphrased statements are not quoted. Pages read only in part are listed as coverage limits (L-ids) in Research Gaps.

Scope boundary: generic Quarkus JUnit content (JUnit 6 rename, `@QuarkusTest` lifecycle, test profiles, `@InjectMock` rules) lives in the existing skill `developing-quarkus-junit-v3-40`; it is referenced by name, not repeated. Handler/packaging is U1 (`developing-quarkus-amazon-lambda-v3-40`), HTTP mapping is U2, security is U3, AWS SDK client configuration is U4/U5.

---

## Metadata

```yaml
Full_Name: Testing Quarkus AWS Lambda functions (io.quarkus:quarkus-amazon-lambda, quarkus-amazon-lambda-http, quarkus-amazon-lambda-rest) offline
Target_Version: Quarkus 3.40 LTS, patch 3.40.1.1
Release_Date: Quarkus 3.40 released 2026-09-30; 3.40.1.1 released 2026-10-19 (family fact, https://quarkus.io/releases)
Support_Status: LTS, community-maintained until 2027-09-30 (family fact, https://quarkus.io/releases)
Primary_Docs: https://quarkus.io/version/3.40/guides/aws-lambda ; https://quarkus.io/version/3.40/guides/aws-lambda-http
Secondary_Docs: https://quarkus.io/version/3.40/guides/all-config ; https://quarkus.io/version/3.40/guides/getting-started-testing ; https://quarkus.io/version/3.40/guides/security-testing ; https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31
Source_At_Tag: https://github.com/quarkusio/quarkus/tree/3.40.1.1/extensions/amazon-lambda
Quarkiverse_Docs: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html
Registry: https://repo1.maven.org/maven2/io/quarkus/quarkus-test-amazon-lambda/maven-metadata.xml ; https://repo1.maven.org/maven2/io/quarkus/quarkus-junit-mockito/3.40.1.1/quarkus-junit-mockito-3.40.1.1.pom
Research_Date: 2026-10-28
Domain_Complexity: Standard
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 5
Unverified_Count: 8
Irresolvable_Count: 0
Research_Quality_Score: 87%   # ~62 sourced claims; 8 unverified; 0 irresolvable -> (62-8)/62
Execution_Notes: >
  Caller constraints honoured: no sub-agents (P2.parallel skipped, all pages fetched by this agent),
  no plan mode (scope approval relayed by the caller from PIPELINE_STATE.md#approvals on 2026-10-28;
  recorded here as a relay, not as an approval by this agent), file written directly instead of via
  research-synthesizer.
```

---

## Executive Summary

Quarkus 3.40.1.1 tests AWS Lambda functions offline with a **mock AWS Lambda event server** that the extension starts in dev and test mode: "the Quarkus AWS Lambda extension boots up a mock AWS Lambda event server in Quarkus Dev and Test mode" (https://quarkus.io/version/3.40/guides/aws-lambda, read 2026-10-28). In test mode it listens on port 8081 and "The default port for Rest Assured is automatically set to 8081 by Quarkus, so you can invoke on this endpoint." Tests are ordinary `@QuarkusTest` classes using `io.quarkus:quarkus-junit` and `io.rest-assured:rest-assured` (the guide's Gradle sample). For plain handlers the test POSTs the input JSON to the mock server; for HTTP Lambdas (`quarkus-amazon-lambda-http` / `-rest`) the mock server "converts HTTP requests into API Gateway event JSON" (paraphrase), so RestAssured calls the REST endpoints directly, and raw API Gateway events (e.g. `APIGatewayV2HTTPEvent` with Cognito claims) can be POSTed to `/_lambda_` (https://quarkus.io/version/3.40/guides/aws-lambda-http, read 2026-10-28). "The mock event server is also started for `@QuarkusIntegrationTest` tests so will work with native binaries too."

The most important 3.40-relevant change is a removal: "The Amazon Lambda Testing module `quarkus-test-amazon-lambda` and the `io.quarkus.amazon.lambda.test.LambdaClient`, which has been deprecated in Quarkus 2.3.0, have now been removed from Quarkus" with the instruction to "move to using `RestAssured` instead" (https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31, read 2026-10-28). Maven Central confirms the last published `quarkus-test-amazon-lambda` is 3.30.8 and there is no 3.40.1.1 POM (HTTP 404). The U4 open item from the U1 research is resolved: the 3.40 configuration reference lists both `quarkus.lambda.mock-event-server.dev-port`/`test-port` and `quarkus.lambda.dev-port`/`test-port` with the same defaults (8080/8081) and marks **none** of them deprecated; the source at tag 3.40.1.1 shows the event server is started with the `quarkus.lambda.mock-event-server.` + `test-port`/`dev-port` property name only, so the `mock-event-server.*` names are the ones to use. Dev Services for AWS services come from Quarkiverse amazon-services 3.23.x, which "starts a containerized AWS stack in dev mode and when running tests" (LocalStack `localstack/localstack:4.13` by default in the 3.23.x docs) unless an `endpoint-override` is set.

Three critical patterns: (1) test with `@QuarkusTest` + RestAssured against the mock event server, never with `LambdaClient`/`quarkus-test-amazon-lambda` (removed); (2) configure ports only with `quarkus.lambda.mock-event-server.dev-port` / `test-port` / `enabled`; (3) never call real AWS from tests: use Dev Services (container) or `@InjectMock` for CDI beans (rules in `developing-quarkus-junit-v3-40`), and treat SAM CLI only as optional local emulation, never as deployment (family rule 4, IaC is Terraform). Domain complexity is **Standard**: one test mechanism with two event shapes (plain vs HTTP), an integration-test/native mode with documented limits, and a Dev Services dependency on a second project (Quarkiverse).

---

## Architectural Guardrails

> Confidence legend: 🟢 High (versioned official page, Maven Central POM/metadata, or source at tag 3.40.1.1, read 2026-10-28) | 🟡 Medium (inference, unversioned/partly read page, or illustrative code) | 🔴 Low (community or unverified, verify before use)
> Family evidence rule applied (`_family_rules_v3.40.md` rule 5): a single versioned official source is enough for High. The template's "fewer than 2 sources means Medium" downgrade is superseded by that rule. Triangulation badges are given where two independent official sources agree.

### ✅ Mandatory Patterns

**A1. Test Lambda handlers with `@QuarkusTest` + RestAssured against the mock event server**
> Confidence: 🟢 High | [✓✓ Triangulated | aws-lambda guide (2026-10-28) + Migration-Guide-3.31 "move to using `RestAssured`" (2026-10-28)]
- Why: the extension "boots up a mock AWS Lambda event server in Quarkus Dev and Test mode"; "The default port for Rest Assured is automatically set to 8081 by Quarkus". "For your unit tests, you can also invoke on the mock event server using any HTTP client you want."
- Code (reconstruction of the guide's `LambdaHandlerTest`: the tool returned it as a summary, not verbatim, so the exact lines are (medium confidence); `Person` is the guide's input POJO):
  ```java
  // Quarkus 3.40.1.1 — plain RequestHandler test (reconstructed from the guide's summary)
  import static io.restassured.RestAssured.given;
  import static org.hamcrest.CoreMatchers.containsString;

  import org.junit.jupiter.api.Test;
  import io.quarkus.test.junit.QuarkusTest;

  @QuarkusTest
  public class LambdaHandlerTest {
      @Test
      public void testSimpleLambdaSuccess() throws Exception {
          Person in = new Person();
          in.setName("Stu");
          given()
                  .contentType("application/json")
                  .accept("application/json")
                  .body(in)
                  .when()
                  .post()                 // mock event server, port 8081 in test mode
                  .then()
                  .statusCode(200)
                  .body(containsString("Hello Stu"));
      }
  }
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28); https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 (2026-10-28)

**A2. Test dependencies are `io.quarkus:quarkus-junit` + `io.rest-assured:rest-assured`**
> Confidence: 🟢 High | [✓✓ Triangulated | aws-lambda guide Gradle sample (2026-10-28) + family fact (quarkus-junit5 → quarkus-junit in 3.31)]
- Why: the 3.40 guide's Gradle sample lists `testImplementation 'io.quarkus:quarkus-junit'` and `testImplementation 'io.rest-assured:rest-assured'`. The guide gives no Maven test snippet; the Maven equivalent (test scope, versions from the Quarkus BOM) is (medium confidence).
- Code:
  ```xml
  <!-- Quarkus 3.40.1.1 — Maven equivalent of the guide's Gradle test deps (medium confidence for the Maven form) -->
  <dependency>
    <groupId>io.quarkus</groupId>
    <artifactId>quarkus-junit</artifactId>
    <scope>test</scope>
  </dependency>
  <dependency>
    <groupId>io.rest-assured</groupId>
    <artifactId>rest-assured</artifactId>
    <scope>test</scope>
  </dependency>
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28); family fact row "quarkus-junit5 was renamed quarkus-junit" (https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31)

**A3. Configure the mock event server only through `quarkus.lambda.mock-event-server.*`**
> Confidence: 🟢 High | [✓✓ Triangulated | aws-lambda guide (2026-10-28) + all-config (2026-10-28) + source `DevServicesLambdaProcessor` at tag 3.40.1.1 (2026-10-28)]
- Why: the guide documents exactly `quarkus.lambda.mock-event-server.dev-port`, `quarkus.lambda.mock-event-server.test-port`, `quarkus.lambda.mock-event-server.enabled`; "A port value of zero will result in a randomly assigned port." The event server build step builds the property name as `"quarkus.lambda.mock-event-server."` + `"test-port"` / `"dev-port"`.
- Defaults (per key, family rule 10):
  | Key | Env var | Default | Source |
  |---|---|---|---|
  | `quarkus.lambda.mock-event-server.dev-port` | `QUARKUS_LAMBDA_MOCK_EVENT_SERVER_DEV_PORT` | `8080` | all-config |
  | `quarkus.lambda.mock-event-server.test-port` | `QUARKUS_LAMBDA_MOCK_EVENT_SERVER_TEST_PORT` | `8081` | all-config |
  | `quarkus.lambda.mock-event-server.enabled` | `QUARKUS_LAMBDA_MOCK_EVENT_SERVER_ENABLED` | `true` | all-config ("Setting to true will start event server even if quarkus.devservices.enabled=false") |
- Code (the guide's example values, not defaults, family rule 11):
  ```properties
  # Quarkus 3.40.1.1 — the guide's example
  quarkus.lambda.mock-event-server.dev-port=8082
  quarkus.lambda.mock-event-server.test-port=8083
  # quarkus.lambda.mock-event-server.enabled=false   # turns the server off
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda ; https://quarkus.io/version/3.40/guides/all-config ; https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-deployment/src/main/java/io/quarkus/amazon/lambda/deployment/DevServicesLambdaProcessor.java (2026-10-28)

**A4. HTTP Lambdas: call the REST endpoint with RestAssured; POST raw API Gateway events to `/_lambda_`**
> Confidence: 🟢 High | [✓✓ Triangulated | aws-lambda-http guide (2026-10-28) + source `AmazonLambdaApi.API_BASE_PATH_TEST = "/_lambda_"` at tag 3.40.1.1 (2026-10-28)]
- Why: with `quarkus-amazon-lambda-http` / `-rest` the mock server turns HTTP requests into API Gateway event JSON, so plain RestAssured calls work; for "more complex API Gateway events" the guide says to "manually do an HTTP POST to `http://localhost:8080/_lambda_`" (8081 in test mode). "Unit testing is the same as any other Java project and does not require running on Amazon."
- Code (lines returned verbatim by the tool from the guide's `AmazonLambdaSimpleTestCase`; the `request(String)` helper that builds the event is **not shown** by the guide (unverified), and the `java.util.HashMap` / `org.junit.jupiter.api.Test` imports are implied):
  ```java
  // Quarkus 3.40.1.1 — HTTP API (v2) raw event test, from aws-lambda-http guide
  import static io.restassured.RestAssured.given;
  import static org.hamcrest.CoreMatchers.equalTo;

  import com.amazonaws.services.lambda.runtime.events.APIGatewayV2HTTPEvent;
  import io.quarkus.test.junit.QuarkusTest;

  @QuarkusTest
  public class AmazonLambdaSimpleTestCase {
      @Test
      public void testJaxrsCognitoJWTSecurityContext() throws Exception {
          APIGatewayV2HTTPEvent request = request("/security/username");
          request.getRequestContext().setAuthorizer(new APIGatewayV2HTTPEvent.RequestContext.Authorizer());
          request.getRequestContext().getAuthorizer().setJwt(new APIGatewayV2HTTPEvent.RequestContext.Authorizer.JWT());
          request.getRequestContext().getAuthorizer().getJwt().setClaims(new HashMap<>());
          request.getRequestContext().getAuthorizer().getJwt().getClaims().put("cognito:username", "Bill");
          given()
                  .contentType("application/json")
                  .accept("application/json")
                  .body(request)
                  .when()
                  .post("/_lambda_")
                  .then()
                  .statusCode(200)
                  .body("body", equalTo("Bill"));
      }
  }
  ```
- Event shapes: HTTP API (`quarkus-amazon-lambda-http`) uses `APIGatewayV2HTTPEvent` / `APIGatewayV2HTTPResponse`; REST API (`quarkus-amazon-lambda-rest`) uses `AwsProxyRequest` / `AwsProxyResponse` in `io.quarkus.amazon.lambda.http.model` (guide). The raw-event response is the API Gateway response JSON, hence `.body("body", ...)`.
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http ; https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AmazonLambdaApi.java (2026-10-28)

**A5. Secured HTTP Lambdas: put the identity in the API Gateway event (Cognito/IAM claims) and enable `quarkus.lambda-http.enable-security`**
> Confidence: 🟢 High (single versioned source per claim)
- Why: the guide's only documented test identity mechanism for Lambda HTTP is the claim inside the event (A4 example, `cognito:username` = "Bill"). `quarkus.lambda-http.enable-security` (default `false`) enables processing of AWS authentication from API Gateway events; `quarkus.lambda-http.map-cognito-to-roles` (default `true`); `quarkus.lambda-http.cognito-role-claim` (default `cognito:groups`); `quarkus.lambda-http.cognito-claim-matcher` (default `[^\[\] \t]+`). HTTP vs REST use different JSON paths (Cognito: `requestContext.authorizer.jwt.claims.cognito:username` for HTTP, `requestContext.authorizer.claims.cognito:username` for REST). Detail of the security model belongs to U3.
- Code:
  ```properties
  # Quarkus 3.40.1.1
  quarkus.lambda-http.enable-security=true
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http ; https://quarkus.io/version/3.40/guides/all-config (2026-10-28)

**A6. Integration/native tests: `@QuarkusIntegrationTest` with the mock event server; no injection into the test**
> Confidence: 🟢 High | [✓✓ Triangulated | aws-lambda guide + aws-lambda-http guide (both: "also started for @QuarkusIntegrationTest") (2026-10-28)]
- Why: "The mock event server is also started for `@QuarkusIntegrationTest` tests so will work with native binaries too." `@QuarkusIntegrationTest` "should be used to launch and test the artifact produced by the Quarkus build" and "supports all the features mentioned in this guide except injecting into tests" (getting-started-testing, see L1). Integration tests run "using the `prod` configuration profile" (family rule 18: tag (medium confidence)); "it's not possible for integration tests" to use test-specific `src/test/resources/application.properties` settings (family rule 18: (medium confidence)).
- Code (common pattern from getting-started-testing; the Lambda guides show no IT class, so this is (medium confidence)):
  ```java
  // Quarkus 3.40.1.1 — runs LambdaHandlerTest against the built artifact (jar or native)
  @QuarkusIntegrationTest
  public class LambdaHandlerIT extends LambdaHandlerTest { }
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda ; https://quarkus.io/version/3.40/guides/aws-lambda-http ; https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-28)

**A7. Use Quarkiverse amazon-services 3.23.x Dev Services (container) for AWS services the function calls**
> Confidence: 🟢 High (versioned Quarkiverse 3.23.x page)
- Why: "Quarkus Amazon Services automatically starts a containerized AWS stack in dev mode and when running tests"; they are disabled when "the endpoint-override is configured"; global switch `quarkus.devservices.enabled=false`, per extension `quarkus.<service>.devservices.enabled=false` (e.g. `quarkus.dynamodb.devservices.enabled=false`); "The extension client is configured automatically." Default provider `quarkus.aws.devservices.provider=localstack`; LocalStack default image `localstack/localstack:4.13`; other providers MiniStack, Moto, Floci; Dev Services "does not verify if the chosen stack actually implements a mock for a given service." Client configuration details belong to U4/U5.
- Code: none needed beyond adding the extension and not setting `endpoint-override` in the test profile.
  ```properties
  # Quarkus 3.40.1.1 + quarkus-amazon-services 3.23.x — keep endpoint-override OUT of the test profile
  # %test.quarkus.dynamodb.endpoint-override=...   <- would disable Dev Services
  ```
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html (2026-10-28)

### ⚠️ Conditional Patterns

**C1. Dev Services container vs `@InjectMock` for AWS-facing code**
> Confidence: 🟡 Medium (decision framing; each option's facts are High)
- Options: A) Dev Services container (A7); B) mock the CDI bean that wraps the AWS client with `@InjectMock` (requires `quarkus-junit-mockito`; rules, including `@Singleton` needing `@MockitoConfig(convertScopes = true)`, are in `developing-quarkus-junit-v3-40`); C) explicit `endpoint-override` to a container you manage.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A Dev Services | Realistic SDK calls, zero config | Docker required ("In test mode, it will cause the test to fail" without Docker); stack may not implement every service | Behaviour against the AWS API matters |
  | B `@InjectMock` | Fast, no Docker | Not available in `@QuarkusIntegrationTest` ("except injecting into tests") | Unit tests of business logic |
  | C endpoint-override | Full control of container | Disables Dev Services; you manage lifecycle | Shared CI LocalStack, custom init |
- Agent: "Ask user whether Docker is available in CI and whether the test must exercise the AWS SDK call or only the business logic."
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html ; https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-28)

**C2. Dev Services stack provider (LocalStack vs MiniStack vs Moto vs Floci)**
> Confidence: 🟡 Medium
- Options: `quarkus.aws.devservices.provider` = `localstack` (default in 3.23.x), `ministack`, `moto`, `floci`.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | localstack (`localstack/localstack:4.13`) | Default, pinned tag | 3.23.x page default; the `dev` docs say LocalStack is supported "up to version 4.13 (latest free community version)" | Default choice |
  | ministack / moto / floci (`:latest` images) | Alternatives | Images default to `:latest` (not reproducible); service coverage unchecked by Dev Services | Licence or coverage reasons |
- Agent: "Ask user before changing the provider; pin the image tag if a `:latest` provider is chosen."
- Note: the `dev` (unversioned) docs say Floci is the default; the 3.23.x page says LocalStack. Use the 3.23.x page (family rule 2).
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html ; https://docs.quarkiverse.io/quarkus-amazon-services/dev/dev-services.html (2026-10-28)

**C3. Optional local emulation with SAM CLI (never a deployment path)**
> Confidence: 🟡 Medium (that it is optional is the guide's wording; the family decision is rule 4)
- Options: A) mock event server only (default; "the Quarkus JUnit integration should be sufficient for most of your needs"); B) `sam local invoke --template target/sam.jvm.yaml --event payload.json` (plain Lambda; `target/sam.native.yaml` for native; Gradle: `build` instead of `target`); C) `sam local start-api --template target/sam.jvm.yaml` then `http://127.0.0.1:3000/hello` (HTTP Lambda guide documents only `start-api`). Both SAM options need Docker. For a fixed principal under `sam local` the HTTP guide offers the env var `QUARKUS_AWS_LAMBDA_FORCE_USER_NAME`.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Mock event server | Speed, no Docker, JUnit-integrated | Not the real Lambda container | Always (default) |
  | SAM local | Lambda container emulation | Docker + SAM CLI; `sam.*.yaml` is not the IaC (Terraform is) | Smoke test of the zip in a Lambda-like container |
- Agent: "Ask user whether local container emulation is wanted; never present `sam deploy` or `sam.*.yaml` as deployment."
- Source: https://quarkus.io/version/3.40/guides/aws-lambda ; https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); family rule 4

**C4. Fixed vs random mock-server test port**
> Confidence: 🟡 Medium
- Options: default 8081; a fixed other port (guide example 8083); `0` for random ("A port value of zero will result in a randomly assigned port").
- Tradeoffs: random avoids clashes in parallel CI runs; RestAssured is configured automatically for the default, but whether RestAssured follows a random/overridden mock port automatically is not stated (unverified, U2).
- Agent: "Ask user whether tests run in parallel on shared hosts."
- Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28)

**C5. Testing a secured HTTP Lambda: event claims vs `@TestSecurity`**
> Confidence: 🟡 Medium
- Options: A) claims in the API Gateway event posted to `/_lambda_` (documented by the Lambda HTTP guide, A4/A5); B) `@TestSecurity(user=..., roles=...)` from `io.quarkus:quarkus-test-security` (documented generically; "The feature is only available for `@QuarkusTest`"). Whether B takes effect through the Lambda mock event server path is not documented (unverified, U3).
- Agent: "Prefer A for Lambda-specific security tests; ask before relying on B."
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http ; https://quarkus.io/version/3.40/guides/security-testing (2026-10-28)

### 🚫 Forbidden Patterns

**F1. Using `quarkus-test-amazon-lambda` / `LambdaClient`**
> Severity: High
> Confidence: 🟢 High
- Why: removed from Quarkus (Migration-Guide-3.31); the last published version on Maven Central is 3.30.8; `quarkus-test-amazon-lambda` 3.40.1.1 does not exist (HTTP 404). In source at tag 3.40.1.1, if `io.quarkus.amazon.lambda.test.LambdaClient` is on the classpath ("legacy testing") the mock event server is **not** started.
- Impact: dependency resolution fails at 3.40.1.1; pinning 3.30.8 mixes Quarkus versions and disables the mock event server.
- ❌ Wrong:
  ```xml
  <dependency>
    <groupId>io.quarkus</groupId>
    <artifactId>quarkus-test-amazon-lambda</artifactId>
    <scope>test</scope>
  </dependency>
  <!-- LambdaClient.invoke(Person.class, in) -->
  ```
- ✅ Correct:
  ```xml
  <dependency><groupId>io.quarkus</groupId><artifactId>quarkus-junit</artifactId><scope>test</scope></dependency>
  <dependency><groupId>io.rest-assured</groupId><artifactId>rest-assured</artifactId><scope>test</scope></dependency>
  <!-- given().body(in).post().then().statusCode(200) -->
  ```
- Source: https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 ; https://repo1.maven.org/maven2/io/quarkus/quarkus-test-amazon-lambda/maven-metadata.xml ; DevServicesLambdaProcessor at tag 3.40.1.1 (2026-10-28)

**F2. Calling real AWS from unit tests**
> Severity: High
> Confidence: 🟢 High (the alternatives are High; the rule is the caller's scope decision and family rule 5)
- Why: "Unit testing is the same as any other Java project and does not require running on Amazon" (aws-lambda-http guide); Dev Services exist to start "a containerized AWS stack ... when running tests". A test profile pointing at real AWS (real credentials, real endpoints) makes tests non-hermetic and can mutate cloud resources.
- Impact: cost, data mutation, credential leakage into CI, flaky tests.
- ❌ Wrong:
  ```properties
  %test.quarkus.dynamodb.endpoint-override=https://dynamodb.eu-west-1.amazonaws.com
  # plus real access keys in CI env
  ```
- ✅ Correct:
  ```properties
  # no endpoint-override in %test -> Dev Services container starts (quarkus-amazon-services 3.23.x)
  ```
  or `@InjectMock` on the CDI bean wrapping the client (see `developing-quarkus-junit-v3-40`).
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http ; https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html (2026-10-28)

**F3. Configuring the mock server with `quarkus.lambda.test-port` / `quarkus.lambda.dev-port`**
> Severity: moderate
> Confidence: 🟢 High
- Why: the keys exist (config root `MockEventServerConfig`, prefix `quarkus.lambda`, defaults 8080/8081, not deprecated), but the event server start-up reads `quarkus.lambda.mock-event-server.` + `test-port`/`dev-port`, and the guide documents only the `mock-event-server.*` names. Whether anything else reads the short names is (unverified, U1).
- Impact: a port set with the short key may not move the mock server.
- ❌ Wrong:
  ```properties
  quarkus.lambda.test-port=8083
  ```
- ✅ Correct:
  ```properties
  quarkus.lambda.mock-event-server.test-port=8083
  ```
- Source: https://quarkus.io/version/3.40/guides/all-config ; https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/MockEventServerConfig.java ; DevServicesLambdaProcessor at tag 3.40.1.1 (2026-10-28)

**F4. `@InjectMock` / `@Inject` in a `@QuarkusIntegrationTest`**
> Severity: moderate
> Confidence: 🟢 High
- Why: `@QuarkusIntegrationTest` "supports all the features mentioned in this guide except injecting into tests"; `@TestSecurity` "is only available for `@QuarkusTest`".
- Impact: the IT does not see the mock; the real bean (and possibly real I/O) runs.
- ❌ Wrong:
  ```java
  @QuarkusIntegrationTest
  class OrderLambdaIT { @InjectMock OrderRepository repo; }
  ```
- ✅ Correct:
  ```java
  @QuarkusTest
  class OrderLambdaTest { @InjectMock OrderRepository repo; }   // mocks only in @QuarkusTest
  @QuarkusIntegrationTest
  class OrderLambdaIT extends OrderLambdaTest { }                // see A6; container deps via Dev Services
  ```
  (The `extends` pattern is (medium confidence) per family rule 18; the ✅ part that is High is "mocks only in `@QuarkusTest`".)
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing ; https://quarkus.io/version/3.40/guides/security-testing (2026-10-28)

**F5. Using `sam.*.yaml` / `sam deploy` as the deployment path**
> Severity: moderate
> Confidence: 🟢 High (family rule 4; the guide frames SAM local as local testing)
- Why: family rule 4 says IaC is Terraform (`provisioning-aws-*-v6`); the 3.40 guides present SAM CLI under "Testing with the SAM CLI" / "Simulate AWS Lambda Deployment with SAM CLI".
- ❌ Wrong:
  ```bash
  sam deploy --template target/sam.jvm.yaml
  ```
- ✅ Correct:
  ```bash
  # Representative — adapt to your environment
  sam local invoke --template target/sam.jvm.yaml --event payload.json   # optional local emulation only
  # deployment: Terraform (provisioning-aws-lambda-v6) consuming target/function.zip
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda ; https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); family rule 4

---

## Migration Guide

> Confidence: 🟢 High | Sources: https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 (2026-10-28) + https://repo1.maven.org/maven2/io/quarkus/quarkus-test-amazon-lambda/maven-metadata.xml (2026-10-28)

**Breaking Changes** (relevant to Lambda testing, up to 3.40):
- ⚠️ Migration Note: `quarkus-test-amazon-lambda` and `io.quarkus.amazon.lambda.test.LambdaClient` (deprecated since 2.3.0) removed (wiki 3.31). Last Central release 3.30.8 (metadata lastUpdated 2026-10-19).
- ⚠️ Migration Note: `quarkus-junit5` → `quarkus-junit` (JUnit 6) in 3.31; relocation POM still resolves at 3.40.1 (family fact). Mockito integration is `io.quarkus:quarkus-junit-mockito` at 3.40.1.1 (POM name "Quarkus - Test framework - JUnit - Mockito", depends on `quarkus-junit`, no relocation).
- Reading `quarkus.http.test-port` via `System.getProperty` no longer works since 3.31 (family fact); the same caution applies by analogy to the mock server port property (medium confidence).
- Breaking changes for the mock event server between 3.31 and 3.40: none found; other wiki migration guides (3.32-3.40) were not read (unverified, U8).

**Upgrade Steps**:
1. Remove `quarkus-test-amazon-lambda` from the POM/Gradle file.
2. Replace `LambdaClient.invoke(...)` with RestAssured `given().body(in).post()` (plain) or endpoint calls / `post("/_lambda_")` (HTTP).
3. Rename `quarkus-junit5` → `quarkus-junit`, `quarkus-junit5-mockito` → `quarkus-junit-mockito` (see `developing-quarkus-junit-v3-40`).
4. Replace any `quarkus.lambda.test-port` / `dev-port` with `quarkus.lambda.mock-event-server.test-port` / `dev-port`.
```bash
# Representative — adapt to your environment
grep -rn "quarkus-test-amazon-lambda\|LambdaClient" pom.xml build.gradle src/test   # expected: no output
grep -rn "quarkus.lambda.test-port\|quarkus.lambda.dev-port" src/                    # expected: no output
```

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| `io.quarkus:quarkus-junit` | 3.31 | 3.40.1.1 | JUnit 6 line (family fact) |
| `io.quarkus:quarkus-junit-mockito` | 3.40.1.1 (checked) | 3.40.1.1 | Central POM |
| `io.quarkus:quarkus-test-amazon-lambda` | — | 3.30.8 | removed; never use with 3.40 |
| `io.quarkus:quarkus-test-security` | 3.40 (guide) | 3.40 | `@QuarkusTest` only |
| quarkus-amazon-services Dev Services | 3.23.x | 3.23.x | family fact row 17 (medium confidence for the 3.23 ↔ 3.40 pairing) |
| LocalStack image | 4.13 (default) | 4.13 | 3.23.x docs |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | aws-lambda guide + source at tag 3.40.1.1]

**Lifecycle (what happens in a `@QuarkusTest` run)** — from source at tag 3.40.1.1:
1. Build step `startEventServer` runs `onlyIfNot = IsProduction.class` and only when `launchMode.isDevOrTest()`; the source comment says it is "required for testing so run it even if devservices.enabled=false".
2. It returns early when legacy testing (`LambdaClient` on the classpath) is detected or `quarkus.lambda.mock-event-server.enabled` is false.
3. Port: `EventServerPortOverrideBuildItem` if present, else the configured `quarkus.lambda.mock-event-server.test-port` (TEST) / `dev-port` (DEV), else `MockEventServerConfig.TEST_PORT` "8081" / `DEV_PORT` "8080". After start it sets that property to the exposed port and sets `quarkus-internal.aws-lambda.test-api` to `localhost:<port>/_lambda_`. Log: `log.debugf("Started event server on port %d", ...)` (debug level).
4. The mock server (`MockEventServer`) registers `POST /_lambda_` and a default `POST` on any other path → `postEvent`; the Lambda poll loop pulls from `/_lambda_/2018-06-01/runtime/invocation/next` and replies to `.../invocation/<requestId>/response` or `/error`.
5. The test's HTTP call stays open until the handler responds; a handler error is returned to the caller with status **500**; there is no response timeout in the mock server code (it waits; `setMaxWorkerExecuteTime(60)` is a worker limit). If the server closes, the caller gets 503.
- Source: DevServicesLambdaProcessor.java, MockEventServer.java, AmazonLambdaApi.java, MockEventServerConfig.java at https://github.com/quarkusio/quarkus/tree/3.40.1.1/extensions/amazon-lambda (2026-10-28)

**Step 1: Plain handler test** — A1 (`post()` to the default base URI on 8081).

**Step 2: Error path test** (illustrative, medium confidence; status 500 is from source):
```java
// Quarkus 3.40.1.1 — handler throws -> mock event server returns 500 to the test client
@Test
void rejectsInvalidInput() {
    given().contentType("application/json").body("{}")
           .when().post()
           .then().statusCode(500);
}
```

**Step 3: AWS event payload JSON as input** (e.g. an SQS/S3/EventBridge payload): POST the JSON file body to the mock server like any input. The guides show no event-class handler example; using `aws-lambda-java-events` types as handler input is U1's open item U7 (unverified). Illustrative:
```java
// Quarkus 3.40.1.1 — illustrative (medium confidence): event JSON kept in src/test/resources/events/
String payload = Files.readString(Path.of("src/test/resources/events/sqs-event.json"));
given().contentType("application/json").body(payload).when().post().then().statusCode(200);
```

**Step 4: HTTP Lambda test** — plain RestAssured on the endpoint (`given().get("/hello")`) or raw event on `/_lambda_` (A4). For a REST API (v1) build use `AwsProxyRequest` instead of `APIGatewayV2HTTPEvent` (event shape from the guide; a REST-API raw test example is not shown (unverified, U4)).

**Step 5: Integration / native** — A6. Build native with `./mvnw install -Dnative -DskipTests -Dquarkus.native.container-build=true` (guide's command skips tests); to run ITs the generic guide uses `maven-failsafe-plugin` (`integration-test`, `verify`) and `-DskipITs=false`. `@QuarkusIntegrationTest` launches the built jar (`java -jar`), native executable, or container image, not `function.zip` itself (medium confidence: inference from getting-started-testing; the Lambda guides do not say which artifact).

**Step 6: Dev Services for AWS calls** — A7, C1, C2.

**Step 7: Mocking CDI beans** — `@InjectMock` needs `io.quarkus:quarkus-junit-mockito`; works "for any normal CDI scoped bean"; `@Singleton` needs `@MockitoConfig(convertScopes = true)`. Full rules: `developing-quarkus-junit-v3-40`.

**Integration**: Quarkus 3.40 Lambda ↔ Quarkiverse amazon-services 3.23.x (Dev Services)
```properties
# Quarkus 3.40.1.1 — illustrative (medium confidence) test profile
%test.quarkus.aws.devservices.provider=localstack          # default per 3.23.x docs, shown for clarity
%test.quarkus.aws.devservices.localstack.image-name=localstack/localstack:4.13   # the 3.23.x default
```

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment (Quarkus 3.40.1.1)
./mvnw test                         # expected: mock event server on :8081; @QuarkusTest classes pass
./mvnw verify -DskipITs=false       # expected: @QuarkusIntegrationTest classes run (failsafe) against the jar
./mvnw verify -Dnative -DskipITs=false   # native ITs; needs GraalVM/Mandrel or container build (exact flag combination for Lambda projects: medium confidence)
grep -rn "quarkus-test-amazon-lambda\|LambdaClient" pom.xml src/test          # expected: no match
grep -rn "quarkus.lambda.test-port\|quarkus.lambda.dev-port" src/             # expected: no match
grep -rn "endpoint-override" src/main/resources/application.properties        # expected: no %test value (keeps Dev Services on)
grep -rn "amazonaws.com" src/test                                             # expected: no match (no real AWS from tests)
sam local invoke --template target/sam.jvm.yaml --event payload.json          # optional, Docker needed; never deployment
```

**Mocking**: see A1, A4 and Step 7; `@InjectMock` details in `developing-quarkus-junit-v3-40`.

---

## Production Readiness

- **Performance (tests)**: mock event server avoids Docker and SAM; Dev Services adds a container start per test run ("sharing is always disabled" in test mode per the 3.23.x isolation section — note the page also lists `shared` default `true`, see U6).
- **CI**: Docker absence makes Dev Services tests fail ("In test mode, it will cause the test to fail"); disable Dev Services or set `endpoint-override` for such runners (C1).
- **Port clashes**: use `quarkus.lambda.mock-event-server.test-port=0` for random ports in parallel CI (C4).
- **Security**: no real credentials in tests (F2); tokens/claims in test events are fake values. Secrets come from Secrets Manager/SSM at runtime only (family rule 5).
- **Monitoring**: not applicable to tests; observability units U11-U13.

---

## Reference Implementations

- Quarkus 3.40 AWS Lambda guide, "Live Coding and Unit/Integration Testing" + "Testing with the SAM CLI": https://quarkus.io/version/3.40/guides/aws-lambda
- Quarkus 3.40 AWS Lambda HTTP guide, `AmazonLambdaSimpleTestCase`, "Simulate AWS Lambda Deployment with SAM CLI", "Simple SAM Local Principal": https://quarkus.io/version/3.40/guides/aws-lambda-http
- Mock event server source at tag 3.40.1.1: https://github.com/quarkusio/quarkus/tree/3.40.1.1/extensions/amazon-lambda/event-server
- Quarkiverse Dev Services 3.23.x: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html
- Sibling skill (by name): `developing-quarkus-junit-v3-40` (generic `@QuarkusTest`, `@InjectMock`, profiles).

---

## Source Bibliography

**Primary (versioned Quarkus 3.40 / source at tag / registry)**
| # | URL | Read | Coverage | Used for |
|---|---|---|---|---|
| S1 | https://quarkus.io/version/3.40/guides/aws-lambda | 2026-10-28 | Full per tool (not truncated), 2 passes | mock server, ports, test example, IT/native, SAM local, Gradle test deps |
| S2 | https://quarkus.io/version/3.40/guides/aws-lambda-http | 2026-10-28 | Full per tool (not truncated), 2 passes | HTTP test, `/_lambda_`, event classes, security keys, SAM start-api, FORCE_USER_NAME |
| S3 | https://quarkus.io/version/3.40/guides/all-config | 2026-10-28 | Partial: 0-100,000 of 232,437 chars (L2); Lambda sections inside the window | `quarkus.lambda.*` / `quarkus.lambda-http.*` keys, defaults, no deprecation |
| S4 | https://quarkus.io/version/3.40/guides/getting-started-testing | 2026-10-28 | 0-100,000 and 100,000-108,105 (two windows; full) | `@QuarkusIntegrationTest`, injection limit, prod profile, failsafe, `@InjectMock` |
| S5 | https://quarkus.io/version/3.40/guides/security-testing | 2026-10-28 | Full per tool | `@TestSecurity`, `quarkus-test-security`, `@QuarkusTest` only |
| S6 | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 | 2026-10-28 | Searched for lambda terms | removal of `quarkus-test-amazon-lambda` / `LambdaClient` |
| S7 | https://repo1.maven.org/maven2/io/quarkus/quarkus-test-amazon-lambda/maven-metadata.xml | 2026-10-28 | Full | latest 3.30.8 |
| S8 | https://repo1.maven.org/maven2/io/quarkus/quarkus-test-amazon-lambda/3.40.1.1/quarkus-test-amazon-lambda-3.40.1.1.pom | 2026-10-28 | HTTP 404 | absence at 3.40.1.1 |
| S9 | https://repo1.maven.org/maven2/io/quarkus/quarkus-junit-mockito/3.40.1.1/quarkus-junit-mockito-3.40.1.1.pom | 2026-10-28 | Full | artifact name/deps |
| S10 | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-http/3.40.1.1/quarkus-amazon-lambda-http-3.40.1.1.pom | 2026-10-28 | Full | deps (vertx-http, security, amazon-lambda) |
| S11 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-deployment/src/main/java/io/quarkus/amazon/lambda/deployment/DevServicesLambdaProcessor.java | 2026-10-28 | Full (summary by tool) | start conditions, port property, legacy check |
| S12 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/MockEventServerConfig.java | 2026-10-28 | Full | `quarkus.lambda` prefix, dev/test port defaults, not deprecated |
| S13 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/LambdaConfig.java | 2026-10-28 | Full | `handler()`, `mockEventServer()` |
| S14 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-deployment/src/main/java/io/quarkus/amazon/lambda/deployment/LambdaBuildConfig.java and …/MockEventServerBuildConfig.java | 2026-10-28 | Full | build-time `enabled` (default true) |
| S15 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/event-server/src/main/java/io/quarkus/amazon/lambda/runtime/MockEventServer.java | 2026-10-28 | Full (summary by tool) | routes, 500 on error, no timeout |
| S16 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AmazonLambdaApi.java | 2026-10-28 | Full | `/_lambda_`, runtime API paths |
| S17 | https://github.com/quarkusio/quarkus/tree/3.40.1.1/test-framework | 2026-10-28 | Directory listing | no amazon-lambda test module at 3.40.1.1 |

**Primary (Quarkiverse)**
| # | URL | Read | Used for |
|---|---|---|---|
| S18 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html | 2026-10-28 | Dev Services mechanism, providers, keys, defaults (version header "Amazon Services 3.23.x") |
| S19 | https://docs.quarkiverse.io/quarkus-amazon-services/dev/dev-services.html | 2026-10-28 | comparison only (dev line: Floci default) — not used for claims (family rule 2) |
| S20 | https://docs.quarkiverse.io/quarkus-amazon-services/dev/index.html | 2026-10-28 | version selector discovery |

**Family facts (applied as given)**: https://quarkus.io/releases ; https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 (junit rename) ; https://github.com/quarkiverse/quarkus-amazon-services/releases (3.23 ↔ 3.40, medium).

**Validation (community)**: none used. One WebSearch (2026-10-28) returned only official pages and was used only to locate S6.

---

## Research Gaps

```
U4 from U1 research — RESOLVED (iteration 1-2): quarkus.lambda.dev-port / quarkus.lambda.test-port are NOT marked
  deprecated in the 3.40 config reference (S3) nor in source (S12, no @Deprecated). They are a separate config root
  (MockEventServerConfig, prefix quarkus.lambda). The event server start-up (S11) reads only
  quarkus.lambda.mock-event-server.{test,dev}-port. Use the mock-event-server.* names.

U1 (unverified): whether any code other than DevServicesLambdaProcessor reads quarkus.lambda.dev-port / test-port
    (only that processor and the config classes were read). Follow-up: grep the 3.40.1.1 tag for devPort()/testPort().
U2 (unverified): whether RestAssured's default port follows a non-default/random mock-event-server.test-port
    (guide states it only for 8081). Follow-up: io.quarkus.test.common RestAssuredURLManager at tag 3.40.1.1.
U3 (unverified): whether @TestSecurity applies to requests entering through the Lambda HTTP mock event server.
U4 (unverified): construction of the guide's request(String) helper (required APIGatewayV2HTTPEvent fields) and a
    REST-API (AwsProxyRequest) raw-event test example; the guide shows neither.
U5 (unverified): whether the HTTP Lambda test also starts the vertx-http server on quarkus.http.test-port (8081)
    alongside the mock event server, and how the two share the port.
U6 (unverified): Dev Services sharing default — the 3.23.x page lists `shared` default true but its (legacy LocalStack)
    isolation section says sharing is disabled by default in dev mode and always disabled in test mode.
U7 (unverified): Dev Services for amazon-services in @QuarkusIntegrationTest / native ITs (not mentioned on S18), and
    which credentials/region values are injected ("configured automatically" only).
U8 (unverified): absence of mock-event-server changes in Quarkus 3.32-3.40 migration guides (not read).

M1 (medium confidence): reconstructed LambdaHandlerTest code (tool returned a summary, not the verbatim block).
M2 (medium confidence): Maven form of the guide's Gradle test dependencies.
M3 (medium confidence): @QuarkusIntegrationTest launches the jar/native/container, not function.zip (inference).
M4 (medium confidence): "IT extends @QuarkusTest class" pattern; "ITs run in prod profile / ignore test
    application.properties" (family rule 18).
M5 (medium confidence): illustrative code (error-path test, event JSON test, Dev Services properties, native verify command).
M6 (medium confidence): @TestSecurity being HTTP-oriented (inference from examples on S5).
M7 (medium confidence): quarkus-amazon-services 3.23.x ↔ Quarkus 3.40 pairing (family fact row 17).
M8 (medium confidence): System.getProperty caution applied by analogy to the mock server port property.

L1 (coverage limit): getting-started-testing read in two windows (0-100,000 and 100,000-108,105 of 108,105 chars);
    the page length differs from the 108,136 recorded in family rule 17 (page may have changed slightly).
L2 (coverage limit): all-config read 0-100,000 of 232,437 chars; the quarkus.lambda* / quarkus.lambda-http* sections
    were inside the window (the U1 research read the rest).
L3 (coverage limit): WebFetch summarisation; source files were summarised by the tool (identifiers/literals quoted).
```

Contradictions with family facts: none. Note (not a family fact): Quarkiverse `dev` docs name Floci as default provider while the 3.23.x docs name LocalStack (S18 vs S19); this research follows 3.23.x (family rule 2).

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Guardrails A3 / Gaps | U1-research U4: are `quarkus.lambda.dev-port`/`test-port` deprecated? | Resolved: not deprecated in config reference; separate root `MockEventServerConfig` | https://quarkus.io/version/3.40/guides/all-config ; MockEventServerConfig.java at 3.40.1.1 (2026-10-28) |
| 1 | Guardrails A3, F3 | Which key the event server actually reads | Resolved: `quarkus.lambda.mock-event-server.` + `test-port`/`dev-port` | DevServicesLambdaProcessor.java at 3.40.1.1 (2026-10-28) |
| 2 | Guardrails F1, Migration | Status of `quarkus-test-amazon-lambda` / `LambdaClient` | Resolved: removed (wiki 3.31), last 3.30.8, 404 at 3.40.1.1; legacy presence disables mock server | Migration-Guide-3.31 ; maven-metadata.xml ; DevServicesLambdaProcessor (2026-10-28) |
| 2 | Implementation Blueprint | Mock server endpoint path and error behaviour | Resolved: `/_lambda_`, default POST route, 500 on handler error, no response timeout | MockEventServer.java ; AmazonLambdaApi.java at 3.40.1.1 (2026-10-28) |
| 3 | Guardrails A7, C2 | Dev Services version line and default provider | Resolved: 3.23.x page, LocalStack `4.13` default (dev line differs: Floci) | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html (2026-10-28) |
| 3 | Research Gaps | U1-U8 | Left (unverified): MAX_ITERATIONS=3 reached; each has a follow-up path, so not IRRESOLVABLE | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Standard)
- [x] All scope areas cited (mock server + ports/keys + U4 resolution, removed test artifact/LambdaClient, @QuarkusTest+RestAssured plain/HTTP, @QuarkusIntegrationTest/native limits, AWS event payload JSON, Dev Services 3.23.x mechanism, SAM local as optional emulation, @InjectMock by reference, secured-endpoint testing as documented, "never call real AWS")
- [x] Pattern counts driven by domain needs (7 / 5 / 5)
- [x] Every anti-pattern has alternative (High alternatives only; medium parts tagged inline per family rule 9)
- [x] All CLI commands marked as representative
- [x] Integration examples complete within scope (Dev Services; client config deferred to U4/U5)
- [x] Sources dated and linked
- [x] Security documented (no real AWS, fake claims, @TestSecurity limits)
- [x] 1+ copy-paste working example (A4 verbatim lines except the undocumented `request()` helper; A3 properties)
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated or single versioned source (family rule 5 supersedes the downgrade)
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in the changelog (iteration 3 row)

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: A1-A7 and F1-F5 core claims (versioned guides, Central metadata, source at tag 3.40.1.1); use `quarkus.lambda.mock-event-server.*`; never `quarkus-test-amazon-lambda`.
- **Medium Confidence (validate with user)**: M1-M8; C1-C5 decisions (Dev Services vs mocks, provider, SAM local, ports, secured-endpoint approach).
- **Low Confidence (must ask human)**: U1-U8 (unverified); no IRRESOLVABLE items.
- **Edge Cases (pause)**: Quarkus 3.40.1.1 is > 30 days after 3.40.0 GA; no active CVE found in the pages read (not searched); Quarkus 4 content excluded (family rule 1).
- **Emergency Stop**: not triggered (all sources official).
