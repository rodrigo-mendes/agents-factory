# Scopes, Qualifiers and Injection: Quarkus ArC 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Sources are versioned 3.40 pages unless a line says otherwise.

## Contents

- [Scope selection](#scope-selection)
- [Injection rules](#injection-rules)
- [Lifecycle, producers and interceptors](#lifecycle-producers-and-interceptors)
- [Build-time bean enablement](#build-time-bean-enablement)
- [Medium-confidence items](#medium-confidence-items)

## Scope selection

| Scope | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `@ApplicationScoped` | lazy init, mockable, circular dependencies | proxy indirection; never access fields directly | default |
| `@Singleton` | slightly better performance; fields can be accessed safely | no proxy; not `@InjectMock`-able without `@MockitoConfig(convertScopes = true)` (medium confidence, L1) | hot path, never mocked |
| `@Dependent` | one instance per injection point | bound to the owner's lifecycle; not mockable with `@InjectMock` without `@MockitoConfig(convertScopes = true)` (medium confidence, L1) | stateful helpers |
| `@RequestScoped` | per-request state | needs an active request context; in Camel `bean`/`process` calls use `@ActivateRequestContext` | request data |

Normal-scoped beans are created lazily, on the first method call on their client proxy; being injected does not create them. `@Singleton` and `@Dependent` beans are created at injection (cdi-reference).

Sources: https://quarkus.io/version/3.40/guides/cdi ; https://quarkus.io/version/3.40/guides/getting-started-testing ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html

## Injection rules

- A producer with no explicit scope is `@Dependent`; an injection point with no qualifier is `@Default` ([cdi](https://quarkus.io/version/3.40/guides/cdi)).
- `@Produces` may be omitted when the method has a scope, stereotype or qualifier annotation. `@Inject` may be omitted on qualified fields, and on the constructor when there is only one ([cdi-reference](https://quarkus.io/version/3.40/guides/cdi-reference)).
- `@All List<T>` injects an immutable list sorted by priority. Programmatic lookup results are sorted with the highest priority first; the default priority is 0 ([cdi-reference](https://quarkus.io/version/3.40/guides/cdi-reference)).
- Qualifier with `@Identifier`:

```java
@ApplicationScoped @Identifier("primary") class PrimaryClient implements Client {}

@Inject @Identifier("primary") Client client;
```

## Lifecycle, producers and interceptors

```java
@ApplicationScoped
public class Inventory {
    @Inject Repo repo;                          // package-private injection
    @PostConstruct void init() { }              // keep side-effect free (cdi guide)
    @PreDestroy void close() { }
}

@ApplicationScoped
class Clients {
    @Produces @ApplicationScoped @Identifier("erp") ErpClient erp() { return new ErpClient(); }
}

@InterceptorBinding @Retention(RUNTIME) @Target({TYPE, METHOD}) @interface Logged {}
@Logged @Interceptor @Priority(2020)
class LoggedInterceptor {
    @AroundInvoke Object log(InvocationContext ctx) throws Exception { return ctx.proceed(); }
}
```

- Interceptors: lower `@Priority` values run first. A decorator needs exactly one `@Delegate`, and decorating built-in beans such as `Event` is unsupported ([cdi](https://quarkus.io/version/3.40/guides/cdi), [cdi-reference](https://quarkus.io/version/3.40/guides/cdi-reference)).
- Events: `Event<T>.fire()` with `@Observes`.
- `@Lock` (READ/WRITE, with timeouts that raise `LockException`) gives container-managed concurrency ([cdi-reference](https://quarkus.io/version/3.40/guides/cdi-reference)).
- A `@Disposes` method for the producer above is (unverified): the 3.40 CDI guide (https://quarkus.io/version/3.40/guides/cdi) does not describe disposer semantics (register U4); rely on the Jakarta CDI spec.

## Build-time bean enablement

- `@DefaultBean` applies only if no other bean has the same types and qualifiers; it supports `@Priority`, default 0.
- `@IfBuildProfile`, `@UnlessBuildProfile`, `@IfBuildProperty`, `@UnlessBuildProperty` are evaluated at build time.
- `@LookupIfProperty` narrows programmatic lookup using runtime config and works only with `Instance<>` lookup.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `@DefaultBean` | overridable library defaults | none noted | library-style defaults |
| `@IfBuildProfile` | zero runtime cost | rebuild per profile | dev and test stubs |
| `@LookupIfProperty` | runtime switch | only with `Instance<>` | feature flags |

Source: https://quarkus.io/version/3.40/guides/cdi-reference

## Medium-confidence items

Each maps to the [register](./unverified-and-risks.md#medium-confidence-items).

- **Private injection members (medium confidence, M1).** Quarkus reaches private members through reflection, which must be registered for GraalVM and enlarges the native executable. Make injection fields, constructors, initializers, observers, producers, disposers and interceptor methods package-private. `quarkus.arc.transform-private-injected-fields` defaults to `true`. Single source: https://quarkus.io/version/3.40/guides/cdi-reference
- **Eager startup (medium confidence, M2).** Use `@io.quarkus.runtime.Startup` or `void onStart(@Observes StartupEvent ev)`; the docs recommend `StartupEvent` over `@Initialized(ApplicationScoped.class)`. Single source: https://quarkus.io/version/3.40/guides/cdi-reference

```java
@ApplicationScoped
class Warmup { void onStart(@Observes StartupEvent ev) { /* init */ } }
```

- **Async observers (medium confidence, M4).** Failures in `@ObservesAsync` observers go to an `AsyncObserverExceptionHandler` bean and are logged by default; usage details were not fully read (cdi-reference).
- **Quarkus REST (medium confidence, M5).** JAX-RS resources are unremovable roots in ArC (cdi-reference). For the default resource scope see skill `developing-quarkus-rest-v3-40`, which read the REST guide.
