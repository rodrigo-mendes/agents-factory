# Investigator notes: Camel Quarkus REST / platform-http 3.40 (starting facts, fetched 2026-10-14)

Source: section-investigator output relayed by the orchestrator. Every item must be re-verified against its URL by the researcher before being written as High. The fetch tool summarizes pages through a small model.

## camel-quarkus-rest (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest.html)
- Artifact org.apache.camel.quarkus:camel-quarkus-rest, JVM+Native since 0.0.1. Provides `rest:method:path:uriTemplate` and `rest-api:path`.
- Depends on camel-quarkus-platform-http and configures it as the REST transport (default HTTP component = platform-http).
- Path parameter names with `-` or `$` need system property `io.vertx.web.route.param.extended-pattern=true`.
- Other transport: add camel-quarkus-servlet (or netty-http) and `restConfiguration().component("servlet")`.
- Page lists no config options.

## camel-quarkus-platform-http (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)
- Artifact org.apache.camel.quarkus:camel-quarkus-platform-http, JVM+Native since 0.3.0. Built on Vert.x via quarkus-vertx-http. Server options delegated to the Quarkus HTTP guide.
- URI `platform-http:path`; `platform-http:/hello` serves all methods; `httpMethodRestrict=GET` limits.
- Multipart: `quarkus.http.body.handle-file-uploads`, `quarkus.http.body.uploads-directory`, `quarkus.http.body.delete-uploaded-files-on-end` (defined only in the Quarkus guide).
- SSL via the Quarkus SSL guide; `SSLContextParameters` "not currently supported".
- Reverse proxy: Exchange.HTTP_URI and Exchange.HTTP_HOST populated from the absolute URL on the request line.
- The page's REST DSL example has a stray `;` before `.post(...)` (do not copy).
- `quarkus.http.root-path` effect on Camel routes: not covered, UNVERIFIED.

## platform-http component (checked on the 4.18.x page ONLY: https://camel.apache.org/components/4.18.x/platform-http-component.html; re-check on 4.22.x)
- matchOnUriPrefix=false; httpMethodRestrict = all; consumes/produces unrestricted; serverRequestValidation=true (415/406 before Camel); useBodyHandler=true; populateBodyWithForm=true; muteException=true; returnHttpRequestHeaders=false; bridgeErrorHandler=false; autowiredEnabled=true; cookiePath=/, cookieHttpOnly=false, cookieSecure=false, cookieSameSite=Lax. Reverse proxy only in camel-platform-http-vertx (Quarkus).

## rest component (https://camel.apache.org/components/next/rest-component.html; `next`, not pinned to 4.22.x)
- bridgeErrorHandler=false, lazyStartProducer=false, autowiredEnabled=true; consumerComponentName/producerComponentName/apiDoc/host/headerFilterStrategy no default. Candidate consumers listed: netty-http, jetty, servlet, undertow, platform-http. `outType` required for response POJO binding.

## restConfiguration defaults (https://camel.apache.org/manual/rest-dsl-binding.html and https://camel.apache.org/components/next/others/main.html)
- component, contextPath, host, port, apiContextPath: no default. bindingMode values off|auto|json|xml|json_xml, default off. JSON binding uses jackson by default. dataFormatProperty values must be strings; Main property is the plural `camel.rest.dataFormatProperties`. skipBindingOnErrorCode=true. enableNoContentResponse=false. enableCORS=false; CORS headers when enabled: Allow-Origin `*`, Allow-Methods `GET, HEAD, POST, PUT, DELETE, TRACE, OPTIONS, CONNECT, PATCH`, Allow-Headers `Origin, Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers`, Max-Age 3600.
- inlineRoutes: enabled by default from Camel 4.5 (https://camel.apache.org/manual/rest-dsl.html); property camel.rest.inline-routes; needs unique direct endpoints.
- clientRequestValidation off by default; failures: 415 content-type vs consumes, 406 accept vs produces, 400 missing required query/header/body, 400 disallowed values, 400 unparsable body (https://camel.apache.org/manual/rest-dsl-validation.html). camel-openapi-validator adds OpenAPI-based validation.
- Jackson (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jackson.html): artifact camel-quarkus-jackson; to use the Quarkus ObjectMapper: `restConfiguration().dataFormatProperty("autoDiscoverObjectMapper","true")` before defining REST routes; customize via an `ObjectMapperCustomizer` @Singleton bean.
- Verbs/paths: `rest("/x").get("/{id}").to("direct:...")`; path params arrive as headers of the same name; default response 200 or 204 with no body; `CamelHttpResponseCode` changes it; unhandled exception -> 500.

## Official example (re-verify)
- https://github.com/apache/camel-quarkus-examples (rest-json, quarkus-rest-json, openapi-contract-first, platform-http-security-keycloak, rest-keycloak-soap-jms). rest-json pom: quarkus.platform.version 3.40.1; deps camel-quarkus-jackson, camel-quarkus-rest, camel-quarkus-direct; tests use quarkus-junit and rest-assured; routes are plain RouteBuilder without @ApplicationScoped, `restConfiguration().bindingMode(RestBindingMode.json)`.
- Release notes https://camel.apache.org/releases/q-3.40.0/ list issues #9195 (openapi-java native WARN/ERROR from swagger ModelResolver; @JsonValue types rendered as objects) and #9153 (native build fails when kamelet DelegatingSchemaResolver reachable without camel-jackson).

## Open gaps (UNVERIFIED so far)
- `.param()` DSL syntax; `apiContextPath` serving behaviour; quarkus.http.port default and restConfiguration host/port interplay; quarkus.http.root-path effect; platform-http defaults on 4.22.x; whether AtlasMap and camel-restdsl-openapi-plugin (cited by the old 3.15 file) still apply to 3.40.

## OpenAPI with Camel REST DSL (investigator, fetched 2026-10-14; re-verify before High)
- Contract-first: `rest().openApi().specification("petstore-v3.json")` (OpenAPI 3.0/3.1; spec on classpath); available since Camel 4.6 (https://camel.apache.org/manual/rest-dsl-openapi.html; https://camel.apache.org/manual/rest-dsl.html documents code-first only). Each operation maps 1:1 to `direct:<operationId>`; missing route fails at startup by default. Base path from the contract; override with `camel.component.rest-openapi.base-path` or `restConfiguration().contextPath(...)`. Precedence change since Camel 4.12: UNVERIFIED (search summary only).
- Camel Quarkus rest-openapi page (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest-openapi.html): default base path `/` can shadow other HTTP endpoints, so set one; artifact camel-quarkus-rest-openapi (JVM+native since 1.0.0), URI `rest-openapi:specificationUri#operationId`; needs a RestProducerFactory (camel-quarkus-http or netty-http); contract files in `src/main/openapi`, `generate-code` goal of quarkus-maven-plugin generates models; codegen props (build time): `quarkus.camel.openapi.codegen.enabled=true`, `model-package=org.apache.camel.quarkus`, `use-bean-validation=false`, `not-null-jackson=false`, `ignore-unknown-properties=false`; add model package to `camel.rest.bindingPackageScan`; native: add spec/contract files to `quarkus.native.resources.includes` (page mixes singular/plural; use plural).
- rest-openapi component 4.22.x (https://camel.apache.org/components/4.22.x/rest-openapi-component.html): `missingOperation` fail|ignore|mock, default fail; `mockIncludePattern` default `classpath:camel-mock/**`; `requestValidationEnabled` default false (producer option); specificationUri default `openapi.json`. Mock order: canned files in `camel-mock`, OpenAPI example (GET), input body (DELETE/PUT/POST/PATCH), empty body.
- Code-first docs: camel-quarkus-openapi-java (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/openapi-java.html): `quarkus.camel.openapi.expose.enabled=false` (build time); when true exposes at `/q/openapi`, requires quarkus-smallrye-openapi; native: `@RegisterForReflection` on model classes; REST via `LambdaRouteBuilder` unsupported; avoid CDI injection in `configure()`. `apiContextPath` is off by default (spec not exposed unless `restConfiguration().apiContextPath("/api-doc")`).
- Validation: `clientRequestValidation` off by default; 415/406/400 mapping; response validation added in Camel 4.13 (errors 500; default not stated); `camel-openapi-validator` (https://camel.apache.org/components/4.22.x/others/openapi-validator.html) replaces the default validator automatically; severity via `camel.rest.validation-levels`.
- Camel 4.22.0 release notes (https://camel.apache.org/releases/release-4.22.0/) list rest-openapi/openapi-java bugs: CAMEL-24117 (shared strategy cross-talk for missingOperation/mockIncludePattern), CAMEL-24118 (RestOpenApiReader invalid OpenAPI 3.x), CAMEL-24115, CAMEL-24112, CAMEL-24113, CAMEL-24114.
- Gaps: `apiProperty`; literal default of clientRequestValidation; whether requestValidationEnabled applies to Rest DSL consumers; `camel.rest.api-context-path` value.
