# Always-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. HTTP Lambda tests: [http-lambda-testing](./http-lambda-testing.md).

## Contents

- [1. Plain handler test](#1-plain-handler-test)
- [2. Test dependencies](#2-test-dependencies)
- [3. Mock event server keys](#3-mock-event-server-keys)
- [4. Integration and native tests](#4-integration-and-native-tests)
- [5. Dev Services for AWS calls](#5-dev-services-for-aws-calls)

## 1. Plain handler test

"For your unit tests, you can also invoke on the mock event server using any HTTP client you want." In test mode the server listens on 8081 and "The default port for Rest Assured is automatically set to 8081 by Quarkus" ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)). `Person` is the guide's input POJO. The code is a reconstruction of the guide's `LambdaHandlerTest`, which the fetch tool returned as a summary (medium confidence).

```java
// Quarkus 3.40.1.1 — plain RequestHandler test
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

Error path (medium confidence, one tag for the 500 status and the illustrative test): a handler error comes back from the mock event server as status 500 ([MockEventServer at tag 3.40.1.1](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/event-server/src/main/java/io/quarkus/amazon/lambda/runtime/MockEventServer.java)).

```java
// Quarkus 3.40.1.1 — handler throws -> mock event server returns 500
@Test
void rejectsInvalidInput() {
    given().contentType("application/json").body("{}")
           .when().post()
           .then().statusCode(500);
}
```

AWS event payload as input (illustrative, medium confidence): keep the JSON under `src/test/resources/events/` and POST it like any input. Using `aws-lambda-java-events` classes as handler input is not documented in the 3.40 guides; that question belongs to `developing-quarkus-amazon-lambda-v3-40`.

```java
String payload = Files.readString(Path.of("src/test/resources/events/sqs-event.json"));
given().contentType("application/json").body(payload).when().post().then().statusCode(200);
```

## 2. Test dependencies

The guide's Gradle sample lists `testImplementation 'io.quarkus:quarkus-junit'` and `testImplementation 'io.rest-assured:rest-assured'` ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)). `quarkus-junit5` was renamed `quarkus-junit` in 3.31 ([wiki](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31)). The guide gives no Maven snippet; the form below is the equivalent with versions from the Quarkus BOM (medium confidence).

```xml
<!-- Quarkus 3.40.1.1 -->
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

For `@InjectMock` add `io.quarkus:quarkus-junit-mockito` (POM name "Quarkus - Test framework - JUnit - Mockito", depends on `quarkus-junit`). Rules, including `@Singleton` needing `@MockitoConfig(convertScopes = true)`, are in `developing-quarkus-junit-v3-40`.

## 3. Mock event server keys

The guide documents the two port keys; `enabled` is listed by the configuration reference. "A port value of zero will result in a randomly assigned port." The event-server start-up builds the property name as `quarkus.lambda.mock-event-server.` + `test-port` or `dev-port` (source at tag 3.40.1.1). That the `mock-event-server.*` names are the ones to use is derived from source, not from a guide statement (medium confidence). Details of the start-up: [mock-event-server](./mock-event-server.md).

| Key | Env var | Default | Source |
|---|---|---|---|
| `quarkus.lambda.mock-event-server.dev-port` | `QUARKUS_LAMBDA_MOCK_EVENT_SERVER_DEV_PORT` | `8080` | [all-config](https://quarkus.io/version/3.40/guides/all-config) |
| `quarkus.lambda.mock-event-server.test-port` | `QUARKUS_LAMBDA_MOCK_EVENT_SERVER_TEST_PORT` | `8081` | [all-config](https://quarkus.io/version/3.40/guides/all-config) |
| `quarkus.lambda.mock-event-server.enabled` | `QUARKUS_LAMBDA_MOCK_EVENT_SERVER_ENABLED` | `true` (medium confidence, M12) | [all-config](https://quarkus.io/version/3.40/guides/all-config) |

The values below are the guide's example, not defaults.

```properties
# Quarkus 3.40.1.1 — the guide's example
quarkus.lambda.mock-event-server.dev-port=8082
quarkus.lambda.mock-event-server.test-port=8083
# quarkus.lambda.mock-event-server.enabled=false   # turns the server off
```

`enabled=true` starts the event server even if `quarkus.devservices.enabled=false` (all-config; medium confidence, M12).

## 4. Integration and native tests

"The mock event server is also started for `@QuarkusIntegrationTest` tests so will work with native binaries too" (aws-lambda and aws-lambda-http guides). `@QuarkusIntegrationTest` "should be used to launch and test the artifact produced by the Quarkus build" and "supports all the features mentioned in this guide except injecting into tests" ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing), read in two windows, L1). Integration tests run with the `prod` profile and cannot use test-specific `src/test/resources/application.properties` settings (medium confidence).

The Lambda guides show no IT class; the common pattern from the testing guide is (medium confidence):

```java
// Quarkus 3.40.1.1 — runs LambdaHandlerTest against the built artifact
@QuarkusIntegrationTest
public class LambdaHandlerIT extends LambdaHandlerTest { }
```

The IT launches the built jar, native executable or container image, not `function.zip` itself (medium confidence, inference from the testing guide). The generic guide uses `maven-failsafe-plugin` (`integration-test`, `verify`) and `-DskipITs=false`. The guide's native command `./mvnw install -Dnative -DskipTests -Dquarkus.native.container-build=true` skips tests.

## 5. Dev Services for AWS calls

"Quarkus Amazon Services automatically starts a containerized AWS stack in dev mode and when running tests." They are disabled when the `endpoint-override` is configured. Global switch `quarkus.devservices.enabled=false`; per extension `quarkus.<service>.devservices.enabled=false`, for example `quarkus.dynamodb.devservices.enabled=false`. "The extension client is configured automatically." Dev Services "does not verify if the chosen stack actually implements a mock for a given service" ([Dev Services 3.23.x](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html)). The container route is option A of [Ask First C1](./ask-first-decisions.md#c1-dev-services-injectmock-or-endpoint-override); `@InjectMock` and `endpoint-override` are the alternatives. Client configuration belongs to `integrating-quarkus-amazon-data-v3-40` and `integrating-quarkus-amazon-messaging-v3-40`.

```properties
# Quarkus 3.40.1.1 + quarkus-amazon-services 3.23.x — keep endpoint-override OUT of the test profile
# %test.quarkus.dynamodb.endpoint-override=...   <- would disable Dev Services
```

Without Docker "In test mode, it will cause the test to fail". Whether Dev Services work in `@QuarkusIntegrationTest` and native ITs, and which credentials and region are injected, is (unverified). The Dev Services sharing default is also (unverified): the 3.23.x page lists `shared` default `true` while its isolation section says sharing is always disabled in test mode. The 3.23.x ↔ Quarkus 3.40 pairing is (medium confidence).
