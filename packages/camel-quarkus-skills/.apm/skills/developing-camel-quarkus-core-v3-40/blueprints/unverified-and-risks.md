# Unverified Register, Risks and Bibliography

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Research quality score reported by the research file: 86% (12 unverified, 4 irresolvable). This register lists **18 unverified items (U1-U18), 0 irresolvable items, 8 medium-confidence items (M1-M8), 0 coverage limits**. Re-classing against the research: the Camel Quarkus LTS end date and the junit5 stub removal date moved from irresolvable to unverified (U1, U15); "no Camel Quarkus build on Quarkus 4" moved to medium (M1, absence of evidence); the `CamelQuarkusTestSupport` package and `adviceRoute()` signature are resolved in the skill `developing-camel-quarkus-junit-v3-40` and are not register items here; the REST-plus-platform-http coexistence question is U11. U13-U17 are gaps recorded while authoring the skill, not individually traced to the research's count of 12. U18 is the inbound platform-http TLS question from the family facts.

## Contents

- [Tag to register mapping](#tag-to-register-mapping)
- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Source Bibliography](#source-bibliography)

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) Camel Quarkus-specific end date | SKILL.md Version-lifetime risk | U1 |
| (unverified) Java 25 for Camel Quarkus | SKILL.md Version Context; migration-guide.md | U2 |
| (unverified) Maven 3.8.2 / 3.9.16 | SKILL.md Version Context; migration-guide.md | U3 |
| (unverified) `ComponentAddEvent` package | SKILL.md Ask First; integration-examples.md | U4 |
| (unverified) `/q/health` and `/q/metrics` base paths | integration-examples.md | U5 |
| (unverified) build-time vs runtime for `quarkus.camel.*` | native-mode.md | U8 |
| (unverified) kebab-case `camel.main.*` keys | integration-examples.md | U9 |
| (unverified) `showAll` option for 4.22 | integration-examples.md | U10 |
| (unverified) REST resource plus platform-http on one server | SKILL.md Ask First; integration-examples.md | U11 |
| (unverified) removal of an `@Identifier`-only bean | SKILL.md Ask First; always-do-patterns.md | U12 |
| (unverified: the quoted wording comes from a tool summary; re-check before quoting verbatim) | always-do-patterns.md | U13 |
| (unverified) pinned versions in the examples repo | integration-examples.md | U14 |
| (unverified) junit5 stub removal date | never-do-patterns.md | U15 |
| (unverified) dead letter channel default redelivery count and delay | SKILL.md Ask First; integration-examples.md | U16 |
| (log output unverified) | SKILL.md Quick Reference; integration-examples.md | U17 |
| inbound platform-http impact (unverified) | SKILL.md Ask First (TLS scope); tls-and-security.md | U18 |
| (medium confidence, absence of evidence) no CQ build on Quarkus 4 | SKILL.md; migration-guide.md; evaluation-scenarios.md | M1 |
| (medium confidence) REST resource plus `ProducerTemplate` | SKILL.md Ask First; integration-examples.md | M2 |
| (medium confidence) error-handling manual pages | SKILL.md Ask First; integration-examples.md | M3 |
| (medium confidence) `ComponentAddEvent` usage | SKILL.md Ask First; integration-examples.md | M4 |
| (medium confidence) runtime catalog trimming | SKILL.md Ask First; native-mode.md | M5 |
| (medium confidence) `@EndpointInject`/`@Produce` setters | never-do-patterns.md | M7 |
| (medium confidence) `startRouteDefinitions()` after AdviceWith | never-do-patterns.md | M8 |
| High (shared version facts) | Version Context; Version-lifetime risk | family-facts sources in the [bibliography](#source-bibliography) |

U6 (Dev UI and live reload) and U7 (`quarkus create app`) have no tag in the text; they are recorded as gaps. M6 (REST DSL vs Quarkus REST choice) is the Ask First "HTTP surface" row.

## Version-lifetime risk

- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November" 2026; Java 21 is the new base (High, https://quarkus.io/blog/quarkus-4-0-0-beta1-released/).
- No Camel Quarkus build on Quarkus 4 is known and the Beta1 post does not mention Camel Quarkus (medium confidence, absence of evidence); no `quarkus-camel-bom` 4.x was seen on Maven Central at research time. Do not assume Quarkus 4 compatibility.
- Camel Quarkus 3.40.0 was released 2026-09-28 and is marked LTS (High, https://camel.apache.org/releases/), 16 days before the research date, so the docs may still change.
- Quarkus 3.40 is community-maintained until 2027-09-30 (High, https://quarkus.io/releases). The Camel Quarkus-specific end date is (unverified); applying the Quarkus date is an inference.
- Plan a Camel Quarkus 4 migration with no known date.

## Unverified items

- U1. Camel Quarkus-specific support end date for 3.40 ("LTS Until" blank on https://camel.apache.org/camel-quarkus/latest/); not resolvable from documentation. Workaround: Quarkus 3.40 LTS to 2027-09-30, used only as an inference.
- U2. Java 25 support in Camel Quarkus 3.40.
- U3. Maven 3.8.2 minimum and 3.9.16 recommended (page not recorded).
- U4. The `ComponentAddEvent` package.
- U5. The `/q/metrics` and `/q/health` base paths.
- U6. Dev UI and route live-reload specifics.
- U7. The `quarkus create app` CLI.
- U8. Build-time vs runtime flag for each `quarkus.camel.*` property.
- U9. The kebab-case form of `camel.main.*` keys.
- U10. Log `showAll` and other log/bean component options.
- U11. Whether a Quarkus REST resource plus `ProducerTemplate` can coexist with `camel-quarkus-platform-http` / `camel-quarkus-rest` on one HTTP server (no official source shows both). The resource-plus-`ProducerTemplate` pattern itself is M2.
- U12. ArC removal behaviour for a bean named only with `@Identifier`. Lookup of `@Identifier` beans from Camel routes is High (Camel Quarkus CDI page); the Quarkus CDI reference lists only `@Named`, observers and explicit exclusions as unremovable. Recommend `@Unremovable`.
- U13. Exact wording of quotes taken from tool summaries (for example the BOM major.minor sentence).
- U14. Pinned versions in camel-quarkus-examples.
- U15. Removal date of the deprecated `camel-quarkus-junit5` stub. That the 3.40.0 stub exists and what it is: High (3.40.0 POM, "Junit5 (Deprecated)", depends only on `camel-quarkus-junit`, no relocation element).
- U16. Dead Letter Channel default redelivery (6 times, 1 s): seen only in a tool summary.
- U17. Log output of the representative commands (`mvn quarkus:dev`, `mvn test`, `mvn verify -Dnative`).
- U18. Whether the 3.40 TLS bridging affects the inbound platform-http server; not resolvable from documentation (no page states it; family fact).

## Irresolvable items

None remain after re-classing. The `CamelQuarkusTestSupport` package and `adviceRoute()` signature are resolved in the skill `developing-camel-quarkus-junit-v3-40`; do not restate them here.

## Medium-confidence items

- M1. No Camel Quarkus build on Quarkus 4 is known (absence of evidence; the Beta1 post does not mention Camel Quarkus).
- M2. A Quarkus REST resource injecting a `ProducerTemplate` and calling `requestBody("direct:processOrder", ...)` (https://github.com/apache/camel-quarkus-examples, `quarkus-rest-json`, `OrderResource.java`, main branch, pom pins Quarkus platform 3.40.1; not in 3.40.x-tagged docs).
- M3. Error-handling defaults (unversioned Camel manual pages; the dead letter default is U16).
- M4. `ComponentAddEvent` usage.
- M5. Runtime catalog trimming.
- M6. REST DSL vs Quarkus REST choice.
- M7. `@EndpointInject`/`@Produce` setter limitation (single source).
- M8. "`startRouteDefinitions()` is no longer needed" since 3.36 (research quote; the testing guide confirms auto-start and auto-cleanup, not this call).

## Source Bibliography

All fetched 2026-10-14. camel.apache.org pages have no page date and are the current stable 3.40.x docs. No community sources were used.

- https://camel.apache.org/releases/ (3.40.0, 2026-09-28, LTS)
- https://camel.apache.org/releases/q-3.40.0/ (Java 17 and 21; shows no date and no Camel or Quarkus versions)
- https://camel.apache.org/camel-quarkus/latest/ (Camel 4.22.1, Quarkus 3.40.1, GraalVM 25.0.4.1)
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/core.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/{cdi,configuration,native-mode,bootstrap,dependency-management,first-steps,testing}.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/{index,3.31.0,3.33.0,3.35.0,3.36.0,3.38.0,3.39.0,3.40.0}.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/{bean,log,direct,timer,platform-http,microprofile-health,micrometer}.html
- https://camel.apache.org/components/4.22.x/{direct-component,timer-component,others/main}.html
- https://camel.apache.org/manual/{exception-clause,error-handler,exception-redelivery,exception-handling-patterns,rest-dsl}.html (unversioned, medium)
- https://quarkus.io/version/3.40/guides/cdi-reference ; https://quarkus.io/guides/rest
- https://quarkus.io/blog/quarkus-3-40-released/ (2026-09-30)
- https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ (2026-10-01)
- https://quarkus.io/blog/mandrel-25-minimum-version/ (2026-05-29)
- https://quarkus.io/releases (LTS policy)
- https://repo1.maven.org/maven2/io/quarkus/platform/quarkus-camel-bom/ (3.40.1, 2026-09-30)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/3.40.0/camel-quarkus-junit5-3.40.0.pom
- https://github.com/apache/camel-quarkus (repo); https://github.com/apache/camel-quarkus-examples
