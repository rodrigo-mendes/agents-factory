# CDI Naming, ArC Removal and Native Mode

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Contents

- [Named vs Identifier](#named-vs-identifier)
- [Scope and discovery](#scope-and-discovery)
- [ArC removal strategy](#arc-removal-strategy)
- [Native mode](#native-mode)
- [Consume on bean methods](#consume-on-bean-methods)

## Named vs Identifier

Orchestrator-verified fact (High; https://quarkus.io/version/3.40/guides/cdi-reference, fetched 2026-10-14): the Quarkus CDI reference says "Instead of @Named, use @io.smallrye.common.annotation.Identifier" except when an external language (for example Qute) needs the bean name. It lists `@Named` beans, observers and explicit exclusions (`@Unremovable`, `quarkus.arc.unremovable-types`) as unremovable.

`@Identifier` lookup from Camel routes is High: the Camel Quarkus CDI page says "As an alternative to @Named, you may also use io.smallrye.common.annotation.Identifier to name and identify a bean" (https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html). The only unverified part is ArC removal of an `@Identifier`-only bean: the CDI reference does not say, so it is (unverified). Recommend `@Unremovable`.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `@Named("x")` | Listed as unremovable | Adds `@Default` when it is the only qualifier, so same-type beans can be ambiguous (medium confidence, no page recorded) | Name-only lookup from Camel |
| `@Identifier("x")` | Type-safe qualifier, Quarkus-recommended | ArC removal when only looked up through Camel is (unverified) | Bean is also injected by type |
| `@Identifier("x")` + `@Unremovable` | Both properties | One extra annotation | Default recommendation when choosing `@Identifier` |

```java
// Camel Quarkus 3.40.x: defensive form
@jakarta.enterprise.context.ApplicationScoped
@io.smallrye.common.annotation.Identifier("orderService")
@io.quarkus.arc.Unremovable
@io.quarkus.runtime.annotations.RegisterForReflection
public class OrderService { /* ... */ }
```

Ask whether the bean is also injected by type elsewhere. If it is only referenced from routes, the default is `@Identifier` + `@Unremovable`; `@Named` is the form the CDI guide shows.

## Scope and discovery

(medium confidence) The page was read through the unversioned URL (https://quarkus.io/version/3.40/guides/cdi-reference is the versioned address; see L1 in the [register](./unverified-and-risks.md#coverage-limits)). Quarkus discovers only classes with a bean-defining annotation, so `@Named` alone is not a scope. Lookup returns null and the route fails with "no bean" at runtime.

```java
// 🚫 WRONG: no scope
@jakarta.inject.Named("svc") public class Svc { public String m(String b){ return b; } }
// ✅ CORRECT
@jakarta.enterprise.context.ApplicationScoped @jakarta.inject.Named("svc")
@io.quarkus.runtime.annotations.RegisterForReflection
public class Svc { public String m(String b){ return b; } }
```

Source: https://quarkus.io/version/3.40/guides/cdi-reference

## ArC removal strategy

(medium confidence) Source: https://quarkus.io/version/3.40/guides/cdi-reference, read through the unversioned URL, first 100,000 of 104,471 characters (L1). `quarkus.arc.remove-unused-beans` takes `all` (default), `fwk` or `none`; `quarkus.arc.unremovable-types=org.acme.**` marks packages unremovable. `none` removes the risk but grows memory and startup, so prefer per-class `@Unremovable` or `unremovable-types` over disabling removal.

## Native mode

- `@RegisterForReflection` on name-referenced beans: High; the native guide says classes needing reflective access must be registered at compile time (https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html).
- 3.40.0 `BeanProcessor` auto-registers classes with `@Handler` methods only (High; raw source at tag 3.40.0, URL in the [bibliography](./unverified-and-risks.md#source-bibliography)).
- Detect misses with `mvn verify -Dnative`. The research's helper `grep -rL "RegisterForReflection" src/main/java | xargs grep -l "@Named\|@Identifier"` is representative only; adapt to your layout.
- 3.40 `serialization-enabled` has three states; relevant only if beans pass `Serializable` payloads in native mode (medium confidence, via the core research; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html).

## Consume on bean methods

High (https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html). `@Consume("...")` on a bean method creates a route automatically, and Camel Quarkus adds `@Singleton` plus `@Named` unless a scope or name is already present. A `RouteBuilder` needs a CDI scope only when it uses `@Inject` or `@ConfigProperty`; a plain `RouteBuilder` without injection needs none.
