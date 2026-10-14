package com.brx.functions.rr.restproxy.obs;

import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.fnproject.fn.api.RuntimeContext;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.monitoring.MonitoringClient;
import com.oracle.bmc.monitoring.model.Datapoint;
import com.oracle.bmc.monitoring.model.MetricDataDetails;
import com.oracle.bmc.monitoring.model.PostMetricDataDetails;
import com.oracle.bmc.monitoring.requests.PostMetricDataRequest;

/**
 * Publishes custom function metrics to OCI Monitoring via PostMetricData.
 *
 * <p>Requires the {@code telemetry-ingestion} endpoint (not the default management/query endpoint)
 * or posts fail silently. Degrades gracefully: when the client is not initialized (local/test) or
 * a post fails, metrics are dropped without disrupting the invocation.
 */
public class MetricsPublisher {

    private static final Logger log = LoggerFactory.getLogger(MetricsPublisher.class);

    private MonitoringClient monitoringClient;
    private String compartmentId;
    private String metricNamespace;
    private String environment;

    /**
     * Initializes the Monitoring client from configuration.
     *
     * @return {@code false} if metric publishing is skipped (test environment or missing
     *         compartment) so the caller can short-circuit dependent setup; {@code true} otherwise.
     */
    public boolean configure(RuntimeContext ctx, String environment) {
        this.environment = environment;
        this.metricNamespace = ctx.getConfigurationByKey("METRIC_NAMESPACE").orElse("app_analytics");
        this.compartmentId = ctx.getConfigurationByKey("COMPARTMENT_OCID").orElse(null);

        if ("test".equalsIgnoreCase(environment)) {
            log.info("Running in TEST environment - skipping OCI Monitoring SDK client initialization");
            return false;
        }

        if (compartmentId == null || compartmentId.isEmpty() || "INJECT_AT_DEPLOY_TIME".equals(compartmentId)) {
            log.warn("COMPARTMENT_OCID configuration parameter is missing or not provided. Monitoring client skipped.");
            return false;
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
        return true;
    }

    public void postMetric(String name, double value, Map<String, String> dimensions) {
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

    public void postInvocation(String path, String method, boolean isColdStart) {
        postMetric("RestProxyInvocation", 1.0, Map.of(
                "route", path,
                "method", method,
                "cold_start", String.valueOf(isColdStart)
        ));
    }

    public void postDuration(String path, String method, long durationMs) {
        postMetric("RestProxyDuration", (double) durationMs, Map.of(
                "route", path,
                "method", method
        ));
    }

    public void postError(String path, String method, int statusCode) {
        postMetric("RestProxyError", 1.0, Map.of(
                "route", path,
                "method", method,
                "status_code", String.valueOf(statusCode)
        ));
    }
}
