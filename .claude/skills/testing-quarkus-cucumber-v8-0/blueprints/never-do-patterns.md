# Never-do patterns

Back to [SKILL.md](../SKILL.md). Sources read 2026-10-31: [CHANGELOG](https://github.com/cucumber/cucumber-jvm/blob/main/CHANGELOG.md), [release notes v8.0.0](https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/release-notes/v8.0.0.md), [engine README](https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-junit-platform-engine).

## JUnit 4 runner

Impact: deprecated for removal in 8.0; mixes the vintage engine into a JUnit 6 build.

```java
// ❌ Wrong
@RunWith(io.cucumber.junit.Cucumber.class)
@CucumberOptions(glue = "com.example.acceptance")
public class RunCucumberTest { }
```

✅ Instead: B1 (`@QuarkusIntegrationTest` plus `Main.run`) or the `@Suite` runner in [runner patterns](./runner-patterns.md#b2-suite-engine-runner).

## Report plugin without Jackson

```properties
# ❌ Wrong: only cucumber-java and the engine on the classpath
cucumber.plugin=html:target/cucumber.html
```

✅ Instead: add `jackson-databind` and `jackson-datatype-jdk8` at test scope (BOM-managed).

## Removed CDI modules

`cucumber-cdi2`, `cucumber-openejb` and `cucumber-deltaspike` are removed in 8.0; the build fails to resolve them.
✅ Instead: `cucumber-picocontainer`. `cucumber-jakarta-cdi` boots its own CDI SE container per scenario, not Quarkus ArC, so it gives no access to the app's beans.

## Subclassing Cucumber classes

Classes not designed for extension are `final` in 8.0; utility classes cannot be instantiated.
✅ Instead: `cucumber.plugin` plugins and hooks.

## Version overrides next to the BOMs

```xml
<!-- ❌ Wrong -->
<artifactId>junit-platform-suite</artifactId><version>1.11.4</version>
```

✅ Instead: no `<version>`; the Quarkus BOM (`junit-bom` 6.1.3) manages it. Also no explicit `junit-jupiter`, `byte-buddy` or `mockito-inline` (family rule 8).

## Surefire discovering `.feature` files

Impact: zero scenarios run and the build is green.
✅ Instead: an `*IT` class (B1) or a `@Suite` class (B2), and a non-zero testcase count in the Failsafe report.

## Real external services in steps

A step that calls the real partner API makes the suite flaky and can change real data.
✅ Instead: WireMock 3.x stubs for the app's outbound calls, configured through `testing-quarkus-integration-v3-40`. Source: https://docs.quarkiverse.io/quarkus-wiremock/dev/index.html.

## Static scenario state

Static fields or a singleton step class leak state between scenarios and break parallel runs.
✅ Instead: PicoContainer-injected `ScenarioContext` ([steps and state](./steps-and-state.md#scenario-state)).

## When Path A is acceptable

`io.quarkiverse.cucumber:quarkus-cucumber:1.3.0` is Ask-First, not forbidden. It is acceptable only if all hold: steps need in-JVM CDI or mocks, Cucumber 7.21.1 (not 8) is accepted, a `@QuarkusTest`-only run (no packaged artifact) is accepted, and the team pins 1.3.0 and runs a spike on Quarkus 3.40 or waits for a release containing PR #310.

Facts (F7, https://repo1.maven.org/maven2/io/quarkiverse/cucumber/quarkus-cucumber/maven-metadata.xml and https://github.com/quarkiverse/quarkus-cucumber):
- Last release 1.3.0 (2025-03-10), cucumber-java 7.21.1, depends on `quarkus-junit5`.
- `@QuarkusIntegrationTest` unsupported (issues #32, #278; PR #119 open).
- JUnit 6 fix (issue #298, PR #310) merged 2026-08-09, unreleased.
- Spike on 2026-10-31: 1.3.0 passed in-process on Quarkus 3.40.1 and resolved cucumber-core 7.21.1.
- Official compatibility of 1.3.0 with Quarkus 3.40 is (unverified).
