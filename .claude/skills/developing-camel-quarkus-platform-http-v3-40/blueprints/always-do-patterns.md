# Always-Do Patterns — Camel Quarkus Platform HTTP 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). High-confidence patterns only; medium and unverified items are in the [register](./unverified-and-risks.md).

## 1. Declare the endpoint and restrict methods

`platform-http:/hello` serves all methods unless `httpMethodRestrict` is set ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)). The URI syntax is `platform-http:path`, with `path` required ([component page](https://camel.apache.org/components/4.22.x/platform-http-component.html)).

```java
// Camel Quarkus 3.40.x / Camel 4.22.x; no injection, so no @ApplicationScoped
public class OrdersRoutes extends RouteBuilder {
    @Override
    public void configure() {
        from("platform-http:/orders?httpMethodRestrict=POST&consumes=application/json&produces=application/json")
            .to("direct:createOrder");
    }
}
```

Defaults of all endpoint options, and the unverified multi-value form of `httpMethodRestrict`, are in the [Quick Reference](../SKILL.md#quick-reference).

## 2. Upload whitelist

Pair `fileNameExtWhitelist` (no default, [component page](https://camel.apache.org/components/4.22.x/platform-http-component.html)) with `httpMethodRestrict=POST`. Full detail and code, including body limits: [file uploads](./file-uploads.md).

## 3. HTTPS through the Quarkus TLS registry

The extension page states that configuring SSL with `SSLContextParameters` is not currently supported and points to the Quarkus SSL guide ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)). Quarkus uses `quarkus.tls.*` plus `quarkus.http.tls-configuration-name` ([HTTP reference](https://quarkus.io/version/3.40/guides/http-reference)). `quarkus.http.ssl-port` defaults to `8443` (same page). Code: [TLS and security](./tls-and-security.md#https-configuration).

## 4. Close plain HTTP when HTTPS is configured

`quarkus.http.insecure-requests` defaults to `enabled`; the other values are `redirect` and `disabled` ([HTTP reference](https://quarkus.io/version/3.40/guides/http-reference)).

```properties
# Quarkus 3.40
quarkus.http.insecure-requests=redirect
```

Use `disabled` when no client may use plain HTTP. If the management interface is on, it rejects plain HTTP once HTTPS is configured ([management reference](https://quarkus.io/version/3.40/guides/management-interface-reference)).

## 5. Read the authenticated identity from the documented header

Inside a route, the authenticated user is in the `VertxPlatformHttpConstants.AUTHENTICATED_USER` header, carrying the Quarkus `SecurityIdentity` / `Principal` ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)).

```java
// Camel Quarkus 3.40.x; header name per VertxPlatformHttpConstants.AUTHENTICATED_USER
from("platform-http:/me?httpMethodRestrict=GET")
    .process(e -> {
        Object user = e.getMessage().getHeader(VertxPlatformHttpConstants.AUTHENTICATED_USER);
        e.getMessage().setBody(String.valueOf(user));   // inspect the real type in your IDE
    });
```

Caveats on the value type and path permissions: [TLS and security](./tls-and-security.md#authentication-and-identity).

## 6. Routes without injection stay plain

`@ApplicationScoped` on a `RouteBuilder` is needed only for `@Inject` or `@ConfigProperty`, and it adds a boot-time penalty ([CDI guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html), verified by the orchestrator 2026-10-14).

```java
// needs injection, so the scope annotation is justified
@ApplicationScoped
public class GreetingRoutes extends RouteBuilder {
    @ConfigProperty(name = "greeting.prefix", defaultValue = "Hello") String prefix;
    @Override
    public void configure() {
        from("platform-http:/hello?httpMethodRestrict=GET")
            .setBody(simple(prefix + " ${header.name}"));
    }
}
```
