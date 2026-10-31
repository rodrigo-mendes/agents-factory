# Integration Examples and Testing — Camel Quarkus REST 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Contents

- [Integration points](#integration-points)
- [Testing](#testing)
- [Reference implementations](#reference-implementations)

## Integration points

- **platform-http**: endpoints are served by the Quarkus Vert.x HTTP server. `quarkus.http.root-path` defaults to `/` and non-Servlet endpoints are served under it (medium confidence, https://quarkus.io/version/3.40/guides/http-reference). Whether REST DSL paths are prefixed by `root-path` is (unverified); test with `curl` in dev mode.
- **Quarkus REST (JAX-RS)**: both run on the same Vert.x server. `quarkus.http.auth.permission` with `applies-to=jaxrs` targets only JAX-RS (https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference, medium confidence). Path-collision behaviour between Quarkus REST and Camel REST is (unverified).
- **openapi-java / rest-openapi**: see [OpenAPI blueprint](./openapi-contract-first.md).
- **jackson**: see [REST DSL configuration](./rest-dsl-configuration.md#reuse-the-quarkus-objectmapper).

## Testing

Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html ; https://quarkus.io/version/3.40/guides/getting-started-testing (medium confidence, both pages). Camel route-test style (`CamelQuarkusTestSupport`, advice) lives in `developing-camel-quarkus-junit-v3-40`.

- Test dependencies in the official example: `quarkus-junit` and `io.rest-assured:rest-assured` (https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/rest-json/pom.xml, medium confidence: `main` branch example).
- `camel-quarkus-junit` is needed only for `CamelQuarkusTestSupport` (JVM only; one shared CamelContext per suite; `@TestProfile` to restart) (medium confidence).
- Tests run on port 8081 (`quarkus.http.test-port`, `0` = random); RestAssured timeout 30 s (`quarkus.http.test-timeout`).
- Replace backends with `@Alternative @Priority` CDI beans, `AdviceWith`, or WireMock/Testcontainers via `QuarkusTestResourceLifecycleManager`.

```java
// Camel Quarkus 3.40.x
@io.quarkus.test.junit.QuarkusTest
class FruitsTest {
    @org.junit.jupiter.api.Test
    void list() {
        io.restassured.RestAssured.given().when().get("/fruits")
            .then().statusCode(200);
    }
}
```

```bash
# Representative: adapt to your environment
./mvnw quarkus:dev
curl -s localhost:8080/fruits          # expected: 200 JSON array
curl -s localhost:8080/api-doc         # only if camel.rest.apiContextPath=/api-doc
./mvnw test                            # @QuarkusTest via Surefire
./mvnw verify -Dnative                 # @QuarkusIntegrationTest via Failsafe
```

## Reference implementations

All under https://github.com/apache/camel-quarkus-examples (fetched 2026-10-14):

- `rest-json`: code-first, JSON binding, pins Quarkus platform 3.40.1.
- `openapi-contract-first`: contract-first, codegen, `/api-doc`.
- `platform-http-security-keycloak`: secured platform-http.
- `quarkus-rest-json`: Quarkus REST alongside Camel.
