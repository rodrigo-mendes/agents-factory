# Unverified Register, Risks and Bibliography

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Research quality score reported by the research file: about 84% (9 unverified, 3 irresolvable). This register lists **13 unverified items (U1-U13)**, **2 irresolvable items (I1-I2)**, **8 medium-confidence items (M1-M8)** and **0 coverage limits (L)**. It has more entries than the research's 9 + 3 because this skill added gaps the research omitted (for example `quarkus.http.root-path`), the family-facts file adds the Camel Quarkus support end date, and the inbound-bridging question moved to U13 (its text tag is `(unverified)`); the extra entries are not individually traced to the research file.

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items-do-not-assert)
- [Medium-confidence items](#medium-confidence-items)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

Shared facts carry the family-facts confidence (verified by the orchestrator 2026-10-14).

- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is planned for the end of November; Java 21 is the new base (High, https://quarkus.io/blog/quarkus-4-0-0-beta1-released/). No Camel Quarkus build on Quarkus 4 is known and the Beta1 post does not mention Camel Quarkus (medium confidence, absence of evidence); do not mix Quarkus 4 artifacts.
- Quarkus 3.40 was released 2026-09-30 as an LTS, community-maintained until 2027-09-30 (High, https://quarkus.io/releases). The Camel Quarkus-specific end date is not published (unverified); applying the Quarkus date to Camel Quarkus is an inference.
- Camel Quarkus 3.40.0 was released 2026-09-28 and is marked LTS (High, https://camel.apache.org/releases/; no LTS-until date given), about two weeks before the research date, so docs may still change. It uses Camel 4.22.1, Quarkus 3.40.1, GraalVM 25.0.4.1 (High, https://camel.apache.org/camel-quarkus/latest/). Java: 17 and 21 (High, https://camel.apache.org/releases/q-3.40.0/); Java 25 for Camel Quarkus is unverified.
- Plan a Camel Quarkus migration with no known date; re-run research when a Quarkus 4 compatible build appears.

## Unverified items

- U1: Effect of `quarkus.http.root-path` on Camel `platform-http` routes (gap added by this skill; the research did not cover it). Test real URLs when a root path is set.
- U2: The comma-separated multi-value form of `httpMethodRestrict` (for example `GET,POST`).
- U3: The `quarkus.http.auth.permission.*` property names (security guide not fetched).
- U4: The Vert.x `Router` observer code for a custom 404.
- U5: HTTP status code returned for a wrong method (405 assumed) and for a rejected upload extension.
- U6: The native profile name (`-Pnative`).
- U7: The integration-tests path in the repo (https://github.com/apache/camel-quarkus/tree/main/integration-tests/platform-http, not fetched).
- U8: Interaction of `useStreaming` with `max-body-size` and `useBodyHandler`.
- U9: Platform-http-specific concurrency options beyond `requestTimeout`.
- U10: Maven requirement for this extension (not researched). Java is High (17 and 21) and GraalVM is covered by the docs index.
- U11: What happens at runtime when `SSLContextParameters` is set on platform-http (the page only says unsupported).
- U12: The Camel Quarkus-specific support end date for 3.40 (the "LTS Until" column is blank on https://camel.apache.org/camel-quarkus/latest/); not resolvable from documentation.
- U13: Whether the 3.40 TLS-registry bridging touches the inbound Vert.x HTTP server (possible TLSv1.2 client breakage on HTTPS endpoints); not resolvable from documentation. Workaround: test with `openssl s_client -tls1_2` after upgrade; review the apache/camel-quarkus 3.40.0 release notes or PR.

## Irresolvable items (do not assert)

| Id | Item | Impact | Workaround |
|---|---|---|---|
| I1 | Defaults of `quarkus.http.body.handle-file-uploads`, `uploads-directory`, `delete-uploaded-files-on-end`, `merge-form-attributes` (all-config HTTP section did not render) | Upload behaviour and temp-file cleanup assumed | Set all explicitly ([file uploads](./file-uploads.md#quarkus-body-properties)) |
| I2 | `quarkus.http.port` (8080) and `test-port` (8081) defaults for 3.40 | Low; curl examples only | Set ports explicitly |

## Medium-confidence items

- M1: No Camel Quarkus build on Quarkus 4 is known (absence of evidence; the Beta1 post does not mention Camel Quarkus).
- M2: BOM listing date for `quarkus-camel-bom` 3.40.1 (Maven listing from an earlier run, not re-fetched); the version 3.40.1 itself is High via the docs index.
- M3: Test SSL port 8444 and the `https` named configuration example (the "Latest" Quarkus page, not pinned to 3.40).
- M4: REST DSL vs Quarkus REST choice (a Quarkus REST resource calling a `ProducerTemplate` appears in https://github.com/apache/camel-quarkus-examples, `quarkus-rest-json`, `OrderResource.java`, main branch, not in 3.40.x-tagged docs; that example uses neither platform-http nor `camel-quarkus-rest`, so no official source shows both on one server).
- M5: A streamed body (`useStreaming=true`) is single-read.
- M6: Reverse proxy notes for `platform-http:proxy` (Quarkus-only, `toD` with `Exchange.HTTP_HOST`, headers from the request line).
- M7: `muteException=false` leaking exception details (inferred from the option description).
- M8: The Camel Quarkus migration guide index (https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/index.html) was not re-fetched.

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) Maven requirement | SKILL.md Version Context | U10 |
| (unverified) LTS end date | SKILL.md Version-lifetime risk, this register | U12 |
| (unverified) inbound-server impact of the 3.40 bridging | SKILL.md Ask First and Quick Reference, tls-and-security.md, migration-guide.md | U13 |
| (unverified) `httpMethodRestrict` comma form | SKILL.md Ask First and Quick Reference | U2 |
| (unverified) `quarkus.http.body.*` defaults | SKILL.md Ask First and Quick Reference, file-uploads.md | I1 |
| (unverified) ports 8080 and 8081, including `8080 default (unverified)` in code samples | SKILL.md Quick Reference, file-uploads.md, integration-examples.md | I2 |
| (unverified) `useStreaming` interaction | SKILL.md Ask First, file-uploads.md | U8 |
| (unverified) `quarkus.http.auth.permission.*` names | SKILL.md Ask First, tls-and-security.md | U3 |
| (unverified) `quarkus.http.root-path` effect | SKILL.md Ask First, tls-and-security.md, migration-guide.md | U1 |
| (unverified) Vert.x `Router` observer code | integration-examples.md | U4 |
| `405 is (unverified)`, `exact status code (unverified)` | integration-examples.md, file-uploads.md | U5 |
| `profile name (unverified)` | integration-examples.md | U6 |
| `quarkus.http.test-port` default (8081) `(unverified)` | integration-examples.md | I2 |
| likely outcome (unverified) of `SSLContextParameters` at runtime | never-do-patterns.md | U11 |
| (medium confidence, absence of evidence) no Camel Quarkus build on Quarkus 4 | SKILL.md, migration-guide.md, evaluation-scenarios.md, this register | M1 |
| (medium confidence) BOM listing | SKILL.md Version Context | M2 |
| (medium confidence) test SSL port 8444, `https` named configuration | SKILL.md Quick Reference, tls-and-security.md | M3 |
| (medium confidence) REST DSL vs Quarkus REST | SKILL.md Ask First, integration-examples.md | M4 |
| (medium confidence) single-read streamed body | SKILL.md Ask First, integration-examples.md | M5 |
| (medium confidence) reverse proxy | SKILL.md Ask First, integration-examples.md | M6 |
| (medium confidence) `muteException=false` leaks details | SKILL.md Ask First, integration-examples.md | M7 |
| (medium confidence) migration guide index not re-fetched | migration-guide.md | M8 |
| High (shared version facts, Java 17 and 21) | [Version-lifetime risk](#version-lifetime-risk) and the family-facts sources in the [bibliography](#source-bibliography) | n/a |

## Source Bibliography

All fetched 2026-10-14 unless marked. camel.apache.org and quarkus.io versioned pages show no page date and count as current because they are the versioned docs for the current stable LTS. No community sources were used.

- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html
- https://camel.apache.org/components/4.22.x/platform-http-component.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
- https://quarkus.io/version/3.40/guides/http-reference
- https://quarkus.io/version/3.40/guides/management-interface-reference
- https://quarkus.io/guides/http-reference ("Latest" page, medium)
- https://quarkus.io/version/3.40/guides/all-config (fetched; the HTTP section did not render)
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html (cited for the `@ApplicationScoped` rule; verified by the orchestrator 2026-10-14)
- Verified by the orchestrator 2026-10-14 (family facts, High): https://camel.apache.org/releases/ ; https://camel.apache.org/releases/q-3.40.0/ ; https://camel.apache.org/camel-quarkus/latest/ ; https://quarkus.io/releases ; https://quarkus.io/blog/quarkus-4-0-0-beta1-released/
- Reused, not re-fetched (medium): https://repo1.maven.org/maven2/io/quarkus/platform/quarkus-camel-bom/ ; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/index.html
