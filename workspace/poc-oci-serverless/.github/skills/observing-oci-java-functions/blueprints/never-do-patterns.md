# Never Do Patterns — OCI Java Functions Observability

## 1. Hardcode OCI Credentials in Source Code or Docker Image

**Impact**: Any developer with OCIR `pull` access can extract the private key. The key grants unrestricted OCI API access — not scoped to the function's permissions. Data breach, resource abuse, unauthorized API calls.

```java
// ❌ DON'T — API Key in Dockerfile or source
// private_key_path = "/function/oci_api_key.pem"  // PEM bundled in image
// fingerprint      = "aa:bb:cc:..."                // visible in image layers
```

```java
// ✅ DO — Resource Principal (zero credentials in code or image)
ResourcePrincipalAuthenticationDetailsProvider provider =
    ResourcePrincipalAuthenticationDetailsProvider.builder().build();
MonitoringClient client = MonitoringClient.builder().build(provider);
```

**Source**: [OCI Functions Security Best Practices](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionssecuritybestpractices.htm)

---

## 2. Create SDK Clients Per Invocation

**Impact**: Resource Principal initialization makes an HTTP call to the metadata service on each creation. `MonitoringClient` sets up a connection pool. Per-invocation creation adds 150–400 ms overhead per call and can cause `java.net.BindException` under sustained load.

```java
// ❌ DON'T — SDK client created on every warm invocation
public String handleRequest(String input) {
    var auth = ResourcePrincipalAuthenticationDetailsProvider.builder().build();  // ❌ HTTP call every time
    var client = MonitoringClient.builder().build(auth);                          // ❌ new pool every time
    // ...
}
```

```java
// ✅ DO — Static initialization at cold-start via @FnConfiguration
private static MonitoringClient MONITORING_CLIENT;

@FnConfiguration
public void configure(RuntimeContext ctx) {
    var auth = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
    MONITORING_CLIENT = MonitoringClient.builder().build(auth);
    // Reused on every warm invocation — zero overhead
}
```

**Source**: [FDK Java FnConfiguration](https://github.com/fnproject/docs/blob/master/fdks/fdk-java/FunctionConfiguration.md)

---

## 3. Fire-and-Forget Threads for Metric or Log Writes

**Impact**: The FDK Java runtime may freeze the container immediately after `handleRequest` returns. Detached threads have no completion guarantee. Metric and log data points are silently lost — dashboards show zeros under load.

```java
// ❌ DON'T — Detached thread for metric post
public String handleRequest(String input) {
    new Thread(() -> postMetric("errors", 1.0)).start();  // ❌ race with container freeze
    return "ok";
}
```

```java
// ✅ DO — Synchronous metric post before returning; catch and log, never rethrow
public String handleRequest(String input) {
    try {
        postMetric("processedItems", 1.0, Map.of("type", "order"));
    } catch (Exception e) {
        // Observability failure must never fail the function
        System.err.println("{\"level\":\"WARN\",\"message\":\"Metric post failed\",\"error\":\""
            + e.getMessage() + "\"}");
    }
    return "ok";
}
```

**Source**: [Fn Project container lifecycle](https://github.com/fnproject/fn)

---

## 4. Expose APM Private Data Key in Function Logs

**Impact**: OCI Logging is searchable via Console and API, and may be forwarded to OCI Logging Analytics or external SIEM. A leaked Private Data Key allows unauthorized trace uploads that inflate APM costs and corrupt trace data. OWASP A02:2021 Cryptographic Failures.

```java
// ❌ DON'T — Log all config variables (includes secrets)
public void configure(RuntimeContext ctx) {
    System.out.println("Config loaded: " + ctx.getConfiguration());  // ❌ logs APM keys, OCIDs, etc.
}
```

```java
// ✅ DO — Log only non-sensitive, operational config keys
public void configure(RuntimeContext ctx) {
    String namespace = ctx.getConfigurationByKey("METRIC_NAMESPACE").orElse("default");
    logStructured("INFO", "Config loaded", Map.of("namespace", namespace));
    // Never log: APM_PRIVATE_DATA_KEY, COMPARTMENT_OCID, connection strings
}
```

**Source**: [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

---

## 5. Post N Individual Metrics in a Loop Near Function Timeout

**Impact**: OCI Functions has a configurable timeout (default 30s). Synchronous SDK calls near the end of a long-running function get killed mid-flight, producing partial metric series, phantom dashboard gaps, and `FunctionTimedOut` errors.

```java
// ❌ DON'T — N individual PostMetricData calls; last ones hit timeout
public String handleRequest(String[] items) {
    process(items);
    for (String item : items) {
        postMetric("itemProcessed", 1.0);  // ❌ N calls; last calls may be killed
    }
    return "ok";
}
```

```java
// ✅ DO — Batch metrics; add elapsed-time guard; single PostMetricData call
public String handleRequest(String[] items) {
    long start = System.currentTimeMillis();
    int count = 0;
    for (String item : items) {
        process(item);
        count++;
        if (System.currentTimeMillis() - start > 25_000) {  // leave 5s buffer for observability
            break;
        }
    }
    // Single batched metric post (max 50 MetricDataDetails per request)
    postMetric("itemsProcessed", count, Map.of("function", "batch-processor"));
    return "processed:" + count;
}
```

**Source**: [OCI Functions Timeout Configuration](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscreatingfunctions.htm)

---

## 6. Use APM Public Data Key for Server-Side Functions

**Impact**: Public Data Keys are write-only and restricted to browser/mobile telemetry endpoints. Server-side span uploads targeting the public key endpoint fail silently — no error is returned. APM Trace Explorer remains empty despite correctly written tracing code.

```yaml
# ❌ DON'T — Public data key in server-side function config
config:
  APM_PUBLIC_DATA_KEY: "oci:apm:public:..."   # write-only; server spans rejected silently
```

```yaml
# ✅ DO — Private data key for server-side; injected from OCI Vault at deploy time
config:
  APM_PRIVATE_DATA_KEY: "INJECT_FROM_OCI_VAULT"
```

```java
// OpenTelemetry OTLP headers — use Private Data Key
// OTEL_EXPORTER_OTLP_HEADERS="Authorization=dataKey <APM_PRIVATE_DATA_KEY>"
```

**Source**: [OCI APM Data Key Types](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/create-apm-domain.html)
