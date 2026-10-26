# Evaluation Scenarios — monitoring-oci-java-functions

## Scenario 1: Canonical — Custom Metric for Order Processing Function

```json
{
  "skills": ["monitoring-oci-java-functions"],
  "query": "Add a custom metric 'orders_processed' (count) to my OrderProcessorFunction that tracks successful vs failed orders by item category. The function runs in a private subnet.",
  "expected_behavior": [
    "Initializes MonitoringClient once in @FnConfiguration (NOT per invocation)",
    "Uses ResourcePrincipalAuthenticationDetailsProvider — no API keys",
    "Calls client.setEndpoint('https://telemetry-ingestion.<region>.oraclecloud.com') after build(provider)",
    "Injects COMPARTMENT_OCID and METRIC_NAMESPACE via function config env vars — NOT hardcoded",
    "Batches MetricDataDetails in a single PostMetricDataRequest using BatchAtomicity.NonAtomic",
    "Checks rejectedMetricsData in the response and logs any rejected entries",
    "Notes that a Service Gateway (not Internet Gateway) is required for private subnet egress to telemetry-ingestion endpoint"
  ]
}
```

---

## Scenario 2: Edge — Datapoint Timestamp Drift

```json
{
  "skills": ["monitoring-oci-java-functions"],
  "query": "My function processes batches of historical records and posts metrics with the original event timestamps. Some records are from 3 hours ago. Why are my metrics not appearing in the dashboard?",
  "expected_behavior": [
    "Identifies that OCI Monitoring silently drops datapoints with timestamps older than 2 hours",
    "Clarifies that PostMetricData returns HTTP 200 with rejectedMetricsData — NOT an HTTP error — making this failure invisible without response inspection",
    "Recommends using current timestamp (Date.from(Instant.now())) for the metric datapoint, not the event's business timestamp",
    "Suggests encoding business event time as a metric dimension or custom attribute instead",
    "Shows the rejectedMetricsData check pattern so the caller detects silent drops"
  ]
}
```

---

## Scenario 3: Edge — oci_faas Alarm Not Firing

```json
{
  "skills": ["monitoring-oci-java-functions"],
  "query": "I created an alarm on oci_faas.FunctionErrorCount using dimension 'functionId' equal to my function OCID but it never fires even though I see errors in the logs.",
  "expected_behavior": [
    "Identifies that 'functionId' does NOT exist as an oci_faas dimension — this is a live-validated gotcha",
    "Specifies the correct dimensions: 'resourceId' (Function OCID) for per-function scope, or 'applicationId' (Application OCID) for per-application scope",
    "Clarifies that FunctionErrorCount counts execution failures (exceptions/crashes/timeouts) — NOT handled HTTP 500 responses returned by the handler",
    "Provides the correct MQL alarm query using resourceId",
    "Recommends verifying available dimensions with: oci monitoring metric-data summarize-metrics-data --namespace oci_faas"
  ]
}
```

---

## Scenario 4: Edge — Alarm Alert Fatigue from Cold-Start Spikes

```json
{
  "skills": ["monitoring-oci-java-functions"],
  "query": "My production alarm on FunctionExecutionDuration is firing every Monday morning and waking up on-call engineers. The P99 spikes to 4s but drops within 60 seconds. How do I fix this without missing real incidents?",
  "expected_behavior": [
    "Identifies cold-start as the root cause of Monday-morning spikes (first invocations after weekend idle)",
    "Explains that the default pending_duration = PT1M fires on the very first evaluation window — before transient spikes resolve",
    "Recommends setting pending_duration >= PT2M (or PT3M for high-traffic functions) on production alarms",
    "Distinguishes between pending_duration (consecutive evaluations before firing) and resolution delay",
    "Notes that reducing the alarm threshold is the wrong fix — it would mask real incidents"
  ]
}
```

---

## Scenario 5: Misuse — Fire-and-Forget Metric Post in Background Thread

```json
{
  "skills": ["monitoring-oci-java-functions"],
  "query": "To avoid slowing down my function response I'm posting metrics in a background thread with CompletableFuture.runAsync(). Is this OK?",
  "expected_behavior": [
    "Identifies this as the fire-and-forget anti-pattern — explicitly covered in Never Do Patterns",
    "Explains that the FDK freezes the container immediately after handleRequest returns — background threads are killed mid-execution",
    "States the real-world impact: metric datapoints are silently lost, creating phantom gaps in dashboards with no error surfaced",
    "Provides the correct pattern: post metrics synchronously before handleRequest returns, with elapsed-time guard leaving at least 5s buffer before function timeout",
    "Does NOT suggest using a thread pool or daemon thread as a workaround"
  ]
}
```
