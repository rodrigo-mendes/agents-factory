package com.brx.functions.common.obs;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * The canonical event envelope carried on the OCI Streaming topic {@code event-stream}.
 *
 * <p>Serialization rules (must match the Terraform / SCH contract):
 * <ul>
 *   <li>The full JSON of this object is the message <b>VALUE</b>.</li>
 *   <li>The message <b>KEY</b> is {@link #event_type} (partitioning / ordering).</li>
 *   <li>{@link #trace} carries the W3C trace context <em>through</em> the stream so producer and
 *       consumers share one distributed trace.</li>
 * </ul>
 * NEVER Base64-encode this manually — the OCI SDK / FDK handles wire encoding on both sides.
 *
 * <p>Accessors use record-style names ({@code event_id()}, {@code event_type()}, …) and the
 * {@link #trace} field is public so consumers read {@code e.trace.traceparent()} directly. The type
 * is {@code @JsonIgnoreProperties(ignoreUnknown = true)} for forward compatibility.
 *
 * <p>Shared across the 3 pub/sub services via {@code brx-fn-obs-commons}: producer and consumers use
 * the ONE envelope type so the wire contract (field names, trace node) cannot diverge between sides.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@JsonIgnoreProperties(ignoreUnknown = true)
public class DomainEvent {

    @JsonProperty("event_id")
    private String eventId;

    @JsonProperty("event_type")
    private String eventType;

    @JsonProperty("payload")
    private Object payload;

    @JsonProperty("correlation_id")
    private String correlationId;

    @JsonProperty("transaction_id")
    private String transactionId;

    @JsonProperty("timestamp")
    private String timestamp;

    @JsonProperty("trace")
    public Trace trace;

    /** W3C trace context propagated inside the event. {@code tracestate} is nullable. */
    @JsonInclude(JsonInclude.Include.NON_NULL)
    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Trace(
            @JsonProperty("traceparent") String traceparent,
            @JsonProperty("tracestate") String tracestate) {
    }

    public DomainEvent() {
    }

    public DomainEvent(String eventId, String eventType, Object payload, String correlationId,
                       String transactionId, String timestamp, Trace trace) {
        this.eventId = eventId;
        this.eventType = eventType;
        this.payload = payload;
        this.correlationId = correlationId;
        this.transactionId = transactionId;
        this.timestamp = timestamp;
        this.trace = trace;
    }

    // Record-style accessors (read side)
    public String event_id() { return eventId; }
    public String event_type() { return eventType; }
    public Object payload() { return payload; }
    public String correlation_id() { return correlationId; }
    public String transaction_id() { return transactionId; }
    public String timestamp() { return timestamp; }
    public Trace trace() { return trace; }

    // JavaBean getters (Jackson serialization on the producer side reuses the @JsonProperty above,
    // but explicit getters keep the type usable from frameworks expecting bean accessors).
    public String getEventId() { return eventId; }
    public String getEventType() { return eventType; }
    public Object getPayload() { return payload; }
    public String getCorrelationId() { return correlationId; }
    public String getTransactionId() { return transactionId; }
    public String getTimestamp() { return timestamp; }
    public Trace getTrace() { return trace; }

    public void setTrace(Trace trace) { this.trace = trace; }
}
