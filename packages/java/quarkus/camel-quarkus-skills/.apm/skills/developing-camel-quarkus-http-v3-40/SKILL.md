---
name: developing-camel-quarkus-http-v3-40
description: "Guides camel-quarkus-http 3.40.x (Camel 4.22, Quarkus 3.40 LTS), the HTTP client/producer: timeouts, TLS registry bridge, auth, errors, fault tolerance. Use when routes call http:/https: endpoints. Not for platform-http (server), Quarkus 4 or the Quarkus REST client."
---

# Developing with Camel Quarkus HTTP 3.40.x (client / producer)

> Version lock: every claim applies to **camel-quarkus-http 3.40.x** only. Research date **2026-10-14**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against a versioned official page; treat them as hypotheses. Tag ids are in the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Core topics (BOM import, route discovery, native reflection, test artifacts) belong to the sibling skill `developing-camel-quarkus-core-v3-40`.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| camel-quarkus-http | 3.40.0 on Maven Central, 2026-09-24; JVM and native since 1.0.0 | https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-http/ ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/http.html |
| Camel Quarkus | 3.40.x (3.40.0 released 2026-09-28, LTS) | https://camel.apache.org/releases/ |
| Camel / Quarkus / GraalVM | 4.22.1 / 3.40.1 / 25.0.4.1 | https://camel.apache.org/camel-quarkus/latest/ |
| Java | 17 and 21 | https://camel.apache.org/releases/q-3.40.0/ |
| Apache HttpClient 5 | 5.6.3 pinned in the Camel 4.22.x parent POM; the version Quarkus resolves is (unverified) | https://github.com/apache/camel/blob/camel-4.22.x/parent/pom.xml |
| camel-quarkus-tls-registry | Experimental, since 3.36.0 | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html |
| Extension page | Lists no limitations and no `quarkus.camel.*` properties | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/http.html |

**Version-lifetime risk** (as of 2026-10-14; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; Java 21 is the new base ([source](https://quarkus.io/blog/quarkus-4-0-0-beta1-released/)).
- No Camel Quarkus build on Quarkus 4 is known; the Beta1 post does not mention Camel Quarkus (medium confidence, absence of evidence; same source).
- Quarkus 3.40 (released 2026-09-30, LTS) is community-maintained until 2027-09-30 ([source](https://quarkus.io/releases)). The Camel Quarkus-specific support end date is (unverified).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [TLS and security](./blueprints/tls-and-security.md)
- [Fault tolerance and error handling](./blueprints/fault-tolerance-and-errors.md)
- [Migration guide to 3.40](./blueprints/migration-guide.md)
- [Integration examples and testing](./blueprints/integration-examples.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Depend on `camel-quarkus-http` for `http:`/`https:` producer endpoints** ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/http.html)). See [patterns](./blueprints/always-do-patterns.md#1-dependency-and-native-ssl).
- **Rely on the extension to enable SSL in native mode automatically** ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/http.html)).
- **Reference the TLS registry bean explicitly on `https:` endpoints** (`sslContextParameters=#defaultSslContextParameters` or `#<name>`) ([tls-registry page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html)). See [TLS](./blueprints/tls-and-security.md#bridging-quarkustls-to-camel).
- **Configure bridged endpoints for TLSv1.3 only, the default.** Since 3.40.0 the default of the bridged beans is TLSv1.3 only ([3.40.0 migration guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)). See [TLS](./blueprints/tls-and-security.md#3400-behaviour-change).
- **Use `camel-quarkus-microprofile-fault-tolerance` for `circuitBreaker()`** ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/microprofile-fault-tolerance.html), Stable). See [fault tolerance](./blueprints/fault-tolerance-and-errors.md#circuit-breaker-with-fallback).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Timeouts and pools ([http component, 4.22.x](https://camel.apache.org/components/4.22.x/http-component.html)) | Defaults are 180000 ms for connect, connection-request and socket; `responseTimeout` has none (0 = infinite). Recommended: set all explicitly. | "What latency budget does the downstream have?" |
| Endpoint TLS verification (medium confidence) | `hostnameVerificationPolicy` (default `CLIENT`) or `x509HostnameVerifier` on the component or endpoint, and revocation handled outside the bridge, because `quarkus.tls` hostname and CRL settings are not bridged. | "Must this partner's hostname and revocation be checked, and where?" |
| `HttpOperationFailedException` throw semantics (medium confidence); Java package (unverified) | `onException` handler vs branching on the status. It is thrown for statuses outside `okStatusCodeRange` when `throwExceptionOnFailure=true`; resolve its import in the IDE. [errors](./blueprints/fault-tolerance-and-errors.md#handling-httpoperationfailedexception). | "Which statuses must the route treat as failures?" |
| Circuit-breaker defaults (unverified): `faultToleranceConfiguration` defaults and timeout-fallback behaviour | Rely on defaults / set every option explicitly and test the timeout path (recommended). [fault tolerance](./blueprints/fault-tolerance-and-errors.md#circuit-breaker-with-fallback). | "What thresholds and timeout must the breaker enforce?" |
| TLS protocol scope | Keep TLSv1.3 / widen `quarkus.tls.protocols` globally (applies to every bridged Camel SSL context); inbound impact (unverified) / named bucket `quarkus.tls.<name>.protocols` for one legacy peer. Prefer the named bucket ([3.40.0 guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)). | "Which HTTPS endpoints lack TLS 1.3?" |
| Status handling (medium confidence) | `throwExceptionOnFailure=true` plus `onException` / `throwExceptionOnFailure=false` and branch on `CamelHttpResponseCode` / widened `okStatusCodeRange`. The page contradicts itself (see Quick Reference); set the range explicitly. | "Do 4xx responses carry business data the route must parse?" |
| 429 handling (medium confidence) | Default: HttpClient 5 waits for `Retry-After` and retries (hidden latency) vs `automaticRetriesDisabled=true` (429 throws at once). | "Is hidden retry latency acceptable?" |
| Credentials (medium confidence) | `authMethod` Basic/Bearer, or OAuth2 client credentials (`oauth2ClientId`, `oauth2ClientSecret`, `oauth2TokenEndpoint`, `oauth2CacheTokens`). Keep secrets in placeholders, not URIs. Option tables swap two descriptions. | "Which auth scheme does the partner use?" |
| Proxy routes (medium confidence) | Inbound `CamelHttp*` headers leak into the producer; use `bridgeEndpoint=true&skipControlHeaders=true`. | "Does the route forward a consumer request?" |
| Java serialization (medium confidence) | Keep `allowJavaSerializedObject=false`; `transferException` is risky with untrusted peers. Native behaviour (unverified). | "Is the peer trusted and also Camel?" |
| Camel `http` vs Quarkus REST client (medium confidence, no official comparison) | `camel-quarkus-http` for EIP flows / typed `@RestClient` with `tls-configuration-name`. | "Is the call part of a route or a plain service API?" |
| Multiple TLS identities (medium confidence) | `sslContextParameters=#name` per endpoint vs separate component instances (one `SSLContextParameters` per `HttpComponent`). | "How many partner trust or identity sets exist?" |
| Plain `camel-http` instead of the extension (unverified: inferred, no source states the difference) | `camel-quarkus-http` (documented to enable native SSL automatically) / plain `camel-http`, whose native behaviour is not documented here. | "Is there a reason to avoid the Quarkus extension?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Use OpenSSL-style cipher names or unknown protocol names in `quarkus.tls.*`. Since 3.40.0 they fail SSL context creation ([guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)). | Use JSSE names ([guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)). |
| Assume a bridged bean enforces `certificate-revocation-list`, `hostname-verification-algorithm`, `key-store.sni`, `alpn` or `pqc-enforcement-policy`; they are not bridged ([tls-registry page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html)). | Do not rely on `quarkus.tls.*` for CRL or hostname checks, the bridge does not carry them over ([tls-registry page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html)). |
| Add `camel-quarkus-resilience4j`; it is not listed in the 3.40.x [extension index](https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html). | `camel-quarkus-microprofile-fault-tolerance` ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/microprofile-fault-tolerance.html), Stable). |

Medium-confidence anti-patterns (trust-all, `CamelHttpUri` from inbound headers, 4.23+ `oauth2CachedTokensKey`, serialized bodies) are in [never-do patterns](./blueprints/never-do-patterns.md#medium-confidence-anti-patterns).

## Quick Reference

Sources are fetched 2026-10-14. Rows from the versioned 4.22.x http component page are High unless tagged (medium confidence) because the page contradicts itself or carries doc defects there.

| Aspect | Value | Source |
|---|---|---|
| `connectTimeout`, `connectionRequestTimeout`, `soTimeout` | 180000 ms each | https://camel.apache.org/components/4.22.x/http-component.html |
| `responseTimeout` | no default (0 = infinite) | https://camel.apache.org/components/4.22.x/http-component.html |
| `maxTotalConnections` / `connectionsPerRoute` | 200 / 20 | https://camel.apache.org/components/4.22.x/http-component.html |
| `throwExceptionOnFailure`, `followRedirects` (medium confidence) | `true`, `false` | https://camel.apache.org/components/4.22.x/http-component.html |
| `okStatusCodeRange` (medium confidence) | `200-299` default; the prose on the same page says "100..299" is success (contradiction recorded in the research; set the range explicitly if 1xx matters) | https://camel.apache.org/components/4.22.x/http-component.html |
| `allowJavaSerializedObject` | `false` | https://camel.apache.org/components/4.22.x/http-component.html |
| `quarkus.tls.protocols` (High) | `TLSv1.3` (default; bridging applies it since 3.40.0) | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html |
| TLS bridge bean | `defaultSslContextParameters`; rename with `quarkus.camel.tls-registry.default-bean-name` | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html |
| `quarkus.camel.tls-registry.quarkus-default-as-global` | `false`; endpoints then opt in with `useGlobalSslContextParameters=true` (default `false`) | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html |
| Certificate reload | `reload-on-certificate-update=true`, `reload-certificate-delay=2000` ms; restarts affected routes | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html |
| Circuit breaker `inheritErrorHandler` | `false` | https://camel.apache.org/components/4.22.x/eips/circuitBreaker-eip.html |
| Representative commands | `./mvnw quarkus:add-extension -Dextensions="camel-quarkus-http"`, `./mvnw test`, `./mvnw verify -Dnative` (log output unverified) | page not recorded |

## External Resources

All fetched 2026-10-14. camel.apache.org pages carry no page date and are the current stable 3.40.x / 4.22.x docs.

- Extension: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/http.html
- Component options: https://camel.apache.org/components/4.22.x/http-component.html
- TLS registry: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html
- 3.40.0 migration guide: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
- Fault tolerance: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/microprofile-fault-tolerance.html
- Quarkus LTS policy: https://quarkus.io/releases
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
