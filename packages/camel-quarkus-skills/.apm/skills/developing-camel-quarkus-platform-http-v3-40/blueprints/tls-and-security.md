# TLS and Security — Camel Quarkus Platform HTTP 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Contents

- [HTTPS configuration](#https-configuration)
- [Does the 3.40 bridging affect the inbound server](#does-the-340-bridging-affect-the-inbound-server)
- [Legacy peers](#legacy-peers)
- [Authentication and identity](#authentication-and-identity)
- [Cookies and error detail](#cookies-and-error-detail)
- [Management interface TLS](#management-interface-tls)

## HTTPS configuration

`SSLContextParameters` is not supported for platform-http; use the Quarkus TLS registry ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)).

```properties
# Quarkus 3.40
quarkus.tls.https.key-store.p12.path=/etc/tls/server.p12
quarkus.tls.https.key-store.p12.password=${KEYSTORE_PASSWORD}
quarkus.http.tls-configuration-name=https
quarkus.http.insecure-requests=redirect
```

`quarkus.http.ssl-port` defaults to `8443`; `insecure-requests` defaults to `enabled` ([HTTP reference](https://quarkus.io/version/3.40/guides/http-reference)). The named configuration `https` is shown in section 3.1 of the "Latest" HTTP reference (medium confidence, https://quarkus.io/guides/http-reference).

## Does the 3.40 bridging affect the inbound server

Whether the bridging touches the inbound server is (unverified): no page states it.

- Fact: the 3.40.0 migration guide changes how Camel bridges `quarkus.tls` into `SSLContextParameters`. Protocols, ciphers and key-exchange groups are now applied, the default is TLSv1.3 only, and unknown names fail ([migration guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)). The guide does not mention platform-http or the HTTP server.
- Fact: platform-http does not support `SSLContextParameters` ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)); server TLS is owned by Vert.x HTTP through `quarkus.http.tls-configuration-name`.
- The guide describes Camel SSL contexts built from registered beans (High). Whether the bridging also affects the inbound platform-http server is (unverified); not resolvable from documentation.
- Workaround: after upgrading, test with `openssl s_client -tls1_2 -connect host:8443` (representative; adapt host and port) and compare with your pre-upgrade behaviour.

## Legacy peers

Global `quarkus.tls.protocols` widening: unknown names fail since 3.40 (High), but its impact on the inbound server is (unverified), so this is an Ask First decision, not a Never Do rule. A named configuration is the cautious option ([migration guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)):

```properties
quarkus.tls.legacy-endpoint.protocols=TLSv1.3,TLSv1.2
```

Details from the guide: a configured cipher list overrides Camel's exclusion filters; `certificate-revocation-list`, `hostname-verification-algorithm`, `key-store.sni`, `alpn` and `pqc-enforcement-policy` are still not bridged. Use JSSE names, not OpenSSL names.

## Authentication and identity

- The authenticated user arrives in the `VertxPlatformHttpConstants.AUTHENTICATED_USER` header ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)).
- With the Vert.x engine, Bearer token validation runs before the body handler ([component page](https://camel.apache.org/components/4.22.x/platform-http-component.html)).
- Path permissions; property names (unverified), security guide not fetched:

```properties
# Quarkus 3.40; confirm names against the Quarkus security guide before use
quarkus.http.auth.permission.api.paths=/api/*
quarkus.http.auth.permission.api.policy=authenticated
```

The effect of `quarkus.http.root-path` on these paths and on Camel routes is (unverified).

## Cookies and error detail

`cookieSecure` and `cookieHttpOnly` default to `false`, so set them when you use cookies. `serverRequestValidation` defaults to `true` ([component page](https://camel.apache.org/components/4.22.x/platform-http-component.html)). `muteException` defaults to `true`; see [error handling](./integration-examples.md#error-handling).

## Management interface TLS

When `quarkus.management.enabled=true`, it has its own TLS through `quarkus.management.tls-configuration-name`, and plain HTTP is rejected once HTTPS is configured ([management reference](https://quarkus.io/version/3.40/guides/management-interface-reference)).
