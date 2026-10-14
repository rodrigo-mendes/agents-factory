# Always-Do Patterns: Camel Quarkus Log 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Medium and unverified items are in the Ask First table in [SKILL.md](../SKILL.md) and the [register](./unverified-and-risks.md).

Contents: [1 EIP versus component](#1-eip-versus-component) · [2 endpoint masking](#2-endpoint-masking) · [3 camel-quarkus-mdc](#3-camel-quarkus-mdc)

## 1. EIP versus component

The Log EIP is "much lighter and meant for logging human logs". The `log:` component prints message content with fine control (`show*` options, `maxChars`, `style`, `multiline`). Defaults are in the SKILL.md Quick Reference.

```java
// Camel Quarkus 3.40.x / Camel 4.22.x. No injection here, so no CDI scope annotation is needed.
public class OrderRoutes extends RouteBuilder {
    @Override
    public void configure() {
        from("platform-http:/orders")
            .routeId("orders")
            .log(LoggingLevel.INFO, "Received order ${header.orderId}")   // EIP, logger name = route id
            .to("log:com.acme.orders?level=DEBUG&showExchangeId=true&showBodyType=true&maxChars=2000");
    }
}
```

Sources: https://camel.apache.org/components/4.22.x/eips/log-eip.html ; https://camel.apache.org/components/4.22.x/log-component.html

## 2. Endpoint masking

`logMask` defaults to `false` on the endpoint, so set it on each URI that can print secrets or PII. More in [masking and security](./masking-and-security.md).

```java
.to("log:com.acme.audit?showExchangeId=true&showRouteId=true&showBodyType=true&logMask=true&maxChars=500")
```

Source: https://camel.apache.org/components/4.22.x/log-component.html

## 3. camel-quarkus-mdc

`camel.main.useMdcLogging` is deprecated in favour of `camel-mdc`. The Camel Quarkus wrapper `camel-quarkus-mdc` is configured with `quarkus.camel.mdc.enabled` and `quarkus.camel.mdc.custom-exchange-headers` / `custom-exchange-properties`. Details in [MDC](./mdc.md).

```properties
# Camel Quarkus 3.40.x (dependency: org.apache.camel.quarkus:camel-quarkus-mdc, version from the BOM)
quarkus.camel.mdc.enabled=true
quarkus.camel.mdc.custom-exchange-headers=X-Correlation-Id
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mdc.html ; https://camel.apache.org/components/4.22.x/others/main.html
