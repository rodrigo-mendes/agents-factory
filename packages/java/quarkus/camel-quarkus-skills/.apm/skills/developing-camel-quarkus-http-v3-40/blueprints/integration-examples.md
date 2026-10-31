# Integration Examples and Testing — camel-quarkus-http 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Contents

- [Full route](#full-route)
- [Application properties](#application-properties)
- [Quarkus REST client alternative](#quarkus-rest-client-alternative)
- [Testing](#testing)
- [Production notes](#production-notes)

## Full route

Plain `RouteBuilder`: no `@Inject` or `@ConfigProperty`, so no `@ApplicationScoped` is needed ([CDI guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html)).

```java
// Camel Quarkus 3.40.x / Camel 4.22.x
import org.apache.camel.builder.RouteBuilder;
// HttpOperationFailedException: package (unverified) on fetched pages, check the IDE import

public class PartnerRoutes extends RouteBuilder {
    @Override
    public void configure() {
        onException(HttpOperationFailedException.class)
            .handled(true)
            .setBody(simple("{\"error\":\"upstream ${exception.statusCode}\"}"));

        from("direct:getOrder").routeId("get-order")
            .removeHeaders("CamelHttp*")
            .setHeader("CamelHttpMethod", constant("GET"))
            .setHeader("CamelHttpPath", simple("/orders/${header.orderId}"))
            .circuitBreaker()
                // option names and defaults of faultToleranceConfiguration: (unverified), check the IDE
                .faultToleranceConfiguration().timeoutEnabled(true).timeoutDuration(2000).end()
                .to("{{partner.base-url}}/api?sslContextParameters=#partner&responseTimeout=5000").id("partner-call")
            .onFallback()
                .setBody(constant("{\"status\":\"degraded\"}"))
            .end();
    }
}
```

Sources: https://camel.apache.org/components/4.22.x/http-component.html ; https://camel.apache.org/components/4.22.x/eips/circuitBreaker-eip.html

## Application properties

```properties
# Camel Quarkus 3.40.x
# read by the route as {{partner.base-url}}; the WireMock test resource below overrides it
partner.base-url=https://partner.example.com
quarkus.tls.partner.trust-store.p12.path=/etc/ssl/partner-truststore.p12
quarkus.tls.partner.trust-store.p12.password=${PARTNER_TRUSTSTORE_PASSWORD}
# TLSv1.3 is the default (High, 3.40.0 migration guide); widen only per named bucket
# camel.component.<name>.<option> binding: page not recorded (medium confidence)
camel.component.https.connect-timeout=5000
```

`quarkus.camel.tls-registry.enabled` appears in the research example; build-time vs runtime for `quarkus.camel.tls-registry.*` is (unverified). TLS default: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html

## Quarkus REST client alternative

Typed interface (`@RegisterRestClient` / `@RestClient`) called from a bean. No official page compares it with camel-http (medium confidence). Source: https://quarkus.io/guides/rest-client (`tls-configuration-name` uses `quarkus.tls.<name>.*`; when set, the default TLS configuration is ignored).

```properties
# Quarkus 3.40.x
quarkus.rest-client.partner-api.url=https://partner.example.com/api
quarkus.rest-client.partner-api.tls-configuration-name=partner
```

## Testing

Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html. WireMock pattern also in https://quarkus.io/guides/rest-client.

```java
// Camel Quarkus 3.40.x: WireMock test resource. CamelQuarkusTestSupport: package and signatures are in the skill developing-camel-quarkus-junit-v3-40
public class PartnerWireMock implements QuarkusTestResourceLifecycleManager {
    WireMockServer server;
    @Override public Map<String, String> start() {
        server = new WireMockServer(wireMockConfig().dynamicPort());
        server.start();
        server.stubFor(get(urlPathMatching("/orders/.*")).willReturn(okJson("{\"id\":1}")));
        return Map.of("partner.base-url", server.baseUrl());   // overrides application.properties
    }
    @Override public void stop() { server.stop(); }
}

@QuarkusTest
@QuarkusTestResource(PartnerWireMock.class)
class GetOrderTest extends CamelQuarkusTestSupport {
    // Advice route "get-order" per test method and replace the step by id:
    // weaveById("partner-call").replace().to("mock:partner"). No wildcard weave patterns.
    // Exact base class, advice and setup signatures: developing-camel-quarkus-junit-v3-40.
}
```

Notes: `CamelQuarkusTestSupport` behaviour and the per-method advice API are in the skill `developing-camel-quarkus-junit-v3-40`. `interceptSendToEndpoint` is not covered by the guide (unverified).

## Production notes

Source for all: https://camel.apache.org/components/4.22.x/http-component.html (medium confidence: sizing advice is inferred from the defaults).

- `responsePayloadStreamingThreshold` defaults to 8192; `disableStreamCache=false`.
- `connectionsPerRoute` (20) caps concurrency to one host. Size it to the thread pool and the downstream SLA.
- Reference implementation: integration-tests/http module in https://github.com/apache/camel-quarkus (contents not fetched).
