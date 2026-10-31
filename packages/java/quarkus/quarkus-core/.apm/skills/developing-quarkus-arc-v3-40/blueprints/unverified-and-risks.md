# Unverified Register, Risks and Bibliography

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 93% (about 60 claims) from a deep run that used all 3 iterations. Family facts verified by the orchestrator on 2026-10-14 keep the tags of the family facts file.

Header counts: 9 unverified (U1-U9), 0 irresolvable, 9 medium-confidence (M1-M9), 1 coverage limit (L1).

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; Java 21 is the new base (High; https://quarkus.io/blog/quarkus-4-0-0-beta1-released/). As of 2026-10-14 no Camel Quarkus build on Quarkus 4 is known and the post does not mention Camel Quarkus (medium confidence, absence of evidence, M6). Plan a migration with no known date.
- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30 (High; https://quarkus.io/releases). Later patch releases may change details: re-check before relying on edge behaviour.
- The Camel Quarkus-specific support end date for 3.40 is not published (unverified, U5). Applying the Quarkus date to Camel Quarkus is an inference.

## Unverified items

9 unverified items. U1, U2 and U5 are not resolvable from documentation: do not assert them.

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | Whether ArC removes a bean qualified only with `@Identifier` (not injected). The CDI reference does not say; not resolvable from documentation after 3 research iterations | Camel lookup by name could fail at runtime; add `@Unremovable`, use `quarkus.arc.unremovable-types` or `remove-unused-beans=fwk`. Follow-up: ArC processor source on the 3.40 branch, or a test with `/q/arc/removed-beans` |
| U2 | Whether Camel Quarkus 3.40 produces an `UnremovableBeanBuildItem` for beans referenced by name in routes. Not resolvable from documentation; the camel-quarkus-bean page does not cover it | Same as U1; `@Unremovable`. Follow-up: camel-quarkus core/bean deployment processors, 3.40.x branch |
| U3 | Minimum Java version for Quarkus 3.40 (not on the fetched pages; Camel Quarkus 3.40 supports Java 17 and 21, High) | Build toolchain choice; check the 3.40 getting-started prerequisites |
| U4 | `@Disposes` semantics: the 3.40 CDI guide does not describe them; the CDI reference mentions disposers only in the native note | A producer-cleanup example rests on the Jakarta CDI spec, not on Quarkus docs |
| U5 | Camel Quarkus-specific support end date for 3.40 (the "LTS Until" column is blank); not resolvable from documentation | Support planning; do not infer from the Quarkus date |
| U6 | ArC-related items in the Quarkus migration guides 3.16 to 3.39 were not reviewed | Read those guides when upgrading from an older release |
| U7 | `@QuarkusComponentTest` was not verified for 3.40 | No guidance given; check the testing guide |
| U8 | The artifact name `io.quarkus:quarkus-arc`: no page was recorded for it | Confirm in the Quarkus CDI guide or the BOM before relying on it |
| U9 | The dev-mode endpoint list (`/q/arc`, `/q/arc/beans`, `/q/arc/removed-beans`, `/q/arc/observers`): no page was recorded | Representative only; confirm in dev mode |

## Irresolvable items

0 irresolvable items. The items the research could not resolve (U1, U2, U5) carry the `(unverified)` tag in the text and are listed above.

## Medium-confidence items

9 medium-confidence items.

| ID | Item | Why medium |
|---|---|---|
| M1 | Private injection members and `transform-private-injected-fields=true` | Research rating kept at medium: no verbatim passage recorded (summary read) |
| M2 | `@Startup` / `StartupEvent` eager creation | Research rating kept at medium: no verbatim passage recorded (summary read) |
| M3 | Factory-method name `AdditionalBeanBuildItem.unremovableOf`; only `setUnremovable()` was seen. Not used in this skill | Page not read for the name |
| M4 | `@ObservesAsync` usage details and `AsyncObserverExceptionHandler` | Not fully read |
| M5 | Quarkus REST: resources as unremovable roots; default resource scope not covered | REST guide not read by this skill's research; skill `developing-quarkus-rest-v3-40` read it |
| M6 | No Camel Quarkus build on Quarkus 4 | Absence of evidence (family fact) |
| M7 | Definition of "unused" differs between the cdi-reference list and the config-property description | Documentation inconsistency |
| M8 | Absence of `quarkus-junit5*` in the 3.40 testing guide: only the first 100,000 of 108,136 characters were read (L1) | Absence of evidence; the guide names `quarkus-junit` and `quarkus-junit-mockito` |
| M9 | The supported remainder of CDI Full features: decorators, a subset of `BeanManager`, `@SessionScoped` with Undertow | Taken from a research summary; the page passage was not recorded |

## Coverage limits

1 coverage limit.

| ID | Page | Limit |
|---|---|---|
| L1 | https://quarkus.io/version/3.40/guides/getting-started-testing | Read the first 100,000 of 108,136 characters; the claim that only normal-scoped beans can be mocked has a recorded verbatim quote ("basically every scope except @Singleton and @Dependent") and is High; the `convertScopes` and `quarkus-junit-mockito` claims come from the part read and no verbatim quote is recorded, so they carry (medium confidence, L1) wherever they appear (family rule 13; same tag as the refactoring skill, and as M15/L2 in the Camel bean register) |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) removal of an `@Identifier`-only bean; (unverified, U1) | SKILL.md Ask First; bean-removal; migration-guide; evaluation-scenarios | U1 |
| (unverified) Camel Quarkus marking name-looked-up beans unremovable; (unverified, U2) | SKILL.md Ask First; bean-removal | U2 |
| (unverified, U3) minimum Java; (unverified) minimum Java | SKILL.md Version Context and Ask First; migration-guide; evaluation-scenarios | U3 |
| (unverified, U4) `@Disposes`; (unverified) with "register U4" | SKILL.md Ask First; scopes-and-injection | U4 |
| (unverified, U5) Camel Quarkus end date | SKILL.md Version Context; this file | U5 |
| (unverified, U6) migration guides 3.16 to 3.39 | migration-guide | U6 |
| (unverified, U7); (unverified, register U7) `@QuarkusComponentTest` | testing; migration-guide | U7 |
| (medium confidence) private members, transform default; (medium confidence, M1) | SKILL.md Ask First and Quick Reference; scopes-and-injection | M1 |
| (medium confidence) eager startup; (medium confidence, M2) | SKILL.md Ask First; scopes-and-injection | M2 |
| (medium confidence) Name of the build-item factory | cdi-lite-limitations | M3 |
| (medium confidence, M4) async observers | scopes-and-injection | M4 |
| (medium confidence, L1) `convertScopes`, `quarkus-junit-mockito` | SKILL.md Ask First (mocking strategy) and Quick Reference; always-do 6; testing; scopes-and-injection | L1 |
| (unverified, U8) artifact name `io.quarkus:quarkus-arc` | SKILL.md Version Context | U8 |
| (unverified, U9) dev-mode endpoint list | SKILL.md Quick Reference and Verification Loop; bean-removal; migration-guide | U9 |
| (medium confidence, M9) supported remainder of CDI Full | cdi-lite-limitations | M9 |
| (medium confidence) Quarkus REST, JAX-RS roots; (medium confidence, M5) | SKILL.md Ask First and Quick Reference; scopes-and-injection | M5 |
| (medium confidence, absence of evidence) Quarkus 4 and Camel Quarkus | SKILL.md Version-lifetime; evaluation-scenarios; this file | M6 |
| (medium confidence, M7) definition of "unused" | bean-removal | M7 |
| (medium confidence, absence of evidence, M8) `quarkus-junit5*` absent from the partly read testing guide | testing; migration-guide | M8 |

## Source Bibliography

All fetched 2026-10-14. quarkus.io/version/3.40 pages document the current stable LTS. camel.apache.org pages carry no page date. No community sources were used as evidence. The fetch tool returns summaries, so confirm exact wording before quoting.

- https://quarkus.io/version/3.40/guides/cdi-reference (read in full)
- https://quarkus.io/version/3.40/guides/cdi
- https://quarkus.io/version/3.40/guides/cdi-integration
- https://quarkus.io/version/3.40/guides/getting-started-testing (first 100,000 of 108,136 characters, L1)
- https://quarkus.io/version/3.40/guides/config-reference
- https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html
- https://camel.apache.org/camel-quarkus/latest/
- https://camel.apache.org/releases/
- https://camel.apache.org/releases/q-3.40.0/ (Java 17 and 21; shows no release date)
- https://quarkus.io/releases
- https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ (2026-10-01)
- Orchestrator-verified family facts for the 3.40 skill family (releases, LTS dates, Camel test artifact rename, RouteBuilder scope rule)

Validation only, not evidence: https://quarkus.io/blog/unused-beans/ (unversioned and older; it restates the same removal roots).
