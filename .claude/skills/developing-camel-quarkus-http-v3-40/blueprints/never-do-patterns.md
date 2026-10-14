# Never-Do Patterns — camel-quarkus-http 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Contents

1. [OpenSSL cipher or unknown protocol names](#1-openssl-cipher-or-unknown-protocol-names-severity-high)
2. [Assuming the bridge enforces revocation and hostname policy](#2-assuming-the-bridge-enforces-revocation-and-hostname-policy-severity-high)
3. [camel-quarkus-resilience4j](#3-camel-quarkus-resilience4j-severity-high)
4. [Medium-confidence anti-patterns](#medium-confidence-anti-patterns) (includes plain camel-http, unverified)

## 1. OpenSSL cipher or unknown protocol names (severity: high)

Since 3.40.0 an unrecognised name fails SSL context creation, and OpenSSL names fail with `ssl-engine=openssl`. A configured list overrides Camel's default exclusion filters (NULL, anon, EXPORT, DES, MD5, RC4), which apply only while `cipher-suites` is unset. Impact: SSL context creation fails, or weak suites are allowed.

```properties
# ❌ WRONG: OpenSSL-style cipher name and a protocol name that is not a JSSE name
quarkus.tls.cipher-suites=ECDHE-RSA-AES128-GCM-SHA256
quarkus.tls.protocols=TLSv9
# ✅ CORRECT: named bucket for the legacy peer, JSSE names
quarkus.tls.legacy-endpoint.protocols=TLSv1.3,TLSv1.2
quarkus.tls.legacy-endpoint.cipher-suites=TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html

## 2. Assuming the bridge enforces revocation and hostname policy (severity: high)

Not bridged: `certificate-revocation-list`, `hostname-verification-algorithm`, `key-store.sni`, `alpn`, `pqc-enforcement-policy`. Startup logs a warning for the first two. Impact: revoked certificates accepted, or `hostname-verification-algorithm=NONE` silently does nothing.

```properties
# ❌ WRONG: ignored by the Camel bridge
quarkus.tls.partner.certificate-revocation-list=/etc/ssl/crl.pem
```
```properties
# ✅ CORRECT: do not rely on quarkus.tls.* for CRL or hostname checks; the bridge does not carry them over.
# Put no revocation or hostname setting under quarkus.tls.partner.*; handle both outside the bridge
quarkus.tls.partner.protocols=TLSv1.3
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html. The endpoint-level option names (`hostnameVerificationPolicy`, default `CLIENT`; `x509HostnameVerifier`) are (medium confidence) (see [tls-and-security](./tls-and-security.md#the-5-settings-that-are-not-bridged)), so they are an Ask First row in SKILL.md, not part of the Never Do alternative.

## 3. camel-quarkus-resilience4j (severity: high)

Not listed in the 3.40.x extension index (its page returned 404). Whether plain `camel-resilience4j` works on Camel Quarkus is (unverified).

```xml
<!-- ❌ WRONG -->
<artifactId>camel-quarkus-resilience4j</artifactId>
<!-- ✅ CORRECT -->
<artifactId>camel-quarkus-microprofile-fault-tolerance</artifactId>
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/resilience4j.html (404).

## Medium-confidence anti-patterns

Contradictory, unversioned, partly read or inferred evidence. They are deliberately not in SKILL.md Never Do. Treat as strong advice, confirm before enforcing.

### Plain `camel-http` where the extension is available (unverified)

This is an inference, not a documented statement: the extension page says what `camel-quarkus-http` enables (native SSL automatically), not what plain `camel-http` lacks. Prefer `camel-quarkus-http` (see [always-do](./always-do-patterns.md#1-dependency-and-native-ssl)); it is an Ask First row in SKILL.md.

Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/http.html

### Trust-all or disabled hostname verification (medium confidence)

The REST client guide marks `trust-all=true` / `hostname-verification-algorithm=NONE` as "not for production"; the http component offers `NoopHostnameVerifier`. Impact: man-in-the-middle.

```java
// ❌ WRONG
.to("https://api.example.com?x509HostnameVerifier=#noopHostnameVerifier")
// ✅ CORRECT: keep default verification
.to("https://api.example.com?sslContextParameters=#partner")
```

Sources: https://quarkus.io/guides/rest-client ; https://camel.apache.org/components/4.22.x/http-component.html

### Java-serialized bodies or `transferException` with untrusted peers (medium confidence)

`allowJavaSerializedObject` defaults to `false`. Since Camel 4.21 an `ObjectInputFilter` applies (`jdk.serialFilter`, or a default denying `java.net.`), plus a new `deserializationFilter` option. Native behaviour is (unverified).

```java
// ❌ WRONG: with allowJavaSerializedObject enabled on the component
.to("http://peer/svc?transferException=true")
// ✅ CORRECT: keep it false; exchange JSON error payloads
.to("https://peer/svc")
```

Sources: https://camel.apache.org/manual/camel-4x-upgrade-guide-4_21.html ; https://camel.apache.org/components/4.22.x/http-component.html

### `CamelHttpUri` leaking from inbound headers on proxy routes (medium confidence)

`CamelHttpUri` overrides the endpoint URI. Inbound `CamelHttp*` headers from a consumer (e.g. platform-http) reach the producer unless `bridgeEndpoint=true` or `skipControlHeaders=true` (both default `false`). Impact: SSRF or wrong path.

```java
// ❌ WRONG
from("platform-http:/proxy").to("https://backend.example.com");
// ✅ CORRECT
from("platform-http:/proxy").to("https://backend.example.com?bridgeEndpoint=true&skipControlHeaders=true");
```

Source: https://camel.apache.org/components/4.22.x/http-component.html

### 4.23+ `oauth2CachedTokensKey` on 4.22.x (unverified)

This option appears only on the `next` page ("before Camel 4.23") and were not in the 4.22.x extraction. Impact: unknown-option failure at endpoint creation.

```java
// ❌ WRONG
.to("https://api?oauth2CacheTokens=true&oauth2CachedTokensKey=FULL_URI")
// ✅ CORRECT
.to("https://api?oauth2CacheTokens=true")
```

Sources: https://camel.apache.org/components/next/http-component.html ; https://camel.apache.org/components/4.22.x/http-component.html
