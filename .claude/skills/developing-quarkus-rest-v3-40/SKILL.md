---
name: developing-quarkus-rest-v3-40
description: "Guides Quarkus 3.40.x REST: quarkus-rest, quarkus-rest-jackson and quarkus-rest-client (threading, client config, TLS, errors, security). Use when writing Jakarta REST resources or REST clients. Not for Quarkus 4, other versions or the Camel REST DSL."
---

# Developing with Quarkus REST 3.40.x

> Version lock: every claim applies to **Quarkus 3.40.x** (latest patch 3.40.1.1; Camel Quarkus 3.40.x pairs with 3.40.1) only. Research date **2026-10-14**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official versioned page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> The Camel REST DSL (`camel-quarkus-rest`) belongs to the sibling skill `developing-camel-quarkus-rest-v3-40`.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| Quarkus | 3.40 released 2026-09-30 as LTS, community-maintained until 2027-09-30 | https://quarkus.io/releases |
| Quarkus REST | `quarkus-rest` is the Jakarta REST server, successor of RESTEasy Reactive (medium confidence, L5) | https://quarkus.io/version/3.40/guides/rest |
| Quarkus latest patch | 3.40.1.1 (2026-10-19) | https://quarkus.io/releases (read 2026-10-28) |
| Camel Quarkus pairing | Camel Quarkus 3.40.x uses Camel 4.22.1 and Quarkus 3.40.1 (the pairing statement of that page, not the latest Quarkus patch) | https://camel.apache.org/camel-quarkus/latest/ |
| Java | 17 and 21 (Camel Quarkus 3.40, High); the Quarkus 3.40 minimum is not recorded (unverified, U8); virtual threads (`@RunOnVirtualThread`) need Java 21+ | https://camel.apache.org/releases/q-3.40.0/ ; https://quarkus.io/version/3.40/guides/virtual-threads |
| Jackson | 2.x in 3.40 and its exact version (unverified) | page not recorded |

**Version-lifetime risk** (as of 2026-10-14; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; Java 21 becomes the base ([source](https://quarkus.io/blog/quarkus-4-0-0-beta1-released/)). No Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence). Pin 3.40.x.
- Quarkus 4 preview details (Jackson 3, renamed customizer, RESTEasy 7) come from a migration wiki (medium confidence) and are NOT for 3.40: [preview](./blueprints/migration-quarkus-4-preview.md).
- The Camel Quarkus-specific support end date for 3.40 is not published (unverified).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference) | [Verification Loop](#verification-loop)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Server resources, errors, JSON, OpenAPI](./blueprints/server-resources.md)
- [REST client](./blueprints/rest-client.md)
- [Security, CORS and TLS](./blueprints/security-and-tls.md)
- Camel with Quarkus REST (ProducerTemplate, REST DSL, shared server): see `developing-camel-quarkus-rest-v3-40` (Quarkus + Camel package)
- [Migration and Quarkus 4 preview](./blueprints/migration-quarkus-4-preview.md)
- [Unverified and irresolvable register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `quarkus-rest-client` for clients.** The 3.40 guide says `quarkus-resteasy-client` "may not be used with Quarkus REST" ([rest guide](https://quarkus.io/version/3.40/guides/rest)). See [patterns](./blueprints/always-do-patterns.md#1-server-and-client-artifacts).
- **Expect `Uni`, `Multi`, `CompletionStage` and `Publisher` endpoints on the IO thread.** They run there by default ([rest guide](https://quarkus.io/version/3.40/guides/rest)). See [patterns](./blueprints/always-do-patterns.md#2-thread-by-signature).
- **Expect every other endpoint signature to be blocking.** It runs on a worker thread ([rest guide](https://quarkus.io/version/3.40/guides/rest)). See [patterns](./blueprints/always-do-patterns.md#2-thread-by-signature).
- **Put `@RunOnVirtualThread` only on blocking endpoints.** It "can only be used on endpoints annotated with @Blocking or considered blocking because of their signature" ([virtual-threads guide](https://quarkus.io/version/3.40/guides/virtual-threads)). See [patterns](./blueprints/always-do-patterns.md#3-virtual-threads).
- **Use `@RunOnVirtualThread` only on Java 21+.** The feature needs Java 21 or later ([virtual-threads guide](https://quarkus.io/version/3.40/guides/virtual-threads)). See [patterns](./blueprints/always-do-patterns.md#3-virtual-threads).
- **Set the base URL of every REST client under a `configKey`.** "Setting the base URL of the client is mandatory" ([rest-client guide](https://quarkus.io/version/3.40/guides/rest-client)). See [patterns](./blueprints/always-do-patterns.md#4-client-url-and-config-key).
- **Select client TLS with `tls-configuration-name`.** It points to a named `quarkus.tls.<name>` bucket ([rest-client guide](https://quarkus.io/version/3.40/guides/rest-client)). See [patterns](./blueprints/always-do-patterns.md#5-named-tls-bucket).
- **Expect an error when the named TLS bucket is missing.** The client throws it ([rest-client guide](https://quarkus.io/version/3.40/guides/rest-client)). See [patterns](./blueprints/always-do-patterns.md#5-named-tls-bucket).
- **Validate request bodies with `@Valid` and `quarkus-hibernate-validator`.** Constraint failures on endpoint parameters return 400 with a violations report ([validation guide](https://quarkus.io/version/3.40/guides/validation)). See [patterns](./blueprints/always-do-patterns.md#6-validation).
- **Return `RestResponse<T>` instead of a raw `Response` when native mode matters.** The type can then be inferred at build time ([rest-json guide](https://quarkus.io/version/3.40/guides/rest-json)). See [patterns](./blueprints/always-do-patterns.md#7-restresponse-for-native).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Endpoint threading | Blocking signature (worker) vs `Uni`/`Multi` (IO thread, never block) vs `@RunOnVirtualThread` (Java 21+, pinning risk on Java 21-23 (medium confidence), I/O-bound only) ([rest](https://quarkus.io/version/3.40/guides/rest), [virtual threads](https://quarkus.io/version/3.40/guides/virtual-threads)) | "Which Java version, and are the downstream calls blocking (JDBC, ProducerTemplate)?" |
| Client return style | Blocking vs `Uni` (each subscription re-sends, so `onFailure().retry().atMost(n)` works) vs `CompletionStage` (retry needs a new call) ([rest-client](https://quarkus.io/version/3.40/guides/rest-client)) | "From which thread is the client called?" |
| JSON customization | `ObjectMapperCustomizer` CDI bean ("simplest (and suggested)") vs own `ObjectMapper` (you reapply defaults) vs `@JsonView` or `@CustomSerialization` per method ([rest-json](https://quarkus.io/version/3.40/guides/rest-json)) | "Global or per-endpoint customization?" |
| Client timeouts | Global defaults are 15000 ms connect and 30000 ms read ([rest-client](https://quarkus.io/version/3.40/guides/rest-client)); that per-client keys inherit them is (unverified) | "Set explicit per-client timeouts?" Default: yes |
| Exception mapping (medium confidence) | Quarkus REST does not log exceptions by default; an `@ServerExceptionMapper` in a resource class applies only to that class ([rest](https://quarkus.io/version/3.40/guides/rest)). Default: global mappers outside resource classes, logging yourself | "Global or per-resource mapping?" |
| Client hostname verification (medium confidence, L3) | Keep `verify-host` on; the rest-client guide says it "should not be disabled in production as it makes the client vulnerable to MITM attacks"; the exact key path is not recorded ([rest-client](https://quarkus.io/version/3.40/guides/rest-client)) | "Does a client need hostname verification off, and in which environment?" |
| CORS (medium confidence) | Off by default; unset origins allow same-origin only; `origins=*` in production "poses severe security risks" ([security-cors](https://quarkus.io/version/3.40/guides/security-cors)). Default: explicit origin list | "Which origins are allowed in production?" |
| Deny-by-default (medium confidence) | `quarkus.security.jaxrs.deny-unannotated-endpoints` defaults to `false`; HTTP permissions run before annotations, so `@PermitAll` cannot override them ([reference](https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference)) | "Should unannotated endpoints be denied?" |
| Swagger UI (medium confidence) | Dev/test only by default vs `quarkus.swagger-ui.always-include=true` ([openapi-swaggerui](https://quarkus.io/version/3.40/guides/openapi-swaggerui)) | "Is the UI needed in production?" |
| Resource + ProducerTemplate vs Camel REST DSL (medium confidence; also in the Camel REST register, M15) | The pattern is published only on the examples main branch; no official source shows both stacks on one server (see skill `developing-camel-quarkus-rest-v3-40`, Quarkus + Camel package). Separate path prefixes if both are present | "Do endpoints need Quarkus REST features (validation, annotations, typed responses)?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Block inside an endpoint that returns `Uni`/`Multi`; it runs on the IO thread ([rest](https://quarkus.io/version/3.40/guides/rest)) | Use a blocking signature so the call runs on a worker thread ([rest](https://quarkus.io/version/3.40/guides/rest)) |
| Combine `quarkus-rest` with `quarkus-resteasy-client` ([rest](https://quarkus.io/version/3.40/guides/rest)) | Use `quarkus-rest-client` ([rest](https://quarkus.io/version/3.40/guides/rest)) |
| Use `trust-all` in production; the guides say "should not be used in production" ([rest-client](https://quarkus.io/version/3.40/guides/rest-client), [tls-registry](https://quarkus.io/version/3.40/guides/tls-registry-reference)) | Use a named bucket with `trust-store.pem.certs` ([tls-registry](https://quarkus.io/version/3.40/guides/tls-registry-reference)) |
| Return a raw `Response` whose entity type is not visible at build time in native mode; no exception is thrown ([rest-json](https://quarkus.io/version/3.40/guides/rest-json)) | Return `RestResponse<T>` ([rest-json](https://quarkus.io/version/3.40/guides/rest-json)) |
| Set `quarkus.rest-client.logging.masked-headers` without `Authorization,Cookie`; the property replaces the defaults ([rest-client](https://quarkus.io/version/3.40/guides/rest-client)) | List `Authorization,Cookie` plus your extra headers ([rest-client](https://quarkus.io/version/3.40/guides/rest-client)) |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Client `connect-timeout` / `read-timeout` (global) | 15000 ms / 30000 ms | https://quarkus.io/version/3.40/guides/rest-client |
| Client `connection-pool-size`, `connection-ttl`, `http2` | 50, 60000, `false`; `keep-alive-enabled` `true` | https://quarkus.io/version/3.40/guides/rest-client |
| Client logging | `quarkus.rest-client.logging.scope=request-response\|all`; `body-limit` 100; masked headers `Authorization, Cookie` | https://quarkus.io/version/3.40/guides/rest-client |
| Deprecated client settings | `proxy-address`, `proxy-user`, `proxy-password`, `non-proxy-hosts`, `proxy-connect-timeout`, `multipart.max-chunk-size`; use `proxy-configuration-name` | https://quarkus.io/version/3.40/guides/rest-client |
| TLS default (medium confidence, L1) | TLSv1.3 | https://quarkus.io/version/3.40/guides/tls-registry-reference |
| Server TLS | `quarkus.http.tls-configuration-name=<name>` | https://quarkus.io/version/3.40/guides/tls-registry-reference |
| `quarkus.rest.*` defaults (medium confidence, L5) | `fail-on-duplicate` true, `removes-trailing-slash` true, `default-produces` true, `input-buffer-size` 10k, `output-buffer-size` 8191 | https://quarkus.io/version/3.40/guides/rest |
| HTTP response compression | off by default | https://quarkus.io/version/3.40/guides/rest |
| Pre-matching filters | always run on an event-loop thread | https://quarkus.io/version/3.40/guides/rest |
| CORS (medium confidence) | `quarkus.http.cors.enabled=false` default | https://quarkus.io/version/3.40/guides/security-cors |
| Proactive authentication (medium confidence) | on by default; off plus `SecurityIdentity` on the IO thread raises `BlockingOperationNotAllowedException` | https://quarkus.io/version/3.40/guides/security-proactive-authentication |
| OpenAPI (medium confidence) | `/q/openapi`, UI `/q/swagger-ui`, OpenAPI 3.1.0 default, artifact `quarkus-smallrye-openapi` | https://quarkus.io/version/3.40/guides/openapi-swaggerui |
| Test port (medium confidence, L2) | `quarkus.http.test-port` 8081 (page read to 100k chars, no verbatim quote recorded) | https://quarkus.io/version/3.40/guides/getting-started-testing |
| Test artifact | `quarkus-junit` (skill `developing-quarkus-junit-v3-40`); Camel routes: skill `developing-camel-quarkus-junit-v3-40` | https://quarkus.io/version/3.40/guides/getting-started-testing ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html |
| Coverage limits (partial reads) | the tls-registry-reference page (first 100k chars, L1), the rest-client header section (L3) and the rest guide (L5) were read only partly; claims on those pages may be incomplete | https://quarkus.io/version/3.40/guides/tls-registry-reference ; https://quarkus.io/version/3.40/guides/rest-client ; https://quarkus.io/version/3.40/guides/rest |
| Representative commands | `./mvnw quarkus:dev`, `./mvnw test`, `./mvnw install -Dnative` | https://quarkus.io/version/3.40/guides/rest-client (native); others page not recorded |

## Verification Loop

Self-check after writing or changing resources or clients (commands as in Quick Reference, "Representative commands"):

```bash
./mvnw test                  # @QuarkusTest suites pass (port 8081 by default: medium confidence, L2)
./mvnw quarkus:dev           # dev mode starts with the resources and clients configured
./mvnw install -Dnative      # only if native mode matters (RestResponse<T> returns)
```

## External Resources

All fetched 2026-10-14.

- Quarkus REST: https://quarkus.io/version/3.40/guides/rest
- REST client: https://quarkus.io/version/3.40/guides/rest-client
- Writing JSON REST services: https://quarkus.io/version/3.40/guides/rest-json
- Virtual threads: https://quarkus.io/version/3.40/guides/virtual-threads
- TLS registry reference: https://quarkus.io/version/3.40/guides/tls-registry-reference
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
