package com.brx.serverless.handler;

import java.lang.reflect.Field;
import java.util.Optional;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import com.fnproject.fn.api.RuntimeContext;

import io.opentelemetry.api.trace.Span;

/**
 * Unit tests for {@link ObservabilityHelper}.
 *
 * These tests run fully offline: no Resource Principal, no OCI Monitoring endpoint,
 * and no APM/OTLP endpoint is contacted. The helper is designed to degrade gracefully
 * when its clients cannot be initialized, and these tests assert exactly that.
 *
 * NOTE: {@code ObservabilityHelper} keeps its collaborators (monitoringClient, tracer,
 * pending APM config) in {@code static} fields. Each test resets that static state via
 * reflection in {@link #resetStaticState()} so tests are order-independent and isolated.
 * We deliberately do NOT use FnTestingRule here: the helper is invoked directly with a
 * RuntimeContext (it is not itself a function entry point), so a plain in-process unit
 * test with a mocked RuntimeContext is the correct, faster tool.
 */
public class ObservabilityHelperTest {

    private RuntimeContext ctx;

    @Before
    public void setUp() throws Exception {
        resetStaticState();
        ctx = mock(RuntimeContext.class);
        // Default: every key absent unless a test overrides it.
        when(ctx.getConfigurationByKey(org.mockito.ArgumentMatchers.anyString()))
                .thenReturn(Optional.empty());
    }

    @After
    public void tearDown() throws Exception {
        resetStaticState();
    }

    /** Convenience to stub a single configuration key on the mocked RuntimeContext. */
    private void config(String key, String value) {
        when(ctx.getConfigurationByKey(eq(key))).thenReturn(Optional.ofNullable(value));
    }

    /** Reset all mutable static fields of ObservabilityHelper to a clean slate. */
    private static void resetStaticState() throws Exception {
        setStatic("monitoringClient", null);
        setStatic("compartmentId", null);
        setStatic("metricNamespace", null);
        setStatic("environment", null);
        setStatic("tracer", null);
        setStatic("pendingApmUrl", null);
        setStatic("pendingApmDataKey", null);
        setStatic("pendingApmServiceName", null);
    }

    private static void setStatic(String name, Object value) throws Exception {
        Field f = ObservabilityHelper.class.getDeclaredField(name);
        f.setAccessible(true);
        f.set(null, value);
    }

    private static Object getStatic(String name) throws Exception {
        Field f = ObservabilityHelper.class.getDeclaredField(name);
        f.setAccessible(true);
        return f.get(null);
    }

    // ── configure() ────────────────────────────────────────────────────────────

    @Test
    public void configureInTestEnvironmentSkipsClientInitWithoutThrowing() throws Exception {
        config("ENVIRONMENT", "test");
        config("COMPARTMENT_OCID", "ocid1.compartment.oc1..aaaa");

        ObservabilityHelper.configure(ctx); // must not throw

        // In TEST env the helper returns before any SDK client init.
        assertNull("monitoringClient must stay null in test environment", getStatic("monitoringClient"));
        assertNull("tracer must stay null in test environment", getStatic("tracer"));
    }

    @Test
    public void configureWithMissingCompartmentDoesNotThrowAndLeavesClientNull() throws Exception {
        config("ENVIRONMENT", "dev");
        // COMPARTMENT_OCID intentionally absent (mock returns Optional.empty()).

        ObservabilityHelper.configure(ctx); // must not throw

        assertNull("monitoringClient must stay null when COMPARTMENT_OCID is missing",
                getStatic("monitoringClient"));
    }

    @Test
    public void configureWithEmptyCompartmentDoesNotThrowAndLeavesClientNull() throws Exception {
        config("ENVIRONMENT", "dev");
        config("COMPARTMENT_OCID", "");

        ObservabilityHelper.configure(ctx); // must not throw

        assertNull("monitoringClient must stay null when COMPARTMENT_OCID is empty",
                getStatic("monitoringClient"));
    }

    @Test
    public void configureWithPlaceholderCompartmentDoesNotThrowAndLeavesClientNull() throws Exception {
        config("ENVIRONMENT", "dev");
        config("COMPARTMENT_OCID", "INJECT_AT_DEPLOY_TIME");

        ObservabilityHelper.configure(ctx); // must not throw

        assertNull("monitoringClient must stay null for the deploy-time placeholder",
                getStatic("monitoringClient"));
    }

    @Test
    public void configureWithoutApmConfigLeavesTracingDisabled() throws Exception {
        config("ENVIRONMENT", "test"); // avoid Resource Principal init entirely
        // APM_DOMAIN_URL / APM_DATA_KEY intentionally absent.

        ObservabilityHelper.configure(ctx); // must not throw

        assertNull("tracer must remain null when APM is not configured", getStatic("tracer"));
    }

    @Test
    public void configureReadsServiceNameConfigKeyForApmServiceName() throws Exception {
        // Regression guard for the SERVICE_NAME (not APM_SERVICE_NAME) fix.
        // We stay in a non-test env with COMPARTMENT_OCID so that the APM config
        // block at the end of configure() is reached and pendingApmServiceName is set.
        config("ENVIRONMENT", "dev");
        config("COMPARTMENT_OCID", "ocid1.compartment.oc1..aaaa");
        config("SERVICE_NAME", "api-handler");

        ObservabilityHelper.configure(ctx); // must not throw (Resource Principal init is caught)

        // Tracing must still be disabled (no APM_DOMAIN_URL / APM_DATA_KEY),
        // but the service name must have been read from SERVICE_NAME.
        Object pendingServiceName = getStatic("pendingApmServiceName");
        assertNotNull("SERVICE_NAME must populate pendingApmServiceName", pendingServiceName);
        org.junit.Assert.assertEquals("api-handler", pendingServiceName);
        assertNull("tracer must remain null when APM endpoint/key are absent", getStatic("tracer"));
    }

    // ── metric posting: graceful degradation when monitoringClient is null ──────

    @Test
    public void postInvocationDoesNotThrowWhenNotConfigured() throws Exception {
        // configure() never called → monitoringClient stays null.
        assertNull(getStatic("monitoringClient"));
        ObservabilityHelper.postInvocation("/hello", "GET", true); // must not throw
    }

    @Test
    public void postDurationDoesNotThrowWhenNotConfigured() throws Exception {
        assertNull(getStatic("monitoringClient"));
        ObservabilityHelper.postDuration("/hello", "GET", 42L); // must not throw
    }

    @Test
    public void postErrorDoesNotThrowWhenNotConfigured() throws Exception {
        assertNull(getStatic("monitoringClient"));
        ObservabilityHelper.postError("/hello", "GET", 500); // must not throw
    }

    // ── tracing: no-op when tracer is null (APM disabled) ───────────────────────

    @Test
    public void startSpanReturnsInvalidSpanWhenTracerDisabled() throws Exception {
        // tracer null AND no pending APM config → returns Span.getInvalid().
        assertNull(getStatic("tracer"));

        Span span = ObservabilityHelper.startSpan("GET", "/hello", null);

        assertNotNull("startSpan must never return null", span);
        assertFalse("span must be invalid when tracing is disabled",
                span.getSpanContext().isValid());
    }

    @Test
    public void endSpanOnInvalidSpanIsNoOp() throws Exception {
        assertNull(getStatic("tracer"));
        Span span = ObservabilityHelper.startSpan("GET", "/hello", null);

        // Ending an invalid span must not throw and must remain a no-op.
        ObservabilityHelper.endSpan(span, 200);
    }

    @Test
    public void endSpanOnNullSpanIsNoOp() {
        ObservabilityHelper.endSpan(null, 200); // must not throw
    }
}
