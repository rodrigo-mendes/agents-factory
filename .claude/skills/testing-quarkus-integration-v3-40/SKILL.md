---
name: testing-quarkus-integration-v3-40
description: "Quarkus 3.40 LTS integration tests: @QuarkusIntegrationTest with Failsafe, Dev Services, RestAssured 6.0.1, WireMock (quarkus-wiremock 1.8.1) and Testcontainers 2.0. Use when writing or fixing *IT tests in Quarkus 3.40. Not for Quarkus 4, Cucumber or unit tests."
---

# Testing Quarkus 3.40 integration tests

> Version lock: every claim applies to **Quarkus 3.40 LTS (3.40.1)** only. Research date **2026-11-01**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; see the [register](./blueprints/unverified-and-risks.md).

## Version Context

| Item | Value | Source (fetched 2026-11-01) |
|---|---|---|
| Quarkus | 3.40 LTS, released 2026-09-30; test artifact `io.quarkus:quarkus-junit` | https://quarkus.io/version/3.40/guides/getting-started-testing |
| Failsafe goals | `integration-test` and `verify`; `skipITs` property | https://quarkus.io/version/3.40/guides/maven-tooling |
| RestAssured | 6.0.1, managed by Quarkus (6.3.0 upstream is not managed) | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/pom.xml |
| JUnit / Testcontainers / Awaitility | 6.1.3 / 2.0.5 / 4.3.0 (read on the 3.40 branch, medium confidence for patches) | https://raw.githubusercontent.com/quarkusio/quarkus/3.40/bom/application/pom.xml |
| Testcontainers 2.0 | `testcontainers-` artifact prefix, `org.testcontainers.<module>` packages, no JUnit 4 | https://github.com/testcontainers/testcontainers-java/releases |
| quarkus-wiremock | 1.8.1 on WireMock 3.13.2, not in the Quarkus BOM | https://docs.quarkiverse.io/quarkus-wiremock/dev/index.html |
| Dev Services | need Docker or Podman for container-based services; timeout 60 s | https://quarkus.io/version/3.40/guides/dev-services |

**Version-lifetime risk** (as of 2026-11-01; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 3.40 was released 2026-09-30 ([releases](https://quarkus.io/releases)); re-check the testing guide before relying on a newer patch.
- RestAssured 6.3.0 exists upstream but Quarkus 3.40 manages 6.0.1: do not override.
- quarkus-wiremock behaviour inside a launched IT process is only partly documented.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Failsafe pom and run modes](./blueprints/failsafe-and-run-modes.md)
- [WireMock, Dev Services and Testcontainers](./blueprints/stubbing-and-containers.md)
- [RestAssured and test data isolation](./blueprints/restassured-and-data.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

Scope split: test types, profiles basics: `developing-quarkus-junit-v3-40` (also `@InjectMock` and `QuarkusMock`); writing
Cucumber scenarios on top of ITs is in `testing-quarkus-cucumber-v8-0`; deriving `.feature` text from a spec is in
`deriving-gherkin-from-openspec-v1-15`. This skill covers the IT itself: build, launch, stubs, containers and data.

## Blueprints & Guardrails

`@QuarkusIntegrationTest` starts the artifact the build produced (fast-jar, native executable or container image) in a
separate process and tests it black-box over HTTP. It runs after `package` under Failsafe. This skill adds the pom setup and run modes; test types and profile basics are in `developing-quarkus-junit-v3-40`.

### ✅ Always Do

- **Bind Failsafe `integration-test` and `verify` for the `*IT` classes** — ITs need the packaged artifact ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)). See [Failsafe pom](./blueprints/failsafe-and-run-modes.md#failsafe-pom).
- **Name IT classes `*IT` and reuse `@QuarkusTest` classes by extension** — Failsafe picks `*IT` ([Maven tooling](https://quarkus.io/version/3.40/guides/maven-tooling)). See [patterns](./blueprints/always-do-patterns.md#naming-and-reuse).
- **Assert only through HTTP with RestAssured** — the app is another process, so the test class cannot inject beans ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)).
- **Pass configuration through a test resource return map, `quarkus.test.arg-line` or `quarkus.test.env.*`** — test-scope `application.properties` is not read ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)). See [patterns](./blueprints/always-do-patterns.md#configuration-reaches-the-app).
- **For an IT profile other than the default `prod`, set `quarkus.test.integration-test-profile` and put the `%profile.` keys in the packaged `src/main/resources/application.properties`** ([all-config](https://quarkus.io/version/3.40/guides/all-config)).
- **Stub every external HTTP dependency with WireMock 3.x** — tests never call a real service (family rule 4). See [stubbing](./blueprints/stubbing-and-containers.md#wiremock-through-quarkus-wiremock).
- **Keep stub files under `mappings/` and `__files/`** — the quarkus-wiremock Dev Service loads them ([quarkus-wiremock docs](https://docs.quarkiverse.io/quarkus-wiremock/dev/index.html)).
- **Use Dev Services for data stores that have one, Testcontainers 2.0 in a test resource otherwise** ([Dev Services guide](https://quarkus.io/version/3.40/guides/dev-services); [Testcontainers releases](https://github.com/testcontainers/testcontainers-java/releases)).
- **Reuse a `RequestSpecification` built once** with `RequestSpecBuilder` ([RestAssured usage](https://github.com/rest-assured/rest-assured/wiki/Usage)). See [RestAssured](./blueprints/restassured-and-data.md#specification-reuse).
- **Declare test dependencies without versions and import the Quarkus platform BOM** — it manages RestAssured and Testcontainers ([pom.xml 3.40.1](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/pom.xml)).
- **Use unique keys per test for created data** — the app and its database live for the whole Failsafe run (derived guidance, medium confidence). See [data isolation](./blueprints/restassured-and-data.md#test-data-isolation).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Artifact the IT launches | jar (default, no Docker for the app), native (proves the image, long build), container (tests the shipped image, needs docker or podman) | "Which artifact is shipped, and does CI have Docker?" |
| Already running app | `quarkus.http.test-host` / `test-port`; test resources and Dev Services do not reach it (medium confidence) | "Is the target shared, and may write tests run there?" |
| WireMock flavour | quarkus-wiremock Dev Service (zero code, file stubs, Quarkiverse dependency) vs manual `WireMockServer` in a test resource (full control) | "May the build depend on a Quarkiverse extension?" |
| CI without Docker | skip ITs (`-DskipITs=true`), or disable Dev Services and give explicit connection config | "Do CI runners provide Docker or Podman?" |
| WireMock Dev Service without Docker | worked in a spike on one machine (medium confidence); no official statement (unverified) | "Is it acceptable to rely on a spike result for the no-Docker case?" |
| Override the RestAssured version managed by the Quarkus BOM (6.0.1, F13) | default: no override; 6.3.0 upstream is not managed and may clash with Quarkus' RestAssured integration | "Is there a bug fixed only in a newer RestAssured that justifies leaving the BOM version?" |
| Container-launched IT reaching WireMock | `localhost` inside the container is not the host; no official guidance | "Must ITs run the container artifact?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| `@Inject` or `@InjectMock` in a `@QuarkusIntegrationTest` class ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)) | RestAssured over HTTP; stub dependencies with WireMock or a test resource |
| IT configuration in `src/test/resources/application.properties` ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)) | test resource `start()` return map, `quarkus.test.arg-line` or `quarkus.test.env.*` |
| `@QuarkusTest` and `*IT` classes in one Surefire run ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)) | Surefire for `@QuarkusTest`, Failsafe for `*IT` |
| Real external API or a WireMock catch-all proxy to it ([rest-client guide](https://quarkus.io/version/3.40/guides/rest-client)) | explicit WireMock stubs; unmatched requests return 404 |
| Testcontainers 1.x coordinates or JUnit 4 `@Rule` containers ([releases](https://github.com/testcontainers/testcontainers-java/releases)) | `testcontainers-<module>` in a `QuarkusTestResourceLifecycleManager` |
| Explicit RestAssured, JUnit or Testcontainers versions ([pom.xml 3.40.1](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/pom.xml)) | no `<version>`; the Quarkus BOM manages them |

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Run jar ITs | `./mvnw verify -DskipITs=false` | https://quarkus.io/version/3.40/guides/maven-tooling |
| Run native ITs | `./mvnw verify -Dnative` | https://quarkus.io/version/3.40/guides/maven-tooling |
| Skip ITs (CI without Docker) | `./mvnw verify -DskipITs=true` | https://quarkus.io/version/3.40/guides/maven-tooling |
| IT profile | `-Dquarkus.test.integration-test-profile=<name>` (default `prod`) | https://quarkus.io/version/3.40/guides/all-config |
| App launch wait | `quarkus.test.wait-time`, default `1M` | https://quarkus.io/version/3.40/guides/all-config |
| RestAssured client timeout | `quarkus.http.test-timeout`, default `30S` | https://quarkus.io/version/3.40/guides/all-config |
| Disable Dev Services | `quarkus.devservices.enabled=false` | https://quarkus.io/version/3.40/guides/dev-services |
| Injection check | `grep -rn "@Inject" src/test/java --include=*IT.java` must be empty | (unverified) |

## External Resources

All fetched 2026-11-01.

- [Quarkus 3.40 testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)
- [Quarkus 3.40 Dev Services guide](https://quarkus.io/version/3.40/guides/dev-services)
- [quarkus-wiremock docs](https://docs.quarkiverse.io/quarkus-wiremock/dev/index.html)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
