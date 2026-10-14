package com.brx.functions.event.consumer.notify;

import java.net.http.HttpClient;
import java.time.Duration;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

import com.brx.functions.common.obs.DomainEvent;
import com.brx.functions.common.obs.ObservabilityHelper;
import com.brx.functions.event.consumer.notify.client.NotifyClient;
import com.brx.functions.event.consumer.notify.obs.TracedCall;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fnproject.events.ConnectorHubFunction;
import com.fnproject.events.input.ConnectorHubBatch;
import com.fnproject.events.input.sch.StreamingData;
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;

import io.opentelemetry.api.trace.Span;
import io.opentelemetry.context.Scope;

/**
 * Service Connector Hub consumer that receives {@code StreamingData<DomainEvent>} batches from the
 * {@code event-stream} and forwards each event to {@code NOTIFY_TARGET_URL} (echo) via HTTP POST.
 *
 * <p>Each record joins the producer's distributed trace by extracting the W3C context carried in
 * the event ({@code startConsumerSpan}), then the HTTP forward is a CLIENT child span. Processing is
 * idempotent (dedup by {@code event_id}) and per-record isolated; an unrecoverable error re-throws
 * as {@link RuntimeException} → 502 so SCH retries the batch.
 */
public class NotifyConsumerFunction extends ConnectorHubFunction<StreamingData<DomainEvent>> {

    private static final Logger log = LoggerFactory.getLogger(NotifyConsumerFunction.class);
    private static final long HTTP_TIMEOUT_MS = 10_000L;

    private final Set<String> processedEventIds = ConcurrentHashMap.newKeySet();

    private ObjectMapper objectMapper;
    private NotifyClient notifyClient;
    private String initError;

    public NotifyConsumerFunction() {
    }

    // Package-private constructor for testing.
    NotifyConsumerFunction(ObjectMapper objectMapper, NotifyClient notifyClient) {
        this.objectMapper = objectMapper;
        this.notifyClient = notifyClient;
    }

    @Override
    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        super.configure(ctx);
        try {
            long start = System.currentTimeMillis();
            ObservabilityHelper.configure(ctx);
            this.objectMapper = new ObjectMapper();

            String targetUrl = ctx.getConfigurationByKey("NOTIFY_TARGET_URL")
                    .orElseThrow(() -> new IllegalStateException("NOTIFY_TARGET_URL is required"));
            HttpClient httpClient = HttpClient.newBuilder()
                    .version(HttpClient.Version.HTTP_1_1)
                    .connectTimeout(Duration.ofSeconds(5))
                    .build();
            this.notifyClient = new NotifyClient(httpClient, targetUrl, HTTP_TIMEOUT_MS);

            log.info("NotifyConsumerFunction COLD_START completed in {}ms | target set",
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

    /** Processes one record: dedup, re-parented CONSUMER span, forward. Isolated per record. */
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

            forward(e);

            ObservabilityHelper.endSpan(span, 200);
            log.info("FORWARDED event | event_id={} | event_type={}", eventId, e.event_type());
        } catch (Exception ex) {
            ObservabilityHelper.endSpan(span, ex);
            // Roll back dedup so a retry can re-process this event.
            if (eventId != null) {
                processedEventIds.remove(eventId);
            }
            log.error("FORWARD failed | event_id={} | {}", eventId, ex.getMessage(), ex);
            throw new RuntimeException("Failed to forward event " + eventId, ex);
        } finally {
            MDC.clear();
        }
    }

    /** Serializes and POSTs the event to the notify target inside a CLIENT child span. */
    private void forward(DomainEvent e) throws Exception {
        String json = objectMapper.writeValueAsString(e);
        TracedCall.run("NotifyTarget.forward", "notify-target", () -> notifyClient.forward(json));
    }
}
