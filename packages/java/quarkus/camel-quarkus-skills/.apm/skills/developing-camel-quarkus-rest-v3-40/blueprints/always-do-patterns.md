# Always-Do Patterns — Camel Quarkus REST 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). The parts of sections 1, 2 and 5 that rest on versioned pages (transport, `bindingMode` default, `quarkus.http.*`) appear in SKILL.md Always Do. Everything tagged (medium confidence) below, including all of sections 3 and 4 except the `missingOperation` default, is in the Ask First table or the Quick Reference.

## 1. Dependencies

`camel-quarkus-rest` "depends on the Platform HTTP extension and configures it as the REST transport provider" (rest extension page, fetched 2026-10-14). That the REST DSL needs `camel-quarkus-jackson` and `camel-quarkus-direct` rests on the official `rest-json` pom on the `main` branch, not the 3.40.x tag (medium confidence). The official 3.40.1 example declares only the three artifacts below.

```xml
<!-- Camel Quarkus 3.40.x; versions managed by quarkus-bom + quarkus-camel-bom 3.40.1 -->
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-rest</artifactId></dependency>
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-jackson</artifactId></dependency>
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-direct</artifactId></dependency>
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest.html ; https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/rest-json/pom.xml

## 2. JSON binding

The `bindingMode` default `off` is documented on the main options 4.22.x page. JSON using Jackson by default and `skipBindingOnErrorCode` default `true` come from the unversioned binding manual (medium confidence).

```java
// Camel Quarkus 3.40.x. Plain RouteBuilder: no injection, so no @ApplicationScoped.
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

The example repository (`main` branch) uses `type` only; `.outType(...)` follows the binding manual example `post().type(UserPojo.class).outType(CountryPojo.class)` (medium confidence).

Source: https://camel.apache.org/manual/rest-dsl-binding.html ; https://camel.apache.org/components/4.22.x/others/main.html ; https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/rest-json/src/main/java/org/acme/rest/json/Routes.java

## 3. Status codes and errors

(medium confidence: REST DSL manual and validation manual are unversioned pages). Default 200 or 204 without body; an unhandled exception gives 500; `{sku}` arrives as header `sku`; custom error codes must be 300+.

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

Source: https://camel.apache.org/manual/rest-dsl.html ; https://camel.apache.org/manual/rest-dsl-validation.html

## 4. Contract-first routes

(medium confidence, unversioned OpenAPI manual): provide one `direct:<operationId>` route per operation; "Camel will fail on startup with an error" when the route is missing, available since Camel 4.6. The `missingOperation` default `fail` is documented on the versioned rest-openapi component 4.22.x page; it is kept in the SKILL.md Quick Reference.

```java
// Camel Quarkus 3.40.x
public class PetRoutes extends org.apache.camel.builder.RouteBuilder {
    @Override public void configure() {
        rest().openApi().specification("petstore.json");
        from("direct:getPetById").to("bean:petService?method=byId");
    }
}
```

```properties
# https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/openapi-contract-first/src/main/resources/application.properties
quarkus.native.resources.includes=petstore.json
quarkus.camel.openapi.codegen.model-package=sample.petstore.model
camel.rest.bindingMode=json
camel.rest.bindingPackageScan=${quarkus.camel.openapi.codegen.model-package}
```

More in [OpenAPI blueprint](./openapi-contract-first.md).

Source: https://camel.apache.org/manual/rest-dsl-openapi.html ; https://camel.apache.org/components/4.22.x/rest-openapi-component.html

## 5. Server settings belong to Quarkus

Platform-http extension page, 2026-10-14: port, TLS, body limits and the CORS filter are `quarkus.http.*` settings. The REST DSL has its own options (`restConfiguration()` or `camel.rest.*`), but the extension page lists no `quarkus.camel.*` options for REST.

```properties
# Camel Quarkus 3.40.x: the platform HTTP server is managed by Quarkus
quarkus.http.port=8080
```

TLS key and certificate settings go through the Quarkus TLS registry (core skill); the exact keys are not repeated here because this skill has not verified them, and whether that registry or the 3.40 TLS bridging applies to the inbound server is (unverified).

Whether `restConfiguration().host()/port()` is ignored or errors under platform-http is (unverified) (see [register](./unverified-and-risks.md#irresolvable-items-do-not-assert)).

Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html
