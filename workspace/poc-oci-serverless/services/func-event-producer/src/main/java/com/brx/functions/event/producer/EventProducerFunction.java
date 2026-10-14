package com.brx.functions.event.producer;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

import com.brx.functions.common.obs.DomainEvent;
import com.brx.functions.common.obs.ObservabilityHelper;
import com.brx.functions.common.obs.TracingSupport.TraceContext;
import com.brx.functions.event.producer.client.StreamPublisher;
import com.brx.functions.event.producer.client.StreamPublisher.StreamPublishException;
import com.brx.functions.event.producer.model.ProducerResponse;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fnproject.events.APIGatewayFunction;
import com.fnproject.events.input.APIGatewayRequestEvent;
import com.fnproject.events.output.APIGatewayResponseEvent;
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.Headers;
import com.fnproject.fn.api.RuntimeContext;
import com.oracle.bmc.ClientConfiguration;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.streaming.StreamClient;

import io.opentelemetry.api.trace.Span;
import io.opentelemetry.context.Scope;

/**
 * API Gateway entry point for the event pub/sub pattern. Accepts a POST body describing an event,
 * builds a {@link DomainEvent}, <b>injects the W3C trace context into the event</b> so consumers
 * join the same distributed trace, publishes it to OCI Streaming ({@code event-stream}) with
 * {@code key = event_type}, verifies per-message delivery, and responds 202.
 *
 * <p>Cold-start init lives in {@link #configure}; the handler reads as a sequence of named steps.
 */
public class EventProducerFunction extends APIGatewayFunction<String, ProducerResponse> {

    private static final Logger log = LoggerFactory.getLogger(EventProducerFunction.class);
    private static final String STREAM_NAME = "event-stream";
    private static final String VERSION = "0.0.2";

    // SDK timeouts MUST stay BELOW the 60s function timeout (func.yaml). The SDK default read timeout
    // is 60s (== fn timeout) — the platform would kill the invocation mid-PutMessages with no cleanup.
    private static final int SDK_CONNECT_TIMEOUT_MS = 5_000;
    private static final int SDK_READ_TIMEOUT_MS = 15_000;

    // Config-key NAMES surfaced by GET /health|/diag (names only — values are never exposed).
    private static final List<String> CONFIG_KEY_NAMES = List.of(
            "ENVIRONMENT", "SERVICE_NAME", "METRIC_NAMESPACE", "COMPARTMENT_OCID",
            "APM_DOMAIN_URL", "APM_DATA_KEY", "STREAM_OCID", "STREAM_MESSAGES_ENDPOINT");

    private ObjectMapper objectMapper;
    private StreamClient streamClient;
    private StreamPublisher publisher;
    private boolean coldStart = true;
    private String initError;

    public EventProducerFunction() {
    }

    // Package-private constructor for testing (bypasses Resource Principal / SDK init).
    EventProducerFunction(ObjectMapper objectMapper, StreamPublisher publisher) {
        this.objectMapper = objectMapper;
        this.publisher = publisher;
    }

    // ── Cold-start initialization ────────────────────────────────────────────────────────────

    @Override
    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        super.configure(ctx);
        try {
            long start = System.currentTimeMillis();
            ObservabilityHelper.configure(ctx);
            this.objectMapper = new ObjectMapper();

            Span cold = ObservabilityHelper.startRootSpan("ColdStart func-event-producer");
            try (Scope scope = cold.makeCurrent()) {
                String streamId = ctx.getConfigurationByKey("STREAM_OCID")
                        .orElseThrow(() -> new IllegalStateException("STREAM_OCID is required"));
                String messagesEndpoint = ctx.getConfigurationByKey("STREAM_MESSAGES_ENDPOINT")
                        .orElseThrow(() -> new IllegalStateException("STREAM_MESSAGES_ENDPOINT is required"));

                ResourcePrincipalAuthenticationDetailsProvider provider =
                        ResourcePrincipalAuthenticationDetailsProvider.builder().build();
                // Cap SDK read/connect timeouts BELOW the 60s function timeout so a slow/hung
                // PutMessages fails fast inside the invocation instead of the platform killing it.
                ClientConfiguration clientConfig = ClientConfiguration.builder()
                        .connectionTimeoutMillis(SDK_CONNECT_TIMEOUT_MS)
                        .readTimeoutMillis(SDK_READ_TIMEOUT_MS)
                        .build();
                this.streamClient = StreamClient.builder()
                        .endpoint(messagesEndpoint)
                        .configuration(clientConfig)
                        .build(provider);
                this.publisher = new StreamPublisher(streamClient, streamId);

                log.info("EventProducerFunction COLD_START completed in {}ms | stream endpoint set",
                        System.currentTimeMillis() - start);
                ObservabilityHelper.endSpan(cold, 200);
            } catch (Exception e) {
                ObservabilityHelper.endSpan(cold, e);
                throw e;
            }
        } catch (Exception e) {
            this.initError = e.getClass().getName() + ": " + e.getMessage();
            log.error("COLD_START INIT FAILED: {}", initError, e);
        }
    }

    // ── Request handling ─────────────────────────────────────────────────────────────────────

    @Override
    public APIGatewayResponseEvent<ProducerResponse> handler(APIGatewayRequestEvent<String> req) {
        long startTime = System.currentTimeMillis();
        boolean isColdStart = coldStart;
        coldStart = false;

        String method = req.getMethod();
        String path = req.getRequestUrl();
        MDC.put("method", method);
        MDC.put("coldStart", String.valueOf(isColdStart));
        log.info("INVOKE {} {} | coldStart={}", method, path, isColdStart);

        try {
            // Diagnostic endpoint — reachable even when init failed, so the health check can REPORT
            // initError (never the config VALUES). Kept before the initError gate on purpose.
            if (isDiagRequest(method, path)) {
                return respond(200, ProducerResponse.diagnostic(initError, VERSION, CONFIG_KEY_NAMES),
                        startTime, isColdStart);
            }

            if (initError != null) {
                log.error("Aborting invocation due to prior initialization failure: {}", initError);
                return respond(500, ProducerResponse.error("Function initialization failed", initError),
                        startTime, isColdStart);
            }

            if (!"POST".equalsIgnoreCase(method)) {
                return respond(405, ProducerResponse.error("Method Not Allowed",
                        "Only POST is supported"), startTime, isColdStart);
            }

            JsonNode body = parseBody(req.getBody());
            String eventType = textOrNull(body, "event_type");
            if (eventType == null || eventType.isBlank()) {
                return respond(400, ProducerResponse.error("Bad Request", "event_type is required"),
                        startTime, isColdStart);
            }

            return publishEvent(body, eventType, startTime, isColdStart);

        } catch (StreamPublishException e) {
            log.error("Streaming publish failed: {}", e.getMessage(), e);
            return respond(503, ProducerResponse.error("Service Unavailable",
                    e.getClass().getName() + ": " + e.getMessage()), startTime, isColdStart);
        } catch (Exception e) {
            log.error("Unexpected error: {}", e.getMessage(), e);
            return respond(500, ProducerResponse.error("Internal server error",
                    e.getClass().getName() + ": " + e.getMessage()), startTime, isColdStart);
        } finally {
            MDC.clear();
        }
    }

    /**
     * Builds the DomainEvent, injects the trace context inside the active SERVER span scope, and
     * publishes it. Kept as a single step so the trace injection and the publish share one span.
     */
    private APIGatewayResponseEvent<ProducerResponse> publishEvent(JsonNode body, String eventType,
            long startTime, boolean isColdStart) throws Exception {
        String eventId = UUID.randomUUID().toString();
        String transactionId = UUID.randomUUID().toString();
        String correlationId = textOrNull(body, "correlation_id");
        String timestamp = Instant.now().toString();
        JsonNode payload = body.has("payload") ? body.get("payload") : null;

        Span span = ObservabilityHelper.startSpan("POST", "/events", null);
        try (Scope scope = span.makeCurrent()) {
            // Inject the ACTIVE span's W3C context so it travels inside the event to the consumers.
            TraceContext trace = ObservabilityHelper.injectTraceContext();
            DomainEvent event = new DomainEvent(eventId, eventType, payload, correlationId,
                    transactionId, timestamp, new DomainEvent.Trace(trace.traceparent(), trace.tracestate()));

            String json = objectMapper.writeValueAsString(event);
            publisher.publish(eventType, json); // key = event_type, value = UTF-8 JSON

            ObservabilityHelper.setEventAttributes(span, transactionId, correlationId, eventId, eventType);
            ObservabilityHelper.endSpan(span, 202);

            log.info("PUBLISHED event | event_id={} | event_type={} | transaction_id={}",
                    eventId, eventType, transactionId);
            return respond(202, ProducerResponse.accepted(eventId, transactionId, STREAM_NAME),
                    startTime, isColdStart);
        } catch (Exception e) {
            ObservabilityHelper.endSpan(span, e);
            throw e;
        }
    }

    /**
     * True for GET {@code /health} or {@code /diag}. {@code getRequestUrl()} may return a bare path or
     * a full URL (optionally with a query string), so the query is stripped and the path is matched by
     * suffix to tolerate the API Gateway deployment prefix.
     */
    private static boolean isDiagRequest(String method, String path) {
        if (!"GET".equalsIgnoreCase(method) || path == null) {
            return false;
        }
        int q = path.indexOf('?');
        String p = q >= 0 ? path.substring(0, q) : path;
        return p.equals("/health") || p.equals("/diag")
                || p.endsWith("/health") || p.endsWith("/diag");
    }

    private JsonNode parseBody(String rawBody) throws Exception {
        if (rawBody == null || rawBody.isBlank()) {
            return objectMapper.createObjectNode();
        }
        return objectMapper.readTree(rawBody);
    }

    private static String textOrNull(JsonNode node, String field) {
        JsonNode value = node.get(field);
        return value != null && !value.isNull() ? value.asText() : null;
    }

    private APIGatewayResponseEvent<ProducerResponse> respond(int status, ProducerResponse body,
            long startTime, boolean isColdStart) {
        long elapsed = System.currentTimeMillis() - startTime;
        body.setElapsedMs(elapsed);
        body.setColdStart(isColdStart);
        log.info("COMPLETE POST /events | status={} | elapsed={}ms", status, elapsed);
        return new APIGatewayResponseEvent.Builder<ProducerResponse>()
                .statusCode(status)
                .headers(Headers.emptyHeaders().addHeader("Content-Type", "application/json"))
                .body(body)
                .build();
    }
}
