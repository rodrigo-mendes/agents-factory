---
name: quarkus-acceptance-tests
description: "Guardrails for Cucumber 8.0 acceptance tests on Quarkus 3.40 LTS: runner, RestAssured, WireMock, tag filter, Failsafe. Use when editing step definitions, *IT classes or feature files in a Quarkus project."
applyTo: "**/src/test/java/**/*Steps.java,**/src/test/java/**/*IT.java,**/src/test/resources/features/**"
---

# Quarkus acceptance tests (Cucumber 8.0, Quarkus 3.40)

Technical facts live in the skills below; this rule says what to check and where to look. Tags
`(unverified)` and `(medium confidence)` from a skill apply here too.

Activation: a glob cannot test the project type. Apply this rule **only in Quarkus projects**
(`pom.xml` with Quarkus BOM); otherwise ignore it.

## Skills

| Need | Skill |
|---|---|
| Cucumber runner (B1/B2), steps, state, tags | `testing-quarkus-cucumber-v8-0` |
| Failsafe, IT limits, Dev Services, RestAssured, WireMock, Testcontainers | `testing-quarkus-integration-v3-40` |
| Feature text from OpenSpec | `deriving-gherkin-from-openspec-v1-15` |
| Test types, profiles, mocks | `developing-quarkus-junit-v3-40` |

## Always

- Import the BOMs and leave managed test artifacts without versions (`testing-quarkus-cucumber-v8-0`).
- Use B1, the default runner, unless the user chose otherwise (`testing-quarkus-cucumber-v8-0`).
- Call the launched app with RestAssured over HTTP (`testing-quarkus-integration-v3-40`).
- Stub every external HTTP dependency with WireMock (`testing-quarkus-integration-v3-40`).
- Tag every scenario (directly or through Rule/Feature inheritance) with `@R<n>` or `@req-<slug>`; add `@change-<id>` only when generating from a change delta (no change tag for a spec root); filter with `cucumber.filter.tags` (`testing-quarkus-cucumber-v8-0`).
- Run acceptance classes with Failsafe, not Surefire (`testing-quarkus-integration-v3-40`).

## Ask First

- `quarkus-cucumber` (Path A) instead of B1 (`testing-quarkus-cucumber-v8-0`).
- B2 `@Suite` runner (`testing-quarkus-cucumber-v8-0`).
- Testcontainers vs Dev Services for a data store (`testing-quarkus-integration-v3-40`).
- Parallel scenario execution (`testing-quarkus-cucumber-v8-0`).

## Never

- `cucumber-junit` / JUnit 4 runners (`testing-quarkus-cucumber-v8-0`).
- Real external service calls in a step or test (`testing-quarkus-integration-v3-40`); use WireMock.
- `@Inject` / `@InjectMock` in an `@QuarkusIntegrationTest` class (`testing-quarkus-integration-v3-40`).
- Version overrides for managed artifacts (`testing-quarkus-cucumber-v8-0`, `testing-quarkus-integration-v3-40`).

## Verify

- `grep -rn "@Inject" src/test/java --include=*IT.java` is empty.
- `grep -rnE "io\.cucumber\.junit\.Cucumber\b|<artifactId>cucumber-junit</artifactId>" src/test pom.xml` shows no JUnit 4 runner (the engine package `io.cucumber.junit.platform.engine` is allowed).
- `java -version` and `mvn -version` report the same major version (17 or 21).
- `./mvnw verify` passes, and the Failsafe report has a non-zero testcase count.
