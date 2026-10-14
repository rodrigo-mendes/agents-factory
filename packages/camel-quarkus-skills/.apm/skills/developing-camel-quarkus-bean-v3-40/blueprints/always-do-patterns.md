# Always-Do Patterns: Camel Quarkus Bean 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Patterns 1 to 3 rest on one versioned 3.40.x / 4.22.x page each. Pattern 4 (method selection) is an Ask First item with a medium-confidence rationale. Other medium-confidence topics (binding annotations, typed lookup, overloads) are in [bean binding](./bean-binding.md).

## 1. Register named beans for reflection

The native guide says classes needing reflective access must be registered at compile time. The CDI guide shows `@ApplicationScoped @Named("myNamedBean") @RegisterForReflection` and says the reflection annotation is important for native mode. That a scope is strictly required on a named bean is medium confidence: [scope and discovery](./cdi-and-native.md#scope-and-discovery).

```java
// Camel Quarkus 3.40.x
@jakarta.enterprise.context.ApplicationScoped
@jakarta.inject.Named("myNamedBean")
@io.quarkus.runtime.annotations.RegisterForReflection
public class NamedBean {
    public String hello(String name) { return "Hello " + name; }
}
// route: from("direct:named").bean("myNamedBean", "hello");
//    or: from("direct:named").to("bean:myNamedBean?method=hello");
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html. Choosing `@Identifier` instead is an Ask First item: see [CDI naming](./cdi-and-native.md#named-vs-identifier).

## 2. Thread-safe singleton beans

`scope` defaults to `Singleton`: created or looked up once and reused for the endpoint's lifetime. `Request` creates one per exchange; `Prototype` one per call, but the outcome depends on the delegated registry (CDI may still return a singleton). Whether `Request` gives one instance per exchange for a CDI-managed named bean is not stated on the page (medium confidence).

```java
// stateless bean: keep the default Singleton
from("direct:s").to("bean:pricing?method=quote");
// per-call state: keep it on the Exchange, not in bean fields; the bean stays stateless
from("direct:r").setProperty("limit", constant(10)).to("bean:pricing?method=quote");
// Ask First only (medium confidence, M13): per-exchange instance via scope=Request
// from("direct:r").to("bean:accumulator?method=add&scope=Request");
```

Source: https://camel.apache.org/components/4.22.x/bean-component.html

## 3. RouteBuilder scope only when injecting

A `RouteBuilder` needs `@ApplicationScoped` only for `@Inject` and `@ConfigProperty`; annotate it only when needed.

```java
// no injection: plain RouteBuilder
public class PlainRoutes extends org.apache.camel.builder.RouteBuilder {
    @Override public void configure() { from("direct:in").to("bean:myNamedBean?method=hello"); }
}

// injection: scope required
@jakarta.enterprise.context.ApplicationScoped
public class ConfiguredRoutes extends org.apache.camel.builder.RouteBuilder {
    @org.eclipse.microprofile.config.inject.ConfigProperty(name = "app.target") String target;
    @Override public void configure() { from("direct:cfg").to(target); }
}
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html

## 4. Select the target method

Ask First item (see SKILL.md). The Bean component has a `method` option, and the DSL accepts `.bean(name, method)` (High, https://camel.apache.org/components/4.22.x/bean-component.html). Marking one method with `@Handler` also selects it (medium confidence, manual page); the [integration examples](./integration-examples.md#bean-and-route) use that form. That pinning avoids `AmbiguousMethodCallException` and per-call selection cost is medium confidence (https://camel.apache.org/manual/bean-binding.html): [bean binding](./bean-binding.md#medium-confidence-pitfalls).

```java
// Camel 4.22.x / CQ 3.40.x: explicit method
from("direct:a").to("bean:orderService?method=validate");
from("direct:b").bean("orderService", "validate");
// or: one @Handler method on the bean, then from("direct:c").bean("orderService");
```
