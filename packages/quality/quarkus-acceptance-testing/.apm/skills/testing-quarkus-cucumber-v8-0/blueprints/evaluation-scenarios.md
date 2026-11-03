# Evaluation scenarios

Back to [SKILL.md](../SKILL.md). Each scenario states the query, the expected behaviour and what must not appear.

## Scenario 1 (canonical)

query: "Add Cucumber acceptance tests to my Quarkus 3.40 REST app. It exposes POST /items."

Expected:
- Asks or states the pattern: B1 default (one `@QuarkusIntegrationTest` IT class calling `Main.run`, medium confidence).
- Imports `cucumber-bom` 8.0.x plus the Quarkus BOM; no versions on `cucumber-java`, `cucumber-junit-platform-engine`, `junit-platform-suite`, RestAssured.
- Failsafe with `integration-test` and `verify`; Surefire excludes `*IT`.
- Steps use RestAssured, a public `ScenarioContext` injected by PicoContainer; scenarios tagged `@R<n>` (plus `@change-<id>` on the Feature only for a change delta).
- Adds Jackson if `html` or `json` plugins are used; ends with `mvn -B verify` and a non-zero testcase count check.

Must not: `@RunWith`, `cucumber-junit`, `quarkus-cucumber`, explicit JUnit versions.

## Scenario 2 (edge: app started by the pipeline)

query: "Our pipeline deploys the app to a container first. Run the Cucumber scenarios against it."

Expected:
- Switches to B2: `@Suite`, `@IncludeEngines("cucumber")`, selector, `@ConfigurationParameter(GLUE_PROPERTY_NAME)`, `junit-platform-suite` from the BOM.
- Base URI through a property (`app.base-uri` is a skill-defined name, not a Quarkus key) set on `RestAssured.baseURI` in a `@BeforeAll` hook.
- Mentions Surefire cannot discover `.feature` files and the naming strategy `long` for Failsafe 3.5.4+ (medium confidence).

Must not: start a second copy of the app, or use `@QuarkusIntegrationTest` for an app it does not start.

## Scenario 3 (rejection: JUnit 4 runner)

query: "Use the cucumber-junit module with @RunWith(Cucumber.class), our other tests are JUnit 4."

Expected:
- Refuses: `cucumber-junit` is deprecated for removal in 8.0 and Quarkus 3.40 tests run on JUnit 6.
- Offers B1 or the `@Suite` runner and the migration steps for `@CucumberOptions`.

Must not: write the `@RunWith` class.

## Scenario 4 (trap: "the Quarkus way")

query: "Just add quarkus-cucumber, that is the Quarkus way of doing Cucumber."

Expected:
- Does not add it silently; presents Ask First with facts: 1.3.0 (2025-03-10), Cucumber 7.21.1, in-process `@QuarkusTest`, no `@QuarkusIntegrationTest`, JUnit 6 fix merged but unreleased, spike passed on Quarkus 3.40.1.
- Asks whether steps need CDI or `@InjectMock` and whether Cucumber 7 is acceptable; keeps B1 as default.
- Tags official compatibility with 3.40 as (unverified).

Must not: claim `quarkus-cucumber` supports Cucumber 8 or packaged-artifact tests.

## Scenario 5 (trap: real partner API)

query: "In the step, call the real payments partner API at their sandbox URL to check the full flow."

Expected:
- Refuses: tests never call a real external service.
- Stubs the app's outbound call with WireMock 3.x and points to `testing-quarkus-integration-v3-40` for the setup.
- Steps still call only the app under test.

Must not: put the partner URL or credentials in a step or feature file.

## Scenario 6 (check: report plugin)

query: "Add an HTML report to the Cucumber run."

Expected: adds `html:` plugin plus `jackson-databind` and `jackson-datatype-jdk8` at test scope without versions; keeps `cucumber.publish.enabled` off.

Must not: add the plugin without Jackson.
