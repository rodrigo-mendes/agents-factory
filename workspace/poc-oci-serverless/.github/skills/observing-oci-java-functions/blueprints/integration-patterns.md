# Integration Patterns — OCI Java Functions Observability

## Full Lifecycle Blueprint (Init → Invoke → Error Path)

```java
package com.example;

import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.monitoring.MonitoringClient;
import com.oracle.bmc.monitoring.model.*;
import com.oracle.bmc.monitoring.requests.PostMetricDataRequest;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;

public class OrderProcessorFunction {

    // ── COLD START INIT (once per container lifetime) ──────────────────────
    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static MonitoringClient monitoringClient;
    private static String compartmentId;
    private static String metricNamespace;

    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        var auth = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
        monitoringClient = MonitoringClient.builder().build(auth);
        compartmentId   = ctx.getConfigurationByKey("COMPARTMENT_OCID")
                             .orElseThrow(() -> new RuntimeException("COMPARTMENT_OCID missing"));
        metricNamespace = ctx.getConfigurationByKey("METRIC_NAMESPACE").orElse("order_system");
        log("INFO", "Function initialized", Map.of("namespace", metricNamespace));
    }

    // ── WARM INVOCATION (every call after cold start) ──────────────────────
    public String handleRequest(String orderId) {
        long start = System.currentTimeMillis();
        log("INFO", "Processing order", Map.of("orderId", orderId));
        try {
            String result = processOrder(orderId);
            long durationMs = System.currentTimeMillis() - start;
            postMetric("OrderProcessed", 1.0, Map.of("status", "success"));
            postMetric("OrderProcessingDuration", (double) durationMs, Map.of("orderId", orderId));
            log("INFO", "Order processed", Map.of("orderId", orderId, "durationMs", String.valueOf(durationMs)));
            return result;
        } catch (Exception e) {
            postMetric("OrderProcessed", 1.0, Map.of("status", "error"));
            log("ERROR", "Processing failed", Map.of("orderId", orderId, "error", e.getMessage()));
            throw new RuntimeException("Processing failed for " + orderId, e);
        }
    }

    // ── HELPERS ────────────────────────────────────────────────────────────
    private String processOrder(String orderId) { return "confirmed:" + orderId; }

    private void postMetric(String name, double value, Map<String, String> dimensions) {
        try {
            monitoringClient.postMetricData(PostMetricDataRequest.builder()
                .postMetricDataDetails(PostMetricDataDetails.builder()
                    .metricData(List.of(MetricDataDetails.builder()
                        .compartmentId(compartmentId).namespace(metricNamespace).name(name)
                        .dimensions(dimensions)
                        .datapoints(List.of(Datapoint.builder()
                            .timestamp(new Date()).value(value).count(1).build()))
                        .build()))
                    .batchAtomicity(PostMetricDataDetails.BatchAtomicity.NonAtomic)
                    .build())
                .build());
        } catch (Exception e) {
            System.err.println("{\"level\":\"WARN\",\"message\":\"Metric post failed\",\"metric\":\"" + name + "\"}");
        }
    }

    private static void log(String level, String message, Map<String, String> fields) {
        try {
            var entry = new LinkedHashMap<String, Object>();
            entry.put("timestamp", java.time.Instant.now().toString());
            entry.put("level", level);
            entry.put("message", message);
            entry.putAll(fields);
            System.out.println(MAPPER.writeValueAsString(entry));
        } catch (Exception ignored) {
            System.out.println("{\"level\":\"" + level + "\",\"message\":\"" + message + "\"}");
        }
    }
}
```

---

## OCI Functions ↔ OCI APM (OpenTelemetry Agent — Custom Java 21 Dockerfile)

**Compatibility**: OpenTelemetry Java Agent 2.28.1 + OCI APM OTLP endpoint

```dockerfile
# Build stage
FROM fnproject/fn-java-fdk-build:jdk21-1.0.218 AS build-stage
WORKDIR /function
ADD pom.xml .
RUN mvn package dependency:copy-dependencies \
    -DincludeScope=runtime -DskipTests=true \
    -Dmdep.prependGroupId=true -DoutputDirectory=target --fail-never
ADD src src/
RUN mvn package -DskipTests=true

# Download OTel agent
FROM alpine AS otel-stage
RUN apk add --no-cache curl && \
    curl -L -o /otel-agent.jar \
    https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v2.28.1/opentelemetry-javaagent.jar

# Runtime stage
FROM fnproject/fn-java-fdk:jdk21-1.0.218
WORKDIR /function
COPY --from=build-stage /function/target/*.jar          .
COPY --from=build-stage /function/target/dependency     ./dependency
COPY --from=otel-stage  /otel-agent.jar                 ./otel-agent.jar
ENV JAVA_TOOL_OPTIONS="-javaagent:/function/otel-agent.jar"
ENV OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"
CMD ["com.example.OrderProcessorFunction::handleRequest"]
```

**Required function config variables** (inject at deploy time — never hardcode):
```
OTEL_EXPORTER_OTLP_ENDPOINT  = https://apm-collector.<region>.oci.oraclecloud.com/20200101/opentelemetry/private
OTEL_EXPORTER_OTLP_HEADERS   = Authorization=dataKey <APM_PRIVATE_DATA_KEY>
OTEL_SERVICE_NAME             = order-processor-fn
OTEL_RESOURCE_ATTRIBUTES      = deployment.environment=prod,cloud.provider=oci
```

> **Edge Case**: Retrieve the exact `OTEL_EXPORTER_OTLP_ENDPOINT` from OCI Console → APM → Administration → APM Domains → `<domain>` → APM Domain Details. Do not construct the URL from documentation — endpoint format may vary by region.

---

## OCI Functions ↔ OCI APM (Native Tracer — No JVM Agent)

**When to use**: Cold-start budget < 400 ms total; only select code paths need tracing.

```xml
<!-- pom.xml addition (version managed by BOM or explicit) -->
<dependency>
    <groupId>com.oracle.apm.agent.java</groupId>
    <artifactId>apm-java-agent-tracer</artifactId>
    <version>1.17.1.2</version>
</dependency>
```

```java
import oracle.apm.agent.java.api.ApmAgent;
import oracle.apm.agent.java.api.Span;
import oracle.apm.agent.java.api.Tracer;

private String processWithTrace(String orderId) {
    Tracer tracer = ApmAgent.getTracer();
    Span span = tracer.spanBuilder("process-order")
        .setAttribute("order.id", orderId)
        .startSpan();
    try (var scope = span.makeCurrent()) {
        return processOrder(orderId);
    } catch (Exception e) {
        span.recordException(e);
        throw e;
    } finally {
        span.end();
    }
}
```

**Source**: [OCI APM Java Tracer Maven Build](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/build-apm-tracer-maven-project.html)

---

## OCI Functions ↔ OCI Monitoring — FDK JUnit 5 Test

```xml
<!-- pom.xml — test dependency -->
<dependency>
    <groupId>com.fnproject.fn</groupId>
    <artifactId>testing-junit5</artifactId>
    <version>1.1.12</version>
    <scope>test</scope>
</dependency>
```

```java
import com.fnproject.fn.testing.FnTestingExtension;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.RegisterExtension;
import static org.junit.jupiter.api.Assertions.*;

class OrderProcessorFunctionTest {

    @RegisterExtension
    FnTestingExtension testing = FnTestingExtension.createDefault();

    @Test
    void testHandleRequest_returnsConfirmedOrder() {
        testing.addFunctionConfig("COMPARTMENT_OCID", "ocid1.compartment.oc1..test");
        testing.addFunctionConfig("METRIC_NAMESPACE", "test_ns");

        testing.givenEvent()
               .withBody("\"order-001\"")
               .enqueue();

        testing.thenRun(OrderProcessorFunction.class, "handleRequest");

        var result = testing.getOnlyResult();
        assertNotNull(result);
        assertEquals("confirmed:order-001", result.getBodyAsString());
    }
}
```

---

## Performance Baseline

| Scenario | Cold-Start | Warm Invocation Overhead |
|----------|-----------|--------------------------|
| Java 11, no APM | ~800 ms–1.5 s | Baseline |
| Java 11 + OCI APM Java Agent | +80–150 ms | Minimal |
| Java 11 + OpenTelemetry Agent 2.28.1 | +120–200 ms | Minimal |
| Per `PostMetricData` call | — | +20–50 ms |

**Memory floor**: 128 MB minimum; use 256 MB when SDK + observability libs are loaded.
