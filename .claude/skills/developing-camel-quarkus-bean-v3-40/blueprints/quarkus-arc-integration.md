# Camel, Config and REST Integration: Quarkus ArC 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Camel pages: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html unless stated.

Moved from `developing-quarkus-arc-v3-40` (blueprint `camel-integration`). Register ids in this file are the ids of this skill's [register](./unverified-and-risks.md): U1 (ArC removal of an `@Identifier`-only bean; the same open question is U1 in the `developing-quarkus-arc-v3-40` register), U14 (Camel Quarkus marking name-looked-up beans unremovable; U2 in the ArC register) and M16 (Quarkus REST resources as unremovable roots; M5 in the ArC register). The ArC-side links point to the sibling skill `developing-quarkus-arc-v3-40` (resolved after install, `.claude/skills/` is flat).

## Contents

- [Calling a CDI bean from a route](#calling-a-cdi-bean-from-a-route)
- [Injecting Camel objects](#injecting-camel-objects)
- [RouteBuilder scope](#routebuilder-scope)
- [SmallRye Config](#smallrye-config)
- [Quarkus REST](#quarkus-rest)

## Calling a CDI bean from a route

Camel Quarkus 3.40 resolves `.bean("myBeanIdentifier", ...)` against `@Identifier("myBeanIdentifier")`, and documents `@Named` lookups too. The Camel Quarkus CDI page says: "As an alternative to @Named, you may also use io.smallrye.common.annotation.Identifier to name and identify a bean" (High; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html). Only ArC removal of an `@Identifier`-only bean is (unverified, U1). The `camel-quarkus-bean` artifact provides bean lookup by name and `@Consume`.

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
- `@Unremovable` is the workaround for the open questions (unverified, U1) and (unverified, U14: whether Camel Quarkus 3.40 marks beans referenced by name in routes as unremovable); it is not stated as required (see [Named vs Identifier](./cdi-and-native.md#named-vs-identifier) here and "bean removal / identifier-only beans" in `developing-quarkus-arc-v3-40`).
- `@Consume` beans get `@Singleton` and `@Named("<name><hash>")` added automatically.
- The bean-specific details (method selection, scopes of the Bean component) are covered by this skill (`developing-camel-quarkus-bean-v3-40`).

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

The scope on a `RouteBuilder` is "required for @Inject and @ConfigProperty" and otherwise costs boot time. See the local always-do pattern [3. RouteBuilder scope only when injecting](./always-do-patterns.md#3-routebuilder-scope-only-when-injecting) (the ArC skill has the same pattern as its pattern 5).

## SmallRye Config

```java
@ConfigProperty(name = "greeting.suffix", defaultValue = "!") String suffix;  // @Inject optional
@ConfigProperty(name = "opt.value") Optional<String> opt;                     // missing gives empty
```

A missing non-`Optional` property fails startup with `ConfigurationException`. `@ConfigMapping` is the recommended approach for groups of properties.

Source: https://quarkus.io/version/3.40/guides/config-reference

## Quarkus REST

JAX-RS resources are unremovable roots (medium confidence, M16; https://quarkus.io/version/3.40/guides/cdi-reference). The local lists of unremovable roots are in [Named vs Identifier](./cdi-and-native.md#named-vs-identifier). For the default resource scope see skill `developing-quarkus-rest-v3-40`, which read the REST guide (also M16).
