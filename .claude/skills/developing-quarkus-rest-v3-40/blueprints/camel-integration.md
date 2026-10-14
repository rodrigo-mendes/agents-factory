# Camel Integration: Quarkus REST 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Camel Quarkus 3.40.x runs on Quarkus 3.40.1 and Camel 4.22.1 (High; https://camel.apache.org/camel-quarkus/latest/). The Camel REST DSL is covered by the sibling skill `developing-camel-quarkus-rest-v3-40`.

## Contents

- [Resource plus ProducerTemplate](#resource-plus-producertemplate)
- [Choosing between resource and REST DSL](#choosing-between-resource-and-rest-dsl)
- [Both stacks on one server](#both-stacks-on-one-server)

## Resource plus ProducerTemplate

(medium confidence, main-branch evidence; register M6.) The `quarkus-rest-json` example in https://github.com/apache/camel-quarkus-examples (file `OrderResource.java`, main branch; its pom pins Quarkus platform 3.40.1) injects a `ProducerTemplate` into a Jakarta REST resource and calls `requestBody("direct:processOrder", ...)`. The pattern is published by the Camel Quarkus project but not in 3.40.x-tagged docs.

```java
// Quarkus 3.40.x + Camel Quarkus 3.40.x (pattern from the examples main branch)
@Path("/api/orders")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class OrderResource {
    @Inject ProducerTemplate producerTemplate;          // Camel Quarkus CDI bean

    @POST                                              // blocking signature: worker thread
    public Response createOrder(@Valid @NotNull Order order) {
        OrderResponse r = producerTemplate.requestBody("direct:processOrder", order, OrderResponse.class);
        return Response.status(Response.Status.CREATED).entity(r).build();
    }
}
```

```java
// route side (illustrative, written for this skill; not taken from the examples repo):
// no scope needed on the RouteBuilder because nothing is injected
public class OrderRoutes extends org.apache.camel.builder.RouteBuilder {
    @Override public void configure() { from("direct:processOrder").bean("orderService", "process"); }
}

// registration of "orderService" (illustrative): a CDI bean named with @Named
@jakarta.inject.Named("orderService")
@jakarta.enterprise.context.ApplicationScoped
public class OrderService {
    public OrderResponse process(Order order) { /* business logic */ return new OrderResponse(); }
}
```

A scope on a `RouteBuilder` is needed only for `@Inject` and `@ConfigProperty` (High; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html).

The example pom uses `quarkus-rest`, `quarkus-rest-jackson`, `camel-quarkus-jackson`, `camel-quarkus-direct`, `camel-quarkus-bean`, `camel-quarkus-kafka` and `quarkus-hibernate-validator`; tests use `quarkus-junit`, `rest-assured` and `awaitility` (https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/quarkus-rest-json/pom.xml, main, medium confidence).

Threading: a plain return type runs on a worker thread, which suits the blocking `ProducerTemplate` call. Returning `Uni` and calling `requestBody` inside would block the IO thread ([never-do](./never-do-patterns.md#1-blocking-call-on-an-io-thread-endpoint)).

## Choosing between resource and REST DSL

(medium confidence; register M6.)

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Quarkus REST resource + `ProducerTemplate` | Quarkus REST features: validation, security annotations, OpenAPI from Jakarta annotations, typed responses | Two layers (resource and route) | Rich API contract; Camel only for integration logic |
| Camel REST DSL (`camel-quarkus-rest` on platform-http) | Everything in Camel routes | Quarkus REST filters and `@ServerExceptionMapper` do not apply | Pure integration endpoints |

REST DSL needs `camel-quarkus-rest`. The platform-http page says "Configuration of the platform HTTP server is managed by Quarkus" and warns "care should be taken when modifying the router configuration when extensions such as RestEASY are present" (High for the quotes; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html).

## Both stacks on one server

- The examples `quarkus-rest-json` pom contains neither `camel-quarkus-platform-http` nor `camel-quarkus-rest`, so **no official source read shows both stacks on the same server**.
- The `rest-json` example of the Camel REST DSL in the same examples repository was not read (name only seen; coverage limit, register L4).
- What happens when a Quarkus REST resource and a platform-http route share a path is irresolvable (register I1).
- Whether `quarkus.rest.path` affects platform-http routes is (unverified) (register U2).
- Research workaround (tagged as the research's recommendation, not an official rule): use disjoint path prefixes, for example resources under `@Path("/api/...")` and the REST DSL under a distinct base such as `/camel`. Do not rely on `quarkus.rest.path` to separate them.
- Server TLS for the shared HTTP server: configure `quarkus.http.tls-configuration-name` explicitly. Whether the Camel Quarkus 3.40 TLS bridging affects the inbound server is (unverified) (register U7).
