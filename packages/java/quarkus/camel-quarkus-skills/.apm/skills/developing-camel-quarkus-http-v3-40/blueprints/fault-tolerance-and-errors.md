# Fault Tolerance and Error Handling — camel-quarkus-http 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Handling HttpOperationFailedException

`throwExceptionOnFailure=true` by default; a status outside `okStatusCodeRange` throws (medium confidence). The exception carries the status code, status line, redirect location and body as a String. Source: https://camel.apache.org/components/4.22.x/http-component.html ; `onException`, `maximumRedeliveries`, `redeliveryDelay`: https://camel.apache.org/manual/error-handler.html (unversioned page).

**Success range contradiction (as stated by the research):** the http component page's prose says "100..299" is success, while the `okStatusCodeRange` option default is `200-299`. Recommendation: set `okStatusCodeRange` explicitly (for example `200-299`) instead of relying on either statement.

```java
// Camel 4.22.x. The exception's Java package is (unverified) on the fetched pages:
// resolve the import with the IDE (the research guessed org.apache.camel.http.base).
public class OrderRoute extends RouteBuilder {
    @Override
    public void configure() {
        onException(HttpOperationFailedException.class)
            .onWhen(exchange -> exchange.getException(HttpOperationFailedException.class).getStatusCode() >= 500)
            .maximumRedeliveries(2).redeliveryDelay(500)
            .handled(true)
            .to("direct:httpServerError");
    }
}
```

Dead Letter Channel default (6 redeliveries, 1 s) is (unverified) (summariser only); set values explicitly.

## Status-code strategy (medium confidence)

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `throwExceptionOnFailure=true` + `onException` (default) | Fail-fast, works with the breaker | Exception cost | Default |
| `throwExceptionOnFailure=false`, branch on `CamelHttpResponseCode` | Control over 4xx bodies | Easy to forget a check | APIs with meaningful 4xx payloads |
| Widened `okStatusCodeRange` (e.g. `200-204,209,301-304`) | Declarative | Hides real failures | Known non-2xx success codes |

## HTTP 429 (medium confidence)

Default: HttpClient 5 waits for `Retry-After` and retries automatically (hidden latency, thread held). With `automaticRetriesDisabled=true`, a 429 throws `HttpOperationFailedException` at once for Camel or the breaker to handle. Source: https://camel.apache.org/components/4.22.x/http-component.html

## Circuit breaker with fallback

Dependency `camel-quarkus-microprofile-fault-tolerance` ("Circuit Breaker EIP using MicroProfile Fault Tolerance"; Stable; JVM and native since 1.0.0). `camel-quarkus-resilience4j` is not listed in the 3.40.x extension index. Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/microprofile-fault-tolerance.html ; https://camel.apache.org/components/4.22.x/eips/circuitBreaker-eip.html ; https://camel.apache.org/components/4.22.x/eips/fault-tolerance-eip.html

```java
// Camel 4.22.x / Camel Quarkus 3.40.x
public class QuoteRoute extends RouteBuilder {
    @Override
    public void configure() {
        from("direct:quote")
            .circuitBreaker()
                .faultToleranceConfiguration().timeoutEnabled(true).timeoutDuration(2000).end()
                .to("https://quotes.example.com/v1/quote?sslContextParameters=#defaultSslContextParameters")
            .onFallback()
                .transform().constant("{\"status\":\"degraded\"}")
            .end();
    }
}
```

(unverified): the `faultToleranceConfiguration` option defaults and whether the fallback runs on timeout (the EIP page only links to the configuration page). Set every option explicitly and test the timeout path. Plain `camel-resilience4j` on Camel Quarkus is (unverified): do not port `resilience4jConfiguration` routes as-is.

## Monitoring checklist

Track circuit-breaker state, the `CamelHttpResponseCode` distribution and TLS handshake failures after any `quarkus.tls` change.
