# Bean Binding, Scope and Method Selection

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Most content here comes from the unversioned Camel manual pages, so it is (medium confidence) unless a versioned page is named.

## Contents

- [Invocation styles](#invocation-styles)
- [Parameter binding annotations](#parameter-binding-annotations)
- [Medium-confidence pitfalls](#medium-confidence-pitfalls)
- [Typed lookup](#typed-lookup)
- [Async return](#async-return)
- [Production notes](#production-notes)

## Invocation styles

High confidence (bean component 4.22.x, extension page). Endpoint options: `method`, `scope` (default `Singleton`), `parameters`, `lazyStartProducer` (default `false`); component option `beanInfoCacheSize` (default `1000`).

| Style | Example | Best when |
|---|---|---|
| Registry name | `.to("bean:x?method=m")`, `.bean("x", "m")` | CDI-managed services (CDI injection inside the bean) |
| Class or instance | `.bean(MyClass.class)`, `.bean(new X())`, `class:fqcn` | stateless helpers, no CDI lifecycle |

Registry-name beans need manual reflection registration for native; see [CDI and native](./cdi-and-native.md). `class:` component options and Bean Method language options are (unverified).

Sources: https://camel.apache.org/components/4.22.x/bean-component.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html

## Parameter binding annotations

Medium confidence (single unversioned manual page). `org.apache.camel` provides `@Body`, `@Header`, `@Headers`, `@Variable`, `@Variables`, `@ExchangeProperty`, `@ExchangeProperties`, `@ExchangeException`. Without annotations the body binds to the first parameter that is not a built-in type (`Exchange`, `Message`, `CamelContext`, `TypeConverter`, `Registry`, `Exception`).

```java
// Camel 4.22.x
public String route(@org.apache.camel.Body String body,
                    @org.apache.camel.Header("operation") String op,
                    @org.apache.camel.ExchangeProperty("tenant") String tenant) {
    return op + ":" + tenant + ":" + body;
}
```

Type+value qualifiers (`int.class 123`) exist in Camel 4.x (medium confidence). Sources: https://camel.apache.org/manual/parameter-binding-annotations.html ; https://camel.apache.org/manual/bean-binding.html

## Medium-confidence pitfalls

These are not Never Do rules because the research tagged them medium.

Overloaded methods without a qualifier lead to `AmbiguousMethodCallException`.

```java
// 🚫 .bean("svc", "hello")            // hello(String) and hello(String,String) both exist
// ✅ .bean("svc", "hello(String.class)")
```

The manual says the return type cannot be `Exchange`; take it as an input instead.

```java
// 🚫 public Exchange process(Exchange e){ return e; }
// ✅ public void process(Exchange e){ e.getMessage().setBody("x"); }
```

Source: https://camel.apache.org/manual/bean-binding.html

Method selection (medium confidence): without a pinned method Camel runs a multi-step selection that ends in body-type matching and throws `AmbiguousMethodCallException` when no single method fits. `@Handler` keeps the route independent of method renames.

## Typed lookup

Medium confidence (unversioned registry manual; the CDI guide is versioned). Beans of different types can share a name, so prefer `lookupByNameAndType`. The DefaultRegistry looks in the runtime platform (ArC) first, then falls back to `SimpleRegistry`. The `org.apache.camel.spi.Registry` package is (unverified): it is not shown on the Camel Quarkus page.

```java
// the Registry package below is unverified: confirm the import in your build
@jakarta.inject.Inject org.apache.camel.spi.Registry registry;
CoolBean bean = registry.lookupByNameAndType("coolBean", CoolBean.class);
```

Sources: https://camel.apache.org/manual/registry.html ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html

## Async return

Medium confidence. Methods may return `CompletionStage`; Camel applies no timeout, and completing with `null` leaves the body unchanged. Source: https://camel.apache.org/manual/bean-binding.html

## Production notes

- `beanInfoCacheSize` caches introspection, not instances (High; https://camel.apache.org/components/4.22.x/bean-component.html). Pinning the method avoids per-call selection cost (inference, medium confidence).
- Exceptions thrown by bean methods go to the route's `onException` or error handler; an `Exception` parameter binds the caught exception (medium confidence; https://camel.apache.org/manual/bean-binding.html). Redelivery defaults for bean exceptions were not verified in this run (unverified).
- No bean-specific metrics are listed on the extension page; use route metrics from `camel-quarkus-micrometer` (unverified).
