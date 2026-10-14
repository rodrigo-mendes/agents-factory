# Always Do Patterns — monitoring-oci-java-functions

## Pattern 1: Resource Principal Authentication for MonitoringClient

**Degree of freedom**: Low (security-critical — exact code)

**IAM prerequisites** (must exist before function deployment):
```
Dynamic Group: match any {resource.type = 'fnfunc', resource.compartment.id = 'ocid1.compartment...'}
Policy: allow dynamic-group <dg-name> to use metrics in compartment <compartment-name>
```

**pom.xml** — SDK BOM is mandatory for version alignment:
```xml
<properties>
    <oci.sdk.version>3.87.0</oci.sdk.version>
    <fdk.version>1.1.12</fdk.version>
</properties>
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>com.oracle.oci.sdk</groupId>
            <artifactId>oci-java-sdk-bom</artifactId>
            <version>${oci.sdk.version}</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
<dependencies>
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-monitoring</artifactId>
        <!-- version resolved from BOM -->
    </dependency>
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <!-- Jersey3 required for SDK 3.x; Jersey2 is forbidden -->
        <artifactId>oci-java-sdk-common-httpclient-jersey3</artifactId>
    </dependency>
</dependencies>
```

**Java setup**:
```java
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.monitoring.MonitoringClient;

// Static: initialized once per container lifetime in @FnConfiguration
private static final ResourcePrincipalAuthenticationDetailsProvider AUTH;
private static final MonitoringClient MONITORING;

static {
    // Throws OciMetadataServiceException if Dynamic Group / IAM policy is missing → halt deployment
    AUTH = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
    MONITORING = MonitoringClient.builder().build(AUTH);
    // REQUIRED for PostMetricData: use the INGESTION endpoint (not the default management/query endpoint).
    // Without this the post fails SILENTLY and the custom metric never appears.
    MONITORING.setEndpoint("https://telemetry-ingestion." + AUTH.getRegion().getRegionId() + ".oraclecloud.com");
}
```

---

## Pattern 2: Static SDK Client Initialization via @FnConfiguration

**Degree of freedom**: Low (performance-critical — exact annotation)

```java
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.monitoring.MonitoringClient;

public class MetricsFunction {

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
                             .orElseThrow(() -> new RuntimeException("COMPARTMENT_OCID missing"));
        metricNamespace = ctx.getConfigurationByKey("METRIC_NAMESPACE")
                             .orElseThrow(() -> new RuntimeException("METRIC_NAMESPACE missing"));
    }

    public String handleRequest(String input) {
        // monitoringClient is warm — no re-initialization cost
        return "ok";
    }
}
```

---

## Pattern 3: PostMetricData with BatchAtomicity.NonAtomic + Rejection Check

**Degree of freedom**: Medium (template — batch contents and dimensions vary)

```java
import com.oracle.bmc.monitoring.model.*;
import com.oracle.bmc.monitoring.requests.PostMetricDataRequest;
import java.util.*;

private void postMetric(String metricName, double value, Map<String, String> dimensions) {
    try {
        var datapoint = Datapoint.builder()
            .timestamp(new Date())   // MUST be within last 2 hours; never use stale event timestamps
            .value(value)
            .count(1)
            .build();

        var metricData = MetricDataDetails.builder()
            .compartmentId(compartmentId)
            .namespace(metricNamespace)
            .name(metricName)
            .dimensions(dimensions)  // max 10 key-value pairs
            .datapoints(List.of(datapoint))
            .build();

        var request = PostMetricDataRequest.builder()
            .postMetricDataDetails(PostMetricDataDetails.builder()
                .metricData(List.of(metricData))
                .batchAtomicity(PostMetricDataDetails.BatchAtomicity.NonAtomic)
                .build())
            .build();

        var response = monitoringClient.postMetricData(request);

        // Check partial rejections (invalid dimensions, stale timestamps) — HTTP 200 does NOT mean all accepted
        if (response.getPostMetricDataResponseDetails() != null &&
            !response.getPostMetricDataResponseDetails().getRejectedMetricsData().isEmpty()) {
            System.err.println("{\"level\":\"WARN\",\"message\":\"Partial metric rejection\",\"count\":"
                + response.getPostMetricDataResponseDetails().getRejectedMetricsData().size() + "}");
        }
    } catch (Exception e) {
        // Observability failure MUST NOT fail the business operation
        System.err.println("{\"level\":\"WARN\",\"message\":\"Metric post failed\",\"metric\":\""
            + metricName + "\",\"error\":\"" + e.getClass().getSimpleName() + "\"}");
    }
}
```

---

## Pattern 4: Inject COMPARTMENT_OCID and METRIC_NAMESPACE via Function Config

**Degree of freedom**: Medium (template — values injected at deploy time)

**func.yaml**:
```yaml
schema_version: 20180708
name: order-processor
version: 0.0.1
runtime: java
entrypoint: com.example.OrderProcessorFunction::handleRequest
memory: 256
timeout: 60
config:
  COMPARTMENT_OCID: "INJECT_AT_DEPLOY_TIME"
  METRIC_NAMESPACE: "order_system"
```

**Terraform injection**:
```hcl
resource "oci_functions_function" "fn" {
  application_id     = oci_functions_application.app.id
  display_name       = "order-processor"
  image              = "${local.registry}/${local.image}:${local.tag}"
  memory_in_mbs      = 256
  timeout_in_seconds = 60

  config = {
    COMPARTMENT_OCID = var.compartment_ocid
    METRIC_NAMESPACE = "order_system_${var.environment}"  # prod / staging isolation
  }
}
```

---

## Pattern 5: Service Gateway in VCN for Private-Subnet Functions

**Degree of freedom**: Low (infrastructure — exact Terraform required)

```hcl
data "oci_core_services" "all_oci_services" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}

resource "oci_core_service_gateway" "fn_service_gw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "fn-service-gateway"

  services {
    service_id = data.oci_core_services.all_oci_services.services[0].id
  }
}

resource "oci_core_route_table" "private_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "private-route-table"

  route_rules {
    destination       = data.oci_core_services.all_oci_services.services[0].cidr_block
    destination_type  = "SERVICE_CIDR_BLOCK"
    network_entity_id = oci_core_service_gateway.fn_service_gw.id
  }
}
```

> **Impact of missing**: `MonitoringClient` throws `SocketTimeoutException` after ~30s. Function returns success but metrics are silently lost. No function invocation error is raised.

---

## Pattern 6: Configure Alarms on oci_faas Built-In Metrics (Zero-Code)

**Degree of freedom**: High (no application code — dashboard and alarm configuration)

**Built-in `oci_faas` metric catalog** (zero application code):

| Metric | Unit | Alert threshold |
|--------|------|----------------|
| `FunctionInvocationCount` | count | Sudden drop → upstream failure |
| `FunctionExecutionDuration` | ms | p99 > 80% of `timeout_in_seconds` |
| `FunctionThrottleCount` | count | Any sustained > 0 |
| `FunctionErrorCount` | count | Any sustained > 0 |
| `FunctionResponseCount` | count | 5xx spike |

**MQL query examples**:
```
# P99 execution duration over 5 minutes
FunctionExecutionDuration[5m]{resourceId="ocid1.fnfunc..."}.percentile(0.99)

# Throttle count — any non-zero is a capacity signal
FunctionThrottleCount[5m]{applicationId="ocid1.fnapp..."}.sum()
```

---

## Pattern 7: Alarm pending_duration ≥ PT2M on Production Alarms

**Degree of freedom**: Medium (Terraform template — duration values vary by metric type)

```hcl
# Error rate — 2 consecutive minutes prevents cold-start false alarms
resource "oci_monitoring_alarm" "fn_error_rate" {
  compartment_id        = var.compartment_ocid
  display_name          = "${var.function_name}-error-rate"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_faas"
  query                 = "FunctionErrorCount[1m]{resourceId=\"${local.fn_ocid}\"}.sum() > 0"
  severity              = "CRITICAL"
  pending_duration      = "PT2M"   # minimum for error metrics
  body                  = "Function ${var.function_name} errors detected."
  destinations          = [local.topic_id]
  message_format        = "ONS_OPTIMIZED"
}

# Duration p99 — 3 minutes to filter cold-start elevation
resource "oci_monitoring_alarm" "fn_duration_p99" {
  compartment_id        = var.compartment_ocid
  display_name          = "${var.function_name}-duration-p99"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_faas"
  query                 = "FunctionExecutionDuration[1m]{resourceId=\"${local.fn_ocid}\"}.percentile(0.99) > ${var.timeout_ms * 0.8}"
  severity              = "WARNING"
  pending_duration      = "PT3M"   # minimum for duration metrics
  body                  = "Function ${var.function_name} p99 duration approaching timeout."
  destinations          = [local.topic_id]
  message_format        = "ONS_OPTIMIZED"
}

# Throttle — sustained throttling indicates capacity breach
resource "oci_monitoring_alarm" "fn_throttle" {
  compartment_id        = var.compartment_ocid
  display_name          = "${var.function_name}-throttle"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_faas"
  query                 = "FunctionThrottleCount[5m]{applicationId=\"${local.app_ocid}\"}.sum() > 0"
  severity              = "ERROR"
  pending_duration      = "PT2M"
  body                  = "Function ${var.function_name} is being throttled."
  destinations          = [local.topic_id]
  message_format        = "ONS_OPTIMIZED"
}
```
