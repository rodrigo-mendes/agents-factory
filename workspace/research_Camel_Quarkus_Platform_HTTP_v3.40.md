# Research: Camel Quarkus Platform HTTP v3.40 (camel-quarkus-platform-http / Camel 4.22.x / Quarkus 3.40.x)

> Every source was fetched on **2026-10-14**. The camel.apache.org and quarkus.io versioned pages show no publication date of their own. They count as current because they are the versioned 3.40.x / 4.22.x / 3.40 docs for the current stable LTS.
> Process note: this is a forked batch run that the user approved in the parent session. There was no user to approve a plan, so P3 (EnterPlanMode/ExitPlanMode) was **skipped**. P2.parallel (section-investigators) and P4 (research-synthesizer) were also not used. The agent fetched each page directly and wrote this file itself. The changelog row records this deviation.
> Tags: **[High]** = an official versioned page states it (exact URL next to it). **[Medium]** = a single source, or a page marked "Latest" rather than pinned to a version. **[UNVERIFIED]** = no official page confirmed it in this run.

## Metadata

```yaml
Full_Name: Apache Camel Quarkus — Platform HTTP extension (org.apache.camel.quarkus:camel-quarkus-platform-http)
Target_Version: 3.40.x (Camel Quarkus 3.40.x = Camel 4.22.x + Quarkus 3.40.x)
Release_Date: 2026-09-28 for Camel Quarkus 3.40.0 (reused from the pilot, which cites https://camel.apache.org/releases/; not re-fetched in this run → Medium)
Support_Status: LTS (reused from the pilot, which cites https://camel.apache.org/releases/ → Medium; the Camel Quarkus-specific LTS end date is UNVERIFIED)
Primary_Docs: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html
Component_Docs: https://camel.apache.org/components/4.22.x/platform-http-component.html
Official_Repo: https://github.com/apache/camel-quarkus
Research_Date: 2026-10-14
Domain_Complexity: Standard (HTTP server surface, security, TLS, uploads; no own crypto/auth)
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 3
Unverified_Count: 9
Irresolvable_Count: 3
Research_Quality_Score: ~84%   # (≈75 claims - 9 unverified - 3 irresolvable) / 75
```

---

## Executive Summary

`camel-quarkus-platform-http` creates HTTP consumer endpoints (`platform-http:/path`) on the Eclipse Vert.x HTTP server that `quarkus-vertx-http` provides. It has no HTTP server of its own, so port, host, body limits, upload handling and TLS all come from Quarkus `quarkus.http.*` / `quarkus.tls.*` configuration and not from Camel. [High] https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html. The extension supports JVM and native mode, both since 0.3.0 [High, same URL]. It is the HTTP transport that the Camel REST DSL uses when `camel-quarkus-rest` is added [High, same URL].

In 3.40 the extension page documents no change specific to platform-http. The 3.40.0 migration guide changes how Camel bridges `quarkus.tls` into `SSLContextParameters`: protocols, ciphers and key-exchange groups are now applied, the default is **TLSv1.3 only**, and unknown names fail. [High] https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html. **That guide does not mention platform-http or the HTTP server.** The extension page also says `SSLContextParameters` is *not supported* for platform-http, which is configured through the Quarkus SSL guide [High, extension URL]. The inference is that the 3.40 bridging change affects outbound Camel clients using a registered bean, not the inbound platform-http server, whose TLS is owned by Vert.x HTTP through `quarkus.http.tls-configuration-name`. This inference is **Medium**. No page states it explicitly.

Three critical patterns: (1) restrict methods (`httpMethodRestrict`) and upload extensions (`fileNameExtWhitelist`) on every consumer; (2) configure HTTPS through the Quarkus TLS registry plus `quarkus.http.insecure-requests`, never through `SSLContextParameters`; (3) rely on Quarkus security (permissions / bearer tokens), and read the user from `VertxPlatformHttpConstants.AUTHENTICATED_USER` in routes. The tier is **Standard**: it exposes an attack surface (uploads, headers, TLS), but authentication and cryptography are delegated to Quarkus.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**1. Declare the endpoint as `platform-http:<path>` and restrict HTTP methods**
> Confidence: 🟢 High | [✓✓ Triangulated | CQ 3.40.x extension page (2026-10-14) + Camel 4.22.x component page (2026-10-14)]
- Why: `platform-http:/hello` serves *all* methods unless `httpMethodRestrict` is set [High] https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html. URI syntax is `platform-http:path`, where `path` is required and `proxy` is the value for reverse-proxy use [High] https://camel.apache.org/components/4.22.x/platform-http-component.html.
- Code:
  ```java
  // Camel Quarkus 3.40.x / Camel 4.22.x
  from("platform-http:/orders?httpMethodRestrict=GET,POST&produces=application/json")
      .to("direct:orders");
  ```
- Endpoint defaults, all from https://camel.apache.org/components/4.22.x/platform-http-component.html [High]: `matchOnUriPrefix=false`, `muteException=true`, `populateBodyWithForm=true`, `returnHttpRequestHeaders=false`, `useBodyHandler=true`, `useCookieHandler=false`, `useStreaming=false`, `handleWriteResponseError=false`, `cookiePath=/`, `cookieSameSite=Lax`, `cookieHttpOnly=false`, `cookieSecure=false`, `bridgeErrorHandler=false`. `consumes`, `produces`, `httpMethodRestrict`, `fileNameExtWhitelist`, `requestTimeout` and `oauthProfile` have no default. The component-level `serverRequestValidation` defaults to `true` [High, same URL].
- Note: the comma-separated `GET,POST` form of `httpMethodRestrict` is **UNVERIFIED** in this run. The pages show single values only.
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html ; https://camel.apache.org/components/4.22.x/platform-http-component.html (2026-10-14)

**2. File uploads: whitelist extensions and set Quarkus body handling explicitly**
> Confidence: 🟢 High | [✓✓ Triangulated | CQ extension page + Camel component page (2026-10-14)]
- Why: the extension page shows uploads with `fileNameExtWhitelist` + `httpMethodRestrict=POST`, read through `AttachmentMessage`. It tells you to review `quarkus.http.body.handle-file-uploads`, `quarkus.http.body.uploads-directory` and `quarkus.http.body.delete-uploaded-files-on-end` [High] https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html. Since Camel 4.10, a single upload puts the file in the body and sets `CamelFileName`, `CamelFileContentType` and `CamelFileLength`. Multiple uploads set `CamelAttachmentsSize` [High] https://camel.apache.org/components/4.22.x/platform-http-component.html.
- Code:
  ```java
  // Camel Quarkus 3.40.x
  from("platform-http:/upload?httpMethodRestrict=POST&fileNameExtWhitelist=adoc,txt")
      .log("got ${header.CamelFileName} (${header.CamelFileLength} bytes)");
  ```
  ```properties
  # Quarkus 3.40 — explicit, do not rely on defaults (defaults UNVERIFIED, see Research Gaps)
  quarkus.http.body.handle-file-uploads=true
  quarkus.http.body.uploads-directory=/var/app/uploads
  quarkus.http.body.delete-uploaded-files-on-end=true
  quarkus.http.limits.max-body-size=10240K
  ```
- Limit: `quarkus.http.limits.max-body-size` defaults to `10240K` [High] https://quarkus.io/version/3.40/guides/http-reference. `max-form-attribute-size` defaults to `2048` [High, same URL]. `max-header-size` defaults to `20K` [High, same URL].
- Source: as above (2026-10-14)

**3. HTTPS through the Quarkus TLS registry, not `SSLContextParameters`**
> Confidence: 🟢 High | [✓✓ Triangulated | CQ extension page (2026-10-14) + Quarkus 3.40 HTTP reference (2026-10-14)]
- Why: the extension page says "configuring SSL with `SSLContextParameters` is not currently supported" and points to the Quarkus SSL guide [High] https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html. Quarkus recommends `quarkus.tls.*` + `quarkus.http.tls-configuration-name` [High] https://quarkus.io/version/3.40/guides/http-reference (the named configuration `https` is shown in section 3.1, per https://quarkus.io/guides/http-reference — Medium, that page is "Latest").
- Code:
  ```properties
  # Quarkus 3.40
  quarkus.tls.https.key-store.p12.path=/etc/tls/server.p12
  quarkus.tls.https.key-store.p12.password=${KEYSTORE_PASSWORD}
  quarkus.http.tls-configuration-name=https
  quarkus.http.insecure-requests=disabled   # default is 'enabled'
  ```
- Defaults: `quarkus.http.ssl-port=8443` [High] https://quarkus.io/version/3.40/guides/http-reference. `quarkus.http.insecure-requests=enabled`, with the other values being `redirect` and `disabled` [High, same URL]. The test SSL port is `8444` [Medium] https://quarkus.io/guides/http-reference ("Latest" page).
- Source: as above (2026-10-14)

**4. Secure with Quarkus security; read the identity from the documented header**
> Confidence: 🟡 Medium (one Camel source + one component statement)
- Why: Quarkus security mechanisms apply to platform-http. Inside a route, the authenticated user is in the `VertxPlatformHttpConstants.AUTHENTICATED_USER` header (`QuarkusHttpUser` → `SecurityIdentity` / `Principal`) [High] https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html. With the Vert.x engine, Bearer token validation runs *before* the body handler, so unauthenticated requests are rejected before buffering or upload [High] https://camel.apache.org/components/4.22.x/platform-http-component.html.
- Code:
  ```properties
  # Quarkus 3.40 — path-based permission (property names per Quarkus security guides; not re-fetched → Medium)
  quarkus.http.auth.permission.api.paths=/api/*
  quarkus.http.auth.permission.api.policy=authenticated
  ```
- Source: as above (2026-10-14). The `quarkus.http.auth.permission.*` names are **UNVERIFIED** in this run because the security guide was not fetched.

### ⚠️ Conditional Patterns

**A. Camel REST DSL on platform-http vs Quarkus REST (JAX-RS)**
> Confidence: 🟡 Medium
- Options: A) `rest()` DSL with `camel-quarkus-rest` (it runs on platform-http); B) a `quarkus-rest` resource calling a `ProducerTemplate`.

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | Camel-native routing, a single model | JAX-RS features | Camel-centric APIs |
  | B | JAX-RS ecosystem | Two programming models; RESTEasy error handling can interfere | An existing JAX-RS codebase |
- Agent: "Ask whether the API surface is owned by Camel routes or by an existing JAX-RS layer."
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html (the REST DSL needs `camel-quarkus-rest`; it warns that RESTEasy may register its own error handling) (2026-10-14)

**B. Streaming vs buffered bodies (`useStreaming`)**
> Confidence: 🟡 Medium
- Options: `useStreaming=false` (default, buffered) or `true` (stream; Vert.x engine only) [High] https://camel.apache.org/components/4.22.x/platform-http-component.html.

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | false | Simple re-readable body | Memory for large bodies | Normal JSON APIs |
  | true | Memory and latency on large payloads | The body is single-read | Large uploads or downloads |
- Agent: "Ask for the expected payload size."
- Note: how `useStreaming` interacts with `max-body-size` and `useBodyHandler` is UNVERIFIED.

**C. Separate management port**
> Confidence: 🟢 High
- `quarkus.management.enabled` is build-time and defaults to `false`. When enabled, the port is `9000` (test `9001`) and the root path is `/q`. Health, Micrometer and Info move to that port [High] https://quarkus.io/version/3.40/guides/management-interface-reference. It has its own TLS through `quarkus.management.tls-configuration-name`, and plain HTTP is rejected once HTTPS is configured [High, same URL].
- Agent: "Ask whether health and metrics must be unreachable from the public ingress (if yes, enable it)."

**D. Reverse proxy (`platform-http:proxy`)**
> Confidence: 🟡 Medium
- Supported only on Quarkus (`camel-platform-http-vertx`). Use `toD` with `Exchange.HTTP_HOST`. Some headers come from the absolute URL on the request line [High] https://camel.apache.org/components/4.22.x/platform-http-component.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html.
- Agent: "Ask whether an open forward proxy is really wanted. If it is, it must be locked down by auth."

**E. TLS protocol scope after 3.40** ⚠️ Migration Note
> Confidence: 🟡 Medium
- Applies to Camel **client** endpoints in the same application that use a bean bridged from `quarkus.tls` (TLSv1.3 default) [High] https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html. For legacy peers, prefer a named configuration (`quarkus.tls.legacy-endpoint.protocols=TLSv1.3,TLSv1.2`) over widening it globally [High, same URL]. Whether the bridging affects the inbound Vert.x HTTP server is UNVERIFIED (the guide is silent).

### 🚫 Forbidden Patterns

**1. Configuring platform-http HTTPS with `SSLContextParameters`**
> Severity: High
> Confidence: 🟢 High
- Why: not supported [High] https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html.
- Impact: TLS settings are silently ineffective, and the server may stay HTTP only.
- ❌ Wrong:
  ```java
  getContext().setSSLContextParameters(scp); // expecting platform-http to serve HTTPS
  ```
- ✅ Correct:
  ```properties
  quarkus.http.tls-configuration-name=https
  ```
- Source: as above (2026-10-14)

**2. Unrestricted upload endpoint**
> Severity: High
> Confidence: 🟢 High
- Why: without `httpMethodRestrict` every method is served. Without `fileNameExtWhitelist` any file type is accepted [High] https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html.
- Impact: arbitrary file types land in the uploads directory.
- ❌ Wrong:
  ```java
  from("platform-http:/upload").to("file:target/in");
  ```
- ✅ Correct:
  ```java
  from("platform-http:/upload?httpMethodRestrict=POST&fileNameExtWhitelist=pdf,txt").to("file:target/in");
  ```
- Source: as above (2026-10-14)

**3. Leaving `insecure-requests=enabled` when HTTPS is configured**
> Severity: Medium
> Confidence: 🟢 High
- Why: the default `enabled` keeps plain HTTP served alongside HTTPS [High] https://quarkus.io/version/3.40/guides/http-reference.
- ❌ Wrong:
  ```properties
  quarkus.http.tls-configuration-name=https
  ```
- ✅ Correct:
  ```properties
  quarkus.http.tls-configuration-name=https
  quarkus.http.insecure-requests=redirect
  ```
- Source: as above (2026-10-14)

**4. Turning off `muteException` in production**
> Severity: Medium
> Confidence: 🟡 Medium
- Why: `muteException` defaults to `true` [High] https://camel.apache.org/components/4.22.x/platform-http-component.html. Disabling it returns exception details to clients. That behaviour is inferred from the option name and description. Medium.
- ❌ Wrong: `platform-http:/api?muteException=false`
- ✅ Correct: keep the default and map errors with `onException(...).handled(true).setHeader(Exchange.HTTP_RESPONSE_CODE, constant(400))`.
- Source: https://camel.apache.org/components/4.22.x/platform-http-component.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html (error-handling section) (2026-10-14)

**5. Widening `quarkus.tls.protocols` globally for one legacy client**
> Severity: High
> Confidence: 🟢 High
- Why: it applies to the whole TLS configuration, and since 3.40 unknown names fail startup [High] https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html.
- ❌ Wrong:
  ```properties
  quarkus.tls.protocols=TLSv1.3,TLSv1.2,TLSv1
  ```
- ✅ Correct:
  ```properties
  quarkus.tls.legacy-endpoint.protocols=TLSv1.3,TLSv1.2
  ```
- Source: as above (2026-10-14)

---

## Migration Guide

> Confidence: 🟢 High | Sources: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html (2026-10-14) + https://camel.apache.org/components/4.22.x/platform-http-component.html (2026-10-14)

**Breaking Changes**:
- The 3.40.0 guide has no item for platform-http [High, guide URL].
- TLS registry bridging: protocols, ciphers and key-exchange groups are now applied to Camel SSL contexts from registered beans. The default is TLSv1.3 only. Unknown names fail. A configured cipher list overrides Camel's exclusion filters. `certificate-revocation-list`, `hostname-verification-algorithm`, `key-store.sni`, `alpn` and `pqc-enforcement-policy` are still not bridged [High, guide URL]. The impact on the inbound server is UNVERIFIED (Medium inference: none).
- File-upload body and headers semantics: since Camel 4.10 [High, component URL]. They are relevant if you are coming from 3.15 (Camel 4.8).

**Upgrade Steps**:
1. Set `quarkus.platform.version=3.40.1` (from the pilot: https://repo1.maven.org/maven2/io/quarkus/platform/quarkus-camel-bom/, 3.40.1 dated 2026-09-30 → Medium, not re-fetched).
2. Run `quarkus update`, then apply each CQ migration guide between your version and 3.40 (index: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/index.html — not re-fetched, Medium).
3. Re-test uploads: check the body and `CamelFileName` headers rather than relying on attachment-only access.
4. Audit the `quarkus.tls.*` names (JSSE, not OpenSSL).

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Camel | 4.22.x | 4.22.x | component docs 4.22.x |
| Quarkus | 3.40.x | 3.40.x | from the pilot; Quarkus 4 has no CQ build (Medium, pilot-derived) |
| quarkus-vertx-http | managed by the platform BOM | — | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | official extension page + component page]

**Lifecycle**:
```xml
<!-- Camel Quarkus 3.40.x — version managed by the Quarkus platform BOM -->
<dependency>
  <groupId>org.apache.camel.quarkus</groupId>
  <artifactId>camel-quarkus-platform-http</artifactId>
</dependency>
```
```java
// Camel Quarkus 3.40.x
@ApplicationScoped
public class Routes extends RouteBuilder {
  @Override public void configure() {
    onException(IllegalArgumentException.class).handled(true)
      .setHeader(Exchange.HTTP_RESPONSE_CODE, constant(400))
      .setBody(constant("{\"error\":\"bad request\"}"));

    from("platform-http:/hello?httpMethodRestrict=GET")
      .setBody(simple("Hello ${header.name}"));
  }
}
```

**Integration**: Platform HTTP ↔ camel-quarkus-rest
```java
// requires camel-quarkus-rest (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)
rest("/api").get("/items").to("direct:list").post("/items").to("direct:create");
```

**Integration**: Platform HTTP ↔ Vert.x Router (custom 404, CDI observer)
```java
// pattern named on https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html; exact code UNVERIFIED
void init(@Observes Router router) {
  router.route().last().handler(ctx -> ctx.response().setStatusCode(404).end("not found"));
}
```

**Integration**: Platform HTTP ↔ quarkus.tls — see Mandatory Pattern 3.

**Integration**: Platform HTTP ↔ camel-quarkus-core — CDI `RouteBuilder` discovery, version table and native mode are in the pilot `research_Camel_Quarkus_Core_v3.40.md` and are not duplicated here.

**Native mode**: supported since 0.3.0 [High, extension URL]. For non-default character encodings, see the charsets section of the native-mode guide [High, extension URL].

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment
./mvnw quarkus:dev
curl -i http://localhost:8080/hello?name=x        # port 8080 default UNVERIFIED in this run
curl -i -X POST http://localhost:8080/hello       # expect 405 (status code UNVERIFIED)
curl -F file=@a.txt http://localhost:8080/upload
./mvnw verify -Pnative                            # native profile name as generated by Quarkus (UNVERIFIED)
```

**Mocking**:
```java
// Camel Quarkus 3.40.x — @QuarkusTest + RestAssured hits the real platform-http endpoint
@QuarkusTest
class HelloTest {
  @Test void hello() {
    given().queryParam("name","x").get("/hello").then().statusCode(200);
  }
}
```
- Testing framework and artifact naming (camel-quarkus-junit vs junit5): see the pilot. The `quarkus.http.test-port` default (8081) is UNVERIFIED: the 3.40 HTTP reference shows only `test-port=0` (https://quarkus.io/guides/http-reference).

---

## Production Readiness

- **Performance**: buffered by default (`useStreaming=false`). Body limit `10240K` (https://quarkus.io/version/3.40/guides/http-reference).
- **Scalability**: inherits the Vert.x event loop. No platform-http-specific concurrency option is documented (UNVERIFIED beyond `requestTimeout`, https://camel.apache.org/components/4.22.x/platform-http-component.html).
- **Monitoring**: put health and metrics on the management interface on port 9000 (https://quarkus.io/version/3.40/guides/management-interface-reference).
- **Security**: TLS registry + `insecure-requests=disabled|redirect`; method and extension whitelists; bearer validation before the body handler (Vert.x); `serverRequestValidation=true` (default); `cookieSecure` and `cookieHttpOnly` default to `false`, so set them when you use cookies (https://camel.apache.org/components/4.22.x/platform-http-component.html).

---

## Reference Implementations

- Extension guide: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html
- Component reference: https://camel.apache.org/components/4.22.x/platform-http-component.html
- Integration tests in the repo: https://github.com/apache/camel-quarkus/tree/main/integration-tests/platform-http (path UNVERIFIED, not fetched)

---

## Source Bibliography

**Primary** (all fetched 2026-10-14; no page dates shown):
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html
- https://camel.apache.org/components/4.22.x/platform-http-component.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
- https://quarkus.io/version/3.40/guides/http-reference
- https://quarkus.io/version/3.40/guides/management-interface-reference
- https://quarkus.io/guides/http-reference ("Latest", Medium)
- https://quarkus.io/version/3.40/guides/all-config (fetched; the HTTP section did not render, see Research Gaps)

**Reused from the pilot (not re-fetched)**: https://camel.apache.org/releases/ ; https://repo1.maven.org/maven2/io/quarkus/platform/quarkus-camel-bom/

**Validation**: no community sources were used.

---

## Research Gaps

```
Gap: Defaults of quarkus.http.body.handle-file-uploads / uploads-directory / delete-uploaded-files-on-end / merge-form-attributes
Impact: Upload behaviour and temp-file cleanup assumed, not proven
Workaround: Set all of them explicitly (Mandatory Pattern 2)
Follow-up: https://quarkus.io/version/3.40/guides/all-config (HTTP section did not render in fetch)
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: quarkus.http.port (8080) / test-port (8081) defaults for 3.40
Impact: Low — curl examples only
Workaround: Set ports explicitly
Follow-up: same all-config page
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: Whether 3.40 TLS-registry bridging touches the inbound Vert.x HTTP server
Impact: Possible TLSv1.2 client breakage on HTTPS endpoints
Workaround: Test with `openssl s_client -tls1_2` after upgrade
Follow-up: apache/camel-quarkus 3.40.0 release notes / PR for the TLS bridging
§7-ref: Iteration 3 — IRRESOLVABLE
```
Other UNVERIFIED items (not gap-looped): the multi-value form of `httpMethodRestrict`; the `quarkus.http.auth.permission.*` names; the Router 404 code; 405 on a wrong method; the native profile name; the integration-tests path; the `useStreaming`/`max-body-size` interaction.

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 0 | Process | P3 plan approval, P2.parallel and the synthesizer were skipped (forked batch, pre-approved) | Noted | — |
| 1 | Production/Security | Management port/defaults | Resolved | https://quarkus.io/version/3.40/guides/management-interface-reference (2026-10-14) |
| 1 | Guardrails | Body limits pinned to 3.40 | Resolved | https://quarkus.io/version/3.40/guides/http-reference (2026-10-14) |
| 2 | Guardrails | quarkus.http.body.* defaults | Attempted all-config (offset 0) — section missing | https://quarkus.io/version/3.40/guides/all-config |
| 3 | Guardrails | quarkus.http.body.*, port defaults | ⚠️ IRRESOLVABLE — the all-config HTTP section is not in the fetched text | — |
| 3 | Migration | TLS bridging vs inbound server | ⚠️ IRRESOLVABLE — the guide is silent; needs source/PR review | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented
- [x] All scope areas cited (URI/options, matching, headers, uploads, security, management/ports, TLS, errors, native, testing)
- [x] Pattern counts driven by domain needs
- [x] Every anti-pattern has alternative
- [x] All CLI commands marked as representative
- [x] Integration examples complete (rest, Vert.x Router, quarkus.tls, core by reference)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns triangulated (3) or downgraded (1)
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score calculated
- [x] Every Research Gap cross-referenced

---

## Agent Operation Notes

- **High Confidence**: Mandatory Patterns 1–3, Forbidden 1–3 and 5, endpoint option defaults, body/header limits, management defaults.
- **Medium Confidence**: security identity handling, streaming, reverse proxy, REST DSL vs JAX-RS, "the 3.40 TLS change does not affect the inbound server", values reused from the pilot (release date, LTS, BOM 3.40.1).
- **Low Confidence (ask a human)**: the 3 IRRESOLVABLE items above.
- **Edge Cases**: 3.40.0 was released about 16 days before this research (<30 days), so documentation may still change.
- **Emergency Stop**: not triggered.
