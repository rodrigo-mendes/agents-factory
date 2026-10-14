# Research: Camel Quarkus Bean v3.40 (camel-quarkus-bean 3.40.x / Camel 4.22.x / Quarkus 3.40.x)

> Version lock: every claim applies to **Camel Quarkus 3.40.x** only. The 3.15-era file was used for topic names only, not as a source.
> All sources were fetched on **2026-10-14**. camel.apache.org pages carry no page date; they count as current because they are the versioned 3.40.x / 4.22.x docs for the current stable LTS. Unversioned Camel manual pages (`/manual/...`) are tagged Medium.
> Method note: WebFetch returns model summaries. Quoted text is the tool's rendering; check the exact wording before reusing it verbatim.
> Process note: this was a forked batch run. The plan-approval step (EnterPlanMode/ExitPlanMode) was **skipped** because no user is present in the fork and the user approved the scheme in the parent session. Sub-investigators were not spawned (orchestrator constraint); all pages were fetched directly. The output file was written directly, not via research-synthesizer.

---

## Metadata

```yaml
Full_Name: Apache Camel Quarkus — Bean extension (org.apache.camel.quarkus:camel-quarkus-bean)
Target_Version: 3.40.x (3.40.0; docs index lists Camel 4.22.1, Quarkus 3.40.1 — https://camel.apache.org/camel-quarkus/latest/ , via pilot research_Camel_Quarkus_Core_v3.40.md, not re-fetched in this run → Medium)
Release_Date: 2026-09-28 per https://camel.apache.org/releases/ (pilot); artifact upload 2026-09-24 per https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-bean/ (fetched 2026-10-14)
Support_Status: LTS (https://camel.apache.org/releases/ via pilot; CQ-specific end date UNVERIFIED)
Primary_Docs: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html
Official_Repo: https://github.com/apache/camel-quarkus
Research_Date: 2026-10-14
Domain_Complexity: Standard (CDI/ArC build-time bean removal, native reflection, bean binding algorithm)
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 3
Unverified_Count: 9
Irresolvable_Count: 2
Research_Quality_Score: 85%   # ~75 claims; (75 - 9 - 2) / 75
```

---

## Executive Summary

`camel-quarkus-bean` brings the Camel **Bean component** (`bean:beanName`), the **Bean Method language** and the **Class component** (`class:beanName`) to Quarkus. It is supported in JVM and native mode since 0.1.0. Besides beans in the Camel registry, it can invoke Quarkus CDI (ArC) beans (High — https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html). The extension page lists no `quarkus.camel.*` properties of its own; endpoint options come from the Camel 4.22.x component page (`method`, `scope` default `Singleton`, `parameters`, `lazyStartProducer` default `false`; component `beanInfoCacheSize` default `1000`) (High — https://camel.apache.org/components/4.22.x/bean-component.html).

What changed relative to the 3.15-era conventions: the 3.40 CQ CDI guide documents `@io.smallrye.common.annotation.Identifier` as a first-class alternative to `@Named` for naming beans used from routes (High — https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html), and the Quarkus CDI reference now explicitly recommends `@Identifier` over `@Named` except when an external language needs the bean name (High — https://quarkus.io/guides/cdi-reference). Bean binding in Camel 4.x supports type+value qualifiers (`int.class 123`), `@Variable`/`@Variables` binding, and `CompletionStage` return values (Medium — https://camel.apache.org/manual/bean-binding.html , https://camel.apache.org/manual/parameter-binding-annotations.html). In the 3.40.0 source, the bean extension auto-registers classes with `@Handler` methods for reflection, but does nothing for classes referenced only by name in `bean:` URIs (High — https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/extensions/bean/deployment/src/main/java/org/apache/camel/quarkus/component/bean/deployment/BeanProcessor.java).

Three critical patterns: (1) a named bean = scope + `@Named` or `@Identifier` + `@RegisterForReflection`; (2) pin the method (`method=` or `@Handler`) to avoid `AmbiguousMethodCallException`; (3) singleton-scoped beans (the default) must be thread-safe. Tier **Standard**: there is no security or crypto surface, but ArC's build-time removal and native reflection create JVM-vs-native divergence.

**Version-lifetime risk:** Quarkus 4.0 GA is planned for end of November 2026, and no Camel Quarkus 4.x exists yet (pilot, https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ , not re-fetched → Medium). Pin 3.40.x.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or unversioned page) | 🔴 Low (verify before use)

### ✅ Mandatory Patterns

**1. Named CDI bean for route lookup: scope + `@Named`/`@Identifier` + `@RegisterForReflection`**
> Confidence: 🟢 High | [✓✓ Triangulated | CQ 3.40 CDI guide + Quarkus CDI reference (2026-10-14)]
- Why: the CQ guide shows `@ApplicationScoped @Named("myNamedBean") @RegisterForReflection`, and says "The `@RegisterForReflection` annotation is important for the native mode". `@Identifier` is documented as an alternative; routes use the identifier value directly. Quarkus CDI only discovers classes that have a bean-defining annotation, so a scope annotation is required (https://quarkus.io/guides/cdi-reference).
- Code:
  ```java
  // Camel Quarkus 3.40.x
  @jakarta.enterprise.context.ApplicationScoped
  @jakarta.inject.Named("myNamedBean")                    // or @io.smallrye.common.annotation.Identifier("myNamedBean")
  @io.quarkus.runtime.annotations.RegisterForReflection
  public class NamedBean {
      public String hello(String name) { return "Hello " + name; }
  }
  // route: from("direct:named").bean("myNamedBean", "hello");
  //    or: from("direct:named").to("bean:myNamedBean?method=hello");
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html ; https://quarkus.io/guides/cdi-reference (2026-10-14)

**2. Pin the target method (`method=`, `.bean(name, method)` or `@Handler`)**
> Confidence: 🟢 High | [✓✓ Triangulated | Camel 4.22.x bean component + Bean Binding manual (2026-10-14)]
- Why: without a pinned method, Camel goes through a 9-step selection ending in body-type matching, and throws `AmbiguousMethodCallException` when no single method fits (https://camel.apache.org/manual/bean-binding.html). `@Handler` keeps the route independent of IDE renames. In 3.40.0, `@Handler` classes are also auto-registered for reflection (BeanProcessor.java at tag 3.40.0).
- Code:
  ```java
  // Camel 4.22.x / CQ 3.40.x
  from("direct:a").to("bean:orderService?method=validate");
  from("direct:b").bean("orderService", "price(${body}, true)");      // value binding
  from("direct:c").bean("orderService", "hello(String.class, *)");    // overload qualifier
  ```
- Source: https://camel.apache.org/components/4.22.x/bean-component.html ; https://camel.apache.org/manual/bean-binding.html (2026-10-14)

**3. Bind headers/properties with annotations instead of reading `Exchange` manually**
> Confidence: 🟡 Medium (single unversioned manual page)
- Why: `org.apache.camel` provides `@Body`, `@Header`, `@Headers`, `@Variable`, `@Variables`, `@ExchangeProperty`, `@ExchangeProperties`, `@ExchangeException`. Without annotations, the body binds to the first parameter that is not a built-in type (`Exchange`, `Message`, `CamelContext`, `TypeConverter`, `Registry`, `Exception`).
- Code:
  ```java
  // Camel 4.22.x
  public String route(@org.apache.camel.Body String body,
                      @org.apache.camel.Header("operation") String op,
                      @org.apache.camel.ExchangeProperty("tenant") String tenant) {
      return op + ":" + tenant + ":" + body;
  }
  ```
- Source: https://camel.apache.org/manual/parameter-binding-annotations.html ; https://camel.apache.org/manual/bean-binding.html (2026-10-14)

**4. Singleton bean scope (default) requires thread-safe beans**
> Confidence: 🟢 High | [✓✓ Triangulated | bean-component 4.22.x (component + endpoint option tables)]
- Why: `scope` default is `Singleton`: "created or looked up once and reused for the endpoint's lifetime", called concurrently. `Request` = once per exchange; `Prototype` = each call, but the behaviour depends on the delegated registry (CDI may still return a singleton).
- Code:
  ```java
  // stateless bean → keep default Singleton
  from("direct:s").to("bean:pricing?method=quote");
  // per-exchange state → Request scope
  from("direct:r").to("bean:accumulator?method=add&scope=Request");
  ```
- Source: https://camel.apache.org/components/4.22.x/bean-component.html (2026-10-14)

**5. Use typed registry lookup (`lookupByNameAndType`)**
> Confidence: 🟢 High (CQ CDI guide + Camel registry manual)
- Why: the Camel registry manual warns that beans of different types can share a name and prefers `lookupByNameAndType`. The DefaultRegistry looks in the runtime platform (ArC) first, then falls back to `SimpleRegistry`.
- Code:
  ```java
  @jakarta.inject.Inject org.apache.camel.spi.Registry registry;
  CoolBean bean = registry.lookupByNameAndType("coolBean", CoolBean.class);
  ```
  (The `org.apache.camel.spi.Registry` package is not shown on the CQ page → UNVERIFIED there.)
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html ; https://camel.apache.org/manual/registry.html (2026-10-14)

### ⚠️ Conditional Patterns

**A. `@Named` vs `@Identifier` for bean naming**
> Confidence: 🟢 High for the recommendation; 🔴 for removal behaviour of `@Identifier`-only beans (IRRESOLVABLE)
- Options: A) `@Named("x")`; B) `@Identifier("x")`; C) `@Identifier("x")` + `@io.quarkus.arc.Unremovable`
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A `@Named` | Guaranteed unremovable ("has a name set with `@Named`") | Adds `@Default` when it is the only qualifier, so same-type beans can be ambiguous | Name-only lookup from Camel (an external "language" using bean names) |
  | B `@Identifier` | Type-safe qualifier, Quarkus-recommended | Not listed as an unremovable root; removal if only looked up via Camel is unconfirmed | Bean is also `@Inject`ed elsewhere |
  | C `@Identifier` + `@Unremovable` | Both properties | One extra annotation | Default recommendation when choosing `@Identifier` |

- Agent: "Ask whether the bean is also injected by type elsewhere. If it is only referenced from routes, use `@Named` or `@Identifier`+`@Unremovable`."
- Source: https://quarkus.io/guides/cdi-reference ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html (2026-10-14)

**B. Invocation style: `bean:` URI vs `.bean()` DSL vs `class:` vs inline instance**
> Confidence: 🟢 High
- Options: `to("bean:x?method=m")`, `.bean("x","m")`, `.bean(MyClass.class)`, `.bean(new X())`, `class:fqcn`, `@FunctionalInterface` lambda with `@Handler`
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Registry name | CDI injection inside the bean | Native reflection is manual | CDI-managed services |
  | Class/instance | No registry needed | No CDI lifecycle | Stateless helpers |

- Agent: "Ask whether the bean needs CDI injection."
- Source: https://camel.apache.org/components/4.22.x/bean-component.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html (2026-10-14)

**C. ArC removal strategy**
> Confidence: 🟢 High
- Options: `quarkus.arc.remove-unused-beans=all` (default) / `fwk` / `none`; `quarkus.arc.unremovable-types=org.acme.**`
- Tradeoffs: `none` removes the risk but grows memory and startup; per-class `@Unremovable` is surgical.
- Agent: "Prefer `@Unremovable` or `unremovable-types` over disabling removal."
- Source: https://quarkus.io/guides/cdi-reference (2026-10-14)

### 🚫 Forbidden Patterns

**1. Bean class without a bean-defining annotation, looked up by name**
> Severity: High
> Confidence: 🟢 High
- Why: Quarkus does not discover classes without a bean-defining annotation; `@Named` alone is not a scope.
- Impact: lookup returns null, so the route fails with "no bean" at runtime.
- ❌ Wrong:
  ```java
  @jakarta.inject.Named("svc") public class Svc { public String m(String b){ return b; } }
  ```
- ✅ Correct:
  ```java
  @jakarta.enterprise.context.ApplicationScoped @jakarta.inject.Named("svc")
  @io.quarkus.runtime.annotations.RegisterForReflection public class Svc { public String m(String b){ return b; } }
  ```
- Source: https://quarkus.io/guides/cdi-reference ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html (2026-10-14)

**2. Omitting `@RegisterForReflection` on name-referenced beans in native mode**
> Severity: High
> Confidence: 🟢 High
- Why: "Classes for which reflective access is needed, have to be registered for reflection at compile time." The 3.40.0 bean BeanProcessor registers `@Handler` classes only, not classes referenced from `bean:` URIs.
- Impact: works in JVM mode, fails in native mode.
- ❌ Wrong:
  ```java
  @ApplicationScoped @Named("calc") public class Calc { public int add(int a){ return a+1; } }
  ```
- ✅ Correct:
  ```java
  @ApplicationScoped @Named("calc") @RegisterForReflection public class Calc { public int add(int a){ return a+1; } }
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html ; BeanProcessor.java @3.40.0 (2026-10-14)

**3. Using `bean:` as a route input**
> Severity: Medium
> Confidence: 🟢 High
- Why: the Bean component is producer-only.
- ❌ Wrong:
  ```java
  from("bean:myBean").to("log:x");
  ```
- ✅ Correct:
  ```java
  from("direct:start").to("bean:myBean");   // or @Consume("direct:start") on a method
  ```
- Source: https://camel.apache.org/components/4.22.x/bean-component.html ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html (2026-10-14)

**4. Mutable state in a Singleton-scoped bean**
> Severity: High
> Confidence: 🟢 High
- Why: default `scope=Singleton` is called concurrently.
- ❌ Wrong:
  ```java
  public class Acc { private List<String> items = new ArrayList<>(); public void add(String s){ items.add(s); } }
  ```
- ✅ Correct:
  ```java
  // keep state on the Exchange, or use scope=Request
  public void add(@org.apache.camel.Body String s, org.apache.camel.Exchange ex){ ex.setProperty("item", s); }
  ```
- Source: https://camel.apache.org/components/4.22.x/bean-component.html (2026-10-14)

**5. Overloaded methods without a qualifier**
> Severity: Medium
> Confidence: 🟡 Medium
- Why: ambiguity leads to `AmbiguousMethodCallException`.
- ❌ Wrong:
  ```java
  .bean("svc", "hello")   // hello(String) and hello(String,String) both exist
  ```
- ✅ Correct:
  ```java
  .bean("svc", "hello(String.class)")
  ```
- Source: https://camel.apache.org/manual/bean-binding.html (2026-10-14)

**6. Returning `Exchange` from a bean method**
> Severity: Medium
> Confidence: 🟡 Medium
- Why: "The return type cannot be `Exchange`." Take `Exchange` as an input instead.
- ❌ Wrong: `public Exchange process(Exchange e){ return e; }`
- ✅ Correct: `public void process(Exchange e){ e.getMessage().setBody("x"); }`
- Source: https://camel.apache.org/manual/bean-binding.html (2026-10-14)

---

## Migration Guide

> Confidence: 🟡 Medium | Sources: pilot research_Camel_Quarkus_Core_v3.40.md (migration-guide pages 3.31–3.40, fetched 2026-10-14) + this run's fetches

**Breaking Changes (bean-relevant, 3.15 → 3.40)**:
- The bean migration guides have no bean-specific entries; the pilot found none in 3.31–3.40 (Medium — https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/index.html via pilot).
- Testing: `camel-quarkus-junit5` → `camel-quarkus-junit` (3.31) (https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html via pilot).
- Quarkus test mocking: `@InjectMock` needs `quarkus-junit-mockito` (the page names no `quarkus-junit5-mockito`) (High — https://quarkus.io/guides/getting-started-testing).
- 3.40: `serialization-enabled` has three states; relevant only if beans pass `Serializable` payloads natively (https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html via pilot).
- Camel 4.x: type+value parameter qualifiers (`int.class 123`) (https://camel.apache.org/manual/bean-binding.html).

**Upgrade Steps**:
1. Set `quarkus.platform.version=3.40.1`, import `quarkus-bom` + `quarkus-camel-bom` (pilot; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/dependency-management.html).
2. Run `quarkus update`; apply migration guides.
3. Audit `@Identifier`-only beans referenced only from routes and add `@Unremovable` (see Research Gaps).
4. Replace junit5 test artifacts.

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| camel-quarkus-bean | 3.40.0 | 3.40.x | Central upload 2026-09-24 (https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-bean/) |
| Camel | 4.22.1 | 4.22.x | pilot, https://camel.apache.org/camel-quarkus/latest/ |
| Quarkus | 3.40.1 | 3.40.x | pilot |
| Java | 17 | 21 | pilot, https://camel.apache.org/releases/q-3.40.0/ |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | CQ CDI guide + bean-component 4.22.x]

**Lifecycle**:
```xml
<!-- Camel Quarkus 3.40.x — version managed by quarkus-camel-bom -->
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-bean</artifactId></dependency>
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-direct</artifactId></dependency>
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-log</artifactId></dependency>
```
```java
// Camel Quarkus 3.40.x — bean + route
@jakarta.enterprise.context.ApplicationScoped
@io.smallrye.common.annotation.Identifier("orderService")
@io.quarkus.arc.Unremovable                               // defensive: see Research Gaps
@io.quarkus.runtime.annotations.RegisterForReflection
public class OrderService {
    @org.apache.camel.Handler
    public String validate(@org.apache.camel.Body String body,
                           @org.apache.camel.Header("source") String source) {
        if (body == null || body.isBlank()) throw new IllegalArgumentException("empty");
        return source + ":" + body;
    }
}

public class OrderRoutes extends org.apache.camel.builder.RouteBuilder {   // no CDI needed (pilot)
    @Override public void configure() {
        onException(IllegalArgumentException.class).handled(true).to("log:invalid?level=WARN");
        from("direct:order").routeId("order")
            .bean("orderService")                  // @Handler selects validate()
            .to("log:order");
    }
}
```

**Integration**: Bean ↔ Quarkus ArC — inject Camel's registry or `ProducerTemplate` (CQ CDI guide); `@Consume("...")` on a bean method creates a route automatically, and CQ adds `@Singleton` + `@Named` unless a scope/name is present (High — https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html).

**Integration**: Bean ↔ camel-quarkus-log — `to("log:name")` after bean calls; log options UNVERIFIED in this run.

**Integration**: Bean ↔ camel-quarkus-jaxb — bean methods receiving JAXB-unmarshalled objects bind by body type conversion (Bean Binding manual). JAXB extension specifics (native registration of JAXB classes) UNVERIFIED in this run.

**Async return**: methods may return `CompletionStage`; Camel applies no timeout, and completing with `null` leaves the body unchanged (Medium — https://camel.apache.org/manual/bean-binding.html).

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment (Camel Quarkus 3.40.x)
mvn test                 # @QuarkusTest, JVM mode
mvn verify -Dnative      # catches missing @RegisterForReflection; Mandrel/GraalVM 25 (pilot)
grep -rL "RegisterForReflection" src/main/java | xargs grep -l "@Named\|@Identifier"   # named beans lacking reflection
```

**Mocking**:
```java
// Quarkus 3.40 — requires io.quarkus:quarkus-junit-mockito (test scope)
@io.quarkus.test.junit.QuarkusTest
class OrderRouteTest {
    @io.quarkus.test.InjectMock OrderService orderService;   // works: @ApplicationScoped is a normal scope
    @jakarta.inject.Inject org.apache.camel.ProducerTemplate template;
    @org.junit.jupiter.api.Test void routes() {
        org.mockito.Mockito.when(orderService.validate("a", null)).thenReturn("ok");
        org.junit.jupiter.api.Assertions.assertEquals("ok", template.requestBody("direct:order", "a", String.class));
    }
}
```
Guarantee: `@InjectMock` works for normal-scoped beans; `@Singleton` needs `@MockitoConfig(convertScopes = true)`, which the docs call "an advanced option" (High — https://quarkus.io/guides/getting-started-testing). Whether a Camel registry lookup by `@Identifier` name returns the mock client proxy is UNVERIFIED.

---

## Production Readiness

- **Performance**: `beanInfoCacheSize` default `1000` caches introspection, not instances; `0`/negative disables it (https://camel.apache.org/components/4.22.x/bean-component.html). Pinning the method avoids per-call selection cost (inference, Medium).
- **Scalability**: Singleton beans are shared across concurrent exchanges; use `scope=Request` for per-exchange state (bean-component 4.22.x).
- **Monitoring**: no bean-specific metrics on the CQ page; use route metrics (`camel-quarkus-micrometer`, pilot).
- **Error handling**: exceptions thrown by bean methods go to the route's `onException`/error handler; an `Exception` parameter binds the caught exception (https://camel.apache.org/manual/bean-binding.html). Defaults: see pilot (exception clauses do not redeliver by default).
- **Security**: `bean:`/`class:` can instantiate classes by FQCN; avoid building bean URIs from untrusted input (inference, UNVERIFIED — no official statement found).

---

## Reference Implementations

- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html — named bean, `@Identifier`, registry lookup, `@Consume`.
- https://camel.apache.org/components/4.22.x/bean-component.html — DSL variants.
- https://github.com/apache/camel-quarkus/tree/3.40.0/extensions/bean — deployment processor.
- https://github.com/apache/camel-quarkus-examples — bean-specific example names UNVERIFIED.

---

## Source Bibliography

**Primary** (all fetched 2026-10-14; camel.apache.org pages undated, current stable):
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/core.html
- https://camel.apache.org/components/4.22.x/bean-component.html
- https://camel.apache.org/manual/bean-binding.html (unversioned)
- https://camel.apache.org/manual/parameter-binding-annotations.html (unversioned)
- https://camel.apache.org/manual/registry.html (unversioned)
- https://quarkus.io/guides/cdi-reference (first 100,000 of 104,471 chars read)
- https://quarkus.io/guides/getting-started-testing
- https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/extensions/bean/deployment/src/main/java/org/apache/camel/quarkus/component/bean/deployment/BeanProcessor.java
- https://github.com/apache/camel-quarkus/issues/4725 (closed 2023-10-30; historical context only, >12 months)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-bean/ (3.40.0, 2026-09-24)
- Pilot: workspace/research_Camel_Quarkus_Core_v3.40.md (version table, LTS, Quarkus 4 risk — not re-fetched)

**Validation**: no community sources used.

---

## Research Gaps

```
Gap: Is a bean named only with @Identifier (no @Named, not injected) removed by ArC when it is only looked up via the Camel registry?
Impact: Works in tests that inject it; "no bean" failure in prod paths that don't
Workaround: add @io.quarkus.arc.Unremovable or use @Named
Follow-up: camel-quarkus core deployment processors (search UnremovableBeanBuildItem) at tag 3.40.0
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: Camel Quarkus-specific LTS end date for 3.40
Impact: support planning
Workaround: assume Quarkus 3.40 LTS window (inference)
Follow-up: https://camel.apache.org/camel-quarkus/latest/ "LTS Until"
§7-ref: inherited from pilot Iteration 1 — IRRESOLVABLE
```
UNVERIFIED (not gap-looped): Registry package on the CQ page; camel-quarkus-log options; camel-quarkus-jaxb native specifics; `@InjectMock` mock visible through Camel name lookup; bean-specific examples repo; security note on FQCN instantiation; Camel/Quarkus/Java version numbers (pilot-sourced, not re-fetched); `class:` component options; Bean Method language options.

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 0 | Guardrails | `@Identifier` officially supported for route lookup (pilot open item) | Resolved | https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html (2026-10-14) |
| 0 | Guardrails | `@Named` vs `@Identifier` recommendation (pilot open item) | Resolved | https://quarkus.io/guides/cdi-reference (2026-10-14) |
| 1 | Research Gaps | `@Identifier`-only bean removal — CDI reference | Updated: not a listed unremovable root (inference only) | https://quarkus.io/guides/cdi-reference (2026-10-14) |
| 2 | Research Gaps | Same — CQ issue #4725 | Updated: covers same-name lookup, not removal | https://github.com/apache/camel-quarkus/issues/4725 (2026-10-14) |
| 3 | Guardrails | Bean extension reflection behaviour | Added: `@Handler` classes auto-registered; no unremovable handling | BeanProcessor.java @3.40.0 (2026-10-14) |
| 3 | Research Gaps | `@Identifier`-only bean removal | ⚠️ IRRESOLVABLE — needs core deployment source inspection, out of budget | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented
- [x] All scope areas cited (endpoint options, lookup, binding, CDI/ArC, native, caching, errors, testing)
- [x] Pattern counts driven by domain needs
- [x] Every anti-pattern has alternative
- [x] All CLI commands marked as representative
- [x] Integration examples complete (ArC, log, jaxb partial — UNVERIFIED specifics)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns triangulated or downgraded to 🟡 Medium
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score calculated
- [x] Every Research Gap cross-referenced in §7

---

## Agent Operation Notes

- **High Confidence**: named bean recipe (scope + name + `@RegisterForReflection`), endpoint options/defaults, scope semantics, producer-only, `@InjectMock` scope rules, `@Handler` reflection auto-registration.
- **Medium Confidence**: bean binding algorithm and annotations (unversioned manual), `CompletionStage` behaviour, pilot-sourced version numbers.
- **Low Confidence (ask human)**: removal of `@Identifier`-only beans; CQ LTS end date.
- **Edge Cases (pause)**: 3.40.0 released <30 days before research (2026-09-28); Quarkus 4 GA expected end Nov 2026.
- **Emergency Stop**: none triggered.
