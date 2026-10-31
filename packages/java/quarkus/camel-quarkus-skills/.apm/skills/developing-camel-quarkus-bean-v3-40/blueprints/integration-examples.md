# Integration Examples

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). The `RouteBuilder` below has no `@Inject` or `@ConfigProperty`, so it carries no CDI scope (https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html). Bean classes themselves need a scope.

## Bean and route

```xml
<!-- Camel Quarkus 3.40.x: versions managed by quarkus-camel-bom -->
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-bean</artifactId></dependency>
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-direct</artifactId></dependency>
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-log</artifactId></dependency>
```

```java
// Camel Quarkus 3.40.x
@jakarta.enterprise.context.ApplicationScoped
@io.smallrye.common.annotation.Identifier("orderService")
@io.quarkus.arc.Unremovable                 // defensive: ArC removal of an @Identifier-only bean is (unverified)
@io.quarkus.runtime.annotations.RegisterForReflection
public class OrderService {
    @org.apache.camel.Handler
    public String validate(@org.apache.camel.Body String body,
                           @org.apache.camel.Header("source") String source) {
        if (body == null || body.isBlank()) throw new IllegalArgumentException("empty");
        return source + ":" + body;
    }
}

public class OrderRoutes extends org.apache.camel.builder.RouteBuilder {
    @Override public void configure() {
        onException(IllegalArgumentException.class).handled(true).to("log:invalid?level=WARN");
        from("direct:order").routeId("order")
            .bean("orderService")            // @Handler selects validate() (medium confidence); or .bean("orderService", "validate")
            .to("log:order");
    }
}
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html ; https://camel.apache.org/components/4.22.x/bean-component.html

## Integrations

- **ArC (High)**: inject Camel's registry or `ProducerTemplate` into beans; `@Consume` on a bean method creates a route (https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html).
- **camel-quarkus-log**: `to("log:name")` after bean calls; the log extension has no options of its own (see the skill `developing-camel-quarkus-log-v3-40`); the Log component options were not researched here (unverified).
- **camel-quarkus-jaxb**: bean methods receiving unmarshalled objects bind by body type conversion (medium confidence; https://camel.apache.org/manual/bean-binding.html). Native registration of JAXB classes is (unverified).
- **Examples repository**: https://github.com/apache/camel-quarkus-examples; bean-specific example names are unverified.
