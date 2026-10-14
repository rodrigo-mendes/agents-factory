package com.brx.functions.rr.restproxy;

import java.util.Map;
import java.util.Optional;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import org.junit.Before;
import org.junit.Test;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import com.fnproject.fn.api.RuntimeContext;

import io.opentelemetry.api.trace.Span;

/**
 * Offline unit tests for {@link ObservabilityHelper}.
 *
 * <p>These tests exercise the graceful-degradation paths only — no live OCI Monitoring,
 * no live APM/OTLP endpoint, and no Resource Principal. They rely on the fact that when
 * {@code monitoringClient} and {@code tracer} are null (never initialized in a plain JVM),
 * every telemetry method is a safe no-op.
 */
public class ObservabilityHelperTest {

    private RuntimeContext ctx;

    @Before
    public void setUp() {
        ctx = mock(RuntimeContext.class);
        // Default: every config key absent unless a test overrides it.
        when(ctx.getConfigurationByKey(anyString())).thenReturn(Optional.empty());
    }

    // ── configure() graceful paths ─────────────────────────────────────────────

    @Test
    public void configureSkipsSdkInTestEnvironment() {
        when(ctx.getConfigurationByKey("ENVIRONMENT")).thenReturn(Optional.of("test"));
        // Must not throw and must not attempt Resource Principal init.
        ObservabilityHelper.configure(ctx);
    }

    @Test
    public void configureMissingCompartmentDoesNotThrow() {
        when(ctx.getConfigurationByKey("ENVIRONMENT")).thenReturn(Optional.of("dev"));
        // COMPARTMENT_OCID absent (Optional.empty from default stub).
        ObservabilityHelper.configure(ctx);
    }

    @Test
    public void configureCompartmentPlaceholderDoesNotThrow() {
        when(ctx.getConfigurationByKey("ENVIRONMENT")).thenReturn(Optional.of("dev"));
        when(ctx.getConfigurationByKey("COMPARTMENT_OCID"))
                .thenReturn(Optional.of("INJECT_AT_DEPLOY_TIME"));
        ObservabilityHelper.configure(ctx);
    }

    @Test
    public void configureApmAbsentLeavesTracingOff() {
        when(ctx.getConfigurationByKey("ENVIRONMENT")).thenReturn(Optional.of("test"));
        // No APM_DOMAIN_URL / APM_DATA_KEY → tracing stays disabled.
        ObservabilityHelper.configure(ctx);

        // startSpan must remain a no-op (invalid) span when tracing is off.
        Span span = ObservabilityHelper.startSpan("GET", "/store/create", null);
        assertNotNull(span);
        assertFalse(span.getSpanContext().isValid());
    }

    // ── metric posts: no-op when monitoringClient is null ──────────────────────

    @Test
    public void postMetricNoThrowWhenMonitoringNull() {
        // Ensure we are in a state where monitoringClient was never initialized.
        when(ctx.getConfigurationByKey("ENVIRONMENT")).thenReturn(Optional.of("test"));
        ObservabilityHelper.configure(ctx);

        ObservabilityHelper.postMetric("UnitTestMetric", 1.0, Map.of("k", "v"));
        ObservabilityHelper.postInvocation("/store/create", "POST", true);
        ObservabilityHelper.postDuration("/store/create", "POST", 42L);
        ObservabilityHelper.postError("/store/create", "POST", 500);
    }

    // ── span lifecycle: no-op when tracer is null ──────────────────────────────

    @Test
    public void startSpanNoThrowWhenTracerNull() {
        Span span = ObservabilityHelper.startSpan("POST", "/store/create", "traceparent-header");
        assertNotNull(span);
        assertFalse(span.getSpanContext().isValid());
    }

    @Test
    public void startChildSpanNoThrowWhenTracerNull() {
        Span span = ObservabilityHelper.startChildSpan("RMS.OAuthToken");
        assertNotNull(span);
        assertFalse(span.getSpanContext().isValid());
    }

    @Test
    public void endSpanNoThrowOnInvalidSpan() {
        Span span = ObservabilityHelper.startChildSpan("BrxServices.PostStore");
        // Both overloads must tolerate a no-op / invalid span.
        ObservabilityHelper.endSpan(span, (Throwable) null);
        ObservabilityHelper.endSpan(span, new RuntimeException("boom"));
        ObservabilityHelper.endSpan(span, 200);
    }

    @Test
    public void endSpanNoThrowOnNullSpan() {
        ObservabilityHelper.endSpan(null, (Throwable) null);
        ObservabilityHelper.endSpan(null, 503);
    }
}
