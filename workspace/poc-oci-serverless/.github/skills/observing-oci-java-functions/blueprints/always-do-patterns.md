# Always Do Patterns — OCI Java Functions Observability

## 1. Resource Principal Authentication — Never Hardcode Credentials

**Degree of freedom**: Low (exact code — fragile; any deviation risks credential exposure)

**Why**: OCI Functions has no `~/.oci/config`. Bundling API key PEM files in Docker images means any developer with OCIR `pull` access can extract the key, granting unrestricted OCI API access.

**IAM prerequisite**: Create a Dynamic Group matching the function OCID, then grant least-privilege policies:
```
allow dynamic-group <dg-name> to use metrics in compartment <compartment>
allow dynamic-group <dg-name> to use log-content in compartment <compartment>
```

```java
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.monitoring.MonitoringClient;

public class MyFunction {
    private static final ResourcePrincipalAuthenticationDetailsProvider AUTH;
    private static final MonitoringClient MONITORING_CLIENT;

    static {
        // Fails fast at cold-start if Dynamic Group / IAM policy is missing
        AUTH = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
        MONITORING_CLIENT = MonitoringClient.builder().build(AUTH);
    }
}
```

**Source**: [OCI Functions Resource Principal](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingociresources.htm)

---

## 2. SDK Client Initialization in @FnConfiguration (Cold-Start Optimization)

**Degree of freedom**: Low (exact pattern — per-invocation creation has measurable performance penalty)

**Why**: FDK Java keeps the JVM alive between invocations. `@FnConfiguration` runs once at cold-start. Creating SDK clients per invocation adds 150–400 ms (Resource Principal metadata HTTP call + connection pool setup) and can exhaust ephemeral TCP ports.

```java
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.monitoring.MonitoringClient;
import com.oracle.bmc.loggingingestion.LoggingClient;

public class ObservableFunction {
    private static MonitoringClient monitoringClient;
    private static LoggingClient loggingClient;
    private static String compartmentId;
    private static String metricNamespace;

    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        var auth = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
        monitoringClient = MonitoringClient.builder().build(auth);
        loggingClient    = LoggingClient.builder().build(auth);
        compartmentId   = ctx.getConfigurationByKey("COMPARTMENT_OCID")
                             .orElseThrow(() -> new RuntimeException("COMPARTMENT_OCID required"));
        metricNamespace = ctx.getConfigurationByKey("METRIC_NAMESPACE").orElse("custom_app");
    }
}
```

**Source**: [FDK Java FnConfiguration](https://github.com/fnproject/docs/blob/master/fdks/fdk-java/FunctionConfiguration.md)

---

## 3. Structured JSON Logging to stdout

**Degree of freedom**: Medium (exact JSON structure required; helper implementation may vary)

**Why**: OCI Logging captures stdout verbatim. Unstructured `println` blocks OCI Logging Analytics field extraction and makes alarm MQL queries on log content impossible.

```java
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;

public class ObservableFunction {
    private static final ObjectMapper MAPPER = new ObjectMapper();

    private static void logStructured(String level, String message, Map<String, String> fields) {
        try {
            var entry = new LinkedHashMap<String, Object>();
            entry.put("timestamp", java.time.Instant.now().toString());
            entry.put("level", level);
            entry.put("message", message);
            entry.putAll(fields);
            System.out.println(MAPPER.writeValueAsString(entry));
        } catch (Exception e) {
            System.err.println("{\"level\":\"ERROR\",\"message\":\"Log serialization failed\"}");
        }
    }

    public String handleRequest(String input) {
        logStructured("INFO", "Function invoked", Map.of("inputSize", String.valueOf(
            input != null ? input.length() : 0)));
        return "ok";
    }
}
```

**Source**: [OCI Functions Logging](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionslogging.htm)

---

## 4. Enable OCI Logging on the Function Application (Terraform)

**Degree of freedom**: Low (exact Terraform resource — missing it causes silent log loss)

**Why**: stdout/stderr are silently discarded unless `oci_logging_log` is configured with `source_type = "OCISERVICE"` for the Functions application. No error is surfaced; the function invokes successfully with no observable output.

```hcl
resource "oci_functions_application" "app" {
  compartment_id = var.compartment_ocid
  display_name   = var.app_name
  subnet_ids     = [var.subnet_ocid]
}

resource "oci_logging_log_group" "fn_log_group" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.app_name}-logs"
}

resource "oci_logging_log" "fn_log" {
  display_name = "${var.app_name}-invoke-log"
  log_group_id = oci_logging_log_group.fn_log_group.id
  log_type     = "SERVICE"

  configuration {
    source {
      category    = "invoke"
      resource    = oci_functions_application.app.id
      service     = "functions"
      source_type = "OCISERVICE"  # MANDATORY
    }
    compartment_id = var.compartment_ocid
  }
  is_enabled         = true
  retention_duration = 30  # days; max 180
}
```

**Source**: [OCI Logging for Functions](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionslogging.htm)

---

## 5. Custom Metrics via OCI Monitoring (PostMetricData)

**Degree of freedom**: Medium (exact API call structure required; metric names and dimensions are application-specific)

**Why**: Built-in `oci_faas` namespace metrics cover invocation counts and duration only. Business-level KPIs (error rates, queue depth, SLA violations) require custom metric posts. Metrics must be posted synchronously during invocation or data points are permanently lost.

```xml
<!-- pom.xml — use BOM (Pattern 6) to omit version here -->
<dependency>
    <groupId>com.oracle.oci.sdk</groupId>
    <artifactId>oci-java-sdk-monitoring</artifactId>
</dependency>
```

```java
import com.oracle.bmc.monitoring.MonitoringClient;
import com.oracle.bmc.monitoring.model.*;
import com.oracle.bmc.monitoring.requests.PostMetricDataRequest;
import java.util.*;

// monitoringClient initialized in @FnConfiguration (Pattern 2)
private void postMetric(String metricName, double value, Map<String, String> dimensions) {
    try {
        var request = PostMetricDataRequest.builder()
            .postMetricDataDetails(PostMetricDataDetails.builder()
                .metricData(List.of(MetricDataDetails.builder()
                    .compartmentId(compartmentId)
                    .namespace(metricNamespace)
                    .name(metricName)
                    .dimensions(dimensions)
                    .datapoints(List.of(Datapoint.builder()
                        .timestamp(new Date())
                        .value(value)
                        .count(1)
                        .build()))
                    .build()))
                .batchAtomicity(PostMetricDataDetails.BatchAtomicity.NonAtomic)
                .build())
            .build();
        monitoringClient.postMetricData(request);
    } catch (Exception e) {
        // Observability failure MUST NOT break the function
        System.err.println("{\"level\":\"WARN\",\"message\":\"Metric post failed\",\"metric\":\"" + metricName + "\"}");
    }
}
```

**Source**: [OCI Monitoring API — PostMetricData](https://github.com/oracle/oci-java-sdk/blob/master/bmc-examples/src/main/java/MonitoringMetricPostExample.java)

---

## 6. Use OCI SDK BOM for Version Alignment

**Degree of freedom**: Low (exact Maven declaration — omitting BOM causes classpath conflicts at cold-start)

**Why**: OCI Java SDK has 80+ modules. Declaring any module version individually risks version drift across the classpath, causing `NoClassDefFoundError` or `ClassCastException` at cold-start.

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
        <groupId>com.fnproject.fn</groupId>
        <artifactId>api</artifactId>
        <version>${fdk.version}</version>
    </dependency>
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-monitoring</artifactId>
        <!-- version managed by BOM -->
    </dependency>
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-loggingingestion</artifactId>
    </dependency>
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-common-httpclient-jersey3</artifactId>
    </dependency>
</dependencies>
```

**Source**: [OCI Java SDK BOM](https://github.com/oracle/oci-java-sdk)

---

## 7. Inject Observability Config via Function Environment Variables

**Degree of freedom**: Medium (exact keys recommended; values are environment-specific)

**Why**: APM endpoints, compartment OCIDs, metric namespaces, and log group OCIDs differ per environment. Hardcoding them means redeployment for every environment change and exposes internal OCI topology in source code.

```yaml
# func.yaml
schema_version: 20180708
name: order-processor
version: 0.0.1
runtime: java
entrypoint: com.example.OrderProcessor::handleRequest
memory: 256
timeout: 60
config:
  COMPARTMENT_OCID: "INJECT_AT_DEPLOY_TIME"
  METRIC_NAMESPACE: "order_system"
  APM_DATA_UPLOAD_ENDPOINT: "INJECT_AT_DEPLOY_TIME"
  APM_PRIVATE_DATA_KEY: "INJECT_AT_DEPLOY_TIME"
```

```hcl
# Terraform equivalent
resource "oci_functions_function" "fn" {
  application_id     = oci_functions_application.app.id
  display_name       = "order-processor"
  image              = "${local.registry}/${local.image_name}:${local.image_tag}"
  memory_in_mbs      = 256
  timeout_in_seconds = 60
  config = {
    COMPARTMENT_OCID         = var.compartment_ocid
    METRIC_NAMESPACE         = "order_system"
    APM_DATA_UPLOAD_ENDPOINT = var.apm_data_upload_endpoint
    APM_PRIVATE_DATA_KEY     = var.apm_private_data_key  # inject from OCI Vault
  }
}
```

**Accessing in Java**:
```java
@FnConfiguration
public void configure(RuntimeContext ctx) {
    compartmentId = ctx.getConfigurationByKey("COMPARTMENT_OCID")
                       .orElseThrow(() -> new RuntimeException("COMPARTMENT_OCID required"));
}
```

**Source**: [FDK Java — FunctionConfiguration](https://github.com/fnproject/docs/blob/master/fdks/fdk-java/FunctionConfiguration.md)
