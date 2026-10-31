---
name: developing-camel-quarkus-platform-http-v3-40
description: "Guides Camel Quarkus 3.40.x platform-http (Camel 4.22, Quarkus 3.40 LTS): endpoints, uploads, TLS, security. Use when a route uses platform-http: or camel-quarkus-platform-http 3.40. Not for Quarkus 4, older Camel Quarkus lines or Spring Boot."
---

# Developing with Camel Quarkus Platform HTTP 3.40.x

> Version lock: every claim applies to **camel-quarkus-platform-http 3.40.x** only. Research date **2026-10-14**.
> Claims tagged unverified or medium confidence were not fully confirmed against an official page; treat them as hypotheses.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| Extension | `org.apache.camel.quarkus:camel-quarkus-platform-http`; JVM and native mode, both since 0.3.0 | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html |
| Camel component docs | 4.22.x | https://camel.apache.org/components/4.22.x/platform-http-component.html |
| Camel Quarkus | 3.40.x; 3.40.0 released 2026-09-28, marked LTS (High; no LTS-until date is given) | https://camel.apache.org/releases/ |
| Bundled versions | Camel 4.22.1, Quarkus 3.40.1, GraalVM 25.0.4.1 (High) | https://camel.apache.org/camel-quarkus/latest/ |
| Quarkus HTTP layer | `quarkus-vertx-http` (Vert.x), managed by the platform BOM; docs pinned to 3.40 | https://quarkus.io/version/3.40/guides/http-reference |
| Platform BOM | `quarkus.platform.version` 3.40.1, dated 2026-09-30 (medium confidence: reused, not re-fetched) | https://repo1.maven.org/maven2/io/quarkus/platform/quarkus-camel-bom/ |
| Java | 17 and 21 (High) | https://camel.apache.org/releases/q-3.40.0/ |
| Maven requirement | not covered by this research (unverified) | page not recorded |

**Version-lifetime risk** (as of 2026-10-14; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is planned for the end of November and Java 21 is the new base (High, https://quarkus.io/blog/quarkus-4-0-0-beta1-released/). No Camel Quarkus build on Quarkus 4 is known; the Beta1 post does not mention Camel Quarkus (medium confidence, absence of evidence).
- Quarkus 3.40 was released 2026-09-30 as an LTS, community-maintained until 2027-09-30 (High, https://quarkus.io/releases). The Camel Quarkus-specific end date is not published (unverified); reusing the Quarkus date is an inference.
- 3.40.0 was released on 2026-09-28 (High, see Version Context), so documentation may still change.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [File uploads](./blueprints/file-uploads.md)
- [TLS and security](./blueprints/tls-and-security.md)
- [Migration guide to 3.40](./blueprints/migration-guide.md)
- [Integration examples, testing, management port](./blueprints/integration-examples.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Restrict HTTP methods on every consumer** with `httpMethodRestrict`. Without it `platform-http:/hello` serves all methods ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)). See [patterns](./blueprints/always-do-patterns.md#1-declare-the-endpoint-and-restrict-methods).
- **Whitelist upload extensions** with `fileNameExtWhitelist`; it has no default ([component page](https://camel.apache.org/components/4.22.x/platform-http-component.html)). See [file uploads](./blueprints/file-uploads.md).
- **Serve HTTPS through the Quarkus TLS registry** (`quarkus.tls.*` + `quarkus.http.tls-configuration-name`) ([HTTP reference](https://quarkus.io/version/3.40/guides/http-reference)). See [TLS and security](./blueprints/tls-and-security.md).
- **Set `quarkus.http.insecure-requests` to `redirect` or `disabled` once HTTPS is configured** ([HTTP reference](https://quarkus.io/version/3.40/guides/http-reference)). See [patterns](./blueprints/always-do-patterns.md#4-close-plain-http-when-https-is-configured).
- **Read the authenticated user from the `VertxPlatformHttpConstants.AUTHENTICATED_USER` header** inside routes ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)). See [patterns](./blueprints/always-do-patterns.md#5-read-the-authenticated-identity-from-the-documented-header).
- **Write routes without `@ApplicationScoped` unless they use `@Inject` or `@ConfigProperty`** ([CDI guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html)).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| HTTP surface | `rest()` DSL on platform-http (needs `camel-quarkus-rest`) vs a Quarkus REST resource calling a `ProducerTemplate` (medium confidence: [official example](https://github.com/apache/camel-quarkus-examples), `quarkus-rest-json`, main branch, which uses neither platform-http nor `camel-quarkus-rest`, so no official source shows both on one server; RESTEasy may register its own error handling) | "Is the API owned by Camel routes or by an existing JAX-RS layer?" |
| Multiple methods | `httpMethodRestrict` with several values (`GET,POST`) is (unverified); use one endpoint per method | "Which methods must this path serve?" |
| Body limits | set `quarkus.http.body.*` and `quarkus.http.limits.max-body-size` explicitly; the `body.*` defaults are (unverified), see [file uploads](./blueprints/file-uploads.md#quarkus-body-properties) | "What upload size and temp-file policy do you need?" |
| Body handling | `useStreaming=false` (default, buffered) vs `true` (Vert.x engine only); single-read body (medium confidence). Interaction with `max-body-size` and `useBodyHandler` is (unverified). | "What is the expected payload size?" |
| Management port | `quarkus.management.enabled` (build time, default `false`) moves health and metrics to port 9000 ([source](https://quarkus.io/version/3.40/guides/management-interface-reference)) | "Must health and metrics be unreachable from the public ingress?" |
| Reverse proxy | `platform-http:proxy` is Quarkus-only (medium confidence); it is an open forward proxy unless locked down by auth | "Is a forward proxy really wanted? Who may call it?" |
| Exception detail | `muteException=true` is the default ([component page](https://camel.apache.org/components/4.22.x/platform-http-component.html)). That `false` leaks exception details is inferred (medium confidence). | "Do callers need error bodies? Map them with `onException` instead." |
| Path permissions | `quarkus.http.auth.permission.*` property names are (unverified) (security guide not fetched) | "Which Quarkus security guide version should I confirm against?" |
| Legacy TLS peer | named `quarkus.tls.<name>` configuration with TLSv1.2 vs global `quarkus.tls.protocols` widening (unknown protocol names fail since 3.40, per the [migration guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)); the inbound-server impact of the 3.40 bridging is (unverified), see [TLS](./blueprints/tls-and-security.md#does-the-340-bridging-affect-the-inbound-server) | "Which clients lack TLS 1.3?" |
| `quarkus.http.root-path` | Effect on Camel `platform-http` routes is (unverified) | "Is a non-default root path set? Test the real URLs." |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Call `setSSLContextParameters(...)` expecting platform-http to serve HTTPS ([source](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)). | Configure a Quarkus TLS registry entry and point `quarkus.http.tls-configuration-name` at it ([HTTP reference](https://quarkus.io/version/3.40/guides/http-reference)). |
| Expose `from("platform-http:/upload")` with no method restriction and no extension whitelist; any method and file type is accepted ([source](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)). | `httpMethodRestrict=POST&fileNameExtWhitelist=pdf` (one value each). |
| Configure HTTPS and leave `insecure-requests` at its default `enabled` ([source](https://quarkus.io/version/3.40/guides/http-reference)). | `quarkus.http.insecure-requests=redirect` (or `disabled`). |
| Add `@ApplicationScoped` to a route that injects nothing; it adds boot-time cost ([CDI guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html)). | Plain `extends RouteBuilder`; it is discovered automatically. |
Full ❌/✅ examples: [never-do patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| URI syntax | `platform-http:path` (`path` required; `proxy` for reverse-proxy use) | https://camel.apache.org/components/4.22.x/platform-http-component.html |
| Endpoint defaults | `matchOnUriPrefix=false`, `muteException=true`, `populateBodyWithForm=true`, `returnHttpRequestHeaders=false`, `useBodyHandler=true`, `useCookieHandler=false`, `useStreaming=false`, `handleWriteResponseError=false`, `bridgeErrorHandler=false` | https://camel.apache.org/components/4.22.x/platform-http-component.html |
| Cookie defaults | `cookiePath=/`, `cookieSameSite=Lax`, `cookieHttpOnly=false`, `cookieSecure=false` | https://camel.apache.org/components/4.22.x/platform-http-component.html |
| No default | `consumes`, `produces`, `httpMethodRestrict`, `fileNameExtWhitelist`, `requestTimeout`, `oauthProfile` | https://camel.apache.org/components/4.22.x/platform-http-component.html |
| Component option | `serverRequestValidation` defaults to `true` | https://camel.apache.org/components/4.22.x/platform-http-component.html |
| Upload headers (since Camel 4.10) | one file: body + `CamelFileName`, `CamelFileContentType`, `CamelFileLength`; several: `CamelAttachmentsSize` | https://camel.apache.org/components/4.22.x/platform-http-component.html |
| Body limit | `quarkus.http.limits.max-body-size=10240K` | https://quarkus.io/version/3.40/guides/http-reference |
| Form and header limits | `max-form-attribute-size=2048`, `max-header-size=20K` | https://quarkus.io/version/3.40/guides/http-reference |
| HTTPS port | `quarkus.http.ssl-port=8443` | https://quarkus.io/version/3.40/guides/http-reference |
| Insecure requests | `enabled` (default), `redirect`, `disabled` | https://quarkus.io/version/3.40/guides/http-reference |
| Test SSL port | 8444 (medium confidence: "Latest" page, not pinned) | https://quarkus.io/guides/http-reference |
| Management interface | build-time, default `false`; when on: port 9000, test port 9001, root `/q` | https://quarkus.io/version/3.40/guides/management-interface-reference |
| Management TLS | `quarkus.management.tls-configuration-name`; plain HTTP rejected once HTTPS is configured | https://quarkus.io/version/3.40/guides/management-interface-reference |
| Bridged TLS default | TLSv1.3 only on Camel SSL contexts built from registered beans; inbound-server impact (unverified) | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html |
| HTTP port 8080, test port 8081 | (unverified) (all-config page did not render) | page not recorded |
| `quarkus.http.body.*` defaults | (unverified); set them explicitly | page not recorded |
| `httpMethodRestrict` with several values | comma-separated form (unverified); use one method per endpoint | page not recorded |

## External Resources

All fetched 2026-10-14 (shared version facts by the orchestrator, see the register). camel.apache.org and quarkus.io versioned pages show no page date and are the current stable docs.

- Extension page: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html
- Component page: https://camel.apache.org/components/4.22.x/platform-http-component.html
- Migration guide 3.40.0: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
- Quarkus 3.40 HTTP reference: https://quarkus.io/version/3.40/guides/http-reference
- Quarkus 3.40 management interface: https://quarkus.io/version/3.40/guides/management-interface-reference
- CDI guide (verified by the orchestrator 2026-10-14): https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
