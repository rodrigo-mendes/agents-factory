# Unverified Register, Risks and Bibliography

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Header counts: 16 unverified (U1-U16: the research's 11 plus 5 skill-added), 4 irresolvable (I1-I4), 14 medium-confidence (M1-M14), 1 coverage limit (L1). The research file reports 11 unverified and 5 irresolvable items and a quality score of 84%; its fifth irresolvable item (unread migration guides) is filed here as coverage limit L1.

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items (do not assert)](#irresolvable-items-do-not-assert)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; Java 21 is the new base version (https://quarkus.io/blog/quarkus-4-0-0-beta1-released/). That Jackson 3 affects `camel-quarkus-jackson` and JSON binding is (unverified) (U16): research only, not in the family facts and not in the Beta1 highlights quoted there.
- No Camel Quarkus build on Quarkus 4 is known; the Beta1 post does not mention Camel Quarkus (medium confidence, absence of evidence). The research also found no Camel Quarkus 4.x on Maven Central as of 2026-10-14. Pin 3.40.x; do not assume Quarkus 4 compatibility.
- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30 (https://quarkus.io/releases). The Camel Quarkus-specific support end date is (unverified) (U9; the "LTS Until" column is blank on https://camel.apache.org/camel-quarkus/latest/); applying the Quarkus date to Camel Quarkus is an inference.
- Camel Quarkus 3.40.0 was released 2026-09-28 and is marked LTS (https://camel.apache.org/releases/), within 30 days of the research date 2026-10-14, so the docs may still change.

## Unverified items

16 unverified items. U1-U11 come from the research; U12-U16 are skill-added.

- U1. The `.required(boolean)` param builder method.
- U2. `camel-openapi-validator` native support in Camel Quarkus.
- U3. Placeholder resolution in a REST path for openapi-java at build time.
- U4. OIDC configuration with platform-http (guide not fetched).
- U5. Path collision between Quarkus REST and Camel REST.
- U6. REST-specific metrics.
- U7. Performance numbers (no official benchmarks found).
- U8. Release date and Camel version on the `q-3.40.0` page. Superseded for the skill's claims: the release date and the Camel version come from the family facts (https://camel.apache.org/releases/ and https://camel.apache.org/camel-quarkus/latest/); the `q-3.40.0` page shows neither and is cited for Java only.
- U9. The Camel Quarkus-specific LTS end date (not resolvable from documentation).
- U10. Whether `contextPath` overrides the contract base path.
- U11. The property name `camel.dataformat.jackson.auto-discover-object-mapper`.
- U12. The runtime result of setting `SSLContextParameters` on the platform-http server (the sibling platform-http register also lists it).
- U13. Whether the Camel Quarkus 3.40.0 TLS bridging (`quarkus.tls` applied to Camel SSL contexts built from registered beans) affects the inbound REST/platform-http server (not resolvable from documentation; no page states it). Related: the effect of the Quarkus TLS registry on the inbound server.
- U14. When the `camel-quarkus-junit5` stub will be removed. The stub facts live in `developing-camel-quarkus-junit-v3-40`; prefer `camel-quarkus-junit`.
- U15. Java 25 support for Camel Quarkus 3.40.
- U16. That Jackson 3 (Quarkus 4) affects `camel-quarkus-jackson` and REST JSON binding (not in the family facts; research only).

The exact wording of quotes taken from tool-summarised pages is a general caveat, not a counted item.

## Irresolvable items (do not assert)

4 irresolvable items. The text tags them (unverified).

| Id | Item | Impact | Workaround |
|---|---|---|---|
| I1 | Effect of `quarkus.http.root-path` on REST DSL paths | Wrong URLs or permission paths | Test with `curl` in dev mode |
| I2 | `restConfiguration().host()/port()` behaviour under platform-http (ignored or error) | Misleading configuration | Use `quarkus.http.port` only |
| I3 | Whether `apiContextPath` or `/q/openapi` need separate `quarkus.http.auth.permission` entries | Unauthenticated spec exposure | Add an explicit permission for the doc path |
| I4 | Camel `enableCORS` vs Quarkus CORS filter on the same request | Duplicate or conflicting CORS headers | Use only the Quarkus filter |

## Medium-confidence items

14 medium-confidence items.

- M1. REST DSL manual pages (`/manual/rest-dsl*.html`) are unversioned and treated as 4.22.x docs: `bindingMode` values, JSON using Jackson, `skipBindingOnErrorCode`, `inlineRoutes`, response codes, custom error codes 300+, `clientRequestValidation` defaults, contract-first startup failure, `enableCORS` defaults.
- M2. Official example poms and code on the `main` branch (not the 3.40.x tag): `camel-quarkus-jackson` and `camel-quarkus-direct` dependencies, `quarkus-junit` + `rest-assured` test dependencies, Quarkus platform 3.40.1 (supporting evidence only; the fact itself comes from the Camel Quarkus docs index).
- M3. `type`/`outType` on verbs: the example uses `type` only; `outType` follows the unversioned binding manual.
- M4. Contract-first: one `direct:<operationId>` route per operation (unversioned OpenAPI manual).
- M5. CORS comparison, including the default origin `*` of `enableCORS(true)` (downgraded from the research's High forbidden-pattern tag because its evidence is the unversioned binding manual); Quarkus CORS and root-path defaults (Quarkus guides, pinned URLs not re-fetched).
- M6. No Camel Quarkus build on Quarkus 4 (absence of evidence).
- M7. AtlasMap removal (search summary of the Camel 4 migration guide).
- M8. `.param()` syntax (search snippet of the latest manual).
- M9. Native registration: `@RegisterForReflection`, contract files in the native image, `src/main/openapi` location; CDI unavailable in `configure()` at build time and REST unsupported in `LambdaRouteBuilder` (openapi-java page). Reason (evidence rule): the contract-file location and the plural `includes` property name rest on a main-branch example and investigator notes, not on a versioned page read in full by the researcher.
- M10. Default base path `/` hiding other endpoints.
- M11. Code-first spec publishing: the `apiContextPath` example value (main-branch example) and the merge of `expose.enabled` into `/q/openapi` (partial evidence). The `expose.enabled` default `false` (build time) is High: versioned openapi-java extension page.
- M12. Testing details: `camel-quarkus-junit` needed only for `CamelQuarkusTestSupport`, test port 8081, RestAssured timeout 30 s, Quarkus authorization reference.
- M13. Camel 4.22 upgrade-guide items (Content-Type from `produces`, `fileNameExtWhitelist`, `vertx-http` header stripping).
- M14. Authenticated-user header (investigator notes).

Resolved as High (rule: versioned page, single source does not lower confidence): alternate transport `camel-quarkus-servlet` (rest extension page), `missingOperation` and platform-http endpoint defaults (components/4.22.x pages), ObjectMapper reuse via `autoDiscoverObjectMapper` (versioned jackson extension page; only the property-name form is U11), `expose.enabled` default (openapi-java page). Moved out of the medium list: Jackson 3 impact is now U16 (not in the family facts).

## Coverage limits

1 coverage limit.

- L1. Nine Camel Quarkus migration guides were not read for REST impact: 3.17, 3.18, 3.23, 3.26, 3.27, 3.33, 3.35, 3.36, 3.38. Possible missed breaking change; read each before upgrading from 3.15: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/index.html

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified): Camel Quarkus-specific LTS end date | SKILL.md Version Context | U9 |
| (unverified): Java 25 for Camel Quarkus | SKILL.md Version Context | U15 |
| (no tag in text): release date and Camel version are not on the `q-3.40.0` page; superseded by the family facts | SKILL.md Version Context (Java row note) | U8 |
| (unverified): effect of `quarkus.http.root-path` on REST DSL paths | SKILL.md Quick Reference; integration-examples; evaluation-scenarios | I1 |
| (unverified): `host()/port()` behaviour under platform-http | always-do-patterns 5; never-do-patterns 1 | I2 |
| (unverified): doc path needs its own permission entry | SKILL.md Ask First; openapi-contract-first; validation-and-cors; evaluation-scenarios | I3 |
| (unverified): Camel CORS and Quarkus CORS filter on one request | SKILL.md Ask First; validation-and-cors; never-do-patterns; evaluation-scenarios | I4 |
| Coverage limit (no tag in text): nine unread migration guides | migration-guide | L1 |
| (unverified): `camel-openapi-validator` native support | SKILL.md Ask First; validation-and-cors | U2 |
| (unverified): whether `contextPath` overrides the contract base path | SKILL.md Ask First; never-do-patterns | U10 |
| (unverified): `.required(boolean)` builder method | rest-dsl-configuration | U1 |
| (unverified): placeholder resolution in a REST path at build time | never-do-patterns | U3 |
| (unverified): OIDC configuration details | validation-and-cors | U4 |
| (unverified): Quarkus REST and Camel REST path collision | validation-and-cors; integration-examples | U5 |
| (unverified): REST metrics and performance numbers | rest-dsl-configuration | U6, U7 |
| (unverified): `camel.dataformat.jackson.auto-discover-object-mapper` name | rest-dsl-configuration | U11 |
| (unverified): runtime result of `SSLContextParameters` on the server | never-do-patterns | U12 |
| (unverified): TLS bridging or TLS registry effect on the inbound server | never-do-patterns; always-do-patterns 5; migration-guide; validation-and-cors; evaluation-scenarios | U13 |
| (unverified): removal date of the `camel-quarkus-junit5` stub | never-do-patterns; migration-guide | U14 |
| (unverified): Jackson 3 (Quarkus 4) impact on JSON binding | SKILL.md Version Context; migration-guide; unverified-and-risks (Version-lifetime risk) | U16 |
| (medium confidence): REST DSL manual claims (binding, error codes, inlineRoutes, validation, startup failure, CORS defaults) | SKILL.md Quick Reference and Ask First; always-do-patterns 2, 3, 4; rest-dsl-configuration; openapi-contract-first; validation-and-cors | M1 |
| (medium confidence): example pom on `main` (dependencies, test dependencies, Quarkus version) | SKILL.md Ask First; always-do-patterns 1; integration-examples; migration-guide; rest-dsl-configuration; evaluation-scenarios | M2 |
| (medium confidence): `type`/`outType` on verbs | SKILL.md Ask First; always-do-patterns 2; evaluation-scenarios | M3 |
| (medium confidence): one `direct:<operationId>` route per operation | SKILL.md Ask First; always-do-patterns 4; openapi-contract-first | M4 |
| (medium confidence): CORS comparison and Quarkus CORS / root-path defaults | SKILL.md Ask First and Quick Reference; never-do-patterns; validation-and-cors; integration-examples; rest-dsl-configuration; evaluation-scenarios | M5 |
| (medium confidence, absence of evidence): no Camel Quarkus build on Quarkus 4 | SKILL.md Version Context; migration-guide; evaluation-scenarios | M6 |
| (medium confidence): AtlasMap removal | SKILL.md Ask First; never-do-patterns; migration-guide; evaluation-scenarios | M7 |
| (medium confidence): `.param()` syntax | rest-dsl-configuration | M8 |
| (medium confidence): native registration | SKILL.md Ask First; openapi-contract-first | M9 |
| (medium confidence): default base path `/` | SKILL.md Ask First; openapi-contract-first; never-do-patterns | M10 |
| (medium confidence): code-first spec publishing (`apiContextPath` example, merge into `/q/openapi`; not the `expose.enabled` default) | SKILL.md Ask First; openapi-contract-first | M11 |
| (medium confidence): testing details and Quarkus authorization reference | SKILL.md Ask First and Quick Reference; integration-examples; validation-and-cors | M12 |
| (medium confidence): Camel 4.22 upgrade-guide items | migration-guide; validation-and-cors | M13 |
| (medium confidence): authenticated-user header | rest-dsl-configuration | M14 |
| (medium confidence): CDI injection in `configure()` and REST in `LambdaRouteBuilder` | never-do-patterns | M9 |

Untagged claims are High: versioned official page fetched 2026-10-14, or an orchestrator-verified family fact (release date and LTS, versions, Quarkus 3.40 LTS end date, Quarkus 4.0.0.Beta1, junit rename). Always Do and Never Do in SKILL.md accept only High; any tag there is a defect.

## Source Bibliography

All fetched 2026-10-14. camel.apache.org manual and component pages carry no page date and are accepted as current docs; `/manual/` pages are unversioned. No community sources were used. The Quarkus blog post cited by the earlier research (AtlasMap-based, pre-Camel-4) was rejected.

- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/openapi-java.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest-openapi.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jackson.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/index.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html
- https://camel.apache.org/camel-quarkus/next/migration-guide/3.39.0.html
- https://camel.apache.org/releases/
- https://camel.apache.org/releases/q-3.40.0/ (Java 17 and 21; neither release date nor Camel version)
- https://camel.apache.org/releases/release-4.0.0/
- https://camel.apache.org/manual/rest-dsl.html
- https://camel.apache.org/manual/rest-dsl-binding.html
- https://camel.apache.org/manual/rest-dsl-validation.html
- https://camel.apache.org/manual/rest-dsl-openapi.html
- https://camel.apache.org/manual/latest/rest-dsl.html (search snippet only, `.param()` syntax)
- https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html
- https://camel.apache.org/manual/camel-4-migration-guide.html (search summary)
- https://camel.apache.org/components/4.22.x/platform-http-component.html
- https://camel.apache.org/components/4.22.x/rest-openapi-component.html
- https://camel.apache.org/components/4.22.x/others/main.html
- https://quarkus.io/version/3.40/guides/http-reference (research fetched the unpinned `/guides/` URL; pinned URL not re-fetched, so claims stay medium)
- https://quarkus.io/version/3.40/guides/security-cors (same note)
- https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference (same note)
- https://quarkus.io/version/3.40/guides/getting-started-testing (same note)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/3.40.0/camel-quarkus-junit5-3.40.0.pom (orchestrator-fetched 2026-10-14)
- https://camel.apache.org/camel-quarkus/latest/
- https://quarkus.io/releases
- https://quarkus.io/blog/quarkus-4-0-0-beta1-released/
- https://github.com/apache/camel-quarkus-examples (`rest-json` pom and Routes.java, `openapi-contract-first` pom and application.properties)
