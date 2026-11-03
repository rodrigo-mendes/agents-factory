# Unverified Register, Risks and Bibliography

Research date 2026-10-31. Back to [SKILL.md](../SKILL.md). Research quality score reported by the research file: 89%. This register lists **3 unverified items (U1-U3), 2 irresolvable items (I1-I2), 6 medium-confidence items (M1-M6), 2 coverage limits (L1-L2)**.

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
| (unverified) hook `order` direction | SKILL.md Ask First; steps-and-state.md | U1 |
| (unverified) fast-jar path `quarkus-run.jar` | runner-patterns.md | U2 |
| (unverified) official compatibility of `quarkus-cucumber` 1.3.0 with Quarkus 3.40 | never-do-patterns.md; evaluation-scenarios.md | U3 |
| (unverified) parallel run of B1 | steps-and-state.md | U3 |
| (unverified) `mvn verify` command row | SKILL.md Quick Reference | U3 |
| (medium confidence) B1 `Main.run` inside `@QuarkusIntegrationTest` | SKILL.md; runner-patterns.md | M1 |
| (medium confidence) naming strategy `long` | SKILL.md Ask First; runner-patterns.md; migration-guide.md | M2 |
| (medium confidence) parallel execution keys | SKILL.md Ask First; steps-and-state.md | M3 |
| (medium confidence) hook-launched jar and Dev Services | SKILL.md Ask First; runner-patterns.md | M4 |
| (medium confidence) suite annotation overrides properties file | steps-and-state.md | M5 |
| (medium confidence) `-Dcucumber.filter.tags` override | always-do-patterns.md; steps-and-state.md | M6 |
| High (shared version facts) | Version Context | family-facts sources in the [bibliography](#source-bibliography) |

## Version-lifetime risk

- Cucumber 8.0.0 was released 2026-09-24 and 8.0.4 on 2026-10-02 (High, CHANGELOG): the line moves fast; re-check the CHANGELOG before pinning a newer patch.
- Quarkus 3.40 LTS was released 2026-09-30 (High, https://quarkus.io/version/3.40/guides/getting-started-testing); Quarkus 4 is out of scope and not verified against Cucumber 8.
- `quarkus-cucumber` main is unreleased (Quarkus 3.31.1, Cucumber 7.34.2); a release with the JUnit 6 fix may change the Path A decision.
- B1 depends on `io.cucumber.core.cli.Main` staying public; Cucumber 8 made many classes final (CHANGELOG 8.0.0), so a later 8.x could change it (medium confidence, see M1).
- B1 runs Cucumber's CLI inside a Jupiter test, not the JUnit Platform engine; the intent of family rule 7 (no `cucumber-junit`) is kept.

## Unverified items

- U1. Direction of hook `order` (before low-to-high, after high-to-low is common but not stated in the README read).
- U2. The fast-jar path `target/quarkus-app/quarkus-run.jar` in a page read for this research.
- U3. Items not confirmed by an official page: `quarkus-cucumber` 1.3.0 officially supported on Quarkus 3.40 (a spike passed, no doc says so); behaviour of parallel execution with B1; output of the representative `mvn verify` command.

## Irresolvable items

- I1. Exact RestAssured version in the Quarkus 3.40 BOM: not in the first 100000 characters read, not in build-parent. Impact low: BOM-managed, no explicit version.
- I2. Official mechanism for a non-Jupiter engine to reuse an app started by `@QuarkusTest` or `@QuarkusIntegrationTest`: none in the 3.40 testing guide (read in full). B1 works around it with a public API call proven by the spike; that is not an official mechanism.

## Medium-confidence items

- M1. B1: `@QuarkusIntegrationTest` plus `io.cucumber.core.cli.Main.run(args, classLoader)`, RestAssured configured by Quarkus. Evidence: orchestrator spike on 2026-10-31 (Quarkus 3.40.1, Cucumber 8.0.4, JDK 21, Maven 3.9.16, Surefire/Failsafe 3.5.4): 2 scenarios passed, Failsafe tests=1 failures=0. No official page shows it.
- M2. `cucumber.junit-platform.naming-strategy=long` for Failsafe 3.5.4+, `surefire` for 3.5.2 and below (single source, engine README; Failsafe current 3.6.1).
- M3. Parallel keys and the `max-pool-size` caveat (engine README only).
- M4. Hook-launched `ProcessBuilder` app (assembled from documented pieces) and Dev Services not starting for such a jar.
- M5. A `@ConfigurationParameter` on the suite takes precedence over `junit-platform.properties` (JUnit Platform behaviour not re-read).
- M6. `-Dcucumber.filter.tags=...` on the Maven command line overriding the tag filter.

## Coverage limits

- L1. Quarkus 3.40 `bom/application/pom.xml`: first 100000 of 318255 characters read.
- L2. quarkus-cucumber issues list: page 1 only (25 of 33 issues).

## Source Bibliography

All fetched 2026-10-31. Provenance: research file and orchestrator spike of the same date.

- https://github.com/cucumber/cucumber-jvm/blob/main/CHANGELOG.md
- https://raw.githubusercontent.com/cucumber/cucumber-jvm/main/release-notes/v8.0.0.md
- https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-junit-platform-engine
- https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-java
- https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-picocontainer
- https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-jakarta-cdi
- https://quarkus.io/version/3.40/guides/getting-started-testing (read in full)
- https://raw.githubusercontent.com/quarkusio/quarkus/3.40/bom/application/pom.xml (partial, L1)
- https://raw.githubusercontent.com/quarkusio/quarkus/3.40/build-parent/pom.xml
- https://maven.apache.org/surefire/maven-failsafe-plugin/ (3.6.1)
- https://docs.quarkiverse.io/quarkus-cucumber/dev/index.html
- https://github.com/quarkiverse/quarkus-cucumber (issues #298, #32, PR #310, #119; partial, L2)
- https://repo1.maven.org/maven2/io/quarkiverse/cucumber/quarkus-cucumber/maven-metadata.xml
- https://docs.quarkiverse.io/quarkus-wiremock/dev/index.html
