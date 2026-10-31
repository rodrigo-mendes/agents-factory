# Unverified Register, Risks and Bibliography

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). The research file reports a quality score of 93% and a deep run that used all 3 iterations. This register lists **5 unverified** items (U1 to U5), **1 irresolvable** item (I1), **13 medium-confidence** items (M1 to M13) and **1 coverage limit** (L1).

## Tag to register mapping

Classes: High / no tag (versioned official page) may appear in Always Do, Never Do (and its alternatives) and Quick Reference. `(medium confidence)` appears only in Ask First, Quick Reference and blueprints, never in Always Do or Never Do. `(unverified)` and `(irresolvable)` are flagged inline, never asserted.

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Version Context, row "Old artifact" (stub removal date) | U2 |
| (unverified) | SKILL.md Version-lifetime risk (Camel Quarkus end date) | U4 |
| (unverified) | SKILL.md Ask First, row "External systems" (`@InjectMock` with by-name beans) | U3 |
| (unverified) | SKILL.md Ask First, row "NotifyBuilder" | U1 |
| (unverified) | SKILL.md Ask First, row "Keeping `camel-quarkus-junit5`" | U2 |
| (unverified) | integration-examples.md, section Mockito | U3 |
| (unverified) | integration-examples.md, section NotifyBuilder | U1 |
| (unverified) | migration-3-31-rename.md, note after the breaking-changes table | U2 |
| (unverified), U5 | SKILL.md Ask First, row "State isolation" (property name `quarkus.test.class-orderer`) | U5 |
| (unverified) | evaluation-scenarios.md, scenario 2 (junit5 stub removal date) | U2 |
| (unverified) | evaluation-scenarios.md, scenario 2 (`NotifyBuilder` behavior) | U1 |
| (irresolvable) | evaluation-scenarios.md, scenario 2 (`createCamelContext()` guide/source conflict) | I1 |
| (irresolvable) | SKILL.md Ask First, row "Registry binding" | I1 |
| (irresolvable) | integration-examples.md, section Registry binding | I1 |
| (irresolvable) | advice-with-and-lifecycle.md, heading "Overriding createCamelContext" | I1 |
| (medium confidence, absence of evidence) | SKILL.md Version-lifetime risk (no Camel Quarkus build on Quarkus 4) | M9 |
| (medium confidence, absence of evidence) | evaluation-scenarios.md, scenario 3 | M9 |
| (medium confidence) | SKILL.md Ask First, row "Base class" (plain `@QuarkusTest` style) | M1 |
| (medium confidence) | SKILL.md Ask First, row "Integration-test reuse" (subclassing) | M2 |
| (medium confidence) | SKILL.md Ask First, row "NotifyBuilder" (unversioned manual page) | M3 |
| (medium confidence) | SKILL.md Ask First, row "replaceFromWith" | M4 |
| (medium confidence) | SKILL.md Quick Reference, row "Integration test profile" | M10 |
| (medium confidence) | always-do-patterns.md, pattern 2 (`template` declaring superclass) | M6 |
| (medium confidence) | always-do-patterns.md, pattern 6 (subclassing the JVM test class) | M2 |
| (medium confidence) | always-do-patterns.md, pattern 6 (`timer-log` example) | M2 |
| (medium confidence) | native-testing.md, rules table (test may extend the JVM test class) | M2 |
| (medium confidence) | native-testing.md, rules table (prod profile, application.properties ignored) | M10 |
| (medium confidence) | native-testing.md, section Reusing a JVM test (`timer-log`) | M2 |
| (medium confidence) | native-testing.md, section Security (credentials in `start()`) | M8 |
| (medium confidence) | integration-examples.md, section Test resources (`@QuarkusTestResource` global default) | M11 |
| (medium confidence) | integration-examples.md, heading Registry binding | M5 |
| (medium confidence) | integration-examples.md, heading NotifyBuilder | M3 |
| (medium confidence) | advice-with-and-lifecycle.md, `doAfterAll` parameter type | M7 |
| (medium confidence) | advice-with-and-lifecycle.md, `replaceFromWith` | M4 |
| (medium confidence) | evaluation-scenarios.md, scenario 5 (prod profile) | M10 |
| (medium confidence) | evaluation-scenarios.md, scenario 5 (plain `@QuarkusTest` base reused by an integration-test subclass, example style) | M1, M2 |
| (medium confidence, M12) | SKILL.md Ask First, row "State isolation"; always-do-patterns.md, pattern 3 (profile comment) | M12 |
| (medium confidence, M12) | evaluation-scenarios.md, scenario 4 | M12 |
| (medium confidence, M13) | SKILL.md Ask First, row "State isolation" (orderer groups tests of the same profile) | M13 |

## Version-lifetime risk

- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; the highlights list Java 21 as the new base version (High, https://quarkus.io/blog/quarkus-4-0-0-beta1-released/, fetched 2026-10-14). No Camel Quarkus build on Quarkus 4 is known; the Beta1 post does not mention Camel Quarkus (medium confidence, absence of evidence). Do not assume Quarkus 4 compatibility.
- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30 (High, https://quarkus.io/releases). The Camel Quarkus-specific end date is (unverified) (U4, not resolvable from documentation); applying the Quarkus date is an inference.
- Camel Quarkus 3.40.0 was released 2026-09-28 and is marked LTS (High, https://camel.apache.org/releases/), 16 days before the research date. Patch releases are expected.
- `camel-quarkus-junit5` 3.40.0 still exists on Maven Central as a deprecated stub (High, POM URL in the bibliography). Its removal date is (unverified) (U2); the 3.31.0 guide promised removal at 3.34.0. Migrate to `camel-quarkus-junit` rather than rely on the stub.

## Unverified items

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | `NotifyBuilder` behavior against the shared `CamelQuarkusTestSupport` context (not in the 3.40 guide or source) | Tests may be flaky; prefer `MockEndpoint`/AdviceWith |
| U2 | When the `camel-quarkus-junit5` stub is removed (3.31 promised 3.34; stub still published at 3.40.0) | Build may break on a later release; depend on `camel-quarkus-junit` only |
| U3 | `@InjectMock` with beans a route looks up by name; Quarkus documents `@InjectMock` generically only | Mock may not reach the route; prefer `MockEndpoint`/AdviceWith |
| U4 | Camel Quarkus-specific LTS end date for 3.40 (blank "LTS Until" column on https://camel.apache.org/camel-quarkus/latest/); not resolvable from documentation | Support planning: Quarkus 3.40 LTS runs to 2027-09-30, as an inference only; watch https://camel.apache.org/releases/ |
| U5 | The property name `quarkus.test.class-orderer`: stated in the Camel research as from the Quarkus 3.40 guide, not named in `developing-quarkus-junit-v3-40` (whose blueprints/profiles-and-resources.md states only that the Quarkus orderer groups tests that need the same application instance: medium, M13) | Do not rely on the property name; group tests by `@TestProfile` manually |

## Irresolvable items (do not assert)

| ID | Item | Impact | Workaround |
|---|---|---|---|
| I1 | The 3.40 testing guide shows overriding `createCamelContext()` with a `super` call, but the 3.40.0 source of `CamelQuarkusTestSupport` declares only `camelContextSupplier()` and `bindToRegistry(Registry)`; `AbstractTestSupport` was not read | A guide sample may not compile | Configure through CDI beans or `@BindToRegistry`, or compile once; follow-up: read `AbstractTestSupport` at tag 3.40.0 |

## Medium-confidence items

| ID | Item | Evidence |
|---|---|---|
| M1 | Plain `@QuarkusTest` style with `@Inject CamelContext`/`ProducerTemplate` as base | `main`-branch examples (https://github.com/apache/camel-quarkus-examples) |
| M2 | An `@QuarkusIntegrationTest` subclassing a plain `@QuarkusTest` class (reuse as integration test) | `main`-branch example https://github.com/apache/camel-quarkus-examples/blob/main/timer-log/src/test/java/org/acme/timer/log/TimerLogIT.java |
| M3 | `NotifyBuilder` API | unversioned manual page https://camel.apache.org/manual/notify-builder.html |
| M4 | `replaceFromWith` | Camel AdviceWith manual, not on the 3.40 Camel Quarkus page |
| M5 | Registry-binding options | guide and 3.40.0 source differ (see I1) |
| M6 | The `template` field's declaring superclass | not read |
| M7 | The `doAfterAll` parameter type `QuarkusTestContext` | taken from the research sample, not separately confirmed |
| M8 | Credential-handling advice for test resources | stated as practice, no official page recorded |
| M9 | No known Camel Quarkus build on Quarkus 4 | absence of evidence; https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ does not mention Camel Quarkus |
| M10 | Integration tests run in the `prod` profile and ignore `src/test/resources/application.properties` | Quarkus 3.40 guide read partly (L1) |
| M11 | `@QuarkusTestResource` is global by default | Quarkus 3.40 guide read partly (L1) |
| M12 | A different `@TestProfile` restarts Quarkus (and the CamelContext) | Quarkus 3.40 guide read partly (L1); same tag as M1 in `developing-quarkus-junit-v3-40` |
| M13 | The Quarkus orderer groups tests of the same profile to reduce restarts | Same tag as M1 in `developing-quarkus-junit-v3-40` (blueprints/profiles-and-resources.md, medium); Quarkus 3.40 guide read partly (L1) |

## Coverage limits

| ID | Limit |
|---|---|
| L1 | https://quarkus.io/version/3.40/guides/getting-started-testing was read for the first 100000 of 108136 characters; statements from the unread tail are medium confidence |

## Source Bibliography

All fetched 2026-10-14. camel.apache.org pages carry no page date and are the current stable 3.40.x docs. No community sources were used.

- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html (versioned, High)
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html (High)
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html (High)
- https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java (tag source, High)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit/3.40.0/camel-quarkus-junit-3.40.0.pom (High)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/3.40.0/camel-quarkus-junit5-3.40.0.pom (High)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/ (listing, High)
- https://quarkus.io/version/3.40/guides/getting-started-testing (versioned; first 100000 of 108136 characters read, L1)
- https://camel.apache.org/manual/notify-builder.html (unversioned, Medium)
- https://camel.apache.org/releases/q-3.40.0/ (Java 17 and 21, High)
- https://camel.apache.org/camel-quarkus/latest/ ; https://camel.apache.org/releases/ ; https://quarkus.io/releases ; https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ (2026-10-01)
- Validation (`main` branch, not a 3.40.x tag, Medium): https://github.com/apache/camel-quarkus-examples ; https://github.com/apache/camel-quarkus/tree/3.40.0/test-framework
