# Unverified Register, Risks and Bibliography

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). The research file reports a quality score of 89% (4 unverified, 2 irresolvable items). This register lists 8 unverified items (U1 to U4 from the research, U5 to U8 added while authoring; U6 and U8 are not resolvable from documentation; U8 is the research's irresolvable item, filed here because the text tag is (unverified)), 0 other irresolvable items and 10 medium-confidence items (M1 to M10).

## Version-lifetime risk

- Quarkus 4.0.0.Beta1 was published 2026-10-01 and the final release is "planned for the end of November" (https://quarkus.io/blog/quarkus-4-0-0-beta1-released/). No Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence; the Beta1 post does not mention Camel Quarkus). The highlights list Java 21 as the new base version. Plan a migration with no known date and do not assume Quarkus 4 compatibility.
- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30 (https://quarkus.io/releases). The Camel Quarkus-specific end date is not published: the "LTS Until" column is blank on https://camel.apache.org/camel-quarkus/latest/. Applying the Quarkus date to Camel Quarkus is an inference (unverified, U6).
- Camel Quarkus 3.40.0 was released 2026-09-28 (https://camel.apache.org/releases/) and the research ran on 2026-10-14. Docs may still change; patch releases are expected.

## Unverified items

- **U1** Log EIP language: the page says the EIP logs "only ... Simple language", yet `logLanguage` / `camel.main.logLanguage` exist. Do not state either as fact.
- **U2** No official quantitative performance overhead figures for the log component. Qualitative only: `maxChars` caps each line, `showFuture` blocks, throughput logging reduces volume, JSON `print-details` is "costly".
- **U3** camel-mdc versus Quarkus Vert.x MDC propagation on Camel async threads.
- **U4** No official Quarkus or Camel Quarkus API found for asserting log output in tests.
- **U5** Whether ArC removes an `@Identifier`-only bean (the CDI reference does not say; `@Named` beans are unremovable; recommend `@Unremovable`). Camel's name lookup with `@Identifier` is NOT unverified: it is documented (high confidence) on https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html.
- **U6** The Camel Quarkus-specific support end date for 3.40: the "LTS Until" column is blank on https://camel.apache.org/camel-quarkus/latest/; not resolvable from documentation. Applying the Quarkus date (2027-09-30) is an inference only.
- **U7** Native build log output equals the JVM output (the `mvn verify -Dnative` expectation in integration-examples): not checked.
- **U8** Which `quarkus.camel.mdc.*` properties are build-time (not resolvable from documentation). Impact: a runtime override of `quarkus.camel.mdc.enabled` may silently fail. Workaround: set it in `application.properties` at build time; check the mdc extension page lock icons or `MdcConfig` in apache/camel-quarkus.

## Medium-confidence items

- **M1** `camel.main.logMask` (and `camel.main.*` in general) in Camel Quarkus: only the `durationMax*` family is stated.
- **M2** Stream-caching guidance (the manual page is ambiguous; the default `true` comes from the main page).
- **M3** Log EIP logger-name strategy.
- **M4** Native-mode reflection for registry-only beans.
- **M5** Absence of log-specific entries in the per-version migration guides (not each re-read).
- **M6** `quarkus.log.level`, `category` and `min-level` defaults and build-time behaviour, and the console format pattern with `%X{...}`, read on the unversioned "Latest" Quarkus guide.
- **M7** No Camel Quarkus build on Quarkus 4 is known (absence of evidence).
- **M8** Legacy MDC key set (`camel.stepId`, `camel.transactionKey`) from the unversioned legacy manual page.
- **M9** Custom mask wiring: a `MaskingFormatter` bean bound as `CamelCustomLogMask` (research recommendation, not confirmed in a versioned 3.40 page).
- **M10** Quarkus JSON logging and MDC propagation claims (`mdc.flat-fields`, `pretty-print`, `excluded-keys`, `print-details`, format ignoring, Vert.x MDC propagation) from https://quarkus.io/version/3.40/guides/logging: coverage of the page by the research is not recorded.

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| Context-wide masking (medium confidence) | SKILL.md Ask First, Quick Reference; masking, quarkus-logging, migration, integration-examples; evaluation-scenarios 5 | M1 |
| Streaming bodies (medium confidence, unversioned ambiguous manual page) | SKILL.md Ask First; never-do 4; evaluation-scenarios 5 | M2 |
| Log EIP logger name (medium confidence) | SKILL.md Ask First; log-component-options | M3 |
| Native-mode beans (medium confidence) | SKILL.md Ask First; masking; integration-examples | M4 |
| No log-specific migration entries (medium confidence) | migration-guide | M5 |
| (medium confidence, read on the unversioned "Latest" guide) | SKILL.md Ask First (category levels and TRACE), Quick Reference (`quarkus.log.level` / `min-level`); mdc (console format pattern); quarkus-logging; never-do 5; evaluation-scenarios 4 | M6 |
| No Camel Quarkus build on Quarkus 4 (medium confidence, absence of evidence) | SKILL.md Version-lifetime risk; migration-guide; evaluation-scenarios 3; this register | M7 |
| MDC key set versus legacy page (medium confidence) | mdc; migration-guide | M8 |
| Log EIP language (unverified) | SKILL.md Ask First; log-component-options | U1 |
| Performance numbers (unverified) | this register only | U2 |
| MDC on async threads (unverified) | SKILL.md Ask First; mdc | U3 |
| Asserting log text in tests (unverified) | SKILL.md Ask First; integration-examples | U4 |
| ArC removal of an `@Identifier`-only bean (unverified) | masking; integration-examples | U5 |
| Camel Quarkus-specific end date (unverified) | SKILL.md Version-lifetime risk; this register | U6 |
| (log output unverified) | integration-examples verification commands | U7 |
| (medium confidence for the wiring) | SKILL.md Ask First (free-form body PII row); masking (custom mask wiring) | M9 |
| (medium confidence, JSON claims from the Quarkus 3.40 guide, coverage not recorded) | SKILL.md Ask First (text vs JSON console), Quick Reference (JSON `mdc.flat-fields` / `pretty-print`); quarkus-logging; masking; mdc | M10 |
| (unverified) mdc build-time properties | mdc | U8 |

## Source Bibliography

All fetched 2026-10-14. camel.apache.org pages have no page date and are the current stable 3.40.x / 4.22.x docs. No community sources were used.

- https://camel.apache.org/releases/ (Camel Quarkus 3.40.0 2026-09-28, LTS; Camel 4.22.1 2026-09-17)
- https://camel.apache.org/camel-quarkus/latest/ (version table: Camel 4.22.1, Quarkus 3.40.1, GraalVM 25.0.4.1)
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/log.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mdc.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/core.html (no logging content)
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/configuration.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/command-mode.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html (no logging content)
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
- https://camel.apache.org/components/4.22.x/log-component.html
- https://camel.apache.org/components/4.22.x/eips/log-eip.html
- https://camel.apache.org/components/4.22.x/others/mdc.html
- https://camel.apache.org/components/4.22.x/others/main.html
- https://camel.apache.org/manual/mdc.html (legacy MDC, unversioned, marked deprecated)
- https://camel.apache.org/manual/stream-caching.html (ambiguous; not relied on for defaults)
- https://quarkus.io/guides/logging ("Latest" selector) and https://quarkus.io/version/3.40/guides/logging (JSON and MDC propagation)
- https://quarkus.io/version/3.40/guides/cdi-reference
- https://camel.apache.org/releases/q-3.40.0/ (Java 17 and 21; no release date, no Camel or Quarkus version on the page)
- https://quarkus.io/releases ; https://quarkus.io/blog/quarkus-4-0-0-beta1-released/
- Validation, found via search and not opened: Maven Central pages for camel-quarkus-mdc 3.40.0 and camel-quarkus-log 3.40.0
