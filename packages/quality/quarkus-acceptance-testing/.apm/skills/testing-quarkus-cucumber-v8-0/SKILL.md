---
name: testing-quarkus-cucumber-v8-0
description: "Cucumber JVM 8.0.4 acceptance tests for Quarkus 3.40 LTS REST apps (black-box, Failsafe, RestAssured). Use when adding or fixing Cucumber scenarios in a Quarkus 3.40 project. Not for Cucumber 7, JUnit 4 runners, Quarkus 4 or in-process CDI tests."
---

# Testing Quarkus with Cucumber 8.0

> Version lock: every claim applies to **Cucumber JVM 8.0.4** on **Quarkus 3.40 LTS** only. Research date **2026-10-31**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; see the [register](./blueprints/unverified-and-risks.md).

## Version Context

| Item | Value | Source (fetched 2026-10-31) |
|---|---|---|
| Cucumber JVM | 8.0.4 (2026-10-02); 8.0.0 on 2026-09-24; last 7.x is 7.34.9 | https://github.com/cucumber/cucumber-jvm/blob/main/CHANGELOG.md |
| Java baseline (Cucumber) | 17 | https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/release-notes/v8.0.0.md |
| Java range (Quarkus 3.40) | 17 and 21 (medium confidence) | https://quarkus.io/version/3.40/guides/getting-started-testing |
| JUnit Platform | 6.x, managed by the Quarkus BOM (6.1.3) | https://raw.githubusercontent.com/quarkusio/quarkus/3.40/bom/application/pom.xml |
| Quarkus | 3.40 LTS, released 2026-09-30; test artifact `quarkus-junit` | https://quarkus.io/version/3.40/guides/getting-started-testing |
| `quarkus-cucumber` (Path A) | 1.3.0 (2025-03-10), Cucumber 7.21.1 | https://repo1.maven.org/maven2/io/quarkiverse/cucumber/quarkus-cucumber/maven-metadata.xml |

**Version-lifetime risk** (as of 2026-10-31; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Cucumber 8.0.0 is recent and already has 4 patch releases; re-check the CHANGELOG before pinning a newer patch.
- `quarkus-cucumber` main is unreleased and its JUnit 6 fix is not in 1.3.0.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Runner patterns B1 and B2 (pom, IT class, suite)](./blueprints/runner-patterns.md)
- [Steps, state, hooks, reports, parallel](./blueprints/steps-and-state.md)
- [Migration 7.x to 8.0](./blueprints/migration-guide.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

Scope split: test types, profiles and mocks are in `developing-quarkus-junit-v3-40`; WireMock, Dev Services,
Testcontainers and Failsafe pom details are in `testing-quarkus-integration-v3-40`; writing the `.feature` from a
spec is in `deriving-gherkin-from-openspec-v1-15`. This skill covers running Cucumber 8 against a Quarkus app.

## Blueprints & Guardrails

Default pattern **B1**: one Failsafe class annotated `@QuarkusIntegrationTest` runs Cucumber through
`io.cucumber.core.cli.Main.run(args, classLoader)` and asserts exit status 0; steps call the packaged app with
RestAssured and Quarkus configures the port. Built from public APIs and proven by a spike, not shown on an official
page (medium confidence). See [runner patterns](./blueprints/runner-patterns.md#b1-cucumber-inside-quarkusintegrationtest-default).

### ✅ Always Do

- **Import both BOMs, no versions on managed artifacts** — `cucumber-bom` 8.0.x plus the Quarkus platform BOM manage Cucumber, JUnit Platform, RestAssured and Jackson ([Quarkus BOM](https://raw.githubusercontent.com/quarkusio/quarkus/3.40/bom/application/pom.xml), RestAssured 6.0.1 per F13). See [patterns](./blueprints/always-do-patterns.md#bom-and-dependencies).
- **Run the acceptance suite with Failsafe, entry class `*IT`, excluded from Surefire** — Failsafe setup is in `testing-quarkus-integration-v3-40` (blueprint failsafe-and-run-modes); only the Cucumber delta is here. Never run `mvn verify` with `skipITs=true` (or pass `-DskipITs=false`), or B1 does not run. See [runner patterns](./blueprints/runner-patterns.md#b1-cucumber-inside-quarkusintegrationtest-default).
- **Use a `@Suite` runner with `@IncludeEngines("cucumber")` when the app is started outside the test** — Surefire and Failsafe cannot discover `.feature` files directly ([engine README](https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-junit-platform-engine)). See [runner patterns](./blueprints/runner-patterns.md#b2-suite-engine-runner).
- **Add `jackson-databind` and `jackson-datatype-jdk8` at test scope for `html`, `json`, `messages`, `timeline`, `usage-json`** — Jackson is no longer shaded in 8.0 ([release notes](https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/release-notes/v8.0.0.md)).
- **Share scenario state through PicoContainer constructor injection** — step classes are recreated per scenario ([cucumber-picocontainer README](https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-picocontainer)). See [steps](./blueprints/steps-and-state.md#scenario-state).
- **Make step classes and state holders public with public constructors** — PicoContainer still requires them in 8.0 ([release notes](https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/release-notes/v8.0.0.md)).
- **Use Cucumber Expressions, `@ParameterType` and `@DataTableType`** instead of regex parsing in steps ([cucumber-java README](https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-java)).
- **Tag every scenario `@R<n>` (plus `@change-<id>` on the Feature for a change delta), and filter with `cucumber.filter.tags`** — factory tag convention, rule 5 (F11); the filter key is in the [engine README](https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-junit-platform-engine).
- **Check that the Failsafe report has a non-zero testcase count** — zero scenarios with a green build means the suite was not discovered (medium confidence).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Who starts the app | B1 (Quarkus starts the packaged jar, medium confidence) vs B2 (pipeline or Docker starts it; official `@Suite` engine, base URI property) | "Does `mvn verify` start the app, or does the pipeline start it before the tests?" |
| Path A `quarkus-cucumber` 1.3.0 | In-process `@QuarkusTest`, CDI-bean steps, Dev Services and mocks; locks Cucumber 7.21.1, no `@QuarkusIntegrationTest`, JUnit 6 fix unreleased | "Do steps need CDI injection or `@InjectMock`, and is Cucumber 7.x acceptable?" |
| Naming strategy | `cucumber.junit-platform.naming-strategy=long` for Surefire/Failsafe 3.5.4+, `surefire` for 3.5.2 and below (medium confidence) | "Which Failsafe version does the build use?" |
| Parallel scenarios | `cucumber.execution.parallel.enabled=true`; flaky with shared data (medium confidence) | "Is test data isolated per scenario?" |
| Hook-launched jar (B2 variant) | `@BeforeAll` starts `quarkus-run.jar` with `ProcessBuilder`; own process code (medium confidence) | "May the suite manage the app process itself?" |
| Hook order | `@Before(order=...)` direction (unverified) | "Do hooks depend on each other's order?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| `@RunWith(Cucumber.class)` or `cucumber-junit`: deprecated for removal ([CHANGELOG](https://github.com/cucumber/cucumber-jvm/blob/main/CHANGELOG.md)) | A `@Suite` runner with `cucumber-junit-platform-engine` (B2, High) or B1 (medium confidence) |
| `html`/`json`/`messages` plugin without Jackson ([release notes](https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/release-notes/v8.0.0.md)) | Add the Jackson 2 pair, BOM-managed |
| `cucumber-cdi2`, `cucumber-openejb`, `cucumber-deltaspike`, `cucumber-jakarta-cdi` (F4): removed or not usable in 8.0 ([CHANGELOG](https://github.com/cucumber/cucumber-jvm/blob/main/CHANGELOG.md)) | `cucumber-picocontainer` |
| Subclass Cucumber classes: not designed for extension, now `final` ([CHANGELOG](https://github.com/cucumber/cucumber-jvm/blob/main/CHANGELOG.md)) | Plugins and hooks |
| Explicit `junit-platform-*` or `junit-jupiter` versions next to the Quarkus BOM ([Quarkus BOM](https://raw.githubusercontent.com/quarkusio/quarkus/3.40/bom/application/pom.xml)) | No `<version>`; the BOM manages it |
| Rely on Surefire to find `.feature` files ([engine README](https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-junit-platform-engine)) | `@Suite` class (B2, High) or `*IT` class (B1, medium confidence; register item M1) |
| Call a real external partner API in a step ([quarkus-wiremock docs](https://docs.quarkiverse.io/quarkus-wiremock/dev/index.html)) | WireMock 3.x stubs, see `testing-quarkus-integration-v3-40` |

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| BOM import | `io.cucumber:cucumber-bom:8.0.4` plus `io.quarkus.platform:quarkus-bom` | https://github.com/cucumber/cucumber-jvm/blob/main/CHANGELOG.md |
| Runner dependencies | `cucumber-java`, `cucumber-junit-platform-engine`, `junit-platform-suite` | https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-junit-platform-engine |
| Glue / plugin / tag keys | `cucumber.glue`, `cucumber.plugin`, `cucumber.filter.tags` | https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-junit-platform-engine |
| Test artifact | `io.quarkus:quarkus-junit` (renamed from `quarkus-junit5` in 3.31) | https://quarkus.io/version/3.40/guides/getting-started-testing |
| Telemetry off | `cucumber.publish.quiet=true`; keep `cucumber.publish.enabled` off | https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-junit-platform-engine |
| Verify | `mvn -B verify`, then count `<testcase` in `target/failsafe-reports` | n/a (unverified); B1 evidence is register item M1 in the [register](./blueprints/unverified-and-risks.md#medium-confidence-items) |

## External Resources

All fetched 2026-10-31.

- [Cucumber JVM engine README](https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-junit-platform-engine)
- [Quarkus 3.40 testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)
- [quarkus-cucumber docs (Path A)](https://docs.quarkiverse.io/quarkus-cucumber/dev/index.html)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
