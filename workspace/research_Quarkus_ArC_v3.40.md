# Research: Quarkus ArC (quarkus-arc, Quarkus CDI container), version 3.40

> Target version: Quarkus 3.40.x LTS (Camel Quarkus 3.40.x builds on Quarkus 3.40.1). Every claim below is for Quarkus 3.40 only. Patterns from other Quarkus versions do not apply here.
> Plan-approval note: this is a forked batch run. The user approved the scheme in the parent session and nobody can approve a plan inside this fork, so P3 (EnterPlanMode/ExitPlanMode) was skipped. Per the caller's constraint, no section-investigators were spawned. All pages were fetched directly on 2026-10-14.

## Metadata

```yaml
Full_Name: Quarkus ArC (io.quarkus:quarkus-arc), the build-time CDI container of Quarkus
Target_Version: "3.40 (3.40.x LTS; 3.40.1 used by Camel Quarkus 3.40.x)"
Release_Date: "2026-09-30 (Quarkus 3.40 LTS) — source https://quarkus.io/releases (via _family_facts_v3.40.md, High)"
Support_Status: "LTS, community-maintained until 2027-09-30 — source https://quarkus.io/releases (family facts, High)"
CDI_Spec: "Jakarta CDI 4.1, CDI Lite (not CDI Full) — source https://quarkus.io/version/3.40/guides/cdi-reference"
Primary_Docs: https://quarkus.io/version/3.40/guides/cdi-reference
Official_Repo: https://github.com/quarkusio/quarkus
Research_Date: 2026-10-14
Domain_Complexity: Standard
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 5
Unverified_Count: 4          # U1-U4 in Research Gaps (includes the 2 IRRESOLVABLE)
Irresolvable_Count: 2        # U1, U2
Research_Quality_Score: 93%  # (≈60 claims - 4 unverified) / 60
```

---

## Executive Summary

ArC is the dependency-injection container in Quarkus 3.40. Its CDI spec is **Jakarta CDI 4.1**. It implements **CDI Lite** with some improvements, passes the CDI Lite TCK, and **does not implement CDI Full** (High, https://quarkus.io/version/3.40/guides/cdi-reference). Most of the work happens at build time. Bean discovery uses a single bean archive in *annotated* mode, built from a Jandex index. ArC then resolves injection points and **removes unused beans by default** (`quarkus.arc.remove-unused-beans=all`, High, https://quarkus.io/version/3.40/guides/cdi-reference). Classes without a bean-defining annotation are not beans. One exception: a class that declares producers or observers becomes an implicit `@Dependent` bean.

Quarkus 3.40 brings no ArC migration work. The official 3.40 migration guide says "Quarkus 3.40 LTS is the direct continuation of 3.39 so we don't expect any changes requiring manual intervention in 3.40" (High for 3.39→3.40 only, https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40). Compared with older (3.15-era) conventions, the 3.40 docs differ in these places:
- They recommend `@io.smallrye.common.annotation.Identifier` instead of `@Named` (High).
- The test artifacts are `quarkus-junit` and `quarkus-junit-mockito`. The 3.40 testing guide does not mention `quarkus-junit5*` (High, https://quarkus.io/version/3.40/guides/getting-started-testing).
- Camel Quarkus 3.40 documents both `@Named` and `@Identifier` lookups from routes (High, https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html).

Three patterns matter most:
1. Use a bean-defining scope annotation (prefer `@ApplicationScoped`), and inject into package-private members rather than private ones.
2. Every bean that is reached only by name or by programmatic lookup (Camel registry, `CDI.current()`) must be unremovable. Use `@Named`, `@Unremovable` or `quarkus.arc.unremovable-types`. Whether an `@Identifier`-only bean survives removal is **not documented** (IRRESOLVABLE U1), so add `@Unremovable` to be safe.
3. `@InjectMock` works only on normal-scoped beans.

Tier **Standard**: there are several integrations (Camel, REST, Config, JUnit), but no security-critical surface of its own.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)
> All quarkus.io/version/3.40 pages were fetched on 2026-10-14. They document the current stable LTS.

### ✅ Mandatory Patterns

**1. Declare beans with a bean-defining annotation; prefer `@ApplicationScoped`**
> Confidence: 🟢 High | [✓✓ Triangulated | cdi (2026-10-14) + cdi-reference (2026-10-14)]
- Why: discovery runs in annotated mode, so classes without a bean-defining annotation are not discovered. Producers and observers are the exception: their declaring class is treated as `@Dependent` (cdi-reference). The CDI guide recommends `@ApplicationScoped` by default. `@Singleton` is slightly faster but has no client proxy and cannot be mocked with QuarkusMock (cdi).
- Code (Quarkus 3.40):
  ```java
  @ApplicationScoped            // normal scope: lazy client proxy, mockable
  public class GreetingService {
      String greet(String n) { return "Hello " + n; }
  }
  ```
- Source: https://quarkus.io/version/3.40/guides/cdi ; https://quarkus.io/version/3.40/guides/cdi-reference (2026-10-14)

**2. Keep name-looked-up / programmatically-looked-up beans unremovable**
> Confidence: 🟢 High | [✓✓ Triangulated | cdi-reference + cdi-integration (2026-10-14)]
- Why: the default is `quarkus.arc.remove-unused-beans=all`. These beans count as unremovable: beans annotated `@io.quarkus.arc.Unremovable`, types listed in `quarkus.arc.unremovable-types`, beans covered by an `UnremovableBeanBuildItem`, beans named with `@Named`, and beans that declare an observer method. ArC cannot detect lookups through `CDI.current()`, so beans used only that way may be removed by mistake (cdi-reference, cdi-integration).
- Code:
  ```java
  @ApplicationScoped
  @Unremovable                       // io.quarkus.arc.Unremovable
  @Identifier("orderMapper")         // io.smallrye.common.annotation.Identifier
  public class OrderMapper { ... }   // looked up only from a Camel route by name
  ```
- Source: https://quarkus.io/version/3.40/guides/cdi-reference ; https://quarkus.io/version/3.40/guides/cdi-integration (2026-10-14)

**3. Prefer `@Identifier` over `@Named` for qualification**
> Confidence: 🟢 High | [✓✓ Triangulated | cdi-reference + Camel Quarkus cdi.html (2026-10-14)]
- Why: `@Named` is string-based. When it is the only qualifier, the bean also gets `@Default`, which can cause ambiguity with other beans of the same type. Keep `@Named` only where an external language (for example Qute) needs the name (cdi-reference). Camel Quarkus 3.40 resolves `.bean("myBeanIdentifier", ...)` against `@Identifier("myBeanIdentifier")` (Camel cdi.html).
- Code:
  ```java
  @ApplicationScoped @Identifier("primary") class PrimaryClient implements Client {}
  // injection
  @Inject @Identifier("primary") Client client;
  ```
- Source: https://quarkus.io/version/3.40/guides/cdi-reference ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html (2026-10-14)

**4. Do not use private injection members (native-friendly)**
> Confidence: 🟡 Medium (single source: cdi-reference)
- Why: Quarkus DI reaches private members through reflection, which has to be registered for GraalVM and makes the native executable bigger. Make injection fields, constructors, initializers, observers, producers, disposers and interceptor methods package-private. `quarkus.arc.transform-private-injected-fields` defaults to `true` (https://quarkus.io/version/3.40/guides/cdi-reference).
- Code:
  ```java
  @ApplicationScoped
  public class Svc { @Inject Repo repo; }   // package-private, not private
  ```
- Source: https://quarkus.io/version/3.40/guides/cdi-reference (2026-10-14)

**5. Eager startup via `@Startup` or a `StartupEvent` observer**
> Confidence: 🟡 Medium (single source: cdi-reference)
- Why: normal-scoped beans are created on the first method call on their client proxy. Being injected does not create them. To create a bean at startup, use `@io.quarkus.runtime.Startup` or `void onStart(@Observes StartupEvent ev)`. The docs recommend `StartupEvent` over `@Initialized(ApplicationScoped.class)`.
- Code:
  ```java
  @ApplicationScoped
  class Warmup { void onStart(@Observes StartupEvent ev) { /* init */ } }
  ```
- Source: https://quarkus.io/version/3.40/guides/cdi-reference (2026-10-14)

**6. `@ApplicationScoped` on a Camel `RouteBuilder` only when it uses `@Inject` / `@ConfigProperty`**
> Confidence: 🟢 High (family fact, verbatim)
- Why: the scope is "required for @Inject and @ConfigProperty"; otherwise it adds a boot-time penalty.
- Code:
  ```java
  @ApplicationScoped
  public class Routes extends RouteBuilder {
      @ConfigProperty(name = "timer.period", defaultValue = "1000") String period;
      @Override public void configure() { fromF("timer:foo?period=%s", period).bean("myBeanIdentifier", "Camel"); }
  }
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html (2026-10-14)

**7. Index external bean archives (Jandex) so their beans are discovered**
> Confidence: 🟢 High | [✓✓ Triangulated | cdi-reference + cdi-integration]
- Why: dependencies are scanned only if they have `beans.xml`, a `META-INF/jandex.idx`, or a `quarkus.index-dependency.<name>.group-id/artifact-id` entry. Otherwise their classes are "not discovered". The documented plugin versions are jandex-maven-plugin 3.6.0 and Gradle Jandex plugin 2.3.0 (https://quarkus.io/version/3.40/guides/cdi-reference).
- Code:
  ```properties
  quarkus.index-dependency.mylib.group-id=com.acme
  quarkus.index-dependency.mylib.artifact-id=acme-model
  ```
- Source: https://quarkus.io/version/3.40/guides/cdi-reference ; https://quarkus.io/version/3.40/guides/cdi-integration (2026-10-14)

### ⚠️ Conditional Patterns

**A. Scope selection: `@ApplicationScoped` vs `@Singleton` vs `@Dependent` vs `@RequestScoped`**
> Confidence: 🟢 High
- Options: see table.

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | `@ApplicationScoped` | lazy init, mockable, circular deps | proxy indirection; never access fields directly (stale data) | default |
  | `@Singleton` | slightly better performance; fields can be accessed safely | no proxy; not `@InjectMock`-able without `@MockitoConfig(convertScopes = true)` | hot paths, never mocked |
  | `@Dependent` | per-injection-point instance | bound to the owner's lifecycle; not mockable | stateful helpers |
  | `@RequestScoped` | per-request state | needs an active request context (in Camel `bean`/`process` calls, use `@ActivateRequestContext`) | request data |

- Agent: "Ask whether the bean must be mocked in tests, and whether it is used from Camel processors (request context)."
- Source: https://quarkus.io/version/3.40/guides/cdi ; https://quarkus.io/version/3.40/guides/getting-started-testing ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html (2026-10-14)

**B. Unused-bean removal mode**
> Confidence: 🟢 High
- Options: `all` (default), `none`/`false`, `fwk`/`framework` (keeps every application bean, still optimizes framework beans).

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | `all` | boot time, memory | name/programmatic lookups need `@Unremovable` | default |
  | `fwk` | safety for app beans looked up dynamically | slightly larger app | heavy Camel name lookup of `@Identifier` beans |
  | `none` | closest to the spec | gives up the dead-code elimination | debugging only |

- Agent: "Ask whether application beans are reached only through string names or `CDI.current()`."
- Source: https://quarkus.io/version/3.40/guides/cdi-reference (2026-10-14)

**C. Build-time bean enablement: `@DefaultBean`, `@IfBuildProfile`/`@UnlessBuildProfile`, `@IfBuildProperty`/`@UnlessBuildProperty`, `@LookupIfProperty`**
> Confidence: 🟢 High (single page, but versioned and fully read in that section)
- Facts:
  - `@DefaultBean` is used only if no other bean with the same types and qualifiers exists. It supports `@Priority`, which defaults to 0.
  - The build-profile and build-property annotations are evaluated **at build time**, so runtime profiles and runtime properties have no effect on them.
  - `@LookupIfProperty` narrows *programmatic lookup* using runtime config.

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | `@DefaultBean` | overridable library defaults | none notable | library/extension-style defaults |
  | `@IfBuildProfile` | zero runtime cost | needs a rebuild per profile | dev/test stubs |
  | `@LookupIfProperty` | runtime switch | works only with `Instance<>` lookup | feature flags |

- Agent: "Ask whether the switch must change at runtime without a rebuild."
- Source: https://quarkus.io/version/3.40/guides/cdi-reference (2026-10-14)

**D. Mocking strategy: `@InjectMock` vs `QuarkusMock` vs test `@Alternative`**
> Confidence: 🟢 High
- Facts:
  - `@InjectMock` and `@InjectSpy` require `quarkus-junit-mockito`.
  - Only normal-scoped beans can be mocked ("basically every scope except @Singleton and @Dependent").
  - Beans used during startup are not mocked automatically. For those, use a test `@Alternative` in `src/test/java`, which does not work for native tests.
- Agent: "Ask whether the bean is used at startup and whether native tests apply."
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14)

### 🚫 Forbidden Patterns

**F1. Relying on `@Identifier` alone for a bean reached only by name from Camel**
> Severity: High
> Confidence: 🟡 Medium (the removal rules are High; whether they apply to `@Identifier` is UNVERIFIED, see U1)
- Why: the removal rules list `@Named`, not `@Identifier`, as a reason a bean is unremovable. Nothing in the docs says Camel Quarkus marks registry-looked-up beans as unremovable (U2).
- Impact: the bean may be removed at build time, and the Camel lookup then fails at runtime.
- ❌ Wrong:
  ```java
  @ApplicationScoped @Identifier("orderMapper") class OrderMapper {}
  ```
- ✅ Correct:
  ```java
  @ApplicationScoped @Identifier("orderMapper") @Unremovable class OrderMapper {}
  ```
- Source: https://quarkus.io/version/3.40/guides/cdi-reference ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html (2026-10-14)

**F2. Using `@Named` as a general-purpose qualifier**
> Severity: Medium
> Confidence: 🟢 High
- Why: a `@Named`-only bean also gets `@Default`, which causes ambiguity.
- Impact: ambiguous-dependency failures at build time.
- ❌ Wrong:
  ```java
  @Inject @Named("primary") ServiceInterface impl;
  ```
- ✅ Correct:
  ```java
  @Inject @Identifier("primary") ServiceInterface impl;
  ```
- Source: https://quarkus.io/version/3.40/guides/cdi-reference (2026-10-14)

**F3. Accessing fields of a normal-scoped bean directly**
> Severity: High
> Confidence: 🟢 High
- Why: the client proxy only delegates method calls.
- Impact: stale or non-contextual data.
- ❌ Wrong:
  ```java
  int n = counterBean.count;      // @ApplicationScoped bean
  ```
- ✅ Correct:
  ```java
  int n = counterBean.getCount();
  ```
- Source: https://quarkus.io/version/3.40/guides/cdi (2026-10-14)

**F4. Expecting CDI portable extensions or CDI Full features to work**
> Severity: High
> Confidence: 🟢 High
- Why: portable extensions are not supported. Use Quarkus extension build items instead (`AdditionalBeanBuildItem`, `UnremovableBeanBuildItem`, `SyntheticBeanBuildItem`, `BeanDefiningAnnotationBuildItem`, `AnnotationsTransformerBuildItem`). `InterceptionFactory` is replaced by `InterceptionProxy`. `@ConversationScoped` is not available.
- Impact: the extension is silently ignored, or the build fails.
- ❌ Wrong:
  ```java
  public class MyExt implements jakarta.enterprise.inject.spi.Extension { void abd(@Observes AfterBeanDiscovery e) {} }
  ```
- ✅ Correct:
  ```java
  @BuildStep AdditionalBeanBuildItem beans() { return AdditionalBeanBuildItem.unremovableOf(MyBean.class); }
  ```
- Source: https://quarkus.io/version/3.40/guides/cdi-reference ; https://quarkus.io/version/3.40/guides/cdi-integration (2026-10-14). (Exact factory-method name `unremovableOf`: 🟡 Medium. The page states `setUnremovable()` exists; it was not read for this name.)

**F5. `@InjectMock` on `@Singleton`/`@Dependent` beans**
> Severity: Medium
> Confidence: 🟢 High
- Impact: the mock is not installed.
- ❌ Wrong:
  ```java
  @Singleton class Clock {}   // test: @InjectMock Clock clock;
  ```
- ✅ Correct:
  ```java
  @ApplicationScoped class Clock {}   // or: @InjectMock @MockitoConfig(convertScopes = true) Clock clock;
  ```
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14)

**F6. Expecting `@IfBuildProfile`/`@IfBuildProperty` to react to runtime config**
> Severity: Medium
> Confidence: 🟢 High
- ❌ Wrong: `-Dquarkus.profile=prod java -jar app.jar`, expecting a dev-only `@IfBuildProfile("dev")` bean to disappear without rebuilding.
- ✅ Correct: rebuild for the profile, or use `@LookupIfProperty` with `Instance<>` to switch at runtime.
- Source: https://quarkus.io/version/3.40/guides/cdi-reference (2026-10-14)

---

## Migration Guide

> Confidence: 🟢 High for 3.39→3.40 | Sources: https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40 (2026-10-14) + https://quarkus.io/version/3.40/guides/cdi-reference (2026-10-14)

**Breaking Changes (3.39→3.40)**: none expected ("direct continuation of 3.39"). ArC items in the 3.16–3.39 migration guides were **not reviewed** in this run (see the Follow-up in Research Gaps).

**Convention changes vs the old 3.15 research file** (these are differences in the 3.40 docs, not documented breaking changes):
1. `@Named("primary")` qualifier → `@Identifier("primary")` (cdi-reference).
2. Test artifacts are `quarkus-junit` + `quarkus-junit-mockito`. `quarkus-junit5*` is absent from the 3.40 testing guide (https://quarkus.io/version/3.40/guides/getting-started-testing). ⚠️ Migration Note.
3. Camel test artifact `camel-quarkus-junit5` → `camel-quarkus-junit`, with imports moving to `org.apache.camel.test.junit6` (family fact, High, https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html). ⚠️ Migration Note.
4. `@QuarkusComponentTest` (used in the 3.15 file) was not verified for 3.40 in this run, so it is not carried forward.

**Upgrade Steps**:
1. Bump the Quarkus platform BOM to 3.40.x (the Camel Quarkus 3.40.x BOM uses Quarkus 3.40.1, family facts).
2. Replace general-purpose `@Named` qualifiers with `@Identifier`. Add `@Unremovable` to beans that are only looked up by name.
3. Rename the test dependencies as described in convention changes 2 and 3.
4. Run `./mvnw quarkus:dev` and inspect `/q/arc/removed-beans`.

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Jakarta CDI | 4.1 (Lite) | 4.1 | cdi-reference |
| Camel Quarkus | 3.40.x | 3.40.x | Quarkus 3.40.1, Camel 4.22.1 (family facts) |
| jandex-maven-plugin | 3.6.0 (documented) | — | cdi-reference |
| Gradle Jandex plugin | 2.3.0 (documented) | — | cdi-reference |
| Java baseline | UNVERIFIED for 3.40 (U3) | — | not on fetched pages; Quarkus 4 moves to Java 21 (family facts) |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | Quarkus cdi/cdi-reference + Camel Quarkus cdi.html]

**Lifecycle** (Quarkus 3.40):
```java
@ApplicationScoped
public class Inventory {
    @Inject Repo repo;                          // package-private injection
    @PostConstruct void init() { }              // keep side-effect free (cdi guide)
    @PreDestroy void close() { }
    void onStart(@Observes StartupEvent ev) { } // eager init
}

// Producer + disposer (producer: High; @Disposes semantics UNVERIFIED in 3.40 guides, U4)
@ApplicationScoped
class Clients {
    @Produces @ApplicationScoped @Identifier("erp") ErpClient erp() { return new ErpClient(); }
    void close(@Disposes @Identifier("erp") ErpClient c) { c.close(); }
}

// Interceptor
@InterceptorBinding @Retention(RUNTIME) @Target({TYPE, METHOD}) @interface Logged {}
@Logged @Interceptor @Priority(2020)
class LoggedInterceptor {
    @AroundInvoke Object log(InvocationContext ctx) throws Exception { return ctx.proceed(); }
}
```
- Producers with no explicit scope default to `@Dependent`. Injection points with no qualifier default to `@Default` (https://quarkus.io/version/3.40/guides/cdi).
- `@Produces` may be omitted when the method has a scope, stereotype or qualifier annotation. `@Inject` may be omitted on qualified fields, and on the constructor when there is only one (https://quarkus.io/version/3.40/guides/cdi-reference).
- Interceptors: lower `@Priority` values run first. Decorators need exactly one `@Delegate`, and decorating built-in beans such as `Event` is unsupported (cdi, cdi-reference).
- Events: `Event<T>.fire()` with `@Observes`. Async observer failures go to an `AsyncObserverExceptionHandler` bean and are logged by default (cdi-reference; 🟡 Medium for `@ObservesAsync` usage details).
- `@All List<T>` injects an immutable list sorted by priority. Programmatic lookup results are sorted with the highest priority first; the default priority is 0 (cdi-reference).

**Integration**: ArC ↔ camel-quarkus-core / camel-quarkus-bean
```java
@ApplicationScoped @Identifier("myBeanIdentifier") @Unremovable @RegisterForReflection
public class MyBean { public String hello(String n) { return "Hello " + n; } }

from("direct:start").bean("myBeanIdentifier", "hello");   // or .to("bean:myBeanIdentifier?method=hello")
```
- The `org.apache.camel.quarkus:camel-quarkus-bean` artifact provides bean lookup by name and `@Consume`. `@EndpointInject`/`@Produce` on fields come from camel-quarkus-core. Beans can inject `CamelContext`, `ProducerTemplate`, `FluentProducerTemplate`, `ConsumerTemplate` and `Registry`.
- `@Consume` beans get `@Singleton` + `@Named("<name><hash>")` added automatically.
- In `bean`/`.process` calls, use `@ActivateRequestContext` to avoid `ContextNotActiveException`.
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html (2026-10-14)

**Integration**: ArC ↔ SmallRye Config
```java
@ConfigProperty(name = "greeting.suffix", defaultValue = "!") String suffix;  // @Inject optional
@ConfigProperty(name = "opt.value") Optional<String> opt;                     // missing → empty
```
- A missing non-Optional property fails startup with `ConfigurationException`. `@ConfigMapping` is the recommended approach for groups of properties (https://quarkus.io/version/3.40/guides/config-reference, 2026-10-14).

**Integration**: ArC ↔ Quarkus REST
- JAX-RS resources are unremovable roots in ArC (https://quarkus.io/version/3.40/guides/cdi-reference). The REST guide itself was not fetched, so the default resource scope is not covered here: 🟡 Medium coverage.

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment (Quarkus 3.40)
./mvnw quarkus:dev -Dquarkus.log.category."io.quarkus.arc.processor".level=DEBUG
# Expected: discovery/removal logs; dev endpoints /q/arc, /q/arc/beans, /q/arc/removed-beans, /q/arc/observers (dev mode only)
curl -s localhost:8080/q/arc/removed-beans
# Expected: your name-looked-up beans are NOT listed
./mvnw test
# Expected: @QuarkusTest suites pass
```

**Mocking** (`quarkus-junit` + `quarkus-junit-mockito`, test scope):
```java
@QuarkusTest
class OrderServiceTest {
    @InjectMock PriceClient priceClient;   // io.quarkus.test.InjectMock; bean must be normal-scoped
    @Inject OrderService service;
    @Test void total() {
        Mockito.when(priceClient.price("A")).thenReturn(10);
        assertEquals(10, service.total("A"));
    }
}
```
- The mock applies only to test methods of the annotated test class. Use `QuarkusMock.installMockForType` in `@BeforeAll`. `@InjectSpy` keeps the real behavior and its observers still run.
- `quarkus.arc.test.disable-application-lifecycle-observers` (default `false`) disables application `StartupEvent`/`ShutdownEvent` observers during tests (https://quarkus.io/version/3.40/guides/cdi-reference).
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14)

---

## Production Readiness

- **Performance**: build-time DI. Normal-scoped beans are lazy, while `@Singleton`/`@Dependent` beans are created at injection. Unused-bean removal reduces boot time and memory (cdi-reference).
- **Scalability**: unaffected by DI. `@Lock` (READ/WRITE, with timeouts that raise `LockException`) gives container-managed concurrency (cdi-reference).
- **Monitoring**: `quarkus.arc.dev-mode.monitoring-enabled` defaults to `false`. Dependency graphs (`generate-dependency-graphs`, default `auto`, generated when there are fewer than 1000 beans) are dev-mode only (https://quarkus.io/version/3.40/guides/cdi-reference).
- **Security/robustness**:
  - Keep `quarkus.arc.detect-wrong-annotations=true` and `detect-unused-false-positives=true` (defaults).
  - `strict-compatibility` defaults to `false`.
  - `transform-unproxyable-classes` defaults to `true`.
  - `context-propagation.enabled` defaults to `true`.
  - All defaults from https://quarkus.io/version/3.40/guides/cdi-reference.
- **Native**: avoid private injection members. Register reflection targets (Camel docs: `@RegisterForReflection` for name-called beans). Test `@Alternative` mocks do not work in native tests.

---

## Reference Implementations

- Quarkus CDI introduction (3.40): https://quarkus.io/version/3.40/guides/cdi
- CDI reference (3.40): https://quarkus.io/version/3.40/guides/cdi-reference
- CDI integration for extensions (3.40): https://quarkus.io/version/3.40/guides/cdi-integration
- Camel Quarkus CDI (3.40.x): https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html
- Testing guide (3.40): https://quarkus.io/version/3.40/guides/getting-started-testing

---

## Source Bibliography

**Primary** (all fetched 2026-10-14; versioned 3.40 pages = current stable LTS):
- https://quarkus.io/version/3.40/guides/cdi-reference (read in full, including offset 100000)
- https://quarkus.io/version/3.40/guides/cdi
- https://quarkus.io/version/3.40/guides/cdi-integration
- https://quarkus.io/version/3.40/guides/getting-started-testing (first 100k of 108k characters)
- https://quarkus.io/version/3.40/guides/config-reference
- https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html
- workspace/_family_facts_v3.40.md (orchestrator-verified; releases, LTS dates, Camel test artifact rename)

**Validation** (search only, not used as evidence): https://quarkus.io/blog/unused-beans/ (unversioned, older; it restates the same removal roots).

---

## Research Gaps

```
U1 Gap: Is an @Identifier-only bean removed by ArC when it is not injected anywhere?
Impact: Camel name lookup could fail at runtime.
Workaround: add @Unremovable (or use quarkus.arc.unremovable-types / remove-unused-beans=fwk).
Follow-up: ArC processor source in quarkusio/quarkus (3.40 branch), or a test with /q/arc/removed-beans.
§7-ref: Iteration 1-3 — IRRESOLVABLE
```
```
U2 Gap: Does Camel Quarkus 3.40 produce UnremovableBeanBuildItem for beans referenced by name in routes?
Impact: same as U1.
Workaround: @Unremovable.
Follow-up: camel-quarkus core/bean deployment processors on GitHub (3.40.x branch).
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
U3 Gap: Minimum Java version for Quarkus 3.40 (not on the fetched pages).
Impact: build toolchain choice.
Follow-up: https://quarkus.io/version/3.40/guides/ getting-started prerequisites.
```
```
U4 Gap: @Disposes semantics are not described in the 3.40 cdi guide ("not covered"). The cdi-reference mentions disposers only in the native note.
Impact: the producer-cleanup example rests on the CDI spec, not on Quarkus docs.
Follow-up: Jakarta CDI 4.1 spec, disposer methods.
```
Also noted (no extra gap count): the cdi-reference "Removing unused beans" list and the config-property description of "unused" differ slightly (the config description says "does not have a name" and omits `@All`). The ArC-related items in the migration guides from 3.16 to 3.39 were not reviewed.

UNVERIFIED total: 4 (U1, U2, U3, U4). IRRESOLVABLE total: 2 (U1, U2).

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Guardrails | remove-unused-beans default = `all`, values none/false/fwk/framework | Resolved | https://quarkus.io/version/3.40/guides/cdi-reference (2026-10-14) |
| 1 | Metadata | CDI 4.1 Lite; unsupported: portable extensions, CDI Full beyond decorators/BeanManager subset/@SessionScoped(Undertow) | Resolved | https://quarkus.io/version/3.40/guides/cdi-reference (2026-10-14) |
| 1 | Guardrails | U1 @Identifier removal — versioned removal section does not mention @Identifier | Updated (still open) | https://quarkus.io/version/3.40/guides/cdi-reference (2026-10-14) |
| 2 | Migration | 3.39→3.40 no manual changes | Added | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40 (2026-10-14) |
| 2 | Guardrails | U1 targeted GitHub/official search — no statement found | Updated (still open) | — |
| 3 | Integration | camel-quarkus-bean page checked for unremovable handling — not covered | ⚠️ IRRESOLVABLE — U2: no official page states it | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html (2026-10-14) |
| 3 | Guardrails | U1 | ⚠️ IRRESOLVABLE — docs list only @Named as the name-based root; behaviour needs source/test | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Standard)
- [x] All scope areas cited (discovery, scopes, qualifiers, producers, interceptors/decorators, events, lifecycle, removal, conditional beans, config, limitations, native, testing)
- [x] Pattern counts driven by domain needs
- [x] Every anti-pattern has alternative
- [x] All CLI commands marked as representative
- [x] Integration examples complete (Camel, Config; REST partially, Medium)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns triangulated or downgraded to 🟡 Medium (4, 5 downgraded)
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score calculated
- [x] Every Research Gap cross-referenced in §7 (U1, U2 IRRESOLVABLE; U3, U4 unverified, not looped beyond iteration budget)

---

## Agent Operation Notes

- **High Confidence**: removal default and roots; the `@Identifier`-over-`@Named` guidance; CDI 4.1 Lite and its limitations; scope semantics; `@InjectMock` restrictions; RouteBuilder scope rule.
- **Medium Confidence**: private-member/native guidance (Always-Do 4); `@Startup` (Always-Do 5); the `AdditionalBeanBuildItem.unremovableOf` name; async observer details; Quarkus REST integration.
- **Low Confidence / ask human**: U1, U2 (IRRESOLVABLE); U3, U4.
- **Edge Cases**: Quarkus 3.40 has been out more than 30 days (released 2026-09-30, i.e. 14 days before 2026-10-14). ⚠️ Correction: it is **less than 30 days old**, so later patch releases may change details. Re-check before skill authoring.
- **Emergency Stop**: not triggered (official versioned docs exist).
