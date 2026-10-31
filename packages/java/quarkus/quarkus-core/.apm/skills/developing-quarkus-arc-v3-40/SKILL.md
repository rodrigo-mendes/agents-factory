---
name: developing-quarkus-arc-v3-40
description: "Guides quarkus-arc (ArC, the Quarkus CDI container) in Quarkus and Camel Quarkus 3.40.x apps: scopes, qualifiers, unused-bean removal, Jandex, mocking. Use when writing CDI beans in 3.40.x. Not for Quarkus 4, other versions or CDI Full."
---

# Developing with Quarkus ArC 3.40.x

> Version lock: every claim applies to **Quarkus 3.40.x** (ArC, `io.quarkus:quarkus-arc`) and to Camel Quarkus 3.40.x apps only. Research date **2026-10-14**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| Quarkus | 3.40; released 2026-09-30, LTS, community-maintained until 2027-09-30 | https://quarkus.io/releases |
| Quarkus latest patch | 3.40.1.1 (2026-10-19) | https://quarkus.io/releases (read 2026-10-28) |
| Camel Quarkus pairing | 3.40.x uses Quarkus 3.40.1, Camel 4.22.1 (the pairing statement of that page, not the latest Quarkus patch) | https://camel.apache.org/camel-quarkus/latest/ |
| CDI spec | Jakarta CDI 4.1, CDI Lite; CDI Full is not implemented | https://quarkus.io/version/3.40/guides/cdi-reference |
| Migration 3.39 to 3.40 | "direct continuation of 3.39", no manual changes expected | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40 |
| Maven artifact | `io.quarkus:quarkus-arc` (unverified, U8) | page not recorded |
| Java | Camel Quarkus 3.40 supports Java 17 and 21; the Quarkus 3.40 minimum is not recorded (unverified, U3) | https://camel.apache.org/releases/q-3.40.0/ |

**Version-lifetime risk** (as of 2026-10-14; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; Java 21 becomes the base ([source](https://quarkus.io/blog/quarkus-4-0-0-beta1-released/)). No Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence). Pin 3.40.x.
- The Camel Quarkus-specific support end date for 3.40 is not published (unverified, U5).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference) | [Verification Loop](#verification-loop)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Scopes, qualifiers and injection](./blueprints/scopes-and-injection.md)
- [Unused-bean removal](./blueprints/bean-removal.md)
- [CDI Lite limitations](./blueprints/cdi-lite-limitations.md)
- Camel bean binding with ArC: see `developing-camel-quarkus-bean-v3-40` (Quarkus + Camel package)
- [Testing and mocking](./blueprints/testing.md)
- [Migration guide (3.15 baseline to 3.40)](./blueprints/migration-guide.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Give every bean class a bean-defining annotation (a scope).** Discovery runs in annotated mode, so a class without one is not a bean ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)). See [patterns](./blueprints/always-do-patterns.md#1-bean-defining-annotation).
- **Mark a bean reached only through `CDI.current()` with `@Unremovable`.** ArC cannot detect such lookups, so the bean may be removed ([CDI integration](https://quarkus.io/version/3.40/guides/cdi-integration)). See [patterns](./blueprints/always-do-patterns.md#2-unremovable-for-programmatic-lookup).
- **Prefer `@io.smallrye.common.annotation.Identifier` to `@Named` for qualification.** The CDI reference says "Instead of @Named, use @Identifier" ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)). See [patterns](./blueprints/always-do-patterns.md#3-identifier-instead-of-named).
- **Index external bean archives.** A dependency is scanned only with `beans.xml`, `META-INF/jandex.idx` or a `quarkus.index-dependency.<name>.*` entry ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)). See [patterns](./blueprints/always-do-patterns.md#4-index-external-bean-archives).
- **Add `@ApplicationScoped` to a Camel `RouteBuilder` only when it uses `@Inject` or `@ConfigProperty`.** The scope is "required for @Inject and @ConfigProperty" ([Camel Quarkus CDI guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html)). See [patterns](./blueprints/always-do-patterns.md#5-routebuilder-scope-only-when-injecting).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Bean reached by name from Camel, qualified only with `@Identifier` | The removal rules list `@Named`, `@Unremovable`, `unremovable-types` and observers as unremovable, not `@Identifier`; removal of an `@Identifier`-only bean is (unverified) and Camel Quarkus marking such beans unremovable is (unverified). Default: add `@Unremovable` ([bean removal](./blueprints/bean-removal.md)) | "Is the bean injected by type anywhere, or only looked up by name?" |
| `@Named` kept as qualifier | Recommendation only, not a failure: a `@Named`-only bean also gets `@Default`, which can be ambiguous; `@Named` stays reasonable when an external language such as Qute needs the name ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)) | "Does an external language need the bean name?" |
| Scope choice | `@ApplicationScoped` (lazy proxy, mockable) vs `@Singleton` (no proxy, not mockable by default) vs `@Dependent` vs `@RequestScoped` ([scopes](./blueprints/scopes-and-injection.md#scope-selection)) | "Must the bean be mocked in tests or used from Camel processors?" |
| Removal mode | `all` (default) vs `fwk` vs `none` ([bean removal](./blueprints/bean-removal.md#removal-modes)) | "Are application beans reached only by string name or `CDI.current()`?" |
| Build-time enablement | `@DefaultBean`, `@IfBuildProfile`, `@IfBuildProperty` (build time) vs `@LookupIfProperty` (runtime, `Instance<>` only) ([scopes](./blueprints/scopes-and-injection.md#build-time-bean-enablement)) | "Must the switch change at runtime without a rebuild?" |
| Mocking strategy | `@InjectMock` vs `QuarkusMock` vs test `@Alternative` (not for native tests). Only normal-scoped beans can be mocked ("basically every scope except @Singleton and @Dependent"), so a `@Singleton` or `@Dependent` bean needs a normal scope such as `@ApplicationScoped` or `@MockitoConfig(convertScopes = true)`; `@InjectMock` and `@InjectSpy` need `quarkus-junit-mockito` in test scope; the `convertScopes` and artifact parts are (medium confidence, L1) ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing); [testing](./blueprints/testing.md#injectmock)) | "Is the bean used at startup, and do native tests apply?" |
| Private injection members (medium confidence) | Package-private members avoid reflection registration and a larger native executable ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)) | "Is the app built as a native executable?" |
| Eager startup (medium confidence) | `@Startup` or `@Observes StartupEvent` vs lazy creation on first proxy call | "Must the bean exist before the first call?" |
| `@Disposes` cleanup (unverified, U4) | The 3.40 CDI guide does not describe disposer semantics; rely on the Jakarta CDI spec | "Is cleanup of a produced bean required?" |
| Quarkus REST scope (medium confidence) | JAX-RS resources are unremovable roots; for the default resource scope see skill `developing-quarkus-rest-v3-40` | "Which scope should the resource use?" |
| Java version (unverified, U3) | Camel Quarkus 3.40 supports Java 17 and 21; the Quarkus 3.40 minimum is not recorded; Quarkus 4 moves to Java 21 | "Which JDK does the build use?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Read fields of a normal-scoped bean directly (`counterBean.count`); the client proxy delegates only method calls ([CDI guide](https://quarkus.io/version/3.40/guides/cdi)) | Call a method (`counterBean.getCount()`) ([CDI guide](https://quarkus.io/version/3.40/guides/cdi)) |
| Use `InterceptionFactory` in application code; ArC replaces it with `InterceptionProxy` ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)) | Use `InterceptionProxy` ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)) |
| Expect `@IfBuildProfile` / `@IfBuildProperty` to react to runtime profile or properties; they are evaluated at build time ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)) | Rebuild per profile, or switch at runtime with `@LookupIfProperty` and `Instance<>` ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)) |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| `quarkus.arc.remove-unused-beans` | `all` default; also `none`/`false`, `fwk`/`framework` | https://quarkus.io/version/3.40/guides/cdi-reference |
| Unremovable roots | `@Unremovable`, `quarkus.arc.unremovable-types`, `UnremovableBeanBuildItem`, `@Named` beans, beans with an observer method | https://quarkus.io/version/3.40/guides/cdi-reference |
| Unannotated producer scope; unqualified injection point | `@Dependent`; `@Default` | https://quarkus.io/version/3.40/guides/cdi |
| `@DefaultBean` | used only if no other bean has the same types and qualifiers; `@Priority` default 0 | https://quarkus.io/version/3.40/guides/cdi-reference |
| Build-profile and build-property annotations | evaluated at build time | https://quarkus.io/version/3.40/guides/cdi-reference |
| `quarkus.arc.transform-private-injected-fields` (medium confidence) | `true` default | https://quarkus.io/version/3.40/guides/cdi-reference |
| `@All List<T>` | immutable, sorted by priority; lookup results highest priority first; default priority 0 | https://quarkus.io/version/3.40/guides/cdi-reference |
| Other ArC defaults | `detect-wrong-annotations=true`, `detect-unused-false-positives=true`, `strict-compatibility=false`, `transform-unproxyable-classes=true`, `context-propagation.enabled=true` | https://quarkus.io/version/3.40/guides/cdi-reference |
| `quarkus.arc.test.disable-application-lifecycle-observers` | `false` default | https://quarkus.io/version/3.40/guides/cdi-reference |
| `quarkus.arc.dev-mode.monitoring-enabled` | `false` default; dependency graphs `auto`, generated below 1000 beans, dev mode only | https://quarkus.io/version/3.40/guides/cdi-reference |
| Documented Jandex plugins | jandex-maven-plugin and the Gradle Jandex plugin (take the versions from the CDI reference) | https://quarkus.io/version/3.40/guides/cdi-reference |
| JAX-RS resources (medium confidence) | unremovable roots | https://quarkus.io/version/3.40/guides/cdi-reference |
| Missing non-`Optional` `@ConfigProperty` | fails startup with `ConfigurationException` | https://quarkus.io/version/3.40/guides/config-reference |
| Test artifacts (medium confidence, L1) | `quarkus-junit` and `quarkus-junit-mockito` | https://quarkus.io/version/3.40/guides/getting-started-testing |
| Camel test artifact | `camel-quarkus-junit` (renamed from `camel-quarkus-junit5`; High) | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html |
| Dev-mode endpoints | `/q/arc`, `/q/arc/beans`, `/q/arc/removed-beans`, `/q/arc/observers` (representative; unverified, U9) | page not recorded |

## Verification Loop

Self-check after writing or changing beans (commands from the blueprints; the dev-mode endpoint is representative, unverified, U9):

```bash
./mvnw test                                                                                   # @QuarkusTest suites pass (testing.md)
./mvnw quarkus:dev -Dquarkus.log.category."io.quarkus.arc.processor".level=DEBUG              # bean-removal.md
curl -s localhost:8080/q/arc/removed-beans                                                    # no bean you rely on is listed as removed
```

## External Resources

All fetched 2026-10-14. quarkus.io/version/3.40 pages document the current stable LTS.

- Quarkus CDI introduction: https://quarkus.io/version/3.40/guides/cdi
- CDI reference: https://quarkus.io/version/3.40/guides/cdi-reference
- CDI integration for extensions: https://quarkus.io/version/3.40/guides/cdi-integration
- Testing guide: https://quarkus.io/version/3.40/guides/getting-started-testing
- Camel Quarkus CDI guide: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
