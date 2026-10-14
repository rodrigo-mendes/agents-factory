package com.brx.functions.rr.restproxy;

import java.util.Map;

import com.brx.functions.rr.restproxy.obs.LoggingBridge;
import com.brx.functions.rr.restproxy.obs.MetricsPublisher;
import com.brx.functions.rr.restproxy.obs.TracingSupport;
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

    public static void postInvocation(String path, String method, boolean isColdStart) {
        metrics.postInvocation(path, method, isColdStart);
    }

    public static void postDuration(String path, String method, long durationMs) {
        metrics.postDuration(path, method, durationMs);
    }

    public static void postError(String path, String method, int statusCode) {
        metrics.postError(path, method, statusCode);
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
}
