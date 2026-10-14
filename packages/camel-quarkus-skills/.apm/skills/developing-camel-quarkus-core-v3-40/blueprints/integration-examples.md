# Integration Examples, Testing, Endpoints — Camel Quarkus 3.40.x

Research date 2026-10-14. All commands are representative; adapt to your environment. Back to [SKILL.md](../SKILL.md).

## Project bootstrap (representative)

```bash
mvn io.quarkus:quarkus-maven-plugin:3.40.1:create \
  -DprojectGroupId=org.acme -DprojectArtifactId=getting-started \
  -Dextensions=camel-quarkus-log,camel-quarkus-timer
mvn clean compile quarkus:dev      # dev mode watches the workspace
```

The CamelContext is "started/stopped according to the Quarkus Application lifecycle". `quarkus.camel.bootstrap.enabled=true` is the default; shutdown is `quarkus.camel.main.shutdown.timeout` (default `PT3S`).

```properties
# Camel Quarkus 3.40.x: application.properties
quarkus.camel.routes-discovery.exclude-patterns = org.acme.legacy.**
camel.main.name = orders-integration
camel.main.use-mdc-logging = true             # default false
camel.component.log.exchange-formatter.show-body-type = false
timer.period = 2000
```

The Camel Main docs list keys in camelCase (`camel.main.useMdcLogging`). The kebab-case form relies on relaxed binding (unverified for the 3.40 page).

## ArC + bean + log

```java
// Camel Quarkus 3.40.x
@jakarta.enterprise.context.ApplicationScoped   // needed here only because of @ConfigProperty
public class OrderRoutes extends org.apache.camel.builder.RouteBuilder {
    @org.eclipse.microprofile.config.inject.ConfigProperty(name = "timer.period", defaultValue = "1000")
    String period;
    @Override public void configure() {
        from("timer:orders?period=" + period).routeId("orders")
            .setBody().constant("world")
            .to("direct:greet");
        from("direct:greet").routeId("greet")
            .bean("greeter", "hello")          // camel-quarkus-bean to CDI bean
            .to("log:greet?showAll=true")      // showAll option (unverified) for 4.22
            .id("greet-log");
    }
}
```

## Quarkus REST resource calling a route (medium confidence: main-branch official example)

The official examples repo injects a `ProducerTemplate` into a Jakarta REST resource and calls `requestBody("direct:processOrder", ...)` ([camel-quarkus-examples](https://github.com/apache/camel-quarkus-examples), `quarkus-rest-json`, `OrderResource.java`, main branch, pom pins Quarkus platform 3.40.1; fetched 2026-10-14; not in 3.40.x-tagged docs). That example uses neither `camel-quarkus-platform-http` nor `camel-quarkus-rest`; running both stacks on one HTTP server is (unverified).

```java
@jakarta.ws.rs.Path("/greet")
public class GreetResource {
    @jakarta.inject.Inject org.apache.camel.ProducerTemplate template;  // injectable per CQ CDI guide
    @jakarta.ws.rs.GET public String greet(@jakarta.ws.rs.QueryParam("name") String name) {
        return template.requestBody("direct:greet", name, String.class);
    }
}
```

Dependencies: `io.quarkus:quarkus-rest`, `camel-quarkus-direct`, `camel-quarkus-bean`, `camel-quarkus-log`.

Alternative, REST DSL (needs `camel-quarkus-platform-http` and `camel-quarkus-rest`):

```java
rest("/say").get("/hello").to("direct:greet");
```

## Error handling

Medium confidence: the Camel manual pages are unversioned and the fetched summaries were partly translated.

- "By default, any Exception Clause will **not** redeliver!"
- The DefaultErrorHandler has no dead letter queue and propagates the error to the caller.
- The dead letter channel default redelivery count and delay (research quote: "at most 6 times using 1-second delay") is (unverified): only a tool summary saw it. Set `maximumRedeliveries` and `redeliveryDelay` explicitly.
- For clause selection, "the closest match wins, across the thrown exception and all its causes".

```java
// Camel 4.22.x / Camel Quarkus 3.40.x
@Override public void configure() {
    errorHandler(deadLetterChannel("log:dead?level=ERROR")
        .maximumRedeliveries(3).redeliveryDelay(500));
    onException(IllegalArgumentException.class)
        .handled(true)              // caller does not see the exception
        .maximumRedeliveries(0)
        .to("log:invalid");
    from("direct:process").routeId("process").to("bean:greeter?method=hello");
}
```

Sources: https://camel.apache.org/manual/{exception-clause,error-handler,exception-redelivery,exception-handling-patterns}.html

## Component customization (medium confidence)

Observing `ComponentAddEvent` is the recommended approach per the bootstrap guide, and the event fires "before the routes and the CamelContext are started". Producing your own component instance skips the Quarkus-specific customization. The package `org.apache.camel.quarkus.core.events` is (unverified) against the 3.40 page; resolve the import with the IDE.

```java
@jakarta.enterprise.context.ApplicationScoped
public class ComponentConfig {
    void onAdd(@jakarta.enterprise.event.Observes org.apache.camel.quarkus.core.events.ComponentAddEvent e) {
        if (e.getComponent() instanceof org.apache.camel.component.log.LogComponent log) { /* customize */ }
    }
}
```

## Testing

"All tests should be annotated with `@QuarkusTest`." `CamelQuarkusTestSupport` works in JVM mode only. Its package and the `doBeforeEach` / `adviceRoute` signatures are stated in the skill `developing-camel-quarkus-junit-v3-40`; take them from there and do not hard-code them from this skill.

Route-test samples, AdviceWith usage, weave-point rules and lifecycle hooks live only in the skill `developing-camel-quarkus-junit-v3-40`. Use `@QuarkusIntegrationTest` for native tests.

## Endpoint facts (Camel 4.22.x component pages)

- `direct:name`: `failIfNoConsumers=true`, `block=true`, `timeout=30000`; synchronous, same CamelContext.
- `timer:name`: `delay=1000`, `period=1000`, `fixedRate=false`, `repeatCount` unset, `daemon=true`, `includeMetadata=false`.

## Operations

```bash
mvn quarkus:dev                          # expect startup logs (log output unverified)
mvn test                                 # @QuarkusTest suites, JVM mode
curl -s localhost:8080/q/health/ready    # with camel-quarkus-microprofile-health; expect {"status":"UP",...}
curl -s localhost:8080/q/health/live
```

- Health: `quarkus.camel.health.enabled=true` is the default (build time). The `/q/health` base path is (unverified).
- Metrics: `camel-quarkus-micrometer` defaults are route policy on, exchange and route event notifiers on, message history off. The `/q/metrics` path is (unverified).
- Tracing: `quarkus.camel.trace.*` (off by default).
- `direct` is synchronous within one CamelContext. Use a broker component for horizontal fan-out.

Reference implementations: https://github.com/apache/camel-quarkus-examples (`main` tracks the latest Quarkus Platform release); pinned versions (unverified), https://camel.apache.org/camel-quarkus/3.40.x/user-guide/first-steps.html
