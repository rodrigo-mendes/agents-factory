# Integration Patterns — monitoring-oci-java-functions

## Java Function ↔ OCI Monitoring (Complete OrderProcessorFunction)

Production-ready function demonstrating all mandatory patterns:

```java
package com.example;

import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.monitoring.MonitoringClient;
import com.oracle.bmc.monitoring.model.*;
import com.oracle.bmc.monitoring.requests.PostMetricDataRequest;

import java.util.*;

public class OrderProcessorFunction {

    // Cold-start init (once per container lifetime)
    private static MonitoringClient monitoringClient;
    private static String compartmentId;
    private static String metricNamespace;

    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        var auth = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
        monitoringClient = MonitoringClient.builder().build(auth);
        // PostMetricData requires the INGESTION endpoint; without it the post fails silently.
        monitoringClient.setEndpoint("https://telemetry-ingestion." + auth.getRegion().getRegionId() + ".oraclecloud.com");

        compartmentId   = ctx.getConfigurationByKey("COMPARTMENT_OCID")
                             .orElseThrow(() -> new RuntimeException("COMPARTMENT_OCID required"));
        metricNamespace = ctx.getConfigurationByKey("METRIC_NAMESPACE")
                             .orElseThrow(() -> new RuntimeException("METRIC_NAMESPACE required"));
    }

    public String handleRequest(String orderId) {
        long start = System.currentTimeMillis();
        try {
            String result = processOrder(orderId);
            long durationMs = System.currentTimeMillis() - start;

            // Synchronous batch post before return
            postBatchMetrics(List.of(
                buildDatapoint("OrderProcessed", 1.0, Map.of("status", "success")),
                buildDatapoint("OrderProcessingDuration", (double) durationMs,
                    Map.of("functionName", "order-processor"))
            ));
            return result;
        } catch (Exception e) {
            postBatchMetrics(List.of(
                buildDatapoint("OrderProcessed", 1.0, Map.of("status", "error")),
                buildDatapoint("OrderErrors", 1.0,
                    Map.of("errorType", e.getClass().getSimpleName()))
            ));
            System.err.println("{\"level\":\"ERROR\",\"orderId\":\"" + orderId
                + "\",\"error\":\"" + e.getMessage() + "\"}");
            throw new RuntimeException("Order processing failed: " + orderId, e);
        }
    }

    private String processOrder(String orderId) {
        return "confirmed:" + orderId;
    }

    private MetricDataDetails buildDatapoint(String name, double value,
                                              Map<String, String> dimensions) {
        return MetricDataDetails.builder()
            .compartmentId(compartmentId)
            .namespace(metricNamespace)
            .name(name)
            .dimensions(dimensions)
            .datapoints(List.of(
                Datapoint.builder()
                    .timestamp(new Date())  // never stale timestamps
                    .value(value)
                    .count(1)
                    .build()))
            .build();
    }

    private void postBatchMetrics(List<MetricDataDetails> metrics) {
        try {
            var request = PostMetricDataRequest.builder()
                .postMetricDataDetails(PostMetricDataDetails.builder()
                    .metricData(metrics)
                    .batchAtomicity(PostMetricDataDetails.BatchAtomicity.NonAtomic)
                    .build())
                .build();

            var response = monitoringClient.postMetricData(request);

            var details = response.getPostMetricDataResponseDetails();
            if (details != null && !details.getRejectedMetricsData().isEmpty()) {
                System.err.println("{\"level\":\"WARN\",\"rejectedCount\":"
                    + details.getRejectedMetricsData().size() + "}");
            }
        } catch (Exception e) {
            // Observability failure MUST NOT fail business operation
            System.err.println("{\"level\":\"WARN\",\"message\":\"Metric post failed\","
                + "\"error\":\"" + e.getClass().getSimpleName() + "\"}");
        }
    }
}
```

---

## Terraform ↔ OCI Monitoring Stack (Complete)

```hcl
variable "compartment_ocid"  {}
variable "function_name"     { default = "order-processor" }
variable "environment"       { default = "prod" }
variable "timeout_seconds"   { default = 60 }
variable "oncall_email"      {}

locals {
  metric_namespace = "order_system_${var.environment}"
  timeout_ms       = var.timeout_seconds * 1000
}

# Notification topic
resource "oci_ons_notification_topic" "fn_alerts" {
  compartment_id = var.compartment_ocid
  name           = "${var.function_name}-alerts-${var.environment}"
}

resource "oci_ons_subscription" "email" {
  compartment_id = var.compartment_ocid
  topic_id       = oci_ons_notification_topic.fn_alerts.id
  protocol       = "EMAIL"
  endpoint       = var.oncall_email
}

# Error count alarm (CRITICAL)
resource "oci_monitoring_alarm" "fn_errors" {
  compartment_id        = var.compartment_ocid
  display_name          = "${var.function_name}-errors-${var.environment}"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_faas"
  query                 = "FunctionErrorCount[1m]{resourceId=\"${oci_functions_function.fn.id}\"}.sum() > 0"
  severity              = "CRITICAL"
  pending_duration      = "PT2M"
  body                  = "CRITICAL: ${var.function_name} errors in ${var.environment}."
  destinations          = [oci_ons_notification_topic.fn_alerts.id]
  message_format        = "ONS_OPTIMIZED"

  overrides {
    query            = "FunctionErrorCount[1m]{resourceId=\"${oci_functions_function.fn.id}\"}.sum() > 10"
    severity         = "CRITICAL"
    pending_duration = "PT1M"
    body             = "ERROR STORM: ${var.function_name} > 10 errors/min. Immediate action required."
  }
}

# Duration p99 alarm (WARNING)
resource "oci_monitoring_alarm" "fn_duration" {
  compartment_id        = var.compartment_ocid
  display_name          = "${var.function_name}-duration-p99-${var.environment}"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_faas"
  query                 = "FunctionExecutionDuration[1m]{resourceId=\"${oci_functions_function.fn.id}\"}.percentile(0.99) > ${local.timeout_ms * 0.8}"
  severity              = "WARNING"
  pending_duration      = "PT3M"
  body                  = "WARNING: ${var.function_name} p99 latency approaching timeout."
  destinations          = [oci_ons_notification_topic.fn_alerts.id]
  message_format        = "ONS_OPTIMIZED"
}

# Throttle alarm (ERROR)
resource "oci_monitoring_alarm" "fn_throttle" {
  compartment_id        = var.compartment_ocid
  display_name          = "${var.function_name}-throttle-${var.environment}"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_faas"
  query                 = "FunctionThrottleCount[5m]{applicationId=\"${oci_functions_application.app.id}\"}.sum() > 0"
  severity              = "ERROR"
  pending_duration      = "PT2M"
  body                  = "ERROR: ${var.function_name} is being throttled."
  destinations          = [oci_ons_notification_topic.fn_alerts.id]
  message_format        = "ONS_OPTIMIZED"
}

# Custom business metric alarm (order error rate > 5%)
resource "oci_monitoring_alarm" "fn_custom_errors" {
  compartment_id        = var.compartment_ocid
  display_name          = "${var.function_name}-order-errors-${var.environment}"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = local.metric_namespace
  query                 = <<-MQL
    OrderProcessed[5m]{status="error"}.sum() /
    OrderProcessed[5m]{}.sum() * 100 > 5
  MQL
  severity              = "ERROR"
  pending_duration      = "PT3M"
  body                  = "Business: ${var.function_name} order error rate > 5% for 3 minutes."
  destinations          = [oci_ons_notification_topic.fn_alerts.id]
  message_format        = "ONS_OPTIMIZED"
}

# Recurring maintenance window suppression
resource "oci_monitoring_alarm_suppression" "weekly_maintenance" {
  alarm_id               = oci_monitoring_alarm.fn_errors.id
  display_name           = "${var.function_name}-maintenance-window"
  time_suppress_from     = "2026-06-01T02:00:00Z"
  time_suppress_until    = "2026-06-01T04:00:00Z"
  suppression_recurrence = "FREQ=WEEKLY;BYDAY=SU;BYHOUR=2;BYMINUTE=0;BYSECOND=0"
  description            = "Weekly maintenance: Sunday 02:00-04:00 UTC"
}

# Function config wiring
resource "oci_functions_function" "fn" {
  application_id     = oci_functions_application.app.id
  display_name       = var.function_name
  image              = "${local.registry}/${local.image}:${local.tag}"
  memory_in_mbs      = 256
  timeout_in_seconds = var.timeout_seconds

  config = {
    COMPARTMENT_OCID = var.compartment_ocid
    METRIC_NAMESPACE = local.metric_namespace
  }
}
```

---

## FDK Testing ↔ MonitoringClient Mock

For unit-testable functions, inject `MonitoringClient` as a constructor parameter:

```java
// Refactored for testability: constructor injection
public class OrderProcessorFunction {
    private final MonitoringClient monitoringClient;
    private final String compartmentId;
    private final String metricNamespace;

    // Production constructor — FDK uses @FnConfiguration to populate fields
    public OrderProcessorFunction() { /* fields set via @FnConfiguration */ }

    // Test constructor — inject mock
    OrderProcessorFunction(MonitoringClient mockClient, String compartmentId, String namespace) {
        this.monitoringClient = mockClient;
        this.compartmentId    = compartmentId;
        this.metricNamespace  = namespace;
    }
}
```

**pom.xml test dependencies**:
```xml
<dependency>
    <groupId>com.fnproject.fn</groupId>
    <artifactId>testing-junit5</artifactId>
    <version>1.1.12</version>
    <scope>test</scope>
</dependency>
<dependency>
    <groupId>org.mockito</groupId>
    <artifactId>mockito-core</artifactId>
    <scope>test</scope>
</dependency>
```

> **Note**: `ResourcePrincipalAuthenticationDetailsProvider` cannot be initialized in unit tests (no OCI metadata service). Extract business logic into a separate class and test it independently. FDK integration tests with `@FnConfiguration` require a real OCI environment or a mocked provider.
