# Camel, Config and REST Integration: Quarkus ArC 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Camel pages: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html unless stated.

## Contents

- [Calling a CDI bean from a route](#calling-a-cdi-bean-from-a-route)
- [Injecting Camel objects](#injecting-camel-objects)
- [RouteBuilder scope](#routebuilder-scope)
- [SmallRye Config](#smallrye-config)
- [Quarkus REST](#quarkus-rest)

## Calling a CDI bean from a route

Camel Quarkus 3.40 resolves `.bean("myBeanIdentifier", ...)` against `@Identifier("myBeanIdentifier")`, and documents `@Named` lookups too. The Camel Quarkus CDI page says: "As an alternative to @Named, you may also use io.smallrye.common.annotation.Identifier to name and identify a bean" (High; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html). Only ArC removal of an `@Identifier`-only bean is unverified (U1). The `camel-quarkus-bean` artifact provides bean lookup by name and `@Consume`.

```java
@ApplicationScoped
@Identifier("myBeanIdentifier")
@Unremovable
@RegisterForReflection
public class MyBean { public String hello(String n) { return "Hello " + n; } }

// in a RouteBuilder
from("direct:start").bean("myBeanIdentifier", "hello");   // or .to("bean:myBeanIdentifier?method=hello")
```

- `@RegisterForReflection` appears in the Camel docs recipe for beans called by name (native mode).
- `@Unremovable` is the workaround for the open questions U1 and U2; it is not stated as required ([bean removal](./bean-removal.md#identifier-only-beans)).
- `@Consume` beans get `@Singleton` and `@Named("<name><hash>")` added automatically.
- The bean-specific details (method selection, scopes of the Bean component) are covered by the sibling skill `developing-camel-quarkus-bean-v3-40`.

Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html

## Injecting Camel objects

Beans can inject `CamelContext`, `ProducerTemplate`, `FluentProducerTemplate`, `ConsumerTemplate` and `Registry`. `@EndpointInject` and `@Produce` on fields come from camel-quarkus-core.

In `bean` and `.process` calls, use `@ActivateRequestContext` to avoid `ContextNotActiveException` when a bean needs the request context.

```java
@ApplicationScoped
class Enricher {
    @Inject ProducerTemplate template;      // package-private, not private

    @ActivateRequestContext
    public void enrich(String body) { template.sendBody("direct:next", body); }
}
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html

## RouteBuilder scope

The scope on a `RouteBuilder` is "required for @Inject and @ConfigProperty" and otherwise costs boot time. See [always-do pattern 5](./always-do-patterns.md#5-routebuilder-scope-only-when-injecting).

## SmallRye Config

```java
@ConfigProperty(name = "greeting.suffix", defaultValue = "!") String suffix;  // @Inject optional
@ConfigProperty(name = "opt.value") Optional<String> opt;                     // missing gives empty
```

A missing non-`Optional` property fails startup with `ConfigurationException`. `@ConfigMapping` is the recommended approach for groups of properties.

Source: https://quarkus.io/version/3.40/guides/config-reference

## Quarkus REST

JAX-RS resources are unremovable roots in ArC (https://quarkus.io/version/3.40/guides/cdi-reference). For the default resource scope see skill `developing-quarkus-rest-v3-40`, which read the REST guide (medium confidence, register M5).
