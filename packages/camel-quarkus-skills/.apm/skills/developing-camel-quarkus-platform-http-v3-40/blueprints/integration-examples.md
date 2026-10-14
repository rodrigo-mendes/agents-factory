# Integration Examples, Testing, Management Port — Platform HTTP 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Contents

- [REST DSL](#rest-dsl)
- [Vert.x Router](#vertx-router)
- [Streaming](#streaming)
- [Reverse proxy](#reverse-proxy)
- [Error handling](#error-handling)
- [Management port](#management-port)
- [Testing](#testing)

## REST DSL

Requires `camel-quarkus-rest`; the REST DSL runs on platform-http ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)). The page also warns that RESTEasy may register its own error handling (medium confidence for the choice between REST DSL and a Quarkus REST resource).

```java
// Camel Quarkus 3.40.x with camel-quarkus-rest
rest("/api").get("/items").to("direct:list").post("/items").to("direct:create");
```

## Vert.x Router

The extension page names the pattern of observing the Vert.x `Router` (for a custom 404). The exact code below is (unverified); check the event type and imports in the IDE.

```java
void init(@Observes Router router) {
    router.route().last().handler(ctx -> ctx.response().setStatusCode(404).end("not found"));
}
```

## Streaming

`useStreaming=false` is the default (buffered); `true` streams and is Vert.x engine only ([component page](https://camel.apache.org/components/4.22.x/platform-http-component.html)). A streamed body is single-read (medium confidence). Use it only for large payloads.

## Reverse proxy

`platform-http:proxy` is supported only on Quarkus (`camel-platform-http-vertx`); use `toD` with `Exchange.HTTP_HOST`, and some headers come from the absolute URL on the request line (medium confidence; [component page](https://camel.apache.org/components/4.22.x/platform-http-component.html), [extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)). Lock it down by authentication, or it is an open forward proxy.

## Error handling

`muteException` defaults to `true` ([component page](https://camel.apache.org/components/4.22.x/platform-http-component.html)). That `muteException=false` returns exception details to clients is inferred from the option description (medium confidence). Keep the default and map errors:

```java
// Camel Quarkus 3.40.x; no injection, so no @ApplicationScoped
public class ApiRoutes extends RouteBuilder {
    @Override
    public void configure() {
        onException(IllegalArgumentException.class).handled(true)
            .setHeader(Exchange.HTTP_RESPONSE_CODE, constant(400))
            .setBody(constant("{\"error\":\"bad request\"}"));

        from("platform-http:/hello?httpMethodRestrict=GET")
            .setBody(simple("Hello ${header.name}"));
    }
}
```

## Management port

`quarkus.management.enabled` is build-time and defaults to `false`. When on, the port is `9000` (test `9001`), the root path is `/q`, and Health, Micrometer and Info move there ([management reference](https://quarkus.io/version/3.40/guides/management-interface-reference)). Enable it when health and metrics must not be reachable through the public ingress.

## Testing

`@QuarkusTest` with RestAssured hits the real platform-http endpoint. For test artifact naming see the skill `developing-camel-quarkus-junit-v3-40`; the `quarkus.http.test-port` default (8081) is (unverified).

```java
@QuarkusTest
class HelloTest {
    @Test
    void hello() {
        given().queryParam("name", "x").get("/hello").then().statusCode(200);
    }
}
```

```bash
# Representative; adapt to your environment
./mvnw quarkus:dev
curl -i "http://localhost:8080/hello?name=x"     # port 8080 default (unverified)
curl -i -X POST http://localhost:8080/hello      # expect rejection; 405 is (unverified)
./mvnw verify -Pnative                           # native profile name (unverified)
```
