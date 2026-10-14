# Integration Patterns — logging-oci-java-functions

Full Maven POM, `logback.xml`, and lifecycle blueprint for OCI Java Functions with structured logging.

---

## Maven POM — Full Logging Stack

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>order-processor-fn</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <fdk.version>1.1.12</fdk.version>
        <oci.sdk.version>3.87.0</oci.sdk.version>
        <slf4j.version>2.0.16</slf4j.version>
        <logback.version>1.5.18</logback.version>
        <logstash.encoder.version>8.0</logstash.encoder.version>
        <java.version>11</java.version>
        <maven.compiler.source>${java.version}</maven.compiler.source>
        <maven.compiler.target>${java.version}</maven.compiler.target>
    </properties>

    <dependencyManagement>
        <dependencies>
            <!-- OCI Java SDK BOM — aligns ALL oci-java-sdk-* module versions -->
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
        <!-- FDK Java API -->
        <dependency>
            <groupId>com.fnproject.fn</groupId>
            <artifactId>api</artifactId>
            <version>${fdk.version}</version>
        </dependency>

        <!-- OCI Logging Ingestion (SDK write path) -->
        <dependency>
            <groupId>com.oracle.oci.sdk</groupId>
            <artifactId>oci-java-sdk-loggingingestion</artifactId>
        </dependency>
        <dependency>
            <groupId>com.oracle.oci.sdk</groupId>
            <artifactId>oci-java-sdk-common-httpclient-jersey3</artifactId>
        </dependency>

        <!-- SLF4J API -->
        <dependency>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-api</artifactId>
            <version>${slf4j.version}</version>
        </dependency>
        <!-- Logback implementation -->
        <dependency>
            <groupId>ch.qos.logback</groupId>
            <artifactId>logback-classic</artifactId>
            <version>${logback.version}</version>
        </dependency>
        <!-- JSON encoder for structured stdout -->
        <dependency>
            <groupId>net.logstash.logback</groupId>
            <artifactId>logstash-logback-encoder</artifactId>
            <version>${logstash.encoder.version}</version>
        </dependency>
        <!-- JUL → SLF4J bridge (routes OCI SDK internal logs through Logback) -->
        <dependency>
            <groupId>org.slf4j</groupId>
            <artifactId>jul-to-slf4j</artifactId>
            <version>${slf4j.version}</version>
        </dependency>
        <!-- JSON serialization (OCI SDK ships Jackson — reuse BOM version) -->
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
        </dependency>

        <!-- Testing -->
        <dependency>
            <groupId>com.fnproject.fn</groupId>
            <artifactId>testing-junit5</artifactId>
            <version>${fdk.version}</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.11.0</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.mockito</groupId>
            <artifactId>mockito-core</artifactId>
            <version>5.11.0</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-dependency-plugin</artifactId>
                <executions>
                    <execution>
                        <id>copy-dependencies</id>
                        <phase>package</phase>
                        <goals><goal>copy-dependencies</goal></goals>
                        <configuration>
                            <outputDirectory>${project.build.directory}/dependency</outputDirectory>
                            <includeScope>runtime</includeScope>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

---

## logback.xml — Production Configuration

`src/main/resources/logback.xml`:

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

    <!-- Suppress OCI SDK internal noise (connection pool, retry events) -->
    <logger name="com.oracle.bmc"     level="WARN"/>
    <logger name="com.oracle.bmc.http" level="ERROR"/>
    <logger name="org.apache.http"    level="WARN"/>
    <logger name="org.glassfish"      level="WARN"/>
</configuration>
```

---

## Lifecycle Blueprint — Full Function Implementation

```java
package com.example;

import ch.qos.logback.classic.Level;
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.loggingingestion.LoggingIngestionClient;
import com.oracle.bmc.loggingingestion.model.*;
import com.oracle.bmc.loggingingestion.requests.PutLogsRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.slf4j.bridge.SLF4JBridgeHandler;

import java.util.*;

public class OrderProcessorFunction {

    // ── COLD START (once per container lifetime) ────────────────────────
    private static final Logger log = LoggerFactory.getLogger(OrderProcessorFunction.class);
    private static LoggingIngestionClient loggingClient;
    private static String auditLogId;

    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        // 1. Bridge JUL → SLF4J
        java.util.logging.LogManager.getLogManager().reset();
        SLF4JBridgeHandler.removeHandlersForRootLogger();
        SLF4JBridgeHandler.install();

        // 2. Apply dynamic log level
        String level = ctx.getConfigurationByKey("LOG_LEVEL").orElse("INFO");
        ((ch.qos.logback.classic.Logger) LoggerFactory.getLogger(Logger.ROOT_LOGGER_NAME))
            .setLevel(Level.toLevel(level, Level.INFO));

        // 3. Init SDK clients (Resource Principal — zero credentials in image)
        var auth = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
        loggingClient = LoggingIngestionClient.builder().build(auth);

        // 4. Load required OCIDs from function config
        auditLogId = ctx.getConfigurationByKey("AUDIT_LOG_OCID")
            .orElseThrow(() -> new RuntimeException("AUDIT_LOG_OCID config required"));

        log.info("Function initialized at level={}", level);
    }

    // ── WARM INVOCATION (every call after cold start) ───────────────────
    public String handleRequest(String orderId) {
        MDC.put("orderId",   orderId);
        MDC.put("requestId", UUID.randomUUID().toString());
        List<LogEntry> auditEntries = new ArrayList<>();

        try {
            log.info("Order processing started");
            String result = processOrder(orderId);
            log.info("Order processing completed result={}", result);

            auditEntries.add(buildEntry("ORDER_PROCESSED",
                Map.of("orderId", orderId, "status", "SUCCESS")));
            return result;

        } catch (Exception e) {
            log.error("Order processing failed", e);
            auditEntries.add(buildEntry("ORDER_FAILED",
                Map.of("orderId", orderId, "error", e.getClass().getSimpleName())));
            throw new RuntimeException("Processing failed for " + orderId, e);

        } finally {
            flushAuditLogs(auditEntries);  // synchronous before return
            MDC.clear();                   // warm invocation safety
        }
    }

    // ── HELPERS ─────────────────────────────────────────────────────────
    private String processOrder(String orderId) {
        return "confirmed:" + orderId;
    }

    private LogEntry buildEntry(String type, Map<String, String> data) {
        try {
            String json = new com.fasterxml.jackson.databind.ObjectMapper()
                .writeValueAsString(Map.of("type", type, "data", data));
            return LogEntry.builder()
                .id(UUID.randomUUID().toString())
                .time(new Date())
                .data(json)
                .build();
        } catch (Exception e) {
            log.warn("Log entry build failed: {}", e.getMessage());
            return null;
        }
    }

    private void flushAuditLogs(List<LogEntry> entries) {
        List<LogEntry> valid = entries.stream().filter(Objects::nonNull).toList();
        if (valid.isEmpty()) return;
        try {
            loggingClient.putLogs(PutLogsRequest.builder()
                .logId(auditLogId)
                .putLogsDetails(PutLogsDetails.builder()
                    .specversion("1.0")
                    .logEntryBatches(List.of(LogEntryBatch.builder()
                        .entries(valid)
                        .source("order-processor-fn")
                        .type("com.example.audit")
                        .defaultlogentrytime(new Date())
                        .build()))
                    .build())
                .build());
        } catch (Exception e) {
            log.warn("Audit log flush failed (non-fatal): {}", e.getMessage());
        }
    }
}
```

---

## Connector Hub — Log Group → OCI Logging Analytics

```hcl
resource "oci_sch_service_connector" "fn_logs_to_la" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.app_name}-logs-to-la"
  state          = "ACTIVE"

  source {
    kind = "logging"
    log_sources {
      compartment_id = var.compartment_ocid
      log_group_id   = oci_logging_log_group.fn_log_group.id
      log_id         = oci_logging_log.fn_invoke_log.id
    }
  }

  target {
    kind                  = "loggingAnalytics"
    log_group_id          = var.log_analytics_log_group_ocid
    log_source_identifier = "OCI Function Invocation Logs"
  }
}
```

> **Note**: OCI Logging Analytics requires separate licensing. Confirm with the team before provisioning.

---

## func.yaml + Terraform Config Variables

```yaml
# func.yaml
schema_version: 20180708
name: order-processor
version: 0.0.1
runtime: java
entrypoint: com.example.OrderProcessorFunction::handleRequest
memory: 256
timeout: 60
config:
  LOG_LEVEL: "INFO"
  AUDIT_LOG_OCID: "INJECT_AT_DEPLOY_TIME"
```

```hcl
# Terraform: inject at deploy time — never hardcode OCIDs in source
resource "oci_functions_function" "fn" {
  application_id     = oci_functions_application.app.id
  display_name       = "order-processor"
  image              = "${local.registry}/${local.image_name}:${local.image_tag}"
  memory_in_mbs      = 256
  timeout_in_seconds = 60
  config = {
    LOG_LEVEL      = "INFO"
    AUDIT_LOG_OCID = oci_logging_log.fn_audit_log.id
  }
}
```
