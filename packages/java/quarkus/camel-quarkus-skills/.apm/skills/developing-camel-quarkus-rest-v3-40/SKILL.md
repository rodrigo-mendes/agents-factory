---
name: developing-camel-quarkus-rest-v3-40
description: "Guides camel-quarkus-rest (REST DSL) on Camel Quarkus 3.40.x (Camel 4.22): JSON binding, contract-first and code-first OpenAPI, validation, CORS. Use when building rest() endpoints in Camel Quarkus 3.40. Not for Quarkus 4, JAX-RS-only apps or core setup."
---

# Developing REST APIs with Camel Quarkus REST 3.40.x

> Version lock: every claim applies to Camel Quarkus 3.40.x (`camel-quarkus-rest` + REST DSL) only. Research date 2026-10-14.
> Untagged claims are High (versioned official page, cited inline). Only `(medium confidence)` and `(unverified)` are tagged; they are hypotheses, see the [tag to register mapping](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Always Do and Never Do hold only High claims. Core topics (BOM import, route discovery, CDI beans, native basics, TLS registry) live in the `developing-camel-quarkus-core-v3-40` skill.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| Camel Quarkus | 3.40.0 released 2026-09-28, LTS (no LTS-until date given) | https://camel.apache.org/releases/ |
| Camel, Quarkus, GraalVM | Camel 4.22.1, Quarkus 3.40.1, GraalVM 25.0.4.1 | https://camel.apache.org/camel-quarkus/latest/ |
| Java | 17 and 21 ("This version supports Java 17 and 21"); Java 25 for Camel Quarkus is (unverified). This page is cited for Java only, not for the release date or the Camel version | https://camel.apache.org/releases/q-3.40.0/ |
| `camel-quarkus-rest` | JVM and native since 0.0.1; depends on `camel-quarkus-platform-http` and configures it as REST transport | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest.html |
| REST DSL manual pages | Unversioned ("latest"); treated as 4.22.x docs, so every claim from them is (medium confidence) | https://camel.apache.org/manual/rest-dsl.html |

**Version-lifetime risk** (as of 2026-10-14; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30 (https://quarkus.io/releases). The Camel Quarkus-specific support end date is not published (unverified); applying the Quarkus date to Camel Quarkus is an inference.
- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; Java 21 becomes the base version (https://quarkus.io/blog/quarkus-4-0-0-beta1-released/). Jackson 3 affecting JSON binding is (unverified): it is not in the family facts, research only.
- No Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence); the Beta1 post does not mention Camel Quarkus.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [REST DSL configuration, binding, params, errors](./blueprints/rest-dsl-configuration.md)
- [OpenAPI: contract-first and code-first](./blueprints/openapi-contract-first.md)
- [Validation, CORS and security](./blueprints/validation-and-cors.md)
- [Migration guide 3.15 to 3.40](./blueprints/migration-guide.md)
- [Integration examples and testing](./blueprints/integration-examples.md)
- [Quarkus REST integration: resource + ProducerTemplate, shared server](./blueprints/quarkus-rest-integration.md)
- [Unverified and irresolvable register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Rely on platform-http as the REST transport**: `camel-quarkus-rest` depends on it and configures it as REST transport ([rest extension](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest.html)). See [patterns](./blueprints/always-do-patterns.md#1-dependencies).
- **Set `bindingMode` explicitly** (for example `restConfiguration().bindingMode(RestBindingMode.json)`): it defaults to `off` ([main options 4.22.x](https://camel.apache.org/components/4.22.x/others/main.html)). See [patterns](./blueprints/always-do-patterns.md#2-json-binding).
- **Configure the HTTP server through `quarkus.http.*`**, not through Camel: "Configuration of the platform HTTP server is managed by Quarkus" ([platform-http extension](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)). See [patterns](./blueprints/always-do-patterns.md#5-server-settings-belong-to-quarkus).

Status codes and `onException` mapping (200/204/500 defaults, custom error codes 300+) rest only on unversioned manual pages, so they are (medium confidence) and live in [patterns](./blueprints/always-do-patterns.md#3-status-codes-and-errors) and the Quick Reference, not here.

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Dependencies beyond the transport | Add `camel-quarkus-jackson` (binding data format) and `camel-quarkus-direct` as the official example does (medium confidence: example pom on the `main` branch, not the 3.40.x tag). | "Which data format and endpoints do the routes use?" |
| `type` / `outType` on verbs | The example uses `type`; `outType` follows the binding manual example (medium confidence: unversioned manual, `main` branch example). | "Should request and response be bound to POJOs?" |
| Contract-first routes | One `direct:<operationId>` route per operation; a missing route fails startup, since Camel 4.6 (medium confidence: unversioned [OpenAPI manual](https://camel.apache.org/manual/rest-dsl-openapi.html)). `missingOperation` defaults to `fail` ([rest-openapi component 4.22.x](https://camel.apache.org/components/4.22.x/rest-openapi-component.html)). See [patterns](./blueprints/always-do-patterns.md#4-contract-first-routes). | "Is there an authoritative OpenAPI document?" |
| Contract-first vs code-first | `rest().openApi()` (governance, generated models; spec must ship in native (medium confidence)) vs REST DSL + `camel-quarkus-openapi-java` (fast iteration; spec derived). See [OpenAPI](./blueprints/openapi-contract-first.md). | "Is there an authoritative OpenAPI document?" If yes, contract-first. |
| Where to publish the spec | `camel.rest.apiContextPath` (example value `/api-doc`) vs merging into Quarkus `/q/openapi` with `quarkus.camel.openapi.expose.enabled=true` (medium confidence). Whether the doc path needs its own permission entry is (unverified). | "Do Quarkus REST (JAX-RS) endpoints coexist with Camel REST?" |
| Resource + `ProducerTemplate` vs REST DSL (medium confidence, M15: the example is on the `main` branch, not the 3.40.x tag) | Quarkus REST resource that injects `ProducerTemplate` and calls a `direct:` route (validation, security annotations, OpenAPI from Jakarta annotations, typed responses; two layers) vs Camel REST DSL on platform-http (everything in routes; Quarkus REST filters and `@ServerExceptionMapper` do not apply). Details and the shared-server limits: [Quarkus REST integration](./blueprints/quarkus-rest-integration.md#choosing-between-resource-and-rest-dsl). | "Rich API contract with Quarkus REST features and Camel only for integration logic, or pure integration endpoints?" |
| Request validation | `clientRequestValidation(true)` (headers, required params, body parse; medium confidence) vs adding `camel-openapi-validator` (schema validation; native support (unverified)). See [validation](./blueprints/validation-and-cors.md). | "Is schema-level validation required?" |
| CORS (medium confidence: unversioned binding manual) | Quarkus filter (`quarkus.http.cors.*`, explicit origins) vs Camel `enableCORS(true)`, whose default headers allow every origin (`*`); do not ship that default to production. Interplay of both on one request is (unverified). | "Which origins may call the API?" Default to the Quarkus filter. |
| Reuse the Quarkus `ObjectMapper` | `dataFormatProperty("autoDiscoverObjectMapper", "true")` vs the Camel-owned mapper that ignores `ObjectMapperCustomizer` beans ([jackson extension](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jackson.html)). | "Do you customize the Quarkus ObjectMapper?" |
| Native registration (medium confidence) | `@RegisterForReflection` on model classes and `quarkus.native.resources.includes` for contract files. | "Is native mode a target?" |
| Default base path `/` (medium confidence) | Contract-first without a base path may hide other endpoints; set `restConfiguration().contextPath("/api")`. Whether it overrides the contract path is (unverified). | "What base path should the API use?" |
| Alternate transport | Keep platform-http vs `camel-quarkus-servlet` + `restConfiguration().component("servlet")` ([rest extension](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest.html)). | "Do you need Servlet-container semantics?" Otherwise keep platform-http. |
| Payload mapping (medium confidence) | `camel-atlasmap` was removed in Camel 4.0 (search summary of the migration guide); do not recommend it. Bind to POJOs and map in a bean. | "Which mapping approach does the team use?" |
| Test artifact | Only `camel-quarkus-junit` is documented in the 3.40 testing guide ([testing guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html)); Camel test style lives in `developing-camel-quarkus-junit-v3-40`. REST tests use `quarkus-junit` + `rest-assured` (medium confidence, example pom on `main`); `camel-quarkus-junit` is needed only for `CamelQuarkusTestSupport` (medium confidence). | "Do tests need CamelQuarkusTestSupport?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Configure TLS on the REST server with `SSLContextParameters` or `restConfiguration()`: "configuring the server for SSL with `SSLContextParameters` is not currently supported" ([platform-http](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)). | Configure the server through `quarkus.http.*` (same page: "managed by Quarkus"). |
| Use hyphens or `$` in path parameter names (`/{order-id}`): Vert.x rejects them unless `io.vertx.web.route.param.extended-pattern=true` is set ([rest extension](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest.html)). | Name it `{orderId}`. |
| Add `camel-quarkus-junit5` or import `org.apache.camel.test.junit5`: renamed to `camel-quarkus-junit` in 3.31, imports moved to `org.apache.camel.test.junit6` ([3.31.0 migration guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html)). See `developing-camel-quarkus-junit-v3-40`. | Use `camel-quarkus-junit` ([testing guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html)). |

Cautions at (medium confidence) or (unverified) level (AtlasMap, default base path, CDI injection inside `configure()`, REST in `LambdaRouteBuilder`, Camel `enableCORS(true)` with default origin `*`, the TLS registry for the inbound server, the runtime result of `SSLContextParameters`) are in [never-do patterns](./blueprints/never-do-patterns.md#medium-confidence-cautions). Code samples in this skill use plain `extends RouteBuilder`; `@ApplicationScoped` is needed only for `@Inject`/`@ConfigProperty` ([CDI guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html)).

## Quick Reference

Rows citing unversioned `/manual/` pages or non-fetched pinned Quarkus URLs are (medium confidence).

| Aspect | Value | Source |
|---|---|---|
| `bindingMode` | Default `off`; values `off`, `auto`, `json`, `xml`, `json_xml`; JSON uses Jackson (medium confidence) | https://camel.apache.org/components/4.22.x/others/main.html ; https://camel.apache.org/manual/rest-dsl-binding.html |
| `skipBindingOnErrorCode` | Default `true` (medium confidence) | https://camel.apache.org/manual/rest-dsl-binding.html |
| `inlineRoutes` | Default `true` since Camel 4.5; inlining needs 1:1 unique `direct:` endpoints (medium confidence) | https://camel.apache.org/manual/rest-dsl.html |
| Response codes | 200 default, 204 without body, 500 on unhandled exception; `{sku}` arrives as header `sku`; custom error codes 300+ (medium confidence) | https://camel.apache.org/manual/rest-dsl.html ; https://camel.apache.org/manual/rest-dsl-validation.html |
| `clientRequestValidation` | Default off (backwards compatibility); failures 415/406/400 (medium confidence) | https://camel.apache.org/manual/rest-dsl-validation.html |
| `clientResponseValidation` | Default `false`, since Camel 4.13; failure gives 500 | https://camel.apache.org/components/4.22.x/others/main.html |
| Contract-first startup | A missing `direct:<operationId>` route fails startup, since Camel 4.6 (medium confidence) | https://camel.apache.org/manual/rest-dsl-openapi.html |
| `missingOperation` | `fail` (default), `ignore`, `mock` | https://camel.apache.org/components/4.22.x/rest-openapi-component.html |
| `enableCORS` | Default `false`; default Allow-Origin `*`, Max-Age `3600` (medium confidence) | https://camel.apache.org/manual/rest-dsl-binding.html |
| Quarkus CORS filter | `quarkus.http.cors.enabled` default `false` (medium confidence) | https://quarkus.io/version/3.40/guides/security-cors |
| `quarkus.http.root-path` | Default `/` (medium confidence); effect on REST DSL paths (unverified) | https://quarkus.io/version/3.40/guides/http-reference |
| `quarkus.camel.openapi.expose.enabled` | Default `false`, build time | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/openapi-java.html |
| Codegen defaults | `codegen.enabled=true`, `model-package=org.apache.camel.quarkus`, `use-bean-validation=false` | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest-openapi.html |
| Test port | 8081 (`quarkus.http.test-port`, `0` = random), RestAssured timeout 30s (medium confidence) | https://quarkus.io/version/3.40/guides/getting-started-testing |
| platform-http defaults | `matchOnUriPrefix=false`, `useBodyHandler=true`, `muteException=true` | https://camel.apache.org/components/4.22.x/platform-http-component.html |
| Verification commands | `./mvnw quarkus:dev`, `curl -s localhost:8080/fruits`, `./mvnw test`, `./mvnw verify -Dnative` (representative) | page not recorded |

## External Resources

All fetched 2026-10-14. camel.apache.org manual and component pages carry no page date.

- Extension page: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest.html
- Platform HTTP: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html
- REST DSL: https://camel.apache.org/manual/rest-dsl.html
- REST DSL OpenAPI: https://camel.apache.org/manual/rest-dsl-openapi.html
- Official examples (`main` branch, not the 3.40.x tag): https://github.com/apache/camel-quarkus-examples (`rest-json`, `openapi-contract-first`)
- Quarkus HTTP reference: https://quarkus.io/version/3.40/guides/http-reference
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
