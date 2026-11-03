# Inventory and go/no-go — software-quality (P2, 2026-10-31)

| Unit | Source item | Official docs | Skill name | Package | Worker | Scope boundary | Overlap |
|---|---|---|---|---|---|---|---|
| U1 (pilot) | need 2 | cucumber-jvm 8.0 release notes + junit-platform-engine README; quarkus-cucumber repo/docs; Quarkus 3.40 testing guide | `testing-quarkus-cucumber-v8-0` | quality/quarkus-acceptance-testing | framework-researcher (exhaustive, both paths) | runner, glue, steps, hooks, DataTable/ParameterType, tags, reports, scenario state, parallel, Surefire/Failsafe | links developing-quarkus-junit-v3-40 |
| U2 | need 3 | Quarkus 3.40 getting-started-testing, dev-services; quarkus-wiremock 1.8; Testcontainers 2.0 | `testing-quarkus-integration-v3-40` | quality/quarkus-acceptance-testing | framework-researcher (exhaustive) | Failsafe pom, IT limits, Dev Services in IT, RestAssured spec reuse, WireMock, Testcontainers 2 resources | links junit, camel-junit, lambda testing, rest-client skills |
| U3 | needs 1 + 4 | Gherkin reference; OpenSpec 1.15 schema/conventions; cucumber.io BDD docs | `deriving-gherkin-from-openspec-v1-15` | quality/acceptance-testing | framework-researcher (exhaustive) | spec->feature mapping, tags, deltas, traceability, coverage script | requirements-methodology-researcher BDD bridge (template only) |
| rule | need 4 | from U3 | `gherkin-feature-authoring` (`**/*.feature`) | quality/acceptance-testing | artifact-author | | |
| rule | needs 2/3 | from U1/U2 | `quarkus-acceptance-tests` | quality/quarkus-acceptance-testing | artifact-author | | |
| agent | DEC-003 | | `acceptance-test-reviewer` (read-only) | quality/acceptance-testing | artifact-author | | quarkus-code-reviewer traceability table |
| agent | DEC-003 | | `acceptance-test-engineer` (executor) | quality/quarkus-acceptance-testing | artifact-author | | |
| command | DEC-003 | | `/building-acceptance-tests` -> acceptance-test-engineer | quality/quarkus-acceptance-testing | artifact-author | | |

Root apm.yml: add only `./packages/quality/quarkus-acceptance-testing` (acceptance-testing is transitive).
Declared gaps: none. Deferred: SaaS-flow wiring (own run).
