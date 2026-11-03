# Migration 7.x to 8.0

Back to [SKILL.md](../SKILL.md). Sources read 2026-10-31: [CHANGELOG](https://github.com/cucumber/cucumber-jvm/blob/main/CHANGELOG.md), [release notes v8.0.0](https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/release-notes/v8.0.0.md).

## Breaking changes

- Java 17 baseline.
- Jackson is opt-in: `json`, `html`, `messages`, `timeline`, `usage-json` need Jackson 2 or 3 on the classpath.
- The engine runs on JUnit Platform 6.1.x (CHANGELOG says 6.1.2, release notes say 6.1.3; the Quarkus BOM pins 6.1.3).
- `cucumber-cdi2`, `cucumber-openejb`, `cucumber-deltaspike` removed.
- `cucumber-junit` (JUnit 4) and `cucumber-testng` deprecated for removal.
- Classes not designed for extension are `final`; utility classes are not instantiable.
- JSpecify nullability annotations can raise warnings in Kotlin or null-checking builds.
- `cucumber.filter.name` now matches partially.

## Upgrade steps from 7.34.x

1. Set the compiler release to 17 or 21.
2. Set `cucumber-bom` to 8.0.4.
3. Replace `@RunWith(Cucumber.class)` with B1 or a `@Suite` runner; move `@CucumberOptions` values to CLI arguments (B1) or `@ConfigurationParameter` / `junit-platform.properties` (B2).
4. Add the Jackson 2 pair if any Jackson-based plugin is used.
5. Replace `cucumber-cdi2` with `cucumber-picocontainer` (or `cucumber-jakarta-cdi` where a separate CDI SE container is acceptable).
6. For B2 set `cucumber.junit-platform.naming-strategy=long` on Failsafe 3.5.4+ (medium confidence).
7. Run `mvn -B verify` and check the testcase count in the Failsafe report is non-zero.

## Moving from `quarkus-cucumber` (Path A)

- Step classes were CDI beans (`@ApplicationScoped`); they become plain public classes with a public constructor and PicoContainer injection.
- `@Inject` of app beans and `@InjectMock` are lost: assertions go over HTTP, stubs move to WireMock.
- `CucumberQuarkusTest` subclasses and `@CucumberOptions` are replaced by the B1 IT class.

## New in 8.0 worth using

- Named hooks (`@Before(name = ...)`).
- `cucumber.glue.classes` for explicit glue, and include/exclude class-name patterns for glue.
- DocString and DataTable on one step (reporting not supported yet).

## Compatibility matrix

| Dependency | Min | Max | Notes |
|---|---|---|---|
| Java | 17 | n/a | Cucumber 8 baseline; Quarkus 3.40 range (medium confidence) |
| Cucumber JVM | 8.0.4 | 8.0.x | `cucumber-bom` |
| JUnit Platform | 6.1.3 (Quarkus BOM) | 6.1.x | engine built on 6.1.2/6.1.3 |
| Quarkus | 3.40 LTS | 3.40.x | `quarkus-junit` |
| Jackson 2 | BOM-managed | 2.x | for html/json/messages |
| Surefire / Failsafe | 3.5.4 (spike) | 3.6.1 (medium confidence) | naming strategy `long` |
| `quarkus-cucumber` | 1.3.0 | 1.3.0 | Cucumber 7.21.1 (Path A) |
