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
        // PostMetricData requires the INGESTION endpoint; without it the post fails silently.
        monitoringClient.setEndpoint("https://telemetry-ingestion." + auth.getRegion().getRegionId() + ".oraclecloud.com");
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

## Distributed Tracing THROUGH OCI Streaming (Producer → N Consumers, One TraceId)

**Problem**: HTTP context propagation (W3C `traceparent` header) does not cross OCI Streaming — an event on a stream carries no HTTP headers. If the producer and each consumer start independent root spans, APM shows N disconnected traces instead of one, and you lose the end-to-end picture across the fan-out.

**Pattern**: carry the W3C trace context **inside the message envelope**, not in transport headers. Add a `trace` field to the `DomainEvent` (a `traceparent` + optional `tracestate`). The producer injects it from its active SERVER span; each consumer re-parents a CONSUMER span onto that remote context. Result: producer SERVER + every consumer CONSUMER span share ONE `TraceId` in APM Trace Explorer. Confirmed live (single TraceId `f94cb37b…` spanning producer + audit + notify consumers).

```java
// ── DomainEvent envelope carries the trace context (not HTTP headers) ──────────
public record TraceContext(String traceparent, String tracestate) {}
// DomainEvent { ... String eventType; Object payload; TraceContext trace; }

// ── PRODUCER: inject the active SERVER span's context into the envelope ─────────
// Called INSIDE the producer's SERVER span scope, just before PutMessages.
public TraceContext injectTraceContext() {
    if (tracer == null) return new TraceContext(null, null);
    Map<String, String> carrier = new HashMap<>();
    GlobalOpenTelemetry.getPropagators().getTextMapPropagator()
        .inject(Context.current(), carrier, Map::put);        // writes W3C traceparent/tracestate
    return new TraceContext(carrier.get("traceparent"), carrier.get("tracestate"));
}
// event.setTrace(injectTraceContext());  → serialize event → stream.putMessages(...)

// ── CONSUMER: re-parent a CONSUMER span onto the envelope's remote context ──────
public Span startConsumerSpan(String name, String traceparent, String tracestate) {
    if (tracer == null) return Span.getInvalid();
    Context parent = Context.current();
    if (traceparent != null && !traceparent.isBlank()) {
        Map<String, String> carrier = new HashMap<>();
        carrier.put("traceparent", traceparent);
        if (tracestate != null && !tracestate.isBlank()) carrier.put("tracestate", tracestate);
        parent = GlobalOpenTelemetry.getPropagators().getTextMapPropagator()
            .extract(Context.current(), carrier, new TextMapGetter<>() {
                public String get(Map<String,String> c, String k) { return c.get(k); }
                public Iterable<String> keys(Map<String,String> c) { return c.keySet(); }
            });
    }
    return tracer.spanBuilder(name)
        .setParent(parent)                     // ← joins the producer's trace
        .setSpanKind(SpanKind.CONSUMER)        // ← messaging semantics in APM
        .startSpan();
}
// Each consumer: Span s = startConsumerSpan("consume " + event.eventType(),
//                          event.trace().traceparent(), event.trace().tracestate());
```

**Rules that make this work**:
- The producer must call `injectTraceContext()` **while the SERVER span is current** — inject captures `Context.current()`, so an empty/invalid context yields a null `traceparent` and the consumers start new roots.
- Register the `W3CTraceContextPropagator` on the SDK (`.setPropagators(ContextPropagators.create(W3CTraceContextPropagator.getInstance()))`) on **both** producer and consumers — otherwise inject/extract are no-ops.
- Use `SpanKind.CONSUMER` on the consumer span (and `SpanKind.SERVER`/`PRODUCER` upstream) so APM renders the messaging fan-out correctly.
- Export spans with `SimpleSpanProcessor`, not `BatchSpanProcessor` (see never-do #7) — the container freezes on return.
- Null-guard everything: with tracing disabled or a partial envelope, degrade to `Span.getInvalid()` no-ops so callers can invoke start/end unconditionally.

**Evidence**: `services/func-event-producer/src/main/java/com/brx/functions/event/producer/obs/TracingSupport.java` (`injectTraceContext` / `startConsumerSpan`); `docs/handoff/event-pubsub/observability-validation-report.md` (single TraceId `f94cb37b…` across producer SERVER + 2 consumer CONSUMER siblings + 1 CLIENT downstream).

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
