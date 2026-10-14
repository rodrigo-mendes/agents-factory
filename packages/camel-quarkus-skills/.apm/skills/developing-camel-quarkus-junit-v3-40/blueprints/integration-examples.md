# Integration Examples: REST Assured, Mockito, Test Resources, NotifyBuilder

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). For the generic Quarkus test framework see the sibling skill `developing-quarkus-junit-v3-40`.

## REST Assured (platform-http / REST DSL)

Quarkus 3.40: the test HTTP port defaults to 8081 (`quarkus.http.test-port`; 0 = random), the REST Assured base URL is configured automatically, and the timeout is 30 s (`quarkus.http.test-timeout`). Source: https://quarkus.io/version/3.40/guides/getting-started-testing

```java
@QuarkusTest
class HelloHttpTest {
    @Test
    void hello() {
        io.restassured.RestAssured.given().when().get("/hello").then().statusCode(200);
    }
}
```

## Mockito

`@InjectMock` and `@InjectSpy` need `quarkus-junit-mockito` at test scope (https://quarkus.io/version/3.40/guides/getting-started-testing).

```xml
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-junit-mockito</artifactId><scope>test</scope></dependency>
```

```java
@InjectMock GreetingService service;   // normal-scoped CDI bean used by a route
```

`@InjectMock` on a `@Singleton` or `@Dependent` bean is not possible without `@MockitoConfig(convertScopes = true)`; beans used during startup are not affected (https://quarkus.io/version/3.40/guides/getting-started-testing).

Behavior with beans that routes look up by name is (unverified): Quarkus documents `@InjectMock` generically only. Prefer `MockEndpoint`/AdviceWith for route collaborators.

## Test resources (WireMock, Testcontainers)

`start()` returns configuration that takes precedence over `application.properties`. `@QuarkusTestResource` is global by default (medium confidence; `restrictToAnnotatedClass = true` limits it to the annotated class); `@WithTestResource` has scopes `MATCHING_RESOURCES` (default), `RESTRICTED_TO_CLASS` and `GLOBAL`. Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html ; https://quarkus.io/version/3.40/guides/getting-started-testing

```java
public class WireMockResource implements QuarkusTestResourceLifecycleManager {
    WireMockServer server;
    public Map<String, String> start() {
        server = new WireMockServer(0); server.start();
        return Map.of("camel.component.foo.server-url", server.baseUrl());
    }
    public void stop() { server.stop(); }
}
@QuarkusTest @QuarkusTestResource(WireMockResource.class)
class FooTest extends CamelQuarkusTestSupport { }
```

## Registry binding (medium confidence)


The guide lists `@Produces @Named` CDI beans, `camelContext.getRegistry().bind(...)` inside `createCamelContext`, and a `@BindToRegistry` field, and says `createCamelRegistry` throws `UnsupportedOperationException`. The 3.40.0 source exposes `protected void bindToRegistry(Registry registry)` and `camelContextSupplier()` and declares no `createCamelContext` (irresolvable). Registry beans bound from a test persist for the suite unless a profile restarts the application. Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html ; the 3.40.0 source file linked in [always-do](./always-do-patterns.md#2-base-class-and-package).

## NotifyBuilder (medium confidence)

`org.apache.camel.builder.NotifyBuilder` is "only intended for testing purposes" and Java DSL only (https://camel.apache.org/manual/notify-builder.html, unversioned page). The 3.40 Camel Quarkus guide and the 3.40.0 source do not mention it; its behavior against the shared suite context is (unverified).

```java
// The manual sample uses the no-arg constructor; passing `context` is an adaptation
NotifyBuilder notify = new NotifyBuilder(context).whenDone(1).create();
template.sendBody("direct:orders", "x");
assertTrue(notify.matches(10, TimeUnit.SECONDS));
```
