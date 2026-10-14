package com.brx.functions.apifacade;

import java.util.Map;
import java.util.Optional;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import org.junit.Test;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import com.fnproject.fn.api.RuntimeContext;

import io.opentelemetry.api.trace.Span;

/**
 * Offline unit tests for {@link ObservabilityHelper}.
 *
 * These exercise the graceful/degraded paths that must never throw when running
 * outside an OCI Functions container (no Resource Principal, no APM, no Monitoring
 * client). All assertions run fully offline — no OCI SDK network calls are made.
 *
 * NOTE: ObservabilityHelper holds static state. configure() is designed so that the
 * Monitoring client and OTel tracer stay null in every scenario tested here, which
 * keeps the metric/span helpers as safe no-ops.
 */
public class ObservabilityHelperTest {

    /** Builds a mock RuntimeContext where every requested key resolves via the supplied map. */
    private RuntimeContext ctxWith(Map<String, String> config) {
        RuntimeContext ctx = mock(RuntimeContext.class);
        when(ctx.getConfigurationByKey(anyString())).thenAnswer(inv -> {
            String key = inv.getArgument(0);
            return Optional.ofNullable(config.get(key));
        });
        return ctx;
    }

    // ===== configure() graceful paths =====

    @Test
    public void configureSkipsWhenEnvironmentIsTest() {
        // ENVIRONMENT=test short-circuits before any SDK client init — must not throw.
        RuntimeContext ctx = ctxWith(Map.of("ENVIRONMENT", "test"));
        ObservabilityHelper.configure(ctx);
    }

    @Test
    public void configureNoThrowWhenCompartmentMissing() {
        // Non-test env but no COMPARTMENT_OCID → Monitoring client skipped, no throw.
        RuntimeContext ctx = ctxWith(Map.of("ENVIRONMENT", "dev"));
        ObservabilityHelper.configure(ctx);
    }

    @Test
    public void configureNoThrowWhenCompartmentIsPlaceholder() {
        // The INJECT_AT_DEPLOY_TIME sentinel is treated as "missing" — no throw.
        RuntimeContext ctx = ctxWith(Map.of(
                "ENVIRONMENT", "dev",
                "COMPARTMENT_OCID", "INJECT_AT_DEPLOY_TIME"));
        ObservabilityHelper.configure(ctx);
    }

    @Test
    public void configureDisablesTracingWhenApmAbsent() {
        // No APM_DOMAIN_URL / APM_DATA_KEY → tracing disabled. startSpan must be a no-op.
        RuntimeContext ctx = ctxWith(Map.of("ENVIRONMENT", "dev"));
        ObservabilityHelper.configure(ctx);

        Span span = ObservabilityHelper.startSpan("GET", "/hello", null);
        assertNotNull(span);
        // Tracing disabled → invalid (no-op) span.
        assertFalse(span.getSpanContext().isValid());
    }

    // ===== metric helpers no-throw when monitoringClient is null =====

    @Test
    public void postInvocationNoThrowWhenMonitoringDisabled() {
        ObservabilityHelper.configure(ctxWith(Map.of("ENVIRONMENT", "test")));
        ObservabilityHelper.postInvocation("/hello", "GET", true);
    }

    @Test
    public void postDurationNoThrowWhenMonitoringDisabled() {
        ObservabilityHelper.configure(ctxWith(Map.of("ENVIRONMENT", "test")));
        ObservabilityHelper.postDuration("/hello", "GET", 42L);
    }

    @Test
    public void postErrorNoThrowWhenMonitoringDisabled() {
        ObservabilityHelper.configure(ctxWith(Map.of("ENVIRONMENT", "test")));
        ObservabilityHelper.postError("/secret", "POST", 503);
    }

    // ===== span helpers no-throw when tracer is null =====

    @Test
    public void startSpanReturnsInvalidWhenTracerNull() {
        ObservabilityHelper.configure(ctxWith(Map.of("ENVIRONMENT", "test")));
        Span span = ObservabilityHelper.startSpan("POST", "/secret", "00-abc-def-01");
        assertNotNull(span);
        assertFalse(span.getSpanContext().isValid());
    }

    @Test
    public void startChildSpanReturnsInvalidWhenTracerNull() {
        ObservabilityHelper.configure(ctxWith(Map.of("ENVIRONMENT", "test")));
        Span span = ObservabilityHelper.startChildSpan("Vault.GetSecret");
        assertNotNull(span);
        assertFalse(span.getSpanContext().isValid());
    }

    @Test
    public void endSpanNoThrowOnInvalidSpan() {
        ObservabilityHelper.configure(ctxWith(Map.of("ENVIRONMENT", "test")));
        Span span = ObservabilityHelper.startChildSpan("ObjectStorage.PutObject");
        // Both overloads must tolerate an invalid/no-op span without throwing.
        ObservabilityHelper.endSpan(span);
        ObservabilityHelper.endSpan(span, 200);
    }

    @Test
    public void endSpanNoThrowOnNullSpan() {
        ObservabilityHelper.endSpan(null);
        ObservabilityHelper.endSpan(null, 500);
    }
}
