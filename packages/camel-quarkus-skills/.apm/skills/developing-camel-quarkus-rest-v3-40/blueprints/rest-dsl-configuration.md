# REST DSL Configuration — Camel Quarkus REST 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Contents

- [Full code-first example](#full-code-first-example)
- [Reuse the Quarkus ObjectMapper](#reuse-the-quarkus-objectmapper)
- [platform-http endpoint defaults](#platform-http-endpoint-defaults)
- [Authenticated user](#authenticated-user)
- [Performance and scalability](#performance-and-scalability)

## Full code-first example

The structure follows the official example (`main` branch) and the unversioned manuals (medium confidence). The `.param()...endParam()` syntax comes from a search snippet of https://camel.apache.org/manual/latest/rest-dsl.html (medium confidence; listed in the bibliography); the existence of a `.required(boolean)` builder method is (unverified).

```java
// Camel Quarkus 3.40.x. No injection here, so no @ApplicationScoped.
import org.apache.camel.Exchange;
import org.apache.camel.builder.RouteBuilder;
import org.apache.camel.model.rest.RestBindingMode;
import org.apache.camel.model.rest.RestParamType;

public class OrderApi extends RouteBuilder {
    @Override public void configure() {
        restConfiguration()
            .bindingMode(RestBindingMode.json)       // default off (rest-dsl-binding.html)
            .clientRequestValidation(true);          // default off (rest-dsl-validation.html)

        rest("/orders")
            .get("/{id}").produces("application/json").outType(Order.class)
                .param().name("verbose").type(RestParamType.query).defaultValue("false").endParam()
                .to("direct:getOrder")
            .post().consumes("application/json").type(Order.class).to("direct:createOrder");

        from("direct:getOrder").bean(OrderService.class, "find(${header.id})");
        from("direct:createOrder")
            .bean(OrderService.class, "create")
            .setHeader(Exchange.HTTP_RESPONSE_CODE, constant(201));
    }
}
```

## Reuse the Quarkus ObjectMapper

Source is the versioned jackson extension page (High). By default `JacksonDataFormat` creates its own `ObjectMapper` and ignores Quarkus `ObjectMapperCustomizer` beans. For REST binding set `autoDiscoverObjectMapper` as a data format property (string value) before defining the REST routes. The Main-property form `camel.rest.dataFormatProperties` is from the main options page, with no default listed. The property name `camel.dataformat.jackson.auto-discover-object-mapper` is (unverified).

```java
restConfiguration().bindingMode(RestBindingMode.json)
    .dataFormatProperty("autoDiscoverObjectMapper", "true");
```
```java
@jakarta.inject.Singleton
public class MapperCustomizer implements io.quarkus.jackson.ObjectMapperCustomizer {
    public void customize(com.fasterxml.jackson.databind.ObjectMapper m) { /* ... */ }
}
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jackson.html ; https://camel.apache.org/components/4.22.x/others/main.html

## platform-http endpoint defaults

Source: versioned component page https://camel.apache.org/components/4.22.x/platform-http-component.html.

| Option | Default |
|---|---|
| `matchOnUriPrefix` | `false` |
| `useBodyHandler` | `true` |
| `populateBodyWithForm` | `true` |
| `muteException` | `true` (keep it, so stack traces are not returned) |
| `returnHttpRequestHeaders` | `false` |
| `useStreaming` | `false` (platform-http-vertx only; useful for large bodies) |
| `cookiePath` / `cookieSameSite` | `/` / `Lax` |
| `cookieHttpOnly` / `cookieSecure` | `false` / `false` |
| component `serverRequestValidation` | `true` |

## Authenticated user

Medium confidence (investigator notes): the authenticated user is available in routes through header `VertxPlatformHttpConstants.AUTHENTICATED_USER` (`QuarkusHttpUser`). Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html

## Performance and scalability

- `inlineRoutes=true` is the default since Camel 4.5 (medium confidence) and reduces the route count (https://camel.apache.org/manual/rest-dsl.html). If one direct route serves several REST verbs, keep it un-inlined or split it, because inlining needs 1:1 unique direct endpoints.
- Throughput is bounded by the Quarkus Vert.x HTTP server; tune `quarkus.http.*` ([HTTP reference](https://quarkus.io/version/3.40/guides/http-reference), medium confidence).
- Performance numbers and REST-specific metrics: (unverified) (no official benchmarks or metrics page found).
