# Never Do Patterns — monitoring-oci-java-functions

## Anti-Pattern 1: API Key Credentials Embedded in Docker Image

```java
// ❌ DON'T — private key baked into function container (OWASP A07:2021)
ConfigFileAuthenticationDetailsProvider provider =
    new ConfigFileAuthenticationDetailsProvider("/function/.oci/config", "DEFAULT");
MonitoringClient client = MonitoringClient.builder().build(provider);
```
**Impact**: Any developer with `OCIR:pull` permission extracts the private key → full tenancy API access.

```java
// ✅ DO — Resource Principal: zero credentials in code or image
ResourcePrincipalAuthenticationDetailsProvider auth =
    ResourcePrincipalAuthenticationDetailsProvider.builder().build();
MonitoringClient client = MonitoringClient.builder().build(auth);
```

---

## Anti-Pattern 2: MonitoringClient Created Per Invocation

```java
// ❌ DON'T — client created inside handleRequest (warm path)
public String handleRequest(String input) {
    var auth = ResourcePrincipalAuthenticationDetailsProvider.builder().build(); // HTTP call each time
    var client = MonitoringClient.builder().build(auth);                         // pool setup each time
    client.postMetricData(buildRequest());
    return "ok";
}
```
**Impact**: +150–400 ms latency per invocation; `BindException` under concurrency; HTTP 429 on metadata service.

```java
// ✅ DO — Static, initialized in @FnConfiguration (cold-start only)
private static MonitoringClient monitoringClient;

@FnConfiguration
public void configure(RuntimeContext ctx) {
    var auth = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
    monitoringClient = MonitoringClient.builder().build(auth);
}
```

---

## Anti-Pattern 3: Fire-and-Forget Metric Posts

```java
// ❌ DON'T — detached thread races with FDK container freeze
public String handleRequest(String input) {
    new Thread(() -> postMetric("OrderProcessed", 1.0, Map.of())).start();
    return "ok";
}

// ❌ ALSO DON'T — CompletableFuture not awaited before return
public String handleRequest(String input) {
    CompletableFuture.runAsync(() -> postMetric("OrderProcessed", 1.0, Map.of()));
    return "ok";
}
```
**Impact**: FDK may freeze container immediately after `handleRequest` returns → metric datapoints silently lost → dashboard gaps.

```java
// ✅ DO — Synchronous post before return; exception swallowed, never propagated
public String handleRequest(String input) {
    String result = processOrder(input);
    postMetric("OrderProcessed", 1.0, Map.of("status", "success")); // synchronous
    return result;
}
```

---

## Anti-Pattern 4: Flat `custom_metrics` Catch-All Namespace

```java
// ❌ DON'T — all functions share one flat namespace
MetricDataDetails.builder()
    .namespace("custom_metrics")  // shared by all functions and services
    .name("OrderProcessed")
    // ...
```
**Impact**: Alarm MQL requires complex dimension filters to isolate signals; metric name collisions across services; `ListMetrics` returns hundreds of unrelated entries at scale.

```java
// ✅ DO — Domain-scoped, environment-suffixed namespace
MetricDataDetails.builder()
    .namespace("order_system_prod")   // domain + environment isolation
    .name("OrderProcessed")
    .dimensions(Map.of("functionName", "order-processor"))
    // ...
```

---

## Anti-Pattern 5: Hardcoded COMPARTMENT_OCID or Namespace in Source

```java
// ❌ DON'T — hardcoded identifiers in source code
private static final String COMPARTMENT = "ocid1.compartment.oc1..aaaa...fixed";
private static final String NAMESPACE   = "prod_order_system";
```
**Impact**: Dev metrics appear in prod series (false FIRING alarms); requires recompilation per environment; leaks tenancy topology into version control.

```java
// ✅ DO — Read from RuntimeContext at cold start
@FnConfiguration
public void configure(RuntimeContext ctx) {
    compartmentId   = ctx.getConfigurationByKey("COMPARTMENT_OCID").orElseThrow(
        () -> new RuntimeException("COMPARTMENT_OCID required"));
    metricNamespace = ctx.getConfigurationByKey("METRIC_NAMESPACE").orElseThrow(
        () -> new RuntimeException("METRIC_NAMESPACE required"));
}
```

---

## Anti-Pattern 6: pending_duration = PT1M (Default) on Production Alarms

```hcl
# ❌ DON'T — pending_duration omitted (defaults to PT1M)
resource "oci_monitoring_alarm" "fn_error" {
  # pending_duration not set → PT1M
  query    = "FunctionErrorCount[1m]{functionId=\"...\"}.sum() > 0"
  severity = "CRITICAL"
}
```
**Impact**: Cold-start duration spikes and transient upstream failures trigger CRITICAL pages for single-point blips → alert fatigue → on-call desensitization → real incidents missed.

```hcl
# ✅ DO — Evidence-based pending_duration per metric type
resource "oci_monitoring_alarm" "fn_error" {
  pending_duration = "PT2M"   # error must persist 2 consecutive minutes
  query            = "FunctionErrorCount[1m]{functionId=\"...\"}.sum() > 0"
  severity         = "CRITICAL"
}
```

---

## Anti-Pattern 7: Datapoint Timestamps Older Than 2 Hours

```java
// ❌ DON'T — stale timestamp from buffered event processing
Datapoint.builder()
    .timestamp(event.getOriginalTimestamp())  // may be hours old
    .value(1.0)
    .build();
```
**Impact**: OCI Monitoring silently drops datapoints with timestamp > 2 hours old at ingestion. `PostMetricData` returns **HTTP 200** with `rejectedMetricsData` — not an HTTP error. With `NonAtomic` batch and no rejection check, loss is invisible.

```java
// ✅ DO — Use current timestamp; encode event age as metric value for SLA tracking
Datapoint.builder()
    .timestamp(new Date())       // ingestion time; always within 2-hour window
    .value(processingLagMs)      // encode event age as value for SLA metrics
    .build();
```
