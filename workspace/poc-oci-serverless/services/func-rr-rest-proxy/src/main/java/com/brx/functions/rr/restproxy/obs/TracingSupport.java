package com.brx.functions.rr.restproxy.obs;

import java.time.Duration;
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
import io.opentelemetry.sdk.trace.export.BatchSpanProcessor;

/**
 * Distributed tracing support (OpenTelemetry → OCI APM via OTLP/HTTP).
 *
 * <p>The OTel SDK is initialized lazily on the first {@link #startSpan} to avoid cold-start
 * overhead. When APM is not configured the tracer stays null and all methods degrade to no-ops
 * ({@link Span#getInvalid()}), so callers can invoke start/end unconditionally.
 */
public class TracingSupport {

    private static final Logger log = LoggerFactory.getLogger(TracingSupport.class);

    private volatile Tracer tracer;
    private volatile String environment = "dev";
    // APM config captured at configure() time; OTel SDK initialized lazily on first startSpan()
    private volatile String pendingApmUrl;
    private volatile String pendingApmDataKey;
    private volatile String pendingApmServiceName;

    public void configure(RuntimeContext ctx, String environment) {
        this.environment = environment;
        this.pendingApmUrl = ctx.getConfigurationByKey("APM_DOMAIN_URL").orElse(null);
        this.pendingApmDataKey = ctx.getConfigurationByKey("APM_DATA_KEY").orElse(null);
        this.pendingApmServiceName = ctx.getConfigurationByKey("SERVICE_NAME").orElse("func-rr-rest-proxy");
        if (pendingApmUrl != null && !pendingApmUrl.isBlank() && pendingApmDataKey != null && !pendingApmDataKey.isBlank()) {
            log.info("APM config stored — OTel SDK will init on first invocation");
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
                    .addSpanProcessor(BatchSpanProcessor.builder(exporter).build())
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

    public Span startSpan(String method, String route, String traceparent) {
        // Lazy init: initialize OTel SDK on first invocation to avoid cold-start overhead
        if (tracer == null && pendingApmUrl != null && pendingApmDataKey != null) {
            synchronized (this) {
                if (tracer == null) {
                    initOpenTelemetry(pendingApmUrl, pendingApmDataKey, pendingApmServiceName);
                }
            }
        }
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
     * Starts a parentless INTERNAL root span (e.g. to wrap cold-start init). Triggers the same lazy
     * OTel SDK init as {@link #startSpan} so init-time child spans (Vault.GetSecret during
     * {@code configure()}) can nest under it. Returns {@link Span#getInvalid()} when tracing is off.
     */
    public Span startRootSpan(String name) {
        if (tracer == null && pendingApmUrl != null && pendingApmDataKey != null) {
            synchronized (this) {
                if (tracer == null) {
                    initOpenTelemetry(pendingApmUrl, pendingApmDataKey, pendingApmServiceName);
                }
            }
        }
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
