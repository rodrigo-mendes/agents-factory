## Integration Patterns

### fn-events ↔ OCI API Gateway

**Pattern**: Synchronous HTTP request/response with typed abstractions.

```java
// API Gateway → Function (fn-events v1.1.x)
// func.yaml cmd: com.example.Function::handler
public class Function extends APIGatewayFunction<OrderRequest, OrderResponse> {
    @Override
    public APIGatewayResponseEvent<OrderResponse> handler(
            APIGatewayRequestEvent<OrderRequest> requestEvent) {
        // Query params, headers, method, body — all typed
        return new APIGatewayResponseEvent.Builder<OrderResponse>()
            .statusCode(HttpStatus.SC_OK)
            .body(new OrderResponse())
            .build();
    }
}
```

**Required Configuration**: API Gateway deployment route must point to the function with `type: ORACLE_FUNCTIONS_BACKEND`.

**Source**: [API Gateway + Functions](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayusingfunctionsbackend.htm)

---

### fn-events ↔ OCI Service Connector Hub (Streaming)

**Pattern**: Async batch processing of Streaming messages with auto base64 decode.

```java
// SCH (Streaming source) → Function (fn-events v1.1.x)
public class StreamProcessorFunction extends ConnectorHubFunction<StreamingData<OrderEvent>> {

    @Override
    public void handler(ConnectorHubBatch<StreamingData<OrderEvent>> batch) {
        for (StreamingData<OrderEvent> stream : batch.getBatch()) {
            OrderEvent event = stream.getValue();    // auto base64 decoded
            String streamName = stream.getStream();
            String partition = stream.getPartition();
            String offset = stream.getOffset();
            process(event);
        }
    }
}
```

**Required Configuration**: Service Connector Hub connector with Streaming source and Functions target.

**Source**: [SCH Streaming Source](https://docs.oracle.com/en-us/iaas/Content/connector-hub/create-service-connector-streaming-source.htm)

---

### fn-events ↔ OCI Notifications

**Pattern**: Async single message processing from topic subscription.

```java
// OCI Notifications → Function (fn-events v1.1.x)
public class NotificationHandler extends NotificationFunction<AlertPayload> {
    @Override
    public void handler(NotificationMessage<AlertPayload> content) {
        AlertPayload payload = content.getBody();
        // Headers available via content.getHeaders()
        process(payload);
    }
}
```

**Required Configuration**: OCI Notification topic with Function subscription.

**Source**: [OCI Notifications](https://docs.oracle.com/en-us/iaas/Content/Notification/Tasks/create-subscription-function.htm)

---

### fn-events ↔ OCI Service Connector Hub (Monitoring)

**Pattern**: Async batch processing of OCI Monitoring metrics.

```java
// SCH (Monitoring source) → Function (fn-events v1.1.x)
public class MetricAlertFunction extends ConnectorHubFunction<MetricData> {

    private double threshold;

    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        this.threshold = Double.parseDouble(
            ctx.getConfigurationByKey("CPU_THRESHOLD").orElse("90.0"));
    }

    @Override
    public void handler(ConnectorHubBatch<MetricData> batch) {
        for (MetricData metric : batch.getBatch()) {
            if (metric.getDatapoints().stream()
                    .anyMatch(dp -> dp.getValue() > threshold)) {
                sendAlert(metric);
            }
        }
    }
}
```

**Source**: [SCH Monitoring Source](https://docs.oracle.com/en-us/iaas/Content/connector-hub/create-service-connector-monitoring-source.htm)

---

## Worked Example (from the reference PoC)

### AuditConsumerFunction — SCH consumer with idempotency and distributed tracing
// from services/func-evt-consumer-audit/src/main/java/com/brx/functions/event/consumer/audit/AuditConsumerFunction.java

```java
public class AuditConsumerFunction extends ConnectorHubFunction<StreamingData<DomainEvent>> {

    private final Set<String> processedEventIds = ConcurrentHashMap.newKeySet();
    private String initError;

    @Override @FnConfiguration
    public void configure(RuntimeContext ctx) {
        super.configure(ctx);
        try {
            ObservabilityHelper.configure(ctx);
        } catch (Exception e) {
            this.initError = e.getClass().getName() + ": " + e.getMessage();
        }
    }

    @Override
    public void handler(ConnectorHubBatch<StreamingData<DomainEvent>> batch) {
        if (initError != null) {
            // Init failure is unrecoverable — signal 502 so SCH retries later.
            throw new RuntimeException("Function initialization failed: " + initError);
        }
        for (StreamingData<DomainEvent> record : batch.getBatch()) {
            processRecord(record);
        }
    }

    private void processRecord(StreamingData<DomainEvent> record) {
        DomainEvent e = record.getValue(); // auto base64-decode + Jackson deserialize
        String eventId = e.event_id();

        // Idempotency guard
        if (eventId != null && !processedEventIds.add(eventId)) {
            return; // already processed
        }

        String traceparent = e.trace != null ? e.trace.traceparent() : null;
        String tracestate  = e.trace != null ? e.trace.tracestate()  : null;

        // Re-parent into the producer's trace for distributed trace continuity
        Span span = ObservabilityHelper.startConsumerSpan("consume " + e.event_type(),
                traceparent, tracestate);
        try (Scope scope = span.makeCurrent()) {
            audit(e);
            ObservabilityHelper.endSpan(span, 200);
        } catch (Exception ex) {
            ObservabilityHelper.endSpan(span, ex);
            if (eventId != null) processedEventIds.remove(eventId);
            throw new RuntimeException("Failed to audit event " + eventId, ex);
        }
    }
}
```

Key patterns encoded here:
- `super.configure(ctx)` called first (required when extending fn-events base classes)
- `initError` pattern: catch in configure(), check at top of handler() → 502 for SCH retry
- `processedEventIds` set provides in-memory idempotency across warm invocations
- `startConsumerSpan(name, traceparent, tracestate)` re-parents the trace from the event envelope
- Per-record isolation: remove event from dedup set on error so SCH can retry that record

### DomainEvent envelope (shared contract)
// from libs/obs-commons/src/main/java/com/brx/functions/common/obs/DomainEvent.java

The `DomainEvent` type is the shared wire contract between producers and consumers:
- `event_type` = Streaming key (partitioning)
- `trace.traceparent` / `trace.tracestate` = W3C context for distributed tracing
- Used unchanged on both producer side (`func-event-producer`) and consumer side (`func-evt-consumer-audit`, `func-evt-consumer-notify`)

