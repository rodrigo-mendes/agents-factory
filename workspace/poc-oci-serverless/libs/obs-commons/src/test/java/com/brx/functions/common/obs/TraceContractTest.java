package com.brx.functions.common.obs;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import java.util.HashMap;
import java.util.Map;

import org.junit.Test;

import com.fasterxml.jackson.databind.ObjectMapper;

import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.SpanContext;
import io.opentelemetry.api.trace.TraceFlags;
import io.opentelemetry.api.trace.TraceState;
import io.opentelemetry.api.trace.propagation.W3CTraceContextPropagator;
import io.opentelemetry.context.Context;
import io.opentelemetry.context.propagation.TextMapGetter;

/**
 * Contract guard for the distributed-trace propagation shared across the 3 pub/sub services.
 *
 * <p>The producer injects the active span's W3C context, that context rides <em>inside</em> the
 * {@link DomainEvent} (serialize), and each consumer extracts it and re-parents its span onto that
 * remote context. If any single byte of that contract drifts — the carrier keys ({@code traceparent}
 * / {@code tracestate}), the {@link W3CTraceContextPropagator}, or the {@link DomainEvent.Trace}
 * field names — the consumer silently starts a NEW trace and the producer→stream→consumers trace
 * breaks. Consolidating the classes into {@code brx-fn-obs-commons} makes that a single source; this
 * test is the executable proof that the round-trip <em>inject → serialize → extract</em> yields the
 * SAME trace id and parent span id.
 */
public class TraceContractTest {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    // A concrete, known W3C traceparent (version-traceId-spanId-flags) as the producer would emit.
    private static final String TRACE_ID = "0af7651916cd43dd8448eb211c80319c";
    private static final String SPAN_ID = "b7ad6b7169203331";
    private static final String TRACEPARENT = "00-" + TRACE_ID + "-" + SPAN_ID + "-01";
    // W3C tracestate keys must be lowercase per the spec — the propagator drops malformed entries.
    private static final String TRACESTATE = "vendora=t61rcWkgMzE,vendorb=1";

    // Same getter TracingSupport uses to read a carrier during extract().
    private static final TextMapGetter<Map<String, String>> CARRIER_GETTER = new TextMapGetter<>() {
        @Override
        public String get(Map<String, String> carrier, String key) {
            return carrier == null ? null : carrier.get(key);
        }

        @Override
        public Iterable<String> keys(Map<String, String> carrier) {
            return carrier.keySet();
        }
    };

    /**
     * Full producer→wire→consumer round-trip: a producer span's W3C context is injected into a
     * carrier, carried inside a serialized {@link DomainEvent}, then extracted on the consumer side.
     * The extracted parent MUST have the identical traceId and spanId — i.e. the consumer span
     * re-parents onto the producer span (no drift).
     */
    @Test
    public void injectSerializeExtract_yieldsSameTraceAndParentSpanIds() throws Exception {
        // ── Producer side: make the known span "current" and inject via the W3C propagator ──
        SpanContext producerSpanCtx = SpanContext.create(
                TRACE_ID, SPAN_ID, TraceFlags.getSampled(),
                TraceState.builder().put("vendora", "t61rcWkgMzE").put("vendorb", "1").build());
        Context producerContext = Context.root().with(Span.wrap(producerSpanCtx));

        Map<String, String> injected = new HashMap<>();
        W3CTraceContextPropagator.getInstance().inject(producerContext, injected, Map::put);

        assertEquals("producer must inject a traceparent for the known span",
                TRACEPARENT, injected.get("traceparent"));

        // ── Wire: the trace context travels INSIDE the DomainEvent (serialize → JSON → deserialize) ──
        DomainEvent produced = new DomainEvent("evt-1", "order.created", null, "corr-1", "txn-1",
                "2026-07-22T00:00:00Z",
                new DomainEvent.Trace(injected.get("traceparent"), injected.get("tracestate")));
        String json = MAPPER.writeValueAsString(produced);
        DomainEvent consumed = MAPPER.readValue(json, DomainEvent.class);

        assertNotNull("trace node must survive serialization", consumed.trace);
        assertEquals("traceparent must survive the wire unchanged",
                TRACEPARENT, consumed.trace.traceparent());

        // ── Consumer side: extract the remote context from the event's carrier and re-parent ──
        Map<String, String> carrier = new HashMap<>();
        carrier.put("traceparent", consumed.trace.traceparent());
        if (consumed.trace.tracestate() != null) {
            carrier.put("tracestate", consumed.trace.tracestate());
        }
        Context extracted = W3CTraceContextPropagator.getInstance()
                .extract(Context.root(), carrier, CARRIER_GETTER);
        SpanContext extractedParent = Span.fromContext(extracted).getSpanContext();

        // THE GUARD: identical trace id and parent span id → the consumer joins the producer trace.
        assertTrue("extracted parent context must be valid", extractedParent.isValid());
        assertEquals("traceId must be identical (same distributed trace)",
                producerSpanCtx.getTraceId(), extractedParent.getTraceId());
        assertEquals("parent spanId must be identical (consumer re-parents onto producer span)",
                producerSpanCtx.getSpanId(), extractedParent.getSpanId());
        assertTrue("sampled flag must be preserved across the round-trip",
                extractedParent.getTraceFlags().isSampled());
    }

    /**
     * tracestate must round-trip too — a consumer that drops it loses vendor context and can subtly
     * change sampling decisions downstream.
     */
    @Test
    public void tracestate_survivesInjectSerializeExtract() throws Exception {
        DomainEvent produced = new DomainEvent("evt-2", "inventory.updated", null, null, null,
                "2026-07-22T00:00:00Z", new DomainEvent.Trace(TRACEPARENT, TRACESTATE));
        DomainEvent consumed = MAPPER.readValue(MAPPER.writeValueAsString(produced), DomainEvent.class);

        Map<String, String> carrier = new HashMap<>();
        carrier.put("traceparent", consumed.trace.traceparent());
        carrier.put("tracestate", consumed.trace.tracestate());
        Context extracted = W3CTraceContextPropagator.getInstance()
                .extract(Context.root(), carrier, CARRIER_GETTER);
        SpanContext parent = Span.fromContext(extracted).getSpanContext();

        assertEquals(TRACE_ID, parent.getTraceId());
        assertEquals(SPAN_ID, parent.getSpanId());
        assertFalse("tracestate must be carried onto the extracted parent",
                parent.getTraceState().isEmpty());
    }

    /**
     * The DomainEvent trace node must serialize using the exact wire keys the consumers extract with
     * ({@code traceparent} / {@code tracestate}). Locks the field names against accidental renames.
     */
    @Test
    public void domainEventSerializesTraceWithW3cKeys() throws Exception {
        DomainEvent produced = new DomainEvent("evt-3", "order.created", null, null, null,
                "2026-07-22T00:00:00Z", new DomainEvent.Trace(TRACEPARENT, TRACESTATE));
        var node = MAPPER.readTree(MAPPER.writeValueAsString(produced));

        assertTrue("envelope must carry a trace node", node.has("trace"));
        assertEquals(TRACEPARENT, node.get("trace").get("traceparent").asText());
        assertEquals(TRACESTATE, node.get("trace").get("tracestate").asText());
    }

    /**
     * Tracer-off contract of the real {@link TracingSupport}: with no APM configured (the tracer is
     * never initialized), {@code injectTraceContext()} returns null ids rather than throwing, and
     * {@code startConsumerSpan(...)} returns an invalid (no-op) span. Callers rely on this so they can
     * invoke the trace APIs unconditionally in local/test runs.
     */
    @Test
    public void tracingSupport_isNoOpWhenTracerNotInitialized() {
        TracingSupport tracing = new TracingSupport(); // configure() never called → tracer stays null

        TracingSupport.TraceContext ctx = tracing.injectTraceContext();
        assertNotNull(ctx);
        assertNull("no traceparent when tracing is off", ctx.traceparent());
        assertNull("no tracestate when tracing is off", ctx.tracestate());

        Span consumerSpan = tracing.startConsumerSpan("consume order.created", TRACEPARENT, TRACESTATE);
        assertNotNull(consumerSpan);
        assertFalse("consumer span must be the invalid no-op span when tracing is off",
                consumerSpan.getSpanContext().isValid());
    }
}
