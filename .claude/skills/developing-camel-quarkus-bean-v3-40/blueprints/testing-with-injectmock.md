# Testing with InjectMock

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Setup

(medium confidence; unversioned guide https://quarkus.io/guides/getting-started-testing, read to 100,000 of 108,136 characters). `@InjectMock` needs `io.quarkus:quarkus-junit-mockito` in test scope; the page names no `quarkus-junit5-mockito`. It works for normal-scoped beans such as `@ApplicationScoped`. A `@Singleton` bean needs `@MockitoConfig(convertScopes = true)`, which the docs call "an advanced option".

## Example

```java
// Quarkus 3.40: requires io.quarkus:quarkus-junit-mockito (test scope)
@io.quarkus.test.junit.QuarkusTest
class OrderRouteTest {
    @io.quarkus.test.InjectMock OrderService orderService;   // @ApplicationScoped is a normal scope
    @jakarta.inject.Inject org.apache.camel.ProducerTemplate template;

    @org.junit.jupiter.api.Test
    void routes() {
        org.mockito.Mockito.when(orderService.validate("a", null)).thenReturn("ok");
        org.junit.jupiter.api.Assertions.assertEquals("ok",
            template.requestBody("direct:order", "a", String.class));
    }
}
```

## Camel test artifact (High)

`camel-quarkus-junit5` was renamed `camel-quarkus-junit` (since 3.31), and the 3.40 testing guide documents only `camel-quarkus-junit` (https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html). Use `camel-quarkus-junit`. Stub details and removal date: [migration guide](./migration-guide.md). Camel route-test style and API signatures live in the skill `developing-camel-quarkus-junit-v3-40`.

## Unverified

- Whether a Camel registry lookup by `@Identifier` name returns the mock client proxy is (unverified). Test it in your build before relying on it.

## Commands

Representative, adapt to your environment; log output was not captured.

```bash
mvn test                 # @QuarkusTest, JVM mode
mvn verify -Dnative      # catches missing @RegisterForReflection
```
