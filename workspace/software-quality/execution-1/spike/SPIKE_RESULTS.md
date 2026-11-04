# Spike results — 2026-10-31 (orchestrator, JDK Corretto 21.0.11, Maven 3.9.16, Windows, no Docker)

Throwaway projects; nothing here ships. Logs: `pathA.log`, `pathB.log`, `pathA-deps.txt`.

| Path | Setup | Command | Result |
|---|---|---|---|
| B1 (Cucumber 8 black-box) | Quarkus platform BOM 3.40.1 + `cucumber-bom` 8.0.4; `quarkus-rest`; test: `quarkus-junit`, `rest-assured`, `cucumber-java`, `cucumber-junit-platform-engine`, `junit-platform-suite`; Surefire/Failsafe 3.5.4. One `@QuarkusIntegrationTest` class `AcceptanceIT` whose `@Test` calls `io.cucumber.core.cli.Main.run(new String[]{"--glue","spike.acceptance","--plugin","pretty","--tags","not @wip","classpath:features"}, contextClassLoader)` and asserts exit status 0. Steps use static RestAssured (`given().get("/greetings/ana")`) with no host/port set. | `mvn -q -B verify` | **PASS**: Quarkus started the packaged jar, RestAssured pointed at it automatically, "2 scenarios (2 passed) / 5 steps (5 passed)", failsafe report tests=1 failures=0. |
| A (quarkus-cucumber 1.3.0) | same BOM 3.40.1, `io.quarkiverse.cucumber:quarkus-cucumber:1.3.0` (test), `AcceptanceTest extends CucumberQuarkusTest` + `@CucumberOptions(features, glue)`, step class `@ApplicationScoped`. | `mvn -q -B verify` | **PASS** in-process (`@QuarkusTest`, Surefire): 7 dynamic tests, 0 failures. Resolved `cucumber-core` **7.21.1** (no Cucumber 8), `junit-jupiter-api` 6.1.3 via quarkus-junit. One stderr line: LogManager accessed before `java.util.logging.manager` was set (Surefire lacks that system property). |

Conclusions for the skill:
1. Path B1 answers the research gap "how does a non-Jupiter engine reuse the app started by Quarkus": run Cucumber through its CLI `Main.run` inside one `@QuarkusIntegrationTest` method; Quarkus configures RestAssured's port. Observed-in-spike (orchestrator), built only from public APIs; not shown on an official page → (medium confidence) in the skill, with this spike as evidence.
2. The `@Suite` engine runner (F3) remains the official way when the app under test is started outside the test (pipeline-started app, `quarkus.http.test-host/port` analogue via a base URI property).
3. Path A works on 3.40.1 today but locks Cucumber at 7.21.1 and in-process only (no `@QuarkusIntegrationTest`): Ask-First, not default.

| C (WireMock in IT) | path B1 + `quarkus-rest-client`, `io.quarkiverse.wiremock:quarkus-wiremock:1.8.1` (provided) + `quarkus-wiremock-test:1.8.1` (test); main `application.properties`: `quarkus.rest-client.partner.url=http://localhost:${quarkus.wiremock.devservices.port}`; stub `src/test/resources/mappings/title.json`; resource calls the partner client. No Docker on the machine. | `mvn -q -B verify` | **PASS**: the packaged jar (prod profile) called the WireMock Dev Service (in-process, no container) through the `${quarkus.wiremock.devservices.port}` expression; 2 scenarios / 5 steps passed. |
