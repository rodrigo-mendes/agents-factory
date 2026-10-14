---
name: developing-camel-quarkus-bean-v3-40
description: "Guides Camel Quarkus 3.40.x bean binding (camel-quarkus-bean, Camel 4.22): bean:, class:, CDI beans, @Handler, native reflection. Use when routes call Java or CDI beans. Not for Quarkus 4, other versions or consuming from bean:."
---

# Developing with Camel Quarkus Bean 3.40.x

> Version lock: every claim applies to **Camel Quarkus 3.40.x** (Camel 4.22.x component docs) only. Research date **2026-10-14**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Core topics (BOMs, CDI basics, route discovery) belong to the sibling skill `developing-camel-quarkus-core-v3-40`.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| Camel Quarkus | 3.40.x; 3.40.0 released 2026-09-28, marked LTS; no LTS-until date given | https://camel.apache.org/releases/ |
| Maven artifact | `camel-quarkus-bean` 3.40.0 uploaded 2026-09-24 | https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-bean/ |
| Camel / Quarkus / GraalVM | 4.22.1 / 3.40.1 / 25.0.4.1 | https://camel.apache.org/camel-quarkus/latest/ |
| `camel-quarkus-bean` status | JVM and native since 0.1.0; no `quarkus.camel.*` options listed | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html |
| Java | 17 and 21 ("This version supports Java 17 and 21") | https://camel.apache.org/releases/q-3.40.0/ |
| Quarkus 3.40 | released 2026-09-30, LTS, community-maintained until 2027-09-30 | https://quarkus.io/releases |

**Version-lifetime risk** (as of 2026-10-14; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; Java 21 becomes the base ([source](https://quarkus.io/blog/quarkus-4-0-0-beta1-released/)). No Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence). Pin 3.40.x.
- The Camel Quarkus-specific support end date for 3.40 is not published (unverified).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Bean binding, scope and method selection](./blueprints/bean-binding.md)
- [CDI naming, ArC removal and native mode](./blueprints/cdi-and-native.md)
- [Testing with InjectMock](./blueprints/testing-with-injectmock.md)
- [Migration guide (3.15 baseline to 3.40)](./blueprints/migration-guide.md)
- [Integration examples](./blueprints/integration-examples.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Add `@RegisterForReflection` to every bean a route references by name.** Classes needing reflective access must be registered at compile time in native mode ([native guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html)). See [patterns](./blueprints/always-do-patterns.md#1-register-named-beans-for-reflection).
- **Keep singleton beans thread-safe.** `scope` defaults to `Singleton`: one instance reused for the endpoint's lifetime ([bean component](https://camel.apache.org/components/4.22.x/bean-component.html)). See [patterns](./blueprints/always-do-patterns.md#2-thread-safe-singleton-beans).
- **Leave a `RouteBuilder` unscoped unless it uses `@Inject` or `@ConfigProperty`.** The scope is required only for those and adds a boot-time penalty ([CDI guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html)). See [patterns](./blueprints/always-do-patterns.md#3-routebuilder-scope-only-when-injecting).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| `@Named` vs `@Identifier` | Quarkus says "Instead of @Named, use @io.smallrye.common.annotation.Identifier" except when an external language needs the bean name; `@Named` beans and `@Unremovable` beans are unremovable ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)). Camel routes can look up an `@Identifier` bean ([CDI guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html)). ArC removal of an `@Identifier`-only bean is (unverified). Default for route-only beans: `@Identifier` + `@Unremovable`; `@Named("x")` is the form the CDI guide shows | "Is the bean also injected by type elsewhere, or only referenced from routes?" |
| Scope on a named bean (medium confidence) | Quarkus discovers only classes with a bean-defining annotation, so `@Named` alone is not enough; the CDI guide recipe is `@ApplicationScoped @Named("x") @RegisterForReflection` ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)) | "Does every bean class carry a scope?" |
| Method selection (medium confidence) | Name the method with `method=` or `.bean(name, method)` (the options exist on the [bean component](https://camel.apache.org/components/4.22.x/bean-component.html) page), or mark one method `@Handler`; avoids `AmbiguousMethodCallException` and per-call selection ([bean binding manual](https://camel.apache.org/manual/bean-binding.html)). See [patterns](./blueprints/always-do-patterns.md#4-select-the-target-method) | "Is there more than one candidate method, and may the route depend on `@Handler`?" |
| Invocation style | `bean:x?method=m` / `.bean("x","m")` (registry, CDI injection; [bean component](https://camel.apache.org/components/4.22.x/bean-component.html)) vs `.bean(MyClass.class)` / `.bean(new X())` / `class:fqcn` (no CDI lifecycle) (unverified) | "Does the bean need CDI injection?" |
| ArC removal (medium confidence) | Keep default removal + `@Unremovable` or `quarkus.arc.unremovable-types` vs `none` (more memory and startup) ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)) | "Which beans are reached only by name?" |
| Per-exchange state | `scope=Request` vs stateless singleton; `Prototype` depends on the registry, CDI may still return a singleton ([bean component](https://camel.apache.org/components/4.22.x/bean-component.html)). Whether `Request` yields one instance per exchange for a CDI-managed named bean is not stated on the page (medium confidence) | "Does the bean hold state between calls?" |
| Typed lookup (medium confidence) | `lookupByNameAndType` because beans of different types can share a name ([registry manual](https://camel.apache.org/manual/registry.html)); the `Registry` package is (unverified) on the Camel Quarkus page | "Do several beans share a name?" |
| Parameter annotations (medium confidence) | `@Body`, `@Header`, `@ExchangeProperty` etc. vs reading `Exchange` manually | "Which headers or properties must the method receive?" |
| Overloads and return type (medium confidence) | Qualify overloads (`hello(String.class)`) or hit `AmbiguousMethodCallException`; the return type cannot be `Exchange` | "Are there overloaded methods, and does any return `Exchange`?" |
| Async return (medium confidence) | `CompletionStage` return: no timeout applied, `null` leaves the body unchanged | "Can the future hang or complete with null?" |
| Mocking a `@Singleton` bean (medium confidence) | `@InjectMock` works on normal scopes; `@Singleton` needs `@MockitoConfig(convertScopes = true)`, "an advanced option" ([testing guide](https://quarkus.io/guides/getting-started-testing)) | "Can the bean use `@ApplicationScoped`?" |
| Bean or class URI from input (inferred, unverified) | Fixed bean names in routes vs names built from untrusted input; no official statement found | "Does any part of a `bean:` or `class:` URI come from user input?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Leave a name-referenced bean without `@RegisterForReflection` for native; the 3.40.0 processor registers only `@Handler` classes ([source](https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/extensions/bean/deployment/src/main/java/org/apache/camel/quarkus/component/bean/deployment/BeanProcessor.java)) | Add `@RegisterForReflection` ([CDI guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html)) |
| Use `from("bean:...")`; the Bean component is producer-only ([source](https://camel.apache.org/components/4.22.x/bean-component.html)) | Call the bean with `.to("bean:myBean")` from another endpoint, or put `@Consume` on a bean method ([CDI guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html)) |
| Keep mutable fields in a default-scope (`Singleton`) bean; calls share one instance ([source](https://camel.apache.org/components/4.22.x/bean-component.html)) | Do not keep per-call state in bean fields: write a stateless bean |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| `scope` default | `Singleton` (also `Request`, `Prototype`) | https://camel.apache.org/components/4.22.x/bean-component.html |
| `lazyStartProducer` default | `false` | https://camel.apache.org/components/4.22.x/bean-component.html |
| `beanInfoCacheSize` default | `1000`; caches introspection, not instances; `0` or negative disables | https://camel.apache.org/components/4.22.x/bean-component.html |
| Direction | producer-only | https://camel.apache.org/components/4.22.x/bean-component.html |
| `quarkus.arc.remove-unused-beans` (medium confidence) | `all` default (also `fwk`, `none`) | https://quarkus.io/version/3.40/guides/cdi-reference |
| `@Consume` on a bean method | creates a route; CQ adds `@Singleton` + `@Named` unless scope/name present | https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html |
| `@Handler` classes | auto-registered for reflection in 3.40.0 | https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/extensions/bean/deployment/src/main/java/org/apache/camel/quarkus/component/bean/deployment/BeanProcessor.java |
| Registry order (medium confidence) | ArC first, then `SimpleRegistry` | https://camel.apache.org/manual/registry.html |
| Unannotated body binding (medium confidence) | first parameter that is not `Exchange`, `Message`, `CamelContext`, `TypeConverter`, `Registry` or `Exception` | https://camel.apache.org/manual/parameter-binding-annotations.html |
| `@InjectMock` dependency (medium confidence) | `io.quarkus:quarkus-junit-mockito`, test scope | https://quarkus.io/guides/getting-started-testing |
| Test artifact | `camel-quarkus-junit` (renamed from `camel-quarkus-junit5` since 3.31; Camel test details: skill `developing-camel-quarkus-junit-v3-40`) | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html |
| Representative commands | `mvn test`, `mvn verify -Dnative` | page not recorded |

## External Resources

All fetched 2026-10-14. camel.apache.org pages carry no page date and are the current stable 3.40.x / 4.22.x docs.

- Bean extension: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html
- CDI guide: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html
- Native mode: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html
- Bean component (4.22.x): https://camel.apache.org/components/4.22.x/bean-component.html
- Quarkus CDI reference: https://quarkus.io/version/3.40/guides/cdi-reference
- Quarkus testing guide: https://quarkus.io/guides/getting-started-testing
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
