# TLS and Security — camel-quarkus-http 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Bridging quarkus.tls to Camel

`camel-quarkus-tls-registry` (Experimental, since 3.36.0) turns `quarkus.tls.*` into `SSLContextParameters` beans. Source for everything in this section: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html

| Aspect | Behaviour |
|---|---|
| Default bucket | Bean `defaultSslContextParameters` (rename: `quarkus.camel.tls-registry.default-bean-name`) |
| Named bucket | `quarkus.tls.<name>.*` becomes bean `#<name>` |
| Global use | Default bucket is global only if `quarkus.camel.tls-registry.quarkus-default-as-global=true` (default `false`); endpoints then opt in with `useGlobalSslContextParameters=true` (default `false`) |
| Certificate reload | `reload-on-certificate-update=true`, `reload-certificate-delay=2000` ms; restarts affected routes |
| Enable flag | `quarkus.camel.tls-registry.enabled`; build-time vs runtime is (unverified) |

```xml
<dependency>
  <groupId>org.apache.camel.quarkus</groupId>
  <artifactId>camel-quarkus-tls-registry</artifactId> <!-- Experimental; 3.40.0 on Central 2026-09-24 -->
</dependency>
```
```java
// Camel 4.22.x / Camel Quarkus 3.40.x
.to("https://partner.example.com/api/orders?sslContextParameters=#partner")
```

## 3.40.0 behaviour change

Protocols, cipher suites and key-exchange groups are now applied to bridged beans. With the default `TLSv1.3`, a bridged endpoint offers TLSv1.3 only. Unknown or OpenSSL-style names fail SSL context creation. Fix #9113 per https://camel.apache.org/releases/q-3.40.0/ and PR #9114 per https://github.com/apache/camel-quarkus/releases ; guide: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html

## The 5 settings that are NOT bridged

| `quarkus.tls.*` setting | Consequence |
|---|---|
| `certificate-revocation-list` | Revocation not checked; startup warning |
| `hostname-verification-algorithm` | Ignored; startup warning |
| `key-store.sni` | Not applied |
| `alpn` | Not applied |
| `pqc-enforcement-policy` | Not applied |

Hostname verification is set on the Camel component or endpoint: `x509HostnameVerifier` (no default) and `hostnameVerificationPolicy` (default `CLIENT`) per https://camel.apache.org/components/4.22.x/http-component.html (medium confidence).

## Legacy peer without TLS 1.3

| Option | Optimizes | Sacrifices |
|---|---|---|
| Keep `TLSv1.3` | Security | Handshake fails with legacy peers |
| Global `quarkus.tls.protocols=TLSv1.3,TLSv1.2` | Compatibility | Applies to every bridged Camel SSL context; the impact on the inbound platform-http server is (unverified); prefer the named bucket |
| Named bucket `quarkus.tls.legacy-endpoint.protocols=TLSv1.3,TLSv1.2` | Isolation | One more bucket to maintain |

Ask which endpoints lack TLS 1.3 before any change. Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html

## Authentication (medium confidence)

Source: https://camel.apache.org/components/4.22.x/http-component.html

- `authMethod`: Basic, Bearer, NTLM (NTLM deprecated); `authUsername`, `authPassword`, `authBearerToken`. `authenticationPreemptive` defaults to `false` and is needed for streaming bodies to avoid `NonRepeatableRequestException`.
- OAuth2 client credentials: `oauth2ClientId`, `oauth2ClientSecret`, `oauth2TokenEndpoint`, `oauth2Scope`, `oauth2ResourceIndicator`. `oauth2CacheTokens` defaults to `false`, `oauth2CachedTokensDefaultExpirySeconds` to 3600, `oauth2CachedTokensExpirationMarginSeconds` to 5. Camel does not validate the token.
- Doc defect: the descriptions of `oauth2TokenEndpoint` and `oauth2ResourceIndicator` are swapped in the option tables. Trust the names.
- Camel 4.22 masks parameter names containing `api-key` / `authorization` in sanitized URIs (https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html).

```java
// Camel 4.22.x: secrets as placeholders, never literals in the URI
.to("https://api.example.com/v1/items"
    + "?oauth2ClientId={{api.client-id}}&oauth2ClientSecret={{api.client-secret}}"
    + "&oauth2TokenEndpoint={{api.token-url}}&oauth2CacheTokens=true")
```

## Other security notes (medium confidence)

- Keep `allowJavaSerializedObject=false`. See [never-do](./never-do-patterns.md#medium-confidence-anti-patterns).
- `useSystemProperties=false` is the default; enable only when system proxy or TLS properties are needed.
- Monitor handshake failures at startup after any `quarkus.tls` change; certificate reload restarts routes.
