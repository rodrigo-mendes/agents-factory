# Unverified Register, Risks and Bibliography

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 89%, a deep run using all 3 iterations, and 4 triangulated claims. Family facts verified by the orchestrator on 2026-10-14 keep the tags of the family facts file.

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Coverage limits](#coverage-limits)
- [Medium-confidence items](#medium-confidence-items)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; Java 21 is the new base (High; https://quarkus.io/blog/quarkus-4-0-0-beta1-released/). Plan a migration; the 3.40 patterns here are not valid on Quarkus 4 unchanged.
- The Quarkus 4 preview details (Jackson 3 packages `tools.jackson.*`, `ObjectMapperCustomizer` renamed `JsonMapperBuilderCustomizer`, endpoints may not return REST client `Response`/`RestResponse`, RESTEasy 7) come from the Quarkus 4 migration wiki: medium confidence and NOT for 3.40 ([preview](./migration-quarkus-4-preview.md#quarkus-4-preview-not-for-340)).
- The Quarkus 4 preview blueprint is migration context only and never applies to 3.40 work (family rule 1: Quarkus 3.40 only; a request for another line is an Ask First).
- No Camel Quarkus build on Quarkus 4 is known; the Beta1 post does not mention Camel Quarkus (medium confidence, absence of evidence).
- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30 (High; https://quarkus.io/releases). As of 2026-10-14 the 3.40 documentation is new and may still change; patch releases are expected.
- The Camel Quarkus-specific support end date for 3.40 is not published (unverified; U6). Applying the Quarkus date to Camel Quarkus is an inference.

## Unverified items

8 unverified items (do not assert them).

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | Per-client `connect-timeout` and `read-timeout` inherit the global defaults (the config reference lists no per-client default) | Unclear effective timeout; set both per client explicitly |
| U2 | Whether `quarkus.rest.path` affects Camel platform-http routes (also in the Camel REST register: U5 in `developing-camel-quarkus-rest-v3-40`) | Do not rely on it to separate stacks; use disjoint path prefixes |
| U3 | Jackson 2.x in Quarkus 3.40 and its exact version (no page recorded) | Read the version from the resolved BOM in your build |
| U4 | Whether Quarkus REST security annotation checks run before request-body deserialization | Do not assume the body is unparsed for unauthorized callers; add HTTP-level permissions |
| U5 | Whether legacy `quarkus-resteasy-reactive*` artifact names still exist as aliases in 3.40 | Use `quarkus-rest*` names |
| U6 | Camel Quarkus-specific support end date for 3.40 (the "LTS Until" column is blank on https://camel.apache.org/camel-quarkus/latest/); not resolvable from documentation (also in the Camel REST register: U9) | Do not infer it from the Quarkus date |
| U7 | Whether the Camel Quarkus 3.40.0 `quarkus.tls` bridging affects the inbound platform-http server; not resolvable from documentation (also in the Camel REST register: U13) | Configure server TLS explicitly with `quarkus.http.tls-configuration-name`. Follow-up: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html |
| U8 | Minimum Java version for Quarkus 3.40 (not on the fetched pages; Camel Quarkus 3.40 supports Java 17 and 21, High; same item as U3 of `developing-quarkus-arc-v3-40`) | Build toolchain choice; check the 3.40 getting-started prerequisites |

## Irresolvable items

1 irresolvable item (no 3.40 page states it; do not assert).

| ID | Item | Impact | Workaround |
|---|---|---|---|
| I1 | Behaviour when a Quarkus REST resource and a Camel platform-http route share a path on the same HTTP server (also in the Camel REST register, merged into U5) | Ambiguous routing or shadowed endpoints | Disjoint path prefixes (research workaround). Follow-up: camel-quarkus issues, platform-http extension source |

## Coverage limits

4 coverage limits (L1, L2, L3, L5; parts of pages not read; claims there may be missing). L4 (the Camel `rest-json` example) moved with the Camel integration blueprint to `developing-camel-quarkus-rest-v3-40` (ID L2 there); the ID L4 is not reused.

| ID | Limit |
|---|---|
| L1 | https://quarkus.io/version/3.40/guides/tls-registry-reference was read only to the first 100k characters |
| L2 | https://quarkus.io/version/3.40/guides/getting-started-testing was read only to the first 100k characters |
| L3 | The header section of https://quarkus.io/version/3.40/guides/rest-client was read only partly |
| L5 | https://quarkus.io/version/3.40/guides/rest was read in two parts but the research records it as read only partly, and the unread part is not identified. Claims from this guide stay High only where a verbatim quote is recorded: `quarkus-resteasy-client` "may not be used with Quarkus REST", the IO-thread and signature-dependent threading quotes, pre-matching filters "are always run on an event-loop thread", `@ServerExceptionMapper` "do not run CDI interceptors...", and "not compressed by default". Other claims taken only from this guide are M1 and M11 |

## Medium-confidence items

12 medium-confidence items.

| ID | Item | Why medium |
|---|---|---|
| M1 | Exception mapping and logging (research M4) | The rest guide is recorded as read only partly (L5) |
| M2 | CORS defaults and wildcard warning (research M6, F4) | Versioned 3.40 page; verbatim quotes recorded but the page is not recorded as fully read (L5) |
| M3 | `deny-unannotated-endpoints` default and proactive authentication (research M7) | Versioned 3.40 pages; verbatim quotes recorded but the pages are not recorded as fully read (L5) |
| M4 | `@PermitAll` cannot override HTTP permissions (research F5) | Versioned 3.40 page; verbatim quote recorded but the page is not recorded as fully read (L5) |
| M5 | OpenAPI and Swagger UI exposure (research C5) | Page does not state Quarkus REST compatibility outright |
| M6 | `ProducerTemplate` in a Jakarta REST resource; resource versus REST DSL (research C2); also in the Camel REST register (M15) | Examples main branch, not 3.40.x-tagged docs |
| M7 | Quarkus 4 preview details and removal of deprecated client settings | Unversioned migration wiki |
| M8 | No Camel Quarkus build on Quarkus 4 (also in the Camel REST register: M6) | Absence of evidence |
| M9 | Virtual-thread pinning risk on Java 21-23 | Stated in the research's architecture notes citing the virtual-threads guide; the Java 21-23 range was not confirmed in a quoted passage |
| M10 | `@TestHTTPEndpoint` in a REST test (rest-client.md sample) | Rated medium confidence in `developing-quarkus-junit-v3-40` (the 3.31 wiki does not name it as the replacement for system-property port lookup); the testing guide was read only partly (L2), the same tag as in the refactoring, ArC and Camel bean skills |
| M11 | Rest-guide claims without a recorded verbatim quote: `quarkus-rest` as successor of RESTEasy Reactive, the artifact names the guide lists, the `@Blocking`/`@NonBlocking` levels and `@Transactional` counting as blocking, the `quarkus.rest.*` config defaults table, response-filter behaviours (streamed `Multi`, client disconnect), CDI and context-object injection | The rest guide is recorded as read only partly (L5) |
| M12 | Absence of `quarkus-junit5` in the 3.40 testing guide, which was read only to the first 100k characters (L2) | Absence of evidence; the guide names `quarkus-junit` |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) Jackson 2.x and its exact version | SKILL.md Version Context; migration-quarkus-4-preview | U3 |
| (unverified) Camel Quarkus end date | SKILL.md Version-lifetime risk | U6 |
| (unverified) per-client timeouts inherit | SKILL.md Ask First; rest-client; evaluation scenario 2 | U1 |
| (unverified) `quarkus.rest.path` and platform-http | server-resources; evaluation scenario 2 | U2 |
| (unverified) annotation checks versus body | security-and-tls | U4 |
| (unverified) legacy `quarkus-resteasy-reactive*` aliases | migration-quarkus-4-preview | U5 |
| (unverified) TLS bridging on the inbound server | security-and-tls | U7 |
| (unverified, U8) minimum Java for Quarkus 3.40 | SKILL.md Version Context | U8 |
| irresolvable shared path (also in the Camel REST register, U5) | evaluation-scenarios.md (scenario 2) | I1 |
| partial reads of pages | SKILL.md Quick Reference; always-do-patterns; security-and-tls; rest-client; server-resources | L1, L2, L3, L5 |
| (medium confidence) exception mapping | SKILL.md Ask First; server-resources | M1 |
| (medium confidence) CORS | SKILL.md Ask First and Quick Reference; security-and-tls; evaluation scenario 5 | M2 |
| (medium confidence) deny-by-default, proactive auth | SKILL.md Ask First and Quick Reference; security-and-tls | M3 |
| (medium confidence) `@PermitAll` | security-and-tls; evaluation scenario 5 | M4 |
| (medium confidence) Swagger UI, OpenAPI | SKILL.md Ask First and Quick Reference; server-resources | M5 |
| (medium confidence) resource + ProducerTemplate (also in the Camel REST register, M15) | SKILL.md Ask First | M6 |
| (medium confidence) Quarkus 4 preview | SKILL.md Version-lifetime risk; rest-client; server-resources; migration-quarkus-4-preview; evaluation scenario 3 | M7 |
| (medium confidence, absence of evidence) Quarkus 4 and Camel | SKILL.md Version-lifetime risk; migration-quarkus-4-preview | M8 |
| (medium confidence) pinning risk on Java 21-23 | SKILL.md Ask First; always-do-patterns | M9 |
| (medium confidence) `@TestHTTPEndpoint` | rest-client.md Mocking and testing | M10 |
| (medium confidence, absence of evidence, M12) `quarkus-junit5` absent from the partly read testing guide | migration-quarkus-4-preview | M12 |
| (medium confidence, L3) `verify-host` key path | SKILL.md Ask First (client hostname verification); never-do 3 note; rest-client | L3 |
| (medium confidence, L1) TLS default TLSv1.3 | SKILL.md Quick Reference; rest-client; security-and-tls | L1 |
| (medium confidence, L2) test port 8081 | SKILL.md Quick Reference; server-resources | L2 |
| (medium confidence, L5) rest-guide claims without a verbatim quote | SKILL.md Version Context and Quick Reference; always-do-patterns (artifact names, threading); migration-quarkus-4-preview; server-resources (configuration defaults, filters, CDI and context objects) | M11 |

## Source Bibliography

All fetched 2026-10-14. camel.apache.org pages carry no page date and are the current stable 3.40.x docs. No older research files were used.

Primary:
- https://quarkus.io/version/3.40/guides/rest (read in two parts, recorded as read only partly: L5)
- https://quarkus.io/version/3.40/guides/rest-client (header section partly read)
- https://quarkus.io/version/3.40/guides/rest-json
- https://quarkus.io/version/3.40/guides/virtual-threads
- https://quarkus.io/version/3.40/guides/security-cors
- https://quarkus.io/version/3.40/guides/openapi-swaggerui
- https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference
- https://quarkus.io/version/3.40/guides/security-proactive-authentication
- https://quarkus.io/version/3.40/guides/validation
- https://quarkus.io/version/3.40/guides/tls-registry-reference (first 100k chars)
- https://quarkus.io/version/3.40/guides/getting-started-testing (first 100k chars)
- https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ (2026-10-01)
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html

Family facts (orchestrator-verified):
- https://quarkus.io/releases
- https://camel.apache.org/releases/
- https://camel.apache.org/camel-quarkus/latest/
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html

Medium confidence (unversioned or main branch):
- https://github.com/quarkusio/quarkus/wiki/Migration-Guide-4.0
- https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/quarkus-rest-json/pom.xml
- https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/quarkus-rest-json/src/main/java/org/acme/rest/json/quarkus/OrderResource.java
- https://github.com/apache/camel-quarkus-examples
