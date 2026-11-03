# Always-do patterns

Back to [SKILL.md](../SKILL.md). All sources read 2026-10-31. Code for the runners: [runner patterns](./runner-patterns.md); steps: [steps and state](./steps-and-state.md).

## BOM and dependencies

- Import `io.quarkus.platform:quarkus-bom` and `io.cucumber:cucumber-bom` (8.0.x) in `dependencyManagement`.
- Declare `cucumber-java`, `cucumber-junit-platform-engine`, `junit-platform-suite`, `rest-assured`, `quarkus-junit` at test scope without `<version>`.
- The Quarkus BOM imports `junit-bom` 6.1.3, so `junit-platform-suite` takes its version from it (family rule 8).
- RestAssured is managed by the Quarkus BOM at test scope; the exact version was not found (see register I1).
- Source: https://github.com/cucumber/cucumber-jvm/blob/main/CHANGELOG.md ("[BOM] dependencies converge", 8.0.3); https://raw.githubusercontent.com/quarkusio/quarkus/3.40/bom/application/pom.xml.

## Failsafe split

- `maven-failsafe-plugin` with goals `integration-test` and `verify`; the `quarkus-maven-plugin` `build` goal packages the app first.
- Surefire excludes `**/*IT.java`; Failsafe runs the acceptance class.
- A passing Surefire run with zero tests is not acceptance evidence: count testcases in `target/failsafe-reports`.
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing.

## Black-box tests with `@QuarkusIntegrationTest`

- It tests the built artifact (jar, native or container) with the `prod` profile; the test class gets no injection and no `src/test/resources/application.properties` (F6).
- Steps reach the app over HTTP only; assert on status, headers and body, never on beans.

## Jackson for report plugins

- Jackson 2 pair, test scope, BOM-managed on Quarkus 3.40: `com.fasterxml.jackson.core:jackson-databind` and `com.fasterxml.jackson.datatype:jackson-datatype-jdk8`.
- Jackson 3 alternative: `tools.jackson.core:jackson-databind`; use it only if the build already moved to Jackson 3.
- Source: https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/release-notes/v8.0.0.md.

## Traceability tags

- Feature-level `@change-<id>` when generating from a change delta (none for a spec root), scenario-level `@R<n>` (or `@req-<slug>` when the spec has no R-ids).
- Verify by script: grep every `Scenario` for an `@R` tag; zero untagged scenarios.
- Filter a run: `mvn -B verify -Dcucumber.filter.tags="@R1"` (medium confidence for the override, see register M6).

## Test data and external services

- Stub every external HTTP dependency of the app with WireMock 3.x (`quarkus-wiremock` 1.8.1 supports `@QuarkusIntegrationTest`), see `testing-quarkus-integration-v3-40`.
- Data stores: Dev Services or Testcontainers, never a shared real database.
- Test types, profiles and `@InjectMock` limits: `developing-quarkus-junit-v3-40`.
- Source: https://docs.quarkiverse.io/quarkus-wiremock/dev/index.html.

## Writing steps

- One step class per domain area; shared state in a public `ScenarioContext` injected by constructor.
- Step text carries intent, not HTTP verbs; the HTTP call lives in the step body.
- Derive the `.feature` text from the spec with `deriving-gherkin-from-openspec-v1-15`; a precondition missing from the spec is a question, not a `Given`.
