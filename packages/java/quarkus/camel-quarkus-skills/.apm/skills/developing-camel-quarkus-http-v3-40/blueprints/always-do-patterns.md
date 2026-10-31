# Always-Do Patterns — camel-quarkus-http 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). All patterns here are high confidence unless tagged.

## Contents

1. [Dependency and native SSL](#1-dependency-and-native-ssl)
2. [TLS registry bean on https endpoints](#2-tls-registry-bean-on-https-endpoints)
3. [Know the TLSv1.3 default](#3-know-the-tlsv13-default)
4. [Handle HttpOperationFailedException (Ask First, medium confidence)](#4-handle-httpoperationfailedexception-ask-first-medium-confidence)
5. [Circuit breaker with fault tolerance](#5-circuit-breaker-with-fault-tolerance)
6. [Recommended: explicit timeouts](#6-recommended-explicit-timeouts)

## 1. Dependency and native SSL

The extension is producer-only (`http`/`https`). It supports JVM and native since 1.0.0 and enables SSL in native mode automatically; no extra setting is documented as needed. The extension page lists no limitations and no `quarkus.camel.*` properties. All behaviour comes from the Camel 4.22.x `camel-http` component (Apache HttpClient 5).

```xml
<!-- Camel Quarkus 3.40.x; version managed by quarkus-camel-bom -->
<dependency>
  <groupId>org.apache.camel.quarkus</groupId>
  <artifactId>camel-quarkus-http</artifactId>
</dependency>
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/http.html ; https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-http/ (3.40.0, 2026-09-24).

## 2. TLS registry bean on https endpoints

Add `camel-quarkus-tls-registry` (Experimental). `quarkus.tls.*` becomes the bean `defaultSslContextParameters`; a named bucket `quarkus.tls.<name>.*` becomes bean `#<name>`. Reference it on each endpoint: the page does not state that bridging applies to an endpoint on its own. Details: [tls-and-security](./tls-and-security.md#bridging-quarkustls-to-camel).

```properties
# Camel Quarkus 3.40.x
quarkus.tls.partner.trust-store.p12.path=/etc/ssl/partner-truststore.p12
quarkus.tls.partner.trust-store.p12.password=${PARTNER_TRUSTSTORE_PASSWORD}
```
```java
// Camel 4.22.x / Camel Quarkus 3.40.x (plain RouteBuilder: no injection, so no @ApplicationScoped)
public class PartnerRoute extends RouteBuilder {
    @Override
    public void configure() {
        from("direct:callPartner")
            .to("https://partner.example.com/api/orders?sslContextParameters=#partner");
    }
}
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html ; https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-tls-registry/ (3.40.0, 2026-09-24).

## 3. Know the TLSv1.3 default

From 3.40.0 the bridged beans apply `protocols`, `cipher-suites` and `key-exchange-groups`. Because `quarkus.tls.protocols` defaults to `TLSv1.3`, a bridged `https:` endpoint now offers TLSv1.3 only; a peer without TLS 1.3 fails the handshake. Decide scope with the user (SKILL.md, Ask First) before changing it.

Confidence: High (default TLSv1.3 only, per the 3.40.0 migration guide). Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html

## 4. Handle HttpOperationFailedException (Ask First, medium confidence)

This is an Ask First row in SKILL.md, not Always Do. Handle `HttpOperationFailedException` with `onException`; it carries the status code, status line, redirect location and body as a String (medium confidence). Its Java package is (unverified): resolve the import in the IDE. The defaults that decide when it is thrown (`throwExceptionOnFailure`, `okStatusCodeRange`, `followRedirects`) are medium confidence (the page contradicts itself on the range): see SKILL.md Quick Reference and set them explicitly. Full example: [fault-tolerance-and-errors](./fault-tolerance-and-errors.md#handling-httpoperationfailedexception).

Sources: https://camel.apache.org/components/4.22.x/http-component.html ; https://camel.apache.org/manual/error-handler.html (unversioned page).

## 5. Circuit breaker with fault tolerance

Use `camel-quarkus-microprofile-fault-tolerance` (Stable, JVM and native). `inheritErrorHandler` defaults to `false`, so the protected step runs once and the breaker handles the failure. Defaults of `faultToleranceConfiguration` are (unverified; Ask First row in SKILL.md): set every option you rely on and test the timeout path. Example: [fault-tolerance-and-errors](./fault-tolerance-and-errors.md#circuit-breaker-with-fallback).

Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/microprofile-fault-tolerance.html ; https://camel.apache.org/components/4.22.x/eips/circuitBreaker-eip.html ; https://camel.apache.org/components/4.22.x/eips/fault-tolerance-eip.html.

## 6. Recommended: explicit timeouts

Versioned 4.22.x page, values seen consistently across 3 fetches. Defaults: `connectTimeout`, `connectionRequestTimeout`, `soTimeout` 180000 ms; `responseTimeout` unset (0 = infinite); `maxTotalConnections` 200; `connectionsPerRoute` 20. A slow downstream can hold threads for 3 minutes or forever. This is in SKILL.md Ask First, not Always Do, because the right values depend on the downstream latency budget.

```properties
# Camel Quarkus 3.40.x: standard camel.component.<name>.<option> binding (binding itself: page not recorded; medium confidence)
camel.component.https.connect-timeout=5000
camel.component.https.connection-request-timeout=2000
camel.component.https.response-timeout=10000
camel.component.https.max-total-connections=200
camel.component.https.connections-per-route=20
```

Source: https://camel.apache.org/components/4.22.x/http-component.html
