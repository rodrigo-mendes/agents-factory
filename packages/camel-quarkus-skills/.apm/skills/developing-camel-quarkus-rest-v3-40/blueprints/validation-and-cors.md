# Validation, CORS and Security — Camel Quarkus REST 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Contents

- [Request and response validation](#request-and-response-validation)
- [CORS](#cors)
- [Security checklist](#security-checklist)

## Request and response validation

Medium confidence for the manual-backed facts (https://camel.apache.org/manual/rest-dsl-validation.html is unversioned); the response-validation default below comes from a versioned 4.22.x page.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `clientRequestValidation(true)` (off by default "to be backwards compatible"; failures 415/406/400) | Zero dependencies | Only headers, required params and body parse | Code-first |
| Add `camel-openapi-validator` (replaces the default validator, validates payloads against the spec) | Schema validation | Extra dependency; native support in Camel Quarkus (unverified) | Contract-first |

Response validation exists since Camel 4.13 (`camel.rest.clientResponseValidation`, default `false`, https://camel.apache.org/components/4.22.x/others/main.html); failures give 500. Custom error codes must be 300+.

```java
restConfiguration().bindingMode(RestBindingMode.json).clientRequestValidation(true);
```

## CORS

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `restConfiguration().enableCORS(true)`: default `false`; default headers Allow-Origin `*`, Allow-Methods `GET, HEAD, POST, PUT, DELETE, TRACE, OPTIONS, CONNECT, PATCH`, Max-Age `3600` ([binding manual](https://camel.apache.org/manual/rest-dsl-binding.html)) | Per-REST-config | Default origin `*` | Never as-is in production; override `corsHeaders` |
| `quarkus.http.cors.enabled=true` (default `false`) with explicit `quarkus.http.cors.origins` ([CORS guide](https://quarkus.io/version/3.40/guides/security-cors)) | One policy for all HTTP endpoints, regex origins | Applies to the whole server | Default choice on Quarkus |

This whole comparison, including the default origin `*` of `enableCORS(true)`, is (medium confidence): its evidence is the unversioned binding manual plus a Quarkus guide not re-fetched at the 3.40 URL. That is why it sits in Ask First and in the medium cautions, not in Never Do. The interaction of both on the same request is (unverified) (irresolvable at research time); use only the Quarkus filter as the workaround.

```properties
quarkus.http.cors.enabled=true
quarkus.http.cors.origins=https://app.example.com
```

## Security checklist

Authentication and TLS are delegated to Quarkus.

- [ ] `quarkus.http.auth.permission.<name>.paths/policy` on REST paths; the longest path wins; `@PermitAll` cannot override (https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference, medium confidence).
- [ ] `applies-to=jaxrs` targets only JAX-RS endpoints (same page, medium confidence). Path collision between Quarkus REST and Camel REST is (unverified).
- [ ] Secure the `apiContextPath` and `/q/openapi` explicitly; the need for a separate entry is (unverified).
- [ ] Keep `muteException=true` (platform-http default, https://camel.apache.org/components/4.22.x/platform-http-component.html) so stack traces are not returned.
- [ ] CORS with explicit origins only.
- [ ] `fileNameExtWhitelist` for uploads: exact, case-insensitive match since Camel 4.22.2 (https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html, medium confidence). Applies only if you upgrade past the pinned Camel 4.22.1.
- [ ] TLS for the REST server through `quarkus.http.*`. The 3.40.0 migration guide (https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html) says `quarkus.tls` settings now apply to Camel SSL contexts built from registered beans; that does not establish any default for the inbound REST server. Whether the bridging or the Quarkus TLS registry affects the inbound platform-http server is (unverified).
- OIDC: the example `platform-http-security-keycloak` exists (https://github.com/apache/camel-quarkus-examples); the OIDC configuration details are (unverified) (guide not fetched).
