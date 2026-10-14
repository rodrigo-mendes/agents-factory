# Research: Quarkus JUnit (quarkus-junit) — Quarkus 3.40.x LTS

> Research run: framework-researcher, skill `researching-technical-frameworks`, depth=deep, MAX_ITERATIONS=3, date 2026-10-14.
> Plan-approval step (P3 EnterPlanMode/ExitPlanMode) was SKIPPED: this is a forked batch run approved by the user upstream, with no user available inside this run.
> Section-investigators and research-synthesizer were NOT used (orchestrator constraint); all pages were fetched directly by this agent with WebFetch/WebSearch on 2026-10-14.
> Confidence tags: **High** = versioned 3.40 page, or official source plus Maven Central artifact; **Medium** = unversioned, wiki-only, or partly-read page; **UNVERIFIED** = no official page confirms it.

---

## Metadata

```yaml
Full_Name: Quarkus JUnit test framework (io.quarkus:quarkus-junit, formerly quarkus-junit5)
Target_Version: Quarkus 3.40.x (artifact checked 3.40.1)
Release_Date: 2026-09-30 (Quarkus 3.40 LTS) — High — https://quarkus.io/releases (orchestrator fact)
Support_Status: LTS, community-maintained until 2027-09-30 — High — https://quarkus.io/releases (orchestrator fact)
Primary_Docs: https://quarkus.io/version/3.40/guides/getting-started-testing
Official_Repo: https://github.com/quarkusio/quarkus (tag 3.40.1)
Research_Date: 2026-10-14
Domain_Complexity: Standard
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 3
Unverified_Count: 3
Irresolvable_Count: 3
Research_Quality_Score: 87%   # 46 tracked claims, 3 unverified, 3 irresolvable: (46-6)/46
```

---

## Executive Summary

Quarkus JUnit is the Quarkus test framework for JUnit Jupiter. Its main entry points are `@QuarkusTest` (JVM tests that run inside the Quarkus application and are CDI beans), `@QuarkusIntegrationTest` (black-box tests against the built jar, native binary or container), and `@QuarkusMainTest` (command-mode applications). The framework also provides test profiles (`QuarkusTestProfile`), test resources (`QuarkusTestResourceLifecycleManager` with `@QuarkusTestResource` or `@WithTestResource`), automatic Dev Services in test mode, and Mockito integration through `quarkus-junit-mockito` (`@InjectMock`, `@InjectSpy`). In 3.40, the test dependency documented in the versioned guide is `io.quarkus:quarkus-junit` with `test` scope (High, https://quarkus.io/version/3.40/guides/getting-started-testing).

Compared with 3.15-era conventions, the big change came in Quarkus **3.31**. Quarkus moved from JUnit 5 to **JUnit 6**, and every `*-junit5` artifact was renamed to `*-junit`. For example, `quarkus-junit5` became `quarkus-junit` and `quarkus-junit5-mockito` became `quarkus-junit-mockito` (High, https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31). In 3.40.1, `quarkus-junit5` still resolves on Maven Central, but only as a **relocation POM** that points to `quarkus-junit` (High, https://repo1.maven.org/maven2/io/quarkus/quarkus-junit5/3.40.1/quarkus-junit5-3.40.1.pom). The Quarkus 3.40.1 BOM pins `junit.jupiter.version` = **6.1.3** and `mockito.version` = **5.21.0** (High, https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/bom/application/pom.xml). Release 3.31 also removed `quarkus.https.test-port` and the `System.getProperty("quarkus.http.test-port")` / `test.url` lookups (High, Migration-Guide-3.31).

The three critical guardrails are:
1. Use `quarkus-junit` (and `quarkus-junit-mockito`), not the `-junit5` names.
2. `@InjectMock` works only on normal-scoped beans. A `@Singleton` bean needs `@MockitoConfig(convertScopes = true)`. Beans used during startup are not affected by mocks (High, versioned guide).
3. Every distinct `@TestProfile` restarts the application, so tests should be grouped by profile. Do not run `@QuarkusTest` and `@QuarkusIntegrationTest` in the same execution (High, versioned guide).

The tier is **Standard**: there are several integrations (Mockito, REST Assured, Camel, Dev Services, JaCoCo) and lifecycle subtleties, but no security-critical surface.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**AD-1 Use `io.quarkus:quarkus-junit` (test scope), not `quarkus-junit5`**
> Confidence: 🟢 High | [✓✓ Triangulated | Migration-Guide-3.31 (2026-10-14 fetch) + Maven Central relocation POM 3.40.1 (2026-10-14) + versioned 3.40 testing guide]
- Why: The 3.31 migration guide states "we renamed all our existing `-junit5` artifacts to `-junit`". The 3.40 guide lists only `quarkus-junit` + `rest-assured`, both `test` scope.
- Code (Quarkus 3.40):
  ```xml
  <dependency>
    <groupId>io.quarkus</groupId>
    <artifactId>quarkus-junit</artifactId>
    <scope>test</scope>
  </dependency>
  <dependency>
    <groupId>io.rest-assured</groupId>
    <artifactId>rest-assured</artifactId>
    <scope>test</scope>
  </dependency>
  ```
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14); https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 (2026-10-14)

**AD-2 Configure Surefire with a JUnit-capable version, JBoss LogManager, and late-bound `@{argLine}`**
> Confidence: 🟢 High | [✓✓ Triangulated | 3.40 testing guide + Migration-Guide-3.31 + 3.40 tests-with-coverage]
- Why: The 3.40 guide says the default Surefire version does not support JUnit and sets `java.util.logging.manager`. Since 3.31, Quarkus passes extra JVM arguments, so any custom `<argLine>` must begin with `@{argLine}`. JaCoCo also requires late evaluation.
- Code:
  ```xml
  <plugin>
    <artifactId>maven-surefire-plugin</artifactId>
    <version>${surefire-plugin.version}</version> <!-- concrete value: UNVERIFIED, the guide uses a placeholder -->
    <configuration>
      <systemPropertyVariables>
        <java.util.logging.manager>org.jboss.logmanager.LogManager</java.util.logging.manager>
      </systemPropertyVariables>
      <argLine>@{argLine} -Xmx256m</argLine>
    </configuration>
  </plugin>
  ```
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing ; https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 ; https://quarkus.io/version/3.40/guides/tests-with-coverage (all 2026-10-14)

**AD-3 Mock only normal-scoped beans with `@InjectMock` (from `quarkus-junit-mockito`)**
> Confidence: 🟢 High | [✓✓ Triangulated | 3.40 testing guide + Migration-Guide-3.31 artifact table]
- Why: The 3.40 guide says `@InjectMock` requires `quarkus-junit-mockito` and normal-scoped beans. `@Singleton` needs `@MockitoConfig(convertScopes = true)`, which the guide says to use only "with full understanding" of the scope change. Beans used during startup are not affected, so use an `@Alternative` for those.
- Code (Quarkus 3.40):
  ```java
  @QuarkusTest
  class GreetingTest {
      @InjectMock                       // bean must be @ApplicationScoped/@RequestScoped
      GreetingService service;

      @InjectMock
      @MockitoConfig(convertScopes = true) // only for @Singleton beans
      LegacySingleton legacy;

      @Test
      void greets() {
          Mockito.when(service.greet()).thenReturn("mocked");
          given().when().get("/hello").then().body(is("mocked"));
      }
  }
  ```
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14)

**AD-4 Group tests by profile; a different `@TestProfile` restarts Quarkus**
> Confidence: 🟡 Medium (single source: versioned guide)
- Why: The guide says: "If a test has a different profile to the previously run test then Quarkus will be shut down and started". The Quarkus orderer groups tests that need the same application instance. Use `quarkus.test.profile.tags` to select profiles in CI.
- Code:
  ```java
  public class MockedProfile implements QuarkusTestProfile {
      @Override public Map<String, String> getConfigOverrides() { return Map.of("greeting.prefix", "test"); }
      @Override public Set<Class<?>> getEnabledAlternatives() { return Set.of(FakeClock.class); }
      @Override public Set<String> tags() { return Set.of("mocked"); }
  }
  @QuarkusTest @TestProfile(MockedProfile.class)
  class MockedTest { /* ... */ }
  ```
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14)

**AD-5 Separate `@QuarkusTest` and `@QuarkusIntegrationTest` executions**
> Confidence: 🟡 Medium (single source)
- Why: The guide says the two should not run in the same execution and recommends splitting them on the `io.quarkus.test.junit.QuarkusTest` tag. `@QuarkusIntegrationTest` runs the packaged artifact, in the `prod` profile by default (changeable with `quarkus.test.integration-test-profile`), and does not support injection.
- Code:
  ```java
  @QuarkusIntegrationTest
  class GreetingIT extends GreetingTest { } // reuse HTTP-only assertions; no @Inject
  ```
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14)

**AD-6 Use `@TestHTTPResource` / `@TestHTTPEndpoint` or the `HttpServer` API, never system properties, to find the test URL**
> Confidence: 🟢 High | [✓✓ Triangulated? no: 2 sources but different claims] downgraded to 🟡 Medium
- Why: The 3.40 guide documents `@TestHTTPResource` (URI/URL/String) and `@TestHTTPEndpoint`. The 3.31 guide says `System.getProperty("quarkus.http.test-port"/"test.url")` "will no longer work", and to inject `io.quarkus.vertx.http.HttpServer` instead.
- Code:
  ```java
  @TestHTTPEndpoint(GreetingResource.class)
  @TestHTTPResource
  URL url;
  ```
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing ; https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 (2026-10-14)

### ⚠️ Conditional Patterns

**CP-1 Mocking strategy: `@Alternative`/`@Mock` vs `QuarkusMock` vs `@InjectMock`/`@InjectSpy`**
> Confidence: 🟢 High (versioned guide)
- Options: A) CDI `@Alternative`/`@Mock` in `src/test/java`; B) `QuarkusMock.installMockForType` (in `@BeforeAll`) or `installMockForInstance` (per test), which does not need Mockito; C) `@InjectMock`; D) `@InjectSpy`, where the real bean and its observers still run.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A Alternative | Works for startup-time beans | Global to all tests | Bean used during boot |
  | B QuarkusMock | No Mockito; per class/test | Manual fakes | Simple hand-written fakes |
  | C @InjectMock | Mockito stubbing per test | Normal scope only; no startup beans | Typical unit-ish tests |
  | D @InjectSpy | Real behaviour + verify | Observers still fire | Verify calls on real bean |

- Agent: "Ask user whether the bean is used at startup and which scope it has."
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14)

**CP-2 Test resource scoping: `@QuarkusTestResource` vs `@WithTestResource`**
> Confidence: 🟡 Medium
- Options: `@QuarkusTestResource` is global unless `restrictToAnnotatedClass = true`, and `parallel = true` starts resources concurrently. `@WithTestResource(scope = MATCHING_RESOURCES (default) | RESTRICTED_TO_CLASS | GLOBAL)` groups tests by resource set.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | @QuarkusTestResource (global) | Single startup | Leaks into all tests | One shared DB/broker |
  | @WithTestResource MATCHING_RESOURCES | Isolation + reuse by group | More restarts | Mixed resource needs |
  | RESTRICTED_TO_CLASS | Strict isolation | Restart per class | Destructive resources |

- Note: The 3.40 page does **not** call `@QuarkusTestResource` deprecated (Medium, absence of evidence).
- Agent: "Ask user whether resources must be isolated per class."
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14)

**CP-3 Dev Services vs explicit test resources**
> Confidence: 🟢 High (versioned dev-services guide)
- Options: Dev Services (automatic in dev and test, for "unconfigured services", need a container environment, disabled when connection config such as a JDBC URL is set, or globally with `quarkus.devservices.enabled=false`) vs a `QuarkusTestResourceLifecycleManager`. Values returned from the manager's `start()` have higher precedence than `application.properties` (Camel testing guide).
- Agent: "Ask user whether CI has a container runtime and whether connection config is pinned."
- Source: https://quarkus.io/version/3.40/guides/dev-services ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html (2026-10-14)

**CP-4 Test port: fixed 8081 vs random**
> Confidence: 🟢 High
- Default `quarkus.http.test-port` = 8081, with `quarkus.http.test-ssl-port` alongside it. A value of `0` picks a random port. The REST Assured timeout `quarkus.http.test-timeout` defaults to 30s. Source for all: https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14).
- Agent: "Ask whether tests run in parallel CI agents on the same host; if so use 0."

### 🚫 Forbidden Patterns

**NP-1 Using `-junit5` artifact names in 3.40**
> Severity: Medium
> Confidence: 🟢 High
- Why: Since 3.31 they are relocation POMs ("Update the artifactId in your project build file."). The retention period is undocumented (IRRESOLVABLE-2).
- Impact: Relocation warnings now, and a build break when the relocations are removed.
- ❌ Wrong:
  ```xml
  <artifactId>quarkus-junit5</artifactId>
  <artifactId>quarkus-junit5-mockito</artifactId>
  ```
- ✅ Correct:
  ```xml
  <artifactId>quarkus-junit</artifactId>
  <artifactId>quarkus-junit-mockito</artifactId>
  ```
- Source: https://repo1.maven.org/maven2/io/quarkus/quarkus-junit5/3.40.1/quarkus-junit5-3.40.1.pom ; https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 (2026-10-14)

**NP-2 `@InjectMock` on a `@Singleton`/`@Dependent` bean without `convertScopes`, or on a startup bean**
> Severity: High
> Confidence: 🟢 High
- Why: Only normal-scoped beans can be mocked, and beans used during startup are not affected.
- Impact: Test failures, or the real bean runs silently.
- ❌ Wrong:
  ```java
  @Singleton class Clock {}           // in test:
  @InjectMock Clock clock;            // fails / not applied
  ```
- ✅ Correct:
  ```java
  @InjectMock @MockitoConfig(convertScopes = true) Clock clock;
  // or make Clock @ApplicationScoped; or use an @Alternative for startup-time beans
  ```
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14)

**NP-3 Reading test port/URL via system properties, or using `quarkus.https.test-port`**
> Severity: High
> Confidence: 🟢 High
- Why: Release 3.31 removed `quarkus.https.port`/`quarkus.https.test-port`, and the system property lookups "will no longer work".
- ❌ Wrong:
  ```java
  int port = Integer.getInteger("quarkus.http.test-port");
  ```
  ```properties
  quarkus.https.test-port=8444
  ```
- ✅ Correct:
  ```java
  @TestHTTPResource URL url;   // or @Inject io.quarkus.vertx.http.HttpServer server;
  ```
  ```properties
  quarkus.http.test-ssl-port=8444
  ```
- Source: https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 ; https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14)

**NP-4 Injecting beans or `@InjectMock` in `@QuarkusIntegrationTest` / `@QuarkusMainTest`**
> Severity: Medium
> Confidence: 🟢 High
- Why: `@QuarkusIntegrationTest` cannot inject. `@QuarkusMainTest` does not support CDI injection, Panache entities, or `@InjectMock`; mock through test profiles instead.
- ❌ Wrong:
  ```java
  @QuarkusMainTest class CliTest { @Inject Service s; @InjectMock Repo r; }
  ```
- ✅ Correct:
  ```java
  @QuarkusMainTest @TestProfile(FakeRepoProfile.class)
  class CliTest {
      @Test @Launch(value = {"--name", "x"}, exitCode = 0)
      void runs(LaunchResult result) { assertTrue(result.getOutput().contains("x")); }
  }
  ```
- Source: https://quarkus.io/version/3.40/guides/command-mode-reference ; https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14)

**NP-5 Different profiles/resources on `@Nested` classes; production `@Alternative` mocks in `src/main`**
> Severity: Medium
> Confidence: 🟢 High
- ❌ Wrong:
  ```java
  @QuarkusTest class Outer { @Nested @TestProfile(Other.class) class Inner {} }
  // src/main/java/.../MockService.java  @Mock @ApplicationScoped
  ```
- ✅ Correct:
  ```java
  @QuarkusTest @TestProfile(Other.class) class OtherTest {}  // separate top-level class
  // src/test/java/.../MockService.java
  ```
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14)

**NP-6 Camel: stopping/starting CamelContext or advising `createRouteBuilder()` routes**
> Severity: Medium
> Confidence: 🟢 High
- ❌ Wrong:
  ```java
  context.stop(); context.start();               // in CamelQuarkusTestSupport
  AdviceWith.adviceWith(context, "*", a -> a.weaveByToUri("kafka:*")...);
  ```
- ✅ Correct:
  ```java
  // restart via a distinct @TestProfile; advise existing app routes by id in doBeforeEach
  AdviceWith.adviceWith(context, "orders", a -> a.weaveById("send").replace().to("mock:out"));
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html (2026-10-14)

---

## Migration Guide

> Confidence: 🟢 High | Sources: https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 (fetched 2026-10-14) + https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html (orchestrator fact)

**Breaking changes (3.15 → 3.40), all introduced in 3.31:**
- JUnit 5 → JUnit 6 ("We updated to JUnit 6 in place of JUnit 5."). The 3.40.1 BOM uses `junit.jupiter.version` 6.1.3 (bom/application/pom.xml @3.40.1).
- Artifact renames: `quarkus-junit5`→`quarkus-junit`, `-junit5-component`→`-junit-component`, `-junit5-config`→`-junit-config`, `-junit5-internal`→`-junit-internal`, `-junit5-mockito`→`-junit-mockito`, `-junit5-mockito-config`→`-junit-mockito-config`, `io.quarkus.junit5:junit5-virtual-threads`→`io.quarkus.junit:junit-virtual-threads`. Relocations are in place.
- Custom Surefire/Failsafe `<argLine>` must include `@{argLine}`.
- Testcontainers 2: some artifacts and packages were renamed (handled by `quarkus update`).
- Removed `quarkus.https.port` / `quarkus.https.test-port`. Port lookups through `System.getProperty` no longer work.
- Removed `quarkus-test-amazon-lambda` / `LambdaClient` (use REST Assured).
- Camel: `camel-quarkus-junit5`→`camel-quarkus-junit`, packages `org.apache.camel.test.junit5`→`org.apache.camel.test.junit6`. The old artifact is kept "until Camel Quarkus 3.34.0" (High, orchestrator fact). Whether `camel-quarkus-junit5` 3.40.0 still resolves is UNVERIFIED (orchestrator fact).

**Upgrade Steps:**
1. `quarkus update --stream=3.40` (Representative). The 3.31 guide says the renames are "handled automatically".
2. Replace the `-junit5` artifactIds in your POMs (NP-1).
3. Prefix any `<argLine>` with `@{argLine}`.
4. Replace system-property port lookups with `@TestHTTPResource` or the `HttpServer` API.
5. For Camel tests, switch to `camel-quarkus-junit` and the `org.apache.camel.test.junit6` imports.

**Compatibility Matrix:**

| Dependency | Version in 3.40.1 | Notes / Source |
|------------|-------------------|----------------|
| JUnit Jupiter | 6.1.3 | High — https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/bom/application/pom.xml |
| Mockito | 5.21.0 | High — same URL |
| REST Assured | UNVERIFIED (U-2) | property not reached in the fetched portion of the BOM |
| Camel Quarkus | 3.40.x on Quarkus 3.40.1 / Camel 4.22.1 | High — https://camel.apache.org/camel-quarkus/latest/ (orchestrator fact) |
| AOT cache test run | JDK 25+ for `quarkus.package.jar.aot.enabled=true` | High — https://quarkus.io/version/3.40/guides/getting-started-testing |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | versioned 3.40 testing guide + Camel Quarkus 3.40.x testing guide]

**Lifecycle (Quarkus 3.40):** Quarkus starts once per test run and is restarted only when the next test has a different profile. `@QuarkusTest` classes are CDI beans. Hang detection defaults to 10 minutes (`quarkus.test.hang-detection-timeout`). Debug arguments go in `quarkus.test.arg-line`. Source: https://quarkus.io/version/3.40/guides/getting-started-testing.

```java
// Quarkus 3.40 — @QuarkusTest with REST Assured, injection, transactional rollback
@QuarkusTest
@TestHTTPEndpoint(GreetingResource.class)
class GreetingResourceTest {
    @Inject GreetingService service;          // tests are CDI beans

    @Test
    void hello() {
        given().when().get().then().statusCode(200).body(is("hello"));  // port 8081 by default
    }

    @Test @TestTransaction                    // rolled back at end of test
    void persists() { /* ... */ }
}

// Test resource
public class PostgresResource implements QuarkusTestResourceLifecycleManager {
    @Override public Map<String, String> start() { /* start container */ return Map.of("quarkus.datasource.jdbc.url", "..."); }
    @Override public void stop() { }
}
@QuarkusTest @WithTestResource(value = PostgresResource.class) // scope defaults to MATCHING_RESOURCES
class RepoTest { }
```

**Conditional execution:** `@EnabledIfConfig`/`@DisabledIfConfig` resolve values through MicroProfile Config. Stacked `@EnabledIfConfig` uses AND logic and stacked `@DisabledIfConfig` uses OR logic. Neither annotation is `@Inherited` (High, versioned guide).

**Dev Services context:** objects implementing `io.quarkus.test.common.DevServicesContext.ContextAware` can be injected with the Dev Services context, which also exposes the container network id (High, versioned guide, tail section).

**Integration**: Quarkus JUnit ↔ camel-quarkus-junit (3.40.x)
```java
// Camel Quarkus 3.40.x — JVM mode only
@QuarkusTest
class OrdersRouteTest extends CamelQuarkusTestSupport {
    @Override public boolean isUseAdviceWith() { return true; }
    @Override protected void doBeforeEach(QuarkusTestContext ctx) throws Exception {
        AdviceWith.adviceWith(context, "orders", a -> a.weaveById("send").replace().to("mock:out"));
    }
    @Test void routes() throws Exception {
        MockEndpoint out = getMockEndpoint("mock:out");
        out.expectedBodiesReceived("x");
        template.sendBody("direct:orders", "x");
        out.assertIsSatisfied();
    }
}
```
Rules (High, https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html):
- Add `camel-quarkus-junit` with test scope.
- There is one shared `CamelContext`, and a restart needs a `@TestProfile`.
- Override `createCamelContext` only by calling `super.createCamelContext()`.
- `createCamelRegistry` throws `UnsupportedOperationException`; use CDI producers, `@BindToRegistry`, or `getRegistry().bind`.
- `beforeAll` maps to `doAfterConstruct` and `beforeEach` maps to `doBeforeEach`.
- Advice is cleaned up between test methods.
- Under `@QuarkusIntegrationTest` native runs, these options do not work.

**Integration**: Quarkus JUnit ↔ @QuarkusMainTest (command mode)
```java
@QuarkusMainTest
class CliTest {
    @Test @Launch(value = {}, exitCode = 1)
    void failsWithoutArgs(LaunchResult r) { }
    @Test void manual(QuarkusMainLauncher launcher) { LaunchResult r = launcher.launch("--x"); }
}
```
Source: https://quarkus.io/version/3.40/guides/command-mode-reference (High). `@QuarkusMainIntegrationTest` runs the built jar or native executable.

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment
./mvnw test                                   # @QuarkusTest via Surefire
./mvnw verify -Dnative                        # @QuarkusIntegrationTest via Failsafe (native)
./mvnw quarkus:test                           # continuous testing without dev mode
./mvnw quarkus:dev                            # then press r to run tests, b for broken-only
./mvnw test -Dquarkus.test.profile.tags=mocked
./mvnw dependency:tree | grep -E "quarkus-junit5|junit-jupiter"
# Expected: no quarkus-junit5; junit-jupiter 6.1.3 on Quarkus 3.40.1
```

**Continuous testing (High, https://quarkus.io/version/3.40/guides/continuous-testing):**
- `quarkus.test.continuous-testing` = `paused` (default) | `enabled` | `disabled`.
- `quarkus.test.exclude-tags` defaults to `slow` and is ignored when `include-tags` is set.
- `quarkus.test.exclude-pattern` defaults to `.*\.IT[^.]+|.*IT|.*ITCase`.
- `quarkus.test.only-test-application-module=true` disables multi-module support.
- `quarkus.test.flat-class-path` is incompatible with continuous testing.
- The Dev UI is not available in `quarkus:test`.

**Coverage (High, https://quarkus.io/version/3.40/guides/tests-with-coverage):**
- Add `io.quarkus:quarkus-jacoco` with test scope. Its automatic configuration works only for `@QuarkusTest`.
- Defaults: `quarkus.jacoco.data-file` = `target/jacoco-quarkus.exec`; `report-location` = `target/jacoco-report` (the page also says `target/jacoco-reports`, IRRESOLVABLE-3).
- Coverage is not supported in native mode.
- Integration-test coverage needs a jar artifact and `quarkus.package.write-transformed-bytecode-to-build-output=true` (use with caution).

**Mocking**:
```java
@QuarkusTest
class SpyTest {
    @InjectSpy GreetingService spy;           // real bean; observers still invoked
    @Test void verifies() { get("/hello"); Mockito.verify(spy).greet(); }
}
@QuarkusTest
class QuarkusMockTest {
    @BeforeAll static void setup() { QuarkusMock.installMockForType(new FakeClock(), Clock.class); }
}
```

---

## Production Readiness

- **Performance**: Each distinct test profile or resource set costs one full application restart, so minimize the number of profiles (High, versioned guide). Concurrent resource startup is available with `@QuarkusTestResource(parallel = true)`. JUnit parallel test execution is not documented on the 3.40 page (IRRESOLVABLE-1).
- **Scalability (CI)**: Use `quarkus.http.test-port=0` for random ports on shared hosts. Split Surefire (unit/`@QuarkusTest`) from Failsafe (`@QuarkusIntegrationTest`). Dev Services need a container runtime, and container sharing applies only in dev mode (High, dev-services guide). Behaviour of Dev Services across profile restarts is UNVERIFIED (U-1).
- **Monitoring**: hang detection (`quarkus.test.hang-detection-timeout`, default 10 min); JaCoCo reports.
- **Security**: Keep `@Alternative`/`@Mock` beans in `src/test/java` only. Never ship Dev Services settings as production config. Dev Services live in deployment modules and do not affect production (High, dev-services guide).

---

## Reference Implementations

- Quarkus 3.40 testing guide: https://quarkus.io/version/3.40/guides/getting-started-testing
- Command mode testing: https://quarkus.io/version/3.40/guides/command-mode-reference
- Continuous testing: https://quarkus.io/version/3.40/guides/continuous-testing
- Coverage: https://quarkus.io/version/3.40/guides/tests-with-coverage
- Dev Services: https://quarkus.io/version/3.40/guides/dev-services
- Camel Quarkus testing: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
- Quarkus quickstarts (main branch, Medium): https://github.com/quarkusio/quarkus-quickstarts

---

## Source Bibliography

**Primary** (all fetched 2026-10-14):
- https://quarkus.io/version/3.40/guides/getting-started-testing (versioned; read in full in two passes)
- https://quarkus.io/version/3.40/guides/command-mode-reference (versioned; testing section)
- https://quarkus.io/version/3.40/guides/continuous-testing (versioned)
- https://quarkus.io/version/3.40/guides/tests-with-coverage (versioned)
- https://quarkus.io/version/3.40/guides/dev-services (versioned; first 100k chars read, so Medium for anything beyond that)
- https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 (official wiki, unversioned page about a specific version)
- https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/bom/application/pom.xml (tag 3.40.1; first 100k chars)
- https://repo1.maven.org/maven2/io/quarkus/quarkus-junit5/3.40.1/quarkus-junit5-3.40.1.pom (relocation POM)
- https://repo1.maven.org/maven2/io/quarkus/quarkus-junit5/maven-metadata.xml (versions up to 4.0.0.Beta1)
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html (versioned)
- workspace/_family_facts_v3.40.md (orchestrator-verified facts, used verbatim)

**Validation** (not used as evidence): an OpenRewrite `quarkus331/JUnitRelocations` recipe page appeared in search results. It is consistent with the 3.31 table but is not an official Quarkus source.

**All Deep-Links**: as above. The old v3.15 file was used only as a topic checklist.

---

## Research Gaps

```
Gap: IRRESOLVABLE-1 — Support for JUnit Jupiter parallel test execution with @QuarkusTest
Impact: Enabling junit.jupiter.execution.parallel may break shared app/profile lifecycle
Workaround: Run Quarkus tests sequentially; parallelize only at the module/fork level; use @QuarkusTestResource(parallel=true) for resource startup
Follow-up: quarkusio/quarkus GitHub issues/discussions on parallel execution
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: IRRESOLVABLE-2 — How long the quarkus-junit5 (and other -junit5) relocation POMs are kept
Impact: Builds using old names will break on removal (4.0 likely, not documented)
Workaround: Migrate to quarkus-junit now
Follow-up: Quarkus 4.0 migration guide when final
§7-ref: Iteration 2 — IRRESOLVABLE
```
```
Gap: IRRESOLVABLE-3 — JaCoCo default report directory: page states both target/jacoco-report and target/jacoco-reports
Impact: CI report upload paths may be wrong
Workaround: Set quarkus.jacoco.report-location explicitly
Follow-up: config reference for quarkus-jacoco 3.40
§7-ref: Iteration 3 — IRRESOLVABLE
```

**UNVERIFIED list (count 3):**
- U-1: Whether Dev Services are restarted or reused when the application restarts because of a profile change (the dev-services page only says they are reused while their configuration is unchanged).
- U-2: The REST Assured version managed by the Quarkus 3.40.1 BOM (not in the portion read).
- U-3: Whether `camel-quarkus-junit5` 3.40.0 still resolves on Maven Central (orchestrator fact, Unverified).

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Migration Guide | Version in which quarkus-junit5 was renamed to quarkus-junit | Resolved: 3.31, together with JUnit 6 | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 (2026-10-14) |
| 1 | Migration Guide | Does quarkus-junit5 3.40.1 resolve? | Resolved: yes, relocation POM to quarkus-junit | https://repo1.maven.org/maven2/io/quarkus/quarkus-junit5/3.40.1/quarkus-junit5-3.40.1.pom (2026-10-14) |
| 2 | Compatibility Matrix | JUnit Jupiter version in Quarkus 3.40 | Resolved: 6.1.3; Mockito 5.21.0 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/bom/application/pom.xml (2026-10-14) |
| 2 | Migration Guide | Retention period of relocations | ⚠️ IRRESOLVABLE — 3.31 guide and POM give no removal date | — |
| 2 | Guardrails | @InjectMock scope requirement | Resolved: normal-scoped; @Singleton needs @MockitoConfig(convertScopes=true) | https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14) |
| 3 | Guardrails | @QuarkusTestResource deprecation | Resolved (Medium): not stated as deprecated on 3.40 page | https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-14) |
| 3 | Production Readiness | JUnit parallel execution support | ⚠️ IRRESOLVABLE — not covered by 3.40 testing guide | — |
| 3 | Quality Control | JaCoCo default report dir | ⚠️ IRRESOLVABLE — page contradicts itself | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Standard)
- [x] All scope areas cited
- [x] Pattern counts driven by domain needs (6 AD / 4 CP / 6 NP)
- [x] Every anti-pattern has alternative
- [x] All CLI commands validated/marked as representative
- [x] Integration examples complete (Camel, REST Assured, Mockito, command mode; ArC via CDI injection/scopes)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated (deep/exhaustive) or downgraded to 🟡 Medium (AD-4, AD-5, AD-6 downgraded)
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in §7

---

## Agent Operation Notes

- **High Confidence (execute without asking)**:
  - AD-1, AD-2, AD-3 (triangulated)
  - The 3.31 rename/JUnit 6 facts
  - Default test port 8081, test timeout 30s, hang detection 10 min, continuous-testing defaults, JaCoCo data-file default
  - The `@QuarkusMainTest` restrictions
  - The Camel `CamelQuarkusTestSupport` rules
- **Medium Confidence (validate with user)**:
  - AD-4, AD-5, AD-6 (single source)
  - That `@QuarkusTestResource` is not deprecated (absence of evidence)
  - Dev Services details beyond the first 100k chars of that page
  - Quickstart examples from the main branch
- **Low Confidence (must ask human)**: U-1, U-2, U-3; IRRESOLVABLE-1, -2, -3.
- **Edge Cases (pause)**: Quarkus 4.0.0.Beta1 exists (2026-10-01, orchestrator fact). Do not mix 4.0 test patterns into 3.40 skills, and expect the `-junit5` relocations to be at risk in 4.0 (inference).
- **Emergency Stop**: not triggered (official versioned sources exist; 3.40 is the current LTS).
