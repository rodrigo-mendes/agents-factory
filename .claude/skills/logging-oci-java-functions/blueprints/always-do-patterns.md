# Always Do Patterns — logging-oci-java-functions

Seven mandatory patterns. Execute all seven for every OCI Java Function that uses logging.

---

## Pattern 1: Enable OCI Logging Log Resource on Function Application

**Why**: The FDK runtime captures `stdout`/`stderr` but the platform **silently discards** them unless an OCI `SERVICE` Log resource with `category = "invoke"` is associated with the Function Application. Most common root cause of "no logs visible" issues.

```hcl
resource "oci_functions_application" "app" {
  compartment_id = var.compartment_ocid
  display_name   = var.app_name
  subnet_ids     = [var.subnet_ocid]
}

resource "oci_logging_log_group" "fn_log_group" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.app_name}-log-group"
}

resource "oci_logging_log" "fn_invoke_log" {
  display_name = "${var.app_name}-invoke-log"
  log_group_id = oci_logging_log_group.fn_log_group.id
  log_type     = "SERVICE"

  configuration {
    source {
      category    = "invoke"
      resource    = oci_functions_application.app.id
      service     = "functions"
      source_type = "OCISERVICE"
    }
    compartment_id = var.compartment_ocid
  }
  is_enabled         = true
  retention_duration = 30   # days; max 180
}
```

Console path: OCI Console → Functions → Applications → [app] → Logs → Enable

---

## Pattern 2: Structured JSON Logging to stdout

**Why**: OCI Logging stores stdout verbatim as a string. Unstructured text is unsearchable and cannot trigger MQL-based alarms. `logstash-logback-encoder` produces ECS-compatible JSON with zero custom code.

**Maven** (`pom.xml`):
```xml
<dependency>
    <groupId>org.slf4j</groupId>
    <artifactId>slf4j-api</artifactId>
    <version>${slf4j.version}</version>    <!-- 2.0.16 -->
</dependency>
<dependency>
    <groupId>ch.qos.logback</groupId>
    <artifactId>logback-classic</artifactId>
    <version>${logback.version}</version>  <!-- 1.5.18 -->
</dependency>
<dependency>
    <groupId>net.logstash.logback</groupId>
    <artifactId>logstash-logback-encoder</artifactId>
    <version>${logstash.encoder.version}</version>  <!-- 8.0 -->
</dependency>
```

**`src/main/resources/logback.xml`**:
```xml
<configuration>
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="net.logstash.logback.encoder.LogstashEncoder">
            <timestampPattern>yyyy-MM-dd'T'HH:mm:ss.SSSZ</timestampPattern>
            <customFields>{"service":"order-processor","cloud":"oci"}</customFields>
        </encoder>
    </appender>
    <root level="${LOG_LEVEL:-INFO}">
        <appender-ref ref="STDOUT"/>
    </root>
    <logger name="com.oracle.bmc" level="WARN"/>
    <logger name="org.apache.http" level="WARN"/>
</configuration>
```

**Function code**:
```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

public class OrderProcessorFunction {
    private static final Logger log = LoggerFactory.getLogger(OrderProcessorFunction.class);

    public String handleRequest(String orderId) {
        MDC.put("orderId", orderId);
        try {
            log.info("Processing order");
            return processOrder(orderId);
        } finally {
            MDC.clear();  // Pattern 3
        }
    }
}
```

---

## Pattern 3: MDC Cleanup on Every Invocation

**Why**: The FDK Java runtime reuses the same JVM thread across warm invocations. MDC values set in invocation N persist into N+1 unless cleared — a silent log-correlation and GDPR compliance hazard.

```java
public String handleRequest(String input) {
    MDC.put("requestId", java.util.UUID.randomUUID().toString());
    MDC.put("orderId", input);
    try {
        return process(input);
    } finally {
        MDC.clear();  // ✅ mandatory — executes even on exception
    }
}
```

---

## Pattern 4: JUL-to-SLF4J Bridge

**Why**: The OCI Java SDK uses `java.util.logging` (JUL) internally. Without the bridge, SDK messages bypass Logback and print unstructured text to stderr.

**Maven**:
```xml
<dependency>
    <groupId>org.slf4j</groupId>
    <artifactId>jul-to-slf4j</artifactId>
    <version>${slf4j.version}</version>  <!-- must match slf4j-api version: 2.0.16 -->
</dependency>
```

**Activation** (once per cold start in `@FnConfiguration`):
```java
import org.slf4j.bridge.SLF4JBridgeHandler;
import java.util.logging.LogManager;

@FnConfiguration
public void configure(RuntimeContext ctx) {
    LogManager.getLogManager().reset();
    SLF4JBridgeHandler.removeHandlersForRootLogger();
    SLF4JBridgeHandler.install();
    // All java.util.logging calls now route through Logback → JSON stdout
}
```

---

## Pattern 5: Resource Principal for LoggingIngestionClient

**Why**: `LoggingIngestionClient.putLogs()` requires IAM authentication. Resource Principal is the only approved mechanism inside OCI Functions — no `~/.oci/config`, no PEM file in the Docker image.

> For full IAM Dynamic Group + IAM policy Terraform, see [`observing-oci-java-functions`] — Resource Principal Auth.

**IAM policy statement** (minimum required):
```
allow dynamic-group <fn-dg-name> to use log-content in compartment id <compartment-ocid>
```

**Cold-start init** (in `@FnConfiguration` or `static {}`):
```java
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.loggingingestion.LoggingIngestionClient;

private static LoggingIngestionClient loggingClient;
private static String auditLogId;

@FnConfiguration
public void configure(RuntimeContext ctx) {
    var auth = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
    loggingClient = LoggingIngestionClient.builder().build(auth);
    auditLogId = ctx.getConfigurationByKey("AUDIT_LOG_OCID")
        .orElseThrow(() -> new RuntimeException("AUDIT_LOG_OCID config required"));
}
```

---

## Pattern 6: PutLogs — Synchronous Batch Before Return

**Why**: The FDK may freeze the container immediately after `handleRequest` returns. Background threads do not have a completion guarantee. Collect entries during invocation; flush once before returning.

```java
import com.oracle.bmc.loggingingestion.model.*;
import com.oracle.bmc.loggingingestion.requests.PutLogsRequest;
import java.util.*;

// Collect entries during invocation
List<LogEntry> auditEntries = new ArrayList<>();

// Build an entry
auditEntries.add(LogEntry.builder()
    .id(UUID.randomUUID().toString())
    .time(new Date())
    .data("{\"type\":\"ORDER_PROCESSED\",\"orderId\":\"" + orderId + "\"}")
    .build());

// Flush synchronously before return (in finally block)
private void flushAuditLogs(List<LogEntry> entries) {
    if (entries.isEmpty()) return;
    try {
        loggingClient.putLogs(PutLogsRequest.builder()
            .logId(auditLogId)
            .putLogsDetails(PutLogsDetails.builder()
                .specversion("1.0")
                .logEntryBatches(List.of(LogEntryBatch.builder()
                    .entries(entries)
                    .source("order-processor-fn")
                    .type("com.example.audit")
                    .defaultlogentrytime(new Date())
                    .build()))
                .build())
            .build());
    } catch (Exception e) {
        log.warn("Audit log flush failed (non-fatal): {}", e.getMessage());
        // ✅ Observability failure must NOT break function execution
    }
}
```

---

## Pattern 7: Log-Level via Function Environment Variable

**Why**: Hardcoded log levels require Docker image rebuild to change. Externalizing via function config enables runtime-level control without redeployment.

**`logback.xml`** (already shown in Pattern 2 — uses `${LOG_LEVEL:-INFO}`).

**`@FnConfiguration`** (apply at cold start):
```java
@FnConfiguration
public void configure(RuntimeContext ctx) {
    String level = ctx.getConfigurationByKey("LOG_LEVEL").orElse("INFO");
    ch.qos.logback.classic.Logger root =
        (ch.qos.logback.classic.Logger) LoggerFactory.getLogger(Logger.ROOT_LOGGER_NAME);
    root.setLevel(ch.qos.logback.classic.Level.toLevel(level, ch.qos.logback.classic.Level.INFO));
    log.info("Log level set to {}", level);
}
```

**Terraform** (per-function config):
```hcl
resource "oci_functions_function" "fn" {
  config = {
    LOG_LEVEL      = "INFO"             # set "DEBUG" for incident troubleshooting
    AUDIT_LOG_OCID = oci_logging_log.fn_audit_log.id
  }

}
```

---

## Worked example (from the reference PoC)

The following snippets are extracted from `libs/obs-commons/` in the PoC. They show how
`LoggingBridge` and `ObservabilityHelper` implement Patterns 4, 1 (JUL bridge + shared facade).

### LoggingBridge — Pattern 4: JUL-to-SLF4J bridge (one-time static install)

```java
// from libs/obs-commons/src/main/java/com/brx/functions/common/obs/LoggingBridge.java

public final class LoggingBridge {

    private LoggingBridge() {}

    // Called once at class-load time via ObservabilityHelper static block.
    // Without this, OCI SDK and FDK internal java.util.logging messages bypass
    // Logback and appear as unstructured text in stderr — not captured by OCI Logging.
    public static void install() {
        try {
            LogManager.getLogManager().reset();
            SLF4JBridgeHandler.removeHandlersForRootLogger();
            SLF4JBridgeHandler.install();
            log.info("JUL-to-SLF4J bridge successfully installed");
        } catch (Exception e) {
            log.error("Failed to install JUL-to-SLF4J bridge: {}", e.getMessage());
        }
    }
}
```

### ObservabilityHelper — shared facade wiring logging + metrics + tracing

```java
// from libs/obs-commons/src/main/java/com/brx/functions/common/obs/ObservabilityHelper.java

public class ObservabilityHelper {

    private static final MetricsPublisher metrics = new MetricsPublisher();
    private static final TracingSupport   tracing = new TracingSupport();

    // Bridge installed once at class-load — covers all three pub/sub services that
    // depend on this shared library (brx-fn-obs-commons).
    static { LoggingBridge.install(); }

    // Single configure() entry point for @FnConfiguration — metrics short-circuits
    // tracing setup if the compartment is missing or environment is "test".
    public static void configure(RuntimeContext ctx) {
        String environment = ctx.getConfigurationByKey("ENVIRONMENT").orElse("dev");
        if (!metrics.configure(ctx, environment)) return; // tracing skipped too
        tracing.configure(ctx, environment);
    }

    // Logging is implicit (SLF4J + LoggingBridge installed above).
    // Metrics and tracing are delegated to their respective collaborators.
    public static void postMetric(String name, double value, Map<String, String> dimensions) {
        metrics.postMetric(name, value, dimensions);
    }
}
```

**Why this matters for logging**:
- `LoggingBridge.install()` in the `static {}` block ensures the bridge is active before any
  SDK class is loaded — OCI SDK log output appears in OCI Logging alongside application logs.
- Single `configure()` call in `@FnConfiguration` keeps cold-start linear: no per-invocation
  client construction, no race conditions from parallel SDK initializations.
