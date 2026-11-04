# Research — Cucumber JVM 8.0.x on Quarkus 3.40 LTS (unit testing-quarkus-cucumber-v8-0)

Save name: `research_Cucumber_QuarkusCucumber_v8.0.md`. Family facts and rules applied:
`workspace/software-quality/_family_facts.md` (F1-F8), `_family_rules.md` (rules 1-10).

## Metadata

```yaml
Full_Name: Cucumber JVM (cucumber-junit-platform-engine) on Quarkus 3.40 LTS
Target_Version: 8.0.4 (Cucumber JVM); Quarkus 3.40 LTS; JUnit Platform 6.1.3 (Quarkus BOM)
Release_Date: 2026-10-02 (8.0.4); 8.0.0 on 2026-09-24
Support_Status: Active (Cucumber 8.0.x current line); Quarkus 3.40 LTS
Primary_Docs: https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-junit-platform-engine
Official_Repo: https://github.com/cucumber/cucumber-jvm
Research_Date: 2026-10-31
Domain_Complexity: Standard
Research_Depth: exhaustive (flat fan-out, no section-investigators, no plan mode, per brief)
Max_Iterations: 5
Gap_Loop_Ran: true
Iterations_Used: 2 of 5
Triangulated_Count: 6
Unverified_Count: 4
Irresolvable_Count: 2
Research_Quality_Score: 89%   # ~55 claims, 4 unverified, 2 irresolvable
```

## Executive Summary

Cucumber JVM 8.0 (8.0.0 on 2026-09-24, current 8.0.4 on 2026-10-02) moves the baseline to Java 17,
runs its JUnit Platform engine on JUnit Platform 6.1.x, makes Jackson opt-in (the `json`, `html`,
`messages`, `timeline` and `usage-json` plugins need an explicit Jackson 2 or 3 dependency), deprecates
`cucumber-junit` (JUnit 4) and `cucumber-testng` for removal, removes `cucumber-cdi2`,
`cucumber-openejb` and `cucumber-deltaspike`, and makes classes not designed for extension `final`
(CHANGELOG 8.0.0; release-notes/v8.0.0.md, read 2026-10-31). The only supported runner going forward is
`cucumber-junit-platform-engine` driven by a JUnit `@Suite` class.

On Quarkus 3.40 two paths exist. **Path A**, the Quarkiverse `quarkus-cucumber` extension, starts the
app as a `@QuarkusTest` and makes step classes CDI beans; its last release is 1.3.0 (2025-03-10, Maven
Central metadata), built against Cucumber 7.x and `quarkus-junit5`, `main` is unreleased (Quarkus
3.31.1, Cucumber 7.34.2), the JUnit 6 IDE fix (#298, PR #310) was merged in August 2026 but not released,
and `@QuarkusIntegrationTest` is unsupported (issue #32 open since 2022, PR #119 open). **Path B**,
plain Cucumber 8 with a `@Suite` runner and RestAssured driving the packaged app black-box under
Maven Failsafe, uses only components that are documented and versioned for the target. Recommendation:
Path B (see "Path A vs Path B decision evidence").

Complexity is Standard: three moving parts (Cucumber engine, JUnit Platform suite, Quarkus packaged
artifact) with one non-obvious gap — no official mechanism lets a non-Jupiter engine (Cucumber) reuse the
app started by `@QuarkusTest` / `@QuarkusIntegrationTest`, so the app lifecycle has to be owned
explicitly (unverified that no such mechanism exists; none found in the 3.40 testing guide, read in full).

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low

### ✅ Mandatory Patterns

**Run Cucumber through the JUnit Platform engine with a `@Suite` runner**
> Confidence: 🟢 High | [✓✓ Triangulated | engine README (2026-10-31) + release-notes/v8.0.0.md (2026-10-31)]
- Why: `cucumber-junit` (JUnit 4) is deprecated for removal in 8.0; the engine README documents `@Suite` + `@IncludeEngines("cucumber")` + selector + `@ConfigurationParameter(GLUE_PROPERTY_NAME)`; Surefire/Failsafe cannot discover `.feature` resources directly, so the suite class is the entry point.
- Code:
  ```java
  package com.example.acceptance;

  import org.junit.platform.suite.api.ConfigurationParameter;
  import org.junit.platform.suite.api.IncludeEngines;
  import org.junit.platform.suite.api.SelectPackages;
  import org.junit.platform.suite.api.Suite;

  import static io.cucumber.junit.platform.engine.Constants.GLUE_PROPERTY_NAME;
  import static io.cucumber.junit.platform.engine.Constants.PLUGIN_PROPERTY_NAME;

  @Suite
  @IncludeEngines("cucumber")
  @SelectPackages("com.example.acceptance")          // features in src/test/resources/com/example/acceptance
  @ConfigurationParameter(key = GLUE_PROPERTY_NAME, value = "com.example.acceptance")
  @ConfigurationParameter(key = PLUGIN_PROPERTY_NAME,
          value = "pretty, html:target/cucumber/report.html, junit:target/cucumber/junit.xml")
  public class RunCucumberIT {
  }
  ```
- Note: `@SelectClasspathResource("features")` is the resource-based alternative; the README example uses `@SelectPackages` (package of features and glue). Selector choice: features must sit in the selected package/resource path.
- Source: https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-junit-platform-engine (2026-10-31)

**Pin versions through `cucumber-bom` 8.0.x and the Quarkus 3.40 platform BOM**
> Confidence: 🟢 High | [✓✓ Triangulated | CHANGELOG 8.0.3 "[BOM] dependencies converge" (2026-10-31) + Quarkus 3.40 bom/application/pom.xml junit 6.1.3 (2026-10-31)]
- Why: the engine and `junit-platform-suite` must share the JUnit Platform line (6.1.x); the Quarkus BOM imports `junit-bom` 6.1.3, so `junit-platform-suite` takes its version from it (family rule 8).
- Code: see Implementation Blueprint pom fragment.
- Source: https://github.com/cucumber/cucumber-jvm/blob/main/CHANGELOG.md ; https://raw.githubusercontent.com/quarkusio/quarkus/3.40/bom/application/pom.xml (2026-10-31)

**Add Jackson explicitly when using `html`, `json`, `messages`, `timeline` or `usage-json`**
> Confidence: 🟢 High | [✓✓ Triangulated | release-notes/v8.0.0.md + CHANGELOG 8.0.0 "Jackson is now opt-in (#3206)"]
- Why: Jackson is no longer shaded; the plugins fail without it. Jackson 2: `com.fasterxml.jackson.core:jackson-databind` + `com.fasterxml.jackson.datatype:jackson-datatype-jdk8`; Jackson 3: `tools.jackson.core:jackson-databind`. On Quarkus 3.40 the BOM manages Jackson 2 (`jackson-bom.version` 2.21.8), so use the Jackson 2 pair without versions.
- Source: release-notes/v8.0.0.md ; CHANGELOG.md (2026-10-31)

**Set the naming strategy for Maven reports**
> Confidence: 🟡 Medium (single source: engine README)
- Why: Surefire/Failsafe report only `<Class> - <Method>`; use `cucumber.junit-platform.naming-strategy=long` for Surefire/Failsafe 3.5.4+, `surefire` for 3.5.2 and below. Current plugin is 3.6.1 (maven.apache.org, 2026-10-31) so `long` applies.
- Source: engine README (2026-10-31); https://maven.apache.org/surefire/maven-failsafe-plugin/ (2026-10-31)

**Run the black-box suite with Failsafe against the packaged artifact**
> Confidence: 🟢 High | [✓✓ Triangulated | Quarkus 3.40 testing guide (Failsafe `integration-test`/`verify`) + engine README (Surefire/Failsafe config)]
- Why: the packaged jar is what ships (`prod` profile); Failsafe `integration-test` runs after `package`, `verify` fails the build afterwards. Name the suite `*IT` so Failsafe picks it up and Surefire does not.
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing (2026-10-31, read fully)

**Share scenario state through PicoContainer constructor injection**
> Confidence: 🟢 High | [✓✓ Triangulated | cucumber-picocontainer README + release-notes v8.0.0 (picocontainer still needs public classes/constructors)]
- Why: step classes and their dependencies are recreated per scenario; state lives in an injected object; Picocontainer is the only DI module that still requires public classes and public constructors in 8.0. Resources needing cleanup implement `org.picocontainer.Disposable` (runs after Cucumber after-hooks).
- Source: https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-picocontainer ; release-notes/v8.0.0.md (2026-10-31)

**Use Cucumber Expressions, `@ParameterType` and `@DataTableType` from `cucumber-java`**
> Confidence: 🟢 High | [✓✓ Triangulated | cucumber-java README + CHANGELOG 8.0.0 (cucumber-expressions v20.1.0)]
- Why: typed step arguments instead of regex parsing in steps; `@ParameterType` method name = expression name, regex in `value`, capture groups passed as `String`s. Release notes recommend a `@DataTableType` transform instead of `DataTable::asList` under JSpecify nullability.
- Source: https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-java (2026-10-31)

### ⚠️ Conditional Patterns

**Who starts the Quarkus app for the Cucumber suite**
> Confidence: 🟡 Medium
- Options: (1) Cucumber `@BeforeAll` hook launching `target/quarkus-app/quarkus-run.jar` with a chosen port and polling readiness; (2) app started outside the test JVM (CI step, container) and the base URI passed as a system property; (3) Path A (`quarkus-cucumber`, `@QuarkusTest` in-JVM).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | 1 hook-launched jar | self-contained `mvn verify` | own process management code (not an official Quarkus API) (medium confidence) | default for Path B |
  | 2 external app | tests real deployment (container/native) | needs CI orchestration | staging/system tests |
  | 3 quarkus-cucumber | CDI injection, Dev Services, mocks | unreleased JUnit 6 fix, Cucumber 7 only, no integration-test mode | team accepts the risks below |
- Agent: "Ask user whether the app is started by the test (hook) or by the pipeline, and whether in-JVM CDI access (Path A) is a hard requirement."
- Source: Quarkus testing guide 3.40 (2026-10-31); quarkus-cucumber issue #32 (2026-10-31)

**Surefire with a `@QuarkusTest`-started app for the Cucumber engine**
> Confidence: 🔴 Low (unverified)
- `@QuarkusTest` is a JUnit Jupiter extension; the Cucumber engine is a separate JUnit Platform engine, and the 3.40 testing guide documents no way for another engine to reuse the started app (guide read fully, 2026-10-31). Quarkiverse's extension works around this by hosting Cucumber inside a Jupiter `@QuarkusTest` class. Do not plan on Surefire + `@QuarkusTest` + plain Cucumber engine. (unverified — absence of documentation, not a documented prohibition)

**Parallel scenarios**
> Confidence: 🟡 Medium (engine README)
- `cucumber.execution.parallel.enabled=true`, strategy `dynamic` (default factor 1) / `fixed` / `custom`; `cucumber.execution.execution-mode.feature=same_thread` keeps scenarios of one feature serial; `cucumber.execution.exclusive-resources.<tag>.read-write` locks scenarios tagged `@<tag>`. `max-pool-size` does not strictly cap concurrency (junit5#3108). Ask the user: shared state in the app under test (DB rows, WireMock stubs) makes parallel runs flaky unless data is isolated.

**Quarkiverse `quarkus-cucumber` (Path A)** — Ask-First; see decision evidence.

### 🚫 Forbidden Patterns

**JUnit 4 runner `@RunWith(Cucumber.class)`**
> Severity: High
> Confidence: 🟢 High
- Why: `cucumber-junit` deprecated for removal in 8.0 (family rule 7).
- Impact: breaks at the next major; mixes JUnit 4 vintage engine into a JUnit 6 build.
- ❌ Wrong:
  ```java
  @RunWith(io.cucumber.junit.Cucumber.class)
  @CucumberOptions(glue = "com.example.acceptance")
  public class RunCucumberTest { }
  ```
- ✅ Correct: the `@Suite` + `@IncludeEngines("cucumber")` runner above.
- Source: CHANGELOG 8.0.0 Deprecated; release-notes/v8.0.0.md (2026-10-31)

**`html`/`json`/`messages` plugin without Jackson on the classpath**
> Severity: High
> Confidence: 🟢 High
- Impact: plugin fails at startup on Cucumber 8 (Jackson unshaded).
- ❌ Wrong: `cucumber.plugin=html:target/cucumber.html` with only `cucumber-java` + engine.
- ✅ Correct: add `jackson-databind` + `jackson-datatype-jdk8` (test scope, Quarkus-BOM managed).
- Source: release-notes/v8.0.0.md (2026-10-31)

**`cucumber-cdi2` / `cucumber-openejb` / `cucumber-deltaspike` on 8.0**
> Severity: High
> Confidence: 🟢 High
- Impact: artifacts removed in 8.0, build fails to resolve.
- ✅ Correct: `cucumber-picocontainer`, or `cucumber-jakarta-cdi` + a CDI SE impl (Weld SE). Note: `cucumber-jakarta-cdi` boots its own CDI SE container per scenario; it does not use Quarkus ArC (Quarkus not mentioned in its README) — it does not give access to the app's beans.
- Source: CHANGELOG 8.0.0 Removed; cucumber-jakarta-cdi README (2026-10-31)

**Subclassing Cucumber classes**
> Severity: Medium
> Confidence: 🟢 High
- Impact: classes not designed for extension are `final` in 8.0 (see api-changes.json); utility classes cannot be instantiated.
- ✅ Correct: use plugins (`cucumber.plugin`) and hooks instead of extending internals.
- Source: CHANGELOG 8.0.0 Changed (2026-10-31)

**Explicit `junit-jupiter`/`junit-platform-*` versions next to the Quarkus BOM**
> Severity: Medium
> Confidence: 🟢 High
- Impact: JUnit Platform version skew between Quarkus (6.1.3) and the Cucumber engine.
- ❌ Wrong: `<artifactId>junit-platform-suite</artifactId><version>1.11.4</version>`
- ✅ Correct: no `<version>`; let the Quarkus BOM (`junit-bom` 6.1.3) manage it (family rule 8).
- Source: Quarkus 3.40 bom/application/pom.xml (2026-10-31)

**Relying on Surefire to find `.feature` files without a suite**
> Severity: Medium | Confidence: 🟢 High
- Impact: zero scenarios run, build green. ✅ Correct: `@Suite` class (or Console Launcher).
- Source: engine README (2026-10-31)

## Migration Guide

> Confidence: 🟢 High | Sources: CHANGELOG.md (2026-10-31) + release-notes/v8.0.0.md (2026-10-31)

**Breaking Changes**: Java 17 baseline; Jackson opt-in; JUnit Platform 6.1.x in the engine (CHANGELOG says 6.1.2, release notes 6.1.3); `cucumber-cdi2`, `cucumber-openejb`, `cucumber-deltaspike` removed; final classes and non-instantiable utility classes; JSpecify nullability may raise Kotlin/JSpecify warnings; `cucumber.filter.name` now matches partially.

**Upgrade Steps** (from 7.34.x):
1. Raise the compiler release to 17 or 21.
2. Set `cucumber-bom` to 8.0.4.
3. Replace `@RunWith(Cucumber.class)` with a `@Suite` runner; move `@CucumberOptions` to `@ConfigurationParameter` / `junit-platform.properties`.
4. Add Jackson 2 (`jackson-databind`, `jackson-datatype-jdk8`) if any of html/json/messages/timeline/usage-json is used.
5. Replace `cucumber-cdi2` with `cucumber-jakarta-cdi` (or move to picocontainer).
6. Set `cucumber.junit-platform.naming-strategy=long` (Surefire/Failsafe 3.5.4+).
7. Run `mvn -B verify` and check the scenario count in the Failsafe report is non-zero.

New in 8.0 worth using: named hooks (`@Before(name=...)`), `cucumber.glue.classes` for explicit glue, glue include/exclude class-name patterns, DocString + DataTable on one step (reporting not yet supported).

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|---|---|---|---|
| Java | 17 | 21 (tested by Quarkus 3.40 LTS) | Cucumber 8 baseline 17 (F2) |
| Cucumber JVM (`cucumber-bom`) | 8.0.4 | 8.0.x | F1 |
| JUnit Platform / Jupiter | 6.1.3 (Quarkus BOM) | 6.1.x | engine built on 6.1.2/6.1.3 (F3) |
| Quarkus | 3.40 LTS | 3.40.x | test artifact `quarkus-junit` (F5) |
| Jackson 2 | 2.21.8 (Quarkus BOM) | 2.x | needed for html/json/messages |
| Surefire / Failsafe | 3.5.4 | 3.6.1 (current) | naming-strategy `long` |
| RestAssured | Quarkus BOM managed | — | exact version (unverified: not in the BOM part read) |
| quarkus-cucumber (Path A) | 1.3.0 | 1.3.0 | Cucumber 7.21.1, `quarkus-junit5` (F7) |

## Implementation Blueprint

> Confidence: 🟢 High for dependencies/runner/steps | 🟡 Medium for the app-launch hook

**pom.xml fragments**
```xml
<properties>
  <maven.compiler.release>21</maven.compiler.release>
  <quarkus.platform.version>3.40.1</quarkus.platform.version> <!-- any 3.40.x LTS patch -->
  <cucumber.version>8.0.4</cucumber.version>
  <failsafe-plugin.version>3.6.1</failsafe-plugin.version>
</properties>

<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>io.quarkus.platform</groupId>
      <artifactId>quarkus-bom</artifactId>
      <version>${quarkus.platform.version}</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
    <dependency>
      <groupId>io.cucumber</groupId>
      <artifactId>cucumber-bom</artifactId>
      <version>${cucumber.version}</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>

<dependencies>
  <dependency><groupId>io.quarkus</groupId><artifactId>quarkus-junit</artifactId><scope>test</scope></dependency>
  <dependency><groupId>io.rest-assured</groupId><artifactId>rest-assured</artifactId><scope>test</scope></dependency>
  <dependency><groupId>io.cucumber</groupId><artifactId>cucumber-java</artifactId><scope>test</scope></dependency>
  <dependency><groupId>io.cucumber</groupId><artifactId>cucumber-junit-platform-engine</artifactId><scope>test</scope></dependency>
  <dependency><groupId>io.cucumber</groupId><artifactId>cucumber-picocontainer</artifactId><scope>test</scope></dependency>
  <dependency><groupId>org.junit.platform</groupId><artifactId>junit-platform-suite</artifactId><scope>test</scope></dependency>
  <!-- Cucumber 8: Jackson needed by html/json/messages plugins -->
  <dependency><groupId>com.fasterxml.jackson.core</groupId><artifactId>jackson-databind</artifactId><scope>test</scope></dependency>
  <dependency><groupId>com.fasterxml.jackson.datatype</groupId><artifactId>jackson-datatype-jdk8</artifactId><scope>test</scope></dependency>
</dependencies>

<build>
  <plugins>
    <plugin>
      <artifactId>maven-failsafe-plugin</artifactId>
      <version>${failsafe-plugin.version}</version>
      <executions>
        <execution>
          <goals><goal>integration-test</goal><goal>verify</goal></goals>
        </execution>
      </executions>
      <configuration>
        <includes><include>**/RunCucumberIT.java</include></includes>
        <systemPropertyVariables>
          <app.jar>${project.build.directory}/quarkus-app/quarkus-run.jar</app.jar>
          <app.port>8089</app.port>
          <java.util.logging.manager>org.jboss.logmanager.LogManager</java.util.logging.manager>
          <maven.home>${maven.home}</maven.home>
        </systemPropertyVariables>
        <properties>
          <configurationParameters>
            cucumber.junit-platform.naming-strategy=long
          </configurationParameters>
        </properties>
      </configuration>
    </plugin>
  </plugins>
</build>
```
`app.jar`/`app.port` are this blueprint's own property names, not Quarkus keys. The path `target/quarkus-app/quarkus-run.jar` is the default fast-jar layout (unverified in a page read for this research).

**src/test/resources/junit-platform.properties**
```properties
cucumber.glue=com.example.acceptance
cucumber.plugin=pretty, html:target/cucumber/report.html, json:target/cucumber/report.json, junit:target/cucumber/junit.xml
cucumber.filter.tags=not @wip
cucumber.junit-platform.naming-strategy=long
cucumber.publish.quiet=true
cucumber.execution.parallel.enabled=false
```
(Keys from the engine README, 2026-10-31. Values set by `@ConfigurationParameter` on the suite take precedence over the file for that suite (medium confidence — JUnit Platform behaviour not re-read here).)

**Shared state + app lifecycle hook**
```java
package com.example.acceptance;

public class ScenarioContext {            // public + public ctor: picocontainer requirement
    public io.restassured.response.Response lastResponse;
    public String createdId;
}
```
```java
package com.example.acceptance;

import io.cucumber.java.AfterAll;
import io.cucumber.java.BeforeAll;
import io.restassured.RestAssured;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

public class AppLifecycleHooks {

    private static Process app;

    @BeforeAll   // must be static, no arguments
    public static void startApp() throws Exception {
        String port = System.getProperty("app.port", "8089");
        String baseUri = System.getProperty("app.base-uri");      // option 2: externally started app
        if (baseUri == null) {
            app = new ProcessBuilder("java", "-Dquarkus.http.port=" + port,
                    "-jar", System.getProperty("app.jar"))
                    .inheritIO().start();
            baseUri = "http://localhost:" + port;
            waitUntilUp(baseUri + "/q/health/ready", Duration.ofSeconds(60)); // needs quarkus-smallrye-health; else poll any route
        }
        RestAssured.baseURI = baseUri;
    }

    @AfterAll
    public static void stopApp() {
        if (app != null) {
            app.destroy();
        }
    }

    private static void waitUntilUp(String url, Duration timeout) throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        long deadline = System.nanoTime() + timeout.toNanos();
        while (System.nanoTime() < deadline) {
            try {
                HttpResponse<Void> r = client.send(HttpRequest.newBuilder(URI.create(url)).build(),
                        HttpResponse.BodyHandlers.discarding());
                if (r.statusCode() == 200) {
                    return;
                }
            } catch (java.io.IOException notYet) {
                // app not listening yet
            }
            Thread.sleep(500);
        }
        throw new IllegalStateException("Application not ready at " + url);
    }
}
```
The hook pattern is assembled from documented pieces (Cucumber static `@BeforeAll`/`@AfterAll`; Quarkus `quarkus.http.port`; JDK `ProcessBuilder`); no official page shows this exact pattern (medium confidence).

**Step definitions with RestAssured, ParameterType, DataTableType, tagged hook**
```java
package com.example.acceptance;

import io.cucumber.java.After;
import io.cucumber.java.Before;
import io.cucumber.java.DataTableType;
import io.cucumber.java.ParameterType;
import io.cucumber.java.Scenario;
import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;
import io.restassured.http.ContentType;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.equalTo;

public class ItemSteps {

    public record Item(String name, BigDecimal price) { }

    private final ScenarioContext ctx;

    public ItemSteps(ScenarioContext ctx) {          // picocontainer constructor injection
        this.ctx = ctx;
    }

    @ParameterType("\\d+(?:\\.\\d{1,2})?")
    public BigDecimal money(String value) {
        return new BigDecimal(value);
    }

    @DataTableType
    public Item item(Map<String, String> row) {
        return new Item(row.get("name"), new BigDecimal(row.get("price")));
    }

    @Before("@R1")
    public void tagHook(Scenario scenario) {
        scenario.log("requirement R1");
    }

    @Given("the catalog contains:")
    public void theCatalogContains(List<Item> items) {
        for (Item i : items) {
            given().contentType(ContentType.JSON).body(Map.of("name", i.name(), "price", i.price()))
                    .when().post("/items")
                    .then().statusCode(201);
        }
    }

    @When("I create an item {string} priced {money}")
    public void iCreateAnItem(String name, BigDecimal price) {
        ctx.lastResponse = given().contentType(ContentType.JSON)
                .body(Map.of("name", name, "price", price))
                .when().post("/items");
    }

    @Then("the response status is {int}")
    public void theResponseStatusIs(int status) {
        ctx.lastResponse.then().statusCode(status);
    }

    @Then("the item name is {string}")
    public void theItemNameIs(String name) {
        ctx.lastResponse.then().body("name", equalTo(name));
    }

    @After
    public void attachOnFailure(Scenario scenario) {
        if (scenario.isFailed() && ctx.lastResponse != null) {
            scenario.attach(ctx.lastResponse.asByteArray(), "application/json", "last-response");
        }
    }
}
```
```gherkin
@R1 @change-add-items
Feature: Items

  Scenario: Create an item
    When I create an item "pen" priced 2.50
    Then the response status is 201
    And the item name is "pen"
```
Hook ordering: Cucumber docs state hook execution order is not defined unless `order` is set; direction of `order` not stated in the README read (unverified: before hooks commonly run low-to-high, after hooks high-to-low).

## Quality Control

**Verification Commands** (representative):
```bash
mvn -B verify                                   # builds the jar, Failsafe runs RunCucumberIT
grep -c "<testcase" target/failsafe-reports/TEST-*.xml   # must be > 0 (zero = suite not discovered)
mvn -B verify -Dcucumber.filter.tags="@R1"      # filter by tag (system property override; medium confidence)
grep -rn "cucumber-junit<\|RunWith(Cucumber" pom.xml src/test   # must be empty
grep -n "jackson-databind" pom.xml              # required if html/json/messages plugin used
```

**Mocking**: external HTTP dependencies of the app go to WireMock 3.x (family rule 4, F8) — see unit testing-quarkus-integration-v3-40. Dev Services do not start for a jar launched by a Cucumber hook (they are started by Quarkus test/dev mode) (medium confidence); provide data stores via Testcontainers or external config.

## Production Readiness

- **Performance**: one app start per suite (`@BeforeAll`), not per scenario; parallel execution only with data isolation.
- **Scalability**: shard by tag (`cucumber.filter.tags`) across CI jobs.
- **Monitoring**: keep `junit` XML + `html` reports as CI artifacts; check non-zero scenario count.
- **Security**: `cucumber.publish.enabled` must stay off (publishes reports to reports.cucumber.io); set `cucumber.publish.quiet=true`. Never put real credentials in feature files.

## Path A vs Path B decision evidence

| Criterion | Path A — `quarkus-cucumber` | Path B — Cucumber 8 engine + Failsafe | Evidence |
|---|---|---|---|
| Cucumber version | 7.21.1 (1.3.0); main 7.34.2 unreleased | 8.0.4 | maven-metadata (lastUpdated 2025-03-10); main pom.xml; CHANGELOG |
| JUnit / Quarkus test artifact | depends on `quarkus-junit5` + `junit-jupiter` + `junit-platform-console` | `junit-platform-suite` from Quarkus BOM (6.1.3) | runtime/pom.xml (main); Quarkus BOM 3.40 |
| JUnit 6 (Quarkus 3.31+) | IDE `runMain` broken; fixed by PR #310, issue #298 closed 2026-08-09, no release since 1.3.0 | native | issue #298; maven-metadata |
| `@QuarkusIntegrationTest` | unsupported (issue #32 open since 2022, PR #119 open; 1.2.0 `@ScenarioScope` made it worse) | the design target (black-box packaged artifact) | issue #32; issue #278 open |
| CDI in steps, `@ScenarioScope`, scenario events | yes | no (black-box only) | docs.quarkiverse.io |
| Dev Services / `@InjectMock` | yes (in-JVM `@QuarkusTest`) — mockito regression reported (#215 open) | no | issues list |
| Maintenance | 24 open issues, 11 open PRs; users asking whether maintained | Cucumber core team, 4 patch releases in Sept-Oct 2026 | repo page; CHANGELOG |
| Coupling to Cucumber internals | drives Cucumber-core directly (F7) — Cucumber 8 final classes increase break risk (medium confidence) | public engine API only | F7; CHANGELOG 8.0.0 |

**Recommendation**: Path B is the default for Quarkus 3.40 + Cucumber 8. Path A is Ask-First and acceptable
only if all hold: the team needs in-JVM CDI/mocks in steps, accepts Cucumber 7.x (not 8), accepts a
`@QuarkusTest`-only (no packaged-artifact) run, and either pins 1.3.0 and verifies it on Quarkus 3.40 /
JUnit 6 in a spike or waits for a release containing PR #310. Compatibility of 1.3.0 with Quarkus 3.40
was not verified by any official page (unverified).

## Reference Implementations

- https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-junit-platform-engine (runner, config, rerun)
- https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-java (annotations, transformers, hooks)
- https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-picocontainer
- https://quarkus.io/version/3.40/guides/getting-started-testing
- https://docs.quarkiverse.io/quarkus-cucumber/dev/index.html
- Neighbour units (link only): developing-quarkus-junit-v3-40; testing-quarkus-integration-v3-40; deriving-gherkin-from-openspec-v1-15.

## Source Bibliography

**Primary** (all read 2026-10-31):
- Cucumber JVM CHANGELOG — https://github.com/cucumber/cucumber-jvm/blob/main/CHANGELOG.md
- Release notes v8.0.0 — https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/release-notes/v8.0.0.md
- Engine README — https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/cucumber-junit-platform-engine/README.md
- cucumber-java README — https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/cucumber-java/README.md
- cucumber-picocontainer README — https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/cucumber-picocontainer/README.md
- cucumber-jakarta-cdi README — https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/cucumber-jakarta-cdi/README.md
- Quarkus 3.40 testing guide — https://quarkus.io/version/3.40/guides/getting-started-testing
- Quarkus 3.40 BOM — https://raw.githubusercontent.com/quarkusio/quarkus/3.40/bom/application/pom.xml (chars 0-100000)
- Quarkus 3.40 build-parent — https://raw.githubusercontent.com/quarkusio/quarkus/3.40/build-parent/pom.xml
- Maven Failsafe — https://maven.apache.org/surefire/maven-failsafe-plugin/
- Quarkiverse docs — https://docs.quarkiverse.io/quarkus-cucumber/dev/index.html
- Maven Central metadata — https://repo1.maven.org/maven2/io/quarkiverse/cucumber/quarkus-cucumber/maven-metadata.xml

**Validation** (GitHub issues/PRs):
- quarkiverse/quarkus-cucumber issues list, #298, #32 (PR #119, #309, #310 referenced), main pom.xml and runtime/pom.xml

**Pages read**

| URL | read on | official | instructions found in the page |
|---|---|---|---|
| https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/release-notes/v8.0.0.md | 2026-10-31 | yes | no |
| https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/cucumber-junit-platform-engine/README.md | 2026-10-31 | yes | no |
| https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/CHANGELOG.md | 2026-10-31 | yes | no |
| https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/cucumber-java/README.md | 2026-10-31 | yes | no |
| https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/cucumber-picocontainer/README.md | 2026-10-31 | yes | no |
| https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/cucumber-jakarta-cdi/README.md | 2026-10-31 | yes | no |
| https://quarkus.io/version/3.40/guides/getting-started-testing | 2026-10-31 (full, 108160 chars in two reads) | yes | no |
| https://raw.githubusercontent.com/quarkusio/quarkus/3.40/bom/application/pom.xml | 2026-10-31 (partial: chars 0-100000 of 318255) | yes | no |
| https://raw.githubusercontent.com/quarkusio/quarkus/3.40/build-parent/pom.xml | 2026-10-31 | yes | no |
| https://maven.apache.org/surefire/maven-failsafe-plugin/ | 2026-10-31 | yes | no |
| https://github.com/quarkiverse/quarkus-cucumber | 2026-10-31 | yes | no |
| https://docs.quarkiverse.io/quarkus-cucumber/dev/index.html | 2026-10-31 | yes | no |
| https://repo1.maven.org/maven2/io/quarkiverse/cucumber/quarkus-cucumber/maven-metadata.xml | 2026-10-31 | yes | no |
| https://github.com/quarkiverse/quarkus-cucumber/issues?q=is%3Aissue | 2026-10-31 (partial: page 1, 25 of 33) | yes | no |
| https://github.com/quarkiverse/quarkus-cucumber/issues/298 | 2026-10-31 | yes | no |
| https://github.com/quarkiverse/quarkus-cucumber/issues/32 | 2026-10-31 | yes | no |
| https://raw.githubusercontent.com/quarkiverse/quarkus-cucumber/main/pom.xml | 2026-10-31 | yes | no |
| https://raw.githubusercontent.com/quarkiverse/quarkus-cucumber/main/runtime/pom.xml | 2026-10-31 | yes | no |

## Research Gaps

```
Gap: RestAssured exact version in the Quarkus 3.40 BOM
Impact: Low — BOM-managed, no explicit version needed
Workaround: no <version>, rely on quarkus-bom
Follow-up: bom/application/pom.xml chars 100000+ (rest-assured.version)
§7-ref: Iteration 1 — IRRESOLVABLE (not in the part read; build-parent does not define it)
```
```
Gap: Official mechanism for a non-Jupiter engine to reuse a @QuarkusTest / @QuarkusIntegrationTest-started app (and the port)
Impact: Medium — drives the hook-launched-jar design
Workaround: Cucumber @BeforeAll hook starting the packaged jar with -Dquarkus.http.port, or externally started app
Follow-up: Quarkus test framework source / Zulip; quarkus-cucumber PR #119
§7-ref: Iteration 2 — IRRESOLVABLE
```
Other (unverified) items: hook `order` direction; `quarkus-run.jar` fast-jar path; Dev Services not starting for a hook-launched jar; quarkus-cucumber 1.3.0 on Quarkus 3.40.

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|---|---|---|---|---|
| 1 | Compatibility Matrix | RestAssured version | ⚠️ IRRESOLVABLE — not in BOM part read nor build-parent | — |
| 1 | Compatibility Matrix | Failsafe current version | Resolved: 3.6.1 | https://maven.apache.org/surefire/maven-failsafe-plugin/ (2026-10-31) |
| 2 | Decision evidence | JUnit 6 status of quarkus-cucumber | Resolved: #298 closed via PR #310 (2026-08-09), unreleased | https://github.com/quarkiverse/quarkus-cucumber/issues/298 (2026-10-31) |
| 2 | Conditional Patterns | @QuarkusTest app reuse by Cucumber engine | ⚠️ IRRESOLVABLE — no official doc in 3.40 testing guide (read fully) | — |

## Completion Checklist

- [x] Domain complexity tier assessed and documented
- [x] All scope areas cited
- [x] Pattern counts driven by domain needs
- [x] Every anti-pattern has alternative
- [x] All CLI commands marked as representative
- [x] Integration examples complete
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns triangulated or downgraded to 🟡 Medium
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score calculated
- [x] Every Research Gap cross-referenced

## Agent Operation Notes

- High: ✓✓ patterns (suite runner, BOMs, Jackson, Failsafe, picocontainer, cucumber-java types).
- Medium: naming strategy, parallel config, app-launch hook — validate with user.
- Low / ask: Path A adoption; any reliance on @QuarkusTest from the Cucumber engine.
- Edge case: Cucumber 8.0.0 is ~5 weeks old (released 2026-09-24); 4 patch releases already.

## Source Bibliography (final)

See "Source Bibliography" and "Pages read" above; every URL read on 2026-10-31.
