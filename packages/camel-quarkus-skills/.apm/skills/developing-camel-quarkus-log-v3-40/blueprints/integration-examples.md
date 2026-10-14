# Integration Examples and Testing

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Commands are representative; adapt to your environment.

## Dependencies (versions from the BOM)

```xml
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-log</artifactId></dependency>
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-mdc</artifactId></dependency>
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-logging-json</artifactId></dependency>
```

## Routes

No injection is used, so the class needs no CDI scope annotation (see https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html).

```java
public class OrderRoutes extends RouteBuilder {
    @Override
    public void configure() {
        from("timer:orders?period=5000").routeId("orders")
            .setBody(constant("{\"pan\":\"4111111111111111\"}"))
            .log("Processing exchange")                                    // EIP, logger name = "orders"
            .to("log:com.acme.orders?showExchangeId=true&logMask=true");     // component
        from("timer:bulk?period=10").to("log:com.acme.bulk?groupInterval=10000&groupDelay=5000");
    }
}
```

## application.properties

```properties
# camel.main.logMask: (medium confidence) in Camel Quarkus; also set logMask=true on sensitive URIs
camel.main.logMask=true
quarkus.camel.mdc.enabled=true
quarkus.log.category."org.apache.camel".level=WARN
quarkus.log.category."com.acme".level=INFO
%dev.quarkus.log.console.json.enabled=false
%test.quarkus.log.console.json.enabled=false
quarkus.log.console.json.log-format=ecs
```

## Custom formatter bean

```java
@ApplicationScoped
@Named("logFormatter")   // auto-detected, applies to every Log endpoint
public class CompactFormatter implements org.apache.camel.spi.ExchangeFormatter {
    public String format(org.apache.camel.Exchange e) { return e.getExchangeId() + " " + e.getMessage().getBody(String.class); }
}
```

This sample keeps `@Named`. `@Identifier` lookup from Camel routes is documented (high confidence, https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html); only ArC removal of an `@Identifier`-only bean is (unverified), so add `@Unremovable` if you switch. See [masking and security](./masking-and-security.md).

## Testing

Assert routing, not log text: replace the log endpoint with a mock. Camel route-test style (AdviceWith, `weaveById`, the test support class) lives only in the skill `developing-camel-quarkus-junit-v3-40`; this skill carries no test sample. The only test artifact documented in the testing guide is `camel-quarkus-junit` (https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html). An official Quarkus or Camel Quarkus API to capture and assert log text in tests: (unverified) (no 3.40.x page found).

## Verification commands

```bash
mvn quarkus:dev                               # expect log lines with category com.acme.orders; "pan" is NOT guaranteed masked (default masking covers key-named values only, see masking-and-security)
mvn verify -Dnative                           # native build; expect the same log output (log output unverified)
grep -rn "showAll=true\|useMdcLogging" src/   # expect: no matches
```

Native mode: `camel-quarkus-log` is supported since 0.0.1; the native-mode guide has no logging-specific notes (https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html). Registry-only beans may need reflection registration (medium confidence).
