# Unverified Register, Risks and Bibliography

Research date 2026-11-01. Back to [SKILL.md](../SKILL.md). Research quality score reported by the research file: 91%. This register lists **3 unverified items (U1-U3), 2 irresolvable items (I1-I2), 5 medium-confidence items (M1-M5), 2 coverage limits (L1-L2)**.

## Contents

- [Tag to register mapping](#tag-to-register-mapping)
- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Source Bibliography](#source-bibliography)

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) `restClient` redirect reaching the launched IT process | stubbing-and-containers.md | I1 |
| (unverified) container-launched IT reaching WireMock | SKILL.md Ask First; stubbing-and-containers.md | I2 |
| (unverified) WireMock Dev Service needs Docker or not | SKILL.md Ask First; stubbing-and-containers.md | U1 |
| (unverified) official IT data-reset mechanism | restassured-and-data.md | U2 |
| (unverified) representative commands | SKILL.md Quick Reference; failsafe-and-run-modes.md; always-do-patterns.md | U3 |
| (medium confidence) `${quarkus.wiremock.devservices.port}` in the jar IT | SKILL.md Ask First; never-do-patterns.md; stubbing-and-containers.md | M1 |
| (medium confidence) test-host and test-port | SKILL.md Ask First; failsafe-and-run-modes.md | M2 |
| (medium confidence) PostgreSQLContainer package | stubbing-and-containers.md | M3 |
| (medium confidence) BOM patch versions read on branch 3.40 | SKILL.md Version Context | M4 |
| (medium confidence) data isolation guidance | SKILL.md Always Do; restassured-and-data.md | M5 |
| High (shared version facts) | Version Context | sources in the [bibliography](#source-bibliography) |

## Version-lifetime risk

- Quarkus 3.40 LTS was released 2026-09-30 (High, https://quarkus.io/version/3.40/guides/getting-started-testing); Quarkus 4 is out of scope.
- RestAssured 6.3.0 (2026-10-23) is newer than the managed 6.0.1; a later Quarkus patch may move the managed version.
- quarkus-wiremock has an open issue about image-building ITs (issue 279, https://github.com/quarkiverse/quarkus-wiremock/issues); WireMock 4 is beta only.
- Testcontainers 2.0.x patch versions move; the BOM decides.

## Unverified items

- U1. Whether the quarkus-wiremock Dev Service needs Docker (embedded server or container); only the spike observed it running without Docker.
- U2. Official guidance on data reset or ordering in ITs; the skill gives derived guidance.
- U3. Output of the representative `mvn verify` and `grep` commands.

## Irresolvable items

- I1. Whether `@ConnectWireMock(restClient=...)` rewrites the URL inside the launched IT process; docs are silent. Workaround: explicit property expression (M1).
- I2. Whether a container-launched IT can reach the WireMock Dev Service from inside the container; docs are silent. Workaround: jar ITs or the manual resource with the `DevServicesContext` network.

## Medium-confidence items

- M1. Orchestrator spike 2026-10-31 (Quarkus 3.40.1, JDK 21, Maven 3.9.16, no Docker): the packaged jar reached the WireMock Dev Service through `quarkus.rest-client.<key>.url=http://localhost:${quarkus.wiremock.devservices.port}` in main `application.properties` (family fact F14); not an official page.
- M2. `test-host` / `test-port` and the effect on test resources and Dev Services: one source, the testing guide.
- M3. The fully qualified `PostgreSQLContainer` package in 2.0.5: follows the 2.0 rule, not printed on the module page.
- M4. JUnit 6.1.3, Testcontainers 2.0.5 and Awaitility 4.3.0 were read on branch 3.40, not tag 3.40.1 (RestAssured was read at the tag).
- M5. Test data isolation and ordering guidance: derived from the lifecycle, not prescribed by a page.

## Coverage limits

- L1. `all-config` first chunk read for core keys only; `maven-tooling` read partially (first 100000 characters).
- L2. RestAssured wiki and changelog read partially.

## Source Bibliography

All fetched 2026-11-01. Provenance: research file `research_Quarkus_IntegrationTesting_v3.40` and the orchestrator spike of 2026-10-31 (path C).

- https://quarkus.io/version/3.40/guides/getting-started-testing
- https://quarkus.io/version/3.40/guides/maven-tooling
- https://quarkus.io/version/3.40/guides/dev-services
- https://quarkus.io/version/3.40/guides/all-config
- https://quarkus.io/version/3.40/guides/rest-client
- https://raw.githubusercontent.com/quarkusio/quarkus/3.40/bom/application/pom.xml
- https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/pom.xml
- https://docs.quarkiverse.io/quarkus-wiremock/dev/index.html
- https://github.com/quarkiverse/quarkus-wiremock/issues
- https://wiremock.org/docs/response-templating/
- https://github.com/testcontainers/testcontainers-java/releases
- https://java.testcontainers.org/modules/databases/postgres/
- https://github.com/rest-assured/rest-assured/wiki/Usage
- https://raw.githubusercontent.com/rest-assured/rest-assured/master/changelog.txt
