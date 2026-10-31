# Unverified Register, Risks and Bibliography

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 88% (9 unverified, 3 irresolvable) over about 100 claims. This register is the reconciled list after the fix passes. Counts: 10 unverified (U1-U10), 3 irresolvable (I1-I3), 14 medium-confidence (M1-M14), 1 coverage limit (L1). The okStatusCodeRange contradiction is recorded inside M2.

## Version-lifetime risk

- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; the highlights list Java 21 as the new base version (High; https://quarkus.io/blog/quarkus-4-0-0-beta1-released/).
- No Camel Quarkus build on Quarkus 4 is known; the Beta1 post does not mention Camel Quarkus (medium confidence, absence of evidence; same source). Do not mix Quarkus 4 artifacts with camel-quarkus-http 3.40.x.
- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30 (High; https://quarkus.io/releases). The Camel Quarkus-specific support end date for 3.40 is (unverified) ("LTS Until" column blank on https://camel.apache.org/camel-quarkus/latest/); applying the Quarkus date to Camel Quarkus is an inference (U8).
- Camel Quarkus 3.40.0 was released 2026-09-28 and is marked LTS (High; https://camel.apache.org/releases/, no LTS-until date given); 3.40.x uses Camel 4.22.1, Quarkus 3.40.1, GraalVM 25.0.4.1 (High; https://camel.apache.org/camel-quarkus/latest/). The release is recent, so the docs may still change.
- Java 17 and 21 (High; https://camel.apache.org/releases/q-3.40.0/; the page names no Camel or Quarkus version and shows no release date). Java 25 for Camel Quarkus: (unverified).
- `camel-quarkus-tls-registry` is Experimental: its option names and defaults may change between minors.

## Unverified items (U1-U10)

| Id | Item | Note |
|---|---|---|
| U1 | Plain `camel-http` lacking native support / automatic native SSL | Inference: the extension page states what the extension adds, not what plain `camel-http` lacks |
| U2 | `transferException` in native mode | Native behaviour of the serialization path unknown |
| U3 | Java package of `HttpOperationFailedException` | Research guessed `org.apache.camel.http.base`; resolve with the IDE |
| U4 | `interceptSendToEndpoint` in the Camel Quarkus testing guide | Not covered by the guide |
| U5 | Dead Letter Channel default of 6 redeliveries / 1 s | Only a tool summary saw it; unversioned manual page |
| U6 | Build-time vs runtime for `quarkus.camel.tls-registry.*` | Not stated on the fetched page |
| U7 | `oauth2CachedTokensKey` in 4.22 | Only on the `next` page ("before Camel 4.23"); absent from the 4.22.x extraction |
| U8 | Camel Quarkus-specific LTS end date for 3.40 | Not resolvable from documentation; see Version-lifetime risk |
| U9 | Log output of the representative commands | Commands are representative |
| U10 | Whether the 3.40 TLS bridging (and a global `quarkus.tls.protocols` change) affects the inbound platform-http server | Not resolvable from documentation; no page states it |

The package, `doBeforeEach` and `adviceRoute` signatures of `CamelQuarkusTestSupport` are not a gap here: they are resolved in the skill `developing-camel-quarkus-junit-v3-40`.

## Irresolvable items (do not assert) (I1-I3)

| Id | Item | Impact | Workaround |
|---|---|---|---|
| I1 | Apache HttpClient 5 version Quarkus resolves under `quarkus-camel-bom` 3.40.x (parent POM pins 5.6.3 / httpcore 5.4.3) | CVE triage; the 4.18 gzip fix depends on 5.6+ | `./mvnw dependency:tree \| grep httpclient5` |
| I2 | Whether plain `camel-resilience4j` works on Camel Quarkus 3.40 (JVM/native) | Teams porting `resilience4jConfiguration` routes | Use `camel-quarkus-microprofile-fault-tolerance` |
| I3 | `faultToleranceConfiguration` option defaults and whether fallback runs on timeout | Breaker thresholds and timeout semantics | Set every option explicitly; test the timeout path |

## Medium-confidence items (M1-M14)

- M1: No Camel Quarkus build on Quarkus 4 is known (absence of evidence; the Beta1 post does not mention Camel Quarkus).
- M2: `throwExceptionOnFailure` / `followRedirects` / `okStatusCodeRange` defaults, the status-code strategy and when `HttpOperationFailedException` is thrown. Contradiction recorded: prose on the http component page says "100..299" is success; the option default is `200-299`. Recommendation: set the range explicitly. Source: https://camel.apache.org/components/4.22.x/http-component.html
- M3: 429 auto-retry by HttpClient 5 (`Retry-After`) and `automaticRetriesDisabled`.
- M4: Auth and OAuth2 options (and the swapped option descriptions in the option tables).
- M5: Proxy-route header leakage (`CamelHttp*`, `bridgeEndpoint`, `skipControlHeaders`).
- M6: Java serialization: `allowJavaSerializedObject` / `transferException` with untrusted peers.
- M7: REST client vs camel-http choice (no official comparison).
- M8: Multiple TLS identities: per-endpoint `sslContextParameters` vs separate component instances.
- M9: `hostnameVerificationPolicy` (default `CLIENT`) and `x509HostnameVerifier` as endpoint-level verification.
- M10: The `camel.component.https.*` property binding (page not recorded).
- M11: Production notes in integration-examples.md (`responsePayloadStreamingThreshold`, `disableStreamCache`, `connectionsPerRoute` sizing).
- M12: Trust-all guidance (REST client guide plus http component page).
- M13: Camel 4.18 and 4.21 upgrade-guide entries (gzip double decompression, `ObjectInputFilter`).
- M14: Other security notes in tls-and-security.md (`useSystemProperties` default, certificate-reload monitoring).

The timeout and pool defaults, `allowJavaSerializedObject=false`, `maxTotalConnections` and `connectionsPerRoute` are read from the versioned 4.22.x http component page and are High. The TLSv1.3 default is High (3.40.0 migration guide).

## Coverage limits (L1)

- L1: The Camel 4.18 and 4.21 upgrade guides were read only partly (page partially read); the entries in M13 may be incomplete.

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence, absence of evidence) | SKILL.md Version-lifetime risk; this register; evaluation-scenarios.md scenario 3 | M1 |
| (unverified), Camel Quarkus-specific support end date | SKILL.md Version-lifetime risk; this register | U8 |
| (unverified), HttpClient 5 version Quarkus resolves | SKILL.md Version Context; migration-guide.md | I1 |
| (medium confidence), status handling, throw semantics, `throwExceptionOnFailure`, `okStatusCodeRange` | SKILL.md Ask First and Quick Reference; fault-tolerance-and-errors.md; always-do-patterns.md section 4 | M2 |
| (unverified), `HttpOperationFailedException` Java package | SKILL.md Ask First; always-do-patterns.md section 4; fault-tolerance-and-errors.md; integration-examples.md | U3 |
| (medium confidence), 429 handling | SKILL.md Ask First; fault-tolerance-and-errors.md | M3 |
| (medium confidence), credentials and auth | SKILL.md Ask First; tls-and-security.md | M4 |
| (medium confidence), proxy routes | SKILL.md Ask First; never-do-patterns.md | M5 |
| (medium confidence), Java serialization | SKILL.md Ask First; never-do-patterns.md | M6 |
| (unverified), `transferException` native behaviour | SKILL.md Ask First; never-do-patterns.md | U2 |
| (medium confidence), Camel `http` vs Quarkus REST client | SKILL.md Ask First; integration-examples.md | M7 |
| (medium confidence), multiple TLS identities | SKILL.md Ask First | M8 |
| (medium confidence), endpoint TLS verification options | SKILL.md Ask First; never-do-patterns.md section 2; tls-and-security.md | M9 |
| (medium confidence), `camel.component.https.*` binding | always-do-patterns.md section 6; integration-examples.md | M10 |
| (medium confidence), production notes | integration-examples.md | M11 |
| (medium confidence), trust-all | never-do-patterns.md | M12 |
| (medium confidence; page partially read, L1), upgrade-guide entries | migration-guide.md | M13 |
| (medium confidence), other security notes | tls-and-security.md | M14 |
| (unverified), plain `camel-http` difference (inferred) | SKILL.md Ask First; never-do-patterns.md | U1 |
| (unverified), `faultToleranceConfiguration` defaults and timeout fallback | SKILL.md Ask First; always-do-patterns.md section 5; fault-tolerance-and-errors.md; integration-examples.md | I3 |
| (unverified), plain `camel-resilience4j` | never-do-patterns.md section 3; fault-tolerance-and-errors.md | I2 |
| (unverified), Dead Letter Channel default | fault-tolerance-and-errors.md | U5 |
| (unverified), `quarkus.camel.tls-registry.*` build-time vs runtime | tls-and-security.md; integration-examples.md | U6 |
| (unverified), `oauth2CachedTokensKey` in 4.22 | never-do-patterns.md | U7 |
| (unverified), `interceptSendToEndpoint` | integration-examples.md | U4 |
| (unverified), inbound platform-http impact of global TLS widening | SKILL.md Ask First; tls-and-security.md | U10 |
| (log output unverified) | SKILL.md Quick Reference; migration-guide.md | U9 |

## Source Bibliography

All fetched 2026-10-14. camel.apache.org pages carry no page date and are the current stable docs. No community sources were used. WebFetch returns model-summarised text; check exact wording before quoting verbatim.

- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/http.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/microprofile-fault-tolerance.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html (also index, 3.39.0, 3.38.0, 3.36.0, 3.35.0, 3.33.0)
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html (testing rename, see `developing-camel-quarkus-junit-v3-40`)
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html
- https://camel.apache.org/camel-quarkus/latest/
- https://camel.apache.org/releases/ ; https://camel.apache.org/releases/q-3.40.0/
- https://github.com/apache/camel-quarkus/releases
- https://camel.apache.org/components/4.22.x/http-component.html
- https://camel.apache.org/components/next/http-component.html (4.23+, cross-check only)
- https://camel.apache.org/components/4.22.x/eips/circuitBreaker-eip.html ; .../fault-tolerance-eip.html ; .../resilience4j-eip.html
- https://camel.apache.org/manual/error-handler.html (unversioned)
- https://camel.apache.org/manual/camel-4x-upgrade-guide-4_18.html (also 4_19, 4_20, 4_21, 4_22)
- https://github.com/apache/camel/blob/camel-4.22.x/parent/pom.xml
- https://quarkus.io/guides/tls-registry-reference (unpinned; consulted, not cited for any claim)
- https://quarkus.io/guides/rest-client
- https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ (2026-10-01)
- https://quarkus.io/releases (LTS policy)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-http/ and .../camel-quarkus-tls-registry/ (3.40.0, 2026-09-24)
