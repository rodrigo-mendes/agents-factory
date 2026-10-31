# Unverified Register, Risks and Bibliography

Authoring date 2026-10-28; Quarkus research dated 2026-10-14 (ArC, REST, JUnit) and AWS family facts verified 2026-10-28. Back to [SKILL.md](../SKILL.md). Family facts keep the tags of `_family_facts_v3.40.md` and the quarkus-aws-saas family facts.

Header counts: 4 unverified (U1-U4), 0 irresolvable, 7 medium-confidence (M1-M7), 1 coverage limit (L1).

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; Java 21 is the new base (High; https://quarkus.io/blog/quarkus-4-0-0-beta1-released/). Quarkus 4 behaviour is out of scope; re-check this skill when 4.0 is final.
- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30; the latest patch is 3.40.1.1 (2026-10-19), fetched 2026-10-28 via the family facts (https://quarkus.io/releases) (High). Patches may change details: re-check edge behaviour.
- No Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence, M7). Plan a migration with no known date.
- The refactoring method is version-independent; only the Quarkus-specific rules above age with the release line.

## Unverified items

4 unverified items. U2 cannot be resolved from documentation: do not assert it.

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | The general refactoring method (Extract Method, Extract Class, DRY, records, facade) and the Fowler catalog URL are stated as team practice; no page was read for this skill and the catalog URL is an (unverified) pointer | Treat as team practice, not as a Quarkus claim; read https://refactoring.com/catalog/ before citing it as evidence |
| U2 | Whether ArC removes a bean qualified only with `@Identifier` (not injected), and whether Camel Quarkus marks name-referenced beans unremovable. The CDI reference does not say | Keep `@Unremovable` on such beans when moving them; follow-up: ArC processor source on the 3.40 branch, or a check of the removed-beans list |
| U3 | Minimum Java version for Quarkus 3.40 (not on the fetched pages; Camel Quarkus 3.40 supports Java 17 and 21) | Records need a JDK that supports them; confirm the build JDK before using them |
| U4 | Dev-mode ArC endpoint paths (`/q/arc`, `/q/arc/beans`, `/q/arc/removed-beans`): listed as representative by the ArC research, page not recorded | Use as a hint only; confirm in the running dev UI |

## Irresolvable items

0 irresolvable items. The item the research could not resolve (U2) carries the `(unverified)` tag in the text and is listed above.

## Medium-confidence items

7 medium-confidence items.

| ID | Item | Why medium |
|---|---|---|
| M1 | Package-private rather than private injection members, and `quarkus.arc.transform-private-injected-fields=true` | ArC research kept it at medium: single source (CDI reference), no verbatim passage recorded |
| M2 | Eager creation with `@Startup` or `StartupEvent` versus lazy creation of normal-scoped beans on the first proxy call, applied to moved init logic | ArC research kept it at medium: single source |
| M3 | `@ServerExceptionMapper` in a resource class applies only to that class; Quarkus REST does not log exceptions by default | REST research M4: single source, partly read |
| M4 | No page read states a preference between constructor and field injection; the REST guide says resources may use either (medium confidence: guide read only partly, REST skill register M11), the CDI reference says `@Inject` may be omitted on a single constructor | Absence of evidence for a recommendation; the "either" claim has no recorded verbatim quote (rule 13) |
| M5 | A normal-scoped class bean can be mocked with `@InjectMock` without an interface | Inferred from the guide's scope rule and from example code in the ArC research (class-typed `@InjectMock`), not from a quoted sentence |
| M6 | The AWS client wrapper, the resource body and the Lambda handler shape in the examples (`SqsClient` calls, `RequestHandler`, `@Named` handler bean) | Illustrative code, not read from a page; the Quarkus rules they demonstrate are sourced separately |
| M7 | No Camel Quarkus build on Quarkus 4 | Absence of evidence (family fact) |

## Coverage limits

1 coverage limit.

| ID | Page | Limit |
|---|---|---|
| L1 | https://quarkus.io/version/3.40/guides/getting-started-testing | Read the first 100,000 of 108,136 characters; the `@InjectMock`, `convertScopes`, `@TestHTTPEndpoint` and `quarkus-junit-mockito` claims come from the part read and no verbatim quote is recorded, so they carry (medium confidence, L1) wherever they appear (same tag as the ArC skill and the Camel bean register M15/L2) |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified, U1); "register U1" | SKILL.md Version Context and the Method (team practice) block; always-do and never-do method sections; refactor-recipe | U1 |
| (unverified, U2) | SKILL.md Ask First (moved bean qualified only with `@Identifier`); always-do (pointer only); reviewer-checklist Q2 | U2 |
| (unverified, U3); (unverified) minimum Java | SKILL.md Version Context and Ask First; refactor-recipe; evaluation-scenarios | U3 |
| (unverified, U4) | SKILL.md Quick Reference; refactor-recipe step 6 | U4 |
| (medium confidence, M1) | SKILL.md Ask First; package-taxonomy; before-after-examples; reviewer-checklist Q11 | M1 |
| (medium confidence, M2) | SKILL.md Ask First; reviewer-checklist Q10 | M2 |
| (medium confidence, M3) | SKILL.md Ask First; reviewer-checklist Q10 | M3 |
| (medium confidence, M4) | SKILL.md Ask First | M4 |
| (medium confidence, L1) `@InjectMock`, `convertScopes`, `@TestHTTPEndpoint`, `quarkus-junit-mockito` | SKILL.md Version Context, Ask First (scope of a new bean; scope change and mocking) and Quick Reference; always-do (method section: test coupling); never-do (method section: scope change, pointer only); evaluation-scenarios 4; reviewer-checklist Q3 | L1 |
| (medium confidence, M5) | SKILL.md Ask First | M5 |
| (medium confidence, M6) | always-do (handler example and its scope note); before-after-examples | M6 |
| (medium confidence, absence of evidence, M7) | this file, Version-lifetime risk | M7 |

## Source Bibliography

All Quarkus pages fetched 2026-10-14 by the research runs unless noted. quarkus.io/version/3.40 pages document the current stable LTS. No community sources were used as evidence.

- https://quarkus.io/version/3.40/guides/cdi-reference (read in full)
- https://quarkus.io/version/3.40/guides/cdi
- https://quarkus.io/version/3.40/guides/rest
- https://quarkus.io/version/3.40/guides/validation
- https://quarkus.io/version/3.40/guides/getting-started-testing (first 100,000 of 108,136 characters, L1)
- https://quarkus.io/guides/aws-lambda (verified by the orchestrator 2026-10-28)
- https://quarkus.io/releases
- https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ (2026-10-01)
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html
- https://camel.apache.org/releases/q-3.40.0/ (Java 17 and 21)
- https://refactoring.com/catalog/ (pointer only, no page read, (unverified) U1)
- Factory provenance (names only, not shipped with the skill): `research_Quarkus_ArC_v3.40.md`, `research_Quarkus_REST_v3.40.md`, `research_Quarkus_JUnit_v3.40.md`, `_family_facts_v3.40.md`, `quarkus-aws-saas/_family_facts_v3.40.md`
- Quarkus-specific rule in this package: `quarkus-clean-code`. No OCI skill or rule is a source.
