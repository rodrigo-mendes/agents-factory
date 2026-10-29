# Unverified Register, Risks and Bibliography

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 85% and a deep run that used all 3 iterations. Family facts verified by the orchestrator on 2026-10-14 are used with the tags of the family facts file.

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; Java 21 is the new base (High; https://quarkus.io/blog/quarkus-4-0-0-beta1-released/). As of 2026-10-14 no Camel Quarkus build on Quarkus 4 is known and the post does not mention Camel Quarkus (medium confidence, absence of evidence; M10). Plan a migration with no known date.
- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30 (High; https://quarkus.io/releases).
- The Camel Quarkus-specific support end date for 3.40 is not published (unverified; U2). Applying the Quarkus date to Camel Quarkus is an inference.
- 3.40.0 was released 2026-09-28, 16 days before the research date. Patch releases are expected.

## Unverified items

14 unverified items (U1-U14; U14 moved from `developing-quarkus-arc-v3-40`, where it was U2; the ArC U1 is the same open question as U1 here and was merged into it). U1 and U2 are not resolvable from documentation: do not assert them.

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | Whether ArC removes a bean named only with `@Identifier` (no `@Named`, not injected) when it is only looked up through the Camel registry. The Quarkus CDI reference does not say; not resolvable from documentation. The `@Identifier` lookup from Camel routes itself is High (Camel Quarkus CDI page) | "no bean" in production paths that tests do not exercise; add `@Unremovable`, use `quarkus.arc.unremovable-types` or `remove-unused-beans=fwk`. Follow-up: ArC processor source on the 3.40 branch, or a test with `/q/arc/removed-beans` |
| U2 | Camel Quarkus-specific support end date for 3.40 (the "LTS Until" column is blank); not resolvable from documentation | Support planning; do not infer from the Quarkus date |
| U3 | Package of `org.apache.camel.spi.Registry` on the Camel Quarkus page | Confirm the import in your build |
| U4 | Options of the Log component used after bean calls: the log extension page has no options of its own (see the skill `developing-camel-quarkus-log-v3-40`); the component options were not researched here | Check the Camel 4.22.x log component page |
| U5 | `camel-quarkus-jaxb` native specifics (registration of JAXB classes) | Check the extension page |
| U6 | Whether a Camel registry lookup by name returns the `@InjectMock` mock | Test in your build |
| U7 | Bean-specific example names in `camel-quarkus-examples` | Search the repository |
| U8 | Security of building `bean:` or `class:` URIs from untrusted input (inferred; `class:` can instantiate by FQCN) | No official statement; keep bean names fixed in routes |
| U9 | `class:` component options, and the claim that `.bean(MyClass.class)`, `.bean(new X())` and `class:fqcn` have no CDI lifecycle | Check the Camel 4.22.x page |
| U10 | Bean Method language options | Check the Camel 4.22.x page |
| U11 | Release in which the deprecated `camel-quarkus-junit5` stub will be removed (the 3.31 guide said "until 3.34.0 is released"; the stub is still published at 3.40.0, High, see [migration guide](./migration-guide.md)) | Use `camel-quarkus-junit` |
| U12 | Redelivery defaults that apply when a bean method throws (not verified in this run; the Dead Letter Channel default of 6 redeliveries / 1 s was seen only in a tool summary) | Configure `onException` or the error handler explicitly |
| U13 | Route metrics for bean calls through `camel-quarkus-micrometer` (the extension page lists no bean-specific metrics; the Micrometer route was not researched) | Check the micrometer extension page |
| U14 | Moved from `developing-quarkus-arc-v3-40` (ID U2 there): whether Camel Quarkus 3.40 produces an `UnremovableBeanBuildItem` for beans referenced by name in routes. Not resolvable from documentation; the camel-quarkus-bean page does not cover it | Same as U1; `@Unremovable`. Follow-up: camel-quarkus core/bean deployment processors, 3.40.x branch |

## Medium-confidence items

16 medium-confidence items (M1-M16; M16 moved from `developing-quarkus-arc-v3-40`).

| ID | Item | Why medium |
|---|---|---|
| M1 | Parameter annotations and unannotated body binding | Single unversioned manual page |
| M2 | Method selection (`@Handler`, pinning with `method=`) and `AmbiguousMethodCallException` on overloads | Unversioned manual page |
| M3 | Return type cannot be `Exchange` | Unversioned manual page |
| M4 | `CompletionStage` return: no timeout, `null` leaves the body unchanged | Unversioned manual page |
| M5 | `lookupByNameAndType` and registry order (ArC first, then `SimpleRegistry`) | Unversioned registry manual |
| M6 | Type+value qualifiers (`int.class 123`) | Unversioned manual page |
| M7 | Scope and discovery: classes need a bean-defining annotation | Page read through the unversioned Quarkus URL, partly read (L1) |
| M8 | ArC removal options (`all`, `fwk`, `none`, `unremovable-types`) | Page read through the unversioned Quarkus URL, partly read (L1) |
| M9 | `serialization-enabled`, no bean-specific entries in the migration index, dependency-management page | Taken from the core research, not re-fetched |
| M10 | No Camel Quarkus build on Quarkus 4 | Absence of evidence |
| M11 | Pinning a method avoids per-call selection cost; error-handling notes | Inference or unversioned page |
| M12 | JAXB-unmarshalled objects bind to bean methods by body type conversion | Unversioned manual page |
| M13 | `scope=Request` gives one instance per exchange for a CDI-managed named bean | The component page states `Request` generally; the CDI case is not stated |
| M14 | `@Named` adds `@Default` when it is the only qualifier | No page recorded |
| M15 | `@InjectMock` needs `quarkus-junit-mockito`; works on normal scopes; `@Singleton` needs `@MockitoConfig(convertScopes = true)` | Unversioned Quarkus guide, partly read (L2) |
| M16 | Moved from `developing-quarkus-arc-v3-40` (ID M5 there): "JAX-RS resources are unremovable roots" (Quarkus REST); default resource scope not covered | REST guide not read by that skill's research; skill `developing-quarkus-rest-v3-40` read it |

## Coverage limits

2 coverage limits.

| ID | Item |
|---|---|
| L1 | The Quarkus CDI reference was read through https://quarkus.io/guides/cdi-reference, "first 100,000 of 104,471 characters". It is cited by the versioned address https://quarkus.io/version/3.40/guides/cdi-reference. The High claims taken from it (`@Identifier` recommendation, unremovable `@Named`/`@Unremovable` beans) were fetched and quoted by the orchestrator on 2026-10-14 (family facts file); M7 and M8 were not cross-checked against the unread remainder |
| L2 | The unversioned Quarkus testing guide https://quarkus.io/guides/getting-started-testing was read to 100,000 of 108,136 characters. The `@InjectMock` claims taken from it (M15) were not cross-checked against the unread remainder |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) ArC removal of an `@Identifier`-only bean | SKILL.md Ask First; always-do-patterns; cdi-and-native; migration-guide; integration-examples; quarkus-arc-integration (as (unverified, U1)) | U1 |
| (unverified) Camel Quarkus end date | SKILL.md Version-lifetime; this file | U2 |
| (unverified) Registry package | SKILL.md Ask First; bean-binding | U3 |
| (unverified) Log component options | integration-examples | U4 |
| (unverified) JAXB native registration | integration-examples | U5 |
| (unverified) mock via registry | testing-with-injectmock | U6 |
| bean-specific example names are unverified | integration-examples | U7 |
| (inferred, unverified) URI from input | SKILL.md Ask First | U8 |
| (unverified) `class:` / Bean Method language options; no CDI lifecycle for `class:fqcn` | SKILL.md Ask First (invocation style); bean-binding | U9, U10 |
| (unverified) stub removal release | migration-guide | U11 |
| (unverified) redelivery defaults | bean-binding | U12 |
| (unverified) bean metrics via micrometer | bean-binding | U13 |
| (medium confidence) `@InjectMock` / `quarkus-junit-mockito` / `convertScopes` | SKILL.md Ask First and Quick Reference; testing-with-injectmock; migration-guide | M15, L2 |
| (medium confidence) parameter annotations, registry order, unannotated binding | SKILL.md Ask First and Quick Reference; bean-binding | M1, M5 |
| (medium confidence) method selection, overloads, return type | SKILL.md Ask First; always-do-patterns; integration-examples; bean-binding | M2, M3 |
| (medium confidence) async return | SKILL.md Ask First; bean-binding | M4 |
| (medium confidence) type+value qualifiers | migration-guide; bean-binding | M6 |
| (medium confidence) scope on a named bean | SKILL.md Ask First; always-do-patterns; cdi-and-native; evaluation-scenarios | M7 |
| (medium confidence) ArC removal | SKILL.md Ask First and Quick Reference; cdi-and-native | M8 |
| (medium confidence, via the core research) | migration-guide; cdi-and-native | M9 |
| (medium confidence, absence of evidence) Quarkus 4 | SKILL.md Version-lifetime; evaluation-scenarios; this file | M10 |
| (inference, medium confidence) pinning cost; (medium confidence) error handling | always-do-patterns; bean-binding | M11 |
| (medium confidence) JAXB body binding | integration-examples | M12 |
| (medium confidence) `Request` scope on a CDI-managed bean | SKILL.md Ask First; always-do-patterns; never-do-patterns | M13 |
| (medium confidence, no page recorded) `@Named` adds `@Default` | cdi-and-native | M14 |
| (unverified, U1) ArC removal of an `@Identifier`-only bean (same row as U1 above) | quarkus-arc-integration | U1 |
| (unverified, U14) Camel Quarkus marking name-looked-up beans unremovable | quarkus-arc-integration | U14 |
| (medium confidence, M16) "JAX-RS resources are unremovable roots" | quarkus-arc-integration | M16 |

## Source Bibliography

All fetched 2026-10-14. camel.apache.org pages have no page date and are the current stable 3.40.x / 4.22.x docs. No community sources were used. The fetch tool returns summaries, so confirm exact wording before quoting. Entries marked via the core research were fetched there, not in this run.

- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/core.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html (via the core research)
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/index.html (via the core research)
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/dependency-management.html (via the core research)
- https://camel.apache.org/camel-quarkus/latest/
- https://camel.apache.org/components/4.22.x/bean-component.html
- https://camel.apache.org/manual/bean-binding.html (unversioned)
- https://camel.apache.org/manual/parameter-binding-annotations.html (unversioned)
- https://camel.apache.org/manual/registry.html (unversioned)
- https://camel.apache.org/releases/ ; https://camel.apache.org/releases/q-3.40.0/ (Java 17 and 21; fetched by the orchestrator)
- https://quarkus.io/version/3.40/guides/cdi-reference (read through https://quarkus.io/guides/cdi-reference, first 100,000 of 104,471 characters; L1)
- https://quarkus.io/guides/getting-started-testing (unversioned, first 100,000 of 108,136 characters; L2)
- https://quarkus.io/releases
- https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ (2026-10-01)
- https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/extensions/bean/deployment/src/main/java/org/apache/camel/quarkus/component/bean/deployment/BeanProcessor.java
- https://github.com/apache/camel-quarkus/issues/4725 (closed 2023-10-30; historical context, more than 12 months old)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-bean/ (3.40.0, 2026-09-24)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/3.40.0/camel-quarkus-junit5-3.40.0.pom (fetched 2026-10-14 by the orchestrator)
- https://github.com/apache/camel-quarkus (repository); https://github.com/apache/camel-quarkus-examples
