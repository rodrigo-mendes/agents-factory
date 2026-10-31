# EMF Implementation (option a, hand-written)

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. The document shape is High ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)); the Java classes are representative sketches, not compiled. Choosing this option is Ask First ([D1](./ask-first-decisions.md#d1-metric-approach)).

## Contents

- [Metrics bean](#metrics-bean)
- [Handler integration](#handler-integration)
- [Per-tenant reporting without per-tenant metrics](#per-tenant-reporting-without-per-tenant-metrics)
- [Micrometer sketch, only with an ADR](#micrometer-sketch-only-with-an-adr)
- [Unit test](#unit-test)

## Metrics bean

The sketch assumes a Jackson `ObjectMapper` bean (`io.quarkus:quarkus-jackson`). Whether `quarkus-amazon-lambda` 3.40.1.1 brings it transitively was not verified (unverified): add the dependency explicitly if the build needs it.

```java
// Quarkus 3.40.1.1 - representative, not compiled
package com.example.metrics;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import jakarta.enterprise.context.ApplicationScoped;

@ApplicationScoped
public class OrderMetrics {

    private static final String NAMESPACE = "SaaS/Orders";   // never "AWS/..."
    private final ObjectMapper mapper;

    OrderMetrics(ObjectMapper mapper) { this.mapper = mapper; }

    /** Writes one EMF document synchronously; call before the handler returns. */
    public void orderPlaced(String service, String tenantTier, String tenantId,
                            String requestId, double latencyMs) {
        ObjectNode root = mapper.createObjectNode();
        ObjectNode aws = root.putObject("_aws");
        aws.put("Timestamp", System.currentTimeMillis());                 // epoch ms
        ObjectNode directive = aws.putArray("CloudWatchMetrics").addObject();
        directive.put("Namespace", NAMESPACE);
        directive.putArray("Dimensions").addArray().add("Service").add("TenantTier"); // bounded
        ArrayNode metrics = directive.putArray("Metrics");                 // at most 100
        metrics.addObject().put("Name", "OrdersPlaced").put("Unit", "Count");
        metrics.addObject().put("Name", "OrderLatency").put("Unit", "Milliseconds");

        root.put("Service", service);        // dimension targets: flat strings
        root.put("TenantTier", tenantTier);
        root.put("OrdersPlaced", 1);         // metric targets: numbers
        root.put("OrderLatency", latencyMs);
        root.put("tenantId", tenantId);      // property only (family rule 7)
        root.put("requestId", requestId);    // property only

        System.out.println(root.toString()); // one line, raw stdout
    }
}
```

## Handler integration

Handler wiring (`QuarkusStreamHandler`, `quarkus.lambda.handler`) belongs to the [developing skill](../../developing-quarkus-amazon-lambda-v3-40/SKILL.md). The tenant comes from the token, never from the path alone (family rule 6).

```java
// Quarkus 3.40.1.1 - representative
@Named("orders")
public class OrdersHandler implements RequestHandler<OrderRequest, OrderResponse> {
    @Inject OrderMetrics metrics;
    @Inject OrderService service;

    @Override
    public OrderResponse handleRequest(OrderRequest in, Context ctx) {
        long start = System.nanoTime();
        OrderResponse out = service.place(in);
        double ms = (System.nanoTime() - start) / 1_000_000.0;
        metrics.orderPlaced("orders", out.tenantTier(), out.tenantId(), ctx.getAwsRequestId(), ms);
        return out;   // metrics already written
    }
}
```

## Per-tenant reporting without per-tenant metrics

CloudWatch Logs Insights; `stats`, `sum`, `pct`, `by` and `bin` are documented on the [stats page](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-Stats.html); visualisations are limited to 100 bars.

```
stats sum(OrdersPlaced) as orders, pct(OrderLatency, 95) as p95 by tenantId, bin(1h)
```

## Micrometer sketch, only with an ADR

No Quarkiverse CloudWatch extension exists (High, family fact). Frozen-environment behaviour of the push registry is (unverified); constructor and SDK client requirements are (unverified).

```xml
<!-- Quarkus 3.40.1.1 - representative -->
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-micrometer</artifactId></dependency>
<dependency><groupId>io.micrometer</groupId><artifactId>micrometer-registry-cloudwatch2</artifactId></dependency> <!-- 1.17.1 via micrometer-bom -->
```

```properties
# default true; false avoids publishing JVM/system meters as billed custom metrics (medium confidence)
quarkus.micrometer.binder-enabled-default=false
```

The `MeterRegistry` must come from your own `@Produces` method configured through MicroProfile Config ([Quarkus Micrometer](https://quarkus.io/version/3.40/guides/telemetry-micrometer)).

## Unit test

No AWS call: capture stdout and parse it, the approach Powertools documents for its own output. A plain JUnit 5 test needs no Quarkus boot. Testing the deployed Lambda through the mock event server is in the testing skill (family fact: `quarkus-test-amazon-lambda` was removed in 3.31).

```java
// Quarkus 3.40.1.1 - representative
class OrderMetricsTest {
    @Test
    void writesOneValidEmfLine() throws Exception {
        PrintStream original = System.out;
        ByteArrayOutputStream captured = new ByteArrayOutputStream();
        System.setOut(new PrintStream(captured));
        try {
            new OrderMetrics(new ObjectMapper()).orderPlaced("orders", "premium", "t-1", "r-1", 12.5);
        } finally { System.setOut(original); }
        String[] lines = captured.toString().trim().split("\n");
        assertEquals(1, lines.length);
        JsonNode root = new ObjectMapper().readTree(lines[0]);
        assertTrue(root.at("/_aws/Timestamp").isIntegralNumber());
        JsonNode dir = root.at("/_aws/CloudWatchMetrics/0");
        assertEquals("SaaS/Orders", dir.get("Namespace").asText());
        assertFalse(dir.get("Dimensions").toString().contains("tenantId"));   // family rule 7
        assertTrue(dir.get("Metrics").size() <= 100);
        assertTrue(root.get("OrdersPlaced").isNumber());
    }
}
```
