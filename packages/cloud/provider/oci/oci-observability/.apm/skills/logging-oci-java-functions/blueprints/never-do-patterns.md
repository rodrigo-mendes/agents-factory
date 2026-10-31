# Never Do Patterns — logging-oci-java-functions

Six forbidden patterns. Each shows ❌ wrong code, ✅ correct alternative, and security/operational impact.

---

## Anti-Pattern 1: No OCI Log Resource on Function Application

```hcl
# ❌ DON'T — Function application with no associated Log resource
resource "oci_functions_application" "app" {
  compartment_id = var.compartment_ocid
  display_name   = "my-app"
  subnet_ids     = [var.subnet_ocid]
  # No oci_logging_log resource — stdout/stderr silently discarded
}
```

```hcl
# ✅ DO — Always provision Log resource alongside Application
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
  retention_duration = 30
}
```

**Impact**: Zero log visibility in OCI Console and OCI Logging despite correct function code. No error is surfaced — all log output is permanently lost.

---

## Anti-Pattern 2: Log4j2 Version < 2.17.1 (Log4Shell)

```xml
<!-- ❌ DON'T — Vulnerable Log4j2 version -->
<dependency>
    <groupId>org.apache.logging.log4j</groupId>
    <artifactId>log4j-core</artifactId>
    <version>2.14.1</version>  <!-- CRITICAL CVE-2021-44228 (CVSS 10.0) -->
</dependency>
```

```xml
<!-- ✅ DO — Use Log4j2 BOM to pin all modules to 2.24.x -->
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.apache.logging.log4j</groupId>
            <artifactId>log4j-bom</artifactId>
            <version>2.24.3</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

Check for vulnerable transitive deps before every release:
```bash
mvn dependency:tree | grep log4j
# Any version < 2.17.1 → block deployment
```

**Impact**: OWASP A06:2021 — Remote Code Execution via JNDI lookup in log messages. Severity: **CRITICAL (CVSS 10.0)**. OCI Functions processes untrusted external payloads — critical exposure vector.

---

## Anti-Pattern 3: Logging PII or Credentials to stdout

```java
// ❌ DON'T — Log all request data including sensitive fields
public String handleRequest(Map<String, String> request) {
    log.info("Request: {}", request);               // may contain passwords, card numbers
    log.debug("Config: {}", ctx.getConfiguration()); // logs ALL config keys including secrets
    return process(request);
}
```

```java
// ✅ DO — Log only non-sensitive identifiers
public String handleRequest(Map<String, String> request) {
    String orderId = request.get("orderId");   // safe — business identifier, not PII
    log.info("Request received for orderId={}", orderId);
    // Never log: passwords, tokens, full card numbers, SSNs, full email addresses, OCIDs
    return process(request);
}
```

**Impact**: GDPR Article 5(1)(f) breach notification obligation + OWASP A09:2021 Security Logging Failures. OCI Logging is searchable and can be forwarded to external SIEM via Connector Hub — any logged secret becomes extractable.

---

## Anti-Pattern 4: MDC Not Cleared Between Warm Invocations

```java
// ❌ DON'T — MDC set but never cleared
public String handleRequest(String orderId) {
    MDC.put("orderId", orderId);
    return processOrder(orderId);
    // MDC.clear() missing — next warm invocation inherits stale orderId
}
```

```java
// ✅ DO — Always clear MDC in a finally block
public String handleRequest(String orderId) {
    MDC.put("orderId", orderId);
    MDC.put("requestId", UUID.randomUUID().toString());
    try {
        return processOrder(orderId);
    } finally {
        MDC.clear();  // executes even on exception
    }
}
```

**Impact**: Silent log-correlation corruption — debugging leads to the wrong invocation's context. GDPR risk if `userId`/`orderId` leaks across different users' requests in a multi-tenant function.

---

## Anti-Pattern 5: Unstructured System.out.println

```java
// ❌ DON'T — Plain-text stdout
public String handleRequest(String orderId) {
    System.out.println("Processing order: " + orderId);  // no level, no fields, no timestamp
    System.out.println("ERROR: " + e.getMessage());      // not parseable
    return "ok";
}
```

```java
// ✅ DO — SLF4J + Logback JSON encoder (see always-do-patterns.md, Pattern 2)
private static final Logger log = LoggerFactory.getLogger(MyFunction.class);

public String handleRequest(String orderId) {
    MDC.put("orderId", orderId);
    try {
        log.info("Processing order");
        // Produces: {"timestamp":"...","level":"INFO","message":"Processing order","orderId":"..."}
        return "ok";
    } finally {
        MDC.clear();
    }
}
```

**Impact**: OCI Logging stores output as a single unstructured `data` string. No severity filtering, no field extraction for OCI Logging Analytics, no MQL alarm capability, no anomaly detection. Entire observability value of OCI Logging is lost.

---

## Anti-Pattern 6: Fire-and-Forget Thread for PutLogs

```java
// ❌ DON'T — Background thread for audit log write
public String handleRequest(String input) {
    new Thread(() -> putAuditLog("order", input)).start();  // may not complete before container freeze
    return "ok";
}
```

```java
// ✅ DO — Synchronous call before return; failure is non-fatal
public String handleRequest(String input) {
    String result = process(input);
    try {
        putAuditLog("order", input);  // synchronous — guaranteed to complete
    } catch (Exception e) {
        log.warn("Audit log write failed — non-fatal: {}", e.getMessage());
        // ✅ Do NOT re-throw — observability failure must not break function execution
    }
    return result;
}
```

**Impact**: Silent audit log loss. FDK container may freeze immediately after `handleRequest` returns — the background thread never completes. Compliance violation for PCI/SOC2/HIPAA audit trail requirements.
