package com.brx.functions.common.obs;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

import com.fnproject.fn.api.RuntimeContext;

import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.SpanContext;
import io.opentelemetry.api.trace.SpanKind;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.api.trace.propagation.W3CTraceContextPropagator;
import io.opentelemetry.context.Context;
import io.opentelemetry.context.propagation.ContextPropagators;
import io.opentelemetry.context.propagation.TextMapGetter;
import io.opentelemetry.exporter.otlp.http.trace.OtlpHttpSpanExporter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;

/**
 * Distributed tracing support (OpenTelemetry → OCI APM via OTLP/HTTP).
 *
 * <p>The OTel SDK is initialized eagerly in {@link #configure} (cold start) when APM is configured,
 * and spans are exported <em>synchronously</em> on {@code span.end()} via {@link SimpleSpanProcessor}.
 * This is the correct serverless pattern: OCI Functions freeze the container the moment the handler
 * returns, so a {@code BatchSpanProcessor}'s background export thread would never run and spans would
 * never reach APM. When APM is not configured the tracer stays null and all methods degrade to no-ops
 * ({@link Span#getInvalid()}), so callers can invoke start/end unconditionally.
 *
 * <p>For the event pub/sub pattern this class also carries the W3C trace context <em>through the
 * stream message</em> (not just HTTP headers): the producer calls {@link #injectTraceContext()}
 * to capture {@code traceparent}/{@code tracestate} from the active span, and each consumer calls
 * {@link #startConsumerSpan(String, String, String)} to re-parent its span onto that remote
 * context — making producer and consumers a single distributed trace.
 *
 * <p>Shared across the 3 pub/sub services via {@code brx-fn-obs-commons}: keeping the W3C
 * inject/extract contract in ONE place is what guarantees the trace cannot drift between the
 * producer and the consumers (a single byte of drift silently breaks re-parenting).
 */
public class TracingSupport {

    private static final Logger log = LoggerFactory.getLogger(TracingSupport.class);

    private volatile Tracer tracer;
    private volatile String environment = "dev";
    // APM config captured at configure() time; OTel SDK initialized eagerly in configure() when
    // present. ensureInitialized() remains a cheap idempotent guard (lazy fallback) for the span APIs.
    private volatile String pendingApmUrl;
    private volatile String pendingApmDataKey;
    private volatile String pendingApmServiceName;

    /** W3C trace context extracted from a span for propagation inside a stream message. */
    public record TraceContext(String traceparent, String tracestate) {
    }

    public void configure(RuntimeContext ctx, String environment) {
        this.environment = environment;
        this.pendingApmUrl = ctx.getConfigurationByKey("APM_DOMAIN_URL").orElse(null);
        this.pendingApmDataKey = ctx.getConfigurationByKey("APM_DATA_KEY").orElse(null);
        this.pendingApmServiceName = ctx.getConfigurationByKey("SERVICE_NAME").orElse("func-event-pubsub");
        if (pendingApmUrl != null && !pendingApmUrl.isBlank() && pendingApmDataKey != null && !pendingApmDataKey.isBlank()) {
            // Init eagerly at cold start (off the request path). Building the exporter makes no
            // network call — export is deferred to span.end() — so this adds no cold-start latency.
            initOpenTelemetry(pendingApmUrl, pendingApmDataKey, pendingApmServiceName);
        } else {
            log.info("APM_DOMAIN_URL or APM_DATA_KEY not configured — OTel tracing disabled");
        }
    }

    private void initOpenTelemetry(String apmDomainUrl, String apmDataKey, String serviceName) {
        try {
            String otlpEndpoint = apmDomainUrl.replaceAll("/$", "")
                    + "/20200101/opentelemetry/private/v1/traces";

            OtlpHttpSpanExporter exporter = OtlpHttpSpanExporter.builder()
                    .setEndpoint(otlpEndpoint)
                    .addHeader("Authorization", "dataKey " + apmDataKey)
                    .setTimeout(Duration.ofSeconds(5))
                    .build();

            Resource resource = Resource.getDefault()
                    .merge(Resource.create(Attributes.of(
                            AttributeKey.stringKey("service.name"), serviceName,
                            AttributeKey.stringKey("deployment.environment"), environment
                    )));

            SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
                    .addSpanProcessor(SimpleSpanProcessor.create(exporter))
                    .setResource(resource)
                    .build();

            OpenTelemetrySdk sdk = OpenTelemetrySdk.builder()
                    .setTracerProvider(tracerProvider)
                    .setPropagators(ContextPropagators.create(W3CTraceContextPropagator.getInstance()))
                    .buildAndRegisterGlobal();

            tracer = sdk.getTracer(serviceName, "1.0.0");
            log.info("OpenTelemetry initialized | endpoint={} | service={}", otlpEndpoint, serviceName);
        } catch (Exception e) {
            log.warn("OpenTelemetry init failed — tracing disabled: {}", e.getMessage());
        }
    }

    /**
     * Idempotent guard for the span APIs: init normally runs eagerly in {@link #configure}, so this
     * is a no-op when the tracer is already set. It doubles as a lazy fallback (double-checked,
     * thread-safe) should a span be requested before configure() completed.
     */
    private void ensureInitialized() {
        if (tracer == null && pendingApmUrl != null && pendingApmDataKey != null) {
            synchronized (this) {
                if (tracer == null) {
                    initOpenTelemetry(pendingApmUrl, pendingApmDataKey, pendingApmServiceName);
                }
            }
        }
    }

    public Span startSpan(String method, String route, String traceparent) {
        // Idempotent guard: init normally ran in configure(); this is a no-op fallback.
        ensureInitialized();
        if (tracer == null) return Span.getInvalid();
        try {
            Context parentContext = Context.current();
            if (traceparent != null && !traceparent.isBlank()) {
                Map<String, String> carrier = Map.of("traceparent", traceparent);
                parentContext = GlobalOpenTelemetry.getPropagators()
                        .getTextMapPropagator()
                        .extract(Context.current(), carrier, new TextMapGetter<>() {
                            @Override
                            public String get(Map<String, String> c, String key) {
                                return c.get(key);
                            }
                            @Override
                            public Iterable<String> keys(Map<String, String> c) {
                                return c.keySet();
                            }
                        });
            }

            Span span = tracer.spanBuilder(method + " " + route)
                    .setParent(parentContext)
                    .setSpanKind(SpanKind.SERVER)
                    .setAttribute("http.method", method)
                    .setAttribute("http.route", route)
                    .startSpan();

            SpanContext spanCtx = span.getSpanContext();
            MDC.put("traceId", spanCtx.getTraceId());
            MDC.put("spanId", spanCtx.getSpanId());

            return span;
        } catch (Exception e) {
            log.debug("startSpan failed: {}", e.getMessage());
            return Span.getInvalid();
        }
    }

    /**
     * Starts a parentless INTERNAL root span (e.g. to wrap cold-start init). Uses the same idempotent
     * init guard as {@link #startSpan} so init-time child spans can nest under it. Returns
     * {@link Span#getInvalid()} when tracing is off.
     */
    public Span startRootSpan(String name) {
        ensureInitialized();
        if (tracer == null) return Span.getInvalid();
        try {
            Span span = tracer.spanBuilder(name)
                    .setNoParent()
                    .setSpanKind(SpanKind.INTERNAL)
                    .startSpan();

            SpanContext spanCtx = span.getSpanContext();
            MDC.put("traceId", spanCtx.getTraceId());
            MDC.put("spanId", spanCtx.getSpanId());

            return span;
        } catch (Exception e) {
            log.debug("startRootSpan failed: {}", e.getMessage());
            return Span.getInvalid();
        }
    }

    public Span startChildSpan(String name) {
        if (tracer == null) return Span.getInvalid();
        try {
            return tracer.spanBuilder(name)
                    .setParent(Context.current())
                    .setSpanKind(SpanKind.CLIENT)
                    .startSpan();
        } catch (Exception e) {
            log.debug("startChildSpan failed: {}", e.getMessage());
            return Span.getInvalid();
        }
    }

    // ── Cross-stream trace propagation ──────────────────────────────────────────────────────────

    /**
     * Injects the W3C trace context of the <em>currently active</em> span into a carrier and returns
     * it as a {@link TraceContext}. The producer calls this inside its SERVER span scope so the
     * resulting {@code traceparent}/{@code tracestate} can travel inside the stream message and let
     * consumers join the same distributed trace. Returns {@code (null, null)} when tracing is off.
     */
    public TraceContext injectTraceContext() {
        if (tracer == null) {
            return new TraceContext(null, null);
        }
        try {
            Map<String, String> carrier = new HashMap<>();
            GlobalOpenTelemetry.getPropagators()
                    .getTextMapPropagator()
                    .inject(Context.current(), carrier, Map::put);
            return new TraceContext(carrier.get("traceparent"), carrier.get("tracestate"));
        } catch (Exception e) {
            log.debug("injectTraceContext failed: {}", e.getMessage());
            return new TraceContext(null, null);
        }
    }

    /**
     * Starts a CONSUMER span re-parented onto the remote trace context carried in the stream message.
     * The span becomes a child of the producer's span (same {@code TraceId}), completing the
     * distributed trace across the stream. MDC is primed with the resulting traceId/spanId. Returns
     * {@link Span#getInvalid()} when tracing is off.
     *
     * @param name        span name (e.g. {@code "consume order.created"})
     * @param traceparent W3C {@code traceparent} from the event envelope (may be null)
     * @param tracestate  W3C {@code tracestate} from the event envelope (may be null)
     */
    public Span startConsumerSpan(String name, String traceparent, String tracestate) {
        ensureInitialized();
        if (tracer == null) return Span.getInvalid();
        try {
            Context parentContext = Context.current();
            if (traceparent != null && !traceparent.isBlank()) {
                Map<String, String> carrier = new HashMap<>();
                carrier.put("traceparent", traceparent);
                if (tracestate != null && !tracestate.isBlank()) {
                    carrier.put("tracestate", tracestate);
                }
                parentContext = GlobalOpenTelemetry.getPropagators()
                        .getTextMapPropagator()
                        .extract(Context.current(), carrier, new TextMapGetter<>() {
                            @Override
                            public String get(Map<String, String> c, String key) {
                                return c.get(key);
                            }
                            @Override
                            public Iterable<String> keys(Map<String, String> c) {
                                return c.keySet();
                            }
                        });
            }

            Span span = tracer.spanBuilder(name)
                    .setParent(parentContext)
                    .setSpanKind(SpanKind.CONSUMER)
                    .startSpan();

            SpanContext spanCtx = span.getSpanContext();
            MDC.put("traceId", spanCtx.getTraceId());
            MDC.put("spanId", spanCtx.getSpanId());

            return span;
        } catch (Exception e) {
            log.debug("startConsumerSpan failed: {}", e.getMessage());
            return Span.getInvalid();
        }
    }

    /**
     * Sets the standard event/messaging attributes on a span. Null-guards each identifier so partial
     * envelopes still tag the span with whatever is present. Constants tie the span to the pub/sub
     * transport for APM filtering.
     */
    public void setEventAttributes(Span span, String txnId, String corrId, String eventId, String eventType) {
        if (span == null || !span.getSpanContext().isValid()) return;
        try {
            if (txnId != null) span.setAttribute("transaction.id", txnId);
            if (corrId != null) span.setAttribute("correlation.id", corrId);
            if (eventId != null) span.setAttribute("event.id", eventId);
            if (eventType != null) span.setAttribute("event.type", eventType);
            span.setAttribute("messaging.system", "oci-streaming");
            span.setAttribute("messaging.destination", "event-stream");
        } catch (Exception e) {
            log.debug("setEventAttributes failed: {}", e.getMessage());
        }
    }

    public void endSpan(Span span, Throwable error) {
        if (span == null || !span.getSpanContext().isValid()) return;
        try {
            if (error != null) {
                span.setStatus(StatusCode.ERROR, error.getClass().getSimpleName());
                span.recordException(error);
            } else {
                span.setStatus(StatusCode.OK);
            }
            span.end();
        } catch (Exception e) {
            log.debug("endSpan(Throwable) failed: {}", e.getMessage());
        }
    }

    public void endSpan(Span span, int statusCode) {
        if (span == null || !span.getSpanContext().isValid()) return;
        try {
            span.setAttribute("http.status_code", statusCode);
            span.setStatus(statusCode >= 500 ? StatusCode.ERROR : StatusCode.OK);
            span.end();
        } catch (Exception e) {
            log.debug("endSpan failed: {}", e.getMessage());
        }
    }
}
