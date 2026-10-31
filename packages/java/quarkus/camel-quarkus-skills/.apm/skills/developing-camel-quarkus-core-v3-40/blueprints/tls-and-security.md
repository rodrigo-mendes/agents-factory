# TLS and Security — Camel Quarkus 3.40.x

Research date 2026-10-14. Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html (plus the notes below). Back to [SKILL.md](../SKILL.md).

## TLS bridging (new in 3.40)

- `quarkus.tls.*` protocols, cipher suites and key-exchange groups are carried into the `SSLContextParameters` that Camel derives from the TLS registry.
- The default is **TLSv1.3 only**.
- Unknown protocol or cipher names now fail SSL context creation. OpenSSL-style names fail with `ssl-engine=openssl`.
- A configured list overrides Camel's default exclusion filters.
- **Not bridged:** `certificate-revocation-list`, `hostname-verification-algorithm`, `key-store.sni`, `alpn` and `pqc-enforcement-policy`. A bridged bean therefore does not check revocation.

## Scope decision (ask first)

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Keep default TLSv1.3 | Security | Legacy peers fail the handshake | All peers support TLS 1.3 |
| Global widening (`quarkus.tls.protocols=TLSv1.3,TLSv1.2`) | Compatibility | Widens the protocols of every bridged Camel SSL context; inbound platform-http impact (unverified) | Avoid unless every peer needs it |
| Named configuration (`quarkus.tls.legacy-endpoint.protocols`) | Isolation | Extra configuration | One legacy peer |

Ask: "Which downstream endpoints lack TLS 1.3?"

```properties
quarkus.tls.legacy-endpoint.protocols=TLSv1.3,TLSv1.2
quarkus.tls.legacy-endpoint.cipher-suites=TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
```

## Other security notes

- platform-http cannot configure server SSL via `SSLContextParameters`. Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html
- The 3.40.0 release fixed "console: exposure-mode=ALL exposes the dev console in production". Verify dev console exposure in prod. Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
- 3.39: Jolokia is locked down in prod (localhost binding, origin filtering). Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.39.0.html
- 3.40 hardening applies if the extensions are used: XSLT restrictions (external entities, `document()`), Avro trusted packages, and LDAP `security-authentication` no longer defaulting to `none`. Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
- The research contains no auth or crypto design for the core itself.
