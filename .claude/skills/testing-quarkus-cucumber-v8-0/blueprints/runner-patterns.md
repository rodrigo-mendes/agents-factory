# Runner patterns B1 and B2

Back to [SKILL.md](../SKILL.md). Path A is covered in [never-do patterns](./never-do-patterns.md#when-path-a-is-acceptable).

## Pom fragment (both patterns)

```xml
<properties>
  <maven.compiler.release>21</maven.compiler.release>
  <quarkus.platform.version>3.40.1</quarkus.platform.version> <!-- any 3.40.x patch -->
  <cucumber.version>8.0.4</cucumber.version>
  <surefire-plugin.version>3.5.4</surefire-plugin.version> <!-- spike version (medium confidence) -->
  <failsafe-plugin.version>3.5.4</failsafe-plugin.version> <!-- spike version (medium confidence) -->
</properties>
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>io.quarkus.platform</groupId><artifactId>quarkus-bom</artifactId>
      <version>${quarkus.platform.version}</version><type>pom</type><scope>import</scope>
    </dependency>
    <dependency>
      <groupId>io.cucumber</groupId><artifactId>cucumber-bom</artifactId>
      <version>${cucumber.version}</version><type>pom</type><scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>
<dependencies>
  <dependency><groupId>io.quarkus</groupId><artifactId>quarkus-junit</artifactId><scope>test</scope></dependency>
  <dependency><groupId>io.rest-assured</groupId><artifactId>rest-assured</artifactId><scope>test</scope></dependency>
  <dependency><groupId>io.cucumber</groupId><artifactId>cucumber-java</artifactId><scope>test</scope></dependency>
  <dependency><groupId>io.cucumber</groupId><artifactId>cucumber-junit-platform-engine</artifactId><scope>test</scope></dependency>
  <!-- cucumber-picocontainer: not in the spike pom (medium confidence) -->
  <dependency><groupId>io.cucumber</groupId><artifactId>cucumber-picocontainer</artifactId><scope>test</scope></dependency>
  <dependency><groupId>org.junit.platform</groupId><artifactId>junit-platform-suite</artifactId><scope>test</scope></dependency>
  <!-- needed only for html/json/messages/timeline/usage-json plugins -->
  <dependency><groupId>com.fasterxml.jackson.core</groupId><artifactId>jackson-databind</artifactId><scope>test</scope></dependency>
  <dependency><groupId>com.fasterxml.jackson.datatype</groupId><artifactId>jackson-datatype-jdk8</artifactId><scope>test</scope></dependency>
</dependencies>
```

The spike pom used Surefire/Failsafe 3.5.4 and the Quarkus platform BOM 3.40.1 (medium confidence for other versions).
The `quarkus-maven-plugin` `build` goal must be present so the packaged app exists before Failsafe runs.

## B1 Cucumber inside @QuarkusIntegrationTest (default)

Evidence: orchestrator spike on 2026-10-31 (JDK 21, Maven 3.9.16): `mvn -q -B verify` passed, "2 scenarios (2 passed)",
Failsafe report tests=1 failures=0. Built from public APIs only (medium confidence; register item M1 in [unverified and risks](./unverified-and-risks.md#medium-confidence-items)).

The Cucumber delta in the pom: Surefire must skip the IT class (the B1 class). Failsafe setup (goals, `maven.home`, log manager) is in `testing-quarkus-integration-v3-40` (blueprint failsafe-and-run-modes). Run `mvn verify` without `skipITs=true` (or pass `-DskipITs=false`) so B1 actually runs.

```xml
<plugin>
  <artifactId>maven-surefire-plugin</artifactId>
  <version>${surefire-plugin.version}</version>
  <configuration>
    <excludes><exclude>**/*IT.java</exclude></excludes>
  </configuration>
</plugin>
```

```java
@QuarkusIntegrationTest
class AcceptanceIT {
    @Test
    void features() {
        byte status = io.cucumber.core.cli.Main.run(
            new String[] {
                "--glue", "com.example.acceptance",
                "--plugin", "pretty",
                "--tags", "not @wip",
                "classpath:features"
            },
            Thread.currentThread().getContextClassLoader());
        assertEquals(0, status, "Cucumber scenarios failed");
    }
}
```

- Quarkus starts the packaged jar (`prod` profile) and configures RestAssured's host and port; steps use static `given()` with no base URI.
- Features sit in `src/test/resources/features`; glue is the package of the step classes.
- One IT method runs every scenario; Cucumber's `pretty` output and exit status carry the detail. Add `junit:` or `html:` plugins for reports (Jackson needed for html).
- The step classes cannot inject CDI beans: the app runs as a separate artifact.
- Test names in the Failsafe report show one test only; use the Cucumber plugins for per-scenario reporting.

## B2 Suite engine runner

Official engine mechanism ([engine README](https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-junit-platform-engine)). Use it when the pipeline or a container starts the app and the tests receive a base URI.

```java
@Suite
@IncludeEngines("cucumber")
@SelectPackages("com.example.acceptance")
@ConfigurationParameter(key = GLUE_PROPERTY_NAME, value = "com.example.acceptance")
@ConfigurationParameter(key = PLUGIN_PROPERTY_NAME,
        value = "pretty, html:target/cucumber/report.html, junit:target/cucumber/junit.xml")
public class RunCucumberIT { }
```

Features must sit in the selected package path (`src/test/resources/com/example/acceptance`); `@SelectClasspathResource("features")` is the alternative.

```java
public class BaseUriHooks {
    @BeforeAll
    public static void configure() {
        RestAssured.baseURI = System.getProperty("app.base-uri", "http://localhost:8080");
    }
}
```

`app.base-uri` is this skill's own property name, not a Quarkus key. Pass it with Failsafe `systemPropertyVariables`.
Set `cucumber.junit-platform.naming-strategy=long` in `junit-platform.properties` for Failsafe 3.5.4+ (medium confidence).
Failsafe `<includes>` should list the suite class (`**/RunCucumberIT.java`) only.

If the suite itself launches `target/quarkus-app/quarkus-run.jar` (`ProcessBuilder`, `-Dquarkus.http.port`, poll a ready URL, destroy in `@AfterAll`), the fast-jar path is (unverified) and Dev Services do not start for that jar (medium confidence): supply stores through Testcontainers or external config.
