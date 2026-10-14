package com.brx.serverless.handler;

import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.bridge.SLF4JBridgeHandler;

import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.trace.Span;
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
import org.slf4j.MDC;

import com.fnproject.fn.api.RuntimeContext;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.monitoring.MonitoringClient;
import com.oracle.bmc.monitoring.model.Datapoint;
import com.oracle.bmc.monitoring.model.MetricDataDetails;
import com.oracle.bmc.monitoring.model.PostMetricDataDetails;
import com.oracle.bmc.monitoring.requests.PostMetricDataRequest;

public class ObservabilityHelper {

    private static final Logger log = LoggerFactory.getLogger(ObservabilityHelper.class);

    private static MonitoringClient monitoringClient;
    private static String compartmentId;
    private static String metricNamespace;
    private static String environment;
    private static volatile Tracer tracer;
    // APM config stored at configure() time; OTel SDK initialized lazily on first startSpan()
    private static volatile String pendingApmUrl;
    private static volatile String pendingApmDataKey;
    private static volatile String pendingApmServiceName;

    static {
        // Initialize JUL to SLF4J Bridge at class-load time
        try {
            java.util.logging.LogManager.getLogManager().reset();
            SLF4JBridgeHandler.removeHandlersForRootLogger();
            SLF4JBridgeHandler.install();
            log.info("JUL-to-SLF4J bridge successfully installed");
        } catch (Exception e) {
            log.error("Failed to install JUL-to-SLF4J bridge: {}", e.getMessage());
        }
    }

    public static void configure(RuntimeContext ctx) {
        environment = ctx.getConfigurationByKey("ENVIRONMENT").orElse("dev");
        metricNamespace = ctx.getConfigurationByKey("METRIC_NAMESPACE").orElse("app_analytics");

        // Use custom property or look for COMPARTMENT_OCID
        compartmentId = ctx.getConfigurationByKey("COMPARTMENT_OCID").orElse(null);

        if ("test".equalsIgnoreCase(environment)) {
            log.info("Running in TEST environment - skipping OCI Monitoring SDK client initialization");
            return;
        }

        if (compartmentId == null || compartmentId.isEmpty() || "INJECT_AT_DEPLOY_TIME".equals(compartmentId)) {
            log.warn("COMPARTMENT_OCID configuration parameter is missing or not provided. Monitoring client skipped.");
            return;
        }

        try {
            log.info("Initializing OCI Monitoring SDK client with Resource Principal details locator");
            ResourcePrincipalAuthenticationDetailsProvider provider = 
                    ResourcePrincipalAuthenticationDetailsProvider.builder().build();
            monitoringClient = MonitoringClient.builder().build(provider);
            // PostMetricData requires the telemetry-INGESTION endpoint, NOT the default management/query
            // endpoint. Without this, custom metric posts fail silently and never appear in OCI Monitoring.
            String ingestionRegion = provider.getRegion() != null
                    ? provider.getRegion().getRegionId()
                    : "sa-saopaulo-1";
            monitoringClient.setEndpoint("https://telemetry-ingestion." + ingestionRegion + ".oraclecloud.com");
            log.info("OCI Monitoring SDK Client initialized successfully under namespace: {} (ingestion region: {})", metricNamespace, ingestionRegion);
        } catch (Exception e) {
            log.warn("Unable to initialize OCI Monitoring Client via Resource Principal (normal if running locally): {}", e.getMessage());
        }

        // Store APM config for lazy OTel init on first invocation (avoids cold-start overhead)
        pendingApmUrl         = ctx.getConfigurationByKey("APM_DOMAIN_URL").orElse(null);
        pendingApmDataKey     = ctx.getConfigurationByKey("APM_DATA_KEY").orElse(null);
        pendingApmServiceName = ctx.getConfigurationByKey("SERVICE_NAME").orElse("api-handler");
        if (pendingApmUrl != null && !pendingApmUrl.isBlank() && pendingApmDataKey != null && !pendingApmDataKey.isBlank()) {
            log.info("APM config stored — OTel SDK will init on first invocation");
        } else {
            log.info("APM_DOMAIN_URL or APM_DATA_KEY not configured — OTel tracing disabled");
        }
    }

    public static void postMetric(String name, double value, Map<String, String> dimensions) {
        if (monitoringClient == null) {
            log.debug("Tracing telemetry metric write: name={}, value={}, dimensions={}", name, value, dimensions);
            return;
        }

        try {
            Map<String, String> finalizedDimensions = new HashMap<>(dimensions);
            finalizedDimensions.put("environment", environment);

            MetricDataDetails metricData = MetricDataDetails.builder()
                    .compartmentId(compartmentId)
                    .namespace(metricNamespace)
                    .name(name)
                    .dimensions(finalizedDimensions)
                    .datapoints(List.of(
                            Datapoint.builder()
                                    .timestamp(new Date())
                                    .value(value)
                                    .count(1)
                                    .build()
                    ))
                    .build();

            PostMetricDataDetails postDetails = PostMetricDataDetails.builder()
                    .metricData(List.of(metricData))
                    .batchAtomicity(PostMetricDataDetails.BatchAtomicity.NonAtomic)
                    .build();

            PostMetricDataRequest request = PostMetricDataRequest.builder()
                    .postMetricDataDetails(postDetails)
                    .build();

            monitoringClient.postMetricData(request);
        } catch (Exception e) {
            log.warn("Degraded state: Failed to post custom metric telemetry: {} - Reason: {}", name, e.getMessage());
        }
    }

    public static void postInvocation(String path, String method, boolean isColdStart) {
        postMetric("ApiHandlerInvocation", 1.0, Map.of(
                "route", path,
                "method", method,
                "cold_start", String.valueOf(isColdStart)
        ));
    }

    public static void postDuration(String path, String method, long durationMs) {
        postMetric("ApiHandlerDuration", (double) durationMs, Map.of(
                "route", path,
                "method", method
        ));
    }

    public static void postError(String path, String method, int statusCode) {
        postMetric("ApiHandlerError", 1.0, Map.of(
                "route", path,
                "method", method,
                "status_code", String.valueOf(statusCode)
        ));
    }

    // ── Distributed Tracing (OpenTelemetry → OCI APM via OTLP/HTTP) ────────────────────────

    private static void initOpenTelemetry(String apmDomainUrl, String apmDataKey, String serviceName) {
        try {
            String otlpEndpoint = apmDomainUrl.replaceAll("/$", "")
                    + "/20200101/opentelemetry/private/v1/traces";

            OtlpHttpSpanExporter exporter = OtlpHttpSpanExporter.builder()
                    .setEndpoint(otlpEndpoint)
                    .addHeader("Authorization", "dataKey " + apmDataKey)
                    .setTimeout(java.time.Duration.ofSeconds(5))
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

    public static Span startSpan(String method, String route, String traceparent) {
        // Lazy init: initialize OTel SDK on first invocation to avoid cold-start overhead
        if (tracer == null && pendingApmUrl != null && pendingApmDataKey != null) {
            synchronized (ObservabilityHelper.class) {
                if (tracer == null) {
                    initOpenTelemetry(pendingApmUrl, pendingApmDataKey, pendingApmServiceName);
                }
            }
        }
        if (tracer == null) return Span.getInvalid();
        try {
            Context parentContext = Context.current();
            if (traceparent != null && !traceparent.isBlank()) {
                java.util.Map<String, String> carrier = java.util.Map.of("traceparent", traceparent);
                parentContext = GlobalOpenTelemetry.getPropagators()
                        .getTextMapPropagator()
                        .extract(Context.current(), carrier, new TextMapGetter<>() {
                            @Override
                            public String get(java.util.Map<String, String> c, String key) {
                                return c.get(key);
                            }
                            @Override
                            public Iterable<String> keys(java.util.Map<String, String> c) {
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

            io.opentelemetry.api.trace.SpanContext spanCtx = span.getSpanContext();
            MDC.put("traceId", spanCtx.getTraceId());
            MDC.put("spanId",  spanCtx.getSpanId());

            return span;
        } catch (Exception e) {
            log.debug("startSpan failed: {}", e.getMessage());
            return Span.getInvalid();
        }
    }

    public static void endSpan(Span span, int statusCode) {
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