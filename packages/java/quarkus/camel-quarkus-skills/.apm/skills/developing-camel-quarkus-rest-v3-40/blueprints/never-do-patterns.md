# Never-Do Patterns — Camel Quarkus REST 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Items 1 to 3 are backed by versioned pages; each ✅ alternative is itself backed by a versioned page. The cautions below them are (medium confidence) or (unverified) and are not hard prohibitions.

## 1. TLS on the REST server through `SSLContextParameters` (severity: high)

"Configuration of the platform HTTP server is managed by Quarkus"; "configuring the server for SSL with `SSLContextParameters` is not currently supported". The runtime result of setting `SSLContextParameters` on this server is (unverified) (the sibling platform-http skill lists it as unverified); do not assert that TLS is "silently" ignored. Port behaviour is not a Never Do: whether `restConfiguration().port()` is ignored or fails is (unverified).

```java
// ❌ WRONG
restConfiguration().endpointProperty("sslContextParameters", "#ssl");
```
```properties
# ✅ CORRECT (Camel Quarkus 3.40.x: server settings are managed by Quarkus, configure them under quarkus.http.*)
quarkus.http.port=8080
```

TLS key and certificate settings may go through the Quarkus TLS registry (see the core skill); that the registry or the 3.40 TLS bridging applies to the inbound server is (unverified), so it is not offered as the alternative in SKILL.md. Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html

## 2. Hyphenated path parameter names (severity: moderate)

Platform-http (Vert.x) rejects `-` and `$` in parameter names unless the system property `io.vertx.web.route.param.extended-pattern=true` is set (versioned page). What the client sees on rejection is not documented.

```java
// ❌ WRONG
rest("/orders").get("/{order-id}").to("direct:order");
// ✅ CORRECT
rest("/orders").get("/{orderId}").to("direct:order");
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest.html

## 3. `camel-quarkus-junit5` (severity: moderate)

Renamed to `camel-quarkus-junit` in 3.31.0; `org.apache.camel.test.junit5` became `org.apache.camel.test.junit6`. The 3.40 testing guide documents only `camel-quarkus-junit`. The old artifact still resolves as a deprecated stub; its removal date is (unverified). Stub details and Camel test style: `developing-camel-quarkus-junit-v3-40`.

```xml
<!-- ❌ WRONG --><artifactId>camel-quarkus-junit5</artifactId>
<!-- ✅ CORRECT --><artifactId>camel-quarkus-junit</artifactId>
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
## Medium-confidence cautions

### Camel CORS with the default `*` origin in production (medium confidence)

The default Allow-Origin of `restConfiguration().enableCORS(true)` is `*`, per the unversioned binding manual (/manual/ pages are at most medium; the research's High tag for this pattern rests on that page and an unpinned Quarkus guide, so it was downgraded). Quarkus calls unrestricted origins in production "severe security risks" (research quote from the unpinned CORS guide, not re-fetched at the 3.40 URL). The interaction of the Camel and Quarkus CORS filters on one request is (unverified). Treat as an Ask First decision; default to the Quarkus filter.

```java
// ❌ AVOID in production
restConfiguration().enableCORS(true);
```
```properties
# ✅ PREFER
quarkus.http.cors.enabled=true
quarkus.http.cors.origins=https://app.example.com
```

Sources: https://camel.apache.org/manual/rest-dsl-binding.html ; https://quarkus.io/version/3.40/guides/security-cors

### AtlasMap for payload mapping (medium confidence)

`camel-atlasmap` was removed in Camel 4.0 with no replacement (CAMEL-19686), per a search summary of the Camel 4 migration guide; the page was not fully fetched. Older Camel Quarkus REST guidance built on AtlasMap does not apply. Do not recommend AtlasMap.

```java
// ❌ WRONG
from("direct:getDetails").to("atlasmap:map/request.adm");
// ✅ CORRECT: bind to POJOs, map in a bean
from("direct:getDetails").bean(DetailsMapper.class, "toBackend");
```

Source: https://camel.apache.org/manual/camel-4-migration-guide.html ; https://camel.apache.org/releases/release-4.0.0/

### Contract-first with the default base path `/` (medium confidence)

"Using the default path `/` can result in other HTTP endpoints already hosted under that path being inaccessible." That `contextPath` overrides the contract base path comes from investigator notes on the OpenAPI manual and is (unverified) as an exact behaviour.

```java
// ❌ WRONG: spec without servers/basePath, alongside other endpoints
rest().openApi().specification("petstore.json");
// ✅ CORRECT
restConfiguration().contextPath("/api");
rest().openApi().specification("petstore.json");
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest-openapi.html

### CDI injection in `configure()` for code-first OpenAPI, REST in `LambdaRouteBuilder` (medium confidence)

openapi-java builds the spec at build time where CDI is unavailable; `LambdaRouteBuilder` REST is not supported. Placeholder resolution in a REST path at build time is (unverified), so the sample below is marked.

```java
// ❌ WRONG: @Inject needs @ApplicationScoped on the RouteBuilder, and CDI is unavailable at build time
@jakarta.enterprise.context.ApplicationScoped
class R extends RouteBuilder {
    @Inject Config cfg;
    public void configure(){ rest(cfg.path()).get().to("direct:x"); }
}
// ✅ CORRECT (placeholder resolution (unverified)): plain RouteBuilder, no injection
class R extends RouteBuilder {
    public void configure(){ rest("{{api.path}}").get().to("direct:x"); }
}
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/openapi-java.html
