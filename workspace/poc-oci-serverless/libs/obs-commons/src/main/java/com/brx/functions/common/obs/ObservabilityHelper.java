package com.brx.functions.common.obs;

import java.util.Map;

import com.brx.functions.common.obs.TracingSupport.TraceContext;
import com.fnproject.fn.api.RuntimeContext;

import io.opentelemetry.api.trace.Span;

/**
 * Static facade over the three observability concerns, each owned by a dedicated collaborator:
 * <ul>
 *   <li>{@link LoggingBridge} — JUL → SLF4J bridge (installed at class load)</li>
 *   <li>{@link MetricsPublisher} — OCI Monitoring custom metrics</li>
 *   <li>{@link TracingSupport} — OpenTelemetry distributed tracing → OCI APM</li>
 * </ul>
 * The static API is preserved for existing call sites; this class only delegates.
 *
 * <p>Shared across the 3 pub/sub services via {@code brx-fn-obs-commons} — a single source of the
 * configure/inject/extract flow so the distributed trace contract cannot drift between services.
 */
public class ObservabilityHelper {

    private static final MetricsPublisher metrics = new MetricsPublisher();
    private static final TracingSupport tracing = new TracingSupport();

    static {
        LoggingBridge.install();
    }

    private ObservabilityHelper() {
    }

    public static void configure(RuntimeContext ctx) {
        String environment = ctx.getConfigurationByKey("ENVIRONMENT").orElse("dev");
        // Preserve original control flow: when metrics setup is skipped (test env / missing
        // compartment), APM/tracing config is not captured either.
        if (!metrics.configure(ctx, environment)) {
            return;
        }
        tracing.configure(ctx, environment);
    }

    // ── Metrics ────────────────────────────────────────────────────────────────────────────

    public static void postMetric(String name, double value, Map<String, String> dimensions) {
        metrics.postMetric(name, value, dimensions);
    }

    // ── Tracing ────────────────────────────────────────────────────────────────────────────

    public static Span startSpan(String method, String route, String traceparent) {
        return tracing.startSpan(method, route, traceparent);
    }

    public static Span startRootSpan(String name) {
        return tracing.startRootSpan(name);
    }

    public static Span startChildSpan(String name) {
        return tracing.startChildSpan(name);
    }

    public static void endSpan(Span span, Throwable error) {
        tracing.endSpan(span, error);
    }

    public static void endSpan(Span span, int statusCode) {
        tracing.endSpan(span, statusCode);
    }

    // ── Cross-stream trace propagation ──────────────────────────────────────────────────────

    /** Captures the active span's W3C trace context for propagation inside a stream message. */
    public static TraceContext injectTraceContext() {
        return tracing.injectTraceContext();
    }

    /** Starts a CONSUMER span re-parented onto the trace context carried in a stream message. */
    public static Span startConsumerSpan(String name, String traceparent, String tracestate) {
        return tracing.startConsumerSpan(name, traceparent, tracestate);
    }

    /** Sets standard event/messaging attributes on a span. */
    public static void setEventAttributes(Span span, String txnId, String corrId,
                                          String eventId, String eventType) {
        tracing.setEventAttributes(span, txnId, corrId, eventId, eventType);
    }
}
