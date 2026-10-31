# ⚠️ Ask First Decisions — OCI Monitoring Alarms

---

## Decision 1: Notification Delivery — ONS vs OCI Streaming

**Ask**: "Is the alarm response human (pager, email) or automated (remediation pipeline, SIEM ingestion)?"

| Option | Service | Use When | Avoid When |
|--------|---------|----------|------------|
| **OCI Notifications (ONS)** | `oci_ons_notification_topic` | On-call alerting, email, PagerDuty, Slack, HTTPS webhook | High-volume alarm events (>100K/day), pure automation |
| **OCI Streaming** | `oci_streaming_stream` | SIEM ingestion, Kafka fan-out, automated remediation pipelines | Human-readable delivery, small team operations |
| **Both (ONS + Streaming)** | Both in `destinations` | Mission-critical: simultaneous pager + automated remediation | Simple single-path workflows |

**ONS example**:
```hcl
resource "oci_monitoring_alarm" "example" {
  # ...
  destinations = [oci_ons_notification_topic.oncall_pagerduty.id]
  message_format = "ONS_OPTIMIZED"   # structured JSON for webhook consumers
}
```

**Streaming example**:
```hcl
resource "oci_monitoring_alarm" "example" {
  # ...
  destinations = [oci_streaming_stream.alarm_events.id]
}
```

**Cost signal**: ONS email/SMS = very low; ONS HTTPS webhook = low; Streaming = per-GB ingested + per-hour capacity. Streaming cost is significant only at >100K events/day.

**Scaling signal**: ONS has per-subscription rate limits and may throttle during alarm flapping (rapid OK/FIRING cycling). Streaming scales horizontally with partition count — preferred for high-frequency alarm scenarios.

---

## Decision 2: Custom Metric Ingestion Method

**Ask**: "Where does the application run, and what type of metric is being emitted?"

| Option | Use When | Avoid When |
|--------|----------|------------|
| **OCI SDK / PostMetricData** | Business-logic metrics, Functions, containerized apps, cross-runtime | Simple host metrics already exposed via `/metrics` |
| **UMA MONITORING config (Prometheus scrape)** | OCI Compute/OKE, existing `/metrics` endpoint, open-source exporters | Serverless (Functions), off-OCI runtimes |
| **OCI APM** | Distributed tracing + span-derived latency metrics, trace-correlated alerting | Utilization/saturation metrics, cost-sensitive setups |

**PostMetricData SDK — use for Functions and business metrics**:
```python
# telemetry-ingestion endpoint (NOT telemetry)
post_metric_data_details = oci.monitoring.models.PostMetricDataDetails(
    metric_data=[
        oci.monitoring.models.MetricDataDetails(
            namespace="myapp_api",
            compartment_id=compartment_ocid,
            name="api_request_count",
            dimensions={"resourceId": instance_id, "endpoint": "/orders"},
            datapoints=[
                oci.monitoring.models.Datapoint(
                    timestamp=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    value=42.0,
                    count=1
                )
            ]
        )
    ]
)
monitoring_client.post_metric_data(post_metric_data_details)
```

**UMA MONITORING config — use for Compute/OKE with existing Prometheus endpoint**:
```json
{
  "sources": [
    {
      "name": "prometheus_scrape",
      "type": "URL",
      "url": "http://localhost:8080/metrics",
      "record_type": "OPENMETRICS_1_0"
    }
  ],
  "namespace": "myapp_api",
  "resource_group": "api-fleet"
}
```

**Decision tree**:
```
App on OCI Compute or OKE?
  └─ Yes → Has /metrics endpoint?
       └─ Yes  → UMA MONITORING config
       └─ No   → PostMetricData SDK
  └─ No (Functions, off-OCI) → PostMetricData SDK

Need trace correlation (latency SLOs, dependency maps)?
  └─ Yes → Add OCI APM (independent of above choice)
```

---

## Decision 3: Per-Dimension vs Grouped Notifications

**Ask**: "How many resources does this alarm cover? Does on-call need the resource ID in the notification to begin triage?"

| Option | `is_notifications_per_metric_dimension_enabled` | Use When | Avoid When |
|--------|---|----|---|
| **Grouped (default)** | `false` | Fleet-wide response is the same regardless of instance; ≤5 resources; noise reduction priority | Triage requires individual resource identity |
| **Per-dimension split** | `true` | Auto-scaling groups where specific instance identity is critical; small fleets (≤50 resources) | Large fleets (500+ instances) — causes notification storms |

**Per-dimension split with `groupBy` for cardinality control**:
```hcl
resource "oci_monitoring_alarm" "cpu_saturation" {
  # ...
  query = "CpuUtilization[1m].groupBy(resourceId).percentile(0.9) > 85"

  # Each unique resourceId generates a separate notification when FIRING
  is_notifications_per_metric_dimension_enabled = true
}
```

**High-cardinality fleet mitigation** (500+ instances):
```hcl
# Aggregate by availability domain (3 ADs) instead of instance (500 IDs)
query = "CpuUtilization[1m].groupBy(availabilityDomain).percentile(0.9) > 85"
is_notifications_per_metric_dimension_enabled = true
# Result: max 3 simultaneous notifications instead of 500
```

**Cost signal**: Per-dimension notifications multiply ONS delivery cost by number of FIRING dimension combinations. Measure actual fleet alarm volume before enabling on large fleets.
