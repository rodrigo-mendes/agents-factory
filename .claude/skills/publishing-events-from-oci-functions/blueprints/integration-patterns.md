## Integration Patterns

### OCI Functions ↔ OCI Streaming

**Official Module**: `oci-java-sdk-streaming` (via BOM)
**Compatibility**: OCI Java SDK v2.0+ / Streaming API v20180418

**Required Configuration**:
```yaml
# func.yaml or application config
STREAM_ENDPOINT: "https://cell-1.streaming.us-ashburn-1.oci.oraclecloud.com"
STREAM_OCID: "ocid1.stream.oc1.iad.xxx"
```

**IAM Policy**:
```
allow dynamic-group <dg-name> to use stream-push in compartment <compartment>
```

**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/streaming/20180418/

### OCI Functions ↔ OCI Notifications (ONS)

**Official Module**: `oci-java-sdk-ons` (via BOM)
**Compatibility**: OCI Java SDK v2.0+ / Notifications API v20181201

**Required Configuration**:
```yaml
NOTIFICATION_ENDPOINT: "https://notification.us-ashburn-1.oraclecloud.com"
TOPIC_OCID: "ocid1.onstopic.oc1.iad.xxx"
```

**IAM Policy**:
```
allow dynamic-group <dg-name> to use ons-topics in compartment <compartment>
```

**Rate Limit**: 60 TPM per topic — aggregate multiple events into a single notification for high-volume scenarios.

**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/notification/20181201/

### OCI Functions ↔ OCI Queue

**Official Module**: `oci-java-sdk-queue` (via BOM)
**Compatibility**: OCI Java SDK v3.0+ / Queue API v20210201

**Required Configuration**:
```yaml
QUEUE_OCID: "ocid1.queue.oc1.iad.xxx"
```

**IAM Policy**:
```
allow dynamic-group <dg-name> to use queues in compartment <compartment>
```

**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/queue/20210201/

### OCI Functions ↔ OCI Monitoring

**Official Module**: `oci-java-sdk-monitoring` (via BOM)
**Compatibility**: OCI Java SDK v2.0+ / Monitoring API v20180401

**Required Configuration**:
```yaml
# ⚠️ Must use telemetry-ingestion, NOT telemetry
MONITORING_ENDPOINT: "https://telemetry-ingestion.us-ashburn-1.oraclecloud.com"
MONITORING_COMPARTMENT: "ocid1.compartment.oc1..xxx"
```

**IAM Policy**:
```
allow dynamic-group <dg-name> to use metrics in compartment <compartment>
```

**Constraints**: Max 50 unique metric streams per request, max 20 dimensions per metric.

**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/monitoring/20180401/

### OCI Functions ↔ OCI Logging

**Official Module**: `oci-java-sdk-loggingingestion` (via BOM)
**Compatibility**: OCI Java SDK v2.0+ / Logging Ingestion API v20200831

**Required Configuration**:
```yaml
LOG_OCID: "ocid1.log.oc1.iad.xxx"
```

**IAM Policy**:
```
allow dynamic-group <dg-name> to use log-content in compartment <compartment>
```

**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/logging-dataplane/20200831/

---

## Worked Example (from the reference PoC)

### DomainEvent envelope contract
// from libs/obs-commons/src/main/java/com/example/functions/common/obs/DomainEvent.java

```java
@JsonInclude(JsonInclude.Include.NON_NULL)
@JsonIgnoreProperties(ignoreUnknown = true)
public class DomainEvent {
    @JsonProperty("event_id")   private String eventId;
    @JsonProperty("event_type") private String eventType;
    @JsonProperty("payload")    private Object payload;
    @JsonProperty("correlation_id") private String correlationId;
    @JsonProperty("transaction_id") private String transactionId;
    @JsonProperty("timestamp")  private String timestamp;
    @JsonProperty("trace")      public Trace trace;

    /** W3C trace context propagated inside the event. tracestate is nullable. */
    public record Trace(
            @JsonProperty("traceparent") String traceparent,
            @JsonProperty("tracestate") String tracestate) {}
    // ... constructors and record-style accessors omitted for brevity
}
```

Key rules encoded in this class:
- `event_type` is the Streaming message **key** (partitioning / ordering)
- `trace` carries W3C traceparent so producer and consumers share one distributed trace
- `@JsonIgnoreProperties(ignoreUnknown = true)` for forward compatibility
- Never Base64-encode manually — SDK handles wire encoding

### StreamPublisher — verified delivery check
// from services/func-event-producer/src/main/java/com/example/functions/event/producer/client/StreamPublisher.java

```java
public void publish(String key, String json) {
    PutMessagesDetailsEntry entry = PutMessagesDetailsEntry.builder()
            .key(key.getBytes(UTF_8))
            .value(json.getBytes(UTF_8))
            .build();

    PutMessagesResponse response = streamClient.putMessages(
            PutMessagesRequest.builder()
                    .streamId(streamId)
                    .putMessagesDetails(PutMessagesDetails.builder()
                            .messages(List.of(entry)).build())
                    .build());

    // CRITICAL: HTTP 200 != all messages succeeded. Inspect every entry.
    int failed = 0;
    for (PutMessagesResultEntry resultEntry : response.getPutMessagesResult().getEntries()) {
        if (resultEntry.getError() != null) {
            failed++;
        }
    }
    if (failed > 0) {
        throw new StreamPublishException(failed + " message(s) failed to publish");
    }
}
```

### EventProducerFunction — trace context injection before publish
// from services/func-event-producer/src/main/java/com/example/functions/event/producer/EventProducerFunction.java

```java
Span span = ObservabilityHelper.startSpan("POST", "/events", null);
try (Scope scope = span.makeCurrent()) {
    // Inject the ACTIVE span's W3C context so it travels inside the event to the consumers.
    TraceContext trace = ObservabilityHelper.injectTraceContext();
    DomainEvent event = new DomainEvent(eventId, eventType, payload, correlationId,
            transactionId, timestamp,
            new DomainEvent.Trace(trace.traceparent(), trace.tracestate()));

    String json = objectMapper.writeValueAsString(event);
    publisher.publish(eventType, json); // key = event_type, value = UTF-8 JSON
}
```

