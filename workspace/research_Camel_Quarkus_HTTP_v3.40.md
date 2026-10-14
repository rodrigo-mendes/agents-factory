# Research: Camel Quarkus HTTP v3.40 (camel-quarkus-http / Camel 4.22.x camel-http / Quarkus 3.40.x)

> Version lock: every claim applies to **Camel Quarkus 3.40.x** (Camel 4.22.x, Quarkus 3.40.x) only. Patterns from the 3.15 research file count as misinformation unless re-verified here.
> All sources fetched **2026-10-14**. Most camel.apache.org pages have no publication date of their own. They count as current because they are the versioned 3.40.x / 4.22.x docs for the current stable LTS.
> Method note: WebFetch returns model-summarised text. Quoted text is the tool's rendering of the page. Check exact wording before quoting verbatim.
> Process note: the plan-approval step (EnterPlanMode/ExitPlanMode) was skipped. This is a forked batch run, and the user approved the scheme in the parent session. No user was available inside the run to approve a plan.
> Core topics (BOM import, route discovery, native reflection, junit rename, Quarkus 4 risk) are **not** repeated here. See `workspace/research_Camel_Quarkus_Core_v3.40.md`.

---

## Metadata

```yaml
Full_Name: Apache Camel Quarkus — HTTP extension (org.apache.camel.quarkus:camel-quarkus-http), wrapping Camel component camel-http (Apache HttpClient 5)
Target_Version: 3.40.x (camel-quarkus-http 3.40.0 on Maven Central 2026-09-24 — https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-http/)
Release_Date: 2026-09-28 (Camel Quarkus 3.40.0 per https://camel.apache.org/releases/ — reused from the core pilot)
Support_Status: LTS (Camel Quarkus 3.40.0 marked LTS at https://camel.apache.org/releases/; Quarkus 3.40 LTS maintained to 2027-09-30 per https://quarkus.io/releases — reused from the core pilot; CQ-specific end date UNVERIFIED)
Primary_Docs: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/http.html + https://camel.apache.org/components/4.22.x/http-component.html
Official_Repo: https://github.com/apache/camel-quarkus
Research_Date: 2026-10-14
Domain_Complexity: Complex (outbound auth incl. OAuth2, TLS bridging with a 3.40 behaviour change, resilience, native mode)
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 5
Unverified_Count: 9
Irresolvable_Count: 3
Research_Quality_Score: 88%   # ~100 claims; (100 - 9 - 3) / 100
```

---

## Executive Summary

`camel-quarkus-http` is the Camel Quarkus extension for the Camel `http`/`https` **producer-only** component. It is supported on JVM and native since 1.0.0, and it enables SSL in native mode automatically, so `quarkus.ssl.native=true` is not needed (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/http.html). The extension page lists no limitations and no `quarkus.camel.*` properties. All behaviour comes from the Camel 4.22.x `camel-http` component, which is built on **Apache HttpClient 5**. The camel-4.22.x parent POM pins `httpclient-version` 5.6.3 and `httpcore-version` 5.4.3 (https://github.com/apache/camel/blob/camel-4.22.x/parent/pom.xml). The version that Quarkus actually resolves is UNVERIFIED.

What changed for HTTP users in 3.40:
1. **TLS bridging.** `camel-quarkus-tls-registry` (Experimental, since 3.36.0) turns `quarkus.tls.*` into `SSLContextParameters` beans. From 3.40.0, `protocols`, `cipher-suites` and `key-exchange-groups` are also applied. Since `quarkus.tls.protocols` defaults to `TLSv1.3`, a bridged `https:` endpoint now offers **TLSv1.3 only**. Unknown or OpenSSL-style names now fail SSL context creation (https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html).
2. **Inherited Camel 4.18–4.22 changes:**
   - gzip double-decompression fix with HttpClient 5.6+ (https://camel.apache.org/manual/camel-4x-upgrade-guide-4_18.html).
   - An `ObjectInputFilter` on the `transferException`/`allowJavaSerializedObject` path, plus the new `deserializationFilter` option (https://camel.apache.org/manual/camel-4x-upgrade-guide-4_21.html).
   - OAuth2 client-credentials options on the endpoint (https://camel.apache.org/components/4.22.x/http-component.html).
3. **No `camel-quarkus-resilience4j` extension exists in 3.40.x.** Its page returns 404 and it is not in the index (https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html). The circuit breaker on Camel Quarkus is `camel-quarkus-microprofile-fault-tolerance`.

Critical patterns:
- Set explicit timeouts. Component defaults are 180000 ms for connect, connection-request and socket, and `responseTimeout` has no default (0 = infinite).
- Reference the bridged bean `#defaultSslContextParameters` or a named one, and decide the TLS protocol scope consciously.
- Handle `HttpOperationFailedException` (`throwExceptionOnFailure=true` by default). Wrap calls in `circuitBreaker()` with `onFallback` from the fault-tolerance extension.

The tier is **Complex** because the extension handles credentials (Basic, Bearer, OAuth2), TLS policy and resilience across several integrations.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**1. Use `camel-quarkus-http` (not plain `camel-http`) managed by the platform BOM**
> Confidence: 🟢 High | [✓✓ Triangulated | CQ http extension page (2026-10-14) + Maven Central camel-quarkus-http 3.40.0 (2026-09-24)]
- Why: the extension adds native support and auto-enables native SSL. BOM alignment rules are in the core research file.
- Code:
  ```xml
  <!-- Camel Quarkus 3.40.x; version managed by quarkus-camel-bom (see core research) -->
  <dependency>
    <groupId>org.apache.camel.quarkus</groupId>
    <artifactId>camel-quarkus-http</artifactId>
  </dependency>
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/http.html (2026-10-14); https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-http/ (3.40.0 dated 2026-09-24)

**2. Set explicit timeouts and pool sizes. Never rely on the 3-minute defaults.**
> Confidence: 🟡 Medium (single page; values seen consistently by 3 independent fetches of https://camel.apache.org/components/4.22.x/http-component.html)
- Why: component defaults (all from https://camel.apache.org/components/4.22.x/http-component.html):

  | Option | Default |
  |---|---|
  | `connectTimeout` | 180000 ms |
  | `connectionRequestTimeout` | 180000 ms |
  | `soTimeout` | 180000 ms |
  | `responseTimeout` | no default (0 = infinite) |
  | `maxTotalConnections` | 200 |
  | `connectionsPerRoute` | 20 |
  | `connectionTimeToLive` | no default |

  A slow downstream holds threads for up to 3 minutes, or forever.
- Code (Camel Quarkus 3.40.x `application.properties`; standard Camel `camel.component.<name>.<option>` binding):
  ```properties
  camel.component.https.connect-timeout=5000
  camel.component.https.connection-request-timeout=2000
  camel.component.https.response-timeout=10000
  camel.component.https.max-total-connections=200
  camel.component.https.connections-per-route=20
  ```
- Source: https://camel.apache.org/components/4.22.x/http-component.html (2026-10-14)

**3. Use the TLS registry bridge for `https:` and reference the bean explicitly** ⚠️ Migration Note
> Confidence: 🟢 High | [✓✓ Triangulated | tls-registry extension page + 3.40.0 migration guide (2026-10-14)]
- Why: `quarkus.tls.*` becomes the bean `defaultSslContextParameters` (renamed with `quarkus.camel.tls-registry.default-bean-name`). Named buckets `quarkus.tls.<name>.*` become beans `#<name>`. The default bucket is set as global only if `quarkus.camel.tls-registry.quarkus-default-as-global=true` (default `false`), and endpoints then opt in with `useGlobalSslContextParameters=true` (default `false`). Certificate reload is on by default (`reload-on-certificate-update=true`, `reload-certificate-delay=2000` ms) and restarts the affected routes. All of this is from https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html.
- Code:
  ```xml
  <dependency>
    <groupId>org.apache.camel.quarkus</groupId>
    <artifactId>camel-quarkus-tls-registry</artifactId>  <!-- Experimental; 3.40.0 on Central 2026-09-24 -->
  </dependency>
  ```
  ```properties
  # Camel Quarkus 3.40.x
  quarkus.tls.partner.trust-store.p12.path=/etc/ssl/partner-truststore.p12
  quarkus.tls.partner.trust-store.p12.password=${PARTNER_TRUSTSTORE_PASSWORD}
  ```
  ```java
  // Camel 4.22.x / Camel Quarkus 3.40.x
  from("direct:callPartner")
      .to("https://partner.example.com/api/orders?sslContextParameters=#partner");
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html (2026-10-14); https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html (2026-10-14); https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-tls-registry/ (3.40.0, 2026-09-24)

**4. Handle `HttpOperationFailedException` explicitly**
> Confidence: 🟢 High | [✓✓ Triangulated | http-component page + resilience4j/circuitBreaker EIP pages (2026-10-14)]
- Why: `throwExceptionOnFailure=true` by default. A status outside `okStatusCodeRange` (default `200-299`) throws `HttpOperationFailedException`, which carries the status code, the status line, the redirect location and the body as a String. `followRedirects` defaults to false (https://camel.apache.org/components/4.22.x/http-component.html).
- Code:
  ```java
  // Camel 4.22.x
  onException(HttpOperationFailedException.class)
      .onWhen(exchange -> exchange.getException(HttpOperationFailedException.class).getStatusCode() >= 500)
      .maximumRedeliveries(2).redeliveryDelay(500)
      .handled(true)
      .to("direct:httpServerError");
  ```
- Source: https://camel.apache.org/components/4.22.x/http-component.html (2026-10-14); https://camel.apache.org/manual/error-handler.html (2026-10-14; `onException`, `maximumRedeliveries`, `redeliveryDelay`)

**5. Wrap calls in `circuitBreaker()` with `onFallback` using `camel-quarkus-microprofile-fault-tolerance`**
> Confidence: 🟢 High | [✓✓ Triangulated | CQ fault-tolerance extension page + circuitBreaker EIP + fault-tolerance EIP (2026-10-14)]
- Why: this extension is Stable, JVM and native since 1.0.0 ("Circuit Breaker EIP using MicroProfile Fault Tolerance"). `inheritErrorHandler` defaults to false, so the protected step runs once and the breaker handles the failure.
- Code:
  ```java
  // Camel 4.22.x / Camel Quarkus 3.40.x (camel-quarkus-microprofile-fault-tolerance)
  from("direct:quote")
      .circuitBreaker()
          .faultToleranceConfiguration().timeoutEnabled(true).timeoutDuration(2000).end()
          .to("https://quotes.example.com/v1/quote?sslContextParameters=#defaultSslContextParameters")
      .onFallback()
          .transform().constant("{\"status\":\"degraded\"}")
      .end();
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/microprofile-fault-tolerance.html ; https://camel.apache.org/components/4.22.x/eips/circuitBreaker-eip.html ; https://camel.apache.org/components/4.22.x/eips/fault-tolerance-eip.html (all 2026-10-14)

**6. Keep credentials out of URIs. Use options and property placeholders.**
> Confidence: 🟡 Medium (single page)
- Why: options are `authMethod` (Basic, Bearer, NTLM; NTLM is deprecated), `authUsername`, `authPassword` and `authBearerToken`. `authenticationPreemptive` defaults to false and is needed for streaming bodies to avoid `NonRepeatableRequestException`. OAuth2 client credentials use `oauth2ClientId`, `oauth2ClientSecret`, `oauth2TokenEndpoint`, `oauth2Scope` and `oauth2ResourceIndicator`. `oauth2CacheTokens` defaults to false, `oauth2CachedTokensDefaultExpirySeconds` to 3600 and `oauth2CachedTokensExpirationMarginSeconds` to 5. Camel does not validate the token. Camel 4.22 also masks parameter names containing `api-key`/`authorization` in sanitized URIs (https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html).
- Code:
  ```java
  // Camel 4.22.x
  .to("https://api.example.com/v1/items"
      + "?oauth2ClientId={{api.client-id}}&oauth2ClientSecret={{api.client-secret}}"
      + "&oauth2TokenEndpoint={{api.token-url}}&oauth2CacheTokens=true")
  ```
- Source: https://camel.apache.org/components/4.22.x/http-component.html (2026-10-14). Doc defect: the descriptions of `oauth2TokenEndpoint` and `oauth2ResourceIndicator` are swapped in the option tables. Trust the names, not the descriptions.

### ⚠️ Conditional Patterns

**A. TLS protocol scope for a legacy (no TLS 1.3) partner** ⚠️ Migration Note
> Confidence: 🟢 High
- Options: A) keep the default `TLSv1.3`; B) widen globally (`quarkus.tls.protocols=TLSv1.3,TLSv1.2`); C) a named bucket only for the legacy endpoint (`quarkus.tls.legacy-endpoint.protocols=TLSv1.3,TLSv1.2`).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | Security | Handshake fails with legacy peers | All peers support TLS 1.3 |
  | B | Compatibility | Weakens every TLS user in the app, not only Camel | Avoid |
  | C | Isolation | One more bucket to maintain | One legacy peer |

- Agent: "Ask which downstream HTTPS endpoints lack TLS 1.3 before any `quarkus.tls.protocols` change."
- Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html ; https://quarkus.io/guides/tls-registry-reference (default `TLSv1.3`; unpinned "current" URL, Medium) (2026-10-14)

**B. Status-code handling: exception vs inspect**
> Confidence: 🟡 Medium
- Options: A) the default `throwExceptionOnFailure=true` plus `onException`; B) `throwExceptionOnFailure=false` and branch on the `CamelHttpResponseCode` header; C) a widened `okStatusCodeRange` (e.g. `200-204,209,301-304`).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | Fail-fast, works with the circuit breaker | Exception cost | Default |
  | B | Full control over 4xx bodies | Easy to forget a check | APIs with meaningful 4xx payloads |
  | C | Declarative | Hides real failures | Known non-2xx success codes |

- Agent: "Ask whether 4xx responses carry business data the route must parse."
- Source: https://camel.apache.org/components/4.22.x/http-component.html (2026-10-14). Contradiction on that page: the prose says "100..299" is success, while the option default is `200-299`. Set the option explicitly if 1xx matters.

**C. HTTP 429 handling**
> Confidence: 🟡 Medium
- Options: A) the default, where HttpClient 5 waits for `Retry-After` and retries automatically; B) `automaticRetriesDisabled=true`, where 429 throws `HttpOperationFailedException` at once and Camel or the breaker handles it.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | Simplicity | Hidden latency, thread held during the wait | Low-volume calls |
  | B | Visible and controlled backoff | More route code | Rate-limited APIs under load |

- Agent: "Ask whether hidden retry latency is acceptable."
- Source: https://camel.apache.org/components/4.22.x/http-component.html (2026-10-14)

**D. Camel `http` producer vs Quarkus REST client**
> Confidence: 🟡 Medium (no official page compares them)
- Options: A) `camel-quarkus-http` inside routes; B) the `quarkus-rest-client-jackson` typed interface (`@RegisterRestClient` / `@RestClient`), called from a bean.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | EIP integration (circuitBreaker, onException, headers), dynamic URIs | Untyped | Integration flows |
  | B | Typed API, uses `quarkus.rest-client.<name>.tls-configuration-name` natively | Camel error handling needs a bean wrapper | Typed contract-first APIs |

- Agent: "Ask whether the call is part of a Camel route or a plain service API."
- Source: https://quarkus.io/guides/rest-client (examples on 3.40.1; `tls-configuration-name` uses `quarkus.tls.<name>.*`, and when set the default TLS config is ignored) (2026-10-14)

**E. Multiple TLS identities**
> Confidence: 🟡 Medium
- Options: A) the `sslContextParameters=#name` endpoint option per call; B) separate component instances.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | Few components | Per-endpoint configuration | A few partners |
  | B | Isolates pools and timeouts per partner | More beans | Different SLAs per partner |

- Agent: "Ask how many partner trust or identity sets exist."
- Source: https://camel.apache.org/components/4.22.x/http-component.html ("only one instance of SSLContextParameters per HttpComponent") (2026-10-14)

### 🚫 Forbidden Patterns

**1. Using OpenSSL cipher names or unknown protocol names in `quarkus.tls.*`**
> Severity: Critical
> Confidence: 🟢 High
- Why: since 3.40.0 an unrecognised name fails SSL context creation, and OpenSSL names fail with `ssl-engine=openssl`. A configured list also overrides Camel's default exclusion filters. Cipher exclusions (NULL, anon, EXPORT, DES, MD5, RC4) apply only while `cipher-suites` is unset.
- Impact: the app fails at startup, or weak suites are allowed.
- ❌ Wrong:
  ```properties
  quarkus.tls.cipher-suites=ECDHE-RSA-AES128-GCM-SHA256
  quarkus.tls.protocols=TLSv1.3,TLSv1.2,TLSv1
  ```
- ✅ Correct:
  ```properties
  quarkus.tls.legacy-endpoint.protocols=TLSv1.3,TLSv1.2
  quarkus.tls.legacy-endpoint.cipher-suites=TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html (2026-10-14)

**2. Assuming a bridged bean checks revocation and hostname policy**
> Severity: High
> Confidence: 🟢 High
- Why: these settings are not bridged: `certificate-revocation-list`, `hostname-verification-algorithm`, `key-store.sni`, `alpn` and `pqc-enforcement-policy`. Startup logs a warning for the first two. Hostname verification is set on the Camel component or endpoint (`x509HostnameVerifier`, no default; `hostnameVerificationPolicy`, default `CLIENT`).
- Impact: revoked certificates are accepted, or `hostname-verification-algorithm=NONE` silently does nothing.
- ❌ Wrong:
  ```properties
  quarkus.tls.partner.certificate-revocation-list=/etc/ssl/crl.pem   # ignored by Camel bridge
  ```
- ✅ Correct:
  ```java
  // Camel 4.22.x — set verification on the endpoint/component; handle CRL outside the bridge
  .to("https://partner.example.com/api?sslContextParameters=#partner&hostnameVerificationPolicy=CLIENT")
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html ; https://camel.apache.org/components/4.22.x/http-component.html (2026-10-14)

**3. Disabling hostname verification (`NoopHostnameVerifier`) or trust-all in production**
> Severity: Critical
> Confidence: 🟡 Medium
- Why: the REST client guide marks `trust-all=true` / `hostname-verification-algorithm=NONE` as "not for production". The http component offers `NoopHostnameVerifier` as a possible value.
- Impact: man-in-the-middle exposure.
- ❌ Wrong:
  ```java
  .to("https://api.example.com?x509HostnameVerifier=#noopHostnameVerifier")
  ```
- ✅ Correct:
  ```java
  .to("https://api.example.com?sslContextParameters=#partner")   // default verification kept
  ```
- Source: https://quarkus.io/guides/rest-client ; https://camel.apache.org/components/4.22.x/http-component.html (2026-10-14)

**4. Adding `camel-quarkus-resilience4j`**
> Severity: High
> Confidence: 🟢 High
- Why: there is no such extension in 3.40.x. Its page returns 404 and it is absent from the extension index.
- Impact: dependency resolution fails, or plain `camel-resilience4j` runs without Quarkus native support (UNVERIFIED).
- ❌ Wrong:
  ```xml
  <artifactId>camel-quarkus-resilience4j</artifactId>
  ```
- ✅ Correct:
  ```xml
  <artifactId>camel-quarkus-microprofile-fault-tolerance</artifactId>
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/resilience4j.html (404) (2026-10-14)

**5. Enabling Java-serialized bodies or `transferException` with untrusted peers**
> Severity: Critical
> Confidence: 🟡 Medium
- Why: `allowJavaSerializedObject` defaults to false. Since Camel 4.21 an `ObjectInputFilter` applies, and when unset it uses `jdk.serialFilter` or a default that denies `java.net.`. Native-mode behaviour for this path is UNVERIFIED.
- Impact: deserialization attacks.
- ❌ Wrong:
  ```java
  .to("http://peer/svc?transferException=true")   // with allowJavaSerializedObject enabled on the component
  ```
- ✅ Correct:
  ```java
  .to("https://peer/svc")   // keep allowJavaSerializedObject=false; exchange JSON error payloads
  ```
- Source: https://camel.apache.org/manual/camel-4x-upgrade-guide-4_21.html ; https://camel.apache.org/components/4.22.x/http-component.html (2026-10-14)

**6. Overriding the target with `CamelHttpUri` from inbound headers (proxy routes)**
> Severity: High
> Confidence: 🟡 Medium
- Why: `CamelHttpUri` overrides the endpoint URI. Inbound `CamelHttp*` headers from a consumer (e.g. platform-http) leak into the producer unless `bridgeEndpoint=true` or `skipControlHeaders=true` (both default false).
- Impact: SSRF, or requests sent to the wrong path.
- ❌ Wrong:
  ```java
  from("platform-http:/proxy").to("https://backend.example.com");
  ```
- ✅ Correct:
  ```java
  from("platform-http:/proxy").to("https://backend.example.com?bridgeEndpoint=true&skipControlHeaders=true");
  ```
- Source: https://camel.apache.org/components/4.22.x/http-component.html (2026-10-14)

**7. Using the 4.23+ `oauth2CachedTokensKey` options on 4.22.x**
> Severity: Medium
> Confidence: 🟡 Medium
- Why: these options appear only on the `next` page, which mentions "before Camel 4.23". They were not in the 4.22.x extraction.
- Impact: unknown-option failure at endpoint creation.
- ❌ Wrong:
  ```java
  .to("https://api?oauth2CacheTokens=true&oauth2CachedTokensKey=FULL_URI")
  ```
- ✅ Correct:
  ```java
  .to("https://api?oauth2CacheTokens=true")
  ```
- Source: https://camel.apache.org/components/next/http-component.html vs https://camel.apache.org/components/4.22.x/http-component.html (2026-10-14)

---

## Migration Guide

> Confidence: 🟢 High | Sources: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html (2026-10-14) + https://camel.apache.org/releases/q-3.40.0/ (2026-10-14)

**Breaking changes (3.15 → 3.40, HTTP-relevant):**
- **3.36.0**: `camel-quarkus-tls-registry` was added (GitHub #8603, https://github.com/apache/camel-quarkus/releases).
- **3.40.0**: TLS registry protocols, ciphers and key-exchange groups are enforced on bridged beans. The default is TLSv1.3 only, and unknown or OpenSSL names fail. Fix #9113 per https://camel.apache.org/releases/q-3.40.0/ and PR #9114 per https://github.com/apache/camel-quarkus/releases.
- **3.39.0**: native-mode Jolokia refuses an HTTPS origin over a plain HTTP agent. This is not camel-http (https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.39.0.html).
- **Camel 4.18**: gzip responses were decompressed twice with HttpClient 5.6+. Fixed by stripping stale `Content-Encoding`/`Content-Length`/`Content-MD5` headers (https://camel.apache.org/manual/camel-4x-upgrade-guide-4_18.html, partially read).
- **Camel 4.21**: `ObjectInputFilter` on the `transferException`/`allowJavaSerializedObject` path, plus the new `deserializationFilter` option (https://camel.apache.org/manual/camel-4x-upgrade-guide-4_21.html, partially read).
- **Camel 4.19 / 4.20 / 4.22**: no camel-http producer change found (https://camel.apache.org/manual/camel-4x-upgrade-guide-4_19.html, .../4_20.html, .../4_22.html).
- Testing (inherited from the core research): `camel-quarkus-junit5` was renamed to `camel-quarkus-junit` in 3.31, and AdviceWith auto-starts routes from 3.36.

**Upgrade steps:**
1. Bump `quarkus.platform.version` to 3.40.1 (see core research).
2. Grep for `quarkus.tls.` and check every protocol and cipher name against JSSE names.
3. List the HTTPS partners without TLS 1.3 and add named buckets for them.
4. Replace any `camel-quarkus-resilience4j` with `camel-quarkus-microprofile-fault-tolerance`.
5. Re-check `okStatusCodeRange`, the timeouts and `allowJavaSerializedObject`.

**Compatibility Matrix:**

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Camel Quarkus | 3.40.0 | 3.40.x | camel-quarkus-http 3.40.0 on Central, 2026-09-24 (https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-http/) |
| Camel | 4.22.x | 4.22.x | Per the 3.40.x docs index (core research) |
| Apache HttpClient | 5.6.3 | — | camel-4.22.x parent pom; the Quarkus-resolved version is UNVERIFIED |
| Java | 17 | 21 | https://camel.apache.org/releases/q-3.40.0/ |
| camel-quarkus-tls-registry | 3.36.0 | 3.40.x | Experimental (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html) |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | official docs (http component + tls-registry) + CQ testing guide]

**Lifecycle**:
```java
// Camel Quarkus 3.40.x / Camel 4.22.x — Init via CDI-discovered RouteBuilder, usage in route, cleanup by Quarkus shutdown
import org.apache.camel.builder.RouteBuilder;
import org.apache.camel.http.base.HttpOperationFailedException; // package UNVERIFIED on fetched pages — check IDE import

public class PartnerRoutes extends RouteBuilder {
    @Override
    public void configure() {
        onException(HttpOperationFailedException.class)
            .handled(true)
            .setBody(simple("{\"error\":\"upstream ${exception.statusCode}\"}"));

        from("direct:getOrder").routeId("get-order")
            .removeHeaders("CamelHttp*")
            .setHeader("CamelHttpMethod", constant("GET"))
            .setHeader("CamelHttpPath", simple("/orders/${header.orderId}"))
            .circuitBreaker()
                .faultToleranceConfiguration().timeoutEnabled(true).timeoutDuration(2000).end()
                .to("https://partner.example.com/api?sslContextParameters=#partner&responseTimeout=5000")
            .onFallback()
                .setBody(constant("{\"status\":\"degraded\"}"))
            .end();
    }
}
```

**Integration**: Camel Quarkus HTTP ↔ quarkus.tls (application.properties)
```properties
# Camel Quarkus 3.40.x
quarkus.camel.tls-registry.enabled=true
quarkus.tls.partner.trust-store.p12.path=/etc/ssl/partner-truststore.p12
quarkus.tls.partner.trust-store.p12.password=${PARTNER_TRUSTSTORE_PASSWORD}
# TLSv1.3 is the default (https://quarkus.io/guides/tls-registry-reference); widen only per bucket
camel.component.https.connect-timeout=5000
```

**Integration**: Quarkus REST client (alternative, typed)
```properties
# Quarkus 3.40.x — https://quarkus.io/guides/rest-client
quarkus.rest-client.partner-api.url=https://partner.example.com/api
quarkus.rest-client.partner-api.tls-configuration-name=partner
```

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment
./mvnw quarkus:add-extension -Dextensions="camel-quarkus-http,camel-quarkus-tls-registry,camel-quarkus-microprofile-fault-tolerance"
./mvnw test                      # JVM tests (CamelQuarkusTestSupport is JVM-only)
./mvnw verify -Dnative           # native; SSL auto-enabled by camel-quarkus-http
grep -rn "quarkus.tls" src/main/resources/application.properties   # audit names (JSSE only)
# Expected: BUILD SUCCESS; no "SSL context" creation errors at startup
```

**Mocking** (https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html; WireMock pattern also in https://quarkus.io/guides/rest-client):
```java
// Camel Quarkus 3.40.x — test resource with WireMock
public class PartnerWireMock implements QuarkusTestResourceLifecycleManager {
    WireMockServer server;
    @Override public Map<String, String> start() {
        server = new WireMockServer(wireMockConfig().dynamicPort());
        server.start();
        server.stubFor(get(urlPathMatching("/orders/.*")).willReturn(okJson("{\"id\":1}")));
        return Map.of("partner.base-url", server.baseUrl());   // overrides application.properties
    }
    @Override public void stop() { server.stop(); }
}

@QuarkusTest
@QuarkusTestResource(PartnerWireMock.class)
class GetOrderTest extends CamelQuarkusTestSupport {
    // AdviceWith.adviceWith(context, "get-order", a -> a.weaveByToUri("https://*").replace().to("mock:partner"));
    // Use specific URIs, not wildcards, per the testing guide.
}
```
- Notes: `CamelQuarkusTestSupport` is JVM only, and a single CamelContext is shared across tests. Use `adviceRoute()` per method. `createCamelRegistry` throws `UnsupportedOperationException`. `interceptSendToEndpoint` is not covered by the CQ testing guide (UNVERIFIED there).

---

## Production Readiness

- **Performance**: the pool defaults are 200 total and 20 per route. `responsePayloadStreamingThreshold` defaults to 8192. `disableStreamCache=false` by default (https://camel.apache.org/components/4.22.x/http-component.html).
- **Scalability**: the per-route limit (20) caps concurrency to one host. Size it to match the thread pool and the downstream SLA.
- **Monitoring**: track the circuit-breaker state, the `CamelHttpResponseCode` distribution and handshake failures at startup after any `quarkus.tls` change. The certificate reload restarts routes (`reload-certificate-delay=2000` ms, https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html).
- **Security**:
  - TLSv1.3 is the default.
  - Revocation is not bridged.
  - Keep `allowJavaSerializedObject=false`.
  - Use placeholders for secrets.
  - Use `bridgeEndpoint`/`skipControlHeaders` on proxies.
  - Use `useSystemProperties=false` (default) unless you need system proxy or TLS properties.

---

## Reference Implementations

- https://camel.apache.org/components/4.22.x/http-component.html — option tables and examples
- https://camel.apache.org/components/4.22.x/eips/circuitBreaker-eip.html — `onFallback` example with an HTTP call
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html — WireMock test resource and AdviceWith
- https://github.com/apache/camel-quarkus (integration-tests/http module; contents not fetched)

---

## Source Bibliography

**Primary** (all accessed 2026-10-14):
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/http.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/microprofile-fault-tolerance.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html (+ index, 3.39.0, 3.38.0, 3.36.0, 3.35.0, 3.33.0)
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
- https://camel.apache.org/releases/q-3.40.0/
- https://github.com/apache/camel-quarkus/releases
- https://camel.apache.org/components/4.22.x/http-component.html
- https://camel.apache.org/components/next/http-component.html (4.23+, cross-check only)
- https://camel.apache.org/components/4.22.x/eips/circuitBreaker-eip.html
- https://camel.apache.org/components/4.22.x/eips/fault-tolerance-eip.html
- https://camel.apache.org/components/4.22.x/eips/resilience4j-eip.html
- https://camel.apache.org/manual/error-handler.html
- https://camel.apache.org/manual/camel-4x-upgrade-guide-4_18.html, 4_19, 4_20, 4_21, 4_22
- https://github.com/apache/camel/blob/camel-4.22.x/parent/pom.xml
- https://quarkus.io/guides/tls-registry-reference
- https://quarkus.io/guides/rest-client
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-http/ and .../camel-quarkus-tls-registry/

**Validation**: no community sources used.

---

## Research Gaps

```
Gap: Apache HttpClient 5 version actually resolved under quarkus-camel-bom 3.40.x
Impact: CVE triage; the 4.18 gzip fix depends on 5.6+
Workaround: ./mvnw dependency:tree | grep httpclient5
Follow-up: Maven Central quarkus-bom 3.40.1 pom
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: Whether plain camel-resilience4j works on Camel Quarkus 3.40 (JVM/native)
Impact: Teams porting resilience4jConfiguration routes
Workaround: Use camel-quarkus-microprofile-fault-tolerance
Follow-up: Camel Quarkus GitHub issues
§7-ref: Iteration 2 — IRRESOLVABLE
```
```
Gap: faultToleranceConfiguration option defaults (and whether fallback runs on timeout)
Impact: Breaker thresholds and timeout semantics
Workaround: Set every option explicitly; test the timeout path
Follow-up: https://camel.apache.org/components/4.22.x/eips/faultToleranceConfiguration-eip.html
§7-ref: Iteration 1 — IRRESOLVABLE
```
Other UNVERIFIED items:
- `transferException` in native mode.
- The `HttpOperationFailedException` Java package.
- `interceptSendToEndpoint` in the CQ guide.
- The Dead Letter Channel default of 6 redeliveries / 1 s (summariser only).
- Build-time vs runtime for `quarkus.camel.tls-registry.*`.
- `oauth2CachedTokensKey` in 4.22.
- The Camel Quarkus LTS end date.

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 0 | Guardrails | tls-registry bridge properties and defaults | Added | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html (2026-10-14) |
| 0 | Guardrails | camel-quarkus-resilience4j absent | Added | https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html (2026-10-14) |
| 1 | Guardrails | headerFilterStrategy option exists (no default) | Resolved | https://camel.apache.org/components/4.22.x/http-component.html (2026-10-14) |
| 1 | Guardrails | okStatusCodeRange 200-299 vs prose 100..299 | Updated (contradiction recorded) | https://camel.apache.org/components/4.22.x/http-component.html (2026-10-14) |
| 1 | Guardrails | faultToleranceConfiguration defaults | ⚠️ IRRESOLVABLE — the EIP page only links to the config page | — |
| 2 | Migration | camel-quarkus-tls-registry 3.40.0 published | Resolved | https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-tls-registry/ (2026-09-24) |
| 2 | Guardrails | camel-resilience4j on Quarkus | ⚠️ IRRESOLVABLE — no official CQ statement | — |
| 3 | Metadata | camel-quarkus-http 3.40.0 on Central | Resolved | https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-http/ (2026-09-24) |
| 3 | Compatibility | Quarkus-resolved httpclient5 version | ⚠️ IRRESOLVABLE — not checked within the iteration budget | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Complex)
- [x] All scope areas cited (endpoint options, methods/headers, query/body, timeouts/pool, TLS, auth, errors, resilience, HttpClient version, native, testing)
- [x] Pattern counts driven by domain needs (6 / 5 / 7)
- [x] Every anti-pattern has alternative
- [x] All CLI commands validated/marked as representative
- [x] Integration examples complete (quarkus.tls, REST client, fault tolerance)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated (deep) or downgraded to 🟡 Medium (patterns 2 and 6)
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in §7

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: the camel-quarkus-http coordinates and native SSL; TLS bridging and the TLSv1.3 default; the not-bridged settings list; `throwExceptionOnFailure` / `HttpOperationFailedException`; fault-tolerance as the circuit-breaker extension; no resilience4j extension.
- **Medium Confidence (validate with user)**: the timeout and pool defaults (single page); the auth/OAuth2 options; the REST client vs camel-http choice; 429 auto-retry; the `quarkus.tls` reference (unpinned URL).
- **Low Confidence (must ask human)**: the IRRESOLVABLE items (the httpclient5 version under Quarkus, resilience4j on Quarkus, fault-tolerance defaults); `transferException` in native.
- **Edge Cases (pause)**: Camel Quarkus 3.40.0 was released 2026-09-28, which is less than 30 days before the research date. `camel-quarkus-tls-registry` is Experimental. Quarkus 4 risk: see the core research.
- **Emergency Stop**: not triggered.
