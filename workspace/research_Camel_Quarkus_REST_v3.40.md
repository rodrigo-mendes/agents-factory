# Research: Camel Quarkus REST v3.40 (camel-quarkus-rest, REST DSL — Camel Quarkus 3.40.x / Camel 4.22.x / Quarkus 3.40.x)

> Version lock: every claim here applies to **Camel Quarkus 3.40.x** only. Patterns from the 3.15 research file are treated as misinformation unless re-verified below.
> All sources fetched **2026-10-14**. camel.apache.org manual/component pages carry no publication date; they are accepted because they are the current docs for the current stable LTS. Pages under `/manual/` are unversioned ("latest"); their links point to 4.22.x component docs (rest-dsl.html, fetched 2026-10-14), so they are treated as documenting 4.22.x — tagged Medium where version-sensitive.
> Method note: WebFetch summarizes pages through a small model; some summaries returned in Spanish or paraphrased. Quoted text is the tool's rendering — re-check before quoting verbatim.
> Plan-approval step (P3 EnterPlanMode/ExitPlanMode) was **skipped**: forked batch run, no user available; scheme approved by the user upstream per the coordinator.
> Confidence tags: **High** = re-fetched by the researcher on the exact URL given; **Medium** = single source, unversioned page, or carried from the core pilot without re-fetch; **UNVERIFIED** = not confirmed by an official page.
> Core topics (BOM import, routes discovery, CDI beans, native reflection basics, TLS registry) are NOT repeated — see `workspace/research_Camel_Quarkus_Core_v3.40.md`.

---

## Metadata

```yaml
Full_Name: Apache Camel Quarkus — REST extension (org.apache.camel.quarkus:camel-quarkus-rest) + REST DSL
Target_Version: 3.40.x (examples pin quarkus.platform.version 3.40.1 — https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/rest-json/pom.xml)
Release_Date: 2026-09-28 for 3.40.0 (carried from core pilot, source https://camel.apache.org/releases/ — Medium; https://camel.apache.org/releases/q-3.40.0/ shows no date)
Support_Status: LTS (carried from core pilot: camel.apache.org/releases marks 3.40.0 LTS; Quarkus 3.40 LTS — Medium; Camel Quarkus-specific end date UNVERIFIED)
Camel_Version: 4.22.x (Medium — q-3.40.0 page does not state it; pilot lists Camel 4.22.1 from https://camel.apache.org/camel-quarkus/3.40.x/)
Java: 17 and 21 (https://camel.apache.org/releases/q-3.40.0/ — High)
Primary_Docs: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest.html
Official_Repo: https://github.com/apache/camel-quarkus ; examples https://github.com/apache/camel-quarkus-examples
Research_Date: 2026-10-14
Domain_Complexity: Standard (HTTP transport delegation, JSON binding, OpenAPI two modes, validation, security delegated to Quarkus, native resources)
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 4
Unverified_Count: 11
Irresolvable_Count: 5
Research_Quality_Score: 84%   # ~100 claims; (100 - 11 - 5) / 100
```

---

## Executive Summary

`camel-quarkus-rest` brings the Camel REST DSL (`rest:` and `rest-api:` components) to Quarkus. It is supported in JVM and native mode since 0.0.1. It **depends on `camel-quarkus-platform-http` and configures it as the REST transport**, so REST endpoints are served by the Quarkus Vert.x HTTP server (`quarkus-vertx-http`), and server settings (port, root path, TLS, body limits, CORS filter) are Quarkus `quarkus.http.*` settings, not Camel ones (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest.html; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html — High). The extension page lists no `quarkus.camel.*` options of its own; the REST DSL is configured via `restConfiguration()` or `camel.rest.*` properties.

What matters in 3.40 versus the 3.15 conventions: (1) **contract-first** is now native to the REST DSL — `rest().openApi().specification("x.json")` maps each `operationId` to `direct:<operationId>` and fails startup when a route is missing (since Camel 4.6, https://camel.apache.org/manual/rest-dsl-openapi.html); Camel Quarkus generates model classes at build time via `quarkus-maven-plugin` `generate-code` (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest-openapi.html). (2) **AtlasMap no longer exists** — `camel-atlasmap` was removed in Camel 4.0 with no replacement (https://camel.apache.org/manual/camel-4-migration-guide.html, via search summary — Medium), so the 3.15 file's AtlasMap patterns are invalid. (3) `inlineRoutes` is **on by default** since Camel 4.5 (https://camel.apache.org/manual/rest-dsl.html; https://camel.apache.org/components/4.22.x/others/main.html — High). (4) Camel 4.22.2 restored `produces`-driven Content-Type for json/xml-bound responses (https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html — Medium, investigator). (5) Test artifact is `camel-quarkus-junit` (renamed from `camel-quarkus-junit5` in 3.31; old name removed after 3.34 — https://camel.apache.org/camel-quarkus/next/migration-guide/3.31.0.html — Medium).

Three critical patterns: declare `camel-quarkus-rest` (platform-http comes transitively) plus `camel-quarkus-jackson` for `bindingMode(json)`; set `outType`/`type` on verbs for POJO binding and register models with `@RegisterForReflection` for native; secure endpoints with Quarkus HTTP security (`quarkus.http.auth.permission.*`), since `SSLContextParameters` on the platform-http server is not supported. Tier **Standard**: several integrations and a security surface, but authentication/TLS are delegated entirely to Quarkus.

**Version-lifetime risk (carried from core pilot, Medium):** Quarkus 4.0.0.Beta1 was released 2026-10-01 (Java 21 baseline, Jackson 3); no Camel Quarkus 4.x exists on Maven Central as of 2026-10-14. Jackson 3 directly affects `camel-quarkus-jackson`/JSON binding. Pin 3.40.x; do not assume Quarkus 4 compatibility.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**1. Depend on `camel-quarkus-rest` (+ a binding data format); platform-http is the transport**
> Confidence: 🟢 High | [✓✓ Triangulated | CQ rest extension page (2026-10-14) + official rest-json example pom (2026-10-14)]
- Why: the extension "depends on the Platform HTTP extension and configures it as the REST transport provider". The official 3.40.1 example declares only `camel-quarkus-rest`, `camel-quarkus-jackson`, `camel-quarkus-direct` (no explicit platform-http).
- Code:
  ```xml
  <!-- Camel Quarkus 3.40.x; versions managed by quarkus-bom + quarkus-camel-bom 3.40.1 -->
  <dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-rest</artifactId></dependency>
  <dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-jackson</artifactId></dependency>
  <dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-direct</artifactId></dependency>
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest.html (2026-10-14); https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/rest-json/pom.xml (2026-10-14)

**2. JSON binding explicitly: `bindingMode(json)` + `type`/`outType`**
> Confidence: 🟢 High | [✓✓ Triangulated | rest-dsl-binding manual + camel main options 4.22.x + rest-json example]
- Why: `bindingMode` default is `off` (https://camel.apache.org/manual/rest-dsl-binding.html; `camel.rest.bindingMode` default `RestBindingMode.off` at https://camel.apache.org/components/4.22.x/others/main.html). Values `off|auto|json|xml|json_xml`. JSON uses jackson by default. `skipBindingOnErrorCode` default `true` (rest-dsl-binding.html).
- Code:
  ```java
  // Camel Quarkus 3.40.x — https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/rest-json/src/main/java/org/acme/rest/json/Routes.java
  public class Routes extends org.apache.camel.builder.RouteBuilder {
      @Override public void configure() {
          restConfiguration().bindingMode(org.apache.camel.model.rest.RestBindingMode.json);
          rest("/fruits")
              .get().outType(Fruit[].class).to("direct:getFruits")
              .post().type(Fruit.class).to("direct:addFruit");
          from("direct:getFruits").setBody().constant(java.util.List.of());
          from("direct:addFruit").log("${body}");
      }
  }
  ```
  (`.outType(...)` added from https://camel.apache.org/manual/rest-dsl-binding.html example `post().type(UserPojo.class).outType(CountryPojo.class)`; the example repo uses `type` only.)
- Source: https://camel.apache.org/manual/rest-dsl-binding.html (2026-10-14); https://camel.apache.org/components/4.22.x/others/main.html (2026-10-14)

**3. Reuse the Quarkus ObjectMapper for REST binding**
> Confidence: 🟡 Medium (single source: CQ jackson page)
- Why: by default `JacksonDataFormat` creates its own ObjectMapper, ignoring Quarkus `ObjectMapperCustomizer` beans. For REST binding set `autoDiscoverObjectMapper` as a data format property (string value) before defining rest routes.
- Code:
  ```java
  // Camel Quarkus 3.40.x
  restConfiguration().bindingMode(RestBindingMode.json)
      .dataFormatProperty("autoDiscoverObjectMapper", "true");
  ```
  ```java
  @jakarta.inject.Singleton
  public class MapperCustomizer implements io.quarkus.jackson.ObjectMapperCustomizer {
      public void customize(com.fasterxml.jackson.databind.ObjectMapper m) { /* ... */ }
  }
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jackson.html (2026-10-14). The Main-property form `camel.rest.dataFormatProperties` is from https://camel.apache.org/components/4.22.x/others/main.html (no default listed).

**4. Set HTTP status codes via `CamelHttpResponseCode`; map exceptions in `onException`**
> Confidence: 🟢 High | [✓✓ Triangulated | rest-dsl manual + rest-dsl-validation manual]
- Why: default response 200, or 204 when no body; unhandled exception → 500; path param `{sku}` arrives as header `sku` (https://camel.apache.org/manual/rest-dsl.html). Custom error codes must be 300+ (https://camel.apache.org/manual/rest-dsl-validation.html).
- Code:
  ```java
  // Camel Quarkus 3.40.x
  onException(com.fasterxml.jackson.core.JsonParseException.class)
      .handled(true)
      .setHeader(Exchange.HTTP_RESPONSE_CODE, constant(400))
      .setHeader(Exchange.CONTENT_TYPE, constant("text/plain"))
      .setBody().constant("Invalid json data");

  rest("/stock").get("/{sku}").to("direct:one-sku");
  from("direct:one-sku")
      .choice()
        .when(simple("${header.sku} == 'CAMEL-MUG'")).setBody(constant("{\"sku\":\"CAMEL-MUG\",\"qty\":42}"))
        .otherwise().setHeader(Exchange.HTTP_RESPONSE_CODE, constant(404))
                    .setBody(simple("{\"error\":\"unknown SKU ${header.sku}\"}"))
      .end();
  ```
- Source: https://camel.apache.org/manual/rest-dsl.html (2026-10-14); https://camel.apache.org/manual/rest-dsl-validation.html (2026-10-14)

**5. Contract-first: one `direct:<operationId>` route per operation**
> Confidence: 🟢 High | [✓✓ Triangulated | rest-dsl-openapi manual + rest-openapi component 4.22.x (missingOperation default `fail`)]
- Why: "Camel will fail on startup with an error" when a `direct:operationId` route is missing (https://camel.apache.org/manual/rest-dsl-openapi.html). `missingOperation` = `fail` (default) | `ignore` | `mock`; `mockIncludePattern` default `classpath:camel-mock/**` (https://camel.apache.org/components/4.22.x/rest-openapi-component.html — page itself shows no version, Medium on version pin). Since Camel 4.6.
- Code:
  ```java
  // Camel Quarkus 3.40.x
  rest().openApi().specification("petstore.json");
  from("direct:getPetById").to("bean:petService?method=byId");
  ```
  ```properties
  # https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/openapi-contract-first/src/main/resources/application.properties
  quarkus.native.resources.includes=petstore.json
  quarkus.camel.openapi.codegen.model-package=sample.petstore.model
  camel.rest.bindingMode=json
  camel.rest.bindingPackageScan=${quarkus.camel.openapi.codegen.model-package}
  ```
- Source: https://camel.apache.org/manual/rest-dsl-openapi.html (2026-10-14); https://camel.apache.org/components/4.22.x/rest-openapi-component.html (2026-10-14)

**6. Native: register model classes and include contract files**
> Confidence: 🟡 Medium (each fact single-sourced)
- Why: openapi-java: "It's the users responsibility to use `@RegisterForReflection` to register all model classes for reflection" (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/openapi-java.html). Contract files must be added to the native image (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest-openapi.html — page mixes `quarkus.native.resources.include`/`includes`; the official example uses `quarkus.native.resources.includes`, plural).
- Code:
  ```java
  @io.quarkus.runtime.annotations.RegisterForReflection
  public record Fruit(String name, String description) {}
  ```
- Source: as above (2026-10-14)

### ⚠️ Conditional Patterns

**A. Contract-first vs code-first**
> Confidence: 🟢 High
- Options: A) contract-first `rest().openApi()` + `camel-quarkus-rest-openapi`; B) code-first REST DSL + `camel-quarkus-openapi-java` to publish docs.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A contract-first | API governance, generated models (`generate-code`), startup fails on missing operations | Spec file must ship in native (`quarkus.native.resources.includes`); default base path `/` can shadow other endpoints | A spec exists/is owned by API team |
  | B code-first | Fast iteration, type-safe Java DSL | Spec is derived; model classes need `@RegisterForReflection`; `LambdaRouteBuilder` REST unsupported | Internal APIs, spec optional |

- Agent: "Ask user: is there an authoritative OpenAPI document? If yes, A."
- Source: https://camel.apache.org/manual/rest-dsl-openapi.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest-openapi.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/openapi-java.html (2026-10-14)

**B. Where to publish the OpenAPI document**
> Confidence: 🟡 Medium
- Options: A) Camel endpoint via `camel.rest.apiContextPath=/api-doc` (example value, https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/openapi-contract-first/src/main/resources/application.properties; no default at https://camel.apache.org/components/4.22.x/others/main.html); B) merge into Quarkus `/q/openapi` with `quarkus.camel.openapi.expose.enabled=true` (default `false`, build-time) + `quarkus-smallrye-openapi` (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/openapi-java.html).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | No extra extension | Separate path to secure | Camel-only API |
  | B | Single spec with Quarkus REST endpoints, Swagger UI | Extra dependency; build-time flag | App mixes Quarkus REST and Camel REST |

- Agent: "Ask user whether Quarkus REST (JAX-RS) endpoints coexist."
- Source: as above (2026-10-14)

**C. Request validation: built-in vs camel-openapi-validator**
> Confidence: 🟢 High
- Options: A) `clientRequestValidation(true)` (off by default "to be backwards compatible"; 415/406/400); B) add `camel-openapi-validator` which replaces the default validator and validates payloads against the spec. Response validation exists since Camel 4.13 (`camel.rest.clientResponseValidation`, default `false`, https://camel.apache.org/components/4.22.x/others/main.html), failures → 500.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | Zero deps | Only headers/required params/body parse | Code-first |
  | B | Schema validation | Extra dependency; native support UNVERIFIED for CQ | Contract-first |

- Agent: "Ask user whether schema-level validation is required."
- Source: https://camel.apache.org/manual/rest-dsl-validation.html (2026-10-14)

**D. CORS: Camel `enableCORS` vs Quarkus CORS filter**
> Confidence: 🟡 Medium
- Options: A) `restConfiguration().enableCORS(true)` — default `false`; default headers Allow-Origin `*`, Allow-Methods `GET, HEAD, POST, PUT, DELETE, TRACE, OPTIONS, CONNECT, PATCH`, Max-Age `3600` (https://camel.apache.org/manual/rest-dsl-binding.html); B) `quarkus.http.cors.enabled=true` (default `false`) with explicit `quarkus.http.cors.origins` (https://quarkus.io/guides/security-cors).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | Per-REST-config | Default origin `*` | Never as-is in prod; override `corsHeaders` |
  | B | One policy for all HTTP endpoints, regex origins | Applies to whole server | Default choice on Quarkus |

- Interaction of A and B on the same request: UNVERIFIED.
- Source: as above (2026-10-14)

**E. Alternate transport (servlet / netty-http)**
> Confidence: 🟢 High (single page, re-fetched)
- Options: platform-http (default) vs `camel-quarkus-servlet` + `restConfiguration().component("servlet")`.
- Agent: "Ask only if the user needs Servlet-container semantics; otherwise keep platform-http."
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest.html (2026-10-14)

### 🚫 Forbidden Patterns

**1. Using AtlasMap for REST payload mapping (from the 3.15 file)**
> Severity: High
> Confidence: 🟡 Medium (search summary of the official migration guide; page not fully fetched)
- Why: `camel-atlasmap` was removed in Camel 4.0, alternative "none" (CAMEL-19686).
- Impact: dependency does not resolve on Camel 4.22 / CQ 3.40.
- ❌ Wrong:
  ```java
  from("direct:getDetails").to("atlasmap:map/request.adm");
  ```
- ✅ Correct:
  ```java
  // Camel Quarkus 3.40.x — bind to POJOs, map in Java/bean
  from("direct:getDetails").bean(DetailsMapper.class, "toBackend");
  ```
- Source: https://camel.apache.org/manual/camel-4-migration-guide.html ; https://camel.apache.org/releases/release-4.0.0/ (2026-10-14)

**2. Configuring the server port/TLS through `restConfiguration()` or `SSLContextParameters`**
> Severity: High
> Confidence: 🟢 High
- Why: "Configuration of the platform HTTP server is managed by Quarkus"; "configuring the server for SSL with `SSLContextParameters` is not currently supported" (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html). Whether `restConfiguration().port()` is ignored or errors under platform-http: UNVERIFIED.
- Impact: TLS silently not applied / port setting ineffective.
- ❌ Wrong:
  ```java
  restConfiguration().port(8443).endpointProperty("sslContextParameters", "#ssl");
  ```
- ✅ Correct:
  ```properties
  # Quarkus 3.40.x — https://quarkus.io/guides/http-reference
  quarkus.http.port=8080
  quarkus.tls.key-store.p12.path=server.p12
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html (2026-10-14)

**3. Enabling Camel CORS with the default `*` origin in production**
> Severity: High
> Confidence: 🟢 High | rest-dsl-binding + Quarkus CORS guide
- Why: default Allow-Origin is `*`; Quarkus calls unrestricted origins in production "severe security risks".
- Impact: cross-origin access from any site.
- ❌ Wrong:
  ```java
  restConfiguration().enableCORS(true);
  ```
- ✅ Correct:
  ```properties
  quarkus.http.cors.enabled=true
  quarkus.http.cors.origins=https://app.example.com
  ```
- Source: https://camel.apache.org/manual/rest-dsl-binding.html ; https://quarkus.io/guides/security-cors (2026-10-14)

**4. Hyphenated path parameter names without extended pattern**
> Severity: Medium
> Confidence: 🟢 High
- Why: platform-http (Vert.x) rejects `-`/`$` in param names unless `io.vertx.web.route.param.extended-pattern=true` (system property).
- Impact: route does not match.
- ❌ Wrong:
  ```java
  rest("/orders").get("/{order-id}").to("direct:order");
  ```
- ✅ Correct:
  ```java
  rest("/orders").get("/{orderId}").to("direct:order");
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest.html (2026-10-14)

**5. Contract-first with the default base path `/` alongside other HTTP endpoints**
> Severity: Medium
> Confidence: 🟡 Medium
- Why: "Using the default path `/` can result in other HTTP endpoints already hosted under that path being inaccessible."
- ❌ Wrong:
  ```java
  rest().openApi().specification("petstore.json"); // spec without servers/basePath
  ```
- ✅ Correct:
  ```java
  restConfiguration().contextPath("/api");
  rest().openApi().specification("petstore.json");
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest-openapi.html (2026-10-14). That `contextPath` overrides the contract base path: from investigator notes (rest-dsl-openapi.html) — Medium.

**6. Using `camel-quarkus-junit5` / `org.apache.camel.test.junit5`**
> Severity: High
> Confidence: 🟡 Medium
- Why: renamed to `camel-quarkus-junit` in 3.31.0; old artifact kept only until 3.34.0.
- ❌ Wrong:
  ```xml
  <artifactId>camel-quarkus-junit5</artifactId>
  ```
- ✅ Correct:
  ```xml
  <artifactId>camel-quarkus-junit</artifactId> <!-- imports org.apache.camel.test.junit6 -->
  ```
- Source: https://camel.apache.org/camel-quarkus/next/migration-guide/3.31.0.html (2026-10-14)

**7. Relying on CDI injection inside `configure()` for code-first OpenAPI, or REST in `LambdaRouteBuilder`**
> Severity: Medium
> Confidence: 🟡 Medium
- Why: openapi-java builds the spec at build time where CDI is unavailable; `LambdaRouteBuilder` REST not supported.
- ❌ Wrong:
  ```java
  @Inject Config cfg; public void configure(){ rest(cfg.path()).get().to("direct:x"); }
  ```
- ✅ Correct:
  ```java
  public void configure(){ rest("{{api.path}}").get().to("direct:x"); } // property placeholder
  ```
  (Placeholder resolution in rest path at build time for openapi-java: UNVERIFIED.)
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/openapi-java.html (2026-10-14)

---

## Migration Guide

> Confidence: 🟡 Medium | Sources: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/index.html (2026-10-14) + https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html (2026-10-14)

**Breaking / behavior changes relevant to REST (3.15 → 3.40):**
- CQ 3.40.0 migration guide: no rest/platform-http/openapi/jackson entries; TLS registry now enforced, `quarkus.tls.protocols` default `TLSv1.3` (https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html).
- CQ 3.39.0: Jolokia/CassandraQL only (https://camel.apache.org/camel-quarkus/next/migration-guide/3.39.0.html).
- CQ 3.31.0: `camel-quarkus-junit5` → `camel-quarkus-junit`; `org.apache.camel.test.junit5` → `junit6` (https://camel.apache.org/camel-quarkus/next/migration-guide/3.31.0.html).
- Camel 4.5: `inlineRoutes` default false → true (https://camel.apache.org/manual/rest-dsl.html).
- Camel 4.6: contract-first REST DSL (https://camel.apache.org/manual/rest-dsl-openapi.html).
- Camel 4.13: response validation (https://camel.apache.org/manual/rest-dsl-validation.html).
- Camel 4.22.2: json/xml binding — responses without Content-Type take it from verb `produces` (restores pre-4.18.4); `fileNameExtWhitelist` exact, case-insensitive match (https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html).
- Camel 4.22.1: REST producer on `vertx-http` strips `Content-Length`, `Host`, `Connection`, `Transfer-Encoding` unless own `headerFilterStrategy` (same URL).
- Camel 4.0: `camel-atlasmap` removed; `camel-restdsl-swagger-plugin` removed → `camel-restdsl-openapi-plugin`; generated REST DSL defaults to platform-http (https://camel.apache.org/manual/camel-4-migration-guide.html — search summary, Medium).
- 3.40.0 release notes: #9195 openapi-java native WARN/ERROR from swagger ModelResolver, `@JsonValue` rendered as objects; #9153 native build fails when kamelet DelegatingSchemaResolver reachable without camel-jackson (https://camel.apache.org/releases/q-3.40.0/ — High).
- CQ guides 3.17, 3.18, 3.23, 3.26, 3.27, 3.33, 3.35, 3.36, 3.38: not read — UNVERIFIED for REST impact.

**Upgrade Steps:**
1. Set `quarkus.platform.version` to 3.40.1 for both BOMs (see core research).
2. Replace `camel-quarkus-junit5` with `camel-quarkus-junit`; change `junit5` imports to `junit6`.
3. Remove AtlasMap; map with POJO binding + beans.
4. If a direct route is shared by several REST verbs, keep it as-is (not inlined) or split it (inlining needs 1:1 unique direct endpoints).
5. Replace `camel-restdsl-openapi-plugin` code generation with `rest().openApi()` + `quarkus-maven-plugin` `generate-code` where possible.
6. Re-test Content-Type of bound responses (4.18.4–4.22.0 behavior differed).

```bash
# Representative — adapt to your environment
grep -rn "camel-quarkus-junit5\|atlasmap\|camel-restdsl-swagger" pom.xml src/
# Expected: no matches after migration
```

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Quarkus platform | 3.40.1 | 3.40.x | https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/rest-json/pom.xml |
| Camel | 4.22.x | 4.22.x | Medium (core pilot) |
| Java | 17 | 21 | https://camel.apache.org/releases/q-3.40.0/ |
| Quarkus 4 / Jackson 3 | — | not supported | carried from core pilot, Medium |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | official example + official docs]

**Lifecycle**:
```java
// Camel Quarkus 3.40.x — code-first REST with params, validation and errors
import org.apache.camel.Exchange;
import org.apache.camel.builder.RouteBuilder;
import org.apache.camel.model.rest.RestBindingMode;
import org.apache.camel.model.rest.RestParamType;

public class OrderApi extends RouteBuilder {
    @Override public void configure() {
        restConfiguration()
            .bindingMode(RestBindingMode.json)                 // default off — rest-dsl-binding.html
            .dataFormatProperty("autoDiscoverObjectMapper", "true") // CQ jackson page
            .clientRequestValidation(true);                   // default false — rest-dsl-validation.html

        rest("/orders")
            .get("/{id}").produces("application/json").outType(Order.class)
                .param().name("verbose").type(RestParamType.query).defaultValue("false").endParam()
                .to("direct:getOrder")
            .post().consumes("application/json").type(Order.class).to("direct:createOrder");

        from("direct:getOrder").bean(OrderService.class, "find(${header.id})");
        from("direct:createOrder")
            .bean(OrderService.class, "create")
            .setHeader(Exchange.HTTP_RESPONSE_CODE, constant(201));
    }
}
```
`.param()...endParam()` syntax: from search snippet of https://camel.apache.org/manual/latest/rest-dsl.html — Medium; existence of a `.required(boolean)` builder method: UNVERIFIED.

**Integration**: Camel Quarkus REST ↔ camel-quarkus-platform-http
- Endpoints served by Quarkus Vert.x HTTP; `quarkus.http.root-path` default `/`, and non-Servlet endpoints are served under it (https://quarkus.io/guides/http-reference). Whether REST DSL paths are prefixed by `root-path`: UNVERIFIED.
- Authenticated user available in routes via header `VertxPlatformHttpConstants.AUTHENTICATED_USER` (`QuarkusHttpUser`) (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html — Medium, investigator).
- platform-http endpoint defaults (https://camel.apache.org/components/4.22.x/platform-http-component.html, page shows no version — Medium): `matchOnUriPrefix=false`, `useBodyHandler=true`, `populateBodyWithForm=true`, `muteException=true`, `returnHttpRequestHeaders=false`, `useStreaming=false`, `cookiePath=/`, `cookieSameSite=Lax`, `cookieHttpOnly=false`, `cookieSecure=false`; component `serverRequestValidation=true`.

**Integration**: Camel Quarkus REST ↔ camel-quarkus-openapi-java / rest-openapi
```xml
<!-- https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/openapi-contract-first/pom.xml -->
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-rest-openapi</artifactId></dependency>
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-openapi-java</artifactId></dependency>
<!-- quarkus-maven-plugin goals: generate-code, build -->
```
Codegen build-time defaults (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest-openapi.html): `quarkus.camel.openapi.codegen.enabled=true`, `model-package=org.apache.camel.quarkus`, `use-bean-validation=false`, `not-null-jackson=false`, `ignore-unknown-properties=false`; contract files under `src/main/openapi` (investigator notes — Medium). rest-openapi producer needs a `RestProducerFactory` (`camel-quarkus-http` or `camel-quarkus-netty-http`).

**Integration**: Camel Quarkus REST ↔ Quarkus REST (JAX-RS) — both run on the same Vert.x server; `quarkus.http.auth.permission` with `applies-to=jaxrs` targets only JAX-RS (https://quarkus.io/guides/security-authorize-web-endpoints-reference — Medium). Path collision behavior between Quarkus REST and Camel REST: UNVERIFIED.

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment
./mvnw quarkus:dev                    # dev mode
curl -s localhost:8080/fruits         # app port 8080, test port 8081 (https://quarkus.io/guides/getting-started-testing)
curl -s localhost:8080/api-doc        # if camel.rest.apiContextPath=/api-doc
./mvnw test                           # @QuarkusTest via Surefire
./mvnw verify -Dnative                # @QuarkusIntegrationTest via Failsafe
# Expected: 200 JSON array; tests green
```

**Testing** (https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html; https://quarkus.io/guides/getting-started-testing — Medium, investigator, both pages):
- Test deps in the official example: `quarkus-junit`, `io.rest-assured:rest-assured` (https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/rest-json/pom.xml — High).
- `camel-quarkus-junit` needed only for `CamelQuarkusTestSupport` (JVM only; one shared CamelContext per suite; `@TestProfile` to restart).
- Tests run on 8081 (`quarkus.http.test-port`, `0` = random); RestAssured timeout 30s (`quarkus.http.test-timeout`).

**Mocking**:
```java
// Camel Quarkus 3.40.x
@io.quarkus.test.junit.QuarkusTest
class FruitsTest {
    @org.junit.jupiter.api.Test
    void list() {
        io.restassured.RestAssured.given().when().get("/fruits")
            .then().statusCode(200);
    }
}
```
Backend replacement: `@Alternative @Priority` CDI beans, `AdviceWith`, or WireMock/Testcontainers via `QuarkusTestResourceLifecycleManager` (testing.html).

---

## Production Readiness

- **Performance**: `inlineRoutes=true` default reduces route count (https://camel.apache.org/manual/rest-dsl.html); `useStreaming` (platform-http-vertx only) for large bodies (https://camel.apache.org/components/4.22.x/platform-http-component.html). Numbers: UNVERIFIED (no official benchmarks found).
- **Scalability**: bounded by Quarkus Vert.x HTTP server; tune via `quarkus.http.*` (https://quarkus.io/guides/http-reference).
- **Monitoring**: health/metrics per core research; REST-specific metrics: UNVERIFIED.
- **Security**:
  - [ ] `quarkus.http.auth.permission.<name>.paths/policy` on REST paths; longest path wins; `@PermitAll` cannot override (https://quarkus.io/guides/security-authorize-web-endpoints-reference).
  - [ ] Secure `apiContextPath` / `/q/openapi` explicitly (need for separate entry: UNVERIFIED).
  - [ ] Keep `muteException=true` (default) so stack traces are not returned.
  - [ ] CORS with explicit origins only.
  - [ ] `fileNameExtWhitelist` for uploads (exact match since 4.22.2).
  - [ ] TLS via Quarkus TLS registry (TLSv1.3 default since CQ 3.40.0).
  - OIDC with platform-http: example `platform-http-security-keycloak` exists (https://github.com/apache/camel-quarkus-examples); OIDC config details UNVERIFIED (guide not fetched).

---

## Reference Implementations

- https://github.com/apache/camel-quarkus-examples/tree/main/rest-json — code-first, JSON binding (pins 3.40.1)
- https://github.com/apache/camel-quarkus-examples/tree/main/openapi-contract-first — contract-first, codegen, `/api-doc`
- https://github.com/apache/camel-quarkus-examples/tree/main/platform-http-security-keycloak — secured platform-http
- https://github.com/apache/camel-quarkus-examples/tree/main/quarkus-rest-json — Quarkus REST alongside Camel
- https://camel.apache.org/manual/rest-dsl.html — canonical REST DSL docs

---

## Source Bibliography

**Primary** (all accessed 2026-10-14; no page dates shown unless noted):
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/openapi-java.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest-openapi.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jackson.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/index.html ; .../3.40.0.html
- https://camel.apache.org/camel-quarkus/next/migration-guide/3.31.0.html ; .../3.39.0.html
- https://camel.apache.org/releases/q-3.40.0/
- https://camel.apache.org/manual/rest-dsl.html ; rest-dsl-binding.html ; rest-dsl-validation.html ; rest-dsl-openapi.html
- https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html
- https://camel.apache.org/manual/camel-4-migration-guide.html (search summary)
- https://camel.apache.org/components/4.22.x/platform-http-component.html ; rest-openapi-component.html ; others/main.html
- https://quarkus.io/guides/http-reference ; security-cors ; security-authorize-web-endpoints-reference ; getting-started-testing
- https://github.com/apache/camel-quarkus-examples (rest-json, openapi-contract-first raw files)

**Validation**: core pilot `workspace/research_Camel_Quarkus_Core_v3.40.md` (release date, LTS, Quarkus 4 risk — carried, not re-fetched).

**Rejected**: https://quarkus.io/blog/camel-quarkus-effortless-apis/ (cited by 3.15 file; AtlasMap-based, pre-Camel-4 content).

---

## Research Gaps

```
Gap: quarkus.http.root-path effect on REST DSL paths
Impact: wrong URLs/permission paths
Workaround: test with curl in dev mode
Follow-up: CQ platform-http page / camel-quarkus GitHub tests
§7-ref: Iteration 2 — IRRESOLVABLE
```
```
Gap: restConfiguration().host()/port() behavior under platform-http
Impact: misleading config
Workaround: use quarkus.http.port only
Follow-up: camel-quarkus source (PlatformHttp recorder)
§7-ref: Iteration 2 — IRRESOLVABLE
```
```
Gap: Whether apiContextPath / /q/openapi need separate quarkus.http.auth.permission entries
Impact: unauthenticated spec exposure
Workaround: add explicit permission for the doc path
Follow-up: platform-http-security-keycloak example
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: Camel enableCORS vs Quarkus CORS filter on the same request
Impact: duplicate/conflicting CORS headers
Workaround: use only the Quarkus filter
Follow-up: CQ issue tracker
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: CQ migration guides 3.17–3.38 (9 guides) not read for REST impact
Impact: possible missed breaking change
Workaround: read each before upgrading from 3.15
Follow-up: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/index.html
§7-ref: Iteration 3 — IRRESOLVABLE
```
Other UNVERIFIED items (inline above): `.required()` param builder; camel-openapi-validator native support; placeholder in rest path for openapi-java; OIDC config; Quarkus REST/Camel REST path collision; REST metrics; performance numbers; release date/Camel version on q-3.40.0 page (carried from pilot); CQ LTS end date; contextPath overriding contract base path; `camel.dataformat.jackson.auto-discover-object-mapper` property name.

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Guardrails | rest-openapi defaults (missingOperation=fail, mockIncludePattern) | Resolved | https://camel.apache.org/components/4.22.x/rest-openapi-component.html (2026-10-14) |
| 1 | Guardrails | camel.rest.* defaults (bindingMode off, inlineRoutes true, enableCORS false, validation false) | Resolved | https://camel.apache.org/components/4.22.x/others/main.html (2026-10-14) |
| 1 | Forbidden | AtlasMap status | Resolved (removed in 4.0) | https://camel.apache.org/manual/camel-4-migration-guide.html (2026-10-14) |
| 1 | Migration | camel-restdsl-openapi-plugin status | Resolved (exists; swagger plugin removed) — Medium | search summary camel.apache.org (2026-10-14) |
| 1 | Integration | platform-http defaults on 4.22.x URL | Resolved (page version not displayed) | https://camel.apache.org/components/4.22.x/platform-http-component.html (2026-10-14) |
| 2 | Integration | quarkus.http.root-path default `/` | Resolved | https://quarkus.io/guides/http-reference (2026-10-14) |
| 2 | Conditional | Quarkus CORS enabled default false | Resolved | https://quarkus.io/guides/security-cors (2026-10-14) |
| 2 | Blueprint | .param() syntax | Updated — Medium | https://camel.apache.org/manual/latest/rest-dsl.html (search snippet) |
| 2 | Integration | root-path effect on Camel REST | ⚠️ IRRESOLVABLE — not documented in CQ or Quarkus pages | — |
| 2 | Integration | restConfiguration host/port under platform-http | ⚠️ IRRESOLVABLE — no official statement | — |
| 3 | Guardrails | apiContextPath value and contract-first example | Resolved | https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/openapi-contract-first/src/main/resources/application.properties (2026-10-14) |
| 3 | Guardrails | validation status codes, response validation 4.13 | Resolved | https://camel.apache.org/manual/rest-dsl-validation.html (2026-10-14) |
| 3 | Security | doc path permissions | ⚠️ IRRESOLVABLE — no official statement | — |
| 3 | Conditional | Camel vs Quarkus CORS interplay | ⚠️ IRRESOLVABLE — no official statement | — |
| 3 | Migration | CQ guides 3.17–3.38 | ⚠️ IRRESOLVABLE — iteration budget exhausted | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Standard)
- [x] All scope areas cited (config, verbs/params, binding, OpenAPI both modes, errors, CORS, security, native, testing)
- [x] Pattern counts driven by domain needs (6 / 5 / 7)
- [x] Every anti-pattern has alternative
- [x] All CLI commands validated/marked as representative
- [x] Integration examples complete (platform-http, openapi-java/rest-openapi, jackson, Quarkus REST, core via pilot)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example (rest-json routes)
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated or downgraded to 🟡 Medium (4 triangulated; #3, #6 Medium)
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in §7

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: Mandatory #1, #2, #4, #5; Forbidden #2, #3, #4; validation status codes; bindingMode/inlineRoutes/CORS defaults.
- **Medium Confidence (validate with user)**: Mandatory #3 (jackson auto-discover), #6 (native); AtlasMap removal; junit rename; migration items from 4.22 upgrade guide; platform-http default table (versionless page); all facts carried from the core pilot.
- **Low Confidence (must ask human)**: the 5 IRRESOLVABLE items and 11 UNVERIFIED items listed in Research Gaps.
- **Edge Cases (pause)**: Quarkus 4 / Jackson 3 transition (no CQ 4.x yet); 3.40.0 released ~16 days before research (<30 days) — docs may still change.
- **Emergency Stop**: none triggered; all sources official.
