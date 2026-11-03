# RestAssured and test data isolation

Back to [SKILL.md](../SKILL.md). Sources read 2026-11-01: [pom.xml 3.40.1](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/pom.xml), [RestAssured usage](https://github.com/rest-assured/rest-assured/wiki/Usage) (partial), [RestAssured changelog](https://raw.githubusercontent.com/rest-assured/rest-assured/master/changelog.txt) (partial), [all-config](https://quarkus.io/version/3.40/guides/all-config).

## Contents

- [Version facts](#version-facts)
- [Specification reuse](#specification-reuse)
- [Auth, JSON assertions and extraction](#auth-json-assertions-and-extraction)
- [Test data isolation](#test-data-isolation)
- [Full flow example](#full-flow-example)

## Version facts

- Quarkus 3.40.1 sets `rest-assured.version` to 6.0.1; the platform BOM manages `rest-assured`, `json-schema-validator` and `kotlin-extensions`.
- RestAssured 6.0.0 requires Java 17 and Groovy 5; 6.0.1 caps JSON number tokens at 1000 characters.
- Upstream 6.3.0 exists but is not managed by Quarkus 3.40: do not override.
- `quarkus.http.test-timeout` (default `30S`) is the client timeout; `quarkus.test.rest-assured.enable-logging-on-failure` defaults to `true`.
- In an IT, Quarkus points RestAssured at the launched app; do not set host or port by hand.

## Specification reuse

```java
static final RequestSpecification JSON = new RequestSpecBuilder()
    .setContentType(ContentType.JSON).addHeader("X-Tenant", "t1").build();

given().spec(JSON).when().get("/api/orders/42").then().statusCode(200);
```

- Build specs once as `static final`; add `ResponseSpecBuilder` for repeated status or content-type checks.
- Per-test differences go on the `given()` chain, not in the shared spec.

## Auth, JSON assertions and extraction

```java
given().spec(JSON).auth().preemptive().basic("alice", "alice")
    .when().get("/api/orders/42")
    .then().statusCode(200).body("id", equalTo(42)).body("items.size()", is(2));

String next = given().spec(JSON).auth().oauth2(token).when().get("/api/orders")
    .then().extract().path("_links.next.href");
```

- Use test users and test tokens only; never real credentials.
- The IT runs the `prod` profile, so prod-only security config must be overridden by a test resource.
- Body paths use Groovy GPath (`items.size()`); `extract().path(...)` feeds follow-up calls.

## Test data isolation

Derived guidance (medium confidence); no official page prescribes an IT data-reset mechanism (unverified).

- The app and its Dev Service database live for the whole Failsafe run, so tests share state.
- Create data with unique keys per test, for example `"it-" + UUID.randomUUID()`, and read back by that key.
- Never rely on method order; `quarkus.test.class-orderer` orders classes only.
- Tag created data (a prefix or a column) so a cleanup step or a later query can tell it apart from seed data.
- Do not assert on global counts or on "the first row"; assert on the key you created.
- Against a shared target (`test-host`), write tests only with explicit approval.

## Full flow example

```java
@QuarkusIntegrationTest
@ConnectWireMock(restClient = "orders-api")   // (unverified) for the launched process; also set %it.quarkus.rest-client.orders-api.url explicitly (see stubbing-and-containers.md)
class OrderFlowIT {
    WireMock wiremock;
    static final RequestSpecification JSON =
        new RequestSpecBuilder().setContentType(ContentType.JSON).build();

    @Test
    void R2_create_persistsAndCallsPricing() {
        String id = "it-" + UUID.randomUUID();
        wiremock.register(post(urlEqualTo("/price")).willReturn(okJson("{\"amount\":10}")));
        given().spec(JSON).body(Map.of("id", id, "sku", "A1"))
            .when().post("/api/orders")
            .then().statusCode(201).body("amount", equalTo(10));
        given().spec(JSON).when().get("/api/orders/" + id).then().statusCode(200);
        wiremock.verifyThat(1, postRequestedFor(urlEqualTo("/price")));
    }
}
```

Test names follow `R<n>_<scenario>_<expectation>` (factory convention F11, not part of Quarkus). The URL wiring for `orders-api` is in [stubbing](./stubbing-and-containers.md#url-wiring-for-the-launched-app).
