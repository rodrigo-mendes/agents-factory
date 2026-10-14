# Security, CORS and TLS: Quarkus REST 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Items here are medium confidence as graded by the research (a full read of each page is not recorded) unless a row says high.

## Contents

- [CORS](#cors)
- [Authorization annotations](#authorization-annotations)
- [PermitAll versus HTTP permissions](#permitall-versus-http-permissions)
- [Proactive authentication](#proactive-authentication)
- [TLS](#tls)

## CORS

(medium confidence; register M2.) `quarkus.http.cors.enabled` defaults to `false`. If `quarkus.http.cors.origins` is unset, only same-origin requests are allowed. "Allowing unrestricted origins with `quarkus.http.cors.origins=*` in production environments poses severe security risks." The rest guide confirms Quarkus includes a CORS filter at the HTTP layer.

```properties
# Quarkus 3.40.x
quarkus.http.cors.enabled=true
quarkus.http.cors.origins=https://app.example.com
%dev.quarkus.http.cors.origins=/.*/

# avoid in production
# quarkus.http.cors.origins=*
```

Source: https://quarkus.io/version/3.40/guides/security-cors

## Authorization annotations

(medium confidence; register M3.) `@RolesAllowed`, `@PermitAll` and `@DenyAll` apply to REST methods. `quarkus.security.jaxrs.deny-unannotated-endpoints` defaults to `false`.

```properties
# Quarkus 3.40.x
quarkus.security.jaxrs.deny-unannotated-endpoints=true   # default false
```

Source: https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference. Whether annotation checks run before request-body deserialization is (unverified) (register U4): do not assume unauthorized callers are rejected before the body is parsed.

## PermitAll versus HTTP permissions

(medium confidence; register M4.) `quarkus.http.auth.permission.*` checks run before annotation checks, so "`@PermitAll` cannot override HTTP-level security configurations". Symptom: unexpected 401 or 403 on a resource marked `@PermitAll`.

```properties
# 🚫 WRONG: policy authenticated on /*, then @PermitAll expecting public access
quarkus.http.auth.permission.all.paths=/*
quarkus.http.auth.permission.all.policy=authenticated

# ✅ CORRECT: open the public prefix at HTTP level
quarkus.http.auth.permission.public.paths=/api/public/*
quarkus.http.auth.permission.public.policy=permit
```

Source: https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference

## Proactive authentication

(medium confidence; register M3.) Proactive authentication "is enabled in Quarkus by default". With it off, reading `SecurityIdentity` on the IO thread fails with `BlockingOperationNotAllowedException`. Source: https://quarkus.io/version/3.40/guides/security-proactive-authentication

## TLS

Source: https://quarkus.io/version/3.40/guides/tls-registry-reference (first 100k chars read, register L1).

- TLS defaults to TLSv1.3.
- REST client: `quarkus.rest-client."key".tls-configuration-name` points to a named bucket ([REST client](./rest-client.md#tls)).
- HTTP server: `quarkus.http.tls-configuration-name=<name>`.
- Camel Quarkus 3.40.0 applies `quarkus.tls` protocols, ciphers and key-exchange groups to Camel SSL contexts built from registered beans; default TLSv1.3 only; unknown names fail; five settings are not bridged (High; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html).
- Whether that bridging affects the inbound platform-http server is (unverified) (register U7): configure server TLS explicitly with `quarkus.http.tls-configuration-name`.
