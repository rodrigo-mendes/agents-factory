---
name: developing-camel-quarkus-junit-v3-40
description: "Guides Camel Quarkus 3.40.x route tests with camel-quarkus-junit: CamelQuarkusTestSupport, AdviceWith, adviceRoute, @QuarkusTest, @QuarkusIntegrationTest. Use when testing Camel routes on Quarkus. Not for generic Quarkus testing (developing-quarkus-junit-v3-40), Quarkus 4 or other versions."
---

# Developing Camel Quarkus Tests with camel-quarkus-junit 3.40.x

> Version lock: every claim applies to **Camel Quarkus 3.40.x** (Camel 4.22.x) only. Research date **2026-10-14**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against a versioned official page; treat them as hypotheses. Every tag maps to a register id: see the [tag to register mapping](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> This skill is the single authority in the family for Camel route-test content (`CamelQuarkusTestSupport`, `doBeforeEach`, `adviceRoute`, AdviceWith); other skills point here.
> The generic Quarkus test framework (`@QuarkusTest` lifecycle, profiles, Mockito) belongs to the sibling skill `developing-quarkus-junit-v3-40`; core topics (BOMs, CDI, route discovery) to `developing-camel-quarkus-core-v3-40`.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| Camel Quarkus | 3.40.0 released 2026-09-28, marked LTS | https://camel.apache.org/releases/ |
| Camel / Quarkus / GraalVM | 4.22.1 / 3.40.1 / 25.0.4.1 | https://camel.apache.org/camel-quarkus/latest/ |
| Java | 17 and 21 | https://camel.apache.org/releases/q-3.40.0/ |
| Test artifact | `org.apache.camel.quarkus:camel-quarkus-junit`; pulls `quarkus-junit`, `camel-quarkus-core`, `camel-test-junit6` (compile scope) | https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit/3.40.0/camel-quarkus-junit-3.40.0.pom |
| Base class | `org.apache.camel.quarkus.test.CamelQuarkusTestSupport extends AbstractTestSupport implements QuarkusTestProfile` | https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java |
| Old artifact | `camel-quarkus-junit5` 3.40.0 is a deprecated stub whose only dependency is `camel-quarkus-junit`; removal date (unverified) | https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/3.40.0/camel-quarkus-junit5-3.40.0.pom |
| Rename | `camel-quarkus-junit5` to `camel-quarkus-junit`, `org.apache.camel.test.junit5` to `junit6` since 3.31 | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html |
| Quarkus 3.40 support | LTS, community-maintained until 2027-09-30 | https://quarkus.io/releases |

**Version-lifetime risk** (as of 2026-10-14; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; Java 21 is the new base ([Beta1 post](https://quarkus.io/blog/quarkus-4-0-0-beta1-released/), High). No Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence). Do not mix Quarkus 4 artifacts.
- The Camel Quarkus-specific end date for 3.40 is (unverified): the "LTS Until" column is blank on https://camel.apache.org/camel-quarkus/latest/; applying the Quarkus date is an inference.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [AdviceWith, lifecycle hooks and route loading](./blueprints/advice-with-and-lifecycle.md)
- [Native and packaged integration tests](./blueprints/native-testing.md)
- [Migration 3.15 to 3.40 (junit5 rename, 3.36 changes)](./blueprints/migration-3-31-rename.md)
- [Integration examples (REST Assured, Mockito, test resources, NotifyBuilder)](./blueprints/integration-examples.md)
- [Unverified and irresolvable register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Depend on `camel-quarkus-junit` at `test` scope.** It is the only test artifact the 3.40 testing guide documents ([testing guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html)). See [patterns](./blueprints/always-do-patterns.md#1-test-dependency).
- **Import `CamelQuarkusTestSupport` from the package `org.apache.camel.quarkus.test`.** The class exists in that package in the 3.40.0 source ([source at tag 3.40.0](https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java)). See [patterns](./blueprints/always-do-patterns.md#2-base-class-and-package).
- **Assume one CamelContext shared by the whole suite.** The guide says one context is shared by the suite ([testing guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html)). See [patterns](./blueprints/always-do-patterns.md#3-one-shared-camelcontext).
- **Put class-wide advice in `doBeforeEach(QuarkusTestMethodContext)`.** The 3.40.0 source declares that hook ([source at tag 3.40.0](https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java)). See [patterns](./blueprints/always-do-patterns.md#4-advice-in-dobeforeeach).
- **Use `adviceRoute(routeId, advice)` for per-method advice of application routes.** The helper handles stop, advice and start ([3.36.0 migration guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html)). See [patterns](./blueprints/always-do-patterns.md#5-per-method-adviceroute).
- **Keep `@QuarkusIntegrationTest` classes free of `@Inject` and bean overrides.** The Camel guide states this restriction ([testing guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html)). See [patterns](./blueprints/always-do-patterns.md#6-integration-tests-without-injection) and [native testing](./blueprints/native-testing.md).
- **Let a `@QuarkusIntegrationTest` talk to the application over the network, filesystem watching or other IPC.** The Camel guide names these channels as the way to communicate ([testing guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html)). See [native testing](./blueprints/native-testing.md).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Base class | Extend `CamelQuarkusTestSupport` (mock and AdviceWith helpers, JVM only, [source](https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java)) vs plain `@QuarkusTest` with `@Inject CamelContext`/`ProducerTemplate` (medium confidence: the plain-test style comes from `main`-branch examples, [source](https://github.com/apache/camel-quarkus-examples)) | "Do you need the mock and AdviceWith helpers, or must the same test also run against the native or packaged artifact?" |
| Integration-test reuse | `@QuarkusIntegrationTest` subclassing a plain `@QuarkusTest` class that uses REST Assured or files only (medium confidence: `main`-branch example, [timer-log](https://github.com/apache/camel-quarkus-examples/blob/main/timer-log/src/test/java/org/acme/timer/log/TimerLogIT.java)) vs a standalone integration test | "Must the JVM test be reused unchanged as an integration test?" |
| State isolation | Shared context (fast, state can leak) vs `@TestProfile` to get a clean context (a different `@TestProfile` restarts Quarkus and the CamelContext, medium confidence, M12, [Quarkus 3.40 guide](https://quarkus.io/version/3.40/guides/getting-started-testing); that the Quarkus orderer groups tests of the same profile to reduce restarts is (medium confidence, M13; same tag as M1 in `developing-quarkus-junit-v3-40`), but the property name `quarkus.test.class-orderer` is (unverified), U5: it is cited in the Camel research and no Quarkus JUnit skill page names it) | "Is cross-class leakage of registry beans or mock expectations acceptable?" |
| External systems | `QuarkusTestResourceLifecycleManager` (config from `start()` wins over `application.properties`) vs Mockito `@InjectMock` (needs `quarkus-junit-mockito`). `@InjectMock` with beans a route looks up by name is (unverified) | "Is the dependency a CDI bean or an external server?" |
| Registry binding | `@Produces @Named` bean, `@BindToRegistry` field or `createCamelContext` override. The guide shows the override, the 3.40.0 source does not declare it (irresolvable) | "Can the bean be a CDI bean instead?" |
| `NotifyBuilder` (medium confidence, unversioned [manual page](https://camel.apache.org/manual/notify-builder.html)) | `NotifyBuilder` vs `MockEndpoint`; behavior against the shared context is (unverified) | "Is a MockEndpoint assertion enough?" |
| `replaceFromWith` (medium confidence: from the Camel AdviceWith manual, not on the 3.40 Camel Quarkus page) | Use it inside `adviceRoute` vs start the route from a `direct:` test route | "Should the consumer endpoint be replaced?" |
| Keeping `camel-quarkus-junit5` | Keep the stub (resolves today, removal date (unverified)) vs migrate | "Can the build move to `camel-quarkus-junit` now?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Use `camel-quarkus-junit5` or `org.apache.camel.test.junit5` imports; renamed in 3.31 ([3.31.0 guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html)) | `camel-quarkus-junit` at test scope and `org.apache.camel.test.junit6` imports |
| Call `startRouteDefinitions()` after AdviceWith; since 3.36 non-advised routes start automatically ([3.36.0 guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html)) | Rely on the auto-start after `@BeforeEach`/`doBeforeEach` ([3.36.0 guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html)) |
| Call `stop()`/`start()` on the shared CamelContext, or return a new one (the guide says you can't call `stop()`/`start()` and that returning a new context "throws an exception", [testing guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html)) | Inspect or configure the injected context, never replace it: the `camelContextSupplier` javadoc says "Do not create your own CamelContext instance" ([source at tag 3.40.0](https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java)); a clean context via `@TestProfile` is in Ask First |
| Use wildcard weave patterns such as `weaveByToUri("kafka:*")` ([testing guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html)) | `weaveById("kafkaProducer")` ([testing guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html)) |
| Advise routes defined in `createRouteBuilder()`; behavior "can be unpredictable" ([testing guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html)) | Advise routes from application code; use `createRouteBuilder()` only for test-only routes ([testing guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html)) |
| Use `@Inject`, bean overrides or `CamelQuarkusTestSupport` in `@QuarkusIntegrationTest`; it does not work in native mode ([source javadoc](https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java)) | Keep the integration test free of `@Inject` and `CamelQuarkusTestSupport`; use network, files or other IPC ([testing guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html)) |
| Override `isUseAdviceWith()`; `@Deprecated(since = "3.15.0")` in the 3.40.0 source ([source](https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java)) | Advise in `doBeforeEach(QuarkusTestMethodContext)` ([source](https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java)) |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| `doBeforeEach` signature | `protected void doBeforeEach(QuarkusTestMethodContext context) throws Exception` | https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java |
| `adviceRoute` signature | `protected void adviceRoute(String routeId, ThrowingConsumer<AdviceWithRouteBuilder, Exception> advice) throws Exception` | https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java |
| Hook mapping | `beforeAll`: `doAfterConstruct`; `beforeEach`: `doBeforeEach`; `afterEach`/`afterTestExecution`: `doAfterEach`; `afterAll`: `doAfterAll` | https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html |
| Mode | `CamelQuarkusTestSupport` is JVM mode only | https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html |
| Test HTTP port / timeout | `quarkus.http.test-port` 8081 (0 = random) / `quarkus.http.test-timeout` 30 s | https://quarkus.io/version/3.40/guides/getting-started-testing |
| Integration test profile | `prod` by default; `src/test/resources/application.properties` ignored (medium confidence) | https://quarkus.io/version/3.40/guides/getting-started-testing |
| Route filters in tests | `quarkus.camel.routes-discovery.include-patterns`/`exclude-patterns`, `camel.main.routes-include-pattern`/`routes-exclude-pattern` | https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html |
| Mockito support | `quarkus-junit-mockito` (test scope) for `@InjectMock`/`@InjectSpy` | https://quarkus.io/version/3.40/guides/getting-started-testing |
| Representative commands | `mvn verify`; `mvn verify -Dnative` | page not recorded |

## External Resources

All fetched 2026-10-14. camel.apache.org pages carry no page date and are the current stable 3.40.x docs.

- Testing guide: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
- 3.31.0 migration guide: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html
- 3.36.0 migration guide: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html
- Quarkus 3.40 testing guide: https://quarkus.io/version/3.40/guides/getting-started-testing
- Source at tag 3.40.0: https://github.com/apache/camel-quarkus/tree/3.40.0/test-framework
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
