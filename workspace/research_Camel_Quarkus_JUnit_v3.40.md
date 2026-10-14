# Research: Camel Quarkus JUnit (camel-quarkus-junit) v3.40

> Run note: this was a forked run (batch 3 of the skill fan-out). The user approved the scheme earlier in the session, and no user is available inside this fork, so the P3 plan-approval step (EnterPlanMode/ExitPlanMode) was skipped. The caller asked for no sub-investigators, so all pages were fetched directly with WebFetch/WebSearch on 2026-10-14. The v3.15 file at `<integrator-project>/research/research_Camel_Quarkus_JUnit5_v3.15.md` supplied topic names only and is not cited as a source.

## Metadata

```yaml
Full_Name: Apache Camel Quarkus JUnit test framework (org.apache.camel.quarkus:camel-quarkus-junit)
Target_Version: 3.40.x (Camel 4.22.1, Quarkus 3.40.1, GraalVM 25.0.4.1)  # https://camel.apache.org/camel-quarkus/latest/ (family facts, High)
Release_Date: 2026-09-28 (Camel Quarkus 3.40.0, LTS)                       # https://camel.apache.org/releases/ (family facts, High)
Support_Status: LTS; Camel Quarkus end date not published (IRRESOLVABLE I2); Quarkus 3.40 community support until 2027-09-30  # https://quarkus.io/releases
Primary_Docs: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
Official_Repo: https://github.com/apache/camel-quarkus (ref 3.40.0, test-framework/camel-quarkus-junit)
Research_Date: 2026-10-14
Domain_Complexity: Standard
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 5
Unverified_Count: 3
Irresolvable_Count: 2
Research_Quality_Score: 93%   # (72 claims - 3 unverified - 2 irresolvable) / 72
```

---

## Executive Summary

`camel-quarkus-junit` is the Camel Quarkus test framework for 3.40.x. Its POM pulls in `io.quarkus:quarkus-junit`, `camel-quarkus-core` and `org.apache.camel:camel-test-junit6`, all at compile scope ([camel-quarkus-junit-3.40.0.pom](https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit/3.40.0/camel-quarkus-junit-3.40.0.pom), High). It provides `org.apache.camel.quarkus.test.CamelQuarkusTestSupport`, a base class for `@QuarkusTest` classes with CamelTestSupport-style helpers: `getMockEndpoint`, `AdviceWith`, `adviceRoute`, `createRouteBuilder` and the `do*` lifecycle hooks. The runtime creates one `CamelContext`, shared by every test in the suite, and the class works only in JVM mode ([3.40 testing guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html), High).

Changes since the 3.15 conventions:
- **3.31:** `camel-quarkus-junit5` was renamed `camel-quarkus-junit`, and imports moved from `org.apache.camel.test.junit5` to `org.apache.camel.test.junit6` ([3.31.0 migration guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html), High).
- **3.36:** routes that are not advised now start automatically after `doBeforeEach()`/`@BeforeEach`, so `startRouteDefinitions()` is no longer needed. A new per-method `adviceRoute()` helper was added, and advice is cleaned up automatically between test methods ([3.36.0 migration guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html), High).
- **`camel-quarkus-junit5` 3.40.0:** it still exists on Maven Central, but only as a deprecated stub. Its whole content is one dependency on `camel-quarkus-junit` ([POM](https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/3.40.0/camel-quarkus-junit5-3.40.0.pom), High). This contradicts the 3.31 statement that it would be removed with 3.34.0.

The three critical patterns are:
1. Depend on `camel-quarkus-junit` at `test` scope.
2. Never stop, start or replace the shared `CamelContext`. Use `@TestProfile` when a clean context is needed.
3. Advise only routes defined in application code. Use specific `weaveById`/URI matchers, not wildcards.

Tier: **Standard**. The surface spans multiple integrations (Quarkus test framework, Mockito, REST Assured, native IT) and has lifecycle traps around the shared context, but it is not security-critical.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**1. Use `camel-quarkus-junit` (test scope) and `org.apache.camel.test.junit6`** ⚠️ Migration Note
> Confidence: 🟢 High | [✓✓ Triangulated | 3.40 testing guide (2026-10-14) + 3.31.0 migration guide (2026-10-14) + junit5 3.40.0 POM "DEPRECATED: This artifact has moved to org.apache.camel.quarkus:camel-quarkus-junit"]
- Why: this is the only test artifact the 3.40 testing guide documents. `junit5` is a deprecated stub.
- Code:
  ```xml
  <!-- Camel Quarkus 3.40.x; version managed by the Camel Quarkus BOM -->
  <dependency>
      <groupId>org.apache.camel.quarkus</groupId>
      <artifactId>camel-quarkus-junit</artifactId>
      <scope>test</scope>
  </dependency>
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html ; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html ; https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/3.40.0/camel-quarkus-junit5-3.40.0.pom (all fetched 2026-10-14)

**2. `@QuarkusTest` + `extends org.apache.camel.quarkus.test.CamelQuarkusTestSupport`**
> Confidence: 🟢 High | [✓✓ Triangulated | testing guide + source at tag 3.40.0]
- Why: the guide says to annotate with `@QuarkusTest` and extend the base class. The 3.40.0 source declares `package org.apache.camel.quarkus.test;` and `public class CamelQuarkusTestSupport extends AbstractTestSupport implements QuarkusTestProfile`. The context is injected (`@Inject protected CamelContext context;`).
- Code:
  ```java
  // Camel Quarkus 3.40.x, JVM mode only
  import io.quarkus.test.junit.QuarkusTest;
  import org.apache.camel.component.mock.MockEndpoint;
  import org.apache.camel.quarkus.test.CamelQuarkusTestSupport;
  import org.junit.jupiter.api.Test;

  @QuarkusTest
  class GreetRouteTest extends CamelQuarkusTestSupport {
      @Test
      void greets() throws Exception {
          MockEndpoint mock = getMockEndpoint("mock:result");
          mock.expectedBodiesReceived("Hello World");
          template.sendBody("direct:start", "World");
          mock.assertIsSatisfied();
      }
  }
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html ; https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java (2026-10-14). Note: `template` is assigned from `contextManager.template()`. Its declaring superclass was not read (Medium).

**3. Treat the CamelContext as one per suite: never stop/start it, never create your own**
> Confidence: 🟢 High | [✓✓ Triangulated | testing guide + source javadoc]
- Why: the guide says one CamelContext is shared and stays started for the whole suite, that returning a new context "throws an exception", and that you can't call `stop()`/`start()`. The `camelContextSupplier` javadoc says "Do not create your own CamelContext instance".
- Code:
  ```java
  // Camel Quarkus 3.40.x — inspect/configure, never replace
  @Inject CamelContext context; // supplied by CamelQuarkusTestSupport
  ```
- Source: same two URLs as pattern 2 (2026-10-14)

**4. Class-wide advice in `@BeforeEach`/`doBeforeEach`; do not call `startRouteDefinitions()` (since 3.36)** ⚠️ Migration Note
> Confidence: 🟢 High | [✓✓ Triangulated | 3.36.0 migration guide + 3.40 testing guide]
- Why: routes that are not advised start automatically once the method completes, and advice is cleaned up between test methods.
- Code:
  ```java
  // Camel Quarkus 3.40.x
  @BeforeEach
  void beforeEach() throws Exception {
      AdviceWith.adviceWith(this.context, "my-kafka-route", route ->
          route.weaveByToUri("kafka:output-topic*").replace().to("mock:kafka-stub"));
  }
  ```
- Hook signature (3.40.0 source): `protected void doBeforeEach(QuarkusTestMethodContext context) throws Exception` (High)
- Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html (2026-10-14)

**5. Per-method advice through `adviceRoute(routeId, advice)`; advise only application routes**
> Confidence: 🟢 High | [✓✓ Triangulated | 3.36.0 migration guide + source at 3.40.0]
- Why: the helper "handles route lifecycle (stop, advice, start) automatically". The javadoc and the guide warn against advising routes from `createRouteBuilder()`, which can behave unpredictably.
- Signature (3.40.0): `protected void adviceRoute(String routeId, ThrowingConsumer<AdviceWithRouteBuilder, Exception> advice) throws Exception`
- Code:
  ```java
  @Test
  void stubbed() throws Exception {
      adviceRoute("my-route", r -> r.weaveById("kafkaProducer").replace().to("mock:stub"));
      // assertions...
  }
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html ; source URL as in pattern 2 (2026-10-14)

**6. `@QuarkusIntegrationTest` subclass for native/packaged runs, talking over network/IPC only**
> Confidence: 🟢 High (docs) / 🟡 Medium (example is main branch)
- Why: the Camel guide says integration tests can't `@Inject` beans or override beans, so communication must use the network, filesystem watching or other IPC, and the test can extend the JVM test class. Quarkus 3.40 says IT supports everything "except injecting into tests", runs with the `prod` profile by default, and ignores `src/test/resources/application.properties`. `CamelQuarkusTestSupport` itself "does not work for native mode tests" (javadoc).
- Code (main-branch example, Medium):
  ```java
  @QuarkusIntegrationTest
  class TimerLogIT extends TimerLogTest { }   // TimerLogTest is a plain @QuarkusTest (no CamelQuarkusTestSupport)
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html ; https://quarkus.io/version/3.40/guides/getting-started-testing (page read for chars 0–100000 of 108136, so Medium for the unread tail) ; https://github.com/apache/camel-quarkus-examples/blob/main/timer-log/src/test/java/org/acme/timer/log/TimerLogIT.java (main branch) (2026-10-14)

### ⚠️ Conditional Patterns

**A. CamelQuarkusTestSupport vs plain `@QuarkusTest` with injected CamelContext/ProducerTemplate**
> Confidence: 🟡 Medium
- Options: A) extend `CamelQuarkusTestSupport`; B) plain `@QuarkusTest` + `@Inject CamelContext`/`ProducerTemplate` + REST Assured/Awaitility (the style of the official examples).

  | Option | Optimizes | Sacrifices | Best When |
  |---|---|---|---|
  | A | mock/AdviceWith helpers, test routes | JVM-only; cannot be reused for an IT | unit-style route logic tests |
  | B | can be reused as a `@QuarkusIntegrationTest` base | no advice helpers | black-box HTTP/file tests, native |

- Agent: "Ask user whether the test must also run against the native/packaged artifact; if yes, choose B for the shared base."
- Source: testing guide (High for the JVM-only limit); the example style is main-branch evidence https://github.com/apache/camel-quarkus-examples (Medium)

**B. State isolation: `@TestProfile` restart vs a shared context**
> Confidence: 🟢 High
- `@TestProfile` restarts the app and the CamelContext. Registry beans bound from a test persist for the suite unless a profile restarts it. Quarkus restarts when "a test has a different profile to the previously run test", and `quarkus.test.class-orderer` groups classes to reduce restarts.
- Tradeoff: isolation vs boot time per profile.
- Agent: "Ask whether cross-class state leakage (registry beans, mock expectations) is acceptable."
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html ; https://quarkus.io/version/3.40/guides/getting-started-testing

**C. External systems: `QuarkusTestResourceLifecycleManager` vs Mockito `@InjectMock`**
> Confidence: 🟢 High (docs) / UNVERIFIED (U3, Camel-bean interplay)
- Test resource: `start()` returns config that takes precedence over `application.properties`. Attach it with `@QuarkusTestResource`, which is global by default (`restrictToAnnotatedClass = true` limits it to the annotated class), or with `@WithTestResource` (scopes `MATCHING_RESOURCES` default, `RESTRICTED_TO_CLASS`, `GLOBAL`).
- `@InjectMock`/`@InjectSpy` need `quarkus-junit-mockito` (test scope).
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html ; https://quarkus.io/version/3.40/guides/getting-started-testing

**D. Registry binding in tests**
> Confidence: 🟡 Medium (guide and source differ in naming)
- Options per the guide: `@Produces @Named` CDI beans; `camelContext.getRegistry().bind(...)` inside `createCamelContext`; `@BindToRegistry` field. The guide says `createCamelRegistry` throws `UnsupportedOperationException`. The 3.40.0 source exposes `protected void bindToRegistry(Registry registry)` and `camelContextSupplier()`, and declares no `createCamelContext` (see I1).
- Source: testing guide + 3.40.0 source URL (2026-10-14)

### 🚫 Forbidden Patterns

**1. `camel-quarkus-junit5` / `org.apache.camel.test.junit5` in 3.40**
> Severity: High
> Confidence: 🟢 High
- Why: renamed in 3.31. The 3.40.0 junit5 artifact is a stub marked "Deprecated".
- Impact: you depend on a deprecated alias, and a stale `junit5` import fails to compile against `camel-test-junit6`.
- ❌ Wrong:
  ```xml
  <artifactId>camel-quarkus-junit5</artifactId>  <!-- import org.apache.camel.test.junit5.* -->
  ```
- ✅ Correct:
  ```xml
  <artifactId>camel-quarkus-junit</artifactId><scope>test</scope> <!-- org.apache.camel.test.junit6.* -->
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html ; junit5 3.40.0 POM (2026-10-14)

**2. Calling `startRouteDefinitions()` after AdviceWith (pre-3.36 idiom)**
> Severity: Medium
> Confidence: 🟢 High
- Why: since 3.36, routes that are not advised start automatically.
- Impact: redundant code carried over from 3.35. Combining it with auto-start is not documented.
- ❌ Wrong:
  ```java
  AdviceWith.adviceWith(context, "my-route", r -> ...);
  startRouteDefinitions();
  ```
- ✅ Correct:
  ```java
  AdviceWith.adviceWith(this.context, "my-route", r -> ...); // routes auto-start after @BeforeEach
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html

**3. Replacing, stopping or starting the CamelContext**
> Severity: High
> Confidence: 🟢 High
- Why: there is one application-scoped context. Returning a new one throws an exception.
- ❌ Wrong:
  ```java
  context.stop(); context.start();
  // or: return new DefaultCamelContext();
  ```
- ✅ Correct:
  ```java
  // isolate with a profile instead
  @QuarkusTest @TestProfile(IsolatedProfile.class)
  class IsolatedTest extends CamelQuarkusTestSupport { }
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html

**4. Wildcard weave patterns such as `weaveByToUri("kafka:*")`**
> Severity: Medium
> Confidence: 🟢 High
- Why: the pattern matches every matching endpoint in the context and can interfere with other routes.
- ❌ Wrong:
  ```java
  route.weaveByToUri("kafka:*").replace().to("mock:x");
  ```
- ✅ Correct:
  ```java
  route.weaveById("kafkaProducer").replace().to("mock:x");
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html

**5. Advising routes from `createRouteBuilder()`**
> Severity: Medium
> Confidence: 🟢 High
- Why: this "can behave unpredictably" (guide). The `adviceRoute` javadoc says the same.
- ❌ Wrong:
  ```java
  @Override protected RoutesBuilder createRouteBuilder() { /* route "t" */ }
  // then: adviceRoute("t", ...)
  ```
- ✅ Correct:
  ```java
  // advise a route defined in src/main (application RouteBuilder);
  // use createRouteBuilder only for test-only routes
  ```
- Source: testing guide + 3.40.0 source

**6. `@Inject` / bean overrides / `CamelQuarkusTestSupport` in `@QuarkusIntegrationTest`**
> Severity: High
> Confidence: 🟢 High
- ❌ Wrong:
  ```java
  @QuarkusIntegrationTest
  class RouteIT extends CamelQuarkusTestSupport { @Inject ProducerTemplate t; }
  ```
- ✅ Correct:
  ```java
  @QuarkusIntegrationTest
  class RouteIT extends RouteHttpTest { }  // base uses REST Assured / files only
  ```
- Source: testing guide; https://quarkus.io/version/3.40/guides/getting-started-testing

**7. Using the deprecated `isUseAdviceWith()` override**
> Severity: Medium
> Confidence: 🟢 High
- Why: it is `@Deprecated(since = "3.15.0")` in the 3.40.0 source, and the javadoc says to advise in `doBeforeEach`.
- ❌ Wrong:
  ```java
  @Override public boolean isUseAdviceWith() { return true; }
  ```
- ✅ Correct:
  ```java
  @BeforeEach void advise() throws Exception { AdviceWith.adviceWith(this.context, "r", b -> ...); }
  ```
- Source: 3.40.0 source URL (pattern 2)

---

## Migration Guide

> Confidence: 🟢 High | Sources: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html (2026-10-14) + https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html (2026-10-14)

**Breaking Changes (3.15 → 3.40)**:
- 3.31: artifact `camel-quarkus-junit5` → `camel-quarkus-junit`; `org.apache.camel.test.junit5` → `org.apache.camel.test.junit6`; `org.apache.camel:camel-test-junit5` → `camel-test-junit6`. The rename aligns with the Quarkus test framework's move from JUnit 5.x to 6.x.
- 3.36: auto-start of routes that are not advised (no `startRouteDefinitions()`), the new `adviceRoute()`, and automatic advice cleanup between test methods.
- Maven Central status: `camel-quarkus-junit5` is missing for 3.34.x, but versions 3.35.0, 3.36.0, 3.38.0, 3.39.0 and 3.40.0 exist (listing https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/; 3.40.0 dated 2026-09-24). The 3.40.0 artifact is a "(Deprecated)" stub that depends on `camel-quarkus-junit`, with no `<relocation>` element. Whether it will be removed in a future release is UNVERIFIED (U2).
- Quarkus side: the Quarkus 3.40 testing guide names `quarkus-junit` and never mentions `quarkus-junit5` (https://quarkus.io/version/3.40/guides/getting-started-testing, High for this statement).

**Upgrade Steps**:
1. Replace `camel-quarkus-junit5` with `camel-quarkus-junit` (test scope).
2. Change imports with `sed -i 's/org.apache.camel.test.junit5/org.apache.camel.test.junit6/g' $(grep -rl 'org.apache.camel.test.junit5' src/test)` (representative).
3. Delete `startRouteDefinitions()` calls that follow AdviceWith. Move per-test advice to `adviceRoute()`.
4. Remove `isUseAdviceWith()` overrides.
5. Run `mvn verify` (JVM tests), then `mvn verify -Dnative` (ITs).

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|---|---|---|---|
| Camel | 4.22.1 | 4.22.x | https://camel.apache.org/camel-quarkus/latest/ (family facts) |
| Quarkus (quarkus-junit) | 3.40.1 | 3.40.x | same source |
| camel-test-junit6 | managed by BOM | — | camel-quarkus-junit 3.40.0 POM |
| GraalVM (native ITs) | 25.0.4.1 | — | family facts |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | official example (main) + official docs]

**Lifecycle** (hook mapping from the testing guide: `afterAll`→`doAfterAll`, `afterEach`/`afterTestExecution`→`doAfterEach`, `beforeAll`→`doAfterConstruct`, `beforeEach`→`doBeforeEach`; signatures from the 3.40.0 source):
```java
// Camel Quarkus 3.40.x
@QuarkusTest
class OrderRouteTest extends CamelQuarkusTestSupport {

    @Override
    protected void doBeforeEach(QuarkusTestMethodContext ctx) throws Exception {
        AdviceWith.adviceWith(this.context, "orders", r ->
            r.weaveById("toErp").replace().to("mock:erp"));
    }   // non-advised routes auto-start afterwards (3.36+)

    @Test
    void routesOrder() throws Exception {
        MockEndpoint erp = getMockEndpoint("mock:erp");
        erp.expectedMessageCount(1);
        template.sendBody("direct:orders", "{\"id\":1}");
        erp.assertIsSatisfied();
    }   // advice cleaned up before the next method

    @Override
    protected void doAfterAll(QuarkusTestContext ctx) throws Exception { }
}
```
Note: `doAfterConstruct` runs before each test under `@TestInstance(Lifecycle.PER_METHOD)` (3.40.0 javadoc).

**Integration**: Camel Quarkus JUnit ↔ REST Assured (platform-http / REST DSL)
```java
// Quarkus 3.40: test HTTP port defaults to 8081 (quarkus.http.test-port; 0 = random); REST Assured base URL auto-configured; timeouts 30 s (quarkus.http.test-timeout)
@QuarkusTest
class HelloHttpTest {
    @Test
    void hello() {
        io.restassured.RestAssured.given().when().get("/hello")
            .then().statusCode(200);
    }
}
@io.quarkus.test.junit.QuarkusIntegrationTest
class HelloHttpIT extends HelloHttpTest { }
```
Source for the port/timeout values: https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14)

**Integration**: Camel Quarkus JUnit ↔ quarkus-junit-mockito
```xml
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-junit-mockito</artifactId><scope>test</scope></dependency>
```
```java
@InjectMock GreetingService service;   // replaces a normal-scoped CDI bean used by a route (U3: Camel-specific behavior UNVERIFIED)
```

**Integration**: test resources (WireMock/Testcontainers)
```java
public class WireMockResource implements QuarkusTestResourceLifecycleManager {
    WireMockServer server;
    public Map<String, String> start() { server = new WireMockServer(0); server.start();
        return Map.of("camel.component.foo.server-url", server.baseUrl()); } // precedence over application.properties
    public void stop() { server.stop(); }
}
@QuarkusTest @QuarkusTestResource(WireMockResource.class)
class FooTest extends CamelQuarkusTestSupport { }
```
Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html

**NotifyBuilder** (`org.apache.camel.builder.NotifyBuilder`, "only intended for testing purposes", Java DSL only):
```java
NotifyBuilder notify = new NotifyBuilder(context).whenDone(1).create();
template.sendBody("direct:orders", "x");
assertTrue(notify.matches(10, TimeUnit.SECONDS));
```
Source: https://camel.apache.org/manual/notify-builder.html (unversioned manual page, links to 4.22.x → Medium). The Camel Quarkus 3.40 testing guide and the 3.40.0 source do not mention NotifyBuilder. Its behavior against the shared suite context is UNVERIFIED (U1). Note that the manual sample uses the no-arg constructor; passing `context` is an adaptation.

**Routes loaded in tests**: all application RouteBuilders plus the XML/YAML matched by `camel.main.routes-include-pattern`. Filter them with `quarkus.camel.routes-discovery.include-patterns|exclude-patterns` and `camel.main.routes-include-pattern|routes-exclude-pattern` (testing guide, High).

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment
mvn dependency:tree -Dincludes=org.apache.camel.quarkus:camel-quarkus-junit*
# Expected: camel-quarkus-junit:3.40.x:test ; no camel-quarkus-junit5
grep -rn "org.apache.camel.test.junit5\|startRouteDefinitions\|isUseAdviceWith" src/test
# Expected: no output
mvn verify                 # @QuarkusTest (JVM)
mvn verify -Dnative        # @QuarkusIntegrationTest via maven-failsafe-plugin (integration-test, verify; native.image.path=${project.build.directory}/${project.build.finalName}-runner)
# Expected: BUILD SUCCESS
```
Failsafe/native details: https://quarkus.io/version/3.40/guides/getting-started-testing (surefire version must be set explicitly: "the default version does not support JUnit").

**Mocking**:
```java
// Camel Quarkus 3.40.x — replace a consumer and an outbound endpoint
adviceRoute("orders", r -> {
    r.replaceFromWith("direct:in");
    r.weaveById("toErp").replace().to("mock:erp");
});
```
`replaceFromWith` and `weaveById` are standard AdviceWith operations. The testing guide documents `weaveByToUri`/`weaveById`; `replaceFromWith` is not shown on the 3.40 Camel Quarkus page and comes from the Camel AdviceWith manual (Medium).

---

## Production Readiness

- **Performance**: each distinct `@TestProfile` restarts Quarkus. Group profiles with `quarkus.test.class-orderer` (Quarkus 3.40 guide).
- **Scalability**: one CamelContext per suite. Registry bindings and mock state can leak across classes (testing guide).
- **Monitoring**: assert on `MockEndpoint`/`NotifyBuilder`. Native ITs observe only network/file/log output (e.g. `target/quarkus.log` in the main-branch timer-log example, Medium).
- **Security**: test resources must inject credentials via `start()` config maps and not commit them to `application.properties`. Integration tests ignore `src/test/resources/application.properties` and run with the `prod` profile (`quarkus.test.integration-test-profile`).

---

## Reference Implementations

- https://github.com/apache/camel-quarkus-examples — 36 examples (main branch, Medium). `timer-log` has `TimerLogTest` (`@QuarkusTest`, Awaitility on `target/quarkus.log`) and `TimerLogIT extends TimerLogTest` (`@QuarkusIntegrationTest`).
- https://github.com/apache/camel-quarkus/tree/3.40.0/test-framework — `camel-quarkus-junit` plus `camel-quarkus-junit-tests` (the subdirectory list was read on main).
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html — canonical patterns.

---

## Source Bibliography

**Primary** (all fetched 2026-10-14):
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html (versioned, High)
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html (High)
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html (High)
- https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java (tag source, High)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit/3.40.0/camel-quarkus-junit-3.40.0.pom (High)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/3.40.0/camel-quarkus-junit5-3.40.0.pom (High)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/ (listing, High)
- https://quarkus.io/version/3.40/guides/getting-started-testing (versioned; first 100000 of 108136 chars read)
- https://camel.apache.org/manual/notify-builder.html (unversioned, Medium)
- workspace/_family_facts_v3.40.md (orchestrator-verified; release/LTS/version rows)

**Validation**: https://github.com/apache/camel-quarkus-examples (main branch, Medium); workspace/research_Camel_Quarkus_Core_v3.40.md (pilot; its junit claims were re-checked here, and its "package UNVERIFIED" and "junit5 3.40.0 status UNVERIFIED" items are now resolved).

**All Deep-Links**: listed above, by section.

---

## Research Gaps

```
Gap: Unverified list (count 3)
U1: NotifyBuilder behavior against the shared CamelQuarkusTestSupport context (not mentioned in the 3.40 guide or source)
U2: Future removal date of the camel-quarkus-junit5 stub (3.31 promised removal at 3.34; stub still published at 3.40.0)
U3: @InjectMock interplay with Camel-referenced beans (e.g. beans looked up by name from routes) — Quarkus documents @InjectMock generically only
Impact: Medium — tests may be flaky or break on upgrade
Workaround: prefer MockEndpoint/AdviceWith; depend on camel-quarkus-junit only
Follow-up: camel-quarkus GitHub issues / next migration guides
```

```
Gap: IRRESOLVABLE list (count 2)
I1: Whether `createCamelContext()` is overridable in 3.40 — the 3.40 guide shows overriding it with super, but the 3.40.0 CamelQuarkusTestSupport source declares no such method (only camelContextSupplier / bindToRegistry; AbstractTestSupport not read)
I2: Camel Quarkus 3.40 LTS end date (blank "LTS Until" column; family facts)
Impact: I1 — guide sample may not compile; I2 — support planning
Workaround: I1 — configure via CDI/@BindToRegistry or test-compile once; I2 — plan against Quarkus 2027-09-30 as an inference
Follow-up: read AbstractTestSupport at tag 3.40.0; watch camel.apache.org/releases
§7-ref: Iteration 3 — IRRESOLVABLE (I1); Iteration 1 — IRRESOLVABLE (I2)
```

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|---|---|---|---|---|
| 1 | Guardrails | Package of CamelQuarkusTestSupport = `org.apache.camel.quarkus.test` | Resolved | 3.40.0 tag source (2026-10-14) |
| 1 | Guardrails | `doBeforeEach(QuarkusTestMethodContext)` parameter type | Resolved | 3.40.0 tag source |
| 1 | Guardrails | `adviceRoute(String, ThrowingConsumer<AdviceWithRouteBuilder, Exception>)` | Resolved | 3.40.0 tag source + 3.36.0 migration guide |
| 1 | Migration | camel-quarkus-junit5 3.40.0 = deprecated stub depending on camel-quarkus-junit, no relocation (overrides the family-facts "Unverified" row) | Resolved | junit5 3.40.0 POM |
| 1 | Metadata | Camel Quarkus LTS end date | ⚠️ IRRESOLVABLE — not published (I2) | — |
| 2 | Guardrails | Native-mode testing covered by the Camel testing guide (`@QuarkusIntegrationTest`, no injection) | Resolved | 3.40 testing guide |
| 2 | Blueprint | NotifyBuilder package/API | Resolved (Medium); Quarkus-context behavior left as U1 | manual/notify-builder.html |
| 3 | Guardrails | `createCamelContext` guide vs source conflict | ⚠️ IRRESOLVABLE — superclass source unread, docs contradict source (I1) | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Standard)
- [x] All scope areas cited (dependency, base class vs plain test, AdviceWith 3.36, mocks, profiles/resources, one context, native IT, JVM-only, REST Assured)
- [x] Pattern counts driven by domain needs
- [x] Every anti-pattern has an alternative
- [x] All CLI commands marked as representative
- [x] Integration examples complete (quarkus-junit, mockito, REST Assured, core, direct/mock)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns triangulated or downgraded (pattern 6 partly Medium)
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score calculated
- [x] Every Research Gap cross-referenced in §7

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: artifact `camel-quarkus-junit` (test); package `org.apache.camel.quarkus.test`; one shared JVM-only context; 3.36 auto-start/cleanup and `adviceRoute`; IT without injection.
- **Medium Confidence (validate with user)**: plain `@QuarkusTest` + IT reuse style (main-branch examples); NotifyBuilder; `replaceFromWith` (Camel manual, not on the 3.40 page); registry-binding options.
- **Low Confidence (must ask human)**: U1–U3; I1 (`createCamelContext`); I2 (LTS end date).
- **Edge Cases (pause)**: 3.40.0 was released 2026-09-28, 16 days before this research; Quarkus 4 is in beta (no Camel Quarkus build is known).
- **Emergency Stop**: none triggered.
