package com.brx.functions.event.consumer.audit;

import java.time.Instant;
import java.time.format.DateTimeParseException;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

import com.brx.functions.common.obs.DomainEvent;
import com.brx.functions.common.obs.ObservabilityHelper;
import com.fnproject.events.ConnectorHubFunction;
import com.fnproject.events.input.ConnectorHubBatch;
import com.fnproject.events.input.sch.StreamingData;
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;

import io.opentelemetry.api.trace.Span;
import io.opentelemetry.context.Scope;

/**
 * Service Connector Hub consumer that audits every {@code DomainEvent} on the {@code event-stream}:
 * it logs a structured audit record, then emits two custom metrics under the shared
 * {@code event_pubsub_analytics} namespace:
 * <ul>
 *   <li>{@code AuditEventProcessed} — count, dimension {@code event_type}</li>
 *   <li>{@code EventConsumeLagMs} — {@code now - event.timestamp} in ms, dimensions
 *       {@code consumer}, {@code event_type}</li>
 * </ul>
 * Each record joins the producer's distributed trace via {@code startConsumerSpan}. Processing is
 * idempotent (dedup by {@code event_id}) and per-record isolated; unrecoverable errors re-throw as
 * {@link RuntimeException} → 502 so SCH retries the batch.
 */
public class AuditConsumerFunction extends ConnectorHubFunction<StreamingData<DomainEvent>> {

    private static final Logger log = LoggerFactory.getLogger(AuditConsumerFunction.class);
    private static final String CONSUMER_NAME = "func-evt-consumer-audit";
    private static final String METRIC_AUDIT_PROCESSED = "AuditEventProcessed";
    private static final String METRIC_CONSUME_LAG_MS = "EventConsumeLagMs";

    private final Set<String> processedEventIds = ConcurrentHashMap.newKeySet();

    /** Sink for custom metrics — defaults to the OCI Monitoring facade; overridable in tests. */
    @FunctionalInterface
    interface MetricSink {
        void post(String name, double value, Map<String, String> dimensions);
    }

    private final MetricSink metrics;
    private String initError;

    public AuditConsumerFunction() {
        this.metrics = ObservabilityHelper::postMetric;
    }

    // Package-private constructor for testing — captures emitted metrics.
    AuditConsumerFunction(MetricSink metrics) {
        this.metrics = metrics;
    }

    @Override
    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        super.configure(ctx);
        try {
            long start = System.currentTimeMillis();
            ObservabilityHelper.configure(ctx);
            log.info("AuditConsumerFunction COLD_START completed in {}ms",
                    System.currentTimeMillis() - start);
        } catch (Exception e) {
            this.initError = e.getClass().getName() + ": " + e.getMessage();
            log.error("COLD_START INIT FAILED: {}", initError, e);
        }
    }

    @Override
    public void handler(ConnectorHubBatch<StreamingData<DomainEvent>> batch) {
        if (initError != null) {
            // Init failure is unrecoverable for this JVM — signal 502 so SCH retries later.
            throw new RuntimeException("Function initialization failed: " + initError);
        }

        int size = batch.getBatch() != null ? batch.getBatch().size() : 0;
        log.info("BATCH received | records={}", size);

        for (StreamingData<DomainEvent> record : batch.getBatch()) {
            processRecord(record);
        }
        log.info("BATCH complete | records={}", size);
    }

    /** Processes one record: dedup, re-parented CONSUMER span, audit log + metrics. Isolated. */
    private void processRecord(StreamingData<DomainEvent> record) {
        DomainEvent e = record.getValue(); // auto base64-decode + Jackson deserialize
        if (e == null) {
            log.warn("Skipping record with null value | partition={} | offset={}",
                    record.getPartition(), record.getOffset());
            return;
        }

        String eventId = e.event_id();
        if (eventId != null && !processedEventIds.add(eventId)) {
            log.info("DEDUP skip | event_id={} already processed", eventId);
            return;
        }

        MDC.put("eventId", eventId);
        MDC.put("eventType", e.event_type());
        String traceparent = e.trace != null ? e.trace.traceparent() : null;
        String tracestate = e.trace != null ? e.trace.tracestate() : null;

        Span span = ObservabilityHelper.startConsumerSpan("consume " + e.event_type(),
                traceparent, tracestate);
        try (Scope scope = span.makeCurrent()) {
            ObservabilityHelper.setEventAttributes(span, e.transaction_id(), e.correlation_id(),
                    eventId, e.event_type());

            audit(e);

            ObservabilityHelper.endSpan(span, 200);
        } catch (Exception ex) {
            ObservabilityHelper.endSpan(span, ex);
            if (eventId != null) {
                processedEventIds.remove(eventId);
            }
            log.error("AUDIT failed | event_id={} | {}", eventId, ex.getMessage(), ex);
            throw new RuntimeException("Failed to audit event " + eventId, ex);
        } finally {
            MDC.clear();
        }
    }

    /** Writes the structured audit log line and emits the two custom metrics. */
    private void audit(DomainEvent e) {
        String eventType = e.event_type();
        log.info("AUDIT event | event_id={} | event_type={} | correlation_id={} | transaction_id={} | timestamp={}",
                e.event_id(), eventType, e.correlation_id(), e.transaction_id(), e.timestamp());

        // AuditEventProcessed — count (dims: event_type; environment auto-added by MetricsPublisher)
        metrics.post(METRIC_AUDIT_PROCESSED, 1.0, Map.of(
                "event_type", nullSafe(eventType)));

        // EventConsumeLagMs — ms gauge (dims: consumer, event_type)
        long lagMs = computeLagMs(e.timestamp());
        if (lagMs >= 0) {
            metrics.post(METRIC_CONSUME_LAG_MS, (double) lagMs, Map.of(
                    "consumer", CONSUMER_NAME,
                    "event_type", nullSafe(eventType)));
        }
    }

    /** Milliseconds between the event timestamp (ISO-8601 UTC) and now; -1 when unparseable. */
    private long computeLagMs(String isoTimestamp) {
        if (isoTimestamp == null || isoTimestamp.isBlank()) {
            return -1;
        }
        try {
            long eventMs = Instant.parse(isoTimestamp).toEpochMilli();
            return Math.max(0, System.currentTimeMillis() - eventMs);
        } catch (DateTimeParseException ex) {
            log.warn("Unparseable event timestamp '{}' — skipping lag metric", isoTimestamp);
            return -1;
        }
    }

    private static String nullSafe(String v) {
        return v != null ? v : "unknown";
    }
}
